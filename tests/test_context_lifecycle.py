"""SPEC section 21: deterministic lifecycle/concurrency acceptance for the
context registry and the closed-binding submit outcome (D1-D5).

Thread and process gates sit before the SQL writer transaction starts; a test
never holds a SQLite lock while waiting for a close commit. Bounded waits are
failsafes only, never scheduling by time.sleep. No P2 apply/delete, no schema
change, no new audit event, no real model/backend call.
"""
from pathlib import Path
import multiprocessing
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

import httpx

import bridge
from codex_core import CodexError
from contexts import ContextError, ContextRegistry

try:
    from bridge import _CLOSED_BINDING_NOTE
except ImportError:  # baseline has no constant; the tests below fail on its behavior
    _CLOSED_BINDING_NOTE = ("Context was closed before binding. The task remains owned by this bridge. "
                            "Do not resubmit; retrieve it by its existing identifiers.")

try:
    from contexts import ContextClosedError
except ImportError:  # baseline has no typed closed error; plain ContextError still fails assertRaises(ContextClosedError)
    class ContextClosedError(ContextError):
        pass

CLOSED_MSG = "Context is closed; create a new context_id instead."
UNKNOWN_MSG = "Unknown context_id."
INVALID_MSG = "Invalid context_id."
WORKSPACE = "workspace-fixture"


class Audit:
    def __init__(self): self.events = []
    def record(self, *args): self.events.append(args)


class GatedRegistry(ContextRegistry):
    """Gates fire at method entry, before any SQL writer transaction opens."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._gates = {}

    def gate(self, name, event):
        self._gates[name] = event

    def close(self, context_id):
        event = self._gates.get("close")
        if event:
            event.wait(timeout=30)
        return super().close(context_id)

    def bind_hermes_run(self, context_id, run_id):
        event = self._gates.get("bind")
        if event:
            event.wait(timeout=30)
        return super().bind_hermes_run(context_id, run_id)


class FakeHermes:
    def __init__(self):
        self.posts = 0
        self.lost = False
        self.capabilities = 0

    def __call__(self, request):
        if request.method == "POST" and request.url.path == "/v1/runs":
            self.posts += 1
            if self.lost:
                self.lost = False
                raise httpx.ReadTimeout("accepted but response lost")
            return httpx.Response(200, json={"run_id": f"run_{self.posts}", "status": "started"})
        if request.method == "GET" and request.url.path == "/v1/capabilities":
            self.capabilities += 1
            return httpx.Response(200, json={"features": {"runs_idempotency": {"supported": True, "durable": True}}})
        return httpx.Response(404)


class FakeCodex:
    def __init__(self):
        self.starts = 0
        self.fail = False

    def start_watchdog(self):
        return False

    def local_status(self):
        return {"fixture_only": True}

    def submit(self, prompt, workspace, mode, model, reasoning_effort):
        self.starts += 1
        if self.fail:
            raise CodexError("fake submit failure")
        status = "pending_local_approval" if mode == "workspace-write" else "queued"
        approval = {"expires_at": 123.0, "policy_root": workspace} if mode == "workspace-write" else None
        return {"job_id": "codex_" + "a" * 32, "status": status, "approval": approval,
                "next": ("Approve locally with ./bridge.sh codex-approve codex_" + "a" * 32
                         if mode == "workspace-write" else "Poll codex_task_status")}

    def __getattr__(self, name):
        raise CodexError("Fixture backend operations are disabled.")


class HandsStub:
    def __getattr__(self, name):
        raise ContextError("Fixture backend operations are disabled.")


def _cross_proc_worker(state_dir, cid, role, barrier, ack, queue):
    class SilentAudit:
        def record(self, *args):
            pass
    registry = ContextRegistry(Path(state_dir), SilentAudit())
    if role == "bind":
        barrier.wait(timeout=30)
        ack.wait(timeout=30)
        try:
            registry.bind_hermes_run(cid, "run_x")
            outcome = "bound"
        except ContextClosedError:
            outcome = "closed_rejected"
    else:
        barrier.wait(timeout=30)
        registry.close(cid)
        ack.set()
        outcome = "closed"
    queue.put((role, outcome))


class TestRegistryLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = GatedRegistry(Path(self.tmp.name), Audit())

    def tearDown(self):
        self.tmp.cleanup()

    def _status(self, cid):
        return self.registry.status(cid)

    def test_close_wins_over_bind(self):
        created = self.registry.create("fixture")
        cid = created["context_id"]
        release = threading.Event()
        self.registry.gate("bind", release)
        result = {}

        def bind():
            try:
                self.registry.bind_hermes_run(cid, "run_x")
                result["outcome"] = "bound"
            except ContextError as exc:
                result["outcome"] = str(exc)

        thread = threading.Thread(target=bind)
        thread.start()
        self.registry.close(cid)
        release.set()
        thread.join(timeout=30)
        self.assertEqual(result["outcome"], CLOSED_MSG)
        self.assertIsNotNone(self._status(cid)["closed"])
        self.assertIsNone(self._status(cid)["hermes_run_id"])

    def test_bind_wins_over_close(self):
        created = self.registry.create("fixture")
        cid = created["context_id"]
        release = threading.Event()
        self.registry.gate("close", release)
        result = {}

        def close():
            try:
                self.registry.close(cid)
                result["outcome"] = "closed"
            except ContextError as exc:
                result["outcome"] = str(exc)

        thread = threading.Thread(target=close)
        thread.start()
        self.registry.bind_hermes_run(cid, "run_x")
        release.set()
        thread.join(timeout=30)
        self.assertEqual(result["outcome"], "closed")
        status = self._status(cid)
        self.assertIsNotNone(status["closed"])
        self.assertEqual(status["hermes_run_id"], "run_x")

    def test_double_close_constant_error(self):
        cid = self.registry.create("fixture")["context_id"]
        self.registry.close(cid)
        with self.assertRaises(ContextClosedError) as ctx:
            self.registry.close(cid)
        self.assertEqual(str(ctx.exception), CLOSED_MSG)

    def test_bind_after_close_constant_error_and_no_write(self):
        cid = self.registry.create("fixture")["context_id"]
        closed = self.registry.close(cid)
        with self.assertRaises(ContextClosedError) as ctx:
            self.registry.bind_hermes_run(cid, "run_x")
        self.assertEqual(str(ctx.exception), CLOSED_MSG)
        status = self._status(cid)
        self.assertEqual(status["closed"], closed["closed"])
        self.assertIsNone(status["hermes_run_id"])
        with self.assertRaises(ContextClosedError):
            self.registry.bind_codex_job(cid, WORKSPACE, "job_x")
        self.assertIsNone(self._status(cid)["codex_workspace"])

    def test_conditional_update_classifies_unknown_and_invalid(self):
        missing = "ctx_" + "b" * 32
        with self.assertRaises(ContextError) as ctx:
            self.registry.bind_hermes_run(missing, "run_x")
        self.assertEqual(str(ctx.exception), UNKNOWN_MSG)
        with self.assertRaises(ContextError) as ctx:
            self.registry.close(missing)
        self.assertEqual(str(ctx.exception), UNKNOWN_MSG)
        with self.assertRaises(ContextError) as ctx:
            self.registry.bind_codex_job("bad id!", WORKSPACE, "job_x")
        self.assertEqual(str(ctx.exception), INVALID_MSG)
        with self.assertRaises(ContextError) as ctx:
            self.registry.close("bad id!")
        self.assertEqual(str(ctx.exception), INVALID_MSG)

    def test_observe_updates_at_most_one_row_with_duplicate_run_references(self):
        first = self.registry.create("fixture a")["context_id"]
        second = self.registry.create("fixture b")["context_id"]
        self.registry.bind_hermes_run(first, "run_d")
        self.registry.bind_hermes_run(second, "run_d")
        self.registry.observe_hermes("run_d", "session_1")
        ordered = sorted([first, second])
        self.assertEqual(self._status(ordered[0])["hermes_session_id"], "session_1")
        self.assertIsNone(self._status(ordered[1])["hermes_session_id"])

    def test_observe_excludes_closed_row_and_keeps_pairing(self):
        first = self.registry.create("fixture a")["context_id"]
        second = self.registry.create("fixture b")["context_id"]
        self.registry.bind_hermes_run(first, "run_d")
        self.registry.bind_hermes_run(second, "run_d")
        self.registry.observe_hermes("run_d", "session_1")
        bound = first if self._status(first)["hermes_session_id"] else second
        self.registry.close(bound)
        self.registry.observe_hermes("run_d", "session_2")
        closed_status = self._status(bound)
        self.assertEqual(closed_status["hermes_session_id"], "session_1")
        other = second if bound == first else first
        self.assertEqual(self._status(other)["hermes_session_id"], "session_2")

    def test_restart_keeps_rows_without_auto_rebind(self):
        cid = self.registry.create("fixture")["context_id"]
        before = self._status(cid)
        self.registry.bind_hermes_run(cid, "run_x")
        rebound = GatedRegistry(Path(self.tmp.name), Audit())
        after = rebound.status(cid)
        self.assertEqual(after["context_id"], cid)
        self.assertEqual(after["hermes_run_id"], "run_x")
        self.assertEqual(after["created"], before["created"])
        self.assertIsNone(after["hermes_session_id"])
        fresh = self.registry.create("fixture 2")["context_id"]
        self.assertIsNotNone(self.registry.status(fresh)["created"])


class TestCrossProcessActors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = ContextRegistry(Path(self.tmp.name), Audit())

    def tearDown(self):
        self.tmp.cleanup()

    def test_two_processes_close_commits_before_bind_write(self):
        cid = self.registry.create("fixture")["context_id"]
        ctx = multiprocessing.get_context("fork")
        barrier = ctx.Barrier(2)
        ack = ctx.Event()
        queue = ctx.Queue()
        bind_proc = ctx.Process(target=_cross_proc_worker,
                                args=(self.tmp.name, cid, "bind", barrier, ack, queue))
        close_proc = ctx.Process(target=_cross_proc_worker,
                                 args=(self.tmp.name, cid, "close", barrier, ack, queue))
        bind_proc.start()
        close_proc.start()
        bind_proc.join(timeout=60)
        close_proc.join(timeout=60)
        results = {}
        while not queue.empty():
            role, outcome = queue.get_nowait()
            results[role] = outcome
        self.assertEqual(bind_proc.exitcode, 0)
        self.assertEqual(close_proc.exitcode, 0)
        self.assertEqual(results["bind"], "closed_rejected")
        self.assertEqual(results["close"], "closed")
        status = self.registry.status(cid)
        self.assertIsNotNone(status["closed"])
        self.assertIsNone(status["hermes_run_id"])


class TestWrapperClosedBindingOutcome(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fake = FakeHermes()
        self.codex = FakeCodex()
        self.model_config = Path(self.tmp.name) / "config.yaml"
        self.model_config.write_text("model:\n  default: deepseek/test\n  provider: nous\n")
        self.b = bridge.Bridge("http://127.0.0.1:8642", "test-secret-123", Path(self.tmp.name),
                               httpx.MockTransport(self.fake), self.model_config)
        self.contexts = ContextRegistry(self.b.state, self.b.audit)
        self.mcp = bridge.server(self.b, self.codex, HandsStub(), self.contexts, None, None)

    def tearDown(self):
        self.b.client.close()
        self.tmp.cleanup()

    def _tool(self, name):
        return self.mcp._tool_manager.get_tool(name).fn

    def _close_during_bind(self):
        """The close commits after the backend acknowledgement, before the bind write."""
        original_hermes = ContextRegistry.bind_hermes_run
        original_codex = ContextRegistry.bind_codex_job

        def hermes(registry, context_id, run_id):
            registry.close(context_id)
            return original_hermes(registry, context_id, run_id)

        def codex(registry, context_id, workspace, job_id):
            registry.close(context_id)
            return original_codex(registry, context_id, workspace, job_id)

        self.contexts.bind_hermes_run = hermes.__get__(self.contexts)
        self.contexts.bind_codex_job = codex.__get__(self.contexts)
        self.addCleanup(self._cleanup_patched)

    def _cleanup_patched(self):
        self.contexts.__dict__.pop("bind_hermes_run", None)
        self.contexts.__dict__.pop("bind_codex_job", None)

    def test_hermes_bound_and_no_context_fields_absent(self):
        cid = self.contexts.create("fixture")["context_id"]
        fn = self._tool("hermes_submit_task")
        out = fn(prompt="fixture", request_id="req-bound", context_id=cid)
        self.assertEqual(out["context_binding"], "bound")
        self.assertNotIn("context_binding_note", out)
        self.assertEqual(out["context_id"], cid)
        self.assertEqual(out["run_id"], "run_1")
        plain = fn(prompt="fixture", request_id="req-plain")
        self.assertNotIn("context_binding", plain)
        self.assertNotIn("context_binding_note", plain)
        self.assertNotIn("context_id", plain)

    def test_hermes_closed_after_ack_keeps_ack_and_returns_closed_rejected(self):
        cid = self.contexts.create("fixture")["context_id"]
        self._close_during_bind()
        fn = self._tool("hermes_submit_task")
        out = fn(prompt="fixture", request_id="req-closed", context_id=cid)
        self.assertEqual(out["context_binding"], "closed_rejected")
        self.assertEqual(out["context_binding_note"], _CLOSED_BINDING_NOTE)
        self.assertEqual(out["run_id"], "run_1")
        self.assertEqual(out["request_id"], "req-closed")
        self.assertEqual(out["status"], "started")
        self.assertEqual(out["context_id"], cid)
        self.assertEqual(self.fake.posts, 1)
        self.assertEqual(len(self.b.recent()["runs"]), 1)

    def test_hermes_precheck_rejects_before_backend_call(self):
        cid = self.contexts.create("fixture")["context_id"]
        self.contexts.close(cid)
        fn = self._tool("hermes_submit_task")
        with self.assertRaises(ContextClosedError) as ctx:
            fn(prompt="fixture", request_id="req-pre", context_id=cid)
        self.assertEqual(str(ctx.exception), CLOSED_MSG)
        with self.assertRaises(ContextError) as ctx:
            fn(prompt="fixture", request_id="req-unknown", context_id="ctx_" + "c" * 32)
        self.assertEqual(str(ctx.exception), UNKNOWN_MSG)
        with self.assertRaises(ContextError):
            fn(prompt="fixture", request_id="req-invalid", context_id="bad id!")
        self.assertEqual(self.fake.posts, 0)

    def test_hermes_same_input_replay_adds_no_submission(self):
        cid = self.contexts.create("fixture")["context_id"]
        fn = self._tool("hermes_submit_task")
        first = fn(prompt="fixture", request_id="req-replay", context_id=cid)
        second = fn(prompt="fixture", request_id="req-replay", context_id=cid)
        self.assertEqual(self.fake.posts, 1)
        self.assertTrue(second["replayed_locally"])
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertEqual(second["context_binding"], "bound")

    def test_hermes_submit_failure_and_db_error_keep_errors(self):
        cid = self.contexts.create("fixture")["context_id"]
        fn = self._tool("hermes_submit_task")
        self.fake.lost = True
        with self.assertRaises(bridge.BridgeError):
            fn(prompt="fixture", request_id="req-lost", context_id=cid)
        self.fake.lost = False
        with patch.object(ContextRegistry, "bind_hermes_run",
                          side_effect=sqlite3.OperationalError("database is locked")):
            with self.assertRaises(sqlite3.OperationalError):
                fn(prompt="fixture", request_id="req-dbusy", context_id=cid)

    def test_codex_bound_pending_approval_and_no_context(self):
        cid = self.contexts.create("fixture")["context_id"]
        fn = self._tool("codex_submit_task")
        out = fn(prompt="fixture", workspace=WORKSPACE, mode="workspace-write", context_id=cid)
        self.assertEqual(out["context_binding"], "bound")
        self.assertNotIn("context_binding_note", out)
        self.assertEqual(out["status"], "pending_local_approval")
        self.assertEqual(out["approval"]["policy_root"], WORKSPACE)
        plain = fn(prompt="fixture", workspace=WORKSPACE, mode="read-only")
        self.assertNotIn("context_binding", plain)
        self.assertNotIn("context_binding_note", plain)

    def test_codex_closed_after_ack_keeps_job_and_returns_closed_rejected(self):
        cid = self.contexts.create("fixture")["context_id"]
        self._close_during_bind()
        fn = self._tool("codex_submit_task")
        out = fn(prompt="fixture", workspace=WORKSPACE, mode="workspace-write", context_id=cid)
        self.assertEqual(out["context_binding"], "closed_rejected")
        self.assertEqual(out["context_binding_note"], _CLOSED_BINDING_NOTE)
        self.assertEqual(out["status"], "pending_local_approval")
        self.assertEqual(out["approval"]["policy_root"], WORKSPACE)
        self.assertTrue(out["job_id"].startswith("codex_"))
        self.assertEqual(self.codex.starts, 1)

    def test_codex_precheck_rejects_before_backend_call(self):
        cid = self.contexts.create("fixture")["context_id"]
        self.contexts.close(cid)
        fn = self._tool("codex_submit_task")
        with self.assertRaises(ContextClosedError):
            fn(prompt="fixture", workspace=WORKSPACE, context_id=cid)
        with self.assertRaises(ContextError):
            fn(prompt="fixture", workspace=WORKSPACE, context_id="ctx_" + "d" * 32)
        self.assertEqual(self.codex.starts, 0)

    def test_codex_submit_failure_and_db_error_keep_errors(self):
        cid = self.contexts.create("fixture")["context_id"]
        fn = self._tool("codex_submit_task")
        self.codex.fail = True
        with self.assertRaises(CodexError):
            fn(prompt="fixture", workspace=WORKSPACE, context_id=cid)
        self.codex.fail = False
        with patch.object(ContextRegistry, "bind_codex_job",
                          side_effect=sqlite3.OperationalError("database is locked")):
            with self.assertRaises(sqlite3.OperationalError):
                fn(prompt="fixture", workspace=WORKSPACE, context_id=cid)


if __name__ == "__main__":
    unittest.main()
