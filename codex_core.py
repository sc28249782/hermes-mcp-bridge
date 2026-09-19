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


class CodexError(RuntimeError):
    pass


class CodexRunner:
    MODES = {"read-only", "workspace-write"}
    TERMINAL = {"completed", "failed", "cancelled", "denied", "timed_out"}

    def __init__(self, config: dict, state: Path):
        self.binary = str(config.get("binary", "codex"))
        self.roots = [Path(p).expanduser().resolve() for p in config.get("allowed_workspaces", [])]
        self.max_prompt = int(config.get("max_prompt_chars", 32000))
        self.max_runtime = int(config.get("max_runtime_seconds", 1800))
        self._children = {}
        self.state = Path(state)
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.logs = self.state / "codex-logs"
        self.logs.mkdir(exist_ok=True, mode=0o700)
        self.dbpath = self.state / "codex.sqlite3"
        with self.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY, created REAL NOT NULL, started REAL,
              finished REAL, workspace TEXT NOT NULL, mode TEXT NOT NULL,
              prompt TEXT NOT NULL, status TEXT NOT NULL, pid INTEGER,
              exit_code INTEGER, log_path TEXT NOT NULL)""")
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

    def _workspace(self, value: str) -> Path:
        if not isinstance(value, str) or not value:
            raise CodexError("workspace is required")
        try:
            path = Path(value).expanduser().resolve(strict=True)
        except OSError as exc:
            raise CodexError("workspace does not exist or cannot be resolved") from exc
        if not path.is_dir():
            raise CodexError("workspace must be an existing directory")
        if not any(path == root or root in path.parents for root in self.roots):
            raise CodexError("workspace is outside allowed_workspaces")
        return path

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
                "write_approval": "local interactive approval required",
                "network": "governed by the Codex sandbox; bridge grants no extra network access"}

    def submit(self, prompt: str, workspace: str, mode: str = "read-only"):
        if mode not in self.MODES:
            raise CodexError("mode must be read-only or workspace-write")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > self.max_prompt:
            raise CodexError(f"prompt must be 1-{self.max_prompt} characters")
        work = self._workspace(workspace)
        job_id = "codex_" + uuid.uuid4().hex
        log = self.logs / f"{job_id}.jsonl"
        status = "pending_local_approval" if mode == "workspace-write" else "queued"
        with self.db() as db:
            db.execute("INSERT INTO jobs(job_id,created,workspace,mode,prompt,status,log_path) VALUES(?,?,?,?,?,?,?)",
                       (job_id, time.time(), str(work), mode, prompt, status, str(log)))
        if mode == "read-only":
            self._start(job_id)
            status = "running"
        return {"job_id": job_id, "status": status,
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
        return {"job_id": job_id, "status": "running", "pid": proc.pid}

    def approve_local(self, job_id):
        row = self._row(job_id)
        if row["status"] != "pending_local_approval" or row["mode"] != "workspace-write":
            raise CodexError("job is not waiting for local write approval")
        return self._start(job_id)

    def deny_local(self, job_id):
        row = self._row(job_id)
        if row["status"] != "pending_local_approval":
            raise CodexError("job is not waiting for approval")
        with self.db() as db:
            db.execute("UPDATE jobs SET status='denied',finished=? WHERE job_id=?", (time.time(), job_id))
        return {"job_id": job_id, "status": "denied"}

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
        row = self._row(job_id)
        status = row["status"]
        exit_code = row["exit_code"]
        if status == "running":
            if time.time() - row["started"] > self.max_runtime:
                self.cancel(job_id, final_status="timed_out")
                status = "timed_out"
            else:
                child = self._children.get(job_id)
                exit_code = child.poll() if child else None
                ended = exit_code is not None or not self._alive(row["pid"])
                if not ended:
                    return {"job_id": job_id, "status": status, "workspace": row["workspace"],
                            "mode": row["mode"], "created": row["created"], "started": row["started"],
                            "exit_code": None}
                self._children.pop(job_id, None)
                status = "completed" if exit_code in (0, None) else "failed"
                with self.db() as db:
                    db.execute("UPDATE jobs SET status=?,finished=?,exit_code=? WHERE job_id=?",
                               (status, time.time(), exit_code, job_id))
        return {"job_id": job_id, "status": status, "workspace": row["workspace"],
                "mode": row["mode"], "created": row["created"], "started": row["started"],
                "exit_code": exit_code}

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
        row = self._row(job_id)
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
        return {"job_id": job_id, "status": final_status}

    def recent(self):
        with self.db() as db:
            rows = db.execute("SELECT job_id,created,workspace,mode,status FROM jobs ORDER BY created DESC LIMIT 30").fetchall()
        return {"jobs": [dict(x) for x in rows]}
