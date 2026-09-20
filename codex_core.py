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
import time
import uuid

from audit import AuditLog


class CodexError(RuntimeError):
    pass


class CodexRunner:
    MODES = {"read-only", "workspace-write"}
    TERMINAL = {"completed", "failed", "cancelled", "denied", "expired", "timed_out"}

    def __init__(self, config: dict, state: Path):
        self.binary = str(config.get("binary", "codex"))
        self.policies = self._policies(config)
        self.roots = [policy["root"] for policy in self.policies]
        self.max_prompt = int(config.get("max_prompt_chars", 32000))
        self.max_runtime = int(config.get("max_runtime_seconds", 1800))
        self.approval_ttl = int(config.get("approval_ttl_seconds", 3600))
        if not 60 <= self.approval_ttl <= 86400:
            raise CodexError("codex.approval_ttl_seconds must be 60-86400")
        self._children = {}
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
              policy_root TEXT, approval_expires REAL)""")
            existing = {row[1] for row in db.execute("PRAGMA table_info(jobs)")}
            for name, definition in (("policy_root", "TEXT"), ("approval_expires", "REAL")):
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
        config = json.loads((root / "bridge-config.json").read_text())
        return cls(config.get("codex", {}), root / "state")

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
            if not isinstance(max_prompt, int) or not 1 <= max_prompt <= 32000:
                raise CodexError("workspace max_prompt_chars must be 1-32000")
            if not isinstance(max_runtime, int) or not 1 <= max_runtime <= 86400:
                raise CodexError("workspace max_runtime_seconds must be 1-86400")
            if not isinstance(concurrency, int) or not 1 <= concurrency <= 8:
                raise CodexError("workspace max_concurrency must be 1-8")
            if (not isinstance(patterns, list) or any(not isinstance(value, str) or not 1 <= len(value) <= 128
                                                      for value in patterns)):
                raise CodexError("workspace deny_prompt_patterns must contain strings of 1-128 characters")
            policies.append({"root": root, "modes": set(modes), "max_prompt_chars": max_prompt,
                             "max_runtime_seconds": max_runtime, "max_concurrency": concurrency,
                             "deny_prompt_patterns": tuple(value.casefold() for value in patterns)})
        return policies

    def _workspace(self, value: str) -> Path:
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
                                        "deny_prompt_patterns": len(policy["deny_prompt_patterns"])} for policy in self.policies],
                "approval_ttl_seconds": self.approval_ttl,
                "write_approval": "local interactive approval required",
                "network": "governed by the Codex sandbox; bridge grants no extra network access"}

    def diagnostics(self):
        try:
            codex = self.health()
        except CodexError as exc:
            codex = {"ok": False, "error": str(exc)}
        return {"codex": codex, "audit": self.audit.status(),
                "state": {"directory": str(self.state), "mode": oct(self.state.stat().st_mode & 0o777)}}

    def submit(self, prompt: str, workspace: str, mode: str = "read-only"):
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
        with self.db() as db:
            active = db.execute("SELECT COUNT(*) FROM jobs WHERE policy_root=? AND status IN ('queued','running')",
                                (str(policy["root"]),)).fetchone()[0]
        if active >= policy["max_concurrency"]:
            raise CodexError("workspace policy concurrency limit is reached")
        job_id = "codex_" + uuid.uuid4().hex
        log = self.logs / f"{job_id}.jsonl"
        status = "pending_local_approval" if mode == "workspace-write" else "queued"
        expires = time.time() + self.approval_ttl if mode == "workspace-write" else None
        with self.db() as db:
            db.execute("INSERT INTO jobs(job_id,created,workspace,mode,prompt,status,log_path,policy_root,approval_expires) VALUES(?,?,?,?,?,?,?,?,?)",
                       (job_id, time.time(), str(work), mode, prompt, status, str(log), str(policy["root"]), expires))
        self.audit.record("codex", "submit", job_id, status,
                          {"workspace": str(work), "policy_root": str(policy["root"]), "mode": mode, "prompt_chars": len(prompt)})
        if mode == "read-only":
            self._start(job_id)
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
        argv = [self.binary, "exec", "--json", "--sandbox", row["mode"],
                "-C", row["workspace"], "-"]
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
                          {"workspace": row["workspace"], "policy_root": row["policy_root"], "mode": row["mode"]})
        return {"job_id": job_id, "status": "running", "pid": proc.pid}

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
        with self.db() as db:
            db.execute("UPDATE jobs SET status='denied',finished=? WHERE job_id=?", (time.time(), job_id))
        self.audit.record("codex", "deny", job_id, "denied", {"mode": row["mode"]})
        return {"job_id": job_id, "status": "denied"}

    def _expire_pending(self, row):
        if row["status"] == "pending_local_approval" and row["approval_expires"] is not None and row["approval_expires"] <= time.time():
            with self.db() as db:
                db.execute("UPDATE jobs SET status='expired',finished=? WHERE job_id=?", (time.time(), row["job_id"]))
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
            if time.time() - row["started"] > self.max_runtime:
                self.cancel(job_id, final_status="timed_out")
                status = "timed_out"
            else:
                child = self._children.get(job_id)
                recovered_after_restart = child is None
                exit_code = child.poll() if child else None
                ended = exit_code is not None or not self._alive(row["pid"])
                if not ended:
                    return {"job_id": job_id, "status": status, "workspace": row["workspace"],
                            "mode": row["mode"], "created": row["created"], "started": row["started"],
                            "exit_code": None, "recovered_after_restart": recovered_after_restart}
                self._children.pop(job_id, None)
                status = "completed" if exit_code in (0, None) else "failed"
                with self.db() as db:
                    db.execute("UPDATE jobs SET status=?,finished=?,exit_code=? WHERE job_id=?",
                               (status, time.time(), exit_code, job_id))
                self.audit.record("codex", "finish", job_id, status,
                                  {"exit_code": exit_code, "recovered_after_restart": child is None})
        return {"job_id": job_id, "status": status, "workspace": row["workspace"],
                "mode": row["mode"], "created": row["created"], "started": row["started"],
                "exit_code": exit_code, "recovered_after_restart": recovered_after_restart,
                "approval": ({"required": True, "expires_at": row["approval_expires"], "policy_root": row["policy_root"]}
                             if status == "pending_local_approval" else None)}

    def result(self, job_id, offset=0, max_chars=12000):
        if offset < 0 or not 1 <= max_chars <= 24000:
            raise CodexError("invalid result page")
        row = self._row(job_id)
        path = Path(row["log_path"])
        data = path.read_text(errors="replace") if path.exists() else ""
        end = min(len(data), offset + max_chars)
        return {**self.status(job_id), "output": data[offset:end], "total_chars": len(data),
                "next_offset": end if end < len(data) else None}

    def cancel(self, job_id, final_status="cancelled"):
        row = self._expire_pending(self._row(job_id))
        if row["status"] == "pending_local_approval":
            return self.deny_local(job_id)
        if row["status"] != "running" or not row["pid"]:
            return {"job_id": job_id, "status": row["status"]}
        if self._alive(row["pid"]):
            try:
                os.killpg(row["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass
        child = self._children.pop(job_id, None)
        if child:
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
        with self.db() as db:
            db.execute("UPDATE jobs SET status=?,finished=? WHERE job_id=?",
                       (final_status, time.time(), job_id))
        self.audit.record("codex", "cancel", job_id, final_status, {"mode": row["mode"]})
        return {"job_id": job_id, "status": final_status}

    def recent(self):
        with self.db() as db:
            rows = db.execute("SELECT job_id,created,workspace,mode,status,policy_root,approval_expires FROM jobs ORDER BY created DESC LIMIT 30").fetchall()
        return {"jobs": [dict(x) for x in rows]}
