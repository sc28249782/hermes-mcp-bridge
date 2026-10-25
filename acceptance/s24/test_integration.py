"""Actual offline SDK integration with explicitly fabricated observation inputs."""
import argparse
import asyncio
from contextlib import asynccontextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import integration as integrated
import observer_channel as channel
import parent_contract as parent
import s24_fixture as fixture

CANDIDATE = None


class IntegrationChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.identities = {"candidate": fixture.PIN, "artifact": parent.ARTIFACT_PIN,
                           "cohort": "offline-sdk-child", "production": "unit-prod", "dev": "unit-dev"}
        self.writers = ["unit-controller", "offline-sdk-child"]
        self.stages = []

    def tearDown(self):
        self.tmp.cleanup()

    async def sample(self, stage):
        # Fabricated test data in one parent monotonic domain. No Windows query,
        # guest/kernel claim, route authentication or real runtime continuity.
        self.stages.append(stage)
        return {"stage": stage, "observed_at": integrated.time.monotonic(),
                "identities": self.identities.copy(),
                "resources": {"host_available_mib": 2000, "guest_available_mib": 1000,
                              "rss_mib": 100, "disk_free_mib": 3000,
                              "workspace_growth_mib": 1, "logs_mib": 1},
                "writers": {"expected": self.writers[:], "observed": self.writers[:]}}

    def coordinator(self, observation=None, factory=integrated.sdk_session, **updates):
        options = dict(source_kind="git-worktree" if (CANDIDATE / ".git").exists()
                       else "release-archive", window=60, session_factory=factory)
        options.update(updates)
        return integrated.OfflineIntegration(CANDIDATE, self.root, observation or self.sample,
                                             self.identities, self.writers, **options)

    def receipt(self):
        return json.loads((self.root / "integration-receipt.json").read_text())

    def assert_leaf_failure(self, coordinator, error_type, message):
        # SDK/AnyIO wraps body errors in nested groups during session teardown.
        # Require exactly the expected leaf; never discard extra cleanup failures.
        try:
            asyncio.run(coordinator.run())
        except BaseException as error:
            leaves = []
            def collect(value):
                if isinstance(value, BaseExceptionGroup):
                    for item in value.exceptions:
                        collect(item)
                else:
                    leaves.append(value)
            collect(error)
            self.assertEqual(len(leaves), 1, repr(error))
            self.assertIsInstance(leaves[0], error_type)
            if message:
                self.assertRegex(str(leaves[0]), message)
        else:
            self.fail("coordinator unexpectedly succeeded")

    def test_complete_sdk_identity_matrix_stop_and_actual_durable_comparison(self):
        coordinator = self.coordinator(self.joined_observer(signed=True))
        receipt = asyncio.run(coordinator.run())
        self.assertEqual(receipt["status"], "OFFLINE_INTEGRATION_CHECKED")
        self.assertEqual(receipt["identity"]["decoded_tools_count"], 27)
        self.assertEqual((receipt["matrix_tool_calls"], receipt["checkpoints"]), (124, 44))
        self.assertEqual(receipt["durable"]["audit_total"], 30)
        self.assertTrue(receipt["sdk_context_exited_normally"])
        for key in ("raw_wire_capture", "complete_writer_cessation_proved", "operational_b_ready",
                    "scoped_gate_closed", "outer_supervisor_integrated"):
            self.assertIs(receipt[key], False)
        trace = (self.root / "integration-trace.jsonl").read_bytes()
        records = [json.loads(line) for line in trace.splitlines()]
        stages = [item["value"]["payload"]["stage"] for item in records
                  if item["kind"] == "parent-request-data" and item["value"]["kind"] == "checkpoint"]
        self.assertEqual(stages, list(parent.STAGES))
        self.assertEqual(sum(item["kind"] == "offline-observer-inputs" for item in records), 44)
        self.assertEqual(sum(item["kind"] == "observer-message-request" for item in records), 44)
        self.assertEqual(sum(item["kind"] == "observer-message-response" for item in records), 44)
        joined_inputs = [item["value"] for item in records if item["kind"] == "offline-observer-inputs"]
        for sample in joined_inputs:
            self.assertIs(sample["host"]["authenticated"], False)
            self.assertIs(sample["host"]["host_identity_proved"], False)
            self.assertIs(sample["host"]["observer_message_proof"]["message_mac_verified"], True)
        self.assertEqual(hashlib.sha256(trace).hexdigest(), receipt["trace_sha256"])
        self.assertEqual(len(trace), receipt["trace_bytes"])
        self.assertEqual(self.receipt(), receipt)
        for name in ("launch-claim.json", "integration-trace.jsonl", "integration-receipt.json"):
            self.assertEqual((self.root / name).stat().st_mode & 0o777, 0o600)
        self.assertEqual(receipt["phases"], ["PREPARED", "RESERVED", "IDENTITY", "MATRIX",
                                            "STOPPING", "VERIFYING_OFFLINE_STATE", "OFFLINE_CHECKED"])
        with self.assertRaises(parent.Hold):
            asyncio.run(coordinator.run())

    def test_complete_matrix_through_independent_supervisor_stops_before_verifier(self):
        factory = integrated.SupervisedSdkFactory(self.root, term_grace=1, allow_kill=True)
        coordinator = self.coordinator(self.joined_observer(signed=True), factory)
        result = asyncio.run(coordinator.run())
        self.assertEqual((result["matrix_tool_calls"], result["checkpoints"]), (124, 44))
        self.assertEqual(result["durable"]["audit_total"], 30)
        self.assertTrue(result["direct_fixture_supervisor_used"])
        self.assertTrue(result["direct_fixture_supervisor"]["leader"]["leader_reaped"])
        self.assertEqual(result["direct_fixture_supervisor"]["reason"], "controller_stop")
        rpc = result["direct_fixture_supervisor"]["rpc_capture"]
        self.assertTrue(rpc["complete_pairs"])
        self.assertEqual(rpc["pending"], 0)
        self.assertEqual(rpc["requests"], rpc["responses"])
        self.assertGreaterEqual(rpc["requests"], 126)  # Matrix124 + identity/discovery/initialize.
        raw = (self.root / "supervisor-rpc.jsonl").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), rpc["trace_sha256"])
        self.assertEqual(len(raw), rpc["trace_bytes"])
        self.assertFalse(rpc["end_to_end_work_capture"])
        self.assertIs(result["outer_supervisor_integrated"], False)
        self.assertIs(result["complete_writer_cessation_proved"], False)
        self.assertIs(result["operational_b_ready"], False)

    def joined_observer(self, mutate_host=None, mutate_continuity=None, *, signed=False, corrupt_mac=False):
        class UnitGuest:
            def sample(guest_self):
                return {"guest_available_bytes": 1000 * integrated.MIB,
                        "account_rss_sampled_bytes": 100 * integrated.MIB,
                        "disk_available_bytes": 3000 * integrated.MIB,
                        "workspace_growth_bytes": -3, "logs_logical_bytes": integrated.MIB,
                        "full_checkpoint_pass": False, "host_observed": False,
                        "complete_writer_coverage": False, "guest_limit_failures": []}

        async def host(stage, binding, challenge):
            data = {"binding_sha256": binding, "challenge": challenge,
                    "evidence_class": "local-read-only-windows-host-memory",
                    "host_available_bytes": 2000 * integrated.MIB, "elapsed_seconds": 0.01,
                    "full_checkpoint_pass": False, "authenticated": False, "host_identity_proved": False}
            if mutate_host:
                mutate_host(data)
            return data

        if signed:
            plain_host = host
            async def provider(stage, nonce):
                return await plain_host(stage, "a" * 64, nonce)
            key = bytes(range(32))  # Public unit key, never a configured host credential.
            binding = dict(attempt="S24-unit-integration", binding="a" * 64,
                           producer="UnitHost", role="host-memory", record=lambda direction, raw: None)
            responder = channel.ObserverResponder(provider, key, **binding)
            async def exchange(raw):
                reply = await responder.respond(raw)
                if corrupt_mac:
                    envelope = parent.decode(reply)
                    envelope["mac_sha256"] = "0" * 64
                    return parent.encode(envelope)
                return reply
            host = channel.SignedHostProvider(channel.ObserverClient(exchange, key, **binding))

        async def continuity():
            data = {"production": self.identities["production"], "dev": self.identities["dev"], "healthy": True}
            if mutate_continuity:
                mutate_continuity(data)
            return data

        async def inventory():
            return self.writers[:]

        joined = integrated.OfflineObservationJoin(UnitGuest(), host, continuity, inventory,
                                                   self.identities, self.writers, "a" * 64)
        return joined

    def test_signed_host_tampering_holds_before_first_matrix_tool_and_never_falls_back(self):
        joined = self.joined_observer(signed=True, corrupt_mac=True)
        coordinator = self.coordinator(joined)
        self.assert_leaf_failure(coordinator, parent.Hold, "observer MAC mismatch")
        self.assertEqual(coordinator.tool_calls, 0)
        self.assertTrue(coordinator.held)
        self.assertTrue(joined.held)
        self.assertTrue(joined.host.client.held)
        self.assertEqual(self.receipt()["status"], "HOLD")
        trace = (self.root / "integration-trace.jsonl").read_text()
        self.assertIn("observer-message-response", trace)
        self.assertNotIn('"kind":"tool"', trace)

    def test_joined_host_mismatch_latches_before_next_stimulus(self):
        joined = self.joined_observer(mutate_host=lambda data: data.update(challenge="0" * 64))
        with self.assertRaisesRegex(parent.Hold, "host correlation mismatch"):
            asyncio.run(joined("before-matrix"))
        self.assertTrue(joined.held)
        with self.assertRaisesRegex(parent.Hold, "observation join held"):
            asyncio.run(joined("before-matrix"))

    def test_joined_continuity_change_and_bool_counter_are_not_accepted(self):
        for joined in (
            self.joined_observer(mutate_host=lambda data: data.update(host_available_bytes=True)),
            self.joined_observer(mutate_continuity=lambda data: data.update(healthy=1)),
            self.joined_observer(mutate_continuity=lambda data: data.update(production="unit-changed")),
        ):
            with self.assertRaises(parent.Hold):
                asyncio.run(joined("before-matrix"))
            self.assertTrue(joined.held)

    def test_join_preserves_negative_growth_as_input_and_normalizes_upper_bound(self):
        joined = self.joined_observer()
        output = asyncio.run(joined("before-matrix"))
        self.assertEqual(output["resources"]["workspace_growth_mib"], 0)
        self.assertEqual(joined.last_inputs["guest"]["workspace_growth_bytes"], -3)

    def test_integrated_source_drift_blocks_stopped_verification(self):
        coordinator = self.coordinator()
        with patch.object(integrated, "source_identity", side_effect=[{"unit-source": "before"},
                                                                    {"unit-source": "after"}]), \
                patch.object(fixture, "inspect_stopped_state", side_effect=AssertionError("source drift blocks read")):
            with self.assertRaisesRegex(parent.Hold, "integrated source drift"):
                asyncio.run(coordinator.run())
        self.assertEqual(self.receipt()["status"], "HOLD")
        self.assertTrue(self.receipt()["sdk_context_exited_normally"])

    def test_bad_observation_latches_and_stops_before_next_case(self):
        async def sample(stage):
            data = await self.sample(stage)
            if stage == "S24_HERMES_OP_PRE:after":
                data["resources"]["host_available_mib"] = 1535
            return data
        coordinator = self.coordinator(sample)
        with patch.object(fixture, "inspect_stopped_state", side_effect=AssertionError("must not inspect failed matrix")):
            self.assert_leaf_failure(coordinator, parent.Hold, "resource threshold")
        self.assertTrue(coordinator.held)
        self.assertEqual(self.receipt()["status"], "HOLD")
        self.assertEqual(self.stages[-1], "S24_HERMES_OP_PRE:after")
        self.assertNotIn("S24_HERMES_OP_COMMIT:before", self.stages)
        with self.assertRaises(parent.Hold):
            asyncio.run(coordinator.run())

    def test_missing_observation_does_not_become_hard_coded_success(self):
        async def missing(stage):
            return True
        coordinator = self.coordinator(missing)
        self.assert_leaf_failure(coordinator, parent.Hold, "observation shape")
        self.assertEqual(coordinator.tool_calls, 0)
        self.assertEqual(self.receipt()["status"], "HOLD")

    def test_identity_failure_closes_sdk_session_without_matrix_or_verifier(self):
        closed = []

        @asynccontextmanager
        async def factory(argv):
            async with integrated.sdk_session(argv) as session:
                original = session.call_tool

                async def altered(name, args):
                    result = await original(name, args)
                    result.structuredContent["version"] = "unit-mismatch"
                    return result
                session.call_tool = altered
                try:
                    yield session
                finally:
                    closed.append(True)

        coordinator = self.coordinator(factory=factory)
        with patch.object(fixture, "inspect_stopped_state", side_effect=AssertionError("must not inspect")):
            self.assert_leaf_failure(coordinator, parent.Hold, "version identity mismatch")
        self.assertEqual(closed, [True])
        self.assertEqual(coordinator.tool_calls, 0)
        self.assertEqual(self.receipt()["status"], "HOLD")

    def test_cancelled_checkpoint_closes_session_and_preserves_partial_evidence(self):
        closed = []

        @asynccontextmanager
        async def factory(argv):
            async with integrated.sdk_session(argv) as session:
                try:
                    yield session
                finally:
                    closed.append(True)

        async def cancelled(stage):
            raise asyncio.CancelledError()

        coordinator = self.coordinator(cancelled, factory)
        with self.assertRaises(asyncio.CancelledError):
            asyncio.run(coordinator.run())
        self.assertEqual(closed, [True])
        self.assertTrue(coordinator.held)
        self.assertTrue((self.root / "launch-claim.json").exists())
        self.assertEqual(self.receipt()["status"], "HOLD")

    def test_stop_failure_blocks_read_only_verifier(self):
        @asynccontextmanager
        async def factory(argv):
            async with integrated.sdk_session(argv) as session:
                yield session
            raise parent.Hold("unit stop result uncertain")

        coordinator = self.coordinator(factory=factory)
        with patch.object(fixture, "inspect_stopped_state", side_effect=AssertionError("no uncertain-stop read")):
            with self.assertRaisesRegex(parent.Hold, "unit stop result uncertain"):
                asyncio.run(coordinator.run())
        self.assertFalse(self.receipt()["sdk_context_exited_normally"])
        self.assertNotIn("VERIFYING_OFFLINE_STATE", coordinator.phases)

    def test_real_post_stop_row_tampering_fails_and_never_restarts_fixture(self):
        calls = []

        @asynccontextmanager
        async def factory(argv):
            calls.append(argv)
            async with integrated.sdk_session(argv) as session:
                yield session
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect(self.root / "state" / "contexts.sqlite3")) as db, db:
                db.execute("UPDATE contexts SET label='unit-drift' WHERE rowid=1")

        coordinator = self.coordinator(factory=factory)
        with self.assertRaisesRegex(RuntimeError, "durable row drift"):
            asyncio.run(coordinator.run())
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.receipt()["status"], "HOLD")
        self.assertTrue(self.receipt()["sdk_context_exited_normally"])

    def test_bad_source_and_existing_claim_rejected_before_new_child(self):
        invoked = []
        def forbidden(argv):
            invoked.append(argv)
            raise AssertionError("must not launch")
        with self.assertRaises(FileNotFoundError):
            integrated.OfflineIntegration(self.root, self.root, self.sample, self.identities,
                                          self.writers, source_kind="release-archive")
        (self.root / "launch-claim.json").write_bytes(b"unit-retained\n")
        (self.root / "launch-claim.json").chmod(0o600)
        coordinator = self.coordinator(factory=forbidden)
        with self.assertRaises(parent.Hold):
            asyncio.run(coordinator.run())
        self.assertTrue(coordinator.held)
        self.assertEqual(invoked, [])
        self.assertFalse((self.root / "integration-trace.jsonl").exists())

    def test_journal_exclusive_bounds_and_sync_failures(self):
        journal = integrated.PrivateJournal(self.root)
        try:
            journal.record("unit", {"one": 1})
            with patch.object(integrated, "TRACE_LIMIT", journal.count), self.assertRaises(parent.Hold):
                journal.record("unit", {"two": 2})
            journal.receipt({"status": "unit"})
            with self.assertRaises(parent.Hold):
                journal.receipt({"status": "must-not-overwrite"})
        finally:
            journal.close()
        self.assertEqual(self.receipt(), {"status": "unit"})
        with self.assertRaises(FileExistsError):
            integrated.PrivateJournal(self.root)

    def test_evidence_failure_ends_session_without_verifying_or_retrying(self):
        coordinator = self.coordinator()
        original = integrated.PrivateJournal.record

        def record(journal, kind, value):
            if kind == "parent-request-data":
                # Actual write path, then fsync failure before any dispatch.
                with patch.object(integrated.os, "fsync", side_effect=OSError("unit trace storage unavailable")):
                    return original(journal, kind, value)
            return original(journal, kind, value)

        with patch.object(integrated.PrivateJournal, "record", record), \
                patch.object(fixture, "inspect_stopped_state", side_effect=AssertionError("must not inspect")):
            self.assert_leaf_failure(coordinator, OSError, "unit trace storage unavailable")
        self.assertEqual(coordinator.tool_calls, 0)
        self.assertTrue(coordinator.held)
        self.assertEqual(self.receipt()["status"], "HOLD")

    def test_finite_window_cancels_stalled_session_entry_without_retry(self):
        entered, ended = [], []

        @asynccontextmanager
        async def stalled(argv):
            entered.append(True)
            try:
                await asyncio.sleep(10)
                yield None
            finally:
                ended.append(True)

        coordinator = self.coordinator(factory=stalled, window=0.02)
        with patch.object(fixture, "inspect_stopped_state", side_effect=AssertionError("no timed-out read")):
            self.assert_leaf_failure(coordinator, TimeoutError, "")
        self.assertEqual((entered, ended), ([True], [True]))
        self.assertTrue(coordinator.held)
        self.assertEqual(self.receipt()["status"], "HOLD")
        self.assertFalse(self.receipt()["sdk_context_exited_normally"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    options, rest = parser.parse_known_args()
    CANDIDATE = fixture.verify_candidate(options.candidate)
    unittest.main(argv=[sys.argv[0], *rest])
