"""Source controls: new owned files/processes only, never a Dev/backend call."""
import ast
from dataclasses import asdict
import json
import hashlib
import platform
import os
from pathlib import Path
import select
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from acceptance.handoff.opencode import facts,owner
from acceptance.handoff.opencode.baseline import C,S
from acceptance.handoff.opencode.batch import Batch
from acceptance.handoff.opencode.fixtures import Prepared,wire,native,capture_args,schema

SOURCE=Path(__file__).resolve().parent
LIB=Path('/lib/x86_64-linux-gnu/libsqlite3.so.0')


class ObservationControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=tempfile.TemporaryDirectory(prefix='oc-owned-build-')
        cls.directory=Path(cls.build.name)
        cls.helpers={}
        for name,flags in (('production',[]),('control',['-DOC_CONTROL_BUILD']),
                           ('authorizer',['-DOC_CONTROL_BUILD','-DOC_CONTROL_AUTHORIZE'])):
            target=cls.directory/name
            result=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O2',*flags,
                str(SOURCE/'oc_snapshot_vfs.c'),str(LIB),'-o',str(target)],capture_output=True)
            if result.returncode:raise AssertionError('native fixture build failed: '+result.stderr.decode())
            target.chmod(0o700);cls.helpers[name]=target
        hung=cls.directory/'hung.c'
        hung.write_text('#include <signal.h>\n#include <unistd.h>\nint main(void){signal(SIGTERM,SIG_IGN);for(;;)pause();}\n')
        target=cls.directory/'hung'
        subprocess.run(['cc','-Wall','-Wextra','-Werror',str(hung),'-o',str(target)],check=True,capture_output=True)
        target.chmod(0o700);cls.helpers['hung']=target
        # This is measured build metadata, not executable authenticity evidence.
        version=subprocess.run([str(cls.helpers['production']),'--build-facts'],capture_output=True,check=True)
        cls.build_facts=version.stdout.decode().strip()
        measured={'kind':'owned-offline-build-facts','python':platform.python_version(),
                  'python_sqlite':sqlite3.sqlite_version,'helper_sqlite':cls.build_facts,
                  'compiler':subprocess.run(['cc','--version'],capture_output=True,check=True).stdout.decode().splitlines()[0],
                  'library_sha256':hashlib.sha256(LIB.read_bytes()).hexdigest(),
                  'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted(SOURCE.iterdir()) if p.suffix in ('.py','.c','.h')},
                  'helper_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in cls.helpers.items()},
                  'authenticity_verified':False,'dev_observed':False}
        print(json.dumps(measured,sort_keys=True),flush=True)

    @classmethod
    def tearDownClass(cls):cls.build.cleanup()

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='oc-owned-case-')
        self.base=Path(self.tmp.name)
        self.case=Prepared(self.base,self.helpers['production'])

    def tearDown(self):
        self.case.close();self.tmp.cleanup()

    def result(self, raw=None):
        with self.case.owner() as controller:
            return controller.observe(self.case.raw if raw is None else raw,'authority_fixture')

    def update(self, sql, args=(), context=False):
        db=sqlite3.connect(self.case.state/('contexts.sqlite3' if context else 'opencode-tasks.sqlite3'))
        try:db.execute(sql,args);db.commit()
        finally:db.close()

    def direct(self, helper='production', target='oct_fixture', flags=()):
        fd,df=capture_args(self.case.state)
        try:
            return subprocess.run([str(self.helpers[helper]),*flags,str(fd),str(df)],
                input=('jobs\n'+target+'\n').encode(),capture_output=True,pass_fds=(fd,df),timeout=3)
        finally:os.close(fd);os.close(df)

    def test_joined_done_is_advisory_only(self):
        receipt=self.result()
        self.assertEqual(receipt.state,'OFFLINE_ADVISORY_DONE')
        self.assertEqual(receipt.native_status,'completed')
        self.assertIs(receipt.helper_stopped,True)
        self.assertIs(receipt.authorizes_actions,False)
        self.assertIs(receipt.dev_observed,False)
        self.assertIs(receipt.original_invocation_verified,False)

    def test_one_child_for_context_job_context(self):
        original=subprocess.Popen
        with mock.patch('acceptance.handoff.opencode.batch.subprocess.Popen',wraps=original) as called:
            self.assertEqual(self.result().state,'OFFLINE_ADVISORY_DONE')
        self.assertEqual(called.call_count,1)
        argv=called.call_args.args[0]
        self.assertEqual(argv[1],'--batch')
        self.assertTrue(argv[0].startswith('/proc/self/fd/'))
        self.assertNotIn('oct_fixture',argv)

    def test_real_frame_has_no_prompt(self):
        r=self.direct()
        self.assertEqual(r.returncode,0)
        self.assertEqual(r.stderr,b'')
        values=owner._decode(r.stdout,'jobs')
        self.assertEqual(values[0],'oct_fixture')
        self.assertNotIn(b'PRIVATE_PROMPT_SENTINEL',r.stdout)

    def test_other_jobs_and_source_files_unchanged(self):
        self.update("INSERT INTO jobs SELECT 'oct_other','req_other',fingerprint,created,started,finished,workspace,'ses_other',model,prompt,'running',NULL,child_pid,worker_start_ticks,child_start_ticks,exit_code,log_path,err_path,binary,max_output_bytes,max_runtime_seconds,cancel_flag,last_known_state,last_transition_at,transition_actor,transition_reason,result_reason FROM jobs")
        before={p.name:p.read_bytes() for p in self.case.state.iterdir() if p.is_file()}
        self.assertEqual(self.result().state,'OFFLINE_ADVISORY_DONE')
        after={p.name:p.read_bytes() for p in self.case.state.iterdir() if p.is_file()}
        self.assertEqual(before,after)
        db=sqlite3.connect(self.case.state/'opencode-tasks.sqlite3')
        try:self.assertEqual(db.execute("SELECT status FROM jobs WHERE job_id='oct_other'").fetchone(),('running',))
        finally:db.close()

    def test_invalid_checkpoint_never_starts_helper(self):
        with mock.patch.object(facts,'Batch',side_effect=AssertionError('must not capture')):
            r=self.result(b'{"PRIVATE_VALUE":true}')
        self.assertEqual(r.state,'HOLD');self.assertIsNone(r.helper_stopped)

    def test_expired_authority_prevents_capture(self):
        self.case.authority['expires_at']=int(time.time())-1
        self.case.write('authority.json',self.case.authority)
        with mock.patch.object(facts,'Batch',side_effect=AssertionError('must not capture')):
            r=self.result()
        self.assertEqual(r.reason,'AUTHORITY_EXPIRED')

    def test_missing_physical_scope_prevents_capture(self):
        self.case.authority['scopes'].remove('physical_state_read')
        self.case.write('authority.json',self.case.authority)
        with mock.patch.object(facts,'Batch',side_effect=AssertionError('must not capture')):r=self.result()
        self.assertEqual(r.reason,'AUTHORITY_UNAVAILABLE')

    def test_read_lock_scope_required(self):
        self.case.authority['scopes'].remove('shared_read_lock')
        self.case.write('authority.json',self.case.authority)
        self.assertEqual(self.result().reason,'AUTHORITY_UNAVAILABLE')

    def test_nonce_epoch_and_dev_flags_rejected(self):
        for field,value in (('nonce','a'*32),('epoch',True),('dev_authorized',True),('active',False)):
            old=self.case.authority[field]
            self.case.authority[field]=value;self.case.write('authority.json',self.case.authority)
            with self.subTest(field=field):self.assertEqual(self.result().reason,'AUTHORITY_UNAVAILABLE')
            self.case.authority[field]=old

    def test_changed_dossier_digest_rejected(self):
        self.case.dossier['job']['model']='PRIVATE_VALUE/model'
        self.case.write('dossier.json',self.case.dossier)
        self.assertEqual(self.result().reason,'BINDING_MISMATCH')

    def test_each_native_identity_mismatch(self):
        for field in ('request_id','session_id','model','workspace','binary','fingerprint','log_path'):
            db=sqlite3.connect(self.case.state/'opencode-tasks.sqlite3')
            try:
                old=db.execute('SELECT '+field+' FROM jobs').fetchone()[0]
                db.execute('UPDATE jobs SET '+field+'=?',('PRIVATE_VALUE',));db.commit()
            finally:db.close()
            with self.subTest(field=field):self.assertEqual(self.result().reason,'BINDING_MISMATCH')
            self.update('UPDATE jobs SET '+field+'=?',(old,))

    def test_native_statuses_preserved_without_goal_success(self):
        for status in ('pending','running','failed','cancelled','permission_required','unknown_exit'):
            self.update('UPDATE jobs SET status=?',(status,))
            with self.subTest(status=status):
                r=self.result();self.assertEqual(r.state,'HOLD');self.assertEqual(r.native_status,status)

    def test_untrusted_status_not_echoed(self):
        self.update('UPDATE jobs SET status=?',('PRIVATE_STATUS',))
        r=self.result();self.assertEqual(r.native_status,'unknown');self.assertNotIn('PRIVATE_STATUS',repr(r))

    def test_exit_zero_not_sufficient(self):
        self.update('UPDATE jobs SET transition_reason=?',('not_proven',))
        self.assertEqual(self.result().reason,'VERIFIER_REJECTED')

    def test_closed_missing_and_unassociated_context(self):
        self.update('UPDATE contexts SET closed=1',context=True)
        self.assertEqual(self.result().reason,'CONTEXT_UNBOUND')
        self.update('DELETE FROM contexts',context=True)
        self.assertEqual(self.result().state,'HOLD')
        self.case.dossier['context_id']=None;self.case.rebind_dossier()
        self.assertEqual(self.result().reason,'CONTEXT_UNBOUND')

    def test_current_binary_cannot_backfill_original(self):
        self.case.dossier['original_binary_required']=True;self.case.rebind_dossier()
        self.assertEqual(self.result().reason,'BINDING_MISMATCH')

    def test_current_binary_drift(self):
        (self.case.state/'inert-binary').write_bytes(b'changed binary bytes')
        self.assertEqual(self.result().reason,'BINDING_MISMATCH')

    def test_goal_evidence_mutation_does_not_fit_output(self):
        (self.case.state/'opencode-task-logs/oct_fixture.jsonl').write_bytes(b'reassuring text: complete')
        self.assertEqual(self.result().reason,'VERIFIER_REJECTED')

    def test_evidence_changes_after_first_real_read(self):
        original=facts.read_all
        output=self.case.state/'opencode-task-logs/oct_fixture.jsonl'
        inode=os.stat(output).st_ino
        changed=False
        def reading(fd,cap):
            nonlocal changed
            raw=original(fd,cap)
            if os.fstat(fd).st_ino==inode and not changed:
                changed=True;output.write_bytes(b'changed after real capture')
            return raw
        with mock.patch.object(facts,'read_all',reading):r=self.result()
        self.assertTrue(changed);self.assertEqual(r.reason,'EVIDENCE_MISMATCH')

    def test_real_hot_journal_rejected_without_recovery(self):
        path=self.case.state/'opencode-tasks.sqlite3'
        pid=os.fork()
        if pid==0:
            db=sqlite3.connect(path)
            db.execute('PRAGMA cache_size=1')
            db.execute('BEGIN IMMEDIATE')
            for i in range(40):
                db.execute("INSERT INTO jobs SELECT ?,?,fingerprint,created,started,finished,workspace,?,model,?,'running',NULL,child_pid,worker_start_ticks,child_start_ticks,exit_code,log_path,err_path,binary,max_output_bytes,max_runtime_seconds,cancel_flag,last_known_state,last_transition_at,transition_actor,transition_reason,result_reason FROM jobs WHERE job_id='oct_fixture'",
                           ('oct_hot_'+str(i),'req_hot_'+str(i),'ses_hot_'+str(i),'X'*8000))
            os._exit(91)  # Actual crash, not commit/close or a manufactured filename.
        self.assertEqual(os.waitpid(pid,0)[1],91<<8)
        journal=Path(str(path)+'-journal')
        self.assertTrue(journal.exists());self.assertGreater(journal.stat().st_size,512)
        before=path.read_bytes();saved=journal.read_bytes()
        self.assertEqual(self.result().state,'HOLD')
        self.assertEqual(path.read_bytes(),before);self.assertEqual(journal.read_bytes(),saved)

    def test_whole_owner_alarm_aborts_pending_helper_honestly(self):
        original=facts.read_all
        output=self.case.state/'opencode-task-logs/oct_fixture.jsonl'
        inode=os.stat(output).st_ino
        def reading(fd,cap):
            raw=original(fd,cap)
            if os.fstat(fd).st_ino==inode:
                signal.setitimer(signal.ITIMER_REAL,0.05)  # Fixture-only shortening.
                time.sleep(1)
            return raw
        with mock.patch.object(facts,'read_all',reading):r=self.result()
        self.assertEqual(r.reason,'BUDGET_EXHAUSTED');self.assertIs(r.helper_stopped,True)

    def test_log_symlink_and_hardlink_reject(self):
        p=self.case.state/'opencode-task-logs/oct_fixture.jsonl'
        target=self.case.control/'private'
        target.write_bytes(p.read_bytes());target.chmod(0o600)
        p.unlink();p.symlink_to(target)
        self.assertEqual(self.result().state,'HOLD')
        p.unlink();os.link(target,p)
        self.assertEqual(self.result().state,'HOLD')

    def test_job_db_mode_and_symlink_reject(self):
        p=self.case.state/'opencode-tasks.sqlite3';p.chmod(0o640)
        self.assertEqual(self.result().state,'HOLD')
        p.chmod(0o600);other=self.case.state/'saved';p.rename(other);p.symlink_to(other)
        self.assertEqual(self.result().state,'HOLD')

    def test_sidecars_reject_without_repair(self):
        for suffix in ('-journal','-wal','-shm'):
            p=self.case.state/('opencode-tasks.sqlite3'+suffix);p.write_bytes(b'PRIVATE_SIDECAR');p.chmod(0o600)
            with self.subTest(suffix=suffix):self.assertEqual(self.result().state,'HOLD')
            self.assertEqual(p.read_bytes(),b'PRIVATE_SIDECAR');p.unlink()

    def test_real_wal_header_rejected(self):
        db=sqlite3.connect(self.case.state/'opencode-tasks.sqlite3')
        try:db.execute('PRAGMA journal_mode=WAL');db.commit()
        finally:db.close()
        self.assertEqual(self.result().state,'HOLD')

    def test_schema_trigger_rejected(self):
        self.update('CREATE TRIGGER evil AFTER UPDATE ON jobs BEGIN DELETE FROM jobs; END')
        self.assertEqual(self.result().state,'HOLD')

    def test_real_unknown_job_reaches_query_failure(self):
        r=self.direct(helper='control',target='oct_missing')
        self.assertEqual(r.returncode,2)
        self.assertIn(b'CONTROL_STAGE=7;',r.stderr)
        self.assertEqual(r.stdout,b'HOLD: capture unavailable\n')

    def test_readonly_fd_required(self):
        fd=os.open(self.case.state/'opencode-tasks.sqlite3',os.O_RDWR)
        df=os.open(self.case.state,os.O_RDONLY|os.O_DIRECTORY)
        try:r=subprocess.run([str(self.helpers['production']),str(fd),str(df)],input=b'jobs\noct_fixture\n',capture_output=True,pass_fds=(fd,df))
        finally:os.close(fd);os.close(df)
        self.assertEqual(r.returncode,2)

    def test_fd_entry_replacement_rejected(self):
        fd,df=capture_args(self.case.state)
        path=self.case.state/'opencode-tasks.sqlite3';path.rename(self.case.state/'held')
        path.write_bytes((self.case.state/'held').read_bytes());path.chmod(0o600)
        try:r=subprocess.run([str(self.helpers['production']),str(fd),str(df)],input=b'jobs\noct_fixture\n',capture_output=True,pass_fds=(fd,df))
        finally:os.close(fd);os.close(df)
        self.assertEqual(r.returncode,2)

    def test_real_vfs_denial_callbacks(self):
        p=self.case.state/'opencode-tasks.sqlite3-journal';p.write_bytes(b'cold');p.chmod(0o600)
        before=(self.case.state/'opencode-tasks.sqlite3').read_bytes()
        r=self.direct(helper='control',flags=('--probe',))
        self.assertEqual(r.returncode,0)
        self.assertEqual(r.stdout,b'CONTROL_DENIALS=2047\n')
        self.assertEqual((self.case.state/'opencode-tasks.sqlite3').read_bytes(),before)
        self.assertEqual(p.read_bytes(),b'cold')

    def test_real_authorizer_denies_prompt_projection(self):
        r=self.direct(helper='authorizer')
        self.assertEqual(r.returncode,2)
        self.assertIn(b'VIOLATED=1;',r.stderr)
        self.assertIn(b'AUTH=23',r.stderr)
        self.assertNotIn(b'PRIVATE_PROMPT_SENTINEL',r.stdout+r.stderr)

    def held(self):
        fd,df=capture_args(self.case.state);read,write=os.pipe()
        proc=subprocess.Popen([str(self.helpers['control']),'--hold-read',str(fd),str(df),str(read)],
                              stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              pass_fds=(fd,df,read))
        os.close(read);os.close(fd);os.close(df)
        proc.stdin.write(b'jobs\noct_fixture\n');proc.stdin.close()
        ready,_,_=select.select([proc.stderr],[],[],2)
        self.assertTrue(ready);self.assertEqual(proc.stderr.readline(),b'CONTROL_READ_LOCK\n')
        return proc,write

    def test_real_shared_lock_blocks_writer_and_snapshot_is_coherent(self):
        proc,release=self.held()
        try:
            db=sqlite3.connect(self.case.state/'opencode-tasks.sqlite3',timeout=0)
            try:
                db.execute('BEGIN IMMEDIATE');db.execute("UPDATE jobs SET model='new/model',transition_reason='new' ")
                with self.assertRaises(sqlite3.OperationalError):db.commit()
                db.rollback()
            finally:db.close()
            os.write(release,b'G');os.close(release);release=None
            data=proc.stdout.read();self.assertEqual(proc.wait(timeout=2),0)
            values=owner._decode(data,'jobs')
            self.assertEqual((values[3],values[12]),('fixture/model','response_completed'))
            self.update("UPDATE jobs SET model='new/model',transition_reason='new'")
            values=owner._decode(self.direct().stdout,'jobs')
            self.assertEqual((values[3],values[12]),('new/model','new'))
        finally:
            if release is not None:os.close(release)
            proc.wait(timeout=2);proc.stdout.close();proc.stderr.close()

    def test_real_one_second_alarm_releases_lock(self):
        proc,release=self.held()
        try:self.assertEqual(proc.wait(timeout=3),72)
        finally:os.close(release);proc.stdout.close();proc.stderr.close()
        self.update("UPDATE jobs SET transition_reason='after_alarm'")

    def test_existing_exclusive_writer_causes_fast_hold(self):
        db=sqlite3.connect(self.case.state/'opencode-tasks.sqlite3',timeout=0)
        try:
            db.execute('BEGIN EXCLUSIVE')
            start=time.monotonic();r=self.direct()
            self.assertEqual(r.returncode,2)
            self.assertLess(time.monotonic()-start,1)
            db.rollback()
        finally:db.close()

    def test_real_success_prefix_then_post_failure_never_done(self):
        original=facts.Batch.request
        def request(session,role,target):
            out=original(session,role,target)
            if role=='jobs':self.update('DELETE FROM contexts',context=True)
            return out
        with mock.patch.object(facts.Batch,'request',request):r=self.result()
        self.assertEqual(r.state,'HOLD')
        self.assertIs(r.helper_stopped,True)

    def test_pidfd_acquisition_failure_still_stops_direct_child(self):
        with mock.patch('acceptance.handoff.opencode.batch.os.pidfd_open',side_effect=OSError('fixture failure')):
            r=self.result()
        self.assertEqual(r.state,'HOLD')
        self.assertIs(r.helper_stopped,True)

    def test_checkpoint_head_race_after_native_capture(self):
        original=facts.Batch.request
        def request(session,role,target):
            out=original(session,role,target)
            if role=='jobs':
                value=json.loads(self.case.raw);p=value['payload']
                p['checkpoint_id']='checkpoint_fixture_002';p['generation']=2;p['parent_sha256']=value['payload_sha256']
                value['payload_sha256']=owner.digest(C.canonical(p))
                self.case.store.append(wire(value),1,self.case.envelope['payload_sha256'])
            return out
        with mock.patch.object(facts.Batch,'request',request):r=self.result()
        self.assertEqual(r.reason,'BINDING_MISMATCH')

    def test_parent_deadline_kills_only_owned_hung_fixture(self):
        rootfd=os.open(self.case.state,os.O_RDONLY|os.O_DIRECTORY)
        helper=os.open(self.helpers['hung'],os.O_RDONLY)
        batch=Batch(rootfd,helper,owner.digest(self.helpers['hung'].read_bytes()),time.monotonic()+0.1)
        try:
            with self.assertRaises(owner.Hold):
                with batch:batch.request('context','ctx_fixture')
            self.assertIsNotNone(batch.proc.returncode)
            self.assertLess(batch.proc.returncode,0)
        finally:os.close(rootfd);os.close(helper)

    def test_frame_trailing_truncation_and_wrong_role(self):
        good=self.direct().stdout
        for raw in (good+b'x',good[:-1],b'x'+good):
            with self.subTest(size=len(raw)),self.assertRaises(owner.Hold):owner._decode(raw,'jobs')
        with self.assertRaises(owner.Hold):owner._decode(good,'context')

    def test_helper_hash_drift_before_execution(self):
        rootfd=os.open(self.case.state,os.O_RDONLY|os.O_DIRECTORY);helper=os.open(self.helpers['production'],os.O_RDONLY)
        try:
            with mock.patch('acceptance.handoff.opencode.batch.subprocess.Popen',side_effect=AssertionError('no exec')):
                with self.assertRaises(owner.Hold):
                    with Batch(rootfd,helper,'a'*64,time.monotonic()+2):pass
        finally:os.close(rootfd);os.close(helper)

    def test_authority_revoked_after_capture(self):
        original=facts.Batch.request
        def request(session,role,target):
            out=original(session,role,target)
            if role=='jobs':
                self.case.authority['active']=False;self.case.write('authority.json',self.case.authority)
            return out
        with mock.patch.object(facts.Batch,'request',request):r=self.result()
        self.assertEqual(r.reason,'AUTHORITY_UNAVAILABLE')
        self.assertIs(r.helper_stopped,True)

    def test_context_closed_between_checks(self):
        original=facts.Batch.request
        def request(session,role,target):
            out=original(session,role,target)
            if role=='jobs':self.update('UPDATE contexts SET closed=1',context=True)
            return out
        with mock.patch.object(facts.Batch,'request',request):r=self.result()
        self.assertEqual(r.reason,'CONTEXT_UNBOUND')

    def test_checkpoint_cas_head_change_rejected(self):
        value=json.loads(self.case.raw);p=value['payload']
        p['checkpoint_id']='checkpoint_fixture_002';p['generation']=2;p['parent_sha256']=value['payload_sha256']
        value['payload_sha256']=owner.digest(C.canonical(p))
        self.case.store.append(wire(value),1,self.case.envelope['payload_sha256'])
        self.assertEqual(self.result().reason,'BINDING_MISMATCH')

    def test_owner_single_use_and_caller_facts_rejection(self):
        with self.case.owner() as controller:
            self.assertEqual(controller.observe(self.case.raw,'authority_fixture').state,'OFFLINE_ADVISORY_DONE')
            with self.assertRaises(owner.Hold):controller.observe(self.case.raw,'authority_fixture')
        self.assertEqual(self.result({'verifier_passed':True}).state,'HOLD')

    def test_private_data_not_in_public_receipt(self):
        r=self.result()
        text=json.dumps(asdict(r))
        for value in ('PRIVATE_PROMPT_SENTINEL',str(self.base),'oct_fixture','req_fixture','ses_fixture','f'*64):
            self.assertNotIn(value,text)

    def test_strict_authority_parser(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":1.0}',b' '*65537,
                    b'{"a":'+b'['*17+b'0'+b']'*17+b'}'):
            with self.assertRaises(owner.Hold):facts.record(raw)

    def test_no_native_runtime_imports_or_mutation_methods(self):
        for file in ('owner.py','batch.py','facts.py','baseline.py'):
            tree=ast.parse((SOURCE/file).read_text())
            imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
            self.assertFalse(any(x and (x.startswith('opencode_') or x=='contexts') for x in imports))
            calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
            self.assertFalse(set(calls)&{'submit','cancel','recent','status','result','_reconcile','chmod'})

    def test_build_facts_are_actual_system_sqlite(self):
        self.assertIn('SQLite=3.45.1',self.build_facts)
        manifest=json.loads((SOURCE/'source-hashes.json').read_bytes())
        for entry in manifest['source']+manifest['unchanged_dependencies']:
            raw=(ROOT/entry['path']).read_bytes()
            self.assertEqual(len(raw),entry['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
        print('Native helper build facts:',self.build_facts.replace('\n','; '))


if __name__=='__main__':unittest.main(verbosity=2)
