"""Mandatory real identity transitions/PID reuse in disposable Linux CI namespaces.

Never write ns_last_pid until PID 1, distinct PID/mount namespaces and coherent
new procfs are proved. No host sysctl/account/service, inventory worker or operator
process is changed. All signals use a separate test-owner pidfd, not the observed
ReadOnlyWorker's handle. Missing namespace capability is a failed control, no skip.
"""
import json
import hashlib
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import types

HERE=Path(__file__).resolve().parent


def require(value):
    if not value: raise RuntimeError('identity namespace control incomplete; no fallback')


def ci_guard():
    require(os.geteuid()==0 and os.environ.get('GITHUB_ACTIONS')=='true'
            and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted'
            and os.environ.get('RUNNER_OS')=='Linux')


def inner(outer_pid,outer_mount):
    ci_guard()
    require(os.getpid()==1 and os.stat('/proc/self/ns/pid').st_ino!=outer_pid
            and os.stat('/proc/self/ns/mnt').st_ino!=outer_mount
            and int(Path('/proc/self/stat').read_text().split()[0])==1)
    def expired(*_): raise RuntimeError('namespace fixture deadline')
    signal.signal(signal.SIGTERM,expired)
    signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,35)
    sys.path.insert(0,str(HERE))
    import observer_guest as guest
    guest.P=guest._load_observation_protocol()
    p=guest.P
    sleep=str(Path(shutil.which('sleep')).resolve(strict=True))
    def spawn(mode):
        script=("import os,sys,signal; signal.signal(signal.SIGALRM,signal.SIG_DFL); "
                "signal.setitimer(signal.ITIMER_REAL,10); print('ready',flush=True); "
                "assert os.read(0,1)==b'G'; ")
        if mode=='exec': script+=f'os.execv({sleep!r},[{sleep!r},"10"])'
        elif mode=='uid':
            script+="os.setgroups([]); os.setresgid(65534,65534,65534); os.setresuid(65534,65534,65534); print('changed',flush=True); signal.pause()"
        else: script+='signal.pause()'
        child=subprocess.Popen([sys.executable,'-I','-S','-B','-c',script],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        control=None
        worker=None
        try:
            require(select.select([child.stdout],[],[],3)[0])
            require(child.stdout.readline()==b'ready\n')
            identity=p.identity(child.pid)
            require(identity['ppid']==os.getpid())
            control=os.pidfd_open(child.pid) # Test actor owns this direct Popen child.
            worker=guest.ReadOnlyWorker(child.pid,p.fingerprint(identity),
                types.SimpleNamespace(pid=os.getpid()),sys.executable)
            require(worker.live() and p.live(control))
            return child,control,worker
        except BaseException:
            if control is not None and child.poll() is None: signal.pidfd_send_signal(control,signal.SIGTERM)
            elif child.poll() is None: child.terminate() # Popen-owned fixture before adoption only.
            child.wait(timeout=3)
            for stream in (child.stdin,child.stdout,child.stderr): stream.close()
            if control is not None: os.close(control)
            if worker is not None: os.close(worker.fd)
            raise
    def cleanup(item):
        child,control,worker=item
        if child.poll() is None: signal.pidfd_send_signal(control,signal.SIGTERM)
        child.wait(timeout=3)
        for stream in (child.stdin,child.stdout,child.stderr): stream.close()
        os.close(control); os.close(worker.fd)
    def emit(case,**evidence):
        print(json.dumps({'evidence_class':'real-identity-private-namespace','case':case,
            'identity_rejected':True,'r1_complete':False,'r2_authorized':False,
            'scope_granted':False,**evidence}),flush=True)
    item=spawn('exec')
    try:
        child,control,worker=item
        child.stdin.write(b'G'); child.stdin.flush()
        deadline=time.monotonic()+3
        current=p.identity(child.pid)
        while current['exe']!=sleep:
            require(time.monotonic()<deadline and p.live(control))
            time.sleep(0.005) # Identity-fixture polling only; no inventory/collect runs.
            current=p.identity(child.pid)
        require(p.live(worker.fd) and current['pid']==worker.saved['pid']
                and current['start_ticks']==worker.saved['start_ticks']
                and current['argv']!=worker.saved['argv'] and not worker.live())
        emit('real_exec',same_pid=True,same_start_ticks=True,exe_and_argv_changed=True)
    finally: cleanup(item)
    item=spawn('uid')
    try:
        child,control,worker=item
        child.stdin.write(b'G'); child.stdin.flush()
        require(select.select([child.stdout],[],[],3)[0])
        require(child.stdout.readline()==b'changed\n')
        require(Path('/proc',str(child.pid)).stat().st_uid==65534 and p.live(worker.fd))
        unreadable=False
        try: accepted=worker.live()
        except (PermissionError,p.Hold): accepted=False; unreadable=True
        require(accepted is False)
        emit('real_uid_drop',worker_still_live=True,real_uid_changed=True,identity_unreadable=unreadable)
    finally: cleanup(item)
    old=spawn('wait')
    new=None
    try:
        child,control,worker=old
        before=dict(worker.saved)
        signal.pidfd_send_signal(control,signal.SIGTERM); child.wait(timeout=3)
        require(not p.live(worker.fd) and not worker.live())
        time.sleep(0.03) # Separate identity-fixture start ticks; no collect is running.
        # Guard again immediately before the only namespaced kernel write.
        require(os.getpid()==1 and os.stat('/proc/self/ns/pid').st_ino!=outer_pid
                and os.stat('/proc/self/ns/mnt').st_ino!=outer_mount
                and int(Path('/proc/self/stat').read_text().split()[0])==1)
        Path('/proc/sys/kernel/ns_last_pid').write_text(str(before['pid']-1))
        new=spawn('wait')
        after=p.identity(new[0].pid)
        require(after['pid']==before['pid'] and after['start_ticks']!=before['start_ticks'])
        require(new[2].live() and not worker.live() and not p.live(worker.fd))
        emit('real_pid_reuse',numeric_pid_reused=True,start_ticks_changed=True,
             replacement_live=True,old_handle_dead=True)
    finally:
        if new is not None: cleanup(new)
        cleanup(old)
    signal.setitimer(signal.ITIMER_REAL,0)
    print('Identity namespace controls: 3 cases passed; real exec/UID/reuse; private namespaces only',flush=True)
    return 0


def main():
    ci_guard()
    if len(sys.argv)==4 and sys.argv[1]=='--inner':
        return inner(int(sys.argv[2]),int(sys.argv[3]))
    require(len(sys.argv)==1 and os.getpid()!=1)
    unshare=shutil.which('unshare'); require(unshare is not None)
    outer_pid=os.stat('/proc/self/ns/pid').st_ino
    outer_mount=os.stat('/proc/self/ns/mnt').st_ino
    with tempfile.TemporaryDirectory(prefix='s24-identity-source-') as directory:
        copy=Path(directory)
        pins={'observer_guest.py':'2bb14cadd9cebb676041ae2f8bcba2d54c2721c2725a50c7d64bc4bbfbf3372c',
              'observation_protocol.py':'34100540890928ac24e621543aee01abc0026e10c43d95c346e57b371894fc2f'}
        for name,digest in pins.items():
            raw=(HERE/name).read_bytes(); require(hashlib.sha256(raw).hexdigest()==digest)
            (copy/name).write_bytes(raw); (copy/name).chmod(0o600)
        # Root-owned NEW copies satisfy the unchanged loader's owner gate. Do
        # not chown/chmod the checkout or relax any source predicate.
        script=copy/Path(__file__).name
        script.write_bytes(Path(__file__).read_bytes()); script.chmod(0o600)
        result=subprocess.run([unshare,'--mount','--pid','--fork','--kill-child','--mount-proc',
            '--propagation','private',sys.executable,'-W','error::ResourceWarning','-I','-S','-B',str(script),
            '--inner',str(outer_pid),str(outer_mount)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            timeout=45,check=False)
    sys.stdout.buffer.write(result.stdout); sys.stdout.buffer.flush()
    warnings=[m.decode() for m in (b'ResourceWarning',b'Exception ignored in',b'Exception ignored while finalizing')
              if m in result.stdout]
    print(json.dumps({'namespace_exit':result.returncode,'warning_markers':warnings}),flush=True)
    require(not warnings and result.returncode==0 and result.stdout.count(b'Identity namespace controls: 3 cases passed;')==1)
    return 0


if __name__=='__main__': raise SystemExit(main())
