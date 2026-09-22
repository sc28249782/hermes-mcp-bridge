"""Explicit metadata-only work contexts; never stores prompts or outputs."""
from __future__ import annotations
from contextlib import contextmanager
import re
import sqlite3
import time
import uuid
from pathlib import Path

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

class ContextError(RuntimeError):
    pass

class ContextRegistry:
    def __init__(self, state: Path, audit):
        # Bridge creates the private state directory (0700) before this registry is constructed.
        self.path = Path(state) / "contexts.sqlite3"
        self.audit = audit
        with self.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS contexts (
                context_id TEXT PRIMARY KEY, label TEXT NOT NULL, created REAL NOT NULL,
                updated REAL NOT NULL, closed REAL, hermes_session_id TEXT,
                hermes_run_id TEXT, codex_workspace TEXT, codex_job_id TEXT)""")
        self.path.chmod(0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _text(value: str, field: str, maximum: int = 80) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(c in value for c in "\r\n\x00"):
            raise ContextError(f"{field} must be 1-{maximum} characters without line breaks.")
        return value.strip()

    def create(self, label: str) -> dict:
        label = self._text(label, "label")
        now = time.time()
        context_id = "ctx_" + uuid.uuid4().hex
        with self.db() as db:
            db.execute("INSERT INTO contexts(context_id,label,created,updated) VALUES(?,?,?,?)",
                       (context_id, label, now, now))
        self.audit.record("context", "create", context_id, "created", {"label_chars": len(label)})
        return self.status(context_id)

    def _row(self, context_id: str, usable: bool = True):
        if not isinstance(context_id, str) or not _ID.fullmatch(context_id):
            raise ContextError("Invalid context_id.")
        with self.db() as db:
            row = db.execute("SELECT * FROM contexts WHERE context_id=?", (context_id,)).fetchone()
        if not row:
            raise ContextError("Unknown context_id.")
        if usable and row["closed"] is not None:
            raise ContextError("Context is closed; create a new context_id instead.")
        return row

    @staticmethod
    def _public(row):
        return {k: row[k] for k in ("context_id","label","created","updated","closed","hermes_session_id","hermes_run_id","codex_workspace","codex_job_id")}

    def status(self, context_id: str) -> dict:
        return self._public(self._row(context_id, usable=False))

    def recent(self, limit: int = 30) -> dict:
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ContextError("limit must be 1-100.")
        with self.db() as db:
            rows = db.execute("SELECT * FROM contexts ORDER BY updated DESC LIMIT ?", (limit,)).fetchall()
        return {"contexts": [self._public(r) for r in rows],
                "note": "Contexts contain metadata only; prompts and outputs are never stored or replayed."}

    def close(self, context_id: str) -> dict:
        self._row(context_id)
        now = time.time()
        with self.db() as db:
            db.execute("UPDATE contexts SET closed=?,updated=? WHERE context_id=?", (now,now,context_id))
        self.audit.record("context", "close", context_id, "closed", {})
        return self.status(context_id)

    def hermes_session(self, context_id: str) -> str | None:
        return self._row(context_id)["hermes_session_id"]

    def bind_hermes_run(self, context_id: str, run_id: str):
        self._row(context_id)
        with self.db() as db:
            db.execute("UPDATE contexts SET hermes_run_id=?,updated=? WHERE context_id=?",
                       (run_id,time.time(),context_id))

    def observe_hermes(self, run_id: str, session_id: str | None):
        if not session_id:
            return
        with self.db() as db:
            row = db.execute("SELECT context_id FROM contexts WHERE hermes_run_id=? AND closed IS NULL", (run_id,)).fetchone()
            if row:
                db.execute("UPDATE contexts SET hermes_session_id=?,updated=? WHERE context_id=?",
                           (session_id,time.time(),row["context_id"]))

    def codex_workspace(self, context_id: str) -> str | None:
        return self._row(context_id)["codex_workspace"]

    def bind_codex_job(self, context_id: str, workspace: str, job_id: str):
        self._row(context_id)
        with self.db() as db:
            db.execute("UPDATE contexts SET codex_workspace=?,codex_job_id=?,updated=? WHERE context_id=?",
                       (workspace,job_id,time.time(),context_id))
