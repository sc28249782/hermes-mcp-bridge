"""Owned OFFLINE native fixture candidate; no production entry or goal claim.

Reuses accepted startup identity/stop primitives, not its inert H/run path.
FixtureBootstrap supplies retained FDs and an independent expected-frame digest.
That bootstrap is trusted test infrastructure, NOT a production resolver/anchor.
NativeRun is callable only from explicit source controls; nothing wires it to
Facts/Batch/planner, a public CLI/MCP, real Dev state, or Reservation.capture().
"""
from dataclasses import dataclass
from fractions import Fraction
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import time

from . import observer_preflight as P, observer_startup as S, owner as V
from .observer_startup import (_need, _remaining, _fork, _ready, _until,
    _reap, _stop_group, _eof, _frame, _byte, _emit, _eligible, _close_except, _owner)


def frame_digest(values):
    return hashlib.sha256(json.dumps(values, ensure_ascii=True,
        separators=(',', ':'), allow_nan=False).encode('ascii')).hexdigest()


@dataclass(frozen=True)
class FixtureBundle:
    """Trusted test-bootstrap handles only; no caller JSON/path/argv factory.

    FDs remain caller-owned and open through run; passed only to S/H. Digests
    are fixture measurements, not hostile-host authentication or original-job
    provenance. The expected digest is locked BEFORE observing native output.
    """
    rootfd: int
    helperfd: int
    jobfd: int
    contextfd: int
    helper_sha256: str
    expected_sha256: str

    @property
    def fds(self):return (self.rootfd,self.helperfd,self.jobfd,self.contextfd)

    def check(self, expected):
        _need(expected == self.expected_sha256, 'FIXTURE_ORACLE_CHANGED')
        _need(len(set(self.fds)) == 4 and all(type(fd) is int and fd>2 for fd in self.fds))
        V.private_dir(self.rootfd)
        for fd,name in ((self.jobfd,'opencode-tasks.sqlite3'),(self.contextfd,'contexts.sqlite3')):
            _need(fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE == os.O_RDONLY)
            V.unchanged(self.rootfd,name,fd)
            st=os.fstat(fd)
            _need(st.st_mode&0o7777 == 0o600 and 0<st.st_size<=67108864)
        st=os.fstat(self.helperfd)
        import stat
        _need(stat.S_ISREG(st.st_mode) and st.st_uid==os.geteuid() and st.st_nlink==1
              and st.st_mode&0o7777==0o700
              and fcntl.fcntl(self.helperfd,fcntl.F_GETFL)&os.O_ACCMODE==os.O_RDONLY)
        _need(V.digest(V.read_all(self.helperfd,4*1024*1024))==self.helper_sha256,'SOURCE_CHANGED')


def _native_entry(gate, output, error, bundle, cutoff):
    # One wrapper process becomes the exact retained native binary: no fifth
    # actor, executable pathname lookup, shell, backend CLI, or numeric signal.
    _need(_byte(gate,cutoff)==b'G','CHANNEL_LOST')
    bundle.check(bundle.expected_sha256)
    copies=[fcntl.fcntl(fd,fcntl.F_DUPFD_CLOEXEC,10) for fd in (gate,output,error)]
    for target,source in enumerate(copies):os.dup2(source,target,inheritable=True)
    _close_except(bundle.fds)
    for fd in (bundle.rootfd,bundle.jobfd,bundle.contextfd):os.set_inheritable(fd,True)
    os.execve(bundle.helperfd,('oc-offline-retained','--batch',str(bundle.jobfd),
        str(bundle.contextfd),str(bundle.rootfd)),{'LANG':'C','LC_ALL':'C','PATH':''})


def _native_supervisor(command, lease, report, gate_r, gate_w, proof_r, proof_w,
                       error_r, error_w, binding, bundle, cutoff, deadline):
    h=S.Child(); total=0
    try:
        _need(_byte(command,cutoff)==b'A')
        _fork(h,_native_entry,(gate_r,proof_w,error_w,bundle,cutoff),
              (gate_r,proof_w,error_w,*bundle.fds),deadline)
        for fd in (gate_r,proof_w,error_w):os.close(fd)
        _eligible(h)
        _emit(report,dict(kind='witness',nonce=binding.nonce,generation=binding.generation,
            role='H',source_sha256=binding.source_sha256,parent=os.getpid(),child=h.pid))
        _need(_byte(command,cutoff)==b'K','ACK_REJECTED')
        _need(not _ready(h.pidfd),'ACTOR_LOST')
        _emit(report,dict(kind='acked',nonce=binding.nonce))
        ready=select.select([command,lease],[],[],_remaining(cutoff))[0]
        _need(command not in ready and lease in ready,'CHANNEL_LOST')
        _need(_byte(lease,cutoff)==b'G')
        _need(os.write(gate_w,b'G')==1)
        os.set_blocking(gate_w,False)
        # error EOF needs no repeated poll; command/lease always take precedence.
        streams=[proof_r,error_r,command,lease]
        # The bounded per-read function below uses this local stream list.
        def read_exact(size):
            nonlocal total
            result=bytearray()
            while len(result)<size:
                ready=select.select(streams,[],[],_remaining(cutoff))[0]
                _need(ready,'BUDGET_EXHAUSTED')
                _need(command not in ready and lease not in ready,'CHANNEL_LOST')
                if error_r in ready:
                    _need(os.read(error_r,4096)==b'','NATIVE_STDERR_REJECTED')
                    streams.remove(error_r)
                if proof_r not in ready:continue
                raw=os.read(proof_r,min(size-len(result),4096))
                _need(raw,'NATIVE_FRAME_REJECTED')
                total+=len(raw);_need(total<=65536,'STREAM_OVER_CAP')
                result.extend(raw)
            return bytes(result)
        values=[]
        for index,(role,target) in enumerate((('context','ctx_fixture'),('jobs','oct_fixture'),('context','ctx_fixture'))):
            request=(role+'\n'+target+'\n').encode('ascii')
            _need(os.write(gate_w,request)==len(request))
            if index==2:os.close(gate_w);gate_w=None
            size=int.from_bytes(read_exact(4),'big')
            _need(10<=size<=65532 and size<=65536-total,'STREAM_OVER_CAP')
            values.append(V._decode(read_exact(size),role))
        _need(frame_digest(values)==bundle.expected_sha256,'FIXTURE_ORACLE_REJECTED')
        _need(_until(h.pidfd,cutoff),'BUDGET_EXHAUSTED')
        _reap(h);_need(h.rc==0,'NATIVE_EXIT_REJECTED')
        # No trailing stdout byte or stderr is acceptable even after a prefix.
        _need(_until(proof_r,cutoff) and os.read(proof_r,1)==b'','NATIVE_FRAME_REJECTED')
        _need(_until(error_r,cutoff) and os.read(error_r,1)==b'','NATIVE_STDERR_REJECTED')
        _emit(report,dict(kind='final',nonce=binding.nonce,helper_reaped=True,
                          stdout_eof=True,stderr_eof=True))
    finally:
        if gate_w is not None:os.close(gate_w)
        if h.pid is not None and h.rc is None:_stop_group([h],deadline)
        if h.pidfd is not None:os.close(h.pidfd)


@dataclass(frozen=True)
class NativeOutcome(S.Outcome):
    # inherited capture_allowed means production authorization: always false.
    # Successful fixture read is expressed ONLY by state, never original goal.
    native_fixture: bool = True


class NativeRun(S.Startup):
    """Fresh fixture R. Own native orchestration; inert Startup.run unchanged.

    Shared methods retain PIDFD/ACK/current checks and fixed pipe bookkeeping.
    Source-equivalent cleanup is explicit here to keep accepted startup bytes
    untouched and make this separate executable profile reviewable.
    """
    def __init__(self,issuer,ref,bundle,attempt_seconds=8):
        super().__init__(issuer,ref,attempt_seconds)
        _need(type(bundle) is FixtureBundle)
        self.bundle=bundle

    def _go(self,owner):
        super()._go(owner)
        self.trace[-1]='NATIVE_FIXTURE_G'

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
            self.bundle.check(b.dossier_sha256)
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
            _fork(self.s, _native_supervisor, (*keep, b, self.bundle, self.capture_deadline, deadline),
                  (*keep, *self.bundle.fds), deadline)
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
            self.bundle.check(b.dossier_sha256)
            _need(time.monotonic() < self.capture_deadline)
            self.final = True; self.trace.append('FINAL')
            _need(os.write(owner_w, b'Q') == 1)
            for c in (self.o, self.s):
                _need(_until(c.pidfd, deadline), 'STOP_UNCONFIRMED')
                _reap(c); _need(c.rc == 0)
            _eof(report_r, 512, deadline)
            reason = 'NATIVE_FIXTURE_ONLY'
        except P.Hold as error:
            reason = error.reason
            if reason in ('CLAIM_UNCONFIRMED', 'ATTEMPT_CONSUMED'):
                consumed = True
        except (OSError, ValueError, TypeError, ChildProcessError, V.Hold):
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
        if reason=='NATIVE_FIXTURE_ONLY' and Fraction(time.monotonic())>=Fraction(deadline):
            reason='BUDGET_EXHAUSTED'
        state = 'OFFLINE_NATIVE_FIXTURE_CONFIRMED' if reason == 'NATIVE_FIXTURE_ONLY' else 'UNKNOWN' if consumed else 'HOLD'
        return NativeOutcome(state, reason, tuple(self.trace), consumed, self.go, self.final, self.known,
                       exit_observed, reaper, stdout_eof, stderr_eof,
                       sum(c.rc is not None for c in (self.o, self.s)))

