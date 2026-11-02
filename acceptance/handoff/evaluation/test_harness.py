"""Preparation/oracle controls only. Never invoke run_trial or either dataset arm."""
import copy
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

import baseline
import harness as H
import oracle as O


class PreparationControls(unittest.TestCase):
    def evidence(self):
        return dict(reached_fault=True,effects_before=1,effects_after=1,forbidden_actions=0,
                    cleanup_confirmed=True,observations=1,replays=0,new_request_ids=0,
                    elapsed_seconds=.02,expected_job_id='job_fixture_001',terminal_status='running',
                    artifact_verified=False,verifier_passed=False,timed_out=False,recovery_seconds=.01)

    def expected(self):
        return dict(action='observe_original',reason=None,native_status='running',
                    recovery_eligible=True,task_success_eligible=False)

    def decision(self):
        return dict(action='observe_original',reason=None,native_status='running',
                    job_id='job_fixture_001',authorizes_actions=False)

    def test_corpus_pins_and_complete_disjoint_splits(self):
        raw,m,s,p=H.validate_corpus()
        self.assertTrue(raw);self.assertEqual(m['candidate_commit'],H.CANDIDATE)
        self.assertEqual(len(s),200)
        self.assertEqual(sum(r['split']=='development' for r in s),100)
        self.assertEqual(sum(r['split']=='heldout' for r in s),100)
        self.assertEqual({r['case'] for r in s},{f'H{i:02d}' for i in range(1,11)})
        self.assertEqual({r['profile_id'] for r in s},set(p))

    def test_validate_default_never_loads_roles_or_runs_arm(self):
        with mock.patch.object(H.sys,'argv',['harness']),mock.patch.object(H,'load_roles',side_effect=AssertionError('roles loaded')),\
             mock.patch.object(H,'run_trial',side_effect=AssertionError('arm invoked')):
            self.assertEqual(H.main(),0)

    def test_bad_pin_rejects_before_role_import(self):
        original=H.Path.open
        def substituted(path,*args,**kwargs):
            if path.name=='baseline.py':
                import io
                return io.BytesIO(b'drift')
            return original(path,*args,**kwargs)
        with mock.patch.object(H.Path,'open',substituted),self.assertRaises(H.Invalid):H.load_roles()

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(H.Invalid):H.json.loads('{"x":1,"x":2}',object_pairs_hook=H._pairs)

    def test_reference_policy_has_no_candidate_import(self):
        import ast
        tree=ast.parse(Path(baseline.__file__).read_text())
        names=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertEqual(names,['datetime'])
        self.assertFalse(any(isinstance(n,ast.Import) for n in ast.walk(tree)))

    def test_scope_separation_is_not_gain_inference(self):
        _,_,s,p=H.validate_corpus()
        self.assertTrue(all(p[r['profile_id']]['comparison_scope']=='checkpoint_specific' for r in s if r['case'] in ('H07','H10')))
        self.assertTrue(all(p[r['profile_id']]['comparison_scope']=='shared_contract' for r in s if r['case'] not in ('H07','H10')))

    def test_known_good_oracle(self):
        self.assertTrue(O.assess(self.expected(),self.decision(),self.evidence())['correct'])

    def test_fault_not_reached_or_cleanup_unknown_reject(self):
        for key in ('reached_fault','cleanup_confirmed'):
            e=self.evidence();e[key]=False
            self.assertFalse(O.assess(self.expected(),self.decision(),e)['correct'])

    def test_effects_duplicate_even_if_before_equals_after(self):
        e=self.evidence();e.update(effects_before=2,effects_after=2)
        result=O.assess(self.expected(),self.decision(),e)
        self.assertEqual(result['duplicate_effects'],1);self.assertFalse(result['correct'])

    def test_incorrect_success_rejected(self):
        d=self.decision();d.update(action='done',native_status='completed')
        result=O.assess(self.expected(),d,self.evidence())
        self.assertEqual(result['incorrect_success'],1);self.assertFalse(result['verified_task_success'])

    def test_original_identity_required(self):
        for jid in (None,'other_job'):
            d=self.decision();d['job_id']=jid
            self.assertFalse(O.assess(self.expected(),d,self.evidence())['correct'])

    def test_authority_promotion_rejected(self):
        d=self.decision();d['authorizes_actions']=True
        self.assertFalse(O.assess(self.expected(),d,self.evidence())['correct'])

    def test_budget_overrun_or_timeout_rejected(self):
        for change in ({'elapsed_seconds':11},{'timed_out':True},{'observations':4},{'replays':2},{'new_request_ids':1}):
            e=self.evidence();e.update(change)
            self.assertFalse(O.assess(self.expected(),self.decision(),e)['correct'])

    def test_boolean_counter_rejects(self):
        e=self.evidence();e['effects_after']=True
        with self.assertRaises(O.Rejected):O.assess(self.expected(),self.decision(),e)

    def test_goal_success_and_correct_hold_denominators_differ(self):
        hold=dict(action='hold',reason='AUTHORITY_EXPIRED',native_status=None,recovery_eligible=False,task_success_eligible=False)
        d=dict(action='hold',reason='AUTHORITY_EXPIRED',native_status=None,job_id=None,authorizes_actions=False)
        result=O.assess(hold,d,self.evidence())
        self.assertTrue(result['correct']);self.assertFalse(result['verified_task_success']);self.assertFalse(result['recovery_eligible'])

    def test_partial_or_duplicated_development_rows_never_unlock_heldout(self):
        _,_,s,p=H.validate_corpus()
        with self.assertRaises(H.Invalid):H.validate_records([],s,p,O,'development')
        wrong=[dict(schedule_id='H01_00',arm='candidate')]*200
        with self.assertRaises(H.Invalid):H.validate_records(wrong,s,p,O,'development')

    def test_runtime_facts_are_path_and_hostname_free(self):
        with tempfile.TemporaryDirectory() as root:facts=H.runtime_facts(root)
        self.assertEqual(set(facts),{'python','os','machine','kernel','sqlite','filesystem_magic','temporary_filesystem_magic'})
        self.assertIs(type(facts['filesystem_magic']),int)
        self.assertNotIn(root,str(facts))

    def test_main_validation_output_root_is_not_side_effect(self):
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/'must_not_exist'
            with mock.patch.object(H.sys,'argv',['harness','validate','--output-root',str(target)]):
                self.assertEqual(H.main(),2)
            self.assertFalse(target.exists())


if __name__=='__main__':unittest.main(verbosity=2)
