"""FIXTURE-ONLY fork/pidfd birth-result probe, not a production broker.

Subset topology: fresh E directly creates R and inert H; O/S are NOT launched.
Tests may drop the user-space fork result; candidate never reads test rescue state.
No clone3/native/SQLite/CLI/goal/authority integration and no positive production flag.
"""
from dataclasses import dataclass
from fractions import Fraction
import fcntl
import os
import signal
import time

from . import observer_preflight as P,observer_startup as S


def _idle():
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    while True:signal.pause()


def _h_body():
    S._need(S._byte(0,_child_cutoff)==b'G','GATE_CLOSED')
    S._need(os.write(1,b'inert-birth\n')==12)
    _idle()


@dataclass
class Slot:
    child: S.Child
    state: str = 'RESERVED'
    create_calls: int = 0
    committed: bool = False


@dataclass(frozen=True)
class Result:
    assessment: str
    reason: str
    r_reaped: bool
    helper_created: bool | None
    helper_binding_known: bool
    helper_binding_committed: bool
    helper_reaped: bool | None
    stdout_eof: bool | None
    stderr_eof: bool | None
    cleanup_confirmed: bool
    unknown_creation: bool
    fixture_gate_sent: bool
    inert_ack: bool
    helper_create_calls: int
    elapsed_ms: int
    budget_preserved: bool
    production_feasible: bool = False
    profile_selected: bool = False
    capture_allowed: bool = False
    authorizes_actions: bool = False
    dev_observed: bool = False
    goal_verified: bool = False


class BirthProbe:
    """Trusted fresh E fixture only. Two closed role slots, one attempt.

    E's own returned child identity does not depend on an R/S relay. This does
    NOT make an ambiguous E fork-result or failed pidfd acquisition recoverable.
    """
    def __init__(self,t0):
        self.t0=t0;self.creator=os.getpid();self.used=False
        self.slots={role:Slot(S.Child()) for role in ('R','H')}
        self.fds=[];self.deadline=self.cutoff=None
        self.stdout=self.stderr=None;self.gate_w=None
        self.gate_r=self.out_w=self.err_w=None
        self.gate_sent=self.ack=False

    def _pipe(self):
        pair=os.pipe2(os.O_CLOEXEC);self.fds.extend(pair);return pair

    def _close(self,*fds):
        for fd in fds:
            if fd in self.fds:os.close(fd);self.fds.remove(fd)

    def _fork_once(self,role):
        # Fixed source roles only, never a caller callback/argv/path factory.
        return os.fork()

    def _record_result(self,role,pid):
        slot=self.slots[role];S._need(type(pid) is int and pid>1,'CREATE_RESULT_UNCONFIRMED')
        slot.child.pid=pid
        # Exact unreaped direct child, single-thread fixture E. This eligibility
        # check is NOT proof of all SIGCHLD/deployment interruption conditions.
        os.waitid(os.P_PID,pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
        slot.child.pidfd=os.pidfd_open(pid)  # one acquisition; no retry/fallback
        S._eligible(slot.child)

    def _commit(self,role):
        slot=self.slots[role]
        S._need(slot.child.pidfd is not None,'BINDING_UNCONFIRMED')
        S._need(Fraction(time.monotonic())<self.cutoff,'BUDGET_EXHAUSTED')
        slot.committed=True;slot.state='BOUND'

    def _create(self,role):
        S._need(role in self.slots,'ROLE_REJECTED')
        slot=self.slots[role]
        S._need(slot.state=='RESERVED' and slot.create_calls==0,'SLOT_CONSUMED')
        S._need(Fraction(time.monotonic())<self.cutoff,'BUDGET_EXHAUSTED')
        slot.state='CREATING';slot.create_calls=1;slot.child.attempted=True
        pid=self._fork_once(role)
        if pid==0:
            try:
                global _child_cutoff
                _child_cutoff=self.cutoff
                signal.signal(signal.SIGTERM,signal.SIG_DFL)
                signal.signal(signal.SIGALRM,lambda *_:os._exit(88))
                left=S._remaining(self.deadline)
                if left<=0:os._exit(88)
                signal.setitimer(signal.ITIMER_REAL,left);S._limits()
                if role=='R':
                    S._close_except(());_idle()
                else:
                    copies=[fcntl.fcntl(fd,fcntl.F_DUPFD_CLOEXEC,10)
                            for fd in (self.gate_r,self.out_w,self.err_w)]
                    for target,source in enumerate(copies):os.dup2(source,target,inheritable=True)
                    S._close_except(());_h_body()
                os._exit(0)
            except BaseException:os._exit(2)
        self._record_result(role,pid)
        self._commit(role)

    def _kill_r(self):
        child=self.slots['R'].child;S._eligible(child)
        signal.pidfd_send_signal(child.pidfd,signal.SIGKILL)
        S._need(S._until(child.pidfd,self.deadline),'STOP_UNCONFIRMED')
        S._reap(child);S._need(child.rc is not None,'STOP_UNCONFIRMED')

    def _before_helper(self):pass  # fixed test scheduling boundary, no callback input

    def _r_current(self):
        S._need(not S._ready(self.slots['R'].child.pidfd),'R_LOST')
        S._need(Fraction(time.monotonic())<self.cutoff,'BUDGET_EXHAUSTED')

    def _release(self):
        self._r_current();h=self.slots['H']
        S._need(h.committed and not S._ready(h.child.pidfd),'H_LOST')
        S._need(os.write(self.gate_w,b'G')==1);self.gate_sent=True
        self._close(self.gate_w)

    def _prefix(self):
        raw=bytearray()
        while len(raw)<12:
            self._r_current()
            S._need(S._until(self.stdout,self.cutoff),'BUDGET_EXHAUSTED')
            part=os.read(self.stdout,12-len(raw));S._need(part,'INERT_PREFIX_REJECTED');raw.extend(part)
        S._need(bytes(raw)==b'inert-birth\n','INERT_PREFIX_REJECTED');self.ack=True

    def _now_eof(self,fd,cap):
        total=0
        while S._ready(fd):
            raw=os.read(fd,4096)
            if not raw:return True
            total+=len(raw);S._need(total<=cap,'STREAM_OVER_CAP')
        return False

    def run(self):
        S._need(os.getpid()==self.creator,'ISSUER_PROCESS_CHANGED')
        S._need(not self.used,'ATTEMPT_CONSUMED');self.used=True
        S._need(signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0),'TIMER_UNAVAILABLE')
        budget=P.Budget.start(self.t0,time.monotonic())
        self.deadline=min(budget.attempt_deadline,budget.ta+8);self.cutoff=self.deadline-3
        S._limits()
        previous=signal.getsignal(signal.SIGALRM)
        def expired(*_):raise P.Hold('BUDGET_EXHAUSTED')
        signal.signal(signal.SIGALRM,expired)
        signal.setitimer(signal.ITIMER_REAL,S._remaining(budget.outer_deadline))
        reason='KNOWN_BIRTH_CLEANUP';out_eof=err_eof=None;confirmed=False
        try:
            self.gate_r,self.gate_w=self._pipe()
            self.stdout,self.out_w=self._pipe();self.stderr,self.err_w=self._pipe()
            self._create('R');self._before_helper();self._r_current()
            self._create('H')
            self._close(self.gate_r,self.out_w,self.err_w)
            self._r_current();self._release();self._r_current();self._prefix()
        except P.Hold as error:reason=error.reason
        except (OSError,ValueError):reason='CREATE_RESULT_UNCONFIRMED'
        finally:
            self._close(*(fd for fd in (self.gate_r,self.gate_w,getattr(self,'out_w',None),
                                       getattr(self,'err_w',None)) if fd is not None))
            try:
                # All retained candidates are direct E children from birth;
                # simultaneous stop is a FIXTURE policy, not old S/R authority.
                known=[s.child for s in self.slots.values() if s.child.pidfd is not None]
                S._stop_group(known,self.deadline)
                unknown=any(s.create_calls and s.child.pidfd is None for s in self.slots.values())
                if not unknown:
                    S._eof(self.stdout,65536,self.deadline);out_eof=True
                    S._eof(self.stderr,4096,self.deadline);err_eof=True
                    confirmed=all(c.rc is not None for c in known)
                else:
                    out_eof=self._now_eof(self.stdout,65536);err_eof=self._now_eof(self.stderr,4096)
            except (P.Hold,OSError,TypeError):reason='STOP_UNCONFIRMED';confirmed=False
            for fd in self.fds:os.close(fd)
            self.fds.clear()
            for slot in self.slots.values():
                if slot.child.pidfd is not None:os.close(slot.child.pidfd)
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)
        h=self.slots['H'];ended=time.monotonic()
        preserved=(budget.attempt_deadline-budget.ta<=20 and budget.outer_deadline-budget.t0==45
                   and self.cutoff==self.deadline-3 and Fraction(ended)<self.deadline)
        if not preserved:confirmed=False;reason='STOP_UNCONFIRMED'
        created=True if h.child.pid is not None else None if h.create_calls else False
        return Result('FIXTURE_BIRTH_ONLY_PROFILE_UNBOUND',reason,self.slots['R'].child.rc is not None,
            created,h.child.pidfd is not None,h.committed,True if h.child.rc is not None else None,
            out_eof,err_eof,confirmed,any(s.create_calls and s.child.pidfd is None for s in self.slots.values()),
            self.gate_sent,self.ack,h.create_calls,int((Fraction(ended)-budget.ta)*1000),preserved)
