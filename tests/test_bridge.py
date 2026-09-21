import json
from pathlib import Path
import sys
import tempfile
import unittest
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import Bridge, BridgeError
from config_schema import ConfigError, load_bridge_config


class FakeHermes:
    def __init__(self):
        self.posts = 0
        self.runs = {}
        self.keys = {}
        self.run_bodies = []
        self.durable = True
        self.lost = False
        self.pending = None
        self.approvals = []

    def __call__(self, req):
        if req.headers.get('authorization') != 'Bearer test-secret-123':
            return httpx.Response(401)
        path = req.url.path
        if path == '/v1/models':
            return httpx.Response(200, json={'data':[{'id':'hermes-agent'}]})
        if path == '/v1/capabilities':
            return httpx.Response(200, json={'features':{
                'run_submission':True, 'run_status':True, 'run_stop':True,
                'run_approval_response':True, 'run_model_override':True,
                'runs_idempotency':{'supported':True,'durable':self.durable}}})
        if path == '/v1/runs' and req.method == 'POST':
            self.posts += 1
            key = req.headers['idempotency-key']
            if key not in self.keys:
                rid = 'run_' + str(len(self.runs)+1)
                self.keys[key] = rid
                body = json.loads(req.content)
                self.run_bodies.append(body)
                self.runs[rid] = {'run_id':rid, 'status':'completed',
                    'session_id':body.get('session_id',rid),
                    'output':'ผลทดสอบ test-secret-123', 'usage':{'total_tokens':3}}
            if self.lost:
                self.lost = False
                raise httpx.ReadTimeout('accepted but response lost')
            return httpx.Response(202, json={'run_id':self.keys[key], 'status':'started'})
        bits = path.split('/')
        rid = bits[3] if len(bits)>3 else ''
        if rid not in self.runs:
            return httpx.Response(404)
        if path.endswith('/stop'):
            self.runs[rid]['status']='cancelled'
            return httpx.Response(200, json={'status':'stopping'})
        if path.endswith('/approval'):
            self.approvals.append(json.loads(req.content))
            return httpx.Response(200,json={'resolved':1})
        if self.pending:
            return httpx.Response(200,json={'run_id':rid,'status':'waiting_for_approval',
                'session_id':rid,'approval':{'request_id':self.pending, 'command':'rm example.txt'}})
        return httpx.Response(200,json=self.runs[rid])


class TestBridge(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.fake=FakeHermes()
        self.model_config=Path(self.tmp.name)/'config.yaml'
        self.model_config.write_text('model:\n  default: deepseek/test\n  provider: nous\n')
        self.b=Bridge('http://127.0.0.1:8642','test-secret-123',Path(self.tmp.name),httpx.MockTransport(self.fake),self.model_config)
    def tearDown(self):
        self.b.client.close()
        self.tmp.cleanup()
    def test_auth_and_lifecycle_followup_pagination(self):
        health=self.b.health()
        self.assertTrue(health['ok'])
        self.assertTrue(health['features']['run_approval_response'])
        rid=self.b.submit('hello','req1')['run_id']
        status=self.b.status(rid)
        self.assertEqual(status['status'],'completed')
        first=self.b.result(rid,0,4)
        self.assertEqual(first['next_offset'],4)
        self.assertNotIn('test-secret-123',self.b.result(rid)['output'])
        self.b.submit('followup','req2',status['session_id'])
        self.assertEqual(self.fake.posts,2)
    def test_duplicate_and_restart_do_not_rerun(self):
        rid=self.b.submit('hello','req1')['run_id']
        self.b.client.close()
        self.b=Bridge('http://127.0.0.1:8642','test-secret-123',Path(self.tmp.name),httpx.MockTransport(self.fake),self.model_config)
        self.assertEqual(self.b.submit('hello','req1')['run_id'],rid)
        self.assertEqual(self.fake.posts,1)
        with self.assertRaises(BridgeError): self.b.submit('changed','req1')
    def test_lost_acceptance_durable_replay(self):
        self.fake.lost=True
        with self.assertRaises(BridgeError): self.b.submit('hello','req1')
        rid=self.b.submit('hello','req1')['run_id']
        self.assertEqual(len(self.fake.runs),1)
        self.assertEqual(rid,'run_1')
    def test_uncertain_without_durable_replay_is_blocked(self):
        self.fake.lost=True
        with self.assertRaises(BridgeError): self.b.submit('hello','req1')
        self.fake.durable=False
        with self.assertRaises(BridgeError): self.b.submit('hello','req1')
        self.assertEqual(self.fake.posts,1)
    def test_old_replay_blocked(self):
        self.fake.lost=True
        with self.assertRaises(BridgeError): self.b.submit('hello','req1')
        with self.b.db() as d: d.execute('UPDATE runs SET created=0')
        with self.assertRaises(BridgeError): self.b.submit('hello','req1')
        self.assertEqual(self.fake.posts,1)
    def test_unknown_runs_and_sessions_rejected(self):
        for method in (self.b.status,self.b.stop,self.b.result):
            with self.assertRaises(BridgeError): method('run_foreign')
        with self.assertRaises(BridgeError): self.b.submit('hi','req1','foreign_session')
        with self.assertRaises(BridgeError): self.b.submit('hi','bad\nkey')
    def test_approval_is_exact_once_and_requires_confirmation(self):
        rid=self.b.submit('hello','req1')['run_id']
        self.fake.pending='approval-123'
        self.assertEqual(self.b.status(rid)['status'],'waiting_for_approval')
        self.b.resolve_local(rid,'once',lambda a,c:False)
        self.assertEqual(self.fake.approvals,[])
        self.b.resolve_local(rid,'once',lambda a,c:True)
        self.assertEqual(self.fake.approvals,[{'choice':'once','request_id':'approval-123','resolve_all':False}])

    def test_deny_approval_is_exact_once(self):
        rid=self.b.submit('hello','req-deny')['run_id']
        self.fake.pending='approval-deny'
        self.b.resolve_local(rid,'deny',lambda a,c:True)
        self.assertEqual(self.fake.approvals,[{'choice':'deny','request_id':'approval-deny','resolve_all':False}])

    def test_stale_and_approval_stale_are_local_labels(self):
        self.b.client.close()
        self.b=Bridge('http://127.0.0.1:8642','test-secret-123',Path(self.tmp.name),httpx.MockTransport(self.fake),
                      self.model_config, operational_config={'stale_run_seconds':2,'approval_stale_seconds':1})
        rid=self.b.submit('hello','req-stale')['run_id']
        self.fake.pending='approval-stale'
        with self.b.db() as d: d.execute('UPDATE runs SET created=0 WHERE run_id=?',(rid,))
        status=self.b.status(rid)
        self.assertTrue(status['stale'])
        self.assertTrue(status['approval_stale'])
        self.assertEqual(self.fake.approvals,[])

    def test_local_status_does_not_call_upstream(self):
        before=self.fake.posts
        status=self.b.local_status()
        self.assertTrue(status['ok'])
        self.assertFalse(status['upstream_checked'])
        self.assertEqual(self.fake.posts,before)
    def test_changed_approval_not_resolved(self):
        rid=self.b.submit('hello','req1')['run_id']
        self.fake.pending='approval-123'
        def change(a,c):
            self.fake.pending='approval-456'
            return True
        with self.assertRaises(BridgeError): self.b.resolve_local(rid,'once',change)
        self.assertEqual(self.fake.approvals,[])
    def test_cached_output_survives_upstream_expiry(self):
        rid=self.b.submit('hello','req1')['run_id']
        original=self.b.result(rid)
        self.fake.runs.clear()
        self.assertEqual(self.b.result(rid),original)
    def test_stop_and_url_guard(self):
        rid=self.b.submit('hello','req1')['run_id']
        self.assertEqual(self.b.stop(rid)['status'],'stopping')
        self.assertEqual(self.b.status(rid)['status'],'cancelled')
        for url in ('http://example.com','http://127.0.0.1/evil','http://user@127.0.0.1'):
            with self.assertRaises(BridgeError): Bridge(url,'key',Path(self.tmp.name))
    def test_redirect_is_not_followed(self):
        self.b.client.close()
        seen=[]
        def redirect(req):
            seen.append(str(req.url))
            return httpx.Response(302,headers={'Location':'http://example.com/steal'})
        self.b.client=httpx.Client(base_url=self.b.base,follow_redirects=False,transport=httpx.MockTransport(redirect))
        with self.assertRaises(BridgeError): self.b.request('GET','/v1/models')
        self.assertEqual(len(seen),1)

    def test_model_override_is_recorded_and_included_in_fingerprint(self):
        started = self.b.submit('hello', 'req-model', model='deepseek/test', provider='nous',
                                model_options={'reasoning_effort':'high'})
        self.assertEqual(self.fake.run_bodies[-1]['model'], 'deepseek/test')
        self.assertEqual(self.fake.run_bodies[-1]['provider'], 'nous')
        self.assertEqual(self.fake.run_bodies[-1]['model_options'], {'reasoning_effort':'high'})
        self.assertEqual(started['requested_model'], 'deepseek/test')
        status = self.b.status(started['run_id'])
        self.assertEqual(status['requested_provider'], 'nous')
        self.assertEqual(status['requested_model_options'], {'reasoning_effort':'high'})
        with self.assertRaises(BridgeError):
            self.b.submit('hello', 'req-model', model='deepseek/other', provider='nous')

    def test_model_override_is_rejected_for_followups(self):
        first = self.b.submit('hello', 'req-first', model='deepseek/test')
        session = self.b.status(first['run_id'])['session_id']
        with self.assertRaises(BridgeError):
            self.b.submit('follow up', 'req-follow', session, model='deepseek/test')
        self.b.submit('follow up', 'req-follow-ok', session)

    def test_model_info_and_catalog(self):
        info = self.b.model_info()
        self.assertEqual(info['configured']['default'], 'deepseek/test')
        self.assertEqual(info['configured']['provider'], 'nous')
        self.assertTrue(info['bridge']['per_run_model_override'])
        self.assertTrue(info['hermes_advertised']['run_model_override'])
        self.assertEqual(self.b.models()['models'][0]['id'], 'hermes-agent')

    def test_existing_database_migrates(self):
        self.b.client.close()
        dbpath = Path(self.tmp.name)/'runs.sqlite3'
        import sqlite3
        with sqlite3.connect(dbpath) as db:
            db.execute('DROP TABLE runs')
            db.execute('CREATE TABLE runs (request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, created REAL NOT NULL, run_id TEXT UNIQUE, session_id TEXT, result TEXT)')
        self.b=Bridge('http://127.0.0.1:8642','test-secret-123',Path(self.tmp.name),httpx.MockTransport(self.fake),self.model_config)
        with self.b.db() as db:
            columns = {row[1] for row in db.execute('PRAGMA table_info(runs)')}
        self.assertTrue({'requested_model','requested_provider','requested_model_options','reported_model'} <= columns)

    def test_usage_summary_and_export_are_sanitized(self):
        rid = self.b.submit('hello', 'req-usage', model='deepseek/test')['run_id']
        self.b.result(rid)
        summary = self.b.usage_summary()
        self.assertEqual(summary['totals']['total_tokens'], 3)
        self.assertEqual(summary['by_model']['deepseek/test']['runs'], 1)
        exported = self.b.usage_export()['records'][0]
        self.assertEqual(exported['run_id'], rid)
        self.assertNotIn('output', exported)
        self.assertNotIn('prompt', exported)
        for bad in (0,1001,'1'):
            with self.assertRaises(BridgeError): self.b.usage_summary(bad)

    def test_config_schema_rejects_bad_types_and_warns_legacy_unknown_keys(self):
        root=Path(self.tmp.name)
        (root/'bridge-config.json').write_text(json.dumps({'api_url':'http://127.0.0.1:8642','hermes_env':'x','unexpected':1}))
        _, warnings=load_bridge_config(root)
        self.assertTrue(any('legacy' in value for value in warnings))
        self.assertTrue(any('unexpected' in value for value in warnings))
        (root/'bridge-config.json').write_text(json.dumps({'schema_version':1,'api_url':'x','hermes_env':'x','hermes':{'stale_run_seconds':'bad'}}))
        with self.assertRaises(ConfigError): load_bridge_config(root)
        (root/'bridge-config.json').write_text(json.dumps({'schema_version':1,'api_url':'x','hermes_env':'x',
            'audit':{'max_bytes':1},'codex':{'workspaces':[{'path':'/tmp','typo':True}]}}))
        with self.assertRaises(ConfigError): load_bridge_config(root)
        (root/'bridge-config.json').write_text(json.dumps({'schema_version':1,'api_url':'x','hermes_env':'x',
            'codex':{'workspaces':[{'path':'/tmp','typo':True}]}}))
        _, warnings=load_bridge_config(root)
        self.assertTrue(any('workspaces[0].typo' in value for value in warnings))


if __name__=='__main__': unittest.main()
