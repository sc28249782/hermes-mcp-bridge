"""Offline fixture admission/Facts/verifier source candidate.

Only an explicitly trusted standalone fixture owner constructs Owner from
retained handles and a fresh epoch/nonce. No production approval issuer, Dev
entry point, CLI, backend/config dispatcher or arbitrary serialized Facts API.
Host/same-uid/same-process compromise is outside this bounded source trust model.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import signal
import threading
import time

from .owner import Hold, need, private_dir, open_file, unchanged, read_all, digest, identity
from .batch import Batch
from .baseline import C,S


SCOPES=frozenset(('scope_handoff_observe','physical_state_read','context_read',
                  'shared_read_lock','evidence_read','current_binary_read','handoff_head_read'))
JOB_FIELDS=('job_id','request_id','session_id','model','workspace','binary','fingerprint',
            'status','exit_code','log_path','max_output_bytes','transition_actor','transition_reason','cancel_flag')


def _pairs(items):
    result={}
    for k,v in items:
        need(k not in result)
        result[k]=v
    return result


def _bad(_):raise Hold()


def record(raw):
    need(type(raw) is bytes and 0<len(raw)<=65536)
    # A pre-parser nesting cap; quoted braces do not count.
    depth=0;quoted=escaped=False
    for b in raw:
        if quoted:
            if escaped:escaped=False
            elif b==92:escaped=True
            elif b==34:quoted=False
        elif b==34:quoted=True
        elif b in (91,123):
            depth+=1;need(depth<=16)
        elif b in (93,125):depth-=1;need(depth>=0)
    try:
        value=json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,
                         parse_constant=_bad,parse_float=_bad,
                         parse_int=lambda s:int(s) if len(s)<=20 else _bad(s))
    except (ValueError,UnicodeError,RecursionError):raise Hold() from None
    need(type(value) is dict)
    return value


def keys(obj, expected):need(type(obj) is dict and set(obj)==set(expected))


def utc(value):return datetime.fromtimestamp(value,timezone.utc).isoformat().replace('+00:00','Z')


@dataclass(frozen=True)
class Receipt:
    state: str
    reason: str | None
    native_status: str | None
    helper_stopped: bool | None
    authorizes_actions: bool=False
    dev_observed: bool=False
    original_invocation_verified: bool=False


class Owner:
    """Trusted-launch boundary, not a public authority service.

    Constructor inputs are accepted ONLY from the standalone trusted fixture
    launcher in tests. Checkpoint input can name references, never these handles,
    source digests, nonce, expected epoch or Store object. No Dev profile exists.
    Existing S.Store is created/admitted by that launcher BEFORE observation;
    observation never initializes/migrates a store or writes checkpoints.
    """
    def __init__(self,statefd,controlfd,logsfd,workspacefd,helperfd,helper_sha,
                 dossier_sha,nonce,epoch,store):
        need(type(store) is S.Store)
        for fd in (statefd,controlfd,logsfd,workspacefd):private_dir(fd)
        need(type(nonce) is str and len(nonce)==32 and type(epoch) is int and epoch>0)
        self.authority_fd=self.dossier_fd=None
        self.statefd=self.controlfd=self.logsfd=self.workspacefd=self.helperfd=None
        try:
            for name,fd in (('statefd',statefd),('controlfd',controlfd),('logsfd',logsfd),
                            ('workspacefd',workspacefd),('helperfd',helperfd)):
                setattr(self,name,os.dup(fd))
        except BaseException:
            self.close()
            raise
        self.helper_sha,self.dossier_sha,self.nonce,self.epoch=helper_sha,dossier_sha,nonce,epoch
        self.store=store
        self.used=False

    def close(self):
        for name in ('authority_fd','dossier_fd','statefd','controlfd','logsfd','workspacefd','helperfd'):
            fd=getattr(self,name,None)
            if fd is not None:os.close(fd);setattr(self,name,None)

    def __enter__(self):return self
    def __exit__(self,*args):self.close()

    def _authority(self, authority_ref, dossier):
        if self.authority_fd is None:self.authority_fd=open_file(self.controlfd,'authority.json',65536)
        unchanged(self.controlfd,'authority.json',self.authority_fd)
        a=record(read_all(self.authority_fd,65536))
        keys(a,('kind','schema','nonce','epoch','authority_ref','dossier_sha256','scopes','expires_at','active','dev_authorized'))
        need(a['kind']=='oc-offline-fixture-admission-v1' and type(a['schema']) is int and a['schema']==1)
        need(a['nonce']==self.nonce and type(a['epoch']) is int and a['epoch']==self.epoch
             and a['authority_ref']==authority_ref and a['active'] is True
             and a['dev_authorized'] is False and a['dossier_sha256']==self.dossier_sha,'AUTHORITY_UNAVAILABLE')
        need(type(a['scopes']) is list and all(type(x) is str for x in a['scopes'])
             and len(a['scopes'])==len(SCOPES) and frozenset(a['scopes'])==SCOPES,'AUTHORITY_UNAVAILABLE')
        need(type(a['expires_at']) is int and time.time()<a['expires_at'],'AUTHORITY_EXPIRED')
        need(a['expires_at']<=self.wall+300,'AUTHORITY_UNAVAILABLE')
        need(dossier['authority_ref']==authority_ref,'AUTHORITY_UNAVAILABLE')
        need(time.monotonic()<self.deadline and time.time()>=self.wall
             and abs((time.time()-self.wall)-(time.monotonic()-self.mono))<2,'BUDGET_EXHAUSTED')
        return a

    def _dossier(self):
        self.dossier_fd=open_file(self.controlfd,'dossier.json',65536)
        raw=read_all(self.dossier_fd,65536)
        need(digest(raw)==self.dossier_sha,'BINDING_MISMATCH')
        d=record(raw)
        keys(d,('kind','schema','authority_ref','backend','repository','head','context_id',
                'workspace_identity','job','goal','original_binary_required'))
        need(d['kind']=='oc-offline-fixture-dossier-v1' and type(d['schema']) is int and d['schema']==1)
        need(d['backend']=='opencode' and d['original_binary_required'] is False,'BINDING_MISMATCH')
        need(type(d['head']) is list and len(d['head'])==3 and type(d['head'][1]) is int)
        need(type(d['workspace_identity']) is list and len(d['workspace_identity'])==2
             and all(type(x) is int for x in d['workspace_identity']))
        keys(d['job'],('job_id','request_id','session_id','model','provider','workspace','workspace_ref',
                       'binary','binary_name','binary_sha256','fingerprint','input_fingerprint_ref',
                       'log_path','evidence_name'))
        keys(d['goal'],('goal_ref','criteria_refs','pending_refs','acceptance_profile_ref',
                        'evidence_id','evidence_kind','size_bytes','sha256','verifier_ref'))
        need(type(d['context_id']) is str and d['context_id'],'CONTEXT_UNBOUND')
        need(d['job']['provider']==d['job']['model'].split('/',1)[0] and '/' in d['job']['model'],'BINDING_MISMATCH')
        return d

    def _head(self,envelope,d):
        p=envelope['payload']
        fresh=self.store.head(p['chain_id'])
        need(C.canonical(fresh)==C.canonical(envelope),'BINDING_MISMATCH')
        need([p['chain_id'],p['generation'],envelope['payload_sha256']]==d['head'],'BINDING_MISMATCH')

    def observe(self, raw, authority_ref):
        need(not self.used,'BUDGET_EXHAUSTED');self.used=True
        need(threading.current_thread() is threading.main_thread())
        need(signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0))
        self.wall,self.mono=time.time(),time.monotonic();self.deadline=self.mono+20
        old=signal.getsignal(signal.SIGALRM)
        def timeout(_sig,_frame):raise Hold('BUDGET_EXHAUSTED')
        signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,45)
        status=None
        session=None
        def stopped():
            return None if session is None or session.proc is None else session.proc.returncode is not None
        try:
            envelope=C.validate(raw)
            d=self._dossier();a=self._authority(authority_ref,d);self._head(envelope,d)
            p=envelope['payload'];b=p['backend'];j=d['job'];g=d['goal']
            need(p['repository']==d['repository'],'BINDING_MISMATCH')
            need(identity(os.fstat(self.workspacefd))==tuple(d['workspace_identity']),'BINDING_MISMATCH')
            workspace=os.readlink('/proc/self/fd/'+str(self.workspacefd))
            state=os.readlink('/proc/self/fd/'+str(self.statefd))
            logs=os.readlink('/proc/self/fd/'+str(self.logsfd))
            need(all(x.startswith('/') and not x.endswith(' (deleted)') for x in (workspace,state,logs)))
            need(not state.startswith(workspace+'/') and state!=workspace,'BINDING_MISMATCH')
            need(identity(os.stat('opencode-task-logs',dir_fd=self.statefd,follow_symlinks=False))==identity(os.fstat(self.logsfd)),'BINDING_MISMATCH')
            need(j['workspace']==workspace and j['binary']==state+'/'+j['binary_name']
                 and j['log_path']==logs+'/'+j['evidence_name'],'BINDING_MISMATCH')
            need(b['name']=='opencode' and b['context_id']==d['context_id'] and b['provider_ref']=='provider_fixture', 'BINDING_MISMATCH')
            for k in ('job_id','request_id','session_id','workspace_ref','input_fingerprint_ref'):
                need(b[k] is not None and b[k]==j[k],'JOB_ID_UNKNOWN' if k=='job_id' else 'BINDING_MISMATCH')
            need(p['task']['goal_ref']==g['goal_ref'] and p['task']['criteria_refs']==g['criteria_refs']
                 and p['task']['pending_step_refs']==g['pending_refs']
                 and p['verification']['acceptance_profile_ref']==g['acceptance_profile_ref'],'BINDING_MISMATCH')
            bf=open_file(self.statefd,j['binary_name'],8*1024*1024)
            try:
                need(digest(read_all(bf,8*1024*1024))==j['binary_sha256'],'BINDING_MISMATCH')
                session=Batch(self.statefd,self.helperfd,self.helper_sha,self.deadline)
                with session:
                    ctx=session.request('context',d['context_id'])
                    need(ctx==(d['context_id'],None),'CONTEXT_UNBOUND')
                    values=session.request('jobs',j['job_id']);native=dict(zip(JOB_FIELDS,values))
                    for k in ('job_id','request_id','session_id','model','workspace','binary','fingerprint','log_path'):
                        need(native[k]==j[k],'BINDING_MISMATCH')
                    status=native['status'] if native['status'] in ('pending','running','completed','failed','cancelled','permission_required','unknown_exit') else 'unknown'
                    need(status=='completed','RECONCILIATION_REQUIRED')
                    need(type(native['exit_code']) is int and native['exit_code']==0
                         and native['transition_actor']=='worker' and native['transition_reason']=='response_completed'
                         and type(native['cancel_flag']) is int and native['cancel_flag']==0,'VERIFIER_REJECTED')
                    need(type(native['max_output_bytes']) is int and 65536<=native['max_output_bytes']<=8388608)
                    out=open_file(self.logsfd,j['evidence_name'],native['max_output_bytes'])
                    try:
                        evidence=read_all(out,native['max_output_bytes'])
                        # Independently locked exact artifact property profile; no model prose oracle.
                        need(type(g['size_bytes']) is int and len(evidence)==g['size_bytes'] and digest(evidence)==g['sha256'],'VERIFIER_REJECTED')
                        self._authority(authority_ref,d);self._head(envelope,d)
                        need(session.request('context',d['context_id'])==(d['context_id'],None),'CONTEXT_UNBOUND')
                        session.finish()
                        unchanged(self.logsfd,j['evidence_name'],out)
                        need(digest(read_all(out,native['max_output_bytes']))==g['sha256'],'EVIDENCE_MISMATCH')
                    finally:os.close(out)
                self._authority(authority_ref,d);self._head(envelope,d)
                unchanged(self.statefd,j['binary_name'],bf)
                need(digest(read_all(bf,8*1024*1024))==j['binary_sha256'],'BINDING_MISMATCH')
            finally:os.close(bf)
            unchanged(self.controlfd,'dossier.json',self.dossier_fd)
            need(digest(read_all(self.dossier_fd,65536))==self.dossier_sha,'BINDING_MISMATCH')
            resolved=frozenset((g['goal_ref'],g['acceptance_profile_ref'],b['input_ref'],b['input_fingerprint_ref'],*g['criteria_refs'],*g['pending_refs']))
            facts=C.Facts(tuple(d['head']),d['repository'],resolved,authority_ref,frozenset(a['scopes']),
                utc(a['expires_at']),utc(time.time()),'opencode',j['workspace_ref'],
                {k:j[k] for k in ('job_id','request_id','session_id','workspace_ref','input_fingerprint_ref')}|{'status':status,'exit_code':0},
                True,{g['evidence_id']:(g['evidence_kind'],g['sha256'],g['size_bytes'],g['verifier_ref'])},
                frozenset((g['evidence_id'],)),True,g['goal_ref'],frozenset(g['criteria_refs']),g['acceptance_profile_ref'])
            decision=C.plan(raw,facts)
            need(decision.action=='done' and decision.authorizes_actions is False,'VERIFIER_REJECTED')
            return Receipt('OFFLINE_ADVISORY_DONE',None,status,True)
        except Hold as error:
            return Receipt('HOLD','STOP_UNCONFIRMED' if stopped() is False else error.code,status,stopped())
        except C.Hold:
            return Receipt('HOLD','BINDING_MISMATCH',status,stopped())
        except (OSError,ValueError,TypeError,KeyError,AttributeError,RuntimeError):
            return Receipt('HOLD','STOP_UNCONFIRMED' if stopped() is False else 'CAPTURE_REJECTED',status,stopped())
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)
