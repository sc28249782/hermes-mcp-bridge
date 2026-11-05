"""S24 guest observer candidate. No operator execution scope is granted."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import selectors
import signal
import stat
import subprocess
import sys
import time
# Exact checked protocol bytes, never current-directory imports.
import stat as _stat
import types as _types

def _load_observation_protocol():
    path = Path(__file__).absolute().with_name('observation_protocol.py')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not (_stat.S_ISREG(info.st_mode) and info.st_uid in (0, os.getuid())
                and info.st_nlink == 1 and not info.st_mode & 0o022 and info.st_size <= 131072):
            raise RuntimeError('protocol source')
        raw = bytearray()
        while True:
            part = os.read(fd, 131073 - len(raw))
            if not part:
                break
            raw.extend(part)
            if len(raw) > 131072:
                raise RuntimeError('protocol size')
        after = os.fstat(fd)
        if hashlib.sha256(raw).hexdigest() != '34100540890928ac24e621543aee01abc0026e10c43d95c346e57b371894fc2f' or any(
                getattr(info, key) != getattr(after, key) for key in
                ('st_dev','st_ino','st_uid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')):
            raise RuntimeError('protocol hash')
    finally:
        os.close(fd)
    module = _types.ModuleType('bound_observation_protocol')
    module.__file__ = str(path)
    exec(compile(bytes(raw), str(path), 'exec'), module.__dict__)
    return module


P=None

CONTROLLER_SHA = '13d8c0ca932c26b8af6c682116bb27e0d2a5df467ed0c33cb73cf8f0d8cc65a5'


def read_config(path):
    path = Path(path)
    P.require(path.is_absolute() and str(path) == os.path.normpath(str(path)))
    parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parent.parts[1:]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = nxt
        info = os.fstat(parent)
        P.require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700)
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            P.require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                      and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) == 0o600)
            raw = bytearray()
            while True:
                chunk = os.read(fd, 16385 - len(raw))
                if not chunk:
                    break
                raw.extend(chunk)
                P.require(len(raw) <= 16384)
            after = os.fstat(fd)
            P.require(all(getattr(before, k) == getattr(after, k) for k in
                          ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_uid','st_nlink')))
        finally:
            os.close(fd)
    finally:
        os.close(parent)
    value = P.loads(bytes(raw))
    P.require(type(value) is dict and set(value) == {
        'root','attempt_name','python_argv','controller_python','health_port','scope_start_epoch',
        'binding_sha256','challenge','log_path'})
    P.correlation(value['binding_sha256'], value['challenge'])
    P.require(value['controller_python'] == sys.executable
              and all(type(value[k]) is str and os.path.isabs(value[k])
                      and value[k] == os.path.normpath(value[k]) for k in ('root','python_argv','log_path'))
              and type(value['health_port']) is int and 1024 <= value['health_port'] <= 65535
              and value['health_port'] not in (8080,8081)
              and type(value['scope_start_epoch']) in (int,float)
              and math.isfinite(value['scope_start_epoch'])
              and 0 <= time.time()-value['scope_start_epoch'] <= 800
              and type(value['attempt_name']) is str
              and re.fullmatch(r'r1-remaining-[A-Za-z0-9_-]{1,64}',value['attempt_name']))
    return value


class ReadOnlyWorker:
    def __init__(self, pid, digest, controller, expected_exe):
        before = P.identity(pid)
        P.require(before['ppid'] == controller.pid and before['uid'] == os.getuid()
                  and before['exe'] == str(Path(expected_exe).resolve(strict=True))
                  and P.fingerprint(before) == digest)
        fd = os.pidfd_open(pid)
        try:
            P.require(P.live(fd) and P.identity(pid) == before)
        except BaseException:
            os.close(fd)
            raise
        self.fd, self.saved = fd, before

    def live(self):
        return P.live(self.fd) and P.identity(self.saved['pid']) == self.saved


def run(cfg):
    C = P.load_source('inventory_control_observed.py', CONTROLLER_SHA, __file__)
    log = P.PrivateLog(cfg['log_path'])
    process = target = worker = None
    rfd = wfd = None
    selector = selectors.DefaultSelector()
    held = False
    window = P.Window(cfg['binding_sha256'],cfg['challenge'])
    events = P.Lines(P.FRAME_LIMIT, P.FRAME_LIMIT * 3)
    messages = P.Lines(P.HOST_LIMIT, P.HOST_LIMIT)
    result_lines = P.Lines(65536,65536)
    results, stderr = [], bytearray()
    stdout_eof = stderr_eof = False
    started = time.monotonic()

    def send(kind, **extra):
        value = {'kind':kind,'binding':cfg['binding_sha256'],'challenge':cfg['challenge'],
                 **P.FALSE_FLAGS,**extra}
        raw = P.encode(value,P.HOST_LIMIT)
        log.append(value)
        # stdout is nonblocking: a blocked/disconnected host is a failure, not an unbounded wait.
        P.require(os.write(sys.stdout.fileno(),raw)==len(raw))

    def consume_events():
        nonlocal worker
        while not events.eof:
            try:
                raw = os.read(rfd,4096)
            except BlockingIOError:
                break
            for event in events.feed(raw):
                window.event(event)
                log.append(event)
                if event['kind']=='worker_bound':
                    P.require(worker is None)
                    worker = ReadOnlyWorker(event['pid'],event['identity'],process,cfg['controller_python'])
            if not raw:
                try:
                    selector.unregister(rfd)
                except KeyError:
                    pass
                break

    try:
        os.set_blocking(sys.stdout.fileno(),False)
        rfd,wfd = os.pipe2(os.O_CLOEXEC | os.O_NONBLOCK)
        P.require(os.fpathconf(wfd,'PC_PIPE_BUF')>=P.FRAME_LIMIT)
        path = str(Path(__file__).absolute().with_name('inventory_control_observed.py'))
        argv = [cfg['controller_python'],'-I','-S','-B',path,'--root',cfg['root'],
                '--attempt-name',cfg['attempt_name'],'--python-argv',cfg['python_argv'],
                '--health-port',str(cfg['health_port']),'--scope-start-epoch',str(cfg['scope_start_epoch']),
                '--observation-fd',str(wfd),'--binding-sha256',cfg['binding_sha256'],
                '--challenge',cfg['challenge']]
        process = subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,pass_fds=(wfd,),close_fds=True,cwd='/',
                                   env={'PATH':'/usr/bin:/bin','LANG':'C'},bufsize=0)
        os.close(wfd)
        wfd=None
        target = C.Target(process,argv)
        for stream,label in ((process.stdout,'stdout'),(process.stderr,'stderr'),
                             (sys.stdin,'host')):
            os.set_blocking(stream.fileno(),False)
            selector.register(stream,selectors.EVENT_READ,label)
        selector.register(rfd,selectors.EVENT_READ,'events')
        while time.monotonic()-started < 65:
            for key,_ in selector.select(0.02):
                label=key.data
                if label=='events':
                    consume_events()
                    continue
                raw=os.read(key.fileobj.fileno(),4096)
                if label=='host':
                    P.require(raw)  # EOF/cancel latches failure; never reconnect.
                    for message in messages.feed(raw):
                        consume_events()
                        window.post(message,worker is not None and worker.live(),
                                    partial=bool(events.pending),eof=events.eof)
                        send('window_confirmed')
                elif label=='stderr':
                    stderr.extend(raw)
                    P.require(len(stderr)<=65536 and not stderr)
                else:
                    results.extend(result_lines.feed(raw))
                    P.require(len(results)<=1)
                if not raw:
                    selector.unregister(key.fileobj)
                    if label=='stdout':
                        stdout_eof=True
                    elif label=='stderr':
                        stderr_eof=True
            if window.phase=='inside' and not window.opened:
                consume_events()
                window.pre(worker is not None and worker.live(),partial=bool(events.pending),eof=events.eof)
                send('sample_window_open')
            if window.phase=='left' and not window.confirmed:
                raise P.Hold()
            if process.poll() is not None and stdout_eof and stderr_eof and events.eof:
                break
        P.require(process.poll() is not None and stdout_eof and stderr_eof and events.eof)
        process.wait(timeout=0)
        P.require(process.returncode==0 and not stderr and len(results)==1)
        result=results[0]
        P.require(type(result) is dict and result.get('status')=='CONTROL_COMPLETE_PENDING_REVIEW'
                  and type(result.get('receipt_sha256')) is str
                  and re.fullmatch('[a-f0-9]{64}',result['receipt_sha256'])
                  and all(result.get(k) is False for k in C.SCOPE_FLAGS))
        window.finish()
        send('observation_complete_pending_review',receipt_sha256=result['receipt_sha256'])
        return 0
    except BaseException:
        held=True
        if target is not None and process.poll() is None:
            try:
                target.send_signal(signal.SIGTERM)
            except BaseException:
                pass
        if process is not None:
            # Drain under the original wrapper deadline. No KILL or numeric PID fallback.
            for stream in (process.stdout,process.stderr):
                if stream is not None:
                    os.set_blocking(stream.fileno(),False)
            while time.monotonic()-started < 74:
                if process.poll() is not None:
                    break
                for stream in (process.stdout,process.stderr):
                    try:
                        if stream is not None:
                            os.read(stream.fileno(),4096)
                    except (OSError,ValueError):
                        pass
                select.select([],[],[],0.02)
            if process.poll() is None:
                os._exit(73)  # Unknown stop; no final receipt. Do not finalize Popen falsely.
            process.wait(timeout=0)
        try:
            send('hold')
        except BaseException:
            pass
        return 2
    finally:
        selector.close()
        for fd in (rfd,wfd,worker.fd if worker else None):
            if fd is not None:
                os.close(fd)
        if process is not None and process.returncode is not None:
            for stream in (process.stdout,process.stderr):
                if stream is not None:
                    stream.close()
            if target is not None:
                target.close()
        log.close()


def main():
    global P
    armed=False
    try:
        if not (signal.getsignal(signal.SIGALRM)==signal.SIG_DFL
                and signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0)):
            raise RuntimeError('existing timer')
        signal.signal(signal.SIGALRM,lambda *_: os._exit(73))
        signal.setitimer(signal.ITIMER_REAL,75)
        armed=True
        P=_load_observation_protocol()
        P.require(len(sys.argv)==3 and sys.argv[1]=='--config')
        return run(read_config(sys.argv[2]))
    except BaseException:
        os.write(sys.stderr.fileno(),b'HOLD: observer incomplete; preserve files; no retry.\n')
        return 2
    finally:
        if armed:
            signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    raise SystemExit(main())
