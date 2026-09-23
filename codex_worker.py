"""Detached, durable supervisor for a single Codex bridge job.

This module is launched by codex_core.  It remains the parent of the Codex CLI
after an interactive `bridge.sh codex-approve` invocation exits, then stores the
terminal exit status in the bridge SQLite state database.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

from audit import AuditLog


def _db(path: Path):
    conn = sqlite3.connect(path, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _ready(fd: int, payload: dict) -> None:
    try:
        os.write(fd, (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8"))
    except OSError:
        pass
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def _terminal(dbpath: Path, job_id: str, worker_pid: int, status: str, exit_code: int | None,
              reason: str, result_reason: str | None) -> None:
    now = time.time()
    with _db(dbpath) as db:
        db.execute(
            "UPDATE jobs SET status=?,finished=?,exit_code=?,exit_signal=NULL,"
            "last_known_state='running',last_transition_at=?,transition_actor='worker',"
            "transition_reason=?,result_reason=? "
            "WHERE job_id=? AND status='running' AND pid=?",
            (status, now, exit_code, now, reason, result_reason, job_id, worker_pid),
        )


def supervise(state: Path, job_id: str, binary: str, ready_fd: int, audit_config: dict | None) -> int:
    dbpath = state / "codex.sqlite3"
    worker_pid = os.getpid()
    with _db(dbpath) as db:
        row = db.execute(
            "SELECT job_id,workspace,mode,prompt,log_path,model,reasoning_effort,status,pid "
            "FROM jobs WHERE job_id=?",
            (job_id,),
        ).fetchone()
    if not row or row["status"] != "running" or row["pid"] != worker_pid:
        _ready(ready_fd, {"ok": False, "error": "job was not reserved for this worker"})
        return 2

    argv = [binary, "exec", "--json", "--sandbox", row["mode"], "-C", row["workspace"]]
    if row["model"]:
        argv.extend(["--model", row["model"]])
    if row["reasoning_effort"]:
        argv.extend(["-c", "model_reasoning_effort=" + row["reasoning_effort"]])
    argv.append("-")
    try:
        with open(row["log_path"], "ab", buffering=0) as log:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=row["workspace"],
                # The worker already has its own session/process group.  Keep
                # the child in it so cancellation kills both atomically.
                start_new_session=False,
                shell=False,
            )
            with _db(dbpath) as db:
                db.execute(
                    "UPDATE jobs SET child_pid=? WHERE job_id=? AND status='running' AND pid=?",
                    (proc.pid, job_id, worker_pid),
                )
            _ready(ready_fd, {"ok": True, "child_pid": proc.pid})
            try:
                proc.stdin.write(row["prompt"].encode("utf-8"))
                proc.stdin.close()
            except (BrokenPipeError, OSError):
                # The child already exited; wait below records its true exit
                # status rather than inventing a successful result.
                pass
            exit_code = proc.wait()
    except OSError:
        _terminal(
            dbpath, job_id, worker_pid, "failed", None, "failed_to_spawn",
            "Codex CLI process could not be started",
        )
        _ready(ready_fd, {"ok": False, "error": "failed to start Codex CLI"})
        return 1

    status = "completed" if exit_code == 0 else "failed"
    _terminal(
        dbpath, job_id, worker_pid, status, exit_code, "process_exit_observed",
        None if exit_code == 0 else "Codex CLI exited with a non-zero status",
    )
    AuditLog(state, audit_config).record(
        "codex", "finish", job_id, status,
        {"exit_code": exit_code, "transition_actor": "worker",
         "transition_reason": "process_exit_observed"},
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--ready-fd", required=True, type=int)
    parser.add_argument("--audit-config-json", default="null")
    args = parser.parse_args()
    try:
        audit_config = json.loads(args.audit_config_json)
    except json.JSONDecodeError:
        audit_config = None
    if audit_config is not None and not isinstance(audit_config, dict):
        audit_config = None
    raise SystemExit(
        supervise(Path(args.state), args.job_id, args.binary, args.ready_fd, audit_config)
    )


if __name__ == "__main__":
    main()
