"""Owned birth-boundary controls. Diagnostic pidfd is never candidate authority."""
from dataclasses import asdict
import ast
from fractions import Fraction
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
from acceptance.handoff.opencode import birth_probe as A,observer_startup as S,observer_preflight as P


def subreaper():
    import ctypes
    libc=ctypes.CDLL(None);libc.prctl.argtypes=[ctypes.c_int]+[ctypes.c_ulong]*4
    v=ctypes.c_int()
    if libc.prctl(37,ctypes.addressof(v),0,0,0)!=0:raise AssertionError('fixture setting')
    return v.value


class BirthControls(unittest.TestCase):
    def trial(self,case='normal'):
        before=subreaper();t0=time.monotonic();read,write=os.pipe2(os.O_CLOEXEC)
        ep=os.fork()
        if ep==0:
            S._close_except((write,));signal.signal(signal.SIGCHLD,signal.SIG_DFL)
            try:
                probe=A.BirthProbe(t0);diag=S.Child();readers=[];forks=[]
                record=A.BirthProbe._record_result;commit=A.BirthProbe._commit
                release=A.BirthProbe._release;fork=A.BirthProbe._fork_once
                real_signal=signal.pidfd_send_signal
                def capture(probe,pid):
                    # TEST ONLY: actual E fork return, before injected loss.
                    # No relay/PID scan; the candidate never sees this handle.
                    diag.pid=pid;diag.pidfd=os.pidfd_open(pid)
                    readers.extend((os.dup(probe.stdout),os.dup(probe.stderr)))
                def recording(probe,role,pid):
                    if role=='H':
                        capture(probe,pid)
                        if case=='early_exit' and not S._until(diag.pidfd,probe.cutoff):raise AssertionError('H did not exit')
                        if case=='r_after_fork':probe._kill_r()
                        if case in ('lost_result','lost_nonreading'):raise P.Hold('CREATE_RESULT_LOST')
                        if case=='pidfd_failure':
                            with mock.patch.object(A.os,'pidfd_open',side_effect=OSError('fixture fault')) as opened:
                                try:return record(probe,role,pid)
                                finally:opened.assert_called_once_with(pid)
                    return record(probe,role,pid)
                def committing(probe,role):
                    if role=='H' and case=='commit_failure':raise P.Hold('SLOT_COMMIT_UNCONFIRMED')
                    commit(probe,role)
                    if role=='H' and case=='r_after_bind':probe._kill_r()
                def releasing(probe):
                    release(probe)
                    if case=='r_after_gate':probe._kill_r()
                def before_helper(probe):
                    if case=='r_before_helper':probe._kill_r()
                def forking(probe,role):
                    forks.append(role)
                    if role=='H' and case=='create_failure':raise OSError('injected before H fork')
                    return fork(probe,role)
                def body():
                    if case=='early_exit':return
                    if case=='lost_nonreading':A._idle()
                    return h_body()
                def signalling(fd,sig,*args):
                    if case=='early_exit' and fd==probe.slots['H'].child.pidfd:
                        raise AssertionError('signal to already exited H')
                    return real_signal(fd,sig,*args)
                h_body=A._h_body
                with mock.patch.object(A.BirthProbe,'_record_result',recording), \
                     mock.patch.object(A.BirthProbe,'_commit',committing), \
                     mock.patch.object(A.BirthProbe,'_release',releasing), \
                     mock.patch.object(A.BirthProbe,'_before_helper',before_helper), \
                     mock.patch.object(A.BirthProbe,'_fork_once',forking), \
                     mock.patch.object(A,'_h_body',side_effect=body), \
                     mock.patch.object(signal,'pidfd_send_signal',side_effect=signalling):
                    result=probe.run()
                    if case=='reuse':
                        try:probe.run()
                        except P.Hold as error:
                            if error.reason!='ATTEMPT_CONSUMED':raise
                        else:raise AssertionError('attempt repeated')
                    if case=='duplicate_slot':
                        try:probe._create('H')
                        except P.Hold as error:
                            if error.reason!='SLOT_CONSUMED':raise
                        else:raise AssertionError('slot reused')
                if forks.count('R')!=1 or forks.count('H')!=(0 if case=='r_before_helper' else 1):
                    raise AssertionError('unexpected launch count')
                diagnostic={'used':False}
                if case in ('lost_result','lost_nonreading','pidfd_failure'):
                    if result.helper_binding_known or result.cleanup_confirmed or result.helper_reaped is not None:
                        raise AssertionError('diagnostic leaked into candidate')
                    live=not S._ready(diag.pidfd)
                    if case=='lost_nonreading' and not live:raise AssertionError('nonreading H already stopped')
                    S._eligible(diag);S._stop_group([diag],probe.deadline)
                    for fd,cap in zip(readers,(65536,4096)):S._eof(fd,cap,probe.deadline)
                    diagnostic=dict(used=True,h_live_before=live,exact_reap=diag.rc is not None,
                        both_eof=True,within_original_deadline=Fraction(time.monotonic())<probe.deadline)
                    if not diagnostic['exact_reap'] or not diagnostic['within_original_deadline']:raise AssertionError('diagnostic failed')
                try:os.waitpid(-1,os.WNOHANG)
                except ChildProcessError:no_children=True
                else:raise AssertionError('fixture child remains')
                if diag.pidfd is not None:os.close(diag.pidfd)
                for fd in readers:os.close(fd)
                payload=dict(candidate=asdict(result),diagnostic=diagnostic,no_children=no_children,
                             create_invocations=len(forks))
                raw=json.dumps(payload,sort_keys=True).encode()+b'\n'
                if len(raw)>4096 or os.write(write,raw)!=len(raw):os._exit(4)
                os._exit(0)
            except BaseException as error:
                os.write(write,json.dumps({'test_error':type(error).__name__}).encode()+b'\n');os._exit(3)
        os.close(write);efd=os.pidfd_open(ep)
        try:
            self.assertTrue(select.select([efd],[],[],15)[0],'E fixture timed out')
            pid,status=os.waitpid(ep,0);self.assertEqual(pid,ep)
            self.assertLess(time.monotonic()-t0,8,'B/E lifecycle exceeded fixture bound')
            raw=os.read(read,4096);self.assertEqual(os.waitstatus_to_exitcode(status),0,raw)
            self.assertEqual(os.read(read,1),b'');self.assertEqual(subreaper(),before)
            v=json.loads(raw);r=v['candidate'];self.assertTrue(v['no_children'])
            for flag in ('production_feasible','profile_selected','capture_allowed','authorizes_actions','dev_observed','goal_verified'):
                self.assertIs(r[flag],False)
            self.assertTrue(r['r_reaped']);self.assertTrue(r['budget_preserved']);self.assertLess(r['elapsed_ms'],8000)
            self.assertNotIn('inert-birth',raw.decode())
            print(json.dumps({'kind':'birth-feasibility-result','case':case,**v},sort_keys=True),flush=True)
            return v
        finally:os.close(efd);os.close(read)

    def test_inert_gate_and_exact_direct_child_cleanup(self):
        r=self.trial()['candidate'];self.assertTrue(r['helper_binding_committed']);self.assertTrue(r['inert_ack'])
        self.assertTrue(r['fixture_gate_sent']);self.assertTrue(r['cleanup_confirmed']);self.assertTrue(r['helper_reaped'])
    def test_r_loss_before_helper_prevents_any_h_create(self):
        r=self.trial('r_before_helper')['candidate'];self.assertEqual(r['helper_create_calls'],0)
        self.assertIs(r['helper_created'],False);self.assertFalse(r['fixture_gate_sent']);self.assertTrue(r['cleanup_confirmed'])
    def loss(self,case,gate=False):
        r=self.trial(case)['candidate'];self.assertEqual(r['reason'],'R_LOST')
        self.assertTrue(r['helper_binding_known']);self.assertTrue(r['helper_reaped']);self.assertTrue(r['cleanup_confirmed'])
        self.assertIs(r['fixture_gate_sent'],gate);self.assertFalse(r['inert_ack'])
    def test_r_loss_after_actual_h_fork_before_result_storage(self):self.loss('r_after_fork')
    def test_r_loss_after_h_binding_before_gate(self):self.loss('r_after_bind')
    def test_r_loss_after_inert_gate_never_publishes_ack(self):self.loss('r_after_gate',True)
    def ambiguous(self,case):
        v=self.trial(case);r=v['candidate'];self.assertTrue(r['unknown_creation'])
        self.assertFalse(r['fixture_gate_sent']);self.assertFalse(r['helper_binding_known']);self.assertFalse(r['cleanup_confirmed'])
        self.assertIsNone(r['helper_reaped']);self.assertTrue(v['diagnostic']['used'])
        return v
    def test_dropped_create_result_does_not_turn_eof_into_reap(self):
        r=self.ambiguous('lost_result')['candidate'];self.assertIsNone(r['helper_created'])
    def test_lost_result_with_nonreading_h_leaves_live_unregistered(self):
        v=self.ambiguous('lost_nonreading');self.assertTrue(v['diagnostic']['h_live_before'])
        self.assertFalse(v['candidate']['stdout_eof']);self.assertFalse(v['candidate']['stderr_eof'])
    def test_pidfd_failure_has_one_attempt_and_no_numeric_fallback(self):
        r=self.ambiguous('pidfd_failure')['candidate'];self.assertTrue(r['helper_created'])
    def test_retained_handle_survives_slot_commit_fault_for_cleanup_only(self):
        r=self.trial('commit_failure')['candidate'];self.assertFalse(r['helper_binding_committed'])
        self.assertTrue(r['helper_binding_known']);self.assertTrue(r['cleanup_confirmed']);self.assertFalse(r['fixture_gate_sent'])
    def test_unreaped_exited_child_can_bind_without_second_signal(self):
        r=self.trial('early_exit')['candidate'];self.assertEqual(r['reason'],'H_LOST')
        self.assertTrue(r['helper_reaped']);self.assertTrue(r['helper_binding_known']);self.assertFalse(r['fixture_gate_sent'])
    def test_definite_injected_fork_error_is_not_claimed_as_no_child(self):
        r=self.trial('create_failure')['candidate'];self.assertTrue(r['unknown_creation']);self.assertIsNone(r['helper_created'])
        self.assertFalse(r['cleanup_confirmed']);self.assertFalse(r['fixture_gate_sent'])
    def test_same_object_cannot_repeat_attempt(self):self.trial('reuse')
    def test_same_slot_cannot_create_second_helper(self):self.trial('duplicate_slot')
    def test_exact_budget_and_invalid_role_fail_before_creation(self):
        b=P.Budget.start(1.0,2.0);self.assertEqual(b.attempt_deadline-b.ta,20);self.assertEqual(b.outer_deadline-b.t0,45)
        p=A.BirthProbe(time.monotonic())
        with self.assertRaises(P.Hold):p._create('outside_roster')
        self.assertTrue(all(s.create_calls==0 for s in p.slots.values()))
    def test_source_has_no_scan_exec_numeric_signal_or_role_expansion(self):
        s=(Path(__file__).parent/'birth_probe.py').read_text();t=ast.parse(s)
        calls=[ast.unparse(n.func) for n in ast.walk(t) if isinstance(n,ast.Call)]
        for name in ('os.kill','os.killpg','os.execve','subprocess.Popen','os.waitpid'):self.assertNotIn(name,calls)
        self.assertEqual(calls.count('os.fork'),1)
    def test_hash_manifest(self):
        m=json.loads((Path(__file__).parent/'birth-probe-hashes.json').read_bytes())
        for e in m['source']+m['pinned_dependencies']:
            raw=(ROOT/e['path']).read_bytes();self.assertEqual(len(raw),e['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),e['sha256'])
        self.assertIs(m['production_feasible'],False);self.assertIs(m['authorizes_actions'],False)


if __name__=='__main__':unittest.main(verbosity=2)
