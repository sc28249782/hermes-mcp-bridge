"""Fixture-only B4 supervisor. Trusted launcher supplies retained capabilities.

No public parser, authority issuer, backend method or goal/Done decision exists.
The independent fixture observer must retain its own supervisor pidfd/report pipe.
Absent final report or observer loss is UNKNOWN, never stop proof.
"""
import fcntl
import json
import math
import os
import resource
import select
import signal
import stat
import time

from .owner import Hold, _decode, _limits, digest, need, open_file, read_all


def _pidfd(fd):
    need(type(fd) is int and os.readlink('/proc/self/fd/' + str(fd)) == 'anon_inode:[pidfd]')


def _pipe(fd):
    need(type(fd) is int and stat.S_ISFIFO(os.fstat(fd).st_mode))


def _target(value):
    need(type(value) is str and 0 < len(value) <= 128
         and all(c.isascii() and (c.isalnum() or c in '_.-') for c in value))
    return value.encode('ascii')


def _report(fd, value):
    # One atomic nonblocking pipe write. A full/closed pipe loses the report;
    # it cannot postpone stop or silently become successful evidence.
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode() + b'\n'
    need(len(raw) <= 512)
    try:
        return os.write(fd, raw) == len(raw)
    except OSError:
        return False


def _spawn(helperfd, dbfd, ctxfd, rootfd, launch):
    """Exactly one fork; helper's only retained capabilities are fixed fd 3..6."""
    pipes = []
    try:
        for _ in range(3):
            pipes.append(os.pipe2(os.O_CLOEXEC))
        parent = (pipes[0][1], pipes[1][0], pipes[2][0])
        launch['parent'] = parent
        # Interrupted fork return is an uncertain launch, never 'no helper'.
        launch['fork_attempted'] = True
        pid = os.fork()
    except BaseException:
        for pair in pipes:
            for fd in pair:
                os.close(fd)
        raise
    if pid == 0:
        try:
            # Duplicate first so fd 0..6 assignments cannot overwrite a source.
            sources = [pipes[0][0], pipes[1][1], pipes[2][1], dbfd, ctxfd, rootfd, helperfd]
            copied = [fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 10) for fd in sources]
            for dest, source in enumerate(copied):
                os.dup2(source, dest, inheritable=True)
            os.closerange(7, resource.getrlimit(resource.RLIMIT_NOFILE)[0])
            _limits()
            # No inherited timer/handler contract is required from the owner.
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            signal.setitimer(signal.ITIMER_REAL, 0)
            os.execve(6, ['oc-retained-helper', '--batch', '3', '4', '5'],
                      {'LANG': 'C', 'LC_ALL': 'C', 'PATH': ''})
        except BaseException:
            os._exit(126)
    launch['pid'] = pid
    for fd in (pipes[0][0], pipes[1][1], pipes[2][1]):
        os.close(fd)
    for fd in parent:
        os.set_blocking(fd, False)
    return pid, parent


def supervise(ownerfd, commandsfd, reportfd, rootfd, helperfd, helper_sha,
              context_id, job_id, started_at, *, lifetime=20.0):
    """Run only in a fresh, single-thread, trusted fixture supervisor process.

    Owner and independent observer are external to this process. A then G is a
    one-use arm/capture barrier; the owner retains commandsfd's write end until
    completion. Owner pidfd/lease loss always cancels the attempt. Only this
    supervisor creates/signals/reaps its direct helper. No numeric-PID signal.
    Caller identities/handles/deadline are NOT a production admission format.
    """
    now = time.monotonic()
    need(type(started_at) in (float, int) and math.isfinite(started_at)
         and 0 <= now - started_at < 45)
    need(type(lifetime) in (float, int) and math.isfinite(lifetime) and 0 < lifetime <= 20)
    outer = started_at + 45
    # Reserve cleanup inside the original outer deadline, never after it.
    deadline = min(now + lifetime, outer - 2)
    need(now < deadline)
    payload = b'context\n' + _target(context_id) + b'\njobs\n' + _target(job_id)
    payload += b'\ncontext\n' + _target(context_id) + b'\n'
    _pidfd(ownerfd)
    _pipe(commandsfd)
    _pipe(reportfd)
    os.set_blocking(commandsfd, False)
    os.set_blocking(reportfd, False)
    _limits()
    need(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0))
    previous = signal.getsignal(signal.SIGALRM)
    def alarm(_sig, _frame):
        raise Hold('BUDGET_EXHAUSTED')
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, outer - time.monotonic()))
    pid = childfd = dbfd = ctxfd = None
    streams = set()
    stdin = stdout = stderr = None
    output = bytearray()
    totals = [0, 0]
    returncode = None
    owner_lost = False
    reason = 'CAPTURE_REJECTED'
    phase = 0
    frames = 0
    report_ok = True
    launch = {'fork_attempted': False, 'pid': None, 'parent': None}

    def owner_dead():
        return bool(select.select([ownerfd], [], [], 0)[0])

    def drain(fd):
        nonlocal reason
        data = os.read(fd, 4096)
        if not data:
            streams.remove(fd)
            return
        slot = 0 if fd == stdout else 1
        totals[slot] += len(data)
        if totals[slot] > (65536 if slot == 0 else 4096):
            raise Hold()
        if slot == 0:
            output.extend(data)
        else:
            # Never emit raw stderr or accept a helper diagnostic as data.
            raise Hold()

    def reap():
        nonlocal returncode
        if returncode is not None:
            return
        found, status = os.waitpid(pid, os.WNOHANG)
        if found:
            returncode = os.waitstatus_to_exitcode(status)

    def stop():
        nonlocal returncode
        if pid is None:
            return
        # EOF may stop an idle helper even if pidfd acquisition failed.
        nonlocal stdin
        if stdin is not None:
            os.close(stdin)
            stdin = None
        limit = min(outer, time.monotonic() + 1.5)
        for sig, allowance in ((signal.SIGTERM, 0.2), (signal.SIGKILL, 1.0)):
            reap()
            if returncode is None and childfd is not None:
                try:
                    signal.pidfd_send_signal(childfd, sig)
                except ProcessLookupError:
                    pass
            until = min(limit, time.monotonic() + allowance)
            while time.monotonic() < until and (returncode is None or streams):
                watched = list(streams) + ([childfd] if childfd is not None and returncode is None else [])
                if not watched:
                    # pidfd unavailable: no polling/numeric signal fallback.
                    break
                ready = select.select(watched, [], [], max(0, until-time.monotonic()))[0]
                for fd in ready:
                    if fd == childfd:
                        reap()
                    else:
                        # Bounded discard during stop, never a success prefix.
                        raw = os.read(fd, 4096)
                        if not raw:
                            streams.remove(fd)
            reap()
            if returncode is not None and not streams:
                break

    try:
        # Hash measured by the independently trusted fixture launcher. No claim
        # that a checksum/mode authenticates a compiler, host or production issuer.
        raw = read_all(helperfd, 4*1024*1024)
        info = os.fstat(helperfd)
        need(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
             and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o700
             and raw[:5] == b'\x7fELF\x02' and digest(raw) == helper_sha)
        while True:
            if owner_dead():
                owner_lost = True
                reason = 'OWNER_LOST'
                break
            if time.monotonic() >= deadline:
                reason = 'BUDGET_EXHAUSTED'
                break
            watched = [ownerfd, commandsfd, *streams]
            if childfd is not None and returncode is None:
                watched.append(childfd)
            ready = select.select(watched, [], [], max(0, deadline-time.monotonic()))[0]
            # Owner death wins over simultaneously ready helper success/output.
            if ownerfd in ready:
                owner_lost = True
                reason = 'OWNER_LOST'
                break
            if commandsfd in ready:
                command = os.read(commandsfd, 16)
                if not command:
                    owner_lost = True
                    reason = 'OWNER_LOST'
                    break
                if command == b'A' and phase == 0:
                    # Recheck after admission and immediately before the fork.
                    need(not owner_dead())
                    dbfd = open_file(rootfd, 'opencode-tasks.sqlite3', 64*1024*1024)
                    ctxfd = open_file(rootfd, 'contexts.sqlite3', 64*1024*1024)
                    need(digest(read_all(helperfd, 4*1024*1024)) == helper_sha)
                    pid, (stdin, stdout, stderr) = _spawn(helperfd, dbfd, ctxfd, rootfd, launch)
                    streams.update((stdout, stderr))
                    # A failed acquisition never authorizes numeric-PID signals.
                    childfd = os.pidfd_open(pid)
                    _pidfd(childfd)
                    phase = 1
                    report_ok = _report(reportfd, {'event': 'READY'})
                    need(report_ok)
                elif command == b'G' and phase == 1:
                    need(not owner_dead())
                    need(os.write(stdin, payload) == len(payload))
                    os.close(stdin)
                    stdin = None
                    phase = 2
                    report_ok = _report(reportfd, {'event': 'CAPTURE'})
                    need(report_ok)
                else:
                    raise Hold()
            for fd in ready:
                if fd in streams:
                    drain(fd)
                elif fd == childfd:
                    reap()
            if pid is not None and returncode is not None and not streams:
                need(phase == 2 and returncode == 0)
                pos = 0
                for role in ('context', 'jobs', 'context'):
                    need(pos + 4 <= len(output))
                    size = int.from_bytes(output[pos:pos+4], 'big')
                    need(10 <= size <= 65536 and pos+4+size <= len(output))
                    _decode(bytes(output[pos+4:pos+4+size]), role)
                    frames += 1
                    pos += 4+size
                need(pos == len(output))
                need(not owner_dead())
                reason = 'CAPTURE_COMPLETE'
                break
    except Hold as error:
        reason = error.code
    except (OSError, ValueError, TypeError, ChildProcessError):
        reason = 'CAPTURE_REJECTED'
    finally:
        # Recover ownership even when post-fork setup fails before _spawn returns.
        if pid is None and launch['pid'] is not None:
            pid = launch['pid']
            stdin, stdout, stderr = launch['parent']
            streams.update((stdout, stderr))
        try:
            stop()
        except (Hold, OSError, ChildProcessError):
            reason = 'STOP_UNCONFIRMED'
        # End-of-attempt owner validation; it grants no continuing authority.
        try:
            owner_lost = owner_lost or owner_dead()
        except OSError:
            owner_lost = True
        if owner_lost:
            reason = 'OWNER_LOST'
        uncertain_launch = launch['fork_attempted'] and pid is None
        stopped = False if uncertain_launch else None if pid is None else returncode is not None and not streams
        if stopped is False:
            reason = 'STOP_UNCONFIRMED'
        result = {'event': 'FINAL', 'reason': reason, 'helper_started': None if uncertain_launch else pid is not None,
                  'helper_stopped': stopped, 'owner_lost': owner_lost,
                  'helper_reaped': None if pid is None else returncode is not None,
                  'pipes_eof': None if pid is None else not streams,
                  'frames': frames if reason == 'CAPTURE_COMPLETE' else 0,
                  'authorizes_actions': False, 'dev_observed': False,
                  'goal_verified': False}
        # No ADVISORY_DONE exists in this primitive, including its positive path.
        try:
            report_ok = _report(reportfd, result) and report_ok
        finally:
            for fd in (stdin, stdout, stderr, childfd, dbfd, ctxfd):
                if fd is not None:
                    os.close(fd)
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
    return report_ok
