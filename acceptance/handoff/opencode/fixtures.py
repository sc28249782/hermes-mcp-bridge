"""Owned synthetic native-schema files. Test-only; never reads a Dev directory."""
import ast
from pathlib import Path
import os
import sqlite3
import json
import time
import secrets

from .baseline import C,S
from .facts import Owner,SCOPES,utc
from .owner import digest,identity

ROOT = Path(__file__).resolve().parents[3]
FIXTURE_RESULT=b'{"fixture_goal":"accepted","sessionID":"ses_fixture"}\n'


def schema(path, table):
    tree = ast.parse((ROOT / path).read_text())
    values = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
              and isinstance(n.value, str) and 'CREATE TABLE IF NOT EXISTS '+table+' (' in n.value]
    assert len(values) == 1
    return values[0]


def native(root):
    root = Path(root)
    root.mkdir(mode=0o700)
    workspace=root.parent/'workspace'
    workspace.mkdir(mode=0o700)
    logs = root / 'opencode-task-logs'
    logs.mkdir(mode=0o700)
    output = logs / 'oct_fixture.jsonl'
    output.write_bytes(FIXTURE_RESULT)
    output.chmod(0o600)
    binary = root / 'inert-binary'
    binary.write_bytes(b'INERT FIXTURE; NEVER EXECUTE\n')
    binary.chmod(0o600)
    dbpath = root / 'opencode-tasks.sqlite3'
    db = sqlite3.connect(dbpath)
    try:
        db.execute(schema('opencode_tasks.py', 'jobs'))
        db.execute('INSERT INTO jobs(job_id,request_id,fingerprint,created,workspace,session_id,model,prompt,status,log_path,err_path,binary,max_output_bytes,max_runtime_seconds,exit_code,transition_actor,transition_reason) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   ('oct_fixture','req_fixture','f'*64,1,str(workspace),'ses_fixture','fixture/model',
                    'PRIVATE_PROMPT_SENTINEL','completed',str(output),str(logs/'err'),str(binary),65536,10,0,'worker','response_completed'))
        db.commit()
    finally:
        db.close()
    dbpath.chmod(0o600)
    ctxpath = root / 'contexts.sqlite3'
    db = sqlite3.connect(ctxpath)
    try:
        db.execute(schema('contexts.py', 'contexts'))
        db.execute('INSERT INTO contexts(context_id,label,created,updated) VALUES (?,?,?,?)',
                   ('ctx_fixture','fixture',1,1))
        db.commit()
    finally:
        db.close()
    ctxpath.chmod(0o600)
    return root


def capture_args(root):
    root = Path(root)
    return os.open(root/'opencode-tasks.sqlite3',os.O_RDONLY),os.open(root,os.O_RDONLY|os.O_DIRECTORY)


def wire(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode('utf-8')


class Prepared:
    """Trusted FIXTURE launcher. This is not a production authority issuer."""
    def __init__(self,base,helper):
        self.base=Path(base)
        self.state=native(self.base/'state')
        self.control=self.base/'control';self.control.mkdir(mode=0o700)
        store_root=self.base/'checkpoints';store_root.mkdir(mode=0o700)
        self.store=S.Store(str(store_root))  # Owned fixture creation before observation.
        self.nonce=secrets.token_hex(16)
        envelope=json.loads((ROOT/'docs/examples/handoff-checkpoint-v1.synthetic.json').read_bytes())
        p=envelope['payload'];p['repository']['worktree_state']='clean'
        p['repository']['commit_sha']='d7515c5fb4e33b41f81a8535fb06a0ea2cd72255'
        p['backend'].update(name='opencode',provider_ref='provider_fixture',job_id='oct_fixture',
                            request_id='req_fixture',session_id='ses_fixture',context_id='ctx_fixture',
                            input_fingerprint_ref='fingerprint_fixture')
        p['authorization'].update(authority_ref='authority_fixture',scope_refs=['scope_handoff_observe'],
                                  snapshot_state='reported_active',expires_at=utc(time.time()+60))
        # Independent preregistered fixture expectation, not observed output.
        content=FIXTURE_RESULT
        evidence=dict(evidence_id='evidence_fixture',kind='result_snapshot',sha256=digest(content),
                      size_bytes=len(content),verified_at=utc(time.time()),verifier_ref='verifier_fixture',verdict='verified')
        p['lifecycle'].update(observation='terminal_observed',native_status='completed',observed_at=utc(time.time()))
        p['evidence']=[evidence]
        p['verification'].update(verdict='verified',evidence_ids=['evidence_fixture'])
        p['last_error']=None
        envelope['payload_sha256']=digest(C.canonical(p))
        self.raw=wire(envelope);C.validate(self.raw);self.envelope=envelope
        self.store.append(self.raw)
        self.dossier=dict(kind='oc-offline-fixture-dossier-v1',schema=1,authority_ref='authority_fixture',
            backend='opencode',repository=p['repository'],head=[p['chain_id'],1,envelope['payload_sha256']],
            context_id='ctx_fixture',workspace_identity=list(identity(os.stat(self.base/'workspace'))),
            original_binary_required=False,
            job=dict(job_id='oct_fixture',request_id='req_fixture',session_id='ses_fixture',model='fixture/model',
                provider='fixture',workspace=str(self.base/'workspace'),workspace_ref=p['backend']['workspace_ref'],
                binary=str(self.state/'inert-binary'),binary_name='inert-binary',binary_sha256=digest((self.state/'inert-binary').read_bytes()),
                fingerprint='f'*64,input_fingerprint_ref='fingerprint_fixture',log_path=str(self.state/'opencode-task-logs/oct_fixture.jsonl'),
                evidence_name='oct_fixture.jsonl'),
            goal=dict(goal_ref=p['task']['goal_ref'],criteria_refs=p['task']['criteria_refs'],pending_refs=p['task']['pending_step_refs'],
                acceptance_profile_ref=p['verification']['acceptance_profile_ref'],evidence_id='evidence_fixture',evidence_kind='result_snapshot',
                size_bytes=len(content),sha256=digest(content),verifier_ref='verifier_fixture'))
        self.authority=dict(kind='oc-offline-fixture-admission-v1',schema=1,nonce=self.nonce,epoch=1,
            authority_ref='authority_fixture',dossier_sha256=digest(wire(self.dossier)),scopes=sorted(SCOPES),
            expires_at=int(time.time())+60,active=True,dev_authorized=False)
        self.write('dossier.json',self.dossier);self.write('authority.json',self.authority)
        self.helper=Path(helper)
        self.handles=[]

    def write(self,name,value):
        path=self.control/name
        if path.exists():path.write_bytes(wire(value))  # Explicit fixture mutation only.
        else:
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            try:os.write(fd,wire(value))
            finally:os.close(fd)

    def rebind_dossier(self):
        self.write('dossier.json',self.dossier)
        self.authority['dossier_sha256']=digest(wire(self.dossier))
        self.write('authority.json',self.authority)

    def owner(self):
        fds=[os.open(path,os.O_RDONLY|os.O_DIRECTORY) for path in
             (self.state,self.control,self.state/'opencode-task-logs',self.base/'workspace')]
        helperfd=os.open(self.helper,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            return Owner(*fds,helperfd,digest(self.helper.read_bytes()),digest(wire(self.dossier)),self.nonce,1,self.store)
        finally:
            for fd in (*fds,helperfd):os.close(fd)

    def close(self):self.store.close()
