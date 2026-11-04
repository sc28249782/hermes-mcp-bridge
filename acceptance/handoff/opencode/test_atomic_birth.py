"""CLONE_PIDFD fixture evidence; unsupported kernel cases are NOT atomicity passes."""
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[3]
SOURCE=Path(__file__).resolve().parent


def pairs(values):
    result={}
    for k,v in values:
        if k in result:raise AssertionError('duplicate fixture result key')
        result[k]=v
    return result


class AtomicControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=tempfile.TemporaryDirectory(prefix='atomic-birth-owned-')
        cls.addClassCleanup(cls.build.cleanup)
        cls.binary=Path(cls.build.name)/'atomic-probe'
        r=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O2',
            str(SOURCE/'atomic_birth_probe.c'),'-o',str(cls.binary)],capture_output=True,timeout=20)
        if r.returncode:raise AssertionError(r.stderr.decode())
        cls.binary.chmod(0o700)
        print(json.dumps(dict(kind='atomic-birth-build',machine=platform.machine(),kernel=platform.release(),
            source_sha256=hashlib.sha256((SOURCE/'atomic_birth_probe.c').read_bytes()).hexdigest(),
            helper_sha256=hashlib.sha256(cls.binary.read_bytes()).hexdigest(),authenticity_verified=False,
            production_feasible=False),sort_keys=True),flush=True)

    def trial(self,case):
        start=time.monotonic_ns();t0=start-(46_000_000_000 if case=='deadline_guard' else 0)
        r=subprocess.run([str(self.binary),case,str(t0)],stdin=subprocess.DEVNULL,
                         capture_output=True,timeout=12,env={'LANG':'C','LC_ALL':'C','PATH':''})
        self.assertLess(time.monotonic_ns()-start,8_000_000_000)
        self.assertEqual(r.returncode,6 if case=='deadline_guard' else 0,r.stdout)
        self.assertEqual(r.stderr,b'');self.assertLessEqual(len(r.stdout),4096)
        self.assertTrue(r.stdout.endswith(b'\n'));self.assertEqual(r.stdout.count(b'\n'),1)
        v=json.loads(r.stdout,object_pairs_hook=pairs)
        self.assertEqual(set(v),{'status','availability','kernel_error','case_exercised','kernel_copyout_observed',
            'pid_return_used_for_target','pid_return_discarded','candidate_helper_signal_calls','sigchld_verified',
            'signal_seen','create_calls','slot_repeat_denied','r_reaped','candidate','diagnostic','no_children',
            'within_original_deadline','elapsed_ms','full_atomicity_proven'})
        self.assertEqual(set(v['candidate']),{'binding_known','helper_reaped','wnowait_repeatable','wait_consumed',
            'stdout_eof','stderr_eof','cleanup_confirmed','unknown_creation','production_feasible','profile_selected',
            'capture_allowed','authorizes_actions','dev_observed','goal_verified'})
        self.assertEqual(set(v['diagnostic']),{'used','h_live_before','exact_reap','both_eof'})
        self.assertTrue(v['no_children']);self.assertFalse(v['full_atomicity_proven'])
        self.assertFalse(v['pid_return_used_for_target'])
        for flag in ('production_feasible','profile_selected','capture_allowed','authorizes_actions','dev_observed','goal_verified'):
            self.assertIs(v['candidate'][flag],False)
        for private in (str(self.binary),'inert-birth','/proc/',str(t0)):
            self.assertNotIn(private,r.stdout.decode())
        if case!='deadline_guard':self.assertTrue(v['within_original_deadline'])
        self.assertGreaterEqual(v['elapsed_ms'],0);self.assertLess(v['elapsed_ms'],8000)
        if v['availability']=='UNSUPPORTED':
            self.assertEqual(v['status'],'UNSUPPORTED');self.assertFalse(v['case_exercised'])
            self.assertFalse(v['kernel_copyout_observed']);self.assertFalse(v['candidate']['cleanup_confirmed'])
            self.assertFalse(v['diagnostic']['used']);self.assertEqual(v['create_calls'],1)
            self.assertIn(v['kernel_error'],('ENOSYS','DENIED'))
        print(json.dumps(dict(kind='atomic-birth-result',case=case,**v),sort_keys=True),flush=True)
        return v

    def known(self,case):
        v=self.trial(case)
        if v['availability']=='UNSUPPORTED':return v
        self.assertEqual(v['availability'],'SUPPORTED');self.assertTrue(v['case_exercised'])
        self.assertEqual(v['status'],'KERNEL_COPYOUT_OBSERVED');self.assertTrue(v['kernel_copyout_observed'])
        self.assertTrue(v['sigchld_verified']);self.assertTrue(v['r_reaped']);self.assertEqual(v['create_calls'],2)
        for flag in ('binding_known','helper_reaped','wnowait_repeatable','wait_consumed','stdout_eof','stderr_eof','cleanup_confirmed'):
            self.assertIs(v['candidate'][flag],True)
        self.assertFalse(v['candidate']['unknown_creation']);self.assertFalse(v['diagnostic']['used'])
        return v

    def test_real_clone3_child_pidfd_copyout(self):self.known('normal')
    def test_numeric_pid_return_discard_does_not_lose_pidfd_binding(self):
        v=self.known('forget_pid')
        if v['availability']=='SUPPORTED':self.assertTrue(v['pid_return_discarded'])
    def test_actual_r_loss_before_result_acceptance(self):self.known('r_loss')
    def test_r_loss_and_discarded_pid_use_only_kernel_pidfd(self):
        v=self.known('r_loss_forget_pid')
        if v['availability']=='SUPPORTED':self.assertTrue(v['pid_return_discarded'])
    def test_real_nonthrowing_signal_handler_preserves_copyout_slot(self):
        v=self.known('signal_flag')
        if v['availability']=='SUPPORTED':self.assertTrue(v['signal_seen']);self.assertTrue(v['pid_return_discarded'])
    def test_zombie_wnowait_twice_then_one_consume_without_signal(self):
        v=self.known('early_exit')
        if v['availability']=='SUPPORTED':self.assertEqual(v['candidate_helper_signal_calls'],0)
    def error(self,case,status,error):
        v=self.trial(case)
        if v['availability']=='UNSUPPORTED':return
        self.assertEqual(v['availability'],'SUPPORTED');self.assertEqual(v['status'],status)
        self.assertEqual(v['kernel_error'],error);self.assertTrue(v['case_exercised'])
        self.assertFalse(v['kernel_copyout_observed']);self.assertTrue(v['candidate']['unknown_creation'])
        self.assertFalse(v['candidate']['binding_known']);self.assertFalse(v['candidate']['cleanup_confirmed'])
        self.assertFalse(v['diagnostic']['used']);self.assertTrue(v['r_reaped'])
    def test_real_invalid_copyout_address_returns_efault(self):self.error('bad_copyout','COPYOUT_ERROR_UNCONFIRMED','EFAULT')
    def test_real_pidfd_allocation_exhaustion_returns_emfile(self):self.error('fd_exhaustion','FD_EXHAUSTION_UNCONFIRMED','EMFILE')
    def lost(self,case):
        v=self.trial(case)
        if v['availability']=='UNSUPPORTED':return
        self.assertEqual(v['status'],'COPYOUT_METADATA_LOST');self.assertTrue(v['kernel_copyout_observed'])
        self.assertTrue(v['pid_return_discarded']);self.assertTrue(v['candidate']['unknown_creation'])
        self.assertFalse(v['candidate']['binding_known']);self.assertFalse(v['candidate']['helper_reaped'])
        self.assertFalse(v['candidate']['cleanup_confirmed']);self.assertFalse(v['candidate']['stdout_eof'])
        self.assertFalse(v['candidate']['stderr_eof']);self.assertEqual(v['candidate_helper_signal_calls'],0)
        for flag in ('used','h_live_before','exact_reap','both_eof'):self.assertTrue(v['diagnostic'][flag])
    def test_erased_copyout_metadata_keeps_unknown_and_needs_test_rescue(self):self.lost('erase_copyout')
    def test_closed_copyout_handle_does_not_reacquire_from_pid(self):self.lost('close_copyout')
    def test_actual_sigchld_ignore_rejected_before_children(self):
        v=self.trial('sigchld_ignore');self.assertEqual(v['status'],'SIGCHLD_REJECTED')
        self.assertFalse(v['sigchld_verified']);self.assertEqual(v['create_calls'],0)
    def test_actual_sa_nocldwait_rejected_before_children(self):
        v=self.trial('sigchld_nocldwait');self.assertEqual(v['status'],'SIGCHLD_REJECTED')
        self.assertFalse(v['sigchld_verified']);self.assertEqual(v['create_calls'],0)
    def test_slot_reuse_does_not_issue_third_clone(self):
        v=self.known('repeat_slot')
        if v['availability']=='SUPPORTED':self.assertTrue(v['slot_repeat_denied']);self.assertEqual(v['create_calls'],2)
    def test_actual_expired_t0_prevents_any_child_creation(self):
        v=self.trial('deadline_guard');self.assertEqual(v['status'],'BUDGET_REJECTED')
        self.assertEqual(v['create_calls'],0);self.assertFalse(v['within_original_deadline'])
    def test_source_policy_uses_pidfd_target_and_no_fallback(self):
        s=(SOURCE/'atomic_birth_probe.c').read_text()
        self.assertIn('syscall(SYS_clone3',s);self.assertIn('a.flags=CLONE_PIDFD',s)
        self.assertNotIn('SYS_clone,',s);self.assertNotIn('SYS_pidfd_open',s)
        self.assertNotRegex(s,r'\b(?:kill|killpg|waitpid|fork|execve|system)\s*\(')
        self.assertEqual(len(re.findall(r'waitid\(P_ALL',s)),1)
        self.assertIn('harness_no_children',s);self.assertIn('memcmp(&frozen,&result',s)
    def test_source_manifest(self):
        m=json.loads((SOURCE/'atomic-birth-hashes.json').read_bytes())
        for e in m['source']+m['pinned_dependencies']:
            raw=(ROOT/e['path']).read_bytes();self.assertEqual(len(raw),e['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),e['sha256'])
        self.assertEqual(m['primitive'],'clone3_CLONE_PIDFD_only_no_fallback')
        self.assertIs(m['full_atomicity_proven'],False);self.assertIs(m['production_feasible'],False)


if __name__=='__main__':unittest.main(verbosity=2)
