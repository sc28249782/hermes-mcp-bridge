"""FIXTURE-ONLY ancestor-E feasibility probe, never a containment capability.

Fixed inert Python R/O/S/H only; no native DB/helper/CLI/Facts/planner path.
A known registry can confirm named cleanup but cannot cover withheld H identity.
All outcomes keep production_feasible/profile_selected/action/capture false.
Use only from a fresh isolated trusted E test process, with B's original T0.
"""
from dataclasses import dataclass
from fractions import Fraction
import fcntl
import os
import select
import signal
import time

from . import observer_preflight as P, observer_startup as S

MODES=('known','prefix','s_reaped','before_children','gap','bad_inventory','pidfd_failure')
_emit=S._emit


def _idle():
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    while True:signal.pause()


def _helper(output,error,prefix):
    copies=[fcntl.fcntl(fd,fcntl.F_DUPFD_CLOEXEC,10) for fd in (output,error)]
    for source,target in zip(copies,(1,2)):os.dup2(source,target,inheritable=True)
    S._close_except(())
    if prefix:S._need(os.write(1,b'fixture-prefix\n')==15)
    _idle()


def _supervisor(command,birth,output,error,prefix,deadline):
    h=S.Child()
    S._need(S._byte(command,deadline)==b'A')
    S._fork(h,_helper,(output,error,prefix),(output,error),deadline)
    os.close(output);os.close(error)
    _emit(birth,dict(kind='helper',h=h.pid))
    action=S._byte(command,deadline)
    if action==b'F':
        S._stop_group([h],deadline)
        _emit(birth,dict(kind='s_reaped',h=h.pid,reaped=True))
    else:raise P.Hold('FIXTURE_PROTOCOL')


def _observer(command,report,s_command,s_write,birth,b_write,output,error,mode,cutoff,deadline):
    # This fixture R sets subreaper, but E remains the ancestor after R dies.
    S._subreaper()
    if mode=='before_children':
        _emit(report,dict(kind='empty'))
        _idle()
    o,s=S.Child(),S.Child()
    S._fork(o,_idle,(),(),deadline)
    keep=(s_command,b_write,output,error)
    S._fork(s,_supervisor,(s_command,b_write,output,error,mode=='prefix',deadline),keep,deadline)
    for fd in keep:os.close(fd)
    _emit(report,dict(kind='wrappers',o=o.pid,s=s.pid))
    S._need(S._byte(command,cutoff)==b'A')
    S._need(os.write(s_write,b'A')==1)
    witness=S._frame(birth,cutoff)
    S._need(set(witness)=={'kind','h'} and witness['kind']=='helper')
    if mode=='gap':_emit(report,dict(kind='gap'))
    elif mode=='bad_inventory':_emit(report,dict(kind='helper',h='not-an-identity'))
    else:_emit(report,witness)
    if mode=='s_reaped':
        S._need(S._byte(command,cutoff)==b'F')
        S._need(os.write(s_write,b'F')==1)
        final=S._frame(birth,cutoff)
        _emit(report,final)
    _idle()


@dataclass(frozen=True)
class Assessment:
    assessment: str
    reason: str
    r_exit_reaped: bool
    wrappers_reaped: int
    helper_launch_known: bool
    helper_exit_observed: bool | None
    helper_reaped_by: str | None
    stdout_eof: bool | None
    stderr_eof: bool | None
    report_eof: bool | None
    cleanup_confirmed: bool
    budget_preserved: bool
    elapsed_ms: int
    cleanup_ms: int | None
    attempt_consumed: bool = True
    profile_selected: bool = False
    production_feasible: bool = False
    capture_allowed: bool = False
    authorizes_actions: bool = False
    dev_observed: bool = False
    goal_verified: bool = False


class AncestorProbe:
    """Owned executable counterexample probe, NOT a production guardian.

    Known registry profile deliberately has no atomic pre-enrollment mechanism.
    Missing H registration therefore cannot be repaired within admitted scope.
    Diagnostic test witness is not read by this class and grants it no signals.
    """
    def __init__(self,t0,mode='known'):
        S._need(mode in MODES,'FIXTURE_MODE_REJECTED')
        self.t0,self.mode=t0,mode
        self.creator=os.getpid();self.used=False
        self.r,self.o,self.s,self.h=(S.Child() for _ in range(4))
        self.fds=[];self.deadline=None;self.stdout=self.stderr=None
        self.helper_attempted=False

    def _pipe(self):
        pair=os.pipe2(os.O_CLOEXEC);self.fds.extend(pair);return pair

    def _close(self,*fds):
        for fd in fds:
            if fd in self.fds:os.close(fd);self.fds.remove(fd)

    def _current_r(self):
        S._need(not S._ready(self.r.pidfd),'R_LOST')
        S._need(time.monotonic()<self.cutoff,'BUDGET_EXHAUSTED')

    def _retain(self,child,pid):
        S._need(type(pid) is int and 1<pid<=2147483647,'IDENTITY_UNBOUND')
        self._current_r()
        child.pid=pid;child.pidfd=os.pidfd_open(pid)
        self._current_r()
        S._need(not S._ready(child.pidfd),'ACTOR_LOST')

    def _retain_helper(self,frame):
        S._need(set(frame)=={'kind','h'} and frame['kind']=='helper','IDENTITY_UNBOUND')
        self.helper_attempted=True
        # S is alive and the fixed fixture S has not reaped H before this ACK.
        S._need(not S._ready(self.s.pidfd),'ACTOR_LOST')
        self._retain(self.h,frame['h'])
        S._need(not S._ready(self.s.pidfd),'ACTOR_LOST')

    def _lose_r(self):
        # Fault injection only: exact owned direct fixture child, retained pidfd.
        S._eligible(self.r)
        signal.pidfd_send_signal(self.r.pidfd,signal.SIGKILL)
        S._need(S._until(self.r.pidfd,self.deadline),'STOP_UNCONFIRMED')
        S._reap(self.r);S._need(self.r.rc is not None,'STOP_UNCONFIRMED')

    def _now_eof(self,fd,cap):
        # Missing identity cannot justify waiting/retrying until an alarm saves
        # us. Sample bounded available bytes; no readiness is NOT an exit proof.
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
        self.deadline=min(budget.attempt_deadline,budget.ta+8)
        self.cutoff=self.deadline-3
        # Ta is locked above before the first R launch, unlike old R-local tests.
        S._limits();S._subreaper()
        previous=signal.getsignal(signal.SIGALRM)
        def expired(*_):raise P.Hold('BUDGET_EXHAUSTED')
        signal.signal(signal.SIGALRM,expired)
        signal.setitimer(signal.ITIMER_REAL,S._remaining(budget.outer_deadline))
        report_eof=out_eof=err_eof=exit_observed=None
        loss_at=None
        reaper=None;confirmed=False;s_reaped=False;reason='KNOWN_SET_ONLY_NO_LAUNCH_GAP_COVERAGE'
        cr=cw=rr=rw=None
        try:
            cr,cw=self._pipe();rr,rw=self._pipe()
            sr,sw=self._pipe();br,bw=self._pipe()
            pr,pw=self._pipe();er,ew=self._pipe();self.stdout,self.stderr=pr,er
            keep=(cr,rw,sr,sw,br,bw,pw,ew)
            S._fork(self.r,_observer,(*keep,self.mode,self.cutoff,self.deadline),keep,self.deadline)
            self._close(*keep)
            frame=S._frame(rr,self.cutoff,(self.r.pidfd,))
            if frame=={'kind':'empty'} and self.mode=='before_children':
                reason='EMPTY_FIXTURE_BRANCH_ONLY'
            else:
                S._need(set(frame)=={'kind','o','s'} and frame['kind']=='wrappers','IDENTITY_UNBOUND')
                self._retain(self.o,frame['o']);self._retain(self.s,frame['s'])
                S._need(os.write(cw,b'A')==1)
                frame=S._frame(rr,self.cutoff,(self.r.pidfd,))
                if frame=={'kind':'gap'}:reason='UNREGISTERED_HELPER'
                else:
                    try:self._retain_helper(frame)
                    except (P.Hold,OSError):reason='HELPER_IDENTITY_UNCONFIRMED'
                if self.mode=='s_reaped' and self.h.pidfd is not None:
                    S._need(os.write(cw,b'F')==1)
                    proof=S._frame(rr,self.cutoff,(self.r.pidfd,))
                    S._need(proof=={'kind':'s_reaped','h':self.h.pid,'reaped':True})
                    s_reaped=True
            loss_at=time.monotonic()
            self._lose_r()
            # E is now exact reaper of adopted O/S. The existing primitive
            # requires waitid child eligibility before any retained-pidfd signal.
            S._stop_group([self.o,self.s],self.deadline)
            if self.h.pidfd is not None:
                try:S._eligible(self.h)
                except ChildProcessError:
                    S._need(s_reaped and S._ready(self.h.pidfd),'STOP_UNCONFIRMED')
                    exit_observed=True;reaper='S'
                else:
                    S._stop_group([self.h],self.deadline)
                    exit_observed=self.h.rc is not None;reaper='E' if exit_observed else None
                S._eof(pr,65536,self.deadline);out_eof=True
                S._eof(er,4096,self.deadline);err_eof=True
                confirmed=True
            elif self.mode=='before_children':
                S._eof(pr,65536,self.deadline);out_eof=True
                S._eof(er,4096,self.deadline);err_eof=True
                confirmed=True
            else:
                # This is the measured gap. No scan, P_ALL wait, numeric PID
                # signal, external witness, fresh timer or second H launch.
                out_eof=self._now_eof(pr,65536);err_eof=self._now_eof(er,4096)
            S._eof(rr,512,self.deadline);report_eof=True
        except (P.Hold,OSError,ValueError):
            reason='STOP_UNCONFIRMED';confirmed=False
            # Failure cleanup is restricted to retained, eligible known actors.
            # Never use a raw PID when a fork/pidfd setup result is uncertain.
            try:
                if self.r.pidfd is not None:S._stop_group([self.r],self.deadline)
                S._stop_group([c for c in (self.o,self.s) if c.pidfd is not None],self.deadline)
                if self.h.pidfd is not None:
                    try:S._eligible(self.h)
                    except ChildProcessError:pass
                    else:S._stop_group([self.h],self.deadline)
            except (P.Hold,OSError):pass
        finally:
            for fd in self.fds:os.close(fd)
            self.fds.clear()
            for c in (self.r,self.o,self.s,self.h):
                if c.pidfd is not None:os.close(c.pidfd)
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)
        ended=time.monotonic()
        preserved=(budget.attempt_deadline-budget.ta<=20 and budget.outer_deadline-budget.t0==45
                   and self.cutoff==self.deadline-3 and Fraction(ended)<self.deadline)
        if not preserved:reason='STOP_UNCONFIRMED';confirmed=False
        return Assessment('INFEASIBLE_TESTED_REGISTRY_PROFILE',reason,self.r.rc is not None,
            sum(c.rc is not None for c in (self.o,self.s)),self.h.pidfd is not None,
            exit_observed,reaper,out_eof,err_eof,report_eof,confirmed,preserved,
            int((Fraction(ended)-budget.ta)*1000),None if loss_at is None else int((ended-loss_at)*1000))
