"""Meaningful source controls, NOT the paired H01-H10 evaluation protocol."""
import ast
import copy
from dataclasses import replace
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import tempfile
import unittest

import checkpoint as C
from checkpoint import Hold, plan, validate
from fixtures import BackendFixture, ROOT, database, encode, envelope, ready
import store as S


def _crash_append(root, raw, generation, digest, when):
    with S.Store(root) as db:
        original = S._commit
        def crash(connection):
            if when == 'before':
                os._exit(88)
            original(connection)
            os._exit(89)
        S._commit = crash
        db.append(raw, generation, digest)


def _concurrent(root, raw, generation, digest, event, conn):
    try:
        with S.Store(root) as db:
            event.wait(5)
            db.append(raw, generation, digest)
        conn.send('committed')
    except Hold as e:
        conn.send(e.code)
    finally:
        conn.close()


class ValidationControls(unittest.TestCase):
    def test_approved_schema_and_example_pinned(self):
        schema = ROOT/'docs/schemas/handoff-checkpoint-v1.schema.json'
        self.assertEqual(hashlib.sha256(schema.read_bytes()).hexdigest(), C.SCHEMA_SHA)
        self.assertEqual(validate((ROOT/'docs/examples/handoff-checkpoint-v1.synthetic.json').read_bytes()), envelope())

    def test_checksum_not_just_shape(self):
        e = envelope(); e['payload_sha256'] = '0'*64
        with self.assertRaises(Hold) as caught:
            validate(C.canonical(e))
        self.assertEqual(caught.exception.code, 'CHECKSUM_MISMATCH')

    def test_reject_duplicate_nonfinite_invalid_bytes_depth_size(self):
        e = encode(envelope())
        cases = [e.replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1'),
                 b'{"schema_version":NaN}', b'{"schema_version":Infinity}', b'\xff', b'{}'*40000,
                 b'['*30+b'0'+b']'*30, e[:-3]]
        for raw in cases:
            with self.subTest(prefix=raw[:8]), self.assertRaises(Hold):
                validate(raw)

    def test_timestamp_always_checked_without_optional_library(self):
        for timestamp in ('bad', '2026-02-30T00:00:00Z', '2026-11-02',
                          '2026-11-02T00:00:00', '2026-11-02T24:00:00Z',
                          '2026-11-02T00:00:60Z', '2026-11-02T00:00:00+25:00',
                          '2026-11-02T00:00:00+00:60', '2026-11-02T00:60:00Z'):
            e = envelope(); e['payload']['created_at'] = timestamp
            with self.subTest(timestamp=timestamp), self.assertRaises(Hold): validate(encode(e))
        self.assertEqual(C.timestamp('2026-11-02T07:00:00+07:00'), C.timestamp('2026-11-02T00:00:00Z'))

    def test_closed_shapes_boolean_integers_and_false_authority(self):
        for change in (lambda e:e.update(schema_version=True),
                       lambda e:e['payload'].update(generation=True),
                       lambda e:e['payload'].update(generation=1.0),
                       lambda e:e['payload']['authorization'].update(authorizes_actions=True),
                       lambda e:e['payload']['backend'].update(workspace_ref='/PRIVATE/path'),
                       lambda e:e['payload'].update(prompt='PRIVATE'),
                       lambda e:e['payload'].update(last_error='PRIVATE')):
            e=envelope();change(e)
            with self.assertRaises(Hold) as caught:validate(encode(e))
            self.assertNotIn('PRIVATE', str(caught.exception))

    def test_generation_and_evidence_foreign_keys(self):
        for change in (lambda e:e['payload'].update(generation=2),
                       lambda e:e['payload'].update(parent_sha256='a'*64),
                       lambda e:e['payload']['verification'].update(evidence_ids=['missing']),
                       lambda e:e['payload']['task'].update(criteria_refs=['same','same'])):
            e=envelope();change(e)
            with self.assertRaises(Hold):validate(encode(e))

    def test_no_runtime_imports_or_mutation_in_validator_planner(self):
        tree=ast.parse(Path(C.__file__).read_text())
        imports=[n.module if isinstance(n,ast.ImportFrom) else n.names[0].name
                 for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertEqual(set(imports), {'dataclasses','datetime','hashlib','json','pathlib','re'})
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('eval','exec') for n in ast.walk(tree)))


class StoreControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.db=S.Store(self.root);self.addCleanup(self.db.close)
        self.e,self.raw,_=ready();self.gen,self.sha=self.db.append(self.raw)

    def next(self, suffix='2'):
        e=copy.deepcopy(self.e);e['payload'].update(checkpoint_id='checkpoint_'+suffix,generation=2,parent_sha256=self.sha)
        return encode(e)

    def test_roundtrip_modes_reopen_and_preserved_predecessor(self):
        self.assertEqual(self.db.head('chain_fixture_001')['payload_sha256'],self.sha)
        self.db.append(self.next(),self.gen,self.sha)
        with S.Store(self.root) as other:
            self.assertEqual(other.head('chain_fixture_001')['payload']['generation'],2)
        self.assertEqual((self.root/S.DB).stat().st_mode & 0o777,0o600)
        with database(self.root/S.DB) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM checkpoints').fetchone()[0],2)
            self.assertEqual(db.execute('SELECT envelope FROM checkpoints WHERE generation=1').fetchone()[0],self.raw)

    def test_stale_or_duplicate_append_rolls_back_without_head_change(self):
        for raw,gen,sha in [(self.raw,0,None),(self.next(),0,None),(self.next(),1,'a'*64)]:
            with self.assertRaises(Hold):self.db.append(raw,gen,sha)
            self.assertEqual(self.db.head('chain_fixture_001')['payload_sha256'],self.sha)

    def test_cap_no_automatic_prune(self):
        with S.Store(self.root,max_rows=1) as limited:
            with self.assertRaises(Hold) as caught:limited.append(self.next(),1,self.sha)
            self.assertEqual(caught.exception.code,'BUDGET_EXHAUSTED')
        self.assertEqual(self.db.head('chain_fixture_001')['payload_sha256'],self.sha)

    def test_unsafe_root_symlink_database_hardlink_journal_rejected(self):
        for mode in (0o755,0o770):
            self.root.chmod(mode)
            with self.assertRaises(Hold):S.Store(self.root)
            self.root.chmod(0o700)
        with tempfile.TemporaryDirectory() as elsewhere:
            link=Path(elsewhere)/'link';link.symlink_to(self.root,target_is_directory=True)
            with self.assertRaises(Hold):S.Store(link)
        journal=self.root/(S.DB+'-journal');journal.symlink_to(self.root/S.DB)
        with self.assertRaises(Hold):self.db.head('chain_fixture_001')
        journal.unlink()
        os.link(self.root/S.DB,self.root/'second-link')
        with self.assertRaises(Hold):S.Store(self.root)
        (self.root/'second-link').unlink()

    def test_database_mode_and_schema_drift_rejected(self):
        (self.root/S.DB).chmod(0o644)
        with self.assertRaises(Hold):self.db.head('chain_fixture_001')
        (self.root/S.DB).chmod(0o600)
        with database(self.root/S.DB) as db:db.execute('CREATE TABLE injected(value)')
        with self.assertRaises(Hold):self.db.head('chain_fixture_001')

    def test_corrupt_record_and_wrong_parent_detected(self):
        self.db.append(self.next(),1,self.sha)
        with database(self.root/S.DB) as db:db.execute('UPDATE checkpoints SET envelope=? WHERE generation=1',(b'{}',))
        with self.assertRaises(Hold):self.db.head('chain_fixture_001')

    def test_root_rename_keeps_descriptor_binding(self):
        moved=self.root.with_name(self.root.name+'_moved')
        self.root.rename(moved)
        self.addCleanup(lambda:moved.rename(self.root))
        # Existing store follows its retained directory, not a new numeric path.
        self.assertEqual(self.db.head('chain_fixture_001')['payload_sha256'],self.sha)

    def test_invalid_input_changes_no_database_bytes(self):
        before=(self.root/S.DB).read_bytes()
        with self.assertRaises(Hold):self.db.append(b'{PRIVATE_INVALID')
        self.assertEqual((self.root/S.DB).read_bytes(),before)

    def test_H07_actual_crash_before_and_after_commit(self):
        for when,code,expected in [('before',88,1),('after',89,2)]:
            with tempfile.TemporaryDirectory() as root:
                with S.Store(root) as db:db.append(self.raw)
                child=mp.get_context('fork').Process(target=_crash_append,args=(root,self.next(),1,self.sha,when))
                child.start();child.join(5)
                try:self.assertEqual(child.exitcode,code)
                finally:
                    if child.is_alive():child.kill();child.join(5)
                    child.close()
                with S.Store(root) as db:self.assertEqual(db.head('chain_fixture_001')['payload']['generation'],expected)

    def test_H10_actual_competing_processes_single_commit(self):
        ctx=mp.get_context('fork');event=ctx.Event();children=[];channels=[]
        try:
            for suffix in ('a','b'):
                parent,child=ctx.Pipe(False);p=ctx.Process(target=_concurrent,args=(str(self.root),self.next(suffix),1,self.sha,event,child))
                p.start();child.close();children.append(p);channels.append(parent)
            event.set();outcomes=[]
            for p,ch in zip(children,channels):
                self.assertTrue(ch.poll(5));outcomes.append(ch.recv());p.join(5);self.assertEqual(p.exitcode,0)
            self.assertCountEqual(outcomes,['committed','CONCURRENT_UPDATE'])
            self.assertEqual(self.db.head('chain_fixture_001')['payload']['generation'],2)
        finally:
            for p in children:
                if p.is_alive():p.kill();p.join(5)
                p.close()
            for ch in channels:ch.close()


class RecoveryControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.backend=BackendFixture(self.temp.name);self.addCleanup(self.backend.close)
        self.backend.admit()

    def test_H01_lost_ACK_same_logical_identity_one_effect(self):
        e,raw,facts=ready(unknown_job=True)
        recovered=BackendFixture(self.temp.name)
        self.addCleanup(recovered.close)
        self.assertEqual(recovered.admit(),'job_fixture_001')
        with self.assertRaises(Hold):recovered.admit('different_fingerprint')
        for backend in ('opencode','hermes'):
            e,raw,facts=ready(backend,unknown_job=True)
            d=plan(raw,replace(facts,job=recovered.observation()))
            self.assertEqual((d.action,d.job_id),('observe_original','job_fixture_001'))
        self.assertFalse(d.authorizes_actions);self.assertEqual(recovered.effects(),1)
        e,raw,facts=ready('codex',unknown_job=True)
        self.assertEqual(plan(raw,replace(facts,job=recovered.observation())).reason,'JOB_ID_UNKNOWN')
        self.assertEqual(recovered.effects(),1)

    def test_H02_disconnect_reconstruction_tracks_original(self):
        _,raw,facts=ready()
        before=self.backend.observation()
        again=BackendFixture(self.temp.name);self.addCleanup(again.close)
        d=plan(raw,replace(facts,job=again.observation()))
        self.assertEqual(d.job_id,before['job_id']);self.assertEqual(d.native_status,'running')
        self.assertEqual(again.effects(),1);self.assertTrue(self.backend.child.is_alive())

    def test_H03_missing_dossier_and_H06_binding_preflight(self):
        _,raw,facts=ready()
        for changed,reason in [(replace(facts,resolved_refs=frozenset()),'MISSING_DOSSIER'),
                               (replace(facts,acceptance_profile_ref='other_profile'),'MISSING_DOSSIER'),
                               (replace(facts,repository=dict(facts.repository,commit_sha='a'*40)),'BINDING_MISMATCH'),
                               (replace(facts,workspace_ref='other_workspace'),'BINDING_MISMATCH'),
                               (replace(facts,context_open=False),'BINDING_MISMATCH'),
                               (replace(facts,head=('other',1,'a'*64)),'STALE_GENERATION')]:
            self.assertEqual(plan(raw,changed).reason,reason)
        self.assertEqual(self.backend.effects(),1)

    def test_H04_cancel_request_not_terminal_and_completion_race(self):
        e,raw,facts=ready();e['payload']['lifecycle']['observation']='cancel_requested';raw=encode(e)
        facts=replace(facts,head=(e['payload']['chain_id'],1,e['payload_sha256']),job=self.backend.observation())
        self.assertEqual(plan(raw,facts).action,'observe_original')
        self.assertTrue(self.backend.cancel_request())
        self.assertEqual(self.backend.observation()['status'],'running')
        self.backend.finish('complete')
        d=plan(raw,replace(facts,job=self.backend.observation()))
        self.assertEqual(d.native_status,'cancelled');self.assertEqual(d.action,'hold')
        self.assertFalse(self.backend.artifact.exists());self.assertEqual(self.backend.effects(),1)

    def test_H04_completion_committed_before_cancel_request(self):
        self.backend.finish('complete')
        self.assertFalse(self.backend.cancel_request())
        self.assertEqual(self.backend.observation()['status'],'completed')
        self.assertTrue(self.backend.artifact.is_file())
        self.assertEqual(self.backend.effects(),1)

    def test_H05_dead_worker_no_terminal_keeps_unknown(self):
        self.backend.finish('crash');self.assertEqual(self.backend.child.exitcode,91)
        observed=self.backend.observation();self.assertEqual(observed['status'],'running')
        # Fixture collector models missing durable terminal; not actual backend recovery.
        observed['status']='unknown_exit'
        _,raw,facts=ready()
        d=plan(raw,replace(facts,job=observed))
        self.assertEqual((d.action,d.native_status),('reconcile_original','unknown_exit'))
        self.assertFalse(self.backend.artifact.exists());self.assertEqual(self.backend.effects(),1)

    def test_H08_native_complete_and_independent_artifact_verification(self):
        self.backend.finish('complete');observed=self.backend.observation()
        e,raw,facts=ready()
        self.assertEqual(plan(raw,replace(facts,job=observed)).reason,'VERIFIER_REJECTED')
        body=self.backend.artifact.read_bytes();sha=hashlib.sha256(body).hexdigest()
        evidence={'evidence_id':'artifact_fixture_001','kind':'artifact','sha256':sha,'size_bytes':len(body),
                  'verified_at':'2026-11-02T00:00:00Z','verifier_ref':'verifier_fixture_001','verdict':'verified'}
        e['payload']['evidence']=[evidence];e['payload']['verification']['evidence_ids']=['artifact_fixture_001']
        raw=encode(e)
        facts=replace(facts,head=(e['payload']['chain_id'],1,e['payload_sha256']),job=observed,
                      evidence={'artifact_fixture_001':('artifact',sha,len(body),'verifier_fixture_001')},
                      required_evidence=frozenset(['artifact_fixture_001']),verifier_passed=True)
        self.assertEqual(plan(raw,facts).action,'done')
        self.backend.artifact.write_bytes(b'drift')
        drift=self.backend.artifact.read_bytes()
        changed=replace(facts,evidence={'artifact_fixture_001':('artifact',hashlib.sha256(drift).hexdigest(),len(drift),'verifier_fixture_001')})
        self.assertEqual(plan(raw,changed).reason,'EVIDENCE_MISMATCH')
        self.backend.artifact.unlink()
        self.assertEqual(plan(raw,replace(facts,evidence={})).reason,'EVIDENCE_MISMATCH')
        self.assertEqual(plan(raw,replace(facts,verifier_passed=False)).reason,'VERIFIER_REJECTED')

    def test_H09_current_authority_not_checkpoint_snapshot(self):
        e,raw,facts=ready();e['payload']['authorization'].update(snapshot_state='reported_active',expires_at='2099-01-01T00:00:00Z')
        raw=encode(e);facts=replace(facts,head=(e['payload']['chain_id'],1,e['payload_sha256']))
        for changed,reason in [(replace(facts,authority_ref=None),'AUTHORITY_UNAVAILABLE'),
                               (replace(facts,expires_at='2026-11-01T00:00:00Z'),'AUTHORITY_EXPIRED'),
                               (replace(facts,scope_refs=frozenset()),'AUTHORITY_OUT_OF_SCOPE')]:
            d=plan(raw,changed);self.assertEqual(d.reason,reason);self.assertFalse(d.authorizes_actions)
        self.assertEqual(self.backend.effects(),1)

    def test_unknown_native_value_and_malicious_id_never_echoed(self):
        _,raw,facts=ready()
        job=self.backend.observation();job['status']='PRIVATE_VALUE'
        self.assertEqual(plan(raw,replace(facts,job=job)).native_status,'unknown')
        job['job_id']='/PRIVATE/path'
        decision=plan(raw,replace(facts,job=job))
        self.assertNotIn('PRIVATE',str(decision))


if __name__=='__main__':unittest.main(verbosity=2)
