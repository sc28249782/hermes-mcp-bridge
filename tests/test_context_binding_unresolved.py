"""SPEC section 22: unresolved binding outcome after a normal backend
acknowledgement (binding_unresolved), produced by the ordered, closed catch
policy wrapped only around the registry binding call.

Deterministic synthetic failures only: one-shot instance patches and a
one-shot commit gate on the real ContextRegistry sqlite state; no sleeps,
no thread or process ordering, no real backend, no production state.
Excluded exceptions must propagate unchanged, and failures outside the
binding call (precheck, submit, acknowledgement extraction) must keep the
existing error.
"""
from pathlib import Path
from copy import deepcopy
from contextlib import contextmanager
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import httpx

import bridge
from codex_core import CodexError
from contexts import ContextClosedError, ContextError, ContextRegistry

try:
    from bridge import _CLOSED_BINDING_NOTE
except ImportError:  # baseline has no constant; the tests below fail on its behavior
    _CLOSED_BINDING_NOTE = ("Context was closed before binding. The task remains owned by this bridge. "
                            "Do not resubmit; retrieve it by its existing identifiers.")
try:
    from bridge import _UNRESOLVED_BINDING_NOTE
except ImportError:  # baseline has no constant; the tests below fail on its behavior
    _UNRESOLVED_BINDING_NOTE = ("Context binding outcome is unresolved. The task remains owned by this bridge "
                                "and the context binding may already be recorded. Do not resubmit; retrieve the "
                                "task by its existing identifiers and check task status.")

from test_context_lifecycle import (FakeCodex, FakeHermes, HandsStub,
                                    CLOSED_MSG, UNKNOWN_MSG, WORKSPACE)

HERMES_ACK_KEYS = {"run_id", "request_id", "status", "replayed",
                   "requested_model", "requested_provider", "requested_model_options", "next"}
CODEX_ACK_KEYS = {"job_id", "status", "approval", "next"}
BINDING_FIELDS = {"context_id", "context_binding", "context_binding_note"}


class Audit:
    def __init__(self): self.events = []
    def record(self, *args): self.events.append(args)


class CommitGateRegistry(ContextRegistry):
    """One-shot commit gate: the next db() commit with a pending write raises
    the armed failure instead of committing. A SELECT-only use (precheck)
    never holds the writer transaction, so it commits normally and the gate
    stays armed for the binding UPDATE."""

    _commit_failure: BaseException | None

    def __init__(self, *args, **kwargs):
        self._commit_failure = None
        super().__init__(*args, **kwargs)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            yield db
            if self._commit_failure is not None and db.in_transaction:
                failure, self._commit_failure = self._commit_failure, None
                raise failure
            db.commit()
        finally:
            db.close()


class TestBindingUnresolvedOutcome(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fake = FakeHermes()
        self.codex = FakeCodex()
        self.model_config = Path(self.tmp.name) / "config.yaml"
        self.model_config.write_text("model:\n  default: deepseek/test\n  provider: nous\n")
        self.b = bridge.Bridge("http://127.0.0.1:8642", "test-secret-123", Path(self.tmp.name),
                               httpx.MockTransport(self.fake), self.model_config)
        self.contexts = CommitGateRegistry(self.b.state, self.b.audit)
        self.mcp = bridge.server(self.b, self.codex, HandsStub(), self.contexts, None, None)
        self.backend_acks = {}
        # Snapshot the entire acknowledgement before the wrapper adds binding
        # fields. Comparing every nested value detects payload changes as well
        # as missing/extra keys.
        for backend, obj in (("hermes", self.b), ("codex", self.codex)):
            original_submit = obj.submit

            def capture_ack(*args, _backend=backend, _submit=original_submit, **kwargs):
                output = _submit(*args, **kwargs)
                self.backend_acks[_backend] = deepcopy(output)
                return output

            patcher = patch.object(obj, "submit", side_effect=capture_ack)
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.b.client.close()
        self.tmp.cleanup()

    def _tool(self, name):
        return self.mcp._tool_manager.get_tool(name).fn

    def _submit(self, backend, cid):
        if backend == "hermes":
            request_id = f"req-{cid[-8:]}"
            return self._tool("hermes_submit_task")(prompt="fixture", request_id=request_id, context_id=cid)
        return self._tool("codex_submit_task")(prompt="fixture", workspace=WORKSPACE,
                                               mode="workspace-write", context_id=cid)

    def _bind_attr(self, backend):
        return "bind_hermes_run" if backend == "hermes" else "bind_codex_job"

    def _assert_unresolved(self, backend, out, cid, calls_before, row_bound):
        """Full backend acknowledgement preserved, exact note, backend calls one,
        and the real row state read back."""
        self.assertEqual(out["context_binding"], "binding_unresolved")
        self.assertEqual(out["context_binding_note"], _UNRESOLVED_BINDING_NOTE)
        self.assertEqual(out["context_id"], cid)
        self.assertEqual({key: value for key, value in out.items() if key not in BINDING_FIELDS},
                         self.backend_acks[backend])
        status = self.contexts.status(cid)
        if backend == "hermes":
            self.assertEqual(set(out) - BINDING_FIELDS, HERMES_ACK_KEYS)
            self.assertEqual(out["run_id"], "run_%d" % (self.fake.posts))
            self.assertEqual(out["status"], "started")
            self.assertFalse(out["replayed"])
            self.assertEqual(out["request_id"], "req-%s" % cid[-8:])
            self.assertEqual(self.fake.posts, calls_before + 1)
            self.assertEqual(status["hermes_run_id"], out["run_id"] if row_bound else None)
        else:
            self.assertEqual(set(out) - BINDING_FIELDS, CODEX_ACK_KEYS)
            self.assertEqual(out["status"], "pending_local_approval")
            self.assertEqual(out["approval"]["policy_root"], WORKSPACE)
            self.assertEqual(self.codex.starts, calls_before + 1)
            self.assertTrue(out["job_id"].startswith("codex_"))
            self.assertEqual(status["codex_job_id"], out["job_id"] if row_bound else None)
            self.assertIsNone(status["closed"])

    def test_allowlisted_failures_convert_at_each_phase(self):
        for backend in ("hermes", "codex"):
            for failure in (sqlite3.OperationalError("database is locked"),
                            ContextError(UNKNOWN_MSG)):
                for phase in ("before", "commit", "after"):
                    with self.subTest(backend=backend, failure=type(failure).__name__, phase=phase):
                        cid = self.contexts.create("fixture %s %s %s" % (backend, type(failure).__name__, phase))["context_id"]
                        calls_before = self.fake.posts if backend == "hermes" else self.codex.starts
                        attr = self._bind_attr(backend)
                        original = getattr(ContextRegistry, attr)
                        if phase == "before":
                            patched = patch.object(self.contexts, attr, side_effect=failure)
                        elif phase == "commit":
                            self.contexts._commit_failure = failure
                            patched = None
                        else:  # after: the binding write commits, then the failure raises
                            def raise_after_commit(*args, _original=original, _registry=self.contexts, _failure=failure):
                                _original(_registry, *args)
                                raise _failure
                            patched = patch.object(self.contexts, attr, side_effect=raise_after_commit)
                        try:
                            if patched is not None:
                                with patched:
                                    out = self._submit(backend, cid)
                            else:
                                out = self._submit(backend, cid)
                        finally:
                            self.contexts._commit_failure = None
                        # before/commit: no write lands; after: the row is bound
                        # even though the outcome stays binding_unresolved.
                        self._assert_unresolved(backend, out, cid, calls_before,
                                                row_bound=(phase == "after"))

    def test_closed_error_is_matched_before_context_error(self):
        # ContextClosedError is a ContextError subclass: the first clause must
        # win and keep the existing closed_rejected outcome and note.
        for backend in ("hermes", "codex"):
            with self.subTest(backend=backend):
                cid = self.contexts.create("fixture closed %s" % backend)["context_id"]
                calls_before = self.fake.posts if backend == "hermes" else self.codex.starts
                with patch.object(self.contexts, self._bind_attr(backend),
                                  side_effect=ContextClosedError(CLOSED_MSG)):
                    out = self._submit(backend, cid)
                self.assertEqual(out["context_binding"], "closed_rejected")
                self.assertEqual(out["context_binding_note"], _CLOSED_BINDING_NOTE)
                self.assertEqual(self.contexts.status(cid)["closed"], None)
                if backend == "hermes":
                    self.assertEqual(self.fake.posts, calls_before + 1)
                else:
                    self.assertEqual(self.codex.starts, calls_before + 1)

    def test_excluded_exceptions_propagate_unchanged(self):
        excluded = (sqlite3.ProgrammingError, sqlite3.IntegrityError, sqlite3.InternalError,
                    sqlite3.DataError, sqlite3.NotSupportedError, sqlite3.DatabaseError,
                    AssertionError, TypeError, KeyError, KeyboardInterrupt, SystemExit)
        for backend in ("hermes", "codex"):
            for exc_class in excluded:
                with self.subTest(backend=backend, exception=exc_class.__name__):
                    cid = self.contexts.create("fixture %s %s" % (backend, exc_class.__name__))["context_id"]
                    calls_before = self.fake.posts if backend == "hermes" else self.codex.starts
                    with patch.object(self.contexts, self._bind_attr(backend), side_effect=exc_class()):
                        with self.assertRaises(exc_class):
                            self._submit(backend, cid)
                    status = self.contexts.status(cid)
                    self.assertIsNone(status["hermes_run_id"] if backend == "hermes" else status["codex_job_id"])
                    if backend == "hermes":
                        self.assertEqual(self.fake.posts, calls_before + 1)
                    else:
                        self.assertEqual(self.codex.starts, calls_before + 1)

    def test_precheck_rejection_and_no_context_stay_unchanged(self):
        # A ContextError raised by the precheck sits OUTSIDE the binding-call
        # catch and must propagate, with zero backend calls.
        cid = self.contexts.create("fixture precheck")["context_id"]
        self.contexts.close(cid)
        for backend in ("hermes", "codex"):
            with self.subTest(backend=backend):
                calls_before = self.fake.posts if backend == "hermes" else self.codex.starts
                fn = self._tool("hermes_submit_task" if backend == "hermes" else "codex_submit_task")
                with self.assertRaises(ContextClosedError):
                    fn(**({"prompt": "fixture", "request_id": "req-pre", "context_id": cid} if backend == "hermes"
                         else {"prompt": "fixture", "workspace": WORKSPACE, "context_id": cid}))
                with self.assertRaises(ContextError):
                    fn(**({"prompt": "fixture", "request_id": "req-unknown", "context_id": "ctx_" + "e" * 32} if backend == "hermes"
                         else {"prompt": "fixture", "workspace": WORKSPACE, "context_id": "ctx_" + "e" * 32}))
                if backend == "hermes":
                    self.assertEqual(self.fake.posts, calls_before)
                else:
                    self.assertEqual(self.codex.starts, calls_before)
        # No context_id: the normal acknowledgement carries no binding field.
        out = self._tool("hermes_submit_task")(prompt="fixture", request_id="req-plain")
        self.assertNotIn("context_binding", out)
        self.assertNotIn("context_binding_note", out)
        self.assertNotIn("context_id", out)

    def test_submit_raise_with_persisted_rows_keeps_error(self):
        # Hermes: the transport times out after the POST was accepted; the runs
        # row is already persisted and the existing error is kept.
        cid = self.contexts.create("fixture lost")["context_id"]
        self.fake.lost = True
        with self.assertRaises(bridge.BridgeError):
            self._tool("hermes_submit_task")(prompt="fixture", request_id="req-lost", context_id=cid)
        self.fake.lost = False
        self.assertEqual(len(self.b.recent()["runs"]), 1)
        self.assertEqual(self.fake.posts, 1)
        # Codex boundary fixture: commit an actual synthetic job row to a
        # separate SQLite store, then raise without returning an acknowledgement.
        # This proves wrapper behavior after durable registration, not native
        # Codex process startup or a real backend acceptance.
        cid2 = self.contexts.create("fixture codex raise")["context_id"]
        job_store = Path(self.tmp.name) / "synthetic-codex-jobs.sqlite3"
        job_id = "codex_" + "a" * 32

        def persist_then_raise(*args, **kwargs):
            with sqlite3.connect(job_store) as db:
                db.execute("CREATE TABLE jobs (job_id TEXT PRIMARY KEY, status TEXT)")
                db.execute("INSERT INTO jobs VALUES (?, ?)", (job_id, "queued"))
            raise CodexError("start failed after durable rows")

        with patch.object(self.codex, "submit", side_effect=persist_then_raise) as submit:
            with patch.object(self.contexts, "bind_codex_job") as bind:
                with self.assertRaises(CodexError):
                    self._tool("codex_submit_task")(prompt="fixture", workspace=WORKSPACE, context_id=cid2)
                bind.assert_not_called()
            submit.assert_called_once()
        with sqlite3.connect(job_store) as db:
            self.assertEqual(db.execute("SELECT job_id, status FROM jobs").fetchall(),
                             [(job_id, "queued")])
        self.assertIsNone(self.contexts.status(cid2)["codex_job_id"])

    def test_guarded_replay_after_unresolved_binding_adds_no_post(self):
        cid = self.contexts.create("fixture replay")["context_id"]
        original = ContextRegistry.bind_hermes_run

        def raise_after_commit(context_id, run_id):
            original(self.contexts, context_id, run_id)
            raise ContextError(UNKNOWN_MSG)

        with patch.object(self.contexts, "bind_hermes_run", side_effect=raise_after_commit):
            first = self._submit("hermes", cid)
        self.assertEqual(first["context_binding"], "binding_unresolved")
        self.assertEqual(self.fake.posts, 1)
        second = self._submit("hermes", cid)
        self.assertEqual(self.fake.posts, 1)  # no new POST for the same request
        self.assertTrue(second["replayed_locally"])
        self.assertEqual(second["run_id"], first["run_id"])
        self.assertEqual(second["context_binding"], "bound")
        self.assertNotIn("context_binding_note", second)

    def test_invalid_ack_extraction_outside_catch_cannot_convert(self):
        # The ack-field extraction sits outside the binding-call catch: a
        # malformed acknowledgement propagates as the existing error even
        # though a conversion helper could have swallowed a ContextError
        # raised inside the try block.
        cid = self.contexts.create("fixture badack")["context_id"]
        with patch.object(self.b, "submit", return_value={"status": "started"}):
            with self.assertRaises(KeyError):
                self._tool("hermes_submit_task")(prompt="fixture", request_id="req-badack", context_id=cid)
        self.assertEqual(self.contexts.status(cid)["hermes_run_id"], None)
        self.assertEqual(self.fake.posts, 0)


if __name__ == "__main__":
    unittest.main()
