"""Owned cell/view subset; NOT source acceptance or full SM/PB coverage."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent


def strict_pairs(items):
    out={}
    for k,v in items:
        if k in out:raise AssertionError('duplicate key')
        out[k]=v
    return out


class CellViewControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='cell-view-owned-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.binary=Path(cls.temp.name)/'probe'
        p=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O2',
            str(HERE/'cell_view_probe.c'),'-o',str(cls.binary)],capture_output=True,timeout=20)
        if p.returncode:raise AssertionError(p.stderr.decode())
        cls.binary.chmod(0o700)

    def trial(self,case):
        start=time.monotonic_ns();t0=-46_000_000_000 if case=='deadline_guard' else start
        r=subprocess.run([str(self.binary),case,str(t0)],stdin=subprocess.DEVNULL,
            env={'LANG':'C','LC_ALL':'C','PATH':''},capture_output=True,timeout=12)
        self.assertLess(time.monotonic_ns()-start,8_000_000_000)
        self.assertEqual(r.returncode,6 if case=='deadline_guard' else 0,r.stdout)
        self.assertEqual(r.stderr,b'');self.assertLessEqual(len(r.stdout),4096)
        self.assertEqual(r.stdout.count(b'\n'),1);self.assertTrue(r.stdout.endswith(b'\n'))
        v=json.loads(r.stdout,object_pairs_hook=strict_pairs)
        self.assertEqual(set(v),{'kind','state','status','availability','create_calls','slot_consumed',
            'initial_commit','restore_calls','restore_ok','second_restore_denied','publication_rejected',
            'fd_reused','closed_after_exact_reap','post_fault_target_calls','candidate','diagnostic',
            'candidate_result_frozen','no_children','within_original_deadline','terminal',
            'production_feasible','profile_selected','capture_allowed','authorizes_actions','dev_observed',
            'goal_verified','full_atomicity_proven'})
        self.assertEqual(set(v['candidate']),{'binding_known','helper_reaped','wnowait_repeatable',
            'wait_consumed','stdout_eof','stderr_eof','cleanup_confirmed'})
        self.assertEqual(set(v['diagnostic']),{'used','h_live_before','exact_reap','both_eof'})
        self.assertEqual(v['state'],'UNKNOWN');self.assertEqual(v['kind'],'cell-view-result')
        self.assertTrue(v['no_children']);self.assertTrue(v['candidate_result_frozen'])
        self.assertEqual(v['post_fault_target_calls'],0)
        for flag in ('production_feasible','profile_selected','capture_allowed','authorizes_actions',
                     'dev_observed','goal_verified','full_atomicity_proven'):
            self.assertIs(v[flag],False)
        for private in (str(self.binary),str(t0),'/proc/'):
            self.assertNotIn(private,r.stdout.decode())
        if case!='deadline_guard':self.assertTrue(v['within_original_deadline'])
        if v['availability']=='UNSUPPORTED':
            self.assertEqual(v['status'],'UNSUPPORTED');self.assertEqual(v['create_calls'],1)
            self.assertFalse(v['candidate']['cleanup_confirmed']);self.assertFalse(v['diagnostic']['used'])
            self.assertFalse(v['initial_commit']);self.assertEqual(v['restore_calls'],0)
        else:
            self.assertEqual(v['availability'],'NOT_PROBED' if case=='deadline_guard' else 'SUPPORTED')
        print(json.dumps(dict(case=case,**v),sort_keys=True),flush=True)
        return v

    def clean(self,case):
        v=self.trial(case)
        if v['availability']=='UNSUPPORTED':return v
        self.assertEqual(v['create_calls'],1);self.assertTrue(v['slot_consumed'])
        for flag in v['candidate']:self.assertIs(v['candidate'][flag],True)
        self.assertFalse(v['diagnostic']['used']);self.assertTrue(v['terminal'])
        return v

    def test_original_bound_cell_cleanup(self):
        v=self.clean('normal')
        if v['availability']=='SUPPORTED':self.assertTrue(v['initial_commit'])
    def test_erased_view_rebuilds_from_retained_cell_cleanup_only(self):
        v=self.clean('view_erased')
        if v['availability']=='SUPPORTED':
            self.assertTrue(v['restore_ok']);self.assertEqual(v['restore_calls'],1)
    def test_second_restore_denied_without_second_child(self):
        v=self.clean('restore_twice')
        if v['availability']=='SUPPORTED':
            self.assertTrue(v['restore_ok']);self.assertTrue(v['second_restore_denied'])
            self.assertEqual(v['restore_calls'],2)
    def publication(self,case):
        v=self.clean(case)
        if v['availability']=='SUPPORTED':
            self.assertFalse(v['initial_commit']);self.assertTrue(v['publication_rejected'])
            self.assertEqual(v['restore_calls'],0)
    def test_fault_before_publication(self):self.publication('before_publish')
    def test_marker_with_incomplete_tuple_rejected(self):self.publication('partial_publish')
    def test_stale_generation_publication_rejected(self):self.publication('stale_publish')
    def proof_lost(self,case):
        v=self.trial(case)
        if v['availability']=='UNSUPPORTED':return
        for flag in v['candidate']:self.assertIs(v['candidate'][flag],False)
        self.assertTrue(v['slot_consumed']);self.assertFalse(v['restore_ok'])
        for flag in v['diagnostic']:self.assertIs(v['diagnostic'][flag],True)
    def test_wrong_generation_aborts_and_diagnostic_stays_separate(self):self.proof_lost('wrong_generation')
    def test_revoked_cell_denies_restore_and_candidate_target(self):self.proof_lost('revoked')
    def test_corrupt_cell_source_and_erased_view_remain_unknown(self):self.proof_lost('cell_corrupt')
    def closed(self,case):
        v=self.trial(case)
        if v['availability']=='UNSUPPORTED':return v
        self.assertEqual(v['status'],'HANDLE_LOST');self.assertTrue(v['closed_after_exact_reap'])
        self.assertFalse(v['candidate']['binding_known']);self.assertFalse(v['candidate']['helper_reaped'])
        self.assertFalse(v['candidate']['cleanup_confirmed']);self.assertFalse(v['diagnostic']['used'])
        self.assertTrue(v['candidate']['stdout_eof']);self.assertTrue(v['candidate']['stderr_eof'])
        return v
    def test_actual_close_after_reap_does_not_reconstruct_handle(self):self.closed('closed_handle')
    def test_actual_closed_fd_reused_for_owned_pipe_is_never_a_target(self):
        v=self.closed('closed_reused')
        if v['availability']=='SUPPORTED':self.assertTrue(v['fd_reused'])
    def test_expired_signed_t0_rejects_before_create(self):
        v=self.trial('deadline_guard');self.assertEqual(v['status'],'BUDGET_REJECTED')
        self.assertEqual(v['create_calls'],0);self.assertFalse(v['within_original_deadline'])
        self.assertFalse(v['slot_consumed'])
    def test_source_policy_has_no_helper_handle_backup_or_fallback(self):
        s=(HERE/'cell_view_probe.c').read_text()
        self.assertEqual(s.count('syscall(SYS_clone3,'),1)
        self.assertIn('args.flags=CLONE_PIDFD',s)
        self.assertNotRegex(s,r'\b(?:kill|killpg|waitpid|fork|execve|system)\s*\(')
        for banned in ('SYS_pidfd_open','SYS_clone,','SCM_RIGHTS','pidfd_getfd','/proc/'):
            self.assertNotIn(banned,s)
        self.assertNotRegex(s,r'fcntl\(c\.fd,')
        self.assertIn('dup2(spare[1],c.fd)',s)  # only unrelated pipe reuse, after exact reap
        self.assertEqual(s.count('waitid(P_ALL'),1)
        self.assertIn('memcmp(&frozen,&result',s)
        self.assertIn('if(!allowed(c))return 0;',s)
    def test_source_manifest(self):
        m=json.loads((HERE/'cell-view-hashes.json').read_bytes())
        for e in m['source']+m['pinned_dependencies']:
            raw=(ROOT/e['path']).read_bytes();self.assertEqual(len(raw),e['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),e['sha256'])
        self.assertIs(m['production_feasible'],False);self.assertIs(m['full_sm_acceptance'],False)
        self.assertEqual(m['helper_pidfds'],1)


if __name__=='__main__':unittest.main(verbosity=2)
