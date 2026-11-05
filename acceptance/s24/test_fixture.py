"""Artifact-only checks; separate from the unchanged candidate test inventory."""
import argparse
import asyncio
from copy import deepcopy
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s24_fixture as fixture

CANDIDATE = None


class FixtureChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)

    def tearDown(self):
        self.tmp.cleanup()

    def direct(self, mutate=None, break_commit=False):
        mcp, bridge, registry = fixture.build(CANDIDATE, self.root / "state")
        if break_commit:
            from contexts import ContextRegistry
            registry.db = ContextRegistry.db.__get__(registry, type(registry))

        async def call(name, arguments):
            try:
                out = mcp._tool_manager.get_tool(name).fn(**arguments)
            except Exception:
                return SimpleNamespace(isError=True, structuredContent=None)
            out = deepcopy(out)
            if mutate is not None:
                mutate(name, arguments, out, registry)
            return SimpleNamespace(isError=False, structuredContent=out)

        return call, bridge, registry

    def test_complete_matrix_over_real_sdk_stdio(self):
        result = asyncio.run(fixture.offline(CANDIDATE, self.root / "state"))
        self.assertEqual(result["evidence_class"], "offline-sdk-smoke")
        self.assertEqual(result["transport_counters"], {"hermes_posts": 10, "codex_submits": 10})
        self.assertEqual(result["durable"], {k: v for k, v in fixture.EXPECTED.items()
                                          if k not in ("hermes_posts", "codex_submits")})

    def test_direct_matrix_has_no_native_spawn_or_http_transport(self):
        call, bridge, _ = self.direct()
        try:
            with patch("subprocess.Popen", side_effect=AssertionError("native spawn forbidden")), \
                    patch("httpx.HTTPTransport.handle_request",
                          side_effect=AssertionError("real HTTP transport forbidden")):
                result = asyncio.run(fixture.matrix(call))
            self.assertEqual(result["evidence_class"], "driver-observations")
        finally:
            bridge.client.close()

    def test_ack_mutation_is_detected(self):
        def mutate(name, arguments, out, registry):
            if name == "hermes_submit_task":
                out["requested_model_options"] = {"unexpected": "change"}

        call, bridge, _ = self.direct(mutate)
        try:
            with self.assertRaisesRegex(RuntimeError, "ACK changed"):
                asyncio.run(fixture.matrix(call))
        finally:
            bridge.client.close()

    def test_unexpected_writer_is_detected(self):
        def mutate(name, arguments, out, registry):
            if name == "hermes_submit_task":
                with registry.db() as db:
                    db.execute("UPDATE contexts SET label='unexpected writer' WHERE context_id=?",
                               (arguments["context_id"],))

        call, bridge, _ = self.direct(mutate)
        try:
            with self.assertRaisesRegex(RuntimeError, "transaction state"):
                asyncio.run(fixture.matrix(call))
        finally:
            bridge.client.close()

    def test_disabling_real_commit_gate_fails_matrix(self):
        call, bridge, _ = self.direct(break_commit=True)
        try:
            with self.assertRaisesRegex(RuntimeError, "transaction state"):
                asyncio.run(fixture.matrix(call))
        finally:
            bridge.client.close()

    def test_post_run_row_drift_fails_snapshot(self):
        call, bridge, registry = self.direct()
        try:
            result = asyncio.run(fixture.matrix(call))
            with registry.db() as db:
                db.execute("UPDATE contexts SET hermes_run_id='unexpected' WHERE label=?",
                           (fixture.label("hermes", "NORMAL"),))
            with self.assertRaisesRegex(RuntimeError, "durable row drift"):
                fixture.inspect_stopped_state(self.root / "state", result)
        finally:
            bridge.client.close()

    def test_checkpoint_order_surrounds_actual_stimulus(self):
        call, bridge, _ = self.direct()
        seen = {}

        async def checkpoint(stage):
            self.assertNotIn(stage, seen)
            seen[stage] = bridge.local_status()["posts"]
            return True

        try:
            asyncio.run(fixture.matrix(call, "parent-route-observations", checkpoint))
            for number, case in enumerate(fixture.CASES):
                prefix = fixture.label("hermes", case)
                self.assertEqual(seen[prefix + ":before"], number)
                self.assertEqual(seen[prefix + ":after"], number + 1)
            self.assertEqual(seen["replay:before"], 9)
            self.assertEqual(seen["replay:after"], 9)
            self.assertEqual(seen["after-matrix"], 10)
        finally:
            bridge.client.close()

    def test_failed_or_missing_live_checkpoint_blocks_stimulus(self):
        call, bridge, _ = self.direct()

        async def reject(stage):
            return False

        try:
            with self.assertRaisesRegex(RuntimeError, "checkpoints required"):
                asyncio.run(fixture.matrix(call, "parent-route-observations"))
            with self.assertRaisesRegex(RuntimeError, "checkpoint failed"):
                asyncio.run(fixture.matrix(call, "parent-route-observations", reject))
            self.assertEqual(bridge.local_status()["posts"], 0)
        finally:
            bridge.client.close()

    def test_candidate_drift_fails_before_state_creation(self):
        altered = self.root / "candidate"
        shutil.copytree(CANDIDATE, altered, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
        with (altered / "bridge.py").open("ab") as stream:
            stream.write(b"\n# synthetic drift\n")
        with self.assertRaisesRegex(RuntimeError, "content mismatch"):
            fixture.build(altered, self.root / "state")
        self.assertFalse((self.root / "state").exists())

    def test_existing_state_and_public_parent_are_rejected(self):
        state = self.root / "state"
        state.mkdir(mode=0o700)
        sentinel = state / "preserve"
        sentinel.write_text("unchanged")
        with self.assertRaises(FileExistsError):
            fixture.build(CANDIDATE, state)
        self.assertEqual(sentinel.read_text(), "unchanged")
        public = self.root / "public"
        public.mkdir(mode=0o755)
        public.chmod(0o755)
        with self.assertRaisesRegex(RuntimeError, "must be private"):
            fixture.build(CANDIDATE, public / "state")
        self.assertFalse((public / "state").exists())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    arguments, remaining = parser.parse_known_args()
    CANDIDATE = fixture.verify_candidate(arguments.candidate)
    unittest.main(argv=[sys.argv[0], *remaining])
