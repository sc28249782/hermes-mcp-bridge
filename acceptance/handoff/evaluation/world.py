"""Synthetic fixture preparation; called only by an explicit future evaluation run.

Candidate fixtures/store are pinned dependencies. No actual backend adapter.
All children are direct children of the harness parent; decision children do not
own fixture workers. No source case runs during corpus validation.
"""
from contextlib import ExitStack
from dataclasses import replace
import copy
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import sqlite3
import tempfile
import time


def _db(path):
    from contextlib import closing
    return closing(sqlite3.connect(path))


def _store_child(store, root, raw, generation, digest, command, gate, output):
    try:
        with store.Store(root) as db:
            if gate is not None:
                gate.wait(5)
            if command.startswith('crash_'):
                original=store._commit
                def commit(connection):
                    if command=='crash_before':os._exit(88)
                    original(connection);os._exit(89)
                store._commit=commit
            db.append(raw,generation,digest)
        output.send('committed')
    except Exception as error:
        output.send(error.code if hasattr(error,'code') else 'HARNESS_ERROR')
    finally:
        output.close()


class World:
    def __init__(self,schedule,modules):
        self.stack=ExitStack();self.children=[];self.channels=[];self.fixture=None
        self.reached=False;self.fault_at=None;self.events=[];self.observations=0;self.storage_action=None
        self.c,self.s,self.fx=modules
        self.schedule=schedule

    def _fault(self):
        if self.fault_at is None:self.fault_at=time.monotonic()

    def _observe(self):
        self.observations+=1
        result=self.fixture.observation()
        # Fixture schema models one native job; Codex has no request replay ID.
        if self.schedule['backend']=='codex':result['request_id']=None
        return result

    def _record_proof(self,e,f):
        body=b'fixture verified artifact\n';sha=hashlib.sha256(body).hexdigest()
        evidence=dict(evidence_id='artifact_fixture_001',kind='artifact',sha256=sha,
                      size_bytes=len(body),verified_at='2026-11-02T00:00:00Z',
                      verifier_ref='verifier_fixture_001',verdict='verified')
        e['payload']['evidence']=[evidence]
        e['payload']['verification']['evidence_ids']=['artifact_fixture_001']
        current=self.fixture.artifact.read_bytes() if self.fixture.artifact.exists() else None
        facts={} if current is None else {'artifact_fixture_001':(
            'artifact',hashlib.sha256(current).hexdigest(),len(current),'verifier_fixture_001')}
        return replace(f,evidence=facts,required_evidence=frozenset(['artifact_fixture_001']),
                       verifier_passed=True)

    def _seed_store(self,e,generation):
        with self.s.Store(self.store_root) as db:
            if generation==2:
                previous=copy.deepcopy(e)
                previous['payload'].update(checkpoint_id='checkpoint_predecessor',generation=1,parent_sha256=None)
                _,sha=db.append(self.fx.encode(previous))
                e['payload'].update(checkpoint_id='checkpoint_current',generation=2,parent_sha256=sha)
                db.append(self.fx.encode(e),1,sha)
            else:
                db.append(self.fx.encode(e))
        return self.fx.encode(e)

    def _spawn(self,raw,generation,digest,command,gate=None):
        recv,send=mp.get_context('fork').Pipe(False)
        p=mp.get_context('fork').Process(target=_store_child,args=(self.s,str(self.store_root),raw,generation,digest,command,gate,send))
        p.start();send.close();self.children.append(p);self.channels.append(recv)
        return p,recv

    def prepare(self):
        root=Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        worker_root=root/'worker';worker_root.mkdir(mode=0o700)
        self.store_root=root/'checkpoint';self.store_root.mkdir(mode=0o700)
        self.fixture=self.fx.BackendFixture(worker_root);self.fixture.admit()
        assert self.fixture.effects()==1 and self.fixture.child.is_alive()
        self.events.append('fixture_effect_committed_ack_discarded')
        e,_,f=self.fx.ready(self.schedule['backend'])
        case,v=self.schedule['case'],self.schedule['variant']
        f=replace(f,job=self._observe())
        if case=='H01':
            self._fault()
            e['payload']['backend']['job_id']=None
            if v=='known_job':e['payload']['backend']['job_id']='job_fixture_001'
            if v=='fingerprint_mismatch':f=replace(f,job=dict(f.job,input_fingerprint_ref='different_fingerprint'))
            if v=='request_missing':e['payload']['backend']['request_id']=None
            self.events.append('response_not_available_to_client')
        elif case=='H02':
            self._fault()
            observer=self.fx.BackendFixture(worker_root)
            try:
                self.observations+=1
                assert observer.observation()['job_id']=='job_fixture_001'
            finally:observer.close()
            if v=='context_closed':f=replace(f,context_open=False)
            if v=='status_unavailable':f=replace(f,job=None)
            if v=='session_mismatch':f=replace(f,job=dict(f.job,session_id='other_session'))
            self.events.append('new_observer_original_worker_retained')
        elif case=='H03':
            self._fault()
            changes={'dossier_missing':dict(resolved_refs=frozenset()),
                     'criteria_missing':dict(resolved_refs=f.resolved_refs-{e['payload']['task']['criteria_refs'][0]}),
                     'goal_mismatch':dict(goal_ref='other_goal'),
                     'profile_mismatch':dict(acceptance_profile_ref='other_profile')}
            f=replace(f,**changes[v]);self.events.append(v)
        elif case=='H04':
            self._fault()
            e['payload']['lifecycle']['observation']='cancel_requested'
            if v in ('cancel_requested','cancel_wins'):
                assert self.fixture.cancel_request()
                if v=='cancel_wins':self.fixture.finish('complete')
            else:
                self.fixture.finish('complete');assert not self.fixture.cancel_request()
            f=replace(f,job=self._observe())
            if v=='complete_wins':f=self._record_proof(e,f)
            self.events.append(v)
        elif case=='H05':
            self._fault()
            if v=='worker_crash':
                self.fixture.finish('crash');assert self.fixture.child.exitcode==91
                native='unknown' if self.schedule['backend']=='hermes' else 'unknown_exit'
                f=replace(f,job=dict(f.job,status=native))
            if v=='status_unavailable':f=replace(f,job=None)
            if v=='native_unknown':f=replace(f,job=dict(f.job,status='new_fixture_status'))
            self.events.append(v)
        elif case=='H06':
            self._fault()
            if v=='commit':f=replace(f,repository=dict(f.repository,commit_sha='a'*40))
            if v=='branch':f=replace(f,repository=dict(f.repository,branch='other_branch'))
            if v=='workspace':f=replace(f,workspace_ref='other_workspace')
            if v=='policy':f=replace(f,repository=dict(f.repository,workspace_policy_ref='other_policy'))
            self.events.append(v)
        elif case=='H08':
            self._fault()
            self.fixture.finish('complete');f=replace(f,job=self._observe())
            if v=='missing':self.fixture.artifact.unlink()
            if v=='drift':self.fixture.artifact.write_bytes(b'drifted fixture')
            f=self._record_proof(e,f)
            if v=='verifier_reject':f=replace(f,verifier_passed=False)
            if v=='exit_nonzero':f=replace(f,job=dict(f.job,exit_code=9))
            self.events.append(v)
        elif case=='H09':
            self._fault()
            e['payload']['authorization'].update(snapshot_state='reported_active',expires_at='2099-01-01T00:00:00Z')
            if v=='missing':f=replace(f,authority_ref=None)
            if v in ('expired','snapshot_forged'):f=replace(f,expires_at='2026-11-01T00:00:00Z')
            if v=='revoked':f=replace(f,authority_ref='revoked_authority')
            if v=='scope_missing':f=replace(f,scope_refs=frozenset())
            self.events.append(v)
        raw=self._seed_store(e,self.schedule['generation'])
        p=e['payload'];f=replace(f,head=(p['chain_id'],p['generation'],e['payload_sha256']))
        # Dossier is preserved complete and identical for both arms. Checkpoint-
        # specific corruption does not poison an unrelated baseline data format.
        dossier=copy.deepcopy(p)
        if case=='H07':
            self._fault()
            if v=='checksum':
                bad=copy.deepcopy(e);bad['payload_sha256']='0'*64;raw=self.c.canonical(bad)
            if v=='duplicate':raw=raw.replace(b'"schema_version":1',b'"schema_version":1,"schema_version":1')
            if v=='unsupported':
                bad=copy.deepcopy(e);bad['schema_version']=99;raw=self.c.canonical(bad)
            if v=='timestamp':
                bad=copy.deepcopy(e);bad['payload']['created_at']='invalid';raw=self.fx.encode(bad)
            if v=='depth':raw=b'['*32+b'0'+b']'*32
            if v=='size':raw=b'x'*65537
            if v=='stale':f=replace(f,head=(p['chain_id'],p['generation']+1,'a'*64))
            if v=='corrupt_store':
                with _db(self.store_root/'checkpoints.sqlite3') as db:
                    with db:db.execute('UPDATE checkpoints SET envelope=? WHERE checkpoint_id=?',(b'broken',p['checkpoint_id']))
                self.storage_action='read'
            if v in ('crash_before','crash_after'):
                newer=copy.deepcopy(e);newer['payload'].update(checkpoint_id='checkpoint_after_crash',generation=p['generation']+1,parent_sha256=e['payload_sha256'])
                new_raw=self.fx.encode(newer)
                child,_=self._spawn(new_raw,p['generation'],e['payload_sha256'],v)
                child.join(5);assert child.exitcode==(88 if v=='crash_before' else 89)
                self.events.append('crash_child_exit_'+str(child.exitcode))
                expected=e if v=='crash_before' else newer
                with _db(self.store_root/'checkpoints.sqlite3') as db:
                    actual=db.execute('SELECT generation,digest FROM heads').fetchone()
                assert actual==(expected['payload']['generation'],expected['payload_sha256'])
                raw=self.fx.encode(expected);dossier=copy.deepcopy(expected['payload'])
                f=replace(f,head=(p['chain_id'],actual[0],actual[1]));self.storage_action='read'
            self.events.append(v)
        if case=='H10':
            self._fault()
            if v=='replay':self.storage_action='replay'
            if v=='cas_race':
                gate=mp.get_context('fork').Event();pairs=[]
                for suffix in ('left','right'):
                    newer=copy.deepcopy(e);newer['payload'].update(checkpoint_id='checkpoint_'+suffix,generation=p['generation']+1,parent_sha256=e['payload_sha256'])
                    pairs.append(self._spawn(self.fx.encode(newer),p['generation'],e['payload_sha256'],'append',gate))
                gate.set();outcomes=[]
                for child,ch in pairs:
                    assert ch.poll(5);outcomes.append(ch.recv());child.join(5);assert child.exitcode==0
                assert sorted(outcomes)==['CONCURRENT_UPDATE','committed']
                self.events.extend('cas_outcome_'+v for v in sorted(outcomes))
                with _db(self.store_root/'checkpoints.sqlite3') as db:tip=db.execute('SELECT generation,digest FROM heads').fetchone()
                assert tip[0]==p['generation']+1
                f=replace(f,head=(p['chain_id'],tip[0],tip[1]))
            if v=='head_mismatch':f=replace(f,head=(p['chain_id'],p['generation']+1,'b'*64))
            if v=='external_anchor_missing':f=replace(f,head=None)
            self.events.append(v)
        self.reached=True
        self.envelope=e;self.raw=raw;self.dossier=dossier;self.facts=f
        return self

    def proof(self):
        expected=hashlib.sha256(b'fixture verified artifact\n').hexdigest()
        body=self.fixture.artifact.read_bytes() if self.fixture.artifact.exists() else None
        with _db(self.fixture.db) as db:requests=db.execute('SELECT count(*) FROM jobs').fetchone()[0]
        ledger=self.fixture.observation()
        artifact_sha=None if body is None else hashlib.sha256(body).hexdigest()
        return dict(effects=self.fixture.effects(),requests=requests,ledger=ledger,artifact_sha256=artifact_sha,artifact_verified=body is not None and hashlib.sha256(body).hexdigest()==expected,
                    terminal_status=self.facts.job.get('status') if self.facts.job else None,
                    verifier_passed=self.facts.verifier_passed)

    def close(self):
        confirmed=True
        for child in self.children:
            try:
                if child.is_alive():child.terminate();child.join(5)
                if child.is_alive():child.kill();child.join(5)
                confirmed=confirmed and not child.is_alive();child.close()
            except (OSError,ValueError):confirmed=False
        for ch in self.channels:ch.close()
        try:
            if self.fixture:self.fixture.close()
        except (OSError,ValueError):confirmed=False
        self.stack.close()
        return confirmed
