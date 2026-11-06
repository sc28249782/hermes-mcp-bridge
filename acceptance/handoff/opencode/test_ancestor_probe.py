"""Owned ancestor-E feasibility controls; diagnostic rescue is NOT candidate proof."""
from dataclasses import asdict
from fractions import Fraction
import ast
import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import sys
import time
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from acceptance.handoff.opencode import ancestor_probe as A,observer_startup as S,observer_preflight as P
SOURCE=Path(__file__).resolve().parent


def setting():
    libc=ctypes.CDLL(None);libc.prctl.argtypes=[ctypes.c_int]+[ctypes.c_ulong]*4
    value=ctypes.c_int()
    if libc.prctl(37,ctypes.addressof(value),0,0,0)!=0:raise AssertionError('fixture subreaper query')
    return value.value


class AncestorControls(unittest.TestCase):
    def trial(self,case='known'):
        before=setting();t0=time.monotonic()  # B locks T0 BEFORE fresh E launch.
        read,write=os.pipe2(os.O_CLOEXEC)
        ep=os.fork()
        if ep==0:
            S._close_except((write,))
            try:
                er,ew=os.pipe2(os.O_CLOEXEC);os.dup2(ew,201,inheritable=True)
                e_pid=os.getpid();real_emit=A._emit;real_close=S._close_except
                original_retain=A.AncestorProbe._retain_helper
                original_loss=A.AncestorProbe._lose_r
                real_signal=signal.pidfd_send_signal
                diag=S.Child();readers=[];before_adopt_denied=[False]
                def emitting(fd,frame):
                    # Extra TEST ONLY S-to-harness channel. R's relay does not
                    # publish a second diagnostic copy; candidate never reads it.
                    if frame.get('kind')=='helper' and os.getppid()!=e_pid:
                        raw=json.dumps(frame,separators=(',',':')).encode()+b'\n'
                        if len(raw)>512 or os.write(201,raw)!=len(raw):raise AssertionError('private birth witness')
                    return real_emit(fd,frame)
                def closing(keep):return real_close((*keep,201))
                def diagnostic_binding(probe):
                    if diag.pidfd is not None or case=='before_children':return
                    frame=S._frame(er,probe.cutoff)
                    if set(frame)!={'kind','h'} or frame['kind']!='helper' or type(frame['h']) is not int:
                        raise AssertionError('diagnostic witness invalid')
                    # This identity is from actual owned S while H is unreaped,
                    # not host enumeration or a backend PID. It is NOT registered
                    # in probe.h and cannot authorize any candidate stop.
                    diag.pid=frame['h'];diag.pidfd=os.pidfd_open(diag.pid)
                    if S._ready(diag.pidfd):raise AssertionError('diagnostic H already exited')
                    readers.extend((os.dup(probe.stdout),os.dup(probe.stderr)))
                def retain(probe,frame):
                    diagnostic_binding(probe)
                    if case=='pidfd_failure':
                        with mock.patch.object(A.os,'pidfd_open',side_effect=OSError('fixture fd failure')) as opened:
                            try:return original_retain(probe,frame)
                            finally:opened.assert_called_once_with(frame['h'])
                    return original_retain(probe,frame)
                def lose(probe):
                    diagnostic_binding(probe)
                    if case=='adoption_guard':
                        with mock.patch.object(S.signal,'pidfd_send_signal',side_effect=AssertionError('premature H signal')) as sent:
                            try:S._signal(diag,signal.SIGTERM)
                            except ChildProcessError:before_adopt_denied[0]=True
                            else:raise AssertionError('H adopted before R/S death')
                            sent.assert_not_called()
                    return original_loss(probe)
                mode='known' if case in ('reuse','adoption_guard') else case
                probe=A.AncestorProbe(t0,mode)
                def signalling(fd,sig,*args):
                    if case=='s_reaped' and os.getpid()==e_pid and fd==probe.h.pidfd:
                        raise AssertionError('E signalled already S-reaped H')
                    return real_signal(fd,sig,*args)
                with mock.patch.object(A,'_emit',side_effect=emitting),mock.patch.object(S,'_close_except',side_effect=closing), \
                     mock.patch.object(A.AncestorProbe,'_retain_helper',retain),mock.patch.object(A.AncestorProbe,'_lose_r',lose), \
                     mock.patch.object(signal,'pidfd_send_signal',side_effect=signalling):
                    result=probe.run()
                    if case=='reuse':
                        try:probe.run()
                        except P.Hold as error:
                            if error.reason!='ATTEMPT_CONSUMED':raise
                        else:raise AssertionError('same attempt repeated')
                diagnostic={'used':False}
                if case in ('gap','bad_inventory','pidfd_failure'):
                    if result.cleanup_confirmed or result.production_feasible or result.helper_exit_observed is not None:
                        raise AssertionError('candidate borrowed diagnostic proof')
                    if diag.pidfd is None or S._ready(diag.pidfd):raise AssertionError('unknown H not alive after candidate return')
                    if any(S._ready(fd) for fd in readers):raise AssertionError('unknown H unexpectedly reached EOF')
                    # Source already returned INFEASIBLE. Only THIS test harness
                    # now uses its additional capability, within ORIGINAL D.
                    S._eligible(diag);S._stop_group([diag],probe.deadline)
                    for fd,cap in zip(readers,(65536,4096)):S._eof(fd,cap,probe.deadline)
                    if diag.rc is None:raise AssertionError('diagnostic did not reap exact H')
                    diagnostic=dict(used=True,h_live_before=True,exact_reap=True,both_eof=True,
                        within_original_deadline=Fraction(time.monotonic())<probe.deadline)
                    if not diagnostic['within_original_deadline']:raise AssertionError('late test rescue')
                try:os.waitpid(-1,os.WNOHANG)
                except ChildProcessError:no_children=True
                else:raise AssertionError('remaining fixture child')
                if case=='adoption_guard' and not before_adopt_denied[0]:raise AssertionError('guard stimulus absent')
                payload=dict(candidate=asdict(result),diagnostic=diagnostic,no_children=no_children,
                    pre_adoption_denied=before_adopt_denied[0])
                for fd in readers:os.close(fd)
                if diag.pidfd is not None:os.close(diag.pidfd)
                for fd in (er,ew,201):os.close(fd)
                raw=json.dumps(payload,sort_keys=True).encode()+b'\n'
                if len(raw)>4096 or os.write(write,raw)!=len(raw):os._exit(4)
                os._exit(0)
            except BaseException as error:
                os.write(write,json.dumps({'test_error':type(error).__name__}).encode()+b'\n');os._exit(3)
        os.close(write);efd=os.pidfd_open(ep)
        try:
            self.assertTrue(select.select([efd],[],[],15)[0],'fixture E did not finish')
            pid,status=os.waitpid(ep,0);self.assertEqual(pid,ep)
            self.assertLess(time.monotonic()-t0,8,'B/E fixture lifecycle exceeded original bound')
            raw=os.read(read,4096);self.assertEqual(os.waitstatus_to_exitcode(status),0,raw)
            self.assertEqual(os.read(read,1),b'');self.assertEqual(setting(),before)
            v=json.loads(raw);self.assertTrue(v['no_children']);r=v['candidate']
            for flag in ('production_feasible','profile_selected','capture_allowed','authorizes_actions','dev_observed','goal_verified'):
                self.assertIs(r[flag],False)
            self.assertEqual(r['assessment'],'INFEASIBLE_TESTED_REGISTRY_PROFILE')
            self.assertTrue(r['r_exit_reaped']);self.assertTrue(r['budget_preserved'])
            self.assertGreaterEqual(r['elapsed_ms'],0);self.assertLess(r['elapsed_ms'],8000)
            self.assertIsNotNone(r['cleanup_ms']);self.assertGreaterEqual(r['cleanup_ms'],0);self.assertLess(r['cleanup_ms'],3000)
            self.assertNotIn('fixture-prefix',raw.decode())
            self.assertEqual(set(r),{f.name for f in __import__('dataclasses').fields(A.Assessment)})
            print(json.dumps({'kind':'ancestor-feasibility-result','case':case,**v},sort_keys=True),flush=True)
            return v
        finally:os.close(efd);os.close(read)

    def test_known_inventory_cleans_up_but_profile_remains_infeasible(self):
        v=self.trial();r=v['candidate'];self.assertTrue(r['cleanup_confirmed'])
        self.assertEqual(r['helper_reaped_by'],'E');self.assertEqual(r['wrappers_reaped'],2)
        self.assertTrue(r['stdout_eof']);self.assertTrue(r['stderr_eof']);self.assertTrue(r['report_eof'])
        self.assertFalse(v['diagnostic']['used'])
    def test_known_prefix_discard_is_not_goal_completion(self):
        r=self.trial('prefix')['candidate'];self.assertTrue(r['cleanup_confirmed']);self.assertEqual(r['helper_reaped_by'],'E')
    def test_s_reaped_helper_is_not_reaped_or_signalled_again_by_e(self):
        r=self.trial('s_reaped')['candidate'];self.assertTrue(r['cleanup_confirmed']);self.assertEqual(r['helper_reaped_by'],'S')
    def test_r_dies_before_controlled_empty_branch_creates_wrappers(self):
        r=self.trial('before_children')['candidate'];self.assertTrue(r['cleanup_confirmed']);self.assertEqual(r['wrappers_reaped'],0)
        self.assertFalse(r['helper_launch_known']);self.assertIsNone(r['helper_exit_observed'])
    def missing(self,case):
        v=self.trial(case);r=v['candidate'];self.assertFalse(r['cleanup_confirmed'])
        self.assertFalse(r['helper_launch_known']);self.assertIsNone(r['helper_exit_observed']);self.assertIsNone(r['helper_reaped_by'])
        self.assertFalse(r['stdout_eof']);self.assertFalse(r['stderr_eof']);self.assertTrue(r['report_eof'])
        self.assertEqual(r['wrappers_reaped'],2);self.assertTrue(v['diagnostic']['used'])
    def test_real_h_spawn_before_withheld_registration_leaves_live_unknown(self):self.missing('gap')
    def test_malformed_registration_cannot_borrow_test_witness(self):self.missing('bad_inventory')
    def test_pidfd_failure_has_no_fallback_or_diagnostic_repair(self):self.missing('pidfd_failure')
    def test_same_probe_object_does_not_repeat_attempt(self):self.trial('reuse')
    def test_pre_adoption_signal_denied_before_actual_r_loss(self):self.trial('adoption_guard')
    def test_exact_budget_and_cap_before_r_launch(self):
        b=P.Budget.start(10.0,12.0);self.assertEqual(b.ta,Fraction(12));self.assertEqual(b.attempt_deadline-b.ta,20)
        self.assertEqual(b.outer_deadline-b.t0,45);self.assertEqual(b.attempt_deadline-b.capture_deadline,3)
    def test_source_has_no_inventory_numeric_signal_or_runtime_dispatch(self):
        tree=ast.parse((SOURCE/'ancestor_probe.py').read_text())
        calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        for forbidden in ('os.kill','os.killpg','os.waitpid','os.waitid','subprocess.Popen','os.execve'):
            self.assertNotIn(forbidden,calls)
        self.assertNotIn('SCM_RIGHTS',(SOURCE/'ancestor_probe.py').read_text())
    def test_source_manifest(self):
        m=json.loads((SOURCE/'ancestor-probe-hashes.json').read_bytes())
        for e in m['source']+m['pinned_dependencies']:
            raw=(ROOT/e['path']).read_bytes();self.assertEqual(len(raw),e['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),e['sha256'])
        self.assertIs(m['production_feasible'],False);self.assertIs(m['authorizes_actions'],False)


if __name__=='__main__':unittest.main(verbosity=2)
