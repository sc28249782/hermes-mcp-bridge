"""SPEC section 21: deterministic lifecycle/concurrency acceptance for the
context registry and the closed-binding submit outcome (D1-D5).

Thread and process gates sit before the SQL writer transaction starts; a test
never holds a SQLite lock while waiting for a close commit. Bounded waits are
failsafes only, never scheduling by time.sleep. No P2 apply/delete, no schema
change, no new audit event, no real model/backend call.
"""
from pathlib import Path
from contextlib import contextmanager
import multiprocessing
import queue as queue_mod
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
except ImportError:  # baseline has no typed closed error; its plain ContextError still fails these tests
    class ContextClosedError(ContextError):
        pass

CLOSED_MSG = "Context is closed; create a new context_id instead."
UNKNOWN_MSG = "Unknown context_id."
INVALID_MSG = "Invalid context_id."
WORKSPACE = "workspace-fixture"
HERMES_BIND_SQL = "UPDATE contexts SET hermes_run_id"
CODEX_BIND_SQL = "UPDATE contexts SET codex_workspace"
CLOSE_SQL = "UPDATE contexts SET closed"
OBSERVE_SQL = "UPDATE contexts SET hermes_session_id"


class Audit:
    def __init__(self): self.events = []
    def record(self, *args): self.events.append(args)


class _GatedConnection:
    """Proxy that pauses one intercepted UPDATE before it executes."""

    def __init__(self, conn, gates):
        self._conn = conn
        self._gates = gates

    def execute(self, sql, params=()):
        for prefix, (release, arrived) in list(self._gates.items()):
            if sql.startswith(prefix):
                # The gated UPDATE has not executed yet, so no writer transaction
                # is open on this connection and the close commit cannot deadlock.
                assert not self._conn.in_transaction, "SQLite lock held while waiting for the gate"
                self._gates.pop(prefix)
                if arrived is not None:
                    arrived.set()
                if not release.wait(timeout=30):
                    raise AssertionError(f"gate timeout waiting for: {prefix}")
        return self._conn.execute(sql, params)

    def __getattr__(self, name):
        return getattr(self._conn, name)


class ExecGateRegistry(ContextRegistry):
    """Gates fire between the precheck SELECT and the UPDATE execute."""

    def __init__(self, *args, **kwargs):
        # Set before super().__init__: the base constructor already opens db().
        self._gates = {}
        super().__init__(*args, **kwargs)

    def gate(self, sql_prefix, release, arrived=None):
        self._gates[sql_prefix] = (release, arrived)

    @contextmanager
    def db(self):
        with super().db() as conn:
            yield _GatedConnection(conn, self._gates)


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
    """bind: pauses its UPDATE before the writer transaction until ack; close: commits then sets ack."""
    class SilentAudit:
        def record(self, *args):
            pass
    registry = ExecGateRegistry(Path(state_dir), SilentAudit())
    try:
        if role == "bind":
            registry.gate(HERMES_BIND_SQL, ack)
            barrier.wait(timeout=30)
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
    finally:
        queue.close()


class TestRegistryLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = ExecGateRegistry(Path(self.tmp.name), Audit())

    def tearDown(self):
        self.tmp.cleanup()

    def _status(self, cid):
        return self.registry.status(cid)

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
        statuses = [self.registry.status(first), self.registry.status(second)]
        with_session = [s for s in statuses if s["hermes_session_id"] == "session_1"]
        # §21.3 requires at-most-one-row and pairing, not which candidate wins.
        self.assertEqual(len(with_session), 1)
        self.assertIsNone(statuses[0]["hermes_session_id"] if with_session[0] is statuses[1]
                          else statuses[1]["hermes_session_id"])
        self.assertEqual([s["hermes_run_id"] for s in statuses], ["run_d", "run_d"])

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
        fresh_registry = ExecGateRegistry(Path(self.tmp.name), Audit())
        after = fresh_registry.status(cid)
        self.assertEqual(after["context_id"], cid)
        self.assertEqual(after["hermes_run_id"], "run_x")
        self.assertEqual(after["created"], before["created"])
        self.assertIsNone(after["hermes_session_id"])
        fresh = self.registry.create("fixture 2")["context_id"]
        self.assertIsNotNone(self.registry.status(fresh)["created"])


class TestStaleWriteInterleaving(unittest.TestCase):
    """Gates fire between the precheck SELECT and the UPDATE execute: the close
    commits while the writer is paused, then the write resumes. On the
    pre-amendment baseline the unconditional UPDATE lands on the closed row;
    the conditional UPDATE fails closed and leaves the row unchanged."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = ExecGateRegistry(Path(self.tmp.name), Audit())
        self.closer = ExecGateRegistry(Path(self.tmp.name), Audit())

    def tearDown(self):
        self.tmp.cleanup()

    def test_close_wins_hermes_bind_rejected_row_unchanged(self):
        cid = self.registry.create("fixture")["context_id"]
        arrived, release = threading.Event(), threading.Event()
        self.registry.gate(HERMES_BIND_SQL, release, arrived)
        result = {}

        def bind():
            try:
                self.registry.bind_hermes_run(cid, "run_x")
                result["outcome"] = "written"
            except ContextError as exc:
                result["outcome"] = (type(exc).__name__, str(exc))

        thread = threading.Thread(target=bind)
        thread.start()
        self.assertTrue(arrived.wait(timeout=30), "bind never reached the gated UPDATE")
        self.closer.close(cid)  # commits while the bind UPDATE is paused
        release.set()
        thread.join(timeout=30)
        self.assertEqual(result["outcome"], (ContextClosedError.__name__, CLOSED_MSG))
        status = self.registry.status(cid)
        self.assertIsNotNone(status["closed"])
        self.assertIsNone(status["hermes_run_id"])

    def test_close_wins_codex_bind_rejected_row_unchanged(self):
        cid = self.registry.create("fixture")["context_id"]
        arrived, release = threading.Event(), threading.Event()
        self.registry.gate(CODEX_BIND_SQL, release, arrived)
        result = {}

        def bind():
            try:
                self.registry.bind_codex_job(cid, WORKSPACE, "job_x")
                result["outcome"] = "written"
            except ContextError as exc:
                result["outcome"] = (type(exc).__name__, str(exc))

        thread = threading.Thread(target=bind)
        thread.start()
        self.assertTrue(arrived.wait(timeout=30), "bind never reached the gated UPDATE")
        self.closer.close(cid)
        release.set()
        thread.join(timeout=30)
        self.assertEqual(result["outcome"], (ContextClosedError.__name__, CLOSED_MSG))
        status = self.registry.status(cid)
        self.assertIsNotNone(status["closed"])
        self.assertIsNone(status["codex_workspace"])

    def test_bind_wins_then_close_retains_binding(self):
        cid = self.registry.create("fixture")["context_id"]
        arrived, release = threading.Event(), threading.Event()
        self.registry.gate(CLOSE_SQL, release, arrived)
        result = {}

        def close():
            try:
                self.registry.close(cid)
                result["outcome"] = "closed"
            except ContextError as exc:
                result["outcome"] = str(exc)

        thread = threading.Thread(target=close)
        thread.start()
        self.assertTrue(arrived.wait(timeout=30), "close never reached the gated UPDATE")
        self.registry.bind_hermes_run(cid, "run_x")  # commits while close is paused
        release.set()
        thread.join(timeout=30)
        self.assertEqual(result["outcome"], "closed")
        status = self.registry.status(cid)
        self.assertIsNotNone(status["closed"])
        self.assertEqual(status["hermes_run_id"], "run_x")

    def test_observe_stale_rebind_is_guarded(self):
        cid = self.registry.create("fixture")["context_id"]
        self.registry.bind_hermes_run(cid, "run_old")
        arrived, release = threading.Event(), threading.Event()
        self.registry.gate(OBSERVE_SQL, release, arrived)

        def observe():
            self.registry.observe_hermes("run_old", "stale_session")

        thread = threading.Thread(target=observe)
        thread.start()
        self.assertTrue(arrived.wait(timeout=30), "observe never reached the gated UPDATE")
        self.closer.bind_hermes_run(cid, "run_new")  # rebind while observe's UPDATE is paused
        release.set()
        thread.join(timeout=30)
        status = self.registry.status(cid)
        self.assertEqual(status["hermes_run_id"], "run_new")
        self.assertIsNone(status["hermes_session_id"])
        self.assertEqual(self.registry._gates, {})


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
        procs = [
            ctx.Process(target=_cross_proc_worker,
                        args=(self.tmp.name, cid, role, barrier, ack, queue))
            for role in ("bind", "close")
        ]
        for proc in procs:
            proc.start()
        results = {}
        try:
            for _ in range(2):
                role, outcome = queue.get(timeout=60)
                results[role] = outcome
        finally:
            for proc in procs:
                proc.join(timeout=10)
                if proc.is_alive():
                    proc.terminate()
                    proc.join(timeout=10)
            queue.close()
            queue.join_thread()
        self.assertEqual(results["bind"], "closed_rejected")
        self.assertEqual(results["close"], "closed")
        for proc in procs:
            self.assertEqual(proc.exitcode, 0)
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

    def test_empty_context_id_is_invalid_zero_backend_calls(self):
        fn = self._tool("hermes_submit_task")
        with self.assertRaises(ContextError) as ctx:
            fn(prompt="fixture", request_id="req-empty", context_id="")
        self.assertEqual(str(ctx.exception), INVALID_MSG)
        self.assertEqual(self.fake.posts, 0)
        codex_fn = self._tool("codex_submit_task")
        with self.assertRaises(ContextError) as ctx:
            codex_fn(prompt="fixture", workspace=WORKSPACE, context_id="")
        self.assertEqual(str(ctx.exception), INVALID_MSG)
        with self.assertRaises(ContextError) as ctx:
            codex_fn(prompt="fixture", workspace=WORKSPACE, context_id="bad id!")
        self.assertEqual(str(ctx.exception), INVALID_MSG)
        self.assertEqual(self.codex.starts, 0)

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
