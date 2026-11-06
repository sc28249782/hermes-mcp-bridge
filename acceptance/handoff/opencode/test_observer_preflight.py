"""Owned offline preflight controls; no Dev/backend or observer process launch."""
import ast
from dataclasses import asdict, replace
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from acceptance.handoff.opencode import observer_preflight as P
SOURCE = Path(__file__).resolve().parent


class PreflightControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='oa-preflight-owned-')
        self.root = Path(self.temp.name)
        self.anchor = self.root/'anchor'; self.anchor.mkdir(mode=0o700)
        self.data = self.root/'data'; self.data.mkdir(mode=0o700)
        self.rootfd = os.open(self.anchor, os.O_RDONLY|os.O_DIRECTORY)
        self.read, self.write = os.pipe2(os.O_CLOEXEC)
        self.issuer = P.FixtureIssuer(self.rootfd, 1)
        self.binding = P.Binding('attempt_fixture', 'nonce_fixture', 1, 'a'*64,
                                 'b'*64, P.SCOPES, 'fixture-owned-cleanup',
                                 time.monotonic(), time.monotonic()+40)
        self.reservations = []

    def tearDown(self):
        for value in self.reservations:
            value.close()
        self.issuer.close()
        os.close(self.rootfd); os.close(self.read)
        if self.write is not None:
            os.close(self.write)
        self.temp.cleanup()

    def register(self, **changes):
        b = replace(self.binding, **changes)
        self.issuer.register(b, self.read)
        return b

    def reserve(self, ref=None):
        value = self.issuer.reserve(ref or self.binding.attempt_ref)
        self.reservations.append(value)
        return value

    def frame(self, b=None, **changes):
        b = b or self.binding
        value = dict(kind='offline-observer-witness-v1', nonce=b.nonce,
                     generation=b.generation, role='H', source_sha256=b.source_sha256)
        value.update(changes)
        return json.dumps(value, separators=(',', ':')).encode()+b'\n'

    def test_valid_reservation_is_durable_but_never_capture_authority(self):
        self.register(); r = self.reserve()
        files = list(self.anchor.iterdir())
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].stat().st_mode&0o777, 0o600)
        self.assertGreater(files[0].stat().st_size, 0)
        os.write(self.write, self.frame())
        result = r.witness()
        self.assertEqual(result.state, 'FIXTURE_WITNESS_PARSED')
        for field in ('capture_allowed', 'authorizes_actions', 'dev_observed'):
            self.assertFalse(getattr(result, field))
        with self.assertRaises(P.Hold) as error:
            r.capture()
        self.assertEqual(error.exception.reason, 'PIDFD_ACK_UNBOUND')

    def test_caller_dict_and_unknown_ref_cannot_issue_admission(self):
        with self.assertRaises(P.Hold):
            self.issuer.register({'verifier_passed': True, 'approved': True}, self.read)
        with mock.patch.object(P.os, 'fork', side_effect=AssertionError('no fork')):
            with self.assertRaises(P.Hold):
                self.issuer.reserve('unknown_fixture')
        self.assertEqual(list(self.anchor.iterdir()), [])

    def test_dev_environment_is_rejected_before_claim(self):
        b = self.register(environment='dev')
        with self.assertRaises(P.Hold) as error:
            self.issuer.reserve(b.attempt_ref)
        self.assertEqual(error.exception.reason, 'PRODUCTION_BINDINGS_UNBOUND')
        self.assertEqual(list(self.anchor.iterdir()), [])

    def test_missing_containment_cannot_be_filled_by_boolean(self):
        b = self.register(containment=True)
        with self.assertRaises(P.Hold) as error:
            self.issuer.reserve(b.attempt_ref)
        self.assertEqual(error.exception.reason, 'CONTAINMENT_UNBOUND')
        self.assertEqual(list(self.anchor.iterdir()), [])

    def test_missing_scopes_cleanup_or_actor_budget_reject(self):
        for n, change in enumerate((dict(scopes=frozenset()), dict(cleanup_after_revoke=False),
                                    dict(actor_count=True), dict(actor_count=5), dict(generation=True))):
            b = self.register(attempt_ref='attempt_'+str(n), **change)
            with self.subTest(change=change), self.assertRaises(P.Hold):
                self.issuer.reserve(b.attempt_ref)
        self.assertEqual(list(self.anchor.iterdir()), [])

    def test_expired_and_revoked_before_claim_leave_no_output(self):
        b = self.register(expires=self.binding.t0+0.001)
        with mock.patch.object(P.time, 'monotonic', return_value=b.t0+1):
            with self.assertRaises(P.Hold):
                self.issuer.reserve(b.attempt_ref)
        self.issuer.revoke(b.attempt_ref)
        with self.assertRaises(P.Hold):
            self.issuer.reserve(b.attempt_ref)
        self.assertEqual(list(self.anchor.iterdir()), [])

    def test_generation_drift_prevents_claim(self):
        self.register(); self.issuer.generation = 2
        with self.assertRaises(P.Hold):
            self.issuer.reserve(self.binding.attempt_ref)
        self.assertEqual(list(self.anchor.iterdir()), [])

    def test_concurrent_processes_only_one_reservation_wins(self):
        self.register()
        gate_r, gate_w = os.pipe2(os.O_CLOEXEC)
        children = []
        for _ in range(2):
            pid = os.fork()
            if pid == 0:
                os.close(gate_w)
                signal.signal(signal.SIGALRM, lambda *_: os._exit(99)); signal.alarm(3)
                os.read(gate_r, 1)
                try:
                    child_issuer = P.FixtureIssuer(self.rootfd, 1)
                    child_issuer.register(replace(self.binding), self.read)
                    r = child_issuer.reserve(self.binding.attempt_ref)
                    r.close(); child_issuer.close(); os._exit(0)
                except P.Hold as error:
                    os._exit(10 if error.reason == 'ATTEMPT_CONSUMED' else 11)
            children.append(pid)
        os.close(gate_r); os.write(gate_w, b'GG'); os.close(gate_w)
        results = [os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]) for pid in children]
        self.assertEqual(sorted(results), [0, 10])
        self.assertEqual(len(list(self.anchor.iterdir())), 1)

    def test_crash_after_exclusive_create_consumes_unknown_attempt(self):
        self.register(); pid = os.fork()
        if pid == 0:
            child_issuer = P.FixtureIssuer(self.rootfd, 1)
            child_issuer.register(replace(self.binding), self.read)
            with mock.patch.object(P.os, 'write', side_effect=lambda *_: os._exit(91)):
                child_issuer.reserve(self.binding.attempt_ref)
            os._exit(92)
        self.assertEqual(os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]), 91)
        files = list(self.anchor.iterdir())
        self.assertEqual(len(files), 1); self.assertEqual(files[0].stat().st_size, 0)
        with self.assertRaises(P.Hold) as error:
            self.issuer.reserve(self.binding.attempt_ref)
        self.assertEqual(error.exception.reason, 'ATTEMPT_CONSUMED')

    def test_fsync_failure_keeps_partial_evidence_and_denies_reuse(self):
        self.register()
        with mock.patch.object(P.os, 'fsync', side_effect=OSError('PRIVATE_SENTINEL')):
            with self.assertRaises(P.Hold) as error:
                self.issuer.reserve(self.binding.attempt_ref)
        self.assertEqual(error.exception.reason, 'CLAIM_UNCONFIRMED')
        self.assertEqual(str(error.exception), '')
        with self.assertRaises(P.Hold) as repeated:
            self.issuer.reserve(self.binding.attempt_ref)
        self.assertEqual(repeated.exception.reason, 'ATTEMPT_CONSUMED')

    def test_data_rollback_and_new_issuer_cannot_redeem_same_anchor_claim(self):
        self.register(); self.reserve()
        snapshot = self.data/'checkpoint.json'; snapshot.write_text('{"generation":1}')
        snapshot.write_text('{"generation":2}'); snapshot.write_text('{"generation":1}')
        other = P.FixtureIssuer(self.rootfd, 1)
        try:
            other.register(replace(self.binding), self.read)
            with self.assertRaises(P.Hold) as error:
                other.reserve(self.binding.attempt_ref)
            self.assertEqual(error.exception.reason, 'ATTEMPT_CONSUMED')
        finally:
            other.close()

    def test_existing_symlink_claim_is_not_repaired(self):
        self.register()
        name = hashlib.sha256(self.binding.attempt_ref.encode()).hexdigest()+'.claim'
        target = self.data/'private'; target.write_bytes(b'PRIVATE_SENTINEL')
        (self.anchor/name).symlink_to(target)
        with self.assertRaises(P.Hold):
            self.issuer.reserve(self.binding.attempt_ref)
        self.assertTrue((self.anchor/name).is_symlink())
        self.assertEqual(target.read_bytes(), b'PRIVATE_SENTINEL')

    def test_root_permission_drift_rejected_without_chmod(self):
        self.register(); self.anchor.chmod(0o750)
        with self.assertRaises(P.Hold):
            self.issuer.reserve(self.binding.attempt_ref)
        self.assertEqual(self.anchor.stat().st_mode&0o777, 0o750)
        self.assertEqual(list(self.anchor.iterdir()), [])
        self.anchor.chmod(0o700)  # Fixture cleanup only; source never repairs mode.

    def test_budget_reserves_three_seconds_without_new_clock_on_witness(self):
        self.register(); r = self.reserve(); saved = r.budget
        self.assertLessEqual(saved.attempt_deadline-saved.ta, 20)
        self.assertEqual(saved.attempt_deadline-saved.capture_deadline, 3)
        self.assertEqual(saved.outer_deadline-saved.t0, 45)
        os.write(self.write, self.frame())
        with mock.patch.object(P.time, 'monotonic', return_value=saved.ta+1):
            r.witness()
        self.assertEqual(r.budget, saved)

    def test_late_start_clock_anomaly_and_insufficient_reserve_reject(self):
        now = time.monotonic()
        for t0 in (now+1, now-45, now-43, float('nan'), True):
            with self.subTest(t0=t0), self.assertRaises(P.Hold):
                P.Budget.start(t0, now)

    def test_revocation_after_reserve_blocks_read_but_retains_limited_cleanup_check(self):
        self.register(); r = self.reserve(); raw = self.frame(); os.write(self.write, raw)
        self.issuer.revoke(self.binding.attempt_ref)
        with self.assertRaises(P.Hold):
            r.witness()
        self.assertEqual(os.read(self.read, 512), raw)
        result = r.cleanup_status()
        self.assertEqual(result.reason, 'OWNERSHIP_UNBOUND')
        self.assertFalse(result.authorizes_actions)
        with mock.patch.object(P.time, 'monotonic', return_value=r.budget.attempt_deadline+0.01):
            with self.assertRaises(P.Hold):
                r.cleanup_status()

    def test_wrong_generation_role_hash_and_extra_field_reject_on_real_pipe(self):
        for n, change in enumerate((dict(generation=True), dict(generation=2), dict(role='S'),
                                    dict(source_sha256='c'*64), dict(nonce='foreign'), dict(approved=True))):
            b = self.register(attempt_ref='attempt_'+str(n)); r = self.reserve(b.attempt_ref)
            os.write(self.write, self.frame(b, **change))
            with self.subTest(change=change), self.assertRaises(P.Hold):
                r.witness()

    def test_partial_and_duplicate_frames_fail_without_retry(self):
        self.register(); r = self.reserve()
        os.write(self.write, b'{"kind":')
        with self.assertRaises(P.Hold):
            r.witness()
        os.write(self.write, self.frame())
        with self.assertRaises(P.Hold):
            r.witness()
        # Separate reservation sees two atomic frames coalesced and rejects.
        os.read(self.read, 512)
        b = self.register(attempt_ref='attempt_second'); r2 = self.reserve(b.attempt_ref)
        os.write(self.write, self.frame(b)*2)
        with self.assertRaises(P.Hold):
            r2.witness()

    def test_closed_or_unavailable_witness_is_not_success(self):
        self.register(); r = self.reserve()
        with self.assertRaises(P.Hold):
            r.witness()
        b = self.register(attempt_ref='attempt_eof'); r2 = self.reserve(b.attempt_ref)
        os.close(self.write); self.write = None
        with self.assertRaises(P.Hold):
            r2.witness()

    def test_parser_overcap_duplicate_keys_float_and_non_ascii_are_rejected(self):
        for raw in (b'X'*513+b'\n', b'{"a":1,"a":2}\n', b'{"a":NaN}\n',
                    b'{"a":1.5}\n', b'{"a":"\xff"}\n', b'{}\n{}\n'):
            with self.subTest(size=len(raw)), self.assertRaises(P.Hold):
                P._frame(raw)

    def test_result_privacy_and_no_runtime_dispatch_source(self):
        self.register(); r = self.reserve(); os.write(self.write, self.frame())
        text = json.dumps(asdict(r.witness()))
        for private in (self.binding.attempt_ref, self.binding.nonce, str(self.root), 'a'*64, 'b'*64):
            self.assertNotIn(private, text)
        tree = ast.parse((SOURCE/'observer_preflight.py').read_text())
        calls = [node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        self.assertFalse(set(calls)&{'fork', 'Popen', 'execve', 'kill', 'pidfd_send_signal',
                                      'submit', 'cancel', 'resume', '_reconcile', 'chmod', 'unlink'})

    def test_source_and_contract_manifest(self):
        m = json.loads((SOURCE/'observer-preflight-hashes.json').read_bytes())
        for entry in m['source']+m['unchanged_dependencies']:
            raw = (ROOT/entry['path']).read_bytes()
            self.assertEqual(len(raw), entry['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
        self.assertFalse(m['dev_observed']); self.assertFalse(m['authorizes_actions'])

    def test_float_cancellation_cannot_extend_exact_budget(self):
        tick=math.nextafter(17.0,-math.inf)
        self.assertGreater((tick+20)-tick,20)  # Reproduce the old CI failure.
        budget=P.Budget.start(tick,tick)
        self.assertEqual(budget.t0,Fraction(tick))
        self.assertEqual(budget.ta,Fraction(tick))
        self.assertEqual(budget.attempt_deadline-budget.ta,20)
        self.assertEqual(budget.attempt_deadline-budget.capture_deadline,3)
        self.assertEqual(budget.outer_deadline-budget.t0,45)
        self.assertLessEqual(budget.attempt_deadline,Fraction(tick)+20)

    def test_inherited_issuer_after_fork_is_not_current_authority(self):
        self.register(); pid = os.fork()
        if pid == 0:
            try:
                self.issuer.reserve(self.binding.attempt_ref)
            except P.Hold as error:
                os._exit(0 if error.reason == 'ISSUER_PROCESS_CHANGED' else 11)
            os._exit(12)
        self.assertEqual(os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]), 0)
        self.assertEqual(list(self.anchor.iterdir()), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
