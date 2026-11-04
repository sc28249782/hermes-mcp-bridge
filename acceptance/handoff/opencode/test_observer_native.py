"""Owned native integration controls; no real backend, credentials or Dev state."""
from dataclasses import asdict,replace
import ast
import ctypes
import hashlib
import json
import os
import platform
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
from acceptance.handoff.opencode import observer_native as N,observer_preflight as P,observer_startup as S
SOURCE=Path(__file__).resolve().parent
LOSS_PHASES=('nonreading','read_lock','first_frame','complete_prefix')
LOSS_CASES={f'both_{phase}_{order}':(phase,order)
            for phase in LOSS_PHASES for order in ('os','so')}


def loss_shim(phase):
    """TEST ONLY: actual C phase barrier; no extra actor or source mutation.

    198 is the private phase write end, 199 a never-released read barrier.
    They are explicitly retained only by test hooks. read_lock keeps the native
    1-second alarm; other barriers have no fresh native alarm or source timer.
    """
    preamble='#define _GNU_SOURCE\n#include <unistd.h>\n#include <string.h>\n'
    preamble+='static ssize_t fixture_write(int,const void*,size_t);\n'
    preamble+='#define write fixture_write\n#define main accepted_main\n'
    if phase=='read_lock':preamble+='#define OC_CONTROL_BUILD\n'
    preamble+='#include "'+str(SOURCE/'oc_snapshot_vfs.c')+'"\n#undef main\n#undef write\n'
    barrier='static void phase_ready(void){if(write(198,"B",1)!=1)_exit(93);char c;if(read(199,&c,1)!=1)_exit(94);_exit(95);}\n'
    notify='static ssize_t fixture_write(int f,const void*p,size_t n){'
    if phase=='read_lock':
        notify+='if(f==2&&n==18&&!memcmp(p,"CONTROL_READ_LOCK\\n",18)){phase_ready();}'
    notify+='ssize_t r=write(f,p,n);'
    if phase=='first_frame':notify+='if(f==1&&n>4&&r==(ssize_t)n)phase_ready();'
    notify+='return r;}\n'
    main='int main(int n,char**v){signal(SIGTERM,SIG_IGN);'
    if phase=='nonreading':main+='phase_ready();'
    if phase=='read_lock':main+='releasefd=199;'
    main+='int r=accepted_main(n,v);if(r)return r;'
    if phase=='complete_prefix':main+='phase_ready();'
    main+='return 0;}\n'
    return preamble+barrier+notify+main


def setting():
    libc=ctypes.CDLL(None);value=ctypes.c_int()
    libc.prctl.argtypes=[ctypes.c_int]+[ctypes.c_ulong]*4
    if libc.prctl(37,ctypes.addressof(value),0,0,0)!=0:raise AssertionError('subreaper query')
    return value.value


def kill(child):
    signal.pidfd_send_signal(child.pidfd,signal.SIGKILL)
    if not select.select([child.pidfd],[],[],1)[0]:raise AssertionError('actor did not exit')


def fixture(directory):
    text=(SOURCE/'native_schema.h').read_text()
    schemas=[ast.literal_eval(line.split(' = ',1)[1].rstrip(';')) for line in text.splitlines() if line.startswith('static const char schema_')]
    values=('oct_fixture','req_fixture','ses_fixture','fixture/model','fixture_workspace',
            'fixture_binary','f'*64,'completed',0,'fixture_log',65536,'worker','response_completed',0)
    names=('job_id','request_id','session_id','model','workspace','binary','fingerprint','status','exit_code',
           'log_path','max_output_bytes','transition_actor','transition_reason','cancel_flag')
    for filename,sql in zip(('opencode-tasks.sqlite3','contexts.sqlite3'),schemas):
        path=directory/filename
        db=sqlite3.connect(path)
        try:
            db.execute(sql)
            if filename.startswith('opencode'):
                row=dict(zip(names,values),created=1,prompt='PRIVATE_NATIVE_PROMPT',err_path='fixture_err',max_runtime_seconds=10)
                db.execute('INSERT INTO jobs('+','.join(row)+') VALUES ('+','.join('?' for _ in row)+')',tuple(row.values()))
            else:db.execute("INSERT INTO contexts(context_id,label,created,updated) VALUES ('ctx_fixture','fixture',1,1)")
            db.commit()
        finally:db.close()
        path.chmod(0o600)
    return N.frame_digest((('ctx_fixture',None),values,('ctx_fixture',None)))


class NativeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=tempfile.TemporaryDirectory(prefix='oa-native-build-')
        cls.addClassCleanup(cls.build.cleanup)
        cls.helper=Path(cls.build.name)/'native'
        compile=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O2',str(SOURCE/'oc_snapshot_vfs.c'),
            '/lib/x86_64-linux-gnu/libsqlite3.so.0','-o',str(cls.helper)],capture_output=True,timeout=20)
        if compile.returncode:raise AssertionError(compile.stderr.decode())
        cls.helper.chmod(0o700)
        cls.helpers={}
        for name,tail in (('nonzero','return 2;'),('trailing','if(write(1,"X",1)!=1)return 3;return 0;'),
                          ('late_stderr','if(write(2,"X",1)!=1)return 3;return 0;'),
                          ('hang','signal(SIGTERM,SIG_IGN);for(;;)pause();'),
                          ('native_s_loss','signal(SIGTERM,SIG_IGN);int p=syscall(SYS_pidfd_open,getppid(),0);if(p<0)return 3;if(syscall(SYS_pidfd_send_signal,p,SIGKILL,0,0))return 3;close(p);for(;;)pause();')):
            shim=Path(cls.build.name)/(name+'.c');target=Path(cls.build.name)/name
            shim.write_text('#define main accepted_main\n#include "'+str(SOURCE/'oc_snapshot_vfs.c')+'"\n#undef main\n#include <sys/syscall.h>\nint main(int n,char**v){int r=accepted_main(n,v);if(r)return r;'+tail+'}\n')
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O2',str(shim),
                '/lib/x86_64-linux-gnu/libsqlite3.so.0','-o',str(target)],check=True,capture_output=True,timeout=20)
            target.chmod(0o700);cls.helpers[name]=target
        for phase in LOSS_PHASES:
            shim=Path(cls.build.name)/(phase+'.c');target=Path(cls.build.name)/phase
            shim.write_text(loss_shim(phase))
            result=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O2',str(shim),
                '/lib/x86_64-linux-gnu/libsqlite3.so.0','-o',str(target)],capture_output=True,timeout=20)
            if result.returncode:raise AssertionError(result.stderr.decode())
            target.chmod(0o700)
            for case,(selected,_) in LOSS_CASES.items():
                if selected==phase:cls.helpers[case]=target
        facts=subprocess.run([str(cls.helper),'--build-facts'],capture_output=True,check=True,timeout=2)
        if not facts.stdout.startswith(b'SQLite=3.45.1\n'):raise AssertionError('unsupported native SQLite fixture build')
        print(json.dumps({'kind':'offline-native-build','source_sha256':hashlib.sha256((SOURCE/'oc_snapshot_vfs.c').read_bytes()).hexdigest(),
            'helper_sha256':hashlib.sha256(cls.helper.read_bytes()).hexdigest(),
            'library_sha256':hashlib.sha256(Path('/lib/x86_64-linux-gnu/libsqlite3.so.0').read_bytes()).hexdigest(),
            'python':platform.python_version(),'native_sqlite':'3.45.1',
            'compiler':subprocess.run(['cc','--version'],capture_output=True,check=True,timeout=2).stdout.decode().splitlines()[0],
            'authenticity_verified':False,'dev_observed':False}),flush=True)

    @classmethod
    def tearDownClass(cls):cls.build.cleanup()

    def trial(self,case='normal'):
        parent_setting=setting()
        with tempfile.TemporaryDirectory(prefix='oa-native-case-') as tmp:
            base=Path(tmp);state=base/'state';state.mkdir(mode=0o700)
            claim=base/'claim';claim.mkdir(mode=0o700)
            expected=fixture(state)
            if case=='sidecar':
                p=state/'opencode-tasks.sqlite3-wal';p.write_bytes(b'');p.chmod(0o600)
            if case in ('missing_job','wrong_status','extra_schema','open_context'):
                target=state/('contexts.sqlite3' if case=='open_context' else 'opencode-tasks.sqlite3')
                db=sqlite3.connect(target)
                try:
                    db.execute({'missing_job':"DELETE FROM jobs",'wrong_status':"UPDATE jobs SET status='running'",
                        'extra_schema':"CREATE TABLE extra(x)",'open_context':"UPDATE contexts SET closed=1"}[case]);db.commit()
                finally:db.close()
            before={p.name:p.read_bytes() for p in state.iterdir()}
            read,write=os.pipe2(os.O_CLOEXEC)
            rpid=os.fork()
            if rpid==0:
                S._close_except((write,))
                try:
                    rootfd=os.open(state,os.O_RDONLY|os.O_DIRECTORY)
                    claimfd=os.open(claim,os.O_RDONLY|os.O_DIRECTORY)
                    helper=self.helpers.get(case,self.helper)
                    helperfd=os.open(helper,os.O_RDONLY|os.O_NOFOLLOW)
                    jobfd=os.open(state/'opencode-tasks.sqlite3',os.O_RDONLY|os.O_NOFOLLOW)
                    ctxfd=os.open(state/'contexts.sqlite3',os.O_RDONLY|os.O_NOFOLLOW)
                    dummy_r,dummy_w=os.pipe2(os.O_CLOEXEC)
                    bundle=N.FixtureBundle(rootfd,helperfd,jobfd,ctxfd,hashlib.sha256(helper.read_bytes()).hexdigest(),expected)
                    issuer=P.FixtureIssuer(claimfd,1)
                    binding=P.Binding('attempt_fixture','nonce_fixture',1,hashlib.sha256((SOURCE/'observer_native.py').read_bytes()).hexdigest(),
                        expected,P.SCOPES,'fixture-owned-cleanup',time.monotonic(),time.monotonic()+40)
                    if case=='unbound':binding=replace(binding,containment='UNBOUND')
                    if case=='dev':binding=replace(binding,environment='dev')
                    if case=='source_drift':binding=replace(binding,source_sha256='a'*64)
                    if case=='oracle_binding':binding=replace(binding,dossier_sha256='a'*64)
                    if case=='helper_hash':bundle=replace(bundle,helper_sha256='a'*64)
                    issuer.register(binding,dummy_r)
                    # Test-private inherited descriptors; normal source keeps
                    # none of these. No watchdog/observer process is added.
                    loss=case in LOSS_CASES
                    phase_r=phase_w=block_r=block_w=None
                    if loss:
                        phase_r,phase_w=os.pipe2(os.O_CLOEXEC)
                        block_r,block_w=os.pipe2(os.O_CLOEXEC)
                        os.dup2(phase_w,198,inheritable=True);os.dup2(block_r,199,inheritable=True)
                    original_close=S._close_except
                    def closing(keep):
                        return original_close((*keep,198,199) if loss else keep)
                    stimulus={'phase_seen':False,'both_exited':False,'h_live_after_loss':False}
                    native_ack=N.NativeRun._ack;native_go=N.NativeRun._go
                    native_emit=N._emit;native_retain=N.NativeRun._retain
                    native_entry=N._native_entry;native_read=N.os.read
                    native_supervisor=N._native_supervisor;fragment_fd=[None]
                    native_exec=N.os.execve
                    def execute(fd,argv,env):
                        if case=='exec_failure':raise OSError('owned exec fault')
                        return native_exec(fd,argv,env)
                    native_eof=N._eof;native_clock=N.time.monotonic
                    observer=os.getpid();eofs=[0];late=[False]
                    def clock():return native_clock()+(100 if late[0] else 0)
                    def eof(fd,cap,deadline):
                        native_eof(fd,cap,deadline)
                        if case=='late_publication' and os.getpid()==observer:
                            eofs[0]+=1
                            if eofs[0]==3:late[0]=True
                    def supervise(*args):
                        fragment_fd[0]=args[5]
                        return native_supervisor(*args)
                    def ack(self,fd):
                        if case=='s_before_ack':kill(self.s)
                        if case=='revoke':self.issuer.revoke(self.ref)
                        if case=='stall_ack':return
                        return native_ack(self,fd)
                    def go(self,fd):
                        if case=='owner_loss':kill(self.o)
                        native_go(self,fd)
                        if loss:
                            if not select.select([phase_r],[],[],1)[0] or os.read(phase_r,1)!=b'B':
                                raise AssertionError('actual native phase not reached')
                            if S._ready(self.h.pidfd):raise AssertionError('H exited before loss stimulus')
                            stimulus['phase_seen']=True
                            actors={'o':self.o,'s':self.s}
                            # Back-to-back retained-pidfd sends, with no reap/
                            # wait between them. Both deaths precede return to R.
                            for role in LOSS_CASES[case][1]:
                                signal.pidfd_send_signal(actors[role].pidfd,signal.SIGKILL)
                            cutoff=time.monotonic()+1
                            for child in (self.o,self.s):
                                if not S._until(child.pidfd,cutoff):raise AssertionError('O/S loss not confirmed')
                            stimulus['both_exited']=True
                            if S._ready(self.h.pidfd):raise AssertionError('H already stopped at adoption boundary')
                            stimulus['h_live_after_loss']=True
                    def retain(self,witness):
                        if case=='s_before_retain':kill(self.s)
                        if case=='pidfd_failure':
                            with mock.patch.object(S.os,'pidfd_open',side_effect=OSError()):return native_retain(self,witness)
                        return native_retain(self,witness)
                    def emit(fd,value):
                        if value['kind']=='witness' and case=='bad_witness':value=dict(value,nonce='wrong')
                        if value['kind']=='final' and case=='missing_final':os._exit(91)
                        if value['kind']=='final' and case=='bad_final':value=dict(value,helper_reaped='true')
                        return native_emit(fd,value)
                    def entry(gate,output,error,b,cutoff):
                        if case in ('s_after_g','stderr','partial','overcap'):
                            if S._byte(gate,cutoff)!=b'G':raise AssertionError('gate')
                            if case=='stderr':os.write(error,b'BAD');return
                            if case=='partial':os.write(output,b'\x00\x00\x00\x20prefix');return
                            if case=='overcap':os.write(output,(65537).to_bytes(4,'big'));return
                            # Test-only actual S crash after actual G receipt.
                            signal.signal(signal.SIGTERM,signal.SIG_IGN)
                            sfd=os.pidfd_open(os.getppid());signal.pidfd_send_signal(sfd,signal.SIGKILL);os.close(sfd)
                            while True:signal.pause()
                        native_entry(gate,output,error,b,cutoff)
                    def fragmented(fd,size):
                        return native_read(fd,min(size,1)) if case=='fragmented_reads' and fd==fragment_fd[0] else native_read(fd,size)
                    # SQLite writer lock is held only in this fresh fixture R.
                    lock=None
                    if case=='exclusive_lock':
                        lock=sqlite3.connect(state/'opencode-tasks.sqlite3');lock.execute('BEGIN EXCLUSIVE')
                    try:
                        with mock.patch.object(N.NativeRun,'_ack',ack),mock.patch.object(N.NativeRun,'_go',go), \
                             mock.patch.object(N.NativeRun,'_retain',retain),mock.patch.object(N,'_emit',side_effect=emit), \
                             mock.patch.object(N,'_native_entry',side_effect=entry),mock.patch.object(N.os,'read',side_effect=fragmented), \
                             mock.patch.object(N,'_native_supervisor',side_effect=supervise),mock.patch.object(N,'_eof',side_effect=eof), \
                             mock.patch.object(N.time,'monotonic',side_effect=clock),mock.patch.object(N.os,'execve',side_effect=execute), \
                             mock.patch.object(S,'_close_except',side_effect=closing),mock.patch.object(N,'_close_except',side_effect=closing):
                            run=N.NativeRun(issuer,binding.attempt_ref,bundle,3.5 if case in ('stall_ack','hang') else 8)
                            result=run.run()
                            if case=='reuse':
                                try:run.run()
                                except P.Hold as error:
                                    if error.reason!='ATTEMPT_CONSUMED':raise
                                else:raise AssertionError('reuse accepted')
                            try:issuer.reserve(binding.attempt_ref)
                            except P.Hold:pass
                            else:raise AssertionError('duplicate reservation')
                    finally:
                        if lock is not None:lock.rollback();lock.close()
                    try:os.waitpid(-1,os.WNOHANG)
                    except ChildProcessError:no_children=True
                    else:raise AssertionError('fixture child remains')
                    value={'outcome':asdict(result),'no_children':no_children,'claims':len(list(claim.iterdir()))}
                    if loss:
                        if not all(stimulus.values()):raise AssertionError('loss stimulus incomplete')
                        value['native_loss_stimulus']=dict(phase=LOSS_CASES[case][0],order=LOSS_CASES[case][1],**stimulus)
                        for fd in (phase_r,phase_w,block_r,block_w,198,199):os.close(fd)
                    issuer.close()
                    for fd in (rootfd,claimfd,helperfd,jobfd,ctxfd,dummy_r,dummy_w):os.close(fd)
                    raw=json.dumps(value,sort_keys=True).encode()+b'\n'
                    if len(raw)>4096 or os.write(write,raw)!=len(raw):os._exit(4)
                    os._exit(0)
                except BaseException as error:
                    os.write(write,json.dumps({'test_error':type(error).__name__}).encode()+b'\n');os._exit(3)
            os.close(write);rfd=os.pidfd_open(rpid)
            try:
                self.assertTrue(select.select([rfd],[],[],15)[0],'fixture R timed out')
                pid,status=os.waitpid(rpid,0);self.assertEqual(pid,rpid)
                raw=os.read(read,4096);self.assertEqual(os.waitstatus_to_exitcode(status),0,raw)
                self.assertEqual(os.read(read,1),b'')
                value=json.loads(raw);self.assertTrue(value['no_children']);self.assertEqual(setting(),parent_setting)
                self.assertEqual(before,{p.name:p.read_bytes() for p in state.iterdir()})
                for flag in ('capture_allowed','authorizes_actions','dev_observed','goal_verified'):self.assertIs(value['outcome'][flag],False)
                for private in ('nonce_fixture','attempt_fixture',tmp,'PRIVATE_NATIVE_PROMPT','fixture_workspace','f'*64):self.assertNotIn(private,raw.decode())
                print(json.dumps({'kind':'offline-native-result','case':case,**value},sort_keys=True),flush=True)
                return value['outcome'],value['claims']
            finally:os.close(rfd);os.close(read)

    def test_native_context_job_context_requires_original_final_reap_and_eof(self):
        r,c=self.trial();self.assertEqual(r['state'],'OFFLINE_NATIVE_FIXTURE_CONFIRMED');self.assertEqual(c,1)
        self.assertEqual(r['trace'],['CLAIM','SUBREAPER','OWNER','SUPERVISOR','WITNESS','PIDFD','ACK','ACKED','NATIVE_FIXTURE_G','FINAL'])
        self.assertIs(r['original_final'],True);self.assertEqual(r['helper_reaped_by'],'S')
        self.assertIs(r['stdout_eof'],True);self.assertIs(r['stderr_eof'],True);self.assertEqual(r['actors_reaped'],2)

    def negative(self,case,go=None):
        r,c=self.trial(case);self.assertNotEqual(r['state'],'OFFLINE_NATIVE_FIXTURE_CONFIRMED');self.assertFalse(r['original_final'])
        if go is not None:self.assertIs(r['fixture_g_sent'],go)
        return r,c

    def test_unbound_has_no_claim_or_launch(self):
        r,c=self.negative('unbound',False);self.assertEqual(c,0);self.assertEqual(r['trace'],[])
    def test_dev_cannot_select_fixture_profile(self):self.negative('dev',False)
    def test_source_drift_consumes_without_actors(self):
        r,c=self.negative('source_drift',False);self.assertEqual(c,1);self.assertEqual(r['actors_reaped'],0)
    def test_oracle_binding_mismatch_before_actors(self):
        r,c=self.negative('oracle_binding',False);self.assertEqual(c,1);self.assertEqual(r['actors_reaped'],0)
    def test_wrong_helper_digest_before_actors(self):self.negative('helper_hash',False)
    def test_wrong_nonce_prevents_ack(self):
        r,_=self.negative('bad_witness',False);self.assertNotIn('ACK',r['trace'])
    def test_revoke_before_ack(self):self.negative('revoke',False)
    def test_s_loss_before_ack_adopts_only_cleanup(self):
        r,_=self.negative('s_before_ack',False);self.assertEqual(r['helper_reaped_by'],'R')
    def test_s_loss_before_retain_can_only_bind_cleanup(self):
        r,_=self.negative('s_before_retain',False);self.assertEqual(r['helper_reaped_by'],'R')
    def test_pidfd_failure_no_retry_or_numeric_fallback(self):
        r,_=self.negative('pidfd_failure',False);self.assertEqual(r['reason'],'STOP_UNCONFIRMED')
    def test_owner_loss_before_g(self):self.negative('owner_loss',False)
    def test_shared_cutoff_stalled_ack(self):self.negative('stall_ack',False)
    def test_actual_s_death_after_actual_g_leaves_unknown(self):
        r,_=self.negative('s_after_g',True);self.assertEqual(r['helper_reaped_by'],'R');self.assertIs(r['stdout_eof'],True)
    def test_native_s_reap_without_final_does_not_invent_reaper(self):
        r,_=self.negative('missing_final',True);self.assertIsNone(r['helper_reaped_by']);self.assertTrue(r['helper_exit_observed'])
    def test_string_boolean_final_rejected(self):self.negative('bad_final',True)
    def test_real_empty_wal_is_denied(self):self.negative('sidecar',True)
    def test_real_exclusive_writer_lock_denied(self):self.negative('exclusive_lock',True)
    def test_missing_original_fixture_job_denied(self):self.negative('missing_job',True)
    def test_wrong_fixture_status_rejects_oracle(self):self.negative('wrong_status',True)
    def test_changed_context_rejects_fixture_oracle(self):self.negative('open_context',True)
    def test_real_extra_schema_rejected(self):self.negative('extra_schema',True)
    def test_stderr_rejects_without_final(self):self.negative('stderr',True)
    def test_partial_success_prefix_rejected(self):self.negative('partial',True)
    def test_oversized_length_rejected_before_allocation(self):self.negative('overcap',True)
    def test_partial_pipe_reads_reassemble_exact_native_frames(self):
        r,_=self.trial('fragmented_reads');self.assertEqual(r['state'],'OFFLINE_NATIVE_FIXTURE_CONFIRMED')
    def test_consumed_object_cannot_repeat_capture(self):
        r,c=self.trial('reuse');self.assertEqual(r['state'],'OFFLINE_NATIVE_FIXTURE_CONFIRMED');self.assertEqual(c,1)
    def test_complete_native_prefix_with_nonzero_exit_rejected(self):self.negative('nonzero',True)
    def test_complete_native_frames_with_trailing_stdout_rejected(self):self.negative('trailing',True)
    def test_native_late_stderr_rejected(self):self.negative('late_stderr',True)
    def test_native_complete_prefix_then_hang_hits_same_cutoff(self):self.negative('hang',True)
    def test_actual_native_h_survives_s_death_and_is_adopted(self):
        r,_=self.negative('native_s_loss',True);self.assertEqual(r['helper_reaped_by'],'R')
        self.assertTrue(r['helper_exit_observed']);self.assertTrue(r['stdout_eof']);self.assertTrue(r['stderr_eof'])
    def test_failed_retained_fd_exec_consumes_without_retry(self):self.negative('exec_failure',True)
    def test_late_publication_cannot_publish_fixture_success(self):
        r,_=self.trial('late_publication');self.assertTrue(r['original_final'])
        self.assertEqual(r['state'],'UNKNOWN');self.assertEqual(r['reason'],'BUDGET_EXHAUSTED')

    def native_both_loss(self,phase,order):
        r,c=self.negative(f'both_{phase}_{order}',True)
        self.assertEqual(r['state'],'UNKNOWN');self.assertEqual(r['actors_reaped'],2)
        self.assertEqual(r['helper_reaped_by'],'R');self.assertIs(r['helper_exit_observed'],True)
        self.assertIs(r['stdout_eof'],True);self.assertIs(r['stderr_eof'],True)
        self.assertEqual(c,1);self.assertNotIn('FINAL',r['trace'])
    def test_both_loss_nonreading_owner_first(self):self.native_both_loss('nonreading','os')
    def test_both_loss_nonreading_supervisor_first(self):self.native_both_loss('nonreading','so')
    def test_both_loss_native_read_lock_owner_first(self):self.native_both_loss('read_lock','os')
    def test_both_loss_native_read_lock_supervisor_first(self):self.native_both_loss('read_lock','so')
    def test_both_loss_native_first_frame_owner_first(self):self.native_both_loss('first_frame','os')
    def test_both_loss_native_first_frame_supervisor_first(self):self.native_both_loss('first_frame','so')
    def test_both_loss_native_complete_prefix_owner_first(self):self.native_both_loss('complete_prefix','os')
    def test_both_loss_native_complete_prefix_supervisor_first(self):self.native_both_loss('complete_prefix','so')
    def test_hash_manifest(self):
        m=json.loads((SOURCE/'observer-native-hashes.json').read_bytes())
        for entry in m['source']+m['pinned_dependencies']:
            raw=(ROOT/entry['path']).read_bytes();self.assertEqual(len(raw),entry['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
        self.assertIs(m['authorizes_actions'],False);self.assertIs(m['dev_observed'],False)

    def test_source_exposes_no_backend_dispatch_or_numeric_stop(self):
        tree=ast.parse((SOURCE/'observer_native.py').read_text())
        calls=[ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node,ast.Call)]
        self.assertNotIn('os.kill',calls);self.assertNotIn('os.killpg',calls)
        self.assertNotIn('subprocess.Popen',calls);self.assertNotIn('V._stop',calls)
        execs=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and ast.unparse(node.func)=='os.execve']
        self.assertEqual(len(execs),1);self.assertEqual(ast.unparse(execs[0].args[0]),'bundle.helperfd')


if __name__=='__main__':unittest.main(verbosity=2)
