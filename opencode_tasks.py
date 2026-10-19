"""Opt-in, unsandboxed OpenCode jobs; see SPEC section 18."""
from __future__ import annotations
from contextlib import contextmanager
import codecs
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import stat
import subprocess
import sys
import threading
import time
from audit import AuditLog
from config_schema import ConfigError, load_bridge_config

SESSION_PATTERN = re.compile(r"ses_[A-Za-z0-9]{8,64}")
TERMINAL = ("completed", "failed", "cancelled", "permission_required", "unknown_exit")
ACTIVE = ("pending", "running", "unknown_exit")
MAX_PROMPT_CHARS = (1, 131072)
MAX_RUNTIME_SECONDS = (1, 14400)
MAX_OUTPUT_BYTES = (65536, 8388608)
START_GRACE = 10

class OpenCodeTaskError(RuntimeError):
    pass

def _proc_starttime(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return None if fields[0] == "Z" else int(fields[19])
    except (OSError, ValueError, IndexError, TypeError):
        return None

def _text(value, label, maximum=4096):
    if not isinstance(value, str) or not value or len(value) > maximum or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise OpenCodeTaskError(f"{label} must be bounded text without control characters")
    return value

def _canonical_workspace(value):
    _text(value, "workspace")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise OpenCodeTaskError("workspace must be an absolute path")
    try:
        path = path.resolve(strict=True)
    except OSError:
        raise OpenCodeTaskError("workspace must be an existing directory") from None
    if not path.is_dir():
        raise OpenCodeTaskError("workspace must be an existing directory")
    return str(path)

class OpenCodeTasks:
    def __init__(self, config, state, audit_config=None):
        if not isinstance(config, dict) or not isinstance(config.get("execution", {}), dict):
            raise OpenCodeTaskError("opencode.execution must be an object")
        execution = config.get("execution", {})
        self.enabled = execution.get("enabled", False)
        if not isinstance(self.enabled, bool):
            raise OpenCodeTaskError("opencode.execution.enabled must be boolean")
        self.state = Path(state)
        if not self.enabled:
            return
        self.state = self.state.resolve()
        if config.get("enabled") is not True:
            raise OpenCodeTaskError("execution requires opencode.enabled")
        self.binary = str(Path(_text(config.get("binary"), "opencode.binary")).expanduser())
        if not Path(self.binary).is_absolute():
            raise OpenCodeTaskError("opencode.binary must be absolute")
        self._validate_binary()
        for key, default, bounds, attribute in (
            ("max_prompt_chars", 32000, MAX_PROMPT_CHARS, "max_prompt"),
            ("max_runtime_seconds", 1800, MAX_RUNTIME_SECONDS, "max_runtime"),
            ("max_output_bytes", 524288, MAX_OUTPUT_BYTES, "max_output")):
            value = execution.get(key, default)
            if type(value) is not int or not bounds[0] <= value <= bounds[1]:
                raise OpenCodeTaskError(f"opencode.execution.{key} must be {bounds[0]}-{bounds[1]}")
            setattr(self, attribute, value)
        workspaces, models = execution.get("allowed_workspaces"), execution.get("allowed_models")
        if not isinstance(workspaces, list) or not workspaces or not isinstance(models, list) or not models:
            raise OpenCodeTaskError("execution requires nonempty allowed_workspaces and allowed_models")
        self.allowed_workspaces = tuple(dict.fromkeys(_canonical_workspace(p) for p in workspaces))
        for model in models:
            _text(model, "model", 128)
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._/+:#-]*", model):
                raise OpenCodeTaskError("model must use provider/model#variant form")
        self.allowed_models = tuple(dict.fromkeys(models))
        if any(self.state.is_relative_to(Path(p)) for p in self.allowed_workspaces):
            raise OpenCodeTaskError("OpenCode state and outputs must be outside every allowed workspace")
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.state.chmod(0o700)
        self.logs = self.state / "opencode-task-logs"
        self.logs.mkdir(mode=0o700, exist_ok=True)
        self.logs.chmod(0o700)
        self.audit_config = audit_config
        self.audit = AuditLog(self.state, audit_config)
        self.dbpath = self.state / "opencode-tasks.sqlite3"
        fd = os.open(self.dbpath, os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        self.dbpath.chmod(0o600)
        with self.db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY, request_id TEXT UNIQUE, fingerprint TEXT NOT NULL,
                created REAL NOT NULL, started REAL, finished REAL,
                workspace TEXT NOT NULL, session_id TEXT NOT NULL, model TEXT NOT NULL,
                prompt TEXT NOT NULL, status TEXT NOT NULL, pid INTEGER, child_pid INTEGER,
                worker_start_ticks INTEGER, child_start_ticks INTEGER,
                exit_code INTEGER, log_path TEXT NOT NULL, err_path TEXT NOT NULL,
                binary TEXT NOT NULL, max_output_bytes INTEGER NOT NULL,
                max_runtime_seconds INTEGER NOT NULL, cancel_flag INTEGER NOT NULL DEFAULT 0,
                last_known_state TEXT, last_transition_at REAL, transition_actor TEXT,
                transition_reason TEXT, result_reason TEXT)''')

    @classmethod
    def from_config(cls, root):
        try:
            config, _ = load_bridge_config(root)
        except ConfigError as exc:
            raise OpenCodeTaskError(str(exc)) from exc
        return cls(config.get("opencode", {}), root / "state", config.get("audit"))

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.dbpath, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _require_enabled(self):
        if not self.enabled:
            raise OpenCodeTaskError("OpenCode task execution is disabled; review docs/SECURITY.md before enabling it")

    def _validate_binary(self):
        try:
            valid = stat.S_ISREG(Path(self.binary).stat().st_mode) and os.access(self.binary, os.X_OK)
        except OSError:
            valid = False
        if not valid:
            raise OpenCodeTaskError("opencode.binary is not a regular executable file")

    @staticmethod
    def _row_for(db, job_id):
        row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise OpenCodeTaskError("unknown job_id")
        return row

    def _row(self, job_id):
        with self.db() as db:
            return self._row_for(db, job_id)

    def _reconcile(self, db):
        for row in db.execute("SELECT * FROM jobs WHERE status IN ('pending','running')").fetchall():
            if time.time() - row["created"] < START_GRACE:
                continue
            ticks = _proc_starttime(row["pid"]) if row["pid"] else None
            if ticks is None or ticks != row["worker_start_ticks"]:
                db.execute("UPDATE jobs SET status='unknown_exit',finished=?,transition_actor='controller',transition_reason='worker_identity_lost',result_reason='Worker exit could not be confirmed' WHERE job_id=? AND status IN ('pending','running')", (time.time(), row["job_id"]))

    @staticmethod
    def _ack(row):
        return {k: row[k] for k in ("job_id", "status", "session_id", "model")}

    @staticmethod
    def _fingerprint(prompt, workspace, model, requested_session):
        return hashlib.sha256(json.dumps([prompt, workspace, model, requested_session], ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()

    def submit(self, prompt, workspace, request_id, session_id=None, model=None):
        self._require_enabled()
        if not isinstance(prompt, str) or not prompt or len(prompt) > self.max_prompt:
            raise OpenCodeTaskError(f"prompt must be 1-{self.max_prompt} characters")
        try:
            prompt.encode("utf-8")
        except UnicodeError:
            raise OpenCodeTaskError("prompt must be valid UTF-8 text") from None
        if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id):
            raise OpenCodeTaskError("request_id must be 1-128 ASCII letters, digits, hyphens or underscores")
        workspace = _canonical_workspace(workspace)
        if workspace not in self.allowed_workspaces:
            raise OpenCodeTaskError("workspace is not allowlisted")
        if session_id is not None and (not isinstance(session_id, str) or not SESSION_PATTERN.fullmatch(session_id)):
            raise OpenCodeTaskError("invalid bridge session_id")
        if model is not None and (not isinstance(model, str) or model not in self.allowed_models):
            raise OpenCodeTaskError("model is not allowlisted")
        self._validate_binary()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._reconcile(db)
            existing = db.execute("SELECT * FROM jobs WHERE request_id=?", (request_id,)).fetchone()
            if existing:
                chosen = existing["model"] if model is None else model
                if existing["fingerprint"] != self._fingerprint(prompt, workspace, chosen, session_id):
                    raise OpenCodeTaskError("request_id was already used with different inputs")
                return self._ack(existing)
            owner = None
            if session_id:
                owner = db.execute("SELECT * FROM jobs WHERE session_id=? ORDER BY created DESC,rowid DESC LIMIT 1", (session_id,)).fetchone()
                if not owner or owner["workspace"] != workspace or owner["status"] != "completed":
                    raise OpenCodeTaskError("resume requires a completed bridge-owned session in the same workspace")
            chosen = model or (owner["model"] if owner else self.allowed_models[0])
            if chosen not in self.allowed_models or (owner and chosen != owner["model"]):
                raise OpenCodeTaskError("resume requires the same allowlisted model")
            if db.execute("SELECT 1 FROM jobs WHERE status IN ('pending','running','unknown_exit') LIMIT 1").fetchone():
                raise OpenCodeTaskError("another OpenCode task is active or unresolved; submission is busy")
            job_id = "oct_" + secrets.token_hex(12)
            actual_session = session_id or "ses_" + secrets.token_hex(16)
            paths = [str(self.logs / (job_id + suffix)) for suffix in (".jsonl", ".stderr")]
            for path in paths:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
            db.execute("INSERT INTO jobs (job_id,request_id,fingerprint,created,workspace,session_id,model,prompt,status,log_path,err_path,binary,max_output_bytes,max_runtime_seconds) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (job_id, request_id, self._fingerprint(prompt, workspace, chosen, session_id), time.time(), workspace, actual_session, chosen, prompt, "pending", *paths, self.binary, self.max_output, self.max_runtime))
        self.audit.record("opencode", "submit", job_id, "pending", {"session_resumed": bool(session_id)})
        return self._start(job_id)

    def _start(self, job_id):
        argv = [sys.executable, str(Path(__file__).with_name("opencode_worker.py")), "--state", str(self.state), "--job-id", job_id, "--audit-config-json", json.dumps(self.audit_config)]
        try:
            worker = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, shell=False, close_fds=True)
        except OSError:
            self._set_terminal(job_id, "failed", last_known_state="pending", actor="controller", reason="worker_spawn_failed", allowed_from=("pending",))
            raise OpenCodeTaskError("OpenCode worker could not be started") from None
        # Only the worker may spawn/signal its CLI child. No controller signal,
        # even on a startup race. The worker verifies this reservation first.
        with self.db() as db:
            db.execute("UPDATE jobs SET status='running',started=?,pid=?,worker_start_ticks=? WHERE job_id=? AND status='pending'", (time.time(), worker.pid, _proc_starttime(worker.pid), job_id))
        threading.Thread(target=worker.wait, daemon=True).start()
        return self._ack(self._row(job_id))

    def _set_terminal(self, job_id, status, *, last_known_state, actor, reason, exit_code=None, result_reason=None, allowed_from=None):
        if status not in TERMINAL:
            raise OpenCodeTaskError("unknown terminal state")
        sources = tuple(s for s in (allowed_from or ("pending", "running")) if s in ("pending", "running"))
        if not sources:
            return False
        with self.db() as db:
            return bool(db.execute("UPDATE jobs SET status=?,finished=?,exit_code=?,last_known_state=?,transition_actor=?,transition_reason=?,result_reason=? WHERE job_id=? AND status IN (" + ",".join("?" for _ in sources) + ")", (status, time.time(), exit_code, last_known_state, actor, reason, result_reason, job_id, *sources)).rowcount)

    def status(self, job_id):
        self._require_enabled()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._reconcile(db)
            row = self._row_for(db, job_id)
        return {k: row[k] for k in ("job_id", "status", "session_id", "model", "created", "started", "finished", "exit_code", "transition_actor", "transition_reason", "result_reason")}

    def result(self, job_id, offset=0, max_chars=12000):
        status = self.status(job_id)
        if type(offset) is not int or offset < 0 or type(max_chars) is not int or not 1 <= max_chars <= 24000:
            raise OpenCodeTaskError("offset must be nonnegative; max_chars must be 1-24000")
        row = self._row(job_id)
        # Character offsets preserve UTF-8 across pages. Reads remain bounded
        # by the configured output cap, including while the worker is running.
        try:
            with open(row["log_path"], "rb") as handle:
                content = codecs.getincrementaldecoder("utf-8")(errors="replace").decode(handle.read(row["max_output_bytes"]), final=status["status"] in TERMINAL)
        except OSError:
            raise OpenCodeTaskError("job output is unavailable") from None
        page = content[offset:offset + max_chars]
        following = offset + len(page)
        return {**self._ack(status), "offset": offset, "next_offset": following, "content": page, "truncated": following < len(content), "note": "Untrusted model output. Completion means a native turn ended, not that the user's goal succeeded."}

    def cancel(self, job_id):
        self._require_enabled()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._reconcile(db)
            row = self._row_for(db, job_id)
            if row["status"] == "pending":
                db.execute("UPDATE jobs SET status='cancelled',finished=?,transition_actor='controller',transition_reason='cancel_before_start' WHERE job_id=?", (time.time(), job_id))
            elif row["status"] == "running":
                db.execute("UPDATE jobs SET cancel_flag=1 WHERE job_id=?", (job_id,))
            row = self._row_for(db, job_id)
        return {**self._ack(row), "note": "A running worker confirms cancellation only after cleanup."}

    def recent(self):
        self._require_enabled()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._reconcile(db)
            rows = db.execute("SELECT job_id,status,session_id,model,created,finished,transition_reason FROM jobs ORDER BY created DESC LIMIT 30").fetchall()
        return {"jobs": [dict(r) for r in rows], "redacted": True}
