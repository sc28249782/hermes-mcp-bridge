"""Review candidate. Default validates pinned corpus only; runs are explicit.

This is not a production sandbox or an authority/approval reader. No run is
started by importing this module or by its unit-control CI.
"""
import argparse
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import importlib.util
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CANDIDATE='c953b6f44116ba0740540e3c78d0b6e2c910573b'
BASELINE='93e9601f74b3e0bc1d963d65635d82f7083eca8a'
BUDGET={'trial_seconds':10,'observation_events':3,'same_logical_replays':1,
        'new_request_ids':0,'model_calls':0,'checkpoint_bytes':65536,'evidence_records':32,
        'max_owned_children':4,'emergency_cleanup_seconds':40}
LOCKED=('acceptance/handoff/checkpoint.py','acceptance/handoff/store.py',
        'acceptance/handoff/fixtures.py','acceptance/handoff/test_offline.py',
        'docs/schemas/handoff-checkpoint-v1.schema.json','docs/examples/handoff-checkpoint-v1.synthetic.json',
        'core.py','codex_core.py','opencode_tasks.py','contexts.py','docs/SPEC.md',
        'acceptance/handoff/evaluation/baseline.py','acceptance/handoff/evaluation/oracle.py',
        'acceptance/handoff/evaluation/world.py','acceptance/handoff/evaluation/harness.py',
        'acceptance/handoff/evaluation/profiles.json','acceptance/handoff/evaluation/schedules.json')


class Invalid(Exception):
    pass


def need(v):
    if not v:raise Invalid('HOLD: evaluation input/evidence rejected')


def encoded(v):
    return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def _pairs(items):
    value={}
    for k,v in items:need(k not in value);value[k]=v
    return value


def read_json(path,limit):
    with path.open('rb') as handle:raw=handle.read(limit+1)
    need(0<len(raw)<=limit)
    return raw,json.loads(raw.decode('ascii'),object_pairs_hook=_pairs,
                         parse_constant=lambda _v:(_ for _ in ()).throw(Invalid()))



def runtime_facts(directory):
    # Read-only statfs ABI is intentionally restricted to Linux x86_64.
    # It reads only the supplied directory descriptor; no mount paths/hostnames.
    import ctypes
    import sqlite3
    need(sys.platform=='linux' and os.uname().machine=='x86_64')
    import tempfile
    def magic(directory):
        fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            buffer=ctypes.create_string_buffer(256)
            libc=ctypes.CDLL(None,use_errno=True)
            libc.fstatfs.argtypes=[ctypes.c_int,ctypes.c_void_p];libc.fstatfs.restype=ctypes.c_int
            need(libc.fstatfs(fd,buffer)==0)
            return ctypes.c_long.from_buffer(buffer).value
        finally:os.close(fd)
    return dict(python='.'.join(map(str,sys.version_info[:3])),os=sys.platform,machine=os.uname().machine,
                kernel=os.uname().release,sqlite=sqlite3.sqlite_version,filesystem_magic=magic(directory),
                temporary_filesystem_magic=magic(tempfile.gettempdir()))



def validate_corpus():
    raw,m=read_json(HERE/'protocol.json',16384)
    need(set(m)=={'schema','kind','status','baseline_commit','candidate_commit','baseline_kind',
                  'budgets','split_sizes','source_files','candidate_mutable','heldout_requires_development','runtime_binding'})
    need(m['schema']==1 and type(m['schema']) is int and m['kind']=='paired-recovery-protocol'
         and m['status']=='PREPARED_NOT_RUN' and m['baseline_commit']==BASELINE and m['candidate_commit']==CANDIDATE
         and m['baseline_kind']=='scripted_client_reference_not_runtime' and m['candidate_mutable'] is False
         and m['heldout_requires_development'] is True and encoded(m['budgets'])==encoded(BUDGET)
         and m['split_sizes']=={'development':100,'heldout':100})
    need(m['runtime_binding'] is None or (type(m['runtime_binding']) is dict and
         set(m['runtime_binding'])=={'python','os','machine','kernel','sqlite','filesystem_magic','temporary_filesystem_magic'}))
    need(set(m['source_files'])==set(LOCKED))
    # Paths are a compiled allowlist, not values accepted from corpus data.
    for name in LOCKED:
        with (ROOT/name).open('rb') as handle:data=handle.read(262145)
        need(len(data)<=262144 and sha(data)==m['source_files'][name])
    _,schedules=read_json(HERE/'schedules.json',131072)
    _,profiles=read_json(HERE/'profiles.json',131072)
    need(type(schedules) is list and len(schedules)==200 and type(profiles) is dict)
    ids=set();configs=set();used=set()
    for row in schedules:
        need(type(row) is dict and set(row)=={'schedule_id','case','split','variant','backend','generation','profile_id'})
        need(row['case'] in [f'H{i:02d}' for i in range(1,11)] and row['split'] in ('development','heldout')
             and row['backend'] in ('hermes','opencode','codex') and type(row['generation']) is int and row['generation'] in (1,2))
        need(row['schedule_id'] not in ids);ids.add(row['schedule_id'])
        config=(row['case'],row['variant'],row['backend'],row['generation'])
        need(config not in configs);configs.add(config)
        p=profiles[row['profile_id']];used.add(row['profile_id'])
        need(set(p)=={'case','variant','backend','comparison_scope','baseline','candidate'})
        need(all(p[k]==row[k] for k in ('case','variant','backend')))
        need(p['comparison_scope']==('checkpoint_specific' if row['case'] in ('H07','H10') else 'shared_contract'))
        for arm in ('baseline','candidate'):
            expected=p[arm]
            need(set(expected)=={'action','reason','native_status','recovery_eligible','task_success_eligible'})
            need(expected['action'] in ('hold','observe_original','reconcile_original','done'))
            need(type(expected['recovery_eligible']) is bool and type(expected['task_success_eligible']) is bool)
    need(used==set(profiles))
    for split in ('development','heldout'):
        for case in [f'H{i:02d}' for i in range(1,11)]:
            need(sum(r['split']==split and r['case']==case for r in schedules)==10)
    return raw,m,schedules,profiles


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def load_roles():
    validate_corpus() # All source pins checked before any role is imported.
    c=load_module('checkpoint',ROOT/'acceptance/handoff/checkpoint.py')
    s=load_module('store',ROOT/'acceptance/handoff/store.py')
    f=load_module('fixtures',ROOT/'acceptance/handoff/fixtures.py')
    return (c,s,f),load_module('eval_baseline',HERE/'baseline.py'),load_module('eval_oracle',HERE/'oracle.py'),load_module('eval_world',HERE/'world.py')


def _decision_child(arm,world,modules,baseline,output):
    c,s,_=modules
    try:
        if arm=='baseline':result=baseline.decide(world.dossier,world.facts)
        else:
            raw=world.raw
            if world.storage_action:
                with s.Store(world.store_root) as store:
                    if world.storage_action=='replay':store.append(raw)
                    raw=encoded(store.head(world.envelope['payload']['chain_id']))
            result=asdict(c.plan(raw,world.facts))
        output.send_bytes(encoded(result))
    except c.Hold as error:
        output.send_bytes(encoded(dict(action='hold',reason=error.code,native_status=None,job_id=None,authorizes_actions=False)))
    except Exception:
        output.send_bytes(encoded(dict(action='hold',reason='HARNESS_ERROR',native_status=None,job_id=None,authorizes_actions=False)))
    finally:output.close()


class Deadline(Exception):
    pass


@contextmanager
def trial_deadline():
    previous=signal.getsignal(signal.SIGALRM)
    def expired(_s,_f):raise Deadline()
    signal.signal(signal.SIGALRM,expired);signal.alarm(10)
    try:yield
    finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)


def run_trial(schedule,arm,profile,roles):
    modules,baseline,oracle,wm=roles
    world=wm.World(schedule,modules);child=None;recv=None
    decision=dict(action='hold',reason='HARNESS_ERROR',native_status=None,job_id=None,authorizes_actions=False)
    proof=dict(effects=1,requests=1,artifact_verified=False,terminal_status=None,verifier_passed=False)
    start=time.monotonic();recovery=None;timed_out=False;cleanup=False
    try:
        with trial_deadline():
            world.prepare();before=world.fixture.effects()
            recv,send=mp.get_context('fork').Pipe(False)
            child=mp.get_context('fork').Process(target=_decision_child,args=(arm,world,modules,baseline,send))
            child.start();send.close()
            need(recv.poll(max(0,10-(time.monotonic()-start))))
            raw=recv.recv_bytes(4096);decision=json.loads(raw.decode('ascii'),object_pairs_hook=_pairs)
            child.join(max(0,10-(time.monotonic()-start)));need(child.exitcode==0)
            proof=world.proof()
    except Deadline:timed_out=True
    except Exception:world.events.append('harness_failure')
    finally:
        # Direct fixture children only. Emergency teardown is bounded separately;
        # any overrun/unknown stop fails the trial; never grant a successful retry.
        if child:
            if child.is_alive():child.terminate();child.join(5)
            if child.is_alive():child.kill();child.join(5)
            cleanup=not child.is_alive()
            if cleanup:child.close()
        if recv:recv.close()
        cleanup=world.close() and (cleanup or child is None)
    end=time.monotonic();elapsed=end-start
    recovery=None if world.fault_at is None else end-world.fault_at
    timed_out=timed_out or elapsed>10
    evidence=dict(reached_fault=world.reached,effects_before=locals().get('before',1),effects_after=proof['effects'],
                  forbidden_actions=0,cleanup_confirmed=cleanup,observations=world.observations,
                  replays=0,new_request_ids=max(0,proof['requests']-1),elapsed_seconds=elapsed,
                  expected_job_id='job_fixture_001',terminal_status=proof['terminal_status'],
                  artifact_verified=proof['artifact_verified'],verifier_passed=proof['verifier_passed'],
                  timed_out=timed_out,recovery_seconds=recovery)
    return dict(schedule_id=schedule['schedule_id'],case=schedule['case'],split=schedule['split'],arm=arm,
                comparison_scope=profile['comparison_scope'],metrics=oracle.assess(profile[arm],decision,evidence),
                evidence=evidence,decision=decision,profile_id=schedule['profile_id'],config_sha256=sha(encoded(schedule)),
                trace=dict(events=world.events,sha256=sha(encoded(world.events))))


def validate_records(rows,schedules,profiles,oracle,split):
    expected={(r['schedule_id'],arm):r for r in schedules if r['split']==split for arm in ('baseline','candidate')}
    seen=set()
    need(type(rows) is list and len(rows)==len(expected)==200)
    for row in rows:
        key=(row['schedule_id'],row['arm']);need(key in expected and key not in seen);seen.add(key)
        s=expected[key];p=profiles[s['profile_id']]
        need(row['case']==s['case'] and row['split']==split and row['profile_id']==s['profile_id']
             and row['config_sha256']==sha(encoded(s)) and row['comparison_scope']==p['comparison_scope'])
        need(set(row['trace'])=={'events','sha256'} and row['trace']['sha256']==sha(encoded(row['trace']['events'])))
        need(row['metrics']==oracle.assess(p[row['arm']],row['decision'],row['evidence']))
    oracle.aggregate(rows) # Exact row schema is independently checked here.
    return all(row['metrics']['correct'] for row in rows)


def read_development(receipt_path,manifest_sha,schedules,profiles,oracle):
    _,receipt=read_json(receipt_path,4*1024**2)
    need(set(receipt)=={'kind','manifest_sha256','split','rows','rows_sha256','summary','threshold_passed',
                        'model_comparison','human_comparison','tokens_per_verified_success'})
    need(receipt['kind']=='paired-recovery-fixture-receipt' and receipt['manifest_sha256']==manifest_sha
         and receipt['split']=='development' and receipt['rows_sha256']==sha(encoded(receipt['rows'])))
    need(validate_records(receipt['rows'],schedules,profiles,oracle,'development'))
    need(receipt['threshold_passed'] is True and receipt['summary']==oracle.aggregate(receipt['rows']))
    return receipt


def main():
    class Parser(argparse.ArgumentParser):
        def error(self,_message):self.exit(2,'HOLD: invalid evaluation arguments\n')
    parser=Parser()
    parser.add_argument('mode',choices=('validate','development','heldout'),nargs='?',default='validate')
    parser.add_argument('--output-root');parser.add_argument('--development-receipt')
    args=parser.parse_args()
    try:
        raw,manifest,schedules,profiles=validate_corpus()
        if args.mode=='validate':
            need(args.output_root is None and args.development_receipt is None)
            print(json.dumps(dict(status='PREPARED_NOT_RUN',schedules=200,proposed_arm_trials=400,manifest_sha256=sha(raw))))
            return 0
        need(sys.platform=='linux' and args.output_root is not None)
        roles=load_roles();oracle=roles[2]
        if args.mode=='heldout':
            need(args.development_receipt is not None)
            read_development(Path(args.development_receipt),sha(raw),schedules,profiles,oracle)
        else:need(args.development_receipt is None)
        need(manifest['runtime_binding'] is not None)
        out=Path(args.output_root)
        need(runtime_facts(out.parent)==manifest['runtime_binding'])
        out.mkdir(mode=0o700,exist_ok=False)
        rows=[]
        # Persist each result before starting the next arm. A partial journal
        # cannot become a passing receipt; aborts retain a bounded UNKNOWN row.
        journal=os.open(out/'records.jsonl',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(journal,'wb') as handle:
            for schedule in schedules:
                if schedule['split']!=args.mode:continue
                for arm in ('baseline','candidate'):
                    try:
                        row=run_trial(schedule,arm,profiles[schedule['profile_id']],roles)
                        line=encoded(row);need(len(line)<=16384)
                    except Exception:
                        line=encoded(dict(kind='aborted_trial',schedule_id=schedule['schedule_id'],
                                          arm=arm,stage='EVIDENCE_VALIDATION',outcome='UNKNOWN'))
                        handle.write(line+b'\n');handle.flush();os.fsync(handle.fileno());raise
                    rows.append(row)
                    handle.write(line+b'\n');handle.flush();os.fsync(handle.fileno())
        passed=validate_records(rows,schedules,profiles,oracle,args.mode)
        receipt=dict(kind='paired-recovery-fixture-receipt',manifest_sha256=sha(raw),split=args.mode,
                     rows=rows,rows_sha256=sha(encoded(rows)),summary=oracle.aggregate(rows),threshold_passed=passed,
                     model_comparison='NOT_TESTED',human_comparison='NOT_TESTED',tokens_per_verified_success='NOT_APPLICABLE')
        data=encoded(receipt);need(len(data)<=4*1024**2)
        fd=os.open(out/'receipt.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
        print(json.dumps(dict(split=args.mode,rows=len(rows),threshold_passed=passed,receipt_sha256=sha(data))))
        return 0 if passed else 2
    except Exception:
        print('HOLD: evaluation input, trial or receipt incomplete; no retry')
        return 2


if __name__=='__main__':sys.exit(main())
