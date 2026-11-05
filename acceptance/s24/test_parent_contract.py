"""Offline contract controls. Injected observations are fabricated TEST DATA."""
import argparse
import asyncio
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import parent_contract as parent
import s24_fixture as fixture

CANDIDATE = None


class ContractChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.ticks = 100.0
        self.identities = {"candidate": fixture.PIN, "artifact": parent.ARTIFACT_PIN,
                           "cohort": "test-cohort-1", "production": "test-prod-1",
                           "dev": "test-dev-1"}
        self.writers = ["test-controller:1", "test-fixture:2"]
        self.calls = []
        self.bridge = None

    def tearDown(self):
        if self.bridge is not None:
            self.bridge.client.close()
        self.tmp.cleanup()

    def clock(self):
        self.ticks += 0.0001
        return self.ticks

    def sample(self, stage):
        return {"stage": stage, "observed_at": self.clock(),
                "identities": deepcopy(self.identities),
                "resources": {"host_available_mib": 2000, "guest_available_mib": 1000,
                              "rss_mib": 100, "disk_free_mib": 3000,
                              "workspace_growth_mib": 10, "logs_mib": 1},
                "writers": {"expected": self.writers[:], "observed": self.writers[:]}}

    def contract(self, mutate=None, actual=False):
        if actual:
            mcp, self.bridge, _ = fixture.build(CANDIDATE, self.root / "state")

        async def exchange(raw):
            request = parent.decode(raw)
            self.calls.append(deepcopy(request))
            kind, payload = request["kind"], request["payload"]
            if kind == "checkpoint":
                output = self.sample(payload["stage"])
            elif actual:
                try:
                    value = mcp._tool_manager.get_tool(payload["name"]).fn(**payload["arguments"])
                    output = {"isError": False, "structuredContent": deepcopy(value), "content": []}
                except Exception:
                    output = {"isError": True, "structuredContent": None, "content": []}
            else:
                output = {"isError": False, "structuredContent": {"nested": [1, {"ack": True}]},
                          "content": [{"type": "text", "text": "unchanged"}],
                          "_meta": {"keep": ["all", "fields"]}, "extra": {"deep": [None, 2]}}
            response = {**request, "payload": output}
            if mutate:
                changed = mutate(request, response)
                if changed is not None:
                    return changed
            return parent.encode(response)

        return parent.OfflineParentContract(exchange, self.identities, self.writers, clock=self.clock)

    async def open_contract(self, contract):
        await contract.checkpoint("before-matrix")

    def assert_latched(self, contract):
        before = len(self.calls)
        with self.assertRaises(parent.Hold):
            asyncio.run(contract.call("bridge_status", {}))
        self.assertEqual(len(self.calls), before)
        self.assertTrue(contract.held)

    def test_complete_immutable_matrix_and_stopped_state(self):
        contract = self.contract(actual=True)
        with patch("subprocess.Popen", side_effect=AssertionError("native spawn forbidden")), \
                patch("httpx.HTTPTransport.handle_request", side_effect=AssertionError("network forbidden")):
            result = asyncio.run(contract.run())
        self.assertEqual(result["evidence_class"], "offline-ipc-contract")
        self.assertEqual(result["matrix"]["evidence_class"], "offline-ipc-contract")
        self.assertEqual(result["checkpoints"], 44)
        stages = [c["payload"]["stage"] for c in self.calls if c["kind"] == "checkpoint"]
        self.assertEqual(stages, list(parent.STAGES))
        self.assertEqual(result["matrix"]["transport_counters"],
                         {"hermes_posts": 10, "codex_submits": 10})
        self.bridge.client.close()
        self.bridge = None
        counts = fixture.inspect_stopped_state(self.root / "state", result["matrix"])
        self.assertEqual(counts["audit_total"], 30)
        before = len(self.calls)
        with self.assertRaises(parent.Hold):
            asyncio.run(contract.run())
        self.assertEqual(len(self.calls), before)

    def test_deep_result_fields_preserved(self):
        contract = self.contract()
        asyncio.run(self.open_contract(contract))
        result = asyncio.run(contract.call("bridge_status", {}))
        self.assertEqual(result.__dict__, {
            "isError": False, "structuredContent": {"nested": [1, {"ack": True}]},
            "content": [{"type": "text", "text": "unchanged"}],
            "_meta": {"keep": ["all", "fields"]}, "extra": {"deep": [None, 2]}})

    def test_ack_mutation_still_fails_original_matrix(self):
        def mutate(request, response):
            if request["kind"] == "tool" and request["payload"]["name"] == "hermes_submit_task":
                response["payload"]["structuredContent"]["new_field"] = "bad ACK"
        contract = self.contract(mutate, actual=True)
        with self.assertRaisesRegex(RuntimeError, "ACK changed"):
            asyncio.run(contract.run())
        self.assert_latched(contract)

    def test_late_observation_failure_blocks_next_matrix_case(self):
        def mutate(request, response):
            if request["kind"] == "checkpoint" and request["payload"]["stage"] == "S24_HERMES_OP_PRE:after":
                response["payload"]["resources"]["host_available_mib"] = 1535
        contract = self.contract(mutate, actual=True)
        with self.assertRaisesRegex(parent.Hold, "resource threshold"):
            asyncio.run(contract.run())
        self.assertEqual(self.bridge.local_status()["posts"], 2)
        self.assertEqual(self.calls[-1]["payload"]["stage"], "S24_HERMES_OP_PRE:after")
        self.assert_latched(contract)

    def test_envelope_negative_controls_latch_without_retry(self):
        with self.assertRaises(parent.Hold):
            parent.decode(b'{"value":1e400}\n')
        controls = [lambda q, r: r.update(seq=0), lambda q, r: r.update(seq=True),
                    lambda q, r: r.update(route="production"), lambda q, r: r.update(kind="other"),
                    lambda q, r: r.update(extra=True), lambda q, r: b"{}\n{}\n",
                    lambda q, r: b'{"seq":1,"seq":1}\n', lambda q, r: b'{"n":NaN}\n',
                    lambda q, r: b"\xff\n", lambda q, r: b"x" * (parent.MAX_FRAME_BYTES + 1)]
        for control in controls:
            with self.subTest(control=control):
                self.calls.clear()
                contract = self.contract(control)
                with self.assertRaises(parent.Hold):
                    asyncio.run(self.open_contract(contract))
                self.assertEqual(len(self.calls), 1)
                self.assert_latched(contract)

    def test_fabricated_true_missing_stale_reused_future_observations_rejected(self):
        controls = [lambda v: True, lambda v: {},
                    lambda v: {**v, "observed_at": 0},
                    lambda v: {**v, "observed_at": self.ticks + 10},
                    lambda v: {**v, "identities": {**v["identities"], "cohort": "changed"}},
                    lambda v: {**v, "writers": {"expected": ["changed"], "observed": ["changed"]}},
                    lambda v: {**v, "writers": {"expected": self.writers, "observed": []}}]
        for control in controls:
            with self.subTest(control=control):
                def mutate(q, r):
                    r["payload"] = control(r["payload"])
                contract = self.contract(mutate)
                with self.assertRaises(parent.Hold):
                    asyncio.run(self.open_contract(contract))
                self.assert_latched(contract)
        contract = self.contract()
        asyncio.run(self.open_contract(contract))
        old = contract.last_observation
        value = self.sample(parent.STAGES[1])
        value["observed_at"] = old
        with self.assertRaises(parent.Hold):
            contract.observation(value, parent.STAGES[1])

    def test_all_resource_thresholds_and_bad_numeric_types(self):
        violations = {"host_available_mib": 1535, "guest_available_mib": 767, "rss_mib": 769,
                      "disk_free_mib": 2047, "workspace_growth_mib": 2049, "logs_mib": 129}
        for key, invalid in violations.items():
            for value in (invalid, True, -1, "1000", None):
                with self.subTest(key=key, value=value):
                    def mutate(q, r):
                        r["payload"]["resources"][key] = value
                    contract = self.contract(mutate)
                    with self.assertRaises(parent.Hold):
                        asyncio.run(self.open_contract(contract))
                    self.assert_latched(contract)

    def test_stale_or_backward_clock_blocks_before_dispatch(self):
        for delta in (3, -2, 1201):
            with self.subTest(delta=delta):
                contract = self.contract()
                asyncio.run(self.open_contract(contract))
                before = len(self.calls)
                self.ticks += delta
                with self.assertRaises(parent.Hold):
                    asyncio.run(contract.call("bridge_status", {}))
                self.assertEqual(len(self.calls), before)
                self.assert_latched(contract)

    def test_error_after_possible_acceptance_never_retries(self):
        contract = self.contract()
        asyncio.run(self.open_contract(contract))
        attempts = []
        async def uncertain(raw):
            attempts.append(raw)
            raise ConnectionError("test lost reply")
        contract.exchange = uncertain
        with self.assertRaises(ConnectionError):
            asyncio.run(contract.call("bridge_status", {}))
        self.assertEqual(len(attempts), 1)
        self.assert_latched(contract)

    def test_timeout_and_cancellation_latch(self):
        for cancel in (False, True):
            contract = self.contract()
            asyncio.run(self.open_contract(contract))
            async def absent(raw):
                if cancel:
                    raise asyncio.CancelledError()
                await asyncio.Event().wait()
            contract.exchange = absent
            with patch.object(parent, "REPLY_TIMEOUT_SECONDS", 0.01):
                with self.assertRaises(asyncio.CancelledError if cancel else TimeoutError):
                    asyncio.run(contract.call("bridge_status", {}))
            self.assert_latched(contract)

    def test_concurrent_request_blocks_inflight_result(self):
        contract = self.contract()
        async def exercise():
            await self.open_contract(contract)
            entered, release = asyncio.Event(), asyncio.Event()
            original = contract.exchange
            async def delayed(raw):
                entered.set()
                await release.wait()
                return await original(raw)
            contract.exchange = delayed
            first = asyncio.create_task(contract.call("bridge_status", {}))
            await entered.wait()
            with self.assertRaises(parent.Hold):
                await contract.call("bridge_status", {})
            release.set()
            with self.assertRaises(parent.Hold):
                await first
        asyncio.run(exercise())
        self.assert_latched(contract)

    def test_unknown_tools_args_ids_and_checkpoint_order_block_before_exchange(self):
        cases = [("hermes_submit_task", {"prompt": "not fixture", "request_id": "x"}),
                 ("bridge_context_status", {"context_id": "unowned"}),
                 ("bridge_context_recent", {"limit": True}),
                 ("bridge_status", {"extra": True}), ("bridge_version", {}),
                 ("tools/list", {}), ("codex_submit_task", {"prompt": "S24_SYNTHETIC",
                  "workspace": "host", "mode": "read-only"})]
        for name, args in cases:
            with self.subTest(name=name, args=args):
                contract = self.contract()
                asyncio.run(self.open_contract(contract))
                before = len(self.calls)
                with self.assertRaises(parent.Hold):
                    asyncio.run(contract.call(name, args))
                self.assertEqual(len(self.calls), before)
                self.assert_latched(contract)
        contract = self.contract()
        with self.assertRaises(parent.Hold):
            asyncio.run(contract.checkpoint(parent.STAGES[1]))
        self.assert_latched(contract)

    def test_trace_budget_fails_before_next_exchange(self):
        contract = self.contract()
        asyncio.run(self.open_contract(contract))
        before = len(self.calls)
        contract.trace_bytes = parent.MAX_TRACE_BYTES
        with self.assertRaises(parent.Hold):
            asyncio.run(contract.call("bridge_status", {}))
        self.assertEqual(len(self.calls), before)
        self.assert_latched(contract)

    def test_valid_fixture_arguments_cannot_be_used_in_another_case(self):
        for case in ("create", "submit"):
            with self.subTest(case=case):
                contract = self.contract()
                asyncio.run(self.open_contract(contract))
                asyncio.run(contract.checkpoint(parent.STAGES[1]))
                contract.contexts["ctx_test"] = "S24_HERMES_OP_PRE"
                before = len(self.calls)
                with self.assertRaises(parent.Hold):
                    if case == "create":
                        asyncio.run(contract.call("bridge_context_create", {"label": "S24_CODEX_NORMAL"}))
                    else:
                        asyncio.run(contract.call("hermes_submit_task", {"prompt": "S24_SYNTHETIC",
                            "context_id": "ctx_test", "request_id": "s24-hermes-OP_PRE"}))
                self.assertEqual(len(self.calls), before)
                self.assert_latched(contract)

    def test_invalid_result_shape_latches(self):
        def mutate(q, r):
            if q["kind"] == "tool":
                r["payload"]["isError"] = "false"
        contract = self.contract(mutate)
        asyncio.run(self.open_contract(contract))
        with self.assertRaises(parent.Hold):
            asyncio.run(contract.call("bridge_status", {}))
        self.assert_latched(contract)

    def test_prebound_inputs_and_finite_window_required(self):
        for window in (True, 0, -1, 1201, float("inf"), float("nan")):
            with self.subTest(window=window), self.assertRaises(parent.Hold):
                parent.OfflineParentContract(lambda _: None, self.identities, self.writers,
                                             clock=self.clock, window_seconds=window)
        for key in ("candidate", "artifact"):
            with self.subTest(key=key), self.assertRaises(parent.Hold):
                parent.OfflineParentContract(lambda _: None, {**self.identities, key: "wrong"},
                                             self.writers, clock=self.clock)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    arguments, remaining = parser.parse_known_args()
    CANDIDATE = fixture.verify_candidate(arguments.candidate)
    unittest.main(argv=[sys.argv[0], *remaining])
