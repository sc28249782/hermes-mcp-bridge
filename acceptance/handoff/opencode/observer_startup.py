"""Owned offline R/O/S/H startup candidate. H is inert Python, NOT SQLite/CLI.

Run only in a fresh trusted fixture R process with a process-local FixtureIssuer.
The one G byte below is an inert-helper startup probe, not protected capture.
Reservation.capture(), production authority/containment and native code unchanged.
"""
import ctypes
from dataclasses import dataclass
from fractions import Fraction
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import select
import signal
import time

from . import observer_preflight as P


def _need(value, reason='PROTOCOL_REJECTED'):
    if not value:
        raise P.Hold(reason)


def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024,)*2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _subreaper():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int]+[ctypes.c_ulong]*4
    libc.prctl.restype = ctypes.c_int
    _need(libc.prctl(36, 1, 0, 0, 0) == 0, 'SUBREAPER_UNAVAILABLE')
    value = ctypes.c_int()
    _need(libc.prctl(37, ctypes.addressof(value), 0, 0, 0) == 0 and value.value == 1,
          'SUBREAPER_UNAVAILABLE')


def _close_except(keep):
    # Close all non-allowlisted descriptors without a /proc/process scan.
    position = 3
    for fd in sorted(set(keep)):
        if fd >= 3:
            os.closerange(position, fd)
            position = fd+1
    os.closerange(position, resource.getrlimit(resource.RLIMIT_NOFILE)[0])


def _ready(fd):
    return bool(select.select([fd], [], [], 0)[0])


def _until(fd, deadline):
    return bool(select.select([fd], [], [], _remaining(deadline))[0])


def _remaining(deadline):
    # POSIX timeout APIs take float; round inward, never extend an exact bound.
    value=Fraction(deadline)-Fraction(time.monotonic())
    if value<=0:return 0.0
    seconds=float(value)
    return math.nextafter(seconds,0.0) if Fraction(seconds)>value else seconds


def _byte(fd, deadline):
    _need(_until(fd, deadline), 'BUDGET_EXHAUSTED')
    value = os.read(fd, 1)
    _need(len(value) == 1, 'CHANNEL_LOST')
    return value


def _emit(fd, value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode('ascii')+b'\n'
    _need(len(raw) <= 512)
    os.set_blocking(fd, False)
    _need(os.write(fd, raw) == len(raw), 'CHANNEL_LOST')


def _frame(fd, deadline, deathfds=()):
    ready = select.select([fd, *deathfds], [], [], _remaining(deadline))[0]
    _need(not any(item in ready for item in deathfds), 'ACTOR_LOST')
    _need(fd in ready, 'BUDGET_EXHAUSTED')
    return P._frame(os.read(fd, 513))


@dataclass
class Child:
    pid: int | None = None
    pidfd: int | None = None
    rc: int | None = None
    attempted: bool = False


def _fork(child, function, args, keep, deadline):
    # function/args are fixed internal actor code, never caller callbacks/argv.
    _need(_remaining(deadline)>0,'BUDGET_EXHAUSTED')
    child.attempted = True
    pid = os.fork()
    if pid == 0:
        try:
            _close_except(keep)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            signal.signal(signal.SIGALRM, lambda *_: os._exit(88))
            remaining=_remaining(deadline)
            if remaining<=0:os._exit(88)
            signal.setitimer(signal.ITIMER_REAL, remaining)
            _limits()
            function(*args)
            os._exit(0)
        except BaseException:
            os._exit(2)
    child.pid = pid  # Preserve ownership before any further parent operation.
    child.pidfd = os.pidfd_open(pid)


def _reap(child):
    if child.rc is None:
        pid, status = os.waitpid(child.pid, os.WNOHANG)
        if pid:
            _need(pid == child.pid)
            child.rc = os.waitstatus_to_exitcode(status)


def _eligible(child):
    _need(child.pid is not None and child.pidfd is not None, 'STOP_UNCONFIRMED')
    os.waitid(os.P_PID, child.pid, os.WEXITED|os.WNOHANG|os.WNOWAIT)


def _signal(child, sig):
    _eligible(child)
    if child.rc is None and not _ready(child.pidfd):
        try:
            signal.pidfd_send_signal(child.pidfd, sig)
        except ProcessLookupError:
            pass  # Exit raced with the signal; caller still confirms/reaps.


def _stop_group(children, deadline):
    pending = [c for c in children if c.pid is not None and c.rc is None]
    for sig, grace in ((signal.SIGTERM, Fraction(1,5)), (signal.SIGKILL, 1)):
        for child in pending:
            _reap(child)
            if child.rc is None:
                _signal(child, sig)
        phase = min(deadline, Fraction(time.monotonic())+grace)
        for child in pending:
            if child.rc is None and _until(child.pidfd, phase):
                _reap(child)
        if all(child.rc is not None for child in pending):
            return
    _need(all(child.rc is not None for child in pending), 'STOP_UNCONFIRMED')


def _eof(fd, cap, deadline):
    total = 0
    while True:
        _need(_until(fd, deadline), 'STOP_UNCONFIRMED')
        raw = os.read(fd, 4096)
        if not raw:
            return
        total += len(raw)
        _need(total <= cap, 'STREAM_OVER_CAP')


def _helper(gate, output, error):
    # No DB, native method, executable, model, caller payload or arbitrary path.
    if _byte(gate, Fraction(time.monotonic())+1) != b'G':
        raise P.Hold('CHANNEL_LOST')
    _need(os.write(output, b'HG1\n') == 4)


def _helper_entry(gate, output, error):
    # These are the actual H stdin/stdout/stderr, not surrogate EOF channels.
    copies = [fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 10) for fd in (gate, output, error)]
    for target, source in enumerate(copies):
        os.dup2(source, target, inheritable=True)
    _close_except(())
    _helper(0, 1, 2)


def _owner(control, lease, deadline):
    _need(_byte(control, deadline) == b'G')
    _need(os.write(lease, b'G') == 1)
    _need(_byte(control, deadline) == b'Q')


def _supervisor(command, lease, report, gate_r, gate_w, proof_r, proof_w,
                error_r, error_w, binding, capture_deadline, deadline):
    h = Child()
    try:
        _need(_byte(command, capture_deadline) == b'A')
        _fork(h, _helper_entry, (gate_r, proof_w, error_w), (gate_r, proof_w, error_w), deadline)
        for fd in (gate_r, proof_w, error_w):
            os.close(fd)
        _eligible(h)  # S proves direct-child eligibility; no reap before ACK.
        _emit(report, dict(kind='witness', nonce=binding.nonce, generation=binding.generation,
                           role='H', source_sha256=binding.source_sha256,
                           parent=os.getpid(), child=h.pid))
        _need(_byte(command, capture_deadline) == b'K', 'ACK_REJECTED')
        _need(not _ready(h.pidfd), 'ACTOR_LOST')
        _emit(report, dict(kind='acked', nonce=binding.nonce))
        ready = select.select([command, lease], [], [], _remaining(capture_deadline))[0]
        _need(command not in ready and lease in ready, 'CHANNEL_LOST')
        _need(_byte(lease, capture_deadline) == b'G')
        _need(os.write(gate_w, b'G') == 1)
        os.close(gate_w); gate_w = None
        _need(_until(proof_r, capture_deadline), 'BUDGET_EXHAUSTED')
        _need(os.read(proof_r, 5) == b'HG1\n')
        _need(_until(h.pidfd, capture_deadline), 'BUDGET_EXHAUSTED')
        _reap(h); _need(h.rc == 0)
        _eof(proof_r, 65536, capture_deadline); _eof(error_r, 4096, capture_deadline)
        _emit(report, dict(kind='final', nonce=binding.nonce,
                           helper_reaped=True, stdout_eof=True, stderr_eof=True))
    finally:
        if gate_w is not None:
            os.close(gate_w)
        if h.pid is not None and h.rc is None:
            _stop_group([h], deadline)
        if h.pidfd is not None:
            os.close(h.pidfd)


@dataclass(frozen=True)
class Outcome:
    state: str
    reason: str
    trace: tuple
    reservation_consumed: bool
    fixture_g_sent: bool
    original_final: bool
    helper_launch_known: bool
    helper_exit_observed: bool | None
    helper_reaped_by: str | None
    stdout_eof: bool | None
    stderr_eof: bool | None
    actors_reaped: int
    capture_allowed: bool = False
    authorizes_actions: bool = False
    dev_observed: bool = False
    goal_verified: bool = False


class Startup:
    """Fresh trusted fixture R only. No production entry or native capture path."""
    def __init__(self, issuer, ref, attempt_seconds=8):
        _need(type(issuer) is P.FixtureIssuer)
        _need(type(attempt_seconds) in (int, float) and math.isfinite(attempt_seconds)
              and 3 < attempt_seconds <= 20, 'BUDGET_EXHAUSTED')
        self.issuer, self.ref, self.seconds = issuer, ref, attempt_seconds
        self.o, self.s, self.h = Child(), Child(), Child()
        self.trace = []
        self.go = self.final = self.known = False
        self.helper_pidfd_attempted = False
        self.reservation = None
        self.fds = []
        self.used = False

    def _new_pipe(self):
        pair = os.pipe2(os.O_CLOEXEC)
        self.fds.extend(pair)
        return pair

    def _close(self, *fds):
        for fd in fds:
            if fd in self.fds:
                os.close(fd); self.fds.remove(fd)

    def _current(self):
        self.issuer._current(self.ref, self.reservation.binding)
        _need(time.monotonic() < self.capture_deadline, 'BUDGET_EXHAUSTED')
        _need(not _ready(self.o.pidfd) and not _ready(self.s.pidfd), 'ACTOR_LOST')

    def _retain(self, witness):
        b = self.reservation.binding
        _need(set(witness) == {'kind','nonce','generation','role','source_sha256','parent','child'})
        _need(witness['kind'] == 'witness' and witness['nonce'] == b.nonce
              and type(witness['generation']) is int and witness['generation'] == b.generation
              and witness['role'] == 'H' and witness['source_sha256'] == b.source_sha256
              and type(witness['parent']) is int and witness['parent'] == self.s.pid
              and type(witness['child']) is int and 1 < witness['child'] <= 2147483647)
        self.known = True
        self.h.pid = witness['child']
        self._current()
        self.helper_pidfd_attempted = True
        self.h.pidfd = os.pidfd_open(self.h.pid)
        self._current()
        _need(not _ready(self.h.pidfd), 'ACTOR_LOST')
        self.trace.append('PIDFD')

    def _ack(self, command):
        self._current()
        _need(os.write(command, b'K') == 1)
        self.trace.append('ACK')

    def _go(self, owner):
        self._current()
        _need(not _ready(self.h.pidfd), 'ACTOR_LOST')
        _need(os.write(owner, b'G') == 1)
        self.go = True
        self.trace.append('FIXTURE_G')

    def run(self):
        _need(not self.used, 'ATTEMPT_CONSUMED')
        self.used = True
        exit_observed = stdout_eof = stderr_eof = None
        reaper = None
        reason = 'PROTOCOL_REJECTED'
        consumed = False
        command_w = owner_w = proof_r = error_r = report_r = None
        deadline = time.monotonic()
        previous_handler = None
        timer_set = False
        try:
            binding, _, _ = self.issuer._current(self.ref)
            _need(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'TIMER_UNAVAILABLE')
            previous_handler = signal.getsignal(signal.SIGALRM)
            def expired(*_): raise P.Hold('BUDGET_EXHAUSTED')
            signal.signal(signal.SIGALRM, expired)
            timer_set = True
            remaining = _remaining(Fraction(binding.t0)+45)
            _need(remaining > 0, 'BUDGET_EXHAUSTED')
            signal.setitimer(signal.ITIMER_REAL, remaining)
            self.reservation = self.issuer.reserve(self.ref)
            consumed = True; self.trace.append('CLAIM')
            b = self.reservation.binding
            _need(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == b.source_sha256,
                  'SOURCE_CHANGED')
            deadline = min(self.reservation.budget.attempt_deadline,
                           self.reservation.budget.ta+Fraction(self.seconds))
            self.capture_deadline = deadline-3
            self._current_setup()
            self.trace.append('SUBREAPER')
            owner_r, owner_w = self._new_pipe(); lease_r, lease_w = self._new_pipe()
            command_r, command_w = self._new_pipe(); report_r, report_w = self._new_pipe()
            gate_r, gate_w = self._new_pipe(); proof_r, proof_w = self._new_pipe()
            error_r, error_w = self._new_pipe()
            self._proof_r, self._error_r = proof_r, error_r
            _fork(self.o, _owner, (owner_r, lease_w, deadline), (owner_r, lease_w), deadline)
            self.trace.append('OWNER')
            keep = (command_r, lease_r, report_w, gate_r, gate_w, proof_r, proof_w, error_r, error_w)
            _fork(self.s, _supervisor, (*keep, b, self.capture_deadline, deadline), keep, deadline)
            self.trace.append('SUPERVISOR')
            self._close(owner_r, lease_r, lease_w, command_r, report_w, gate_r, gate_w, proof_w, error_w)
            self._current(); _need(os.write(command_w, b'A') == 1)
            witness = _frame(report_r, self.capture_deadline, (self.o.pidfd, self.s.pidfd))
            self.trace.append('WITNESS')
            self._retain(witness)
            self._ack(command_w)
            ack = _frame(report_r, self.capture_deadline, (self.o.pidfd, self.s.pidfd))
            _need(ack == {'kind': 'acked', 'nonce': b.nonce})
            self.trace.append('ACKED')
            self._go(owner_w)
            final = _frame(report_r, self.capture_deadline, (self.o.pidfd,))
            _need(set(final) == {'kind','nonce','helper_reaped','stdout_eof','stderr_eof'}
                  and final['kind'] == 'final' and final['nonce'] == b.nonce
                  and all(final[k] is True for k in ('helper_reaped','stdout_eof','stderr_eof')))
            self.issuer._current(self.ref, b)
            _need(time.monotonic() < self.capture_deadline)
            self.final = True; self.trace.append('FINAL')
            _need(os.write(owner_w, b'Q') == 1)
            for c in (self.o, self.s):
                _need(_until(c.pidfd, deadline), 'STOP_UNCONFIRMED')
                _reap(c); _need(c.rc == 0)
            _eof(report_r, 512, deadline)
            reason = 'STARTUP_ONLY'
        except P.Hold as error:
            reason = error.reason
            if reason in ('CLAIM_UNCONFIRMED', 'ATTEMPT_CONSUMED'):
                consumed = True
        except (OSError, ValueError, TypeError, ChildProcessError):
            reason = 'PROTOCOL_REJECTED'
        finally:
            try:
                # Cooperative CANCEL/owner EOF uses <=0.2 s from the 0.6 s
                # control/drain reserve; then two <=1.2 s stop phases fit <=3 s.
                if command_w is not None and self.s.pidfd is not None and self.s.rc is None:
                    try: os.write(command_w, b'C')
                    except OSError: pass
                self._close(*(fd for fd in (command_w, owner_w) if fd is not None))
                cooperative = min(deadline, Fraction(time.monotonic())+Fraction(1,5))
                for c in (self.o, self.s):
                    if c.pidfd is not None and c.rc is None and _until(c.pidfd, cooperative):
                        _reap(c)
                _stop_group([self.o, self.s], deadline)
                if self.known:
                    try:
                        os.waitid(os.P_PID, self.h.pid, os.WEXITED|os.WNOHANG|os.WNOWAIT)
                    except ChildProcessError:
                        _need(self.h.pidfd is not None and _ready(self.h.pidfd), 'STOP_UNCONFIRMED')
                        exit_observed = True
                        reaper = 'S' if self.final else None
                    else:
                        # Cleanup-only acquisition after valid witness and exact
                        # S reap, never a late ACK/capture or numeric signal.
                        if self.h.pidfd is None:
                            _need(not self.helper_pidfd_attempted, 'STOP_UNCONFIRMED')
                            self.helper_pidfd_attempted = True
                            self.h.pidfd = os.pidfd_open(self.h.pid)
                        _stop_group([self.h], deadline)
                        exit_observed = self.h.rc is not None
                        reaper = 'R' if exit_observed else None
                    _eof(proof_r, 65536, deadline); stdout_eof = True
                    _eof(error_r, 4096, deadline); stderr_eof = True
                elif self.s.attempted:
                    reason = 'STOP_UNCONFIRMED'
                if any(c.attempted and c.pid is None for c in (self.o, self.s)):
                    reason = 'STOP_UNCONFIRMED'
            except (P.Hold, OSError, ChildProcessError):
                reason = 'STOP_UNCONFIRMED'
            for fd in self.fds:
                os.close(fd)
            self.fds.clear()
            for c in (self.o, self.s, self.h):
                if c.pidfd is not None:
                    os.close(c.pidfd)
            if self.reservation is not None:
                self.reservation.close()
            if timer_set:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous_handler)
        state = 'FIXTURE_STARTUP_CONFIRMED' if reason == 'STARTUP_ONLY' else 'UNKNOWN' if consumed else 'HOLD'
        return Outcome(state, reason, tuple(self.trace), consumed, self.go, self.final, self.known,
                       exit_observed, reaper, stdout_eof, stderr_eof,
                       sum(c.rc is not None for c in (self.o, self.s)))

    def _current_setup(self):
        # Bootstrap-only fixed checks before any O/S/H launch.
        self.issuer._current(self.ref, self.reservation.binding)
        _need(time.monotonic() < self.capture_deadline, 'BUDGET_EXHAUSTED')
        _limits(); _subreaper()
