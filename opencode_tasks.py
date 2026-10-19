"""Controller for OpenCode bridge execution jobs (SPEC section 18).

Disabled by default. While disabled, every call fails closed and no process
is ever spawned. The controller mints and stores the session identifier before
spawn, enforces idempotency and admission concurrency (1 globally, 1 per
session), and never signals a stored PID or PGID: a detached durable worker
(opencode_worker.py) owns the CLI process and its terminal record.

Execution boundary: the bridge injects no permission configuration, adds no
sandbox, and never approves a native permission request. Workspace selection
is a current-working-directory allowlist only, not filesystem or network
isolation. Native OpenCode configuration, plugins, and saved permissions
apply unchanged.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import stat as stat_module
import select
import signal
import subprocess
import sys
import time

import opencode_core
from audit import AuditLog
from config_schema import ConfigError, load_bridge_config

SESSION_PATTERN = re.compile(r"^ses_[A-Za-z0-9]{8,64}$")
TERMINAL = ("completed", "failed", "cancelled", "permission_required", "unknown_exit")
ACTIVE = ("pending", "running", "unknown_exit")
MAX_PROMPT_CHARS = (1, 131_072)
MAX_RUNTIME_SECONDS = (30, 14_400)
MAX_OUTPUT_BYTES = (65_536, 8_388_608)


class OpenCodeTaskError(RuntimeError):
    pass


def _canonical_workspace(value: str) -> str:
    return str(Path(value).expanduser().resolve(strict=False))


class OpenCodeTasks:
    """Durable controller for bridge-owned OpenCode task jobs."""

    def __init__(self, config: dict, state: Path):
        if not isinstance(config, dict):
            raise OpenCodeTaskError("opencode configuration must be an object")
        execution = config.get("execution")
        if execution is None:
            execution = {}
        if not isinstance(execution, dict):
            raise OpenCodeTaskError("opencode.execution must be an object")
        self.enabled = bool(execution.get("enabled", False))
        self.binary = str(config.get("binary", ""))
        self.max_prompt = int(execution.get("max_prompt_chars", 32_000))
        self.max_runtime = int(execution.get("max_runtime_seconds", 1_800))
        self.max_output = int(execution.get("max_output_bytes", 524_288))
        if not self.enabled:
            # Fail closed before any validation side effects or filesystem use.
            self.allowed_workspaces: tuple[str, ...] = ()
            self.allowed_models: tuple[str, ...] = ()
            self.state = state
            return
        if not self.binary:
            raise OpenCodeTaskError("opencode.execution requires the section 16 opencode.binary")
        if not 1 <= self.max_prompt <= MAX_PROMPT_CHARS[1]:
            raise OpenCodeTaskError("opencode.execution.max_prompt_chars must be 1-131072")
        if not MAX_RUNTIME_SECONDS[0] <= self.max_runtime <= MAX_RUNTIME_SECONDS[1]:
            raise OpenCodeTaskError("opencode.execution.max_runtime_seconds must be 30-14400")
        if not MAX_OUTPUT_BYTES[0] <= self.max_output <= MAX_OUTPUT_BYTES[1]:
            raise OpenCodeTaskError("opencode.execution.max_output_bytes must be 65536-8388608")
        workspaces = execution.get("allowed_workspaces")
        models = execution.get("allowed_models")
        if not isinstance(workspaces, list) or not workspaces:
            raise OpenCodeTaskError("opencode.execution.allowed_workspaces must be a non-empty list")
        if not isinstance(models, list) or not models:
            raise OpenCodeTaskError("opencode.execution.allowed_models must be a non-empty list")
        canonical_workspaces = []
        for value in workspaces:
            if not isinstance(value, str) or not value:
                raise OpenCodeTaskError("allowed_workspaces entries must be non-empty strings")
            if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
                raise OpenCodeTaskError("allowed_workspaces entries must not contain control characters")
            if not Path(value).expanduser().is_absolute():
                raise OpenCodeTaskError("allowed_workspaces entries must be absolute paths")
            canonical = _canonical_workspace(value)
            if canonical not in canonical_workspaces:
                canonical_workspaces.append(canonical)
        canonical_models = []
        for value in models:
            if not isinstance(value, str) or not value or len(value) > 128:
                raise OpenCodeTaskError("allowed_models entries must be non-empty strings up to 128 characters")
            if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
                raise OpenCodeTaskError("allowed_models entries must not contain control characters")
            if value.count("/") != 1 or not value.split("/")[0] or not value.split("/")[1]:
                raise OpenCodeTaskError("allowed_models entries must use the provider/model form")
            if value not in canonical_models:
                canonical_models.append(value)
        self.allowed_workspaces = tuple(canonical_workspaces)
        self.allowed_models = tuple(canonical_models)
        self.state = state
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.audit_config = config.get("audit")
        self.audit = AuditLog(self.state, self.audit_config)
        self.logs = self.state / "opencode-task-logs"
        self.logs.mkdir(exist_ok=True, mode=0o700)
        self.dbpath = self.state / "opencode-tasks.sqlite3"
        with self.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY, request_id TEXT UNIQUE, fingerprint TEXT NOT NULL,
              created REAL NOT NULL, started REAL, finished REAL,
              workspace TEXT NOT NULL, session_id TEXT NOT NULL, model TEXT NOT NULL,
              prompt TEXT NOT NULL, status TEXT NOT NULL, pid INTEGER, child_pid INTEGER,
              worker_start_ticks INTEGER, child_start_ticks INTEGER,
              exit_code INTEGER, log_path TEXT NOT NULL, err_path TEXT NOT NULL,
              binary TEXT NOT NULL,
              max_output_bytes INTEGER NOT NULL, max_runtime_seconds INTEGER NOT NULL,
              cancel_flag INTEGER NOT NULL DEFAULT 0,
              last_known_state TEXT, last_transition_at REAL,
              transition_actor TEXT, transition_reason TEXT, result_reason TEXT)""")
        self.dbpath.chmod(0o600)

    @classmethod
    def from_config(cls, root: Path):
        try:
            config, warnings = load_bridge_config(root)
        except ConfigError as exc:
            raise OpenCodeTaskError(str(exc)) from exc
        opencode = config.get("opencode", {})
        runner = cls(opencode, root / "state")
        return runner

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.dbpath, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def _row_for(db, job_id):
        return db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()

    def _row(self, job_id):
        with self.db() as db:
            row = self._row_for(db, job_id)
        if row is None:
            raise OpenCodeTaskError("unknown job_id")
        return row

    def _require_enabled(self):
        if not self.enabled:
            raise OpenCodeTaskError(
                "OpenCode task execution is disabled in bridge-config.json; "
                "review docs/SECURITY.md before enabling it")

    def _validate_binary(self):
        path = Path(self.binary)
        try:
            info = path.stat()
        except OSError:
            raise OpenCodeTaskError("opencode.binary is not a regular executable file") from None
        if not stat_module.S_ISREG(info.st_mode) or not os.access(path, os.X_OK):
            raise OpenCodeTaskError("opencode.binary is not a regular executable file")

    def _workspace(self, value: str | None):
        if not isinstance(value, str) or not value:
            raise OpenCodeTaskError("workspace is required")
        canonical = _canonical_workspace(value)
        if canonical not in self.allowed_workspaces:
            raise OpenCodeTaskError("workspace is not in the allowlisted workspaces")
        return canonical

    def _model(self, value: str | None):
        chosen = value if isinstance(value, str) and value else self.allowed_models[0]
        if chosen not in self.allowed_models:
            raise OpenCodeTaskError("model is not in the allowlisted models")
        return chosen

    def _fingerprint(self, prompt: str, workspace: str, model: str, session_id: str) -> str:
        digest = hashlib.sha256()
        for value in (prompt, workspace, model, session_id):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value.encode("utf-8"))
        return digest.hexdigest()

    def submit(self, prompt: str, workspace: str, request_id: str,
               session_id: str | None = None, model: str | None = None) -> dict:
        self._require_enabled()
        if not isinstance(prompt, str) or not prompt or len(prompt) > self.max_prompt:
            raise OpenCodeTaskError(f"prompt must be 1-{self.max_prompt} characters")
        if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", request_id):
            raise OpenCodeTaskError("request_id must be 1-128 characters of [A-Za-z0-9._-]")
        if session_id is not None:
            if not isinstance(session_id, str) or not SESSION_PATTERN.fullmatch(session_id):
                raise OpenCodeTaskError("session_id must match ses_ plus 8-64 alphanumeric characters")
            with self.db() as db:
                owner = db.execute(
                    "SELECT job_id,workspace,model,status FROM jobs WHERE session_id=?",
                    (session_id,)).fetchone()
            if owner is None:
                raise OpenCodeTaskError("session_id does not name a bridge-owned session")
            if owner["status"] in TERMINAL and owner["status"] not in ("completed",):
                raise OpenCodeTaskError("the owning job of this session did not complete")
        workspace = self._workspace(workspace)
        model = self._model(model)
        resume_session = session_id
        if resume_session is None:
            resume_session = "ses_" + secrets.token_hex(16)
        fingerprint = self._fingerprint(prompt, workspace, model, resume_session)
        # Idempotency: same request_id plus same fingerprint replays the
        # original acknowledgement; a different fingerprint is rejected
        # without a second model invocation.
        with self.db() as db:
            existing = db.execute("SELECT * FROM jobs WHERE request_id=?", (request_id,)).fetchone()
            if existing is not None:
                if existing["fingerprint"] != fingerprint:
                    raise OpenCodeTaskError("request_id was already used with different inputs")
                return self._ack(self._row_for(db, existing["job_id"]))
            active = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE status IN ('pending','running','unknown_exit')").fetchone()[0]
            if active:
                raise OpenCodeTaskError("another OpenCode task is active; submission is busy")
            session_active = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE session_id=? AND status IN ('pending','running','unknown_exit')",
                (resume_session,)).fetchone()[0]
            if session_active:
                raise OpenCodeTaskError("another task for this session is active; submission is busy")
            job_id = "oct_" + secrets.token_hex(12)
            log_path = str(self.logs / f"{job_id}.jsonl")
            err_path = str(self.logs / f"{job_id}.stderr")
            db.execute(
                "INSERT INTO jobs (job_id,request_id,fingerprint,created,workspace,session_id,model,"
                "prompt,status,log_path,err_path,binary,max_output_bytes,max_runtime_seconds,cancel_flag) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                (job_id, request_id, fingerprint, time.time(), workspace, resume_session, model,
                 prompt, "pending", log_path, err_path, self.binary, self.max_output, self.max_runtime))
        for path in (log_path, err_path):
            handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(handle)
        self.audit.record("opencode", "submit", job_id, "pending",
                          {"workspace": workspace, "model": model,
                           "session_resumed": bool(session_id)})
        return self._start(job_id)

    def _ack(self, row: sqlite3.Row) -> dict:
        return {"job_id": row["job_id"], "status": row["status"],
                "session_id": row["session_id"], "model": row["model"]}

    def _start(self, job_id: str) -> dict:
        row = self._row(job_id)
        if row["status"] != "pending":
            return self._ack(row)
        self._validate_binary()
        read_fd, write_fd = os.pipe()
        worker_argv = [
            sys.executable, str(Path(__file__).with_name("opencode_worker.py")),
            "--state", str(self.state), "--job-id", job_id, "--ready-fd", str(write_fd),
            "--audit-config-json", json.dumps(self.audit_config, separators=(",", ":")),
        ]
        try:
            worker = subprocess.Popen(
                worker_argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, cwd=self.state, start_new_session=True,
                shell=False, pass_fds=(write_fd,))
        except OSError as exc:
            os.close(read_fd)
            os.close(write_fd)
            raise OpenCodeTaskError("failed to start OpenCode worker") from exc
        finally:
            try:
                os.close(write_fd)
            except OSError:
                pass
        with self.db() as db:
            changed = db.execute(
                "UPDATE jobs SET status='running',started=?,pid=?,worker_start_ticks=? "
                "WHERE job_id=? AND status='pending'",
                (time.time(), worker.pid, _proc_starttime(worker.pid), job_id)).rowcount
        if changed != 1:
            try:
                os.killpg(worker.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            os.close(read_fd)
            raise OpenCodeTaskError("job state changed before start")
        try:
            ready, _, _ = select.select([read_fd], [], [], 5)
            payload = json.loads(os.read(read_fd, 4096).decode("utf-8")) if ready else {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            payload = {}
        finally:
            os.close(read_fd)
        if not payload.get("ok"):
            # The worker never gained the CLI child; the controller kills only
            # its own live worker child (it is this process's direct child, so
            # killpg is legitimate), reaps by handle, and records the failure.
            try:
                opencode_core.OpenCodeRunner._signal_group(worker.pid, signal.SIGTERM)
                state_flag, _ = opencode_core.OpenCodeRunner._observe_leader(
                    worker.pid, time.monotonic() + opencode_core.KILL_GRACE_SECONDS)
                if state_flag != "unknown":
                    opencode_core.OpenCodeRunner._signal_group(worker.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                worker.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            self._set_terminal(job_id, "failed", last_known_state="running", actor="start",
                               reason="worker_not_ready",
                               result_reason="OpenCode worker could not start the CLI",
                               allowed_from=("running",))
            self.audit.record("opencode", "start_failed", job_id, "failed", {})
            raise OpenCodeTaskError("failed to start OpenCode CLI")
        return self._ack(self._row(job_id))

    def _set_terminal(self, job_id, status, *, last_known_state, actor, reason,
                      exit_code=None, result_reason=None, allowed_from=None):
        if status not in TERMINAL:
            raise OpenCodeTaskError("unknown terminal state")
        clauses = ["job_id=?"]
        values: list = [job_id]
        if allowed_from:
            clauses.append("status IN (%s)" % ",".join("?" * len(allowed_from)))
            values.extend(allowed_from)
        with self.db() as db:
            changed = db.execute(
                "UPDATE jobs SET status=?,finished=?,exit_code=?,"
                "last_known_state=?,last_transition_at=?,transition_actor=?,"
                "transition_reason=?,result_reason=? WHERE " + " AND ".join(clauses),
                [status, time.time(), exit_code, last_known_state, time.time(),
                 actor, reason, result_reason] + values).rowcount
        return changed == 1

    def status(self, job_id: str) -> dict:
        self._require_enabled()
        row = self._row(job_id)
        payload = {
            "job_id": row["job_id"], "status": row["status"],
            "session_id": row["session_id"], "model": row["model"],
            "created": row["created"], "started": row["started"], "finished": row["finished"],
            "last_known_state": row["last_known_state"] or row["status"],
            "transition_actor": row["transition_actor"] or "unknown",
            "transition_reason": row["transition_reason"] or "unknown",
            "result_reason": row["result_reason"],
        }
        if row["status"] == "running" and row["started"] and \
                time.time() - row["started"] > row["max_runtime_seconds"]:
            # The worker enforces the deadline independently; this only
            # reports the deadline as passed without signaling anything.
            payload["deadline_passed"] = True
        return payload

    def result(self, job_id: str, offset: int = 0, max_chars: int = 12_000) -> dict:
        self._require_enabled()
        row = self._row(job_id)
        if not isinstance(offset, int) or offset < 0:
            raise OpenCodeTaskError("offset must be a non-negative integer")
        if not isinstance(max_chars, int) or not 1 <= max_chars <= 48_000:
            raise OpenCodeTaskError("max_chars must be 1-48000")
        try:
            with open(row["log_path"], "rb") as handle:
                handle.seek(offset)
                raw = handle.read(max_chars + 1)
        except OSError:
            raise OpenCodeTaskError("job output is not available") from None
        next_offset = offset + min(len(raw), max_chars)
        content = raw[:max_chars].decode("utf-8", errors="replace")
        return {"job_id": job_id, "status": row["status"], "offset": offset,
                "next_offset": next_offset, "content": content,
                "truncated": len(raw) > max_chars,
                "note": ("Model output is untrusted; inspect it directly. The bridge cannot "
                         "infer goal success or permission outcomes from this content.")}

    def cancel(self, job_id: str) -> dict:
        self._require_enabled()
        row = self._row(job_id)
        if row["status"] in TERMINAL:
            return {"job_id": job_id, "status": row["status"],
                    "note": "job already reached a terminal state"}
        if row["status"] == "pending":
            changed = self._set_terminal(job_id, "cancelled", last_known_state="pending",
                                         actor="controller", reason="cancel_requested",
                                         result_reason="Cancelled before the worker started",
                                         allowed_from=("pending",))
            if changed:
                self.audit.record("opencode", "cancel", job_id, "cancelled", {})
                return {"job_id": job_id, "status": "cancelled"}
        with self.db() as db:
            db.execute("UPDATE jobs SET cancel_flag=1 WHERE job_id=? AND status='running'",
                       (job_id,))
        self.audit.record("opencode", "cancel", job_id, "requested", {})
        return {"job_id": job_id, "status": row["status"],
                "note": "cancellation was requested; the worker confirms cleanup"}

    def recent(self) -> dict:
        self._require_enabled()
        with self.db() as db:
            rows = db.execute(
                "SELECT job_id,status,session_id,model,created,finished,transition_reason,result_reason "
                "FROM jobs ORDER BY created DESC LIMIT 30").fetchall()
        return {"jobs": [{key: row[key] for key in row.keys()} for row in rows],
                "redacted": True}


def _proc_starttime(pid: int) -> int | None:
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
        close = text.rfind(")")
        fields = text[close + 2:].split()
        if len(fields) <= 19:
            return None
        return int(fields[19])
    except (OSError, ValueError, IndexError):
        return None
