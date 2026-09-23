"""Permission-gated Codex CLI runner for WSL2."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import uuid

from audit import AuditLog
from config_schema import ConfigError, load_bridge_config


class CodexError(RuntimeError):
    pass


class CodexRunner:
    MODES = {"read-only", "workspace-write"}
    TERMINAL = {"completed", "failed", "cancelled", "denied", "expired", "timed_out", "unknown_exit"}
    REASONING_EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}

    def __init__(self, config: dict, state: Path):
        self.binary = str(config.get("binary", "codex"))
        self.policies = self._policies(config)
        self.roots = [policy["root"] for policy in self.policies]
        self.max_prompt = int(config.get("max_prompt_chars", 32000))
        self.max_runtime = int(config.get("max_runtime_seconds", 1800))
        self.approval_ttl = int(config.get("approval_ttl_seconds", 3600))
        self.watchdog_interval = int(config.get("watchdog_interval_seconds", 15))
        if not 60 <= self.approval_ttl <= 86400:
            raise CodexError("codex.approval_ttl_seconds must be 60-86400")
        if not 5 <= self.watchdog_interval <= 300:
            raise CodexError("codex.watchdog_interval_seconds must be 5-300")
        self._children = {}
        self._watchdog_lock = threading.Lock()
        self._watchdog_stop = threading.Event()
        self._watchdog_thread = None
        self.state = Path(state)
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.audit = AuditLog(self.state, config.get("audit"))
        self.logs = self.state / "codex-logs"
        self.logs.mkdir(exist_ok=True, mode=0o700)
        self.dbpath = self.state / "codex.sqlite3"
        with self.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY, created REAL NOT NULL, started REAL,
              finished REAL, workspace TEXT NOT NULL, mode TEXT NOT NULL,
              prompt TEXT NOT NULL, status TEXT NOT NULL, pid INTEGER,
              exit_code INTEGER, log_path TEXT NOT NULL,
              policy_root TEXT, approval_expires REAL,
              model TEXT, reasoning_effort TEXT)""")
            existing = {row[1] for row in db.execute("PRAGMA table_info(jobs)")}
            for name, definition in (("policy_root", "TEXT"), ("approval_expires", "REAL"),
                                     ("model", "TEXT"), ("reasoning_effort", "TEXT"),
                                     ("last_known_state", "TEXT"), ("last_transition_at", "REAL"),
                                     ("transition_actor", "TEXT"), ("transition_reason", "TEXT"),
                                     ("exit_signal", "INTEGER"), ("result_reason", "TEXT")):
                if name not in existing:
                    db.execute(f"ALTER TABLE jobs ADD COLUMN {name} {definition}")
        self.dbpath.chmod(0o600)

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.dbpath, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @classmethod
    def from_config(cls, root: Path):
        try:
            config, warnings = load_bridge_config(root)
        except ConfigError as exc:
            raise CodexError(str(exc)) from exc
        runner = cls(config.get("codex", {}), root / "state")
        runner.config_warnings = warnings
        return runner

    @classmethod
    def _policies(cls, config: dict):
        raw = config.get("workspaces")
        if raw is None:
            raw = [{"path": path} for path in config.get("allowed_workspaces", [])]
        if not isinstance(raw, list):
            raise CodexError("codex.workspaces must be a list")
        policies = []
        for entry in raw:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                raise CodexError("each codex workspace policy needs a path")
            root = Path(entry["path"]).expanduser().resolve()
            modes = entry.get("modes", sorted(cls.MODES))
            if not isinstance(modes, list) or not modes or set(modes) - cls.MODES:
                raise CodexError("workspace modes must be read-only and/or workspace-write")
            max_prompt = entry.get("max_prompt_chars", config.get("max_prompt_chars", 32000))
            max_runtime = entry.get("max_runtime_seconds", config.get("max_runtime_seconds", 1800))
            concurrency = entry.get("max_concurrency", 1)
            patterns = entry.get("deny_prompt_patterns", [])
            models = entry.get("allowed_models", config.get("allowed_models", []))
            efforts = entry.get("allowed_reasoning_efforts", config.get("allowed_reasoning_efforts", []))
            if not isinstance(max_prompt, int) or not 1 <= max_prompt <= 32000:
                raise CodexError("workspace max_prompt_chars must be 1-32000")
            if not isinstance(max_runtime, int) or not 1 <= max_runtime <= 86400:
                raise CodexError("workspace max_runtime_seconds must be 1-86400")
            if not isinstance(concurrency, int) or not 1 <= concurrency <= 8:
                raise CodexError("workspace max_concurrency must be 1-8")
            if (not isinstance(patterns, list) or any(not isinstance(value, str) or not 1 <= len(value) <= 128
                                                      for value in patterns)):
                raise CodexError("workspace deny_prompt_patterns must contain strings of 1-128 characters")
            if (not isinstance(models, list) or any(not isinstance(value, str) or not value or len(value) > 128
                                                    for value in models)):
                raise CodexError("workspace allowed_models must contain non-empty strings up to 128 characters")
            if (not isinstance(efforts, list) or set(efforts) - cls.REASONING_EFFORTS):
                raise CodexError("workspace allowed_reasoning_efforts contains an unsupported value")
            policies.append({"root": root, "modes": set(modes), "max_prompt_chars": max_prompt,
                             "max_runtime_seconds": max_runtime, "max_concurrency": concurrency,
                             "deny_prompt_patterns": tuple(value.casefold() for value in patterns),
                             "allowed_models": tuple(models),
                             "allowed_reasoning_efforts": tuple(efforts)})
        return policies

    def _workspace(self, value: str) -> tuple[Path, dict]:
        if not isinstance(value, str) or not value:
            raise CodexError("workspace is required")
        try:
            path = Path(value).expanduser().resolve(strict=True)
        except OSError as exc:
            raise CodexError("workspace does not exist or cannot be resolved") from exc
        if not path.is_dir():
            raise CodexError("workspace must be an existing directory")
        matches = [policy for policy in self.policies if path == policy["root"] or policy["root"] in path.parents]
        if not matches:
            raise CodexError("workspace is outside allowed_workspaces")
        return path, max(matches, key=lambda policy: len(policy["root"].parts))

    def health(self):
        if not self.roots:
            raise CodexError("codex.allowed_workspaces is empty")
        try:
            probe = subprocess.run([self.binary, "--version"], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, timeout=10, shell=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise CodexError("Codex CLI version probe failed") from exc
        if probe.returncode:
            raise CodexError("Codex CLI version probe failed")
        return {"ok": True, "version": probe.stdout.strip()[:300],
                "allowed_workspaces": [str(p) for p in self.roots],
                "modes": sorted(self.MODES),
                "workspace_policies": [{"path": str(policy["root"]), "modes": sorted(policy["modes"]),
                                        "max_prompt_chars": policy["max_prompt_chars"],
                                        "max_runtime_seconds": policy["max_runtime_seconds"],
                                        "max_concurrency": policy["max_concurrency"],
                                        "deny_prompt_patterns": len(policy["deny_prompt_patterns"]),
                                        "allowed_models": list(policy["allowed_models"]),
                                        "allowed_reasoning_efforts": list(policy["allowed_reasoning_efforts"])} for policy in self.policies],
                "approval_ttl_seconds": self.approval_ttl,
                "watchdog_interval_seconds": self.watchdog_interval,
                "watchdog": {"running": bool(self._watchdog_thread and self._watchdog_thread.is_alive())},
                "write_approval": "local interactive approval required",
                "network": "governed by the Codex sandbox; bridge grants no extra network access"}

    def diagnostics(self):
        try:
            codex = self.health()
        except CodexError as exc:
            codex = {"ok": False, "error": str(exc)}
        return {"codex": codex, "config_warnings": getattr(self, "config_warnings", []), "audit": self.audit.status(),
                "state": {"directory": str(self.state), "mode": oct(self.state.stat().st_mode & 0o777)}}

    def local_status(self):
        """Fast local heartbeat; does not invoke the Codex CLI."""
        with self.db() as db:
            jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        return {"ok": True, "upstream_checked": False, "registered_jobs": jobs,
                "watchdog": {"running": bool(self._watchdog_thread and self._watchdog_thread.is_alive()),
                             "interval_seconds": self.watchdog_interval},
                "audit": self.audit.status(),
                "state": {"directory": str(self.state), "mode": oct(self.state.stat().st_mode & 0o777)}}

    def start_watchdog(self):
        """Start the persistent-server timeout watchdog exactly once."""
        with self._watchdog_lock:
            if self._watchdog_thread and self._watchdog_thread.is_alive():
                return False
            self._watchdog_stop.clear()
            self._watchdog_thread = threading.Thread(target=self._watchdog_loop,
                                                     name="codex-timeout-watchdog", daemon=True)
            self._watchdog_thread.start()
            return True

    def _watchdog_loop(self):
        while not self._watchdog_stop.wait(self.watchdog_interval):
            try:
                self.enforce_timeouts()
            except (CodexError, OSError, sqlite3.Error):
                self.audit.record("codex", "watchdog_error", "watchdog", "error", {})

    def _policy_for_row(self, row):
        return next((policy for policy in self.policies if str(policy["root"]) == row["policy_root"]), None)

    def _runtime_for_row(self, row):
        policy = self._policy_for_row(row)
        return policy["max_runtime_seconds"] if policy else self.max_runtime

    def enforce_timeouts(self):
        """Enforce policy runtime independently of caller polling."""
        now = time.time()
        with self.db() as db:
            rows = db.execute("SELECT * FROM jobs WHERE status='running' AND started IS NOT NULL").fetchall()
        outcomes = []
        for row in rows:
            if now - row["started"] > self._runtime_for_row(row):
                outcomes.append(self.cancel(row["job_id"], final_status="timed_out"))
        return {"checked": len(rows), "outcomes": outcomes}

    def submit(self, prompt: str, workspace: str, mode: str = "read-only",
               model: str | None = None, reasoning_effort: str | None = None):
        if mode not in self.MODES:
            raise CodexError("mode must be read-only or workspace-write")
        if not isinstance(prompt, str) or not prompt.strip():
            raise CodexError("prompt must be non-empty")
        work, policy = self._workspace(workspace)
        if mode not in policy["modes"]:
            raise CodexError("workspace policy does not allow this sandbox mode")
        if len(prompt) > policy["max_prompt_chars"]:
            raise CodexError(f"prompt exceeds workspace limit of {policy['max_prompt_chars']} characters")
        if any(pattern in prompt.casefold() for pattern in policy["deny_prompt_patterns"]):
            raise CodexError("workspace policy blocked this prompt pattern")
        if model is not None:
            if not isinstance(model, str) or model not in policy["allowed_models"]:
                raise CodexError("requested model is not allowed by this workspace policy")
        if reasoning_effort is not None:
            if (not isinstance(reasoning_effort, str)
                    or reasoning_effort not in policy["allowed_reasoning_efforts"]):
                raise CodexError("requested reasoning_effort is not allowed by this workspace policy")
        job_id = "codex_" + uuid.uuid4().hex
        log = self.logs / f"{job_id}.jsonl"
        status = "pending_local_approval" if mode == "workspace-write" else "queued"
        expires = time.time() + self.approval_ttl if mode == "workspace-write" else None
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            active = db.execute("SELECT COUNT(*) FROM jobs WHERE policy_root=? AND status IN ('queued','running')",
                                (str(policy["root"]),)).fetchone()[0]
            if active >= policy["max_concurrency"]:
                raise CodexError("workspace policy concurrency limit is reached")
            db.execute("INSERT INTO jobs(job_id,created,workspace,mode,prompt,status,log_path,policy_root,approval_expires,model,reasoning_effort) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       (job_id, time.time(), str(work), mode, prompt, status, str(log), str(policy["root"]), expires,
                        model, reasoning_effort))
        self.audit.record("codex", "submit", job_id, status,
                          {"workspace": str(work), "policy_root": str(policy["root"]), "mode": mode,
                           "prompt_chars": len(prompt), "model": model, "reasoning_effort": reasoning_effort})
        if mode == "read-only":
            try:
                self._start(job_id)
            except CodexError:
                self._mark_start_failed(job_id)
                raise
            status = "running"
        return {"job_id": job_id, "status": status,
                "approval": {"expires_at": expires, "policy_root": str(policy["root"])} if expires else None,
                "next": ("Approve locally with ./bridge.sh codex-approve " + job_id
                         if mode == "workspace-write" else "Poll codex_task_status")}

    def _row(self, job_id):
        if not isinstance(job_id, str) or not job_id.startswith("codex_") or len(job_id) != 38:
            raise CodexError("invalid Codex job ID")
        with self.db() as db:
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if not row:
            raise CodexError("unknown Codex job ID")
        return row

    def _start(self, job_id):
        row = self._row(job_id)
        if row["status"] not in ("queued", "pending_local_approval"):
            raise CodexError("job is not startable")
        argv = [self.binary, "exec", "--json", "--sandbox", row["mode"], "-C", row["workspace"]]
        if row["model"]:
            argv.extend(["--model", row["model"]])
        if row["reasoning_effort"]:
            argv.extend(["-c", "model_reasoning_effort=" + row["reasoning_effort"]])
        argv.append("-")
        with open(row["log_path"], "ab", buffering=0) as log:
            try:
                proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=log,
                                        stderr=subprocess.STDOUT, cwd=row["workspace"],
                                        start_new_session=True, shell=False)
                proc.stdin.write(row["prompt"].encode("utf-8"))
                proc.stdin.close()
            except OSError as exc:
                raise CodexError("failed to start Codex CLI") from exc
        with self.db() as db:
            changed = db.execute("UPDATE jobs SET status='running',started=?,pid=? WHERE job_id=? AND status=?",
                                 (time.time(), proc.pid, job_id, row["status"])).rowcount
        if changed != 1:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            raise CodexError("job state changed before start")
        self._children[job_id] = proc
        self.audit.record("codex", "start", job_id, "running",
                          {"workspace": row["workspace"], "policy_root": row["policy_root"], "mode": row["mode"],
                           "model": row["model"], "reasoning_effort": row["reasoning_effort"]})
        return {"job_id": job_id, "status": "running", "pid": proc.pid}

    def _set_terminal(self, job_id, status, *, last_known_state, actor, reason,
                      exit_code=None, exit_signal=None, result_reason=None,
                      allowed_from=None):
        if status not in self.TERMINAL:
            raise CodexError("terminal status is required")
        clauses = ["job_id=?"]
        values = [status, time.time(), exit_code, exit_signal, last_known_state,
                  actor, reason, result_reason, job_id]
        if allowed_from:
            placeholders = ",".join("?" for _ in allowed_from)
            clauses.append(f"status IN ({placeholders})")
            values.extend(allowed_from)
        with self.db() as db:
            return db.execute(
                "UPDATE jobs SET status=?,finished=?,exit_code=?,exit_signal=?,"
                "last_known_state=?,last_transition_at=finished,transition_actor=?,"
                "transition_reason=?,result_reason=? WHERE " + " AND ".join(clauses),
                values).rowcount

    @staticmethod
    def _terminal_record(row):
        return {
            "last_known_state": row["last_known_state"] or row["status"],
            "transitioned_at": row["last_transition_at"] or row["finished"],
            "transition_actor": row["transition_actor"] or "unknown",
            "transition_reason": row["transition_reason"] or "unknown",
            "exit_signal": row["exit_signal"],
            "result_reason": row["result_reason"],
        }

    def _mark_start_failed(self, job_id):
        if self._set_terminal(job_id, "failed", last_known_state="queued",
                              actor="start", reason="failed_to_spawn",
                              result_reason="Codex CLI process could not be started",
                              allowed_from=("queued", "pending_local_approval")):
            self.audit.record("codex", "start_failed", job_id, "failed", {})

    def approval_preview(self, job_id):
        row = self._expire_pending(self._row(job_id))
        return {key: row[key] for key in ("job_id", "workspace", "mode", "model", "reasoning_effort", "prompt")}

    def approve_local(self, job_id):
        row = self._row(job_id)
        row = self._expire_pending(row)
        if row["status"] != "pending_local_approval" or row["mode"] != "workspace-write":
            raise CodexError("job is not waiting for local write approval")
        self.audit.record("codex", "approve", job_id, "accepted", {"mode": row["mode"]})
        return self._start(job_id)

    def deny_local(self, job_id):
        row = self._row(job_id)
        row = self._expire_pending(row)
        if row["status"] != "pending_local_approval":
            raise CodexError("job is not waiting for approval")
        self._set_terminal(job_id, "denied", last_known_state="pending_local_approval",
                           actor="local_operator", reason="approval_denied",
                           result_reason="Local operator denied the write approval",
                           allowed_from=("pending_local_approval",))
        self.audit.record("codex", "deny", job_id, "denied", {"mode": row["mode"]})
        return {"job_id": job_id, "status": "denied"}

    def _expire_pending(self, row):
        if row["status"] == "pending_local_approval" and row["approval_expires"] is not None and row["approval_expires"] <= time.time():
            self._set_terminal(row["job_id"], "expired", last_known_state="pending_local_approval",
                               actor="watchdog", reason="approval_expired",
                               result_reason="Local write approval expired",
                               allowed_from=("pending_local_approval",))
            self.audit.record("codex", "approval_expired", row["job_id"], "expired",
                              {"workspace": row["workspace"], "policy_root": row["policy_root"]})
            return self._row(row["job_id"])
        return row

    @staticmethod
    def _alive(pid):
        try:
            if Path(f"/proc/{pid}/stat").read_text().split()[2] == "Z":
                return False
        except (OSError, IndexError):
            pass
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def status(self, job_id):
        row = self._expire_pending(self._row(job_id))
        status = row["status"]
        exit_code = row["exit_code"]
        recovered_after_restart = False
        if status == "running":
            if time.time() - row["started"] > self._runtime_for_row(row):
                self.cancel(job_id, final_status="timed_out")
                row = self._row(job_id)
                status = row["status"]
                if status == "running":
                    return {"job_id": job_id, "status": status, "workspace": row["workspace"],
                            "mode": row["mode"], "created": row["created"], "started": row["started"],
                            "exit_code": None, "recovered_after_restart": False,
                            "timeout_enforcement_pending": True, "model": row["model"],
                            "reasoning_effort": row["reasoning_effort"]}
            else:
                child = self._children.get(job_id)
                recovered_after_restart = child is None
                # A live Popen handle is authoritative. A child can become a
                # zombie between poll() and a /proc/PID check; recording that
                # race as unknown_exit loses its real exit status.
                exit_code = child.poll() if child else None
                ended = exit_code is not None if child else not self._alive(row["pid"])
                if not ended:
                    return {"job_id": job_id, "status": status, "workspace": row["workspace"],
                            "mode": row["mode"], "created": row["created"], "started": row["started"],
                            "exit_code": None, "recovered_after_restart": recovered_after_restart,
                            "model": row["model"], "reasoning_effort": row["reasoning_effort"]}
                self._children.pop(job_id, None)
                status = "completed" if exit_code == 0 else "failed" if exit_code is not None else "unknown_exit"
                if exit_code is None:
                    actor = "recovery" if recovered_after_restart else "status_poll"
                    reason = ("process_not_alive_after_bridge_restart" if recovered_after_restart
                              else "process_ended_without_exit_status")
                    result_reason = "Codex process exit status was unavailable"
                else:
                    actor = "status_poll"
                    reason = "process_exit_observed"
                    result_reason = None if exit_code == 0 else "Codex CLI exited with a non-zero status"
                self._set_terminal(job_id, status, last_known_state="running", actor=actor,
                                   reason=reason, exit_code=exit_code,
                                   result_reason=result_reason, allowed_from=("running",))
                row = self._row(job_id)
                status = row["status"]
                exit_code = row["exit_code"]
                self.audit.record("codex", "finish", job_id, status,
                                  {"exit_code": exit_code, "recovered_after_restart": recovered_after_restart,
                                   "transition_actor": actor, "transition_reason": reason})
        return {"job_id": job_id, "status": status, "workspace": row["workspace"],
                "mode": row["mode"], "created": row["created"], "started": row["started"],
                "exit_code": exit_code, "recovered_after_restart": recovered_after_restart,
                "model": row["model"], "reasoning_effort": row["reasoning_effort"],
                "terminal": self._terminal_record(row) if status in self.TERMINAL else None,
                "approval": ({"required": True, "expires_at": row["approval_expires"], "policy_root": row["policy_root"]}
                             if status == "pending_local_approval" else None)}

    def result(self, job_id, offset=0, max_chars=12000):
        if (isinstance(offset, bool) or not isinstance(offset, int) or offset < 0
                or isinstance(max_chars, bool) or not isinstance(max_chars, int)
                or not 1 <= max_chars <= 24000):
            raise CodexError("invalid result page: offset must be a non-negative integer and max_chars must be 1-24000")
        row = self._row(job_id)
        path = Path(row["log_path"])
        data = path.read_text(errors="replace") if path.exists() else ""
        end = min(len(data), offset + max_chars)
        return {**self.status(job_id), "output": data[offset:end], "total_chars": len(data),
                "next_offset": end if end < len(data) else None}

    def _terminate(self, pid, child):
        if self._alive(pid):
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 2
        while self._alive(pid) and time.monotonic() < deadline:
            if child:
                child.poll()
            time.sleep(0.05)
        if self._alive(pid):
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 2
            while self._alive(pid) and time.monotonic() < deadline:
                if child:
                    child.poll()
                time.sleep(0.05)
        return not self._alive(pid)

    def cancel(self, job_id, final_status="cancelled"):
        row = self._expire_pending(self._row(job_id))
        if row["status"] == "pending_local_approval":
            return self.deny_local(job_id)
        if row["status"] != "running" or not row["pid"]:
            return {"job_id": job_id, "status": row["status"]}
        child = self._children.get(job_id)
        if not self._terminate(row["pid"], child):
            self.audit.record("codex", "cancel_pending", job_id, "running", {"mode": row["mode"]})
            return {"job_id": job_id, "status": "running", "cancellation_pending": True}
        actor = "watchdog" if final_status == "timed_out" else "local_operator"
        reason = "runtime_limit_exceeded" if final_status == "timed_out" else "cancellation_requested"
        result_reason = ("Workspace runtime limit was exceeded" if final_status == "timed_out"
                         else "Codex job was cancelled by the local operator")
        changed = self._set_terminal(job_id, final_status, last_known_state="running",
                                     actor=actor, reason=reason, result_reason=result_reason,
                                     allowed_from=("running",))
        if not changed:
            return {"job_id": job_id, "status": self._row(job_id)["status"]}
        self._children.pop(job_id, None)
        self.audit.record("codex", "cancel", job_id, final_status, {"mode": row["mode"]})
        return {"job_id": job_id, "status": final_status}

    def recent(self):
        with self.db() as db:
            rows = db.execute("SELECT job_id,created,workspace,mode,status,policy_root,approval_expires,model,reasoning_effort FROM jobs ORDER BY created DESC LIMIT 30").fetchall()
        return {"jobs": [dict(x) for x in rows]}
