"""Detached, durable supervisor for one OpenCode bridge execution job.

This module is launched by opencode_tasks. It remains the direct parent of the
OpenCode CLI process after the bridge disconnects, enforces the runtime and
output limits independently of controller polling, honors the database cancel
flag, and writes the terminal record to the bridge SQLite state database.

Cleanup invariant (identical to the section 16 health probe): the CLI child
starts its own session so the leader's PID is its process-group ID. Every
`killpg` happens only while the leader is still an unreaped child of this
worker, observed with `WNOHANG | WNOWAIT`, and the leader is reaped exactly
once, by handle, after the final group signal. The controller never signals a
stored PID or PGID.

The worker never approves a native permission request. An observed permission
request classifies the job as `permission_required`; an unresolved ask that
outlives the runtime deadline produces `failed` with a timeout reason.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time

import opencode_core
from audit import AuditLog

POLL_SECONDS = 0.2
MAX_LINE_BYTES = 65_536
STRIPPED_ENV_KEYS = ("OPENCODE_CONFIG", "OPENCODE_CONFIG_CONTENT", "OPENCODE_CONFIG_DIR")


def _db(path: Path):
    conn = sqlite3.connect(path, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


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
              reason: str, result_reason: str | None) -> bool:
    """Write the terminal record once; terminal states are immutable."""
    now = time.time()
    with _db(dbpath) as db:
        changed = db.execute(
            "UPDATE jobs SET status=?,finished=?,exit_code=?,"
            "last_known_state='running',last_transition_at=?,transition_actor='worker',"
            "transition_reason=?,result_reason=? "
            "WHERE job_id=? AND status IN ('pending','running') AND pid=?",
            (status, now, exit_code, now, reason, result_reason, job_id, worker_pid),
        ).rowcount
    return changed == 1


def _log_has_permission_event(path: Path) -> bool:
    try:
        with open(path, "rb") as handle:
            for line in handle:
                if b'"permission' in line:
                    return True
    except OSError:
        pass
    return False


def _classify_log(path: Path, session_id: str) -> str | None:
    """Validate the JSONL output and return a failure classification, or None.

    Every event must be a bounded JSON object; every sessionID it carries must
    match the job session. Completion evidence is a text or step-finish event.
    An explicit error event fails the job even when the process exited 0.
    """
    saw_completion = False
    try:
        with open(path, "rb") as handle:
            for line in handle:
                if len(line) > MAX_LINE_BYTES:
                    return "output line exceeded the bounded object size"
                try:
                    event = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return "output contained a malformed JSON event"
                if not isinstance(event, dict):
                    return "output contained a non-object event"
                event_session = event.get("sessionID")
                part = event.get("part") if isinstance(event.get("part"), dict) else {}
                if isinstance(event_session, str) and event_session != session_id:
                    return "output carried a foreign session identifier"
                if part.get("sessionID") and part["sessionID"] != session_id:
                    return "output carried a foreign session identifier"
                if event.get("type") == "error" or part.get("type") == "error":
                    return "the CLI reported an error event"
                if event.get("type") == "text" or part.get("type") in ("text", "step-finish"):
                    saw_completion = True
    except OSError:
        return "job output could not be read"
    if not saw_completion:
        return "no valid response completion event was observed"
    return None


def _flag_set(dbpath: Path, job_id: str, worker_pid: int) -> bool:
    with _db(dbpath) as db:
        row = db.execute(
            "SELECT cancel_flag FROM jobs WHERE job_id=? AND status='running' AND pid=?",
            (job_id, worker_pid),
        ).fetchone()
    return bool(row and row["cancel_flag"])


def supervise(state: Path, job_id: str, ready_fd: int, audit_config: dict | None) -> int:
    dbpath = state / "opencode-tasks.sqlite3"
    worker_pid = os.getpid()
    row = None
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with _db(dbpath) as db:
            row = db.execute(
                "SELECT workspace,model,session_id,prompt,log_path,err_path,status,pid "
                "FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
        if row and row["status"] == "running" and row["pid"] == worker_pid:
            break
        if row and row["status"] not in ("pending", "running"):
            _ready(ready_fd, {"ok": False, "error": "job was not reserved for this worker"})
            return 2
        time.sleep(0.01)
    else:
        _ready(ready_fd, {"ok": False, "error": "job reservation timed out"})
        return 2

    # Fixed argv per SPEC section 18.3: no caller-supplied flags, no --auto,
    # no --server, no --continue, no file attachments.
    argv = [
        job_binary(state, job_id),
        "run", "--standalone", "--format", "json",
        "--session", row["session_id"], "--model", row["model"],
    ]
    env = {key: value for key, value in os.environ.items() if key not in STRIPPED_ENV_KEYS}
    try:
        with open(row["log_path"], "ab", buffering=0) as out_log, \
                open(row["err_path"], "ab", buffering=0) as err_log:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=out_log,
                stderr=err_log,
                cwd=row["workspace"],
                # The worker owns the CLI group: the child starts its own
                # session so its PID is the group ID, and only this direct
                # parent ever signals it (WNOWAIT invariant).
                start_new_session=True,
                shell=False,
                env=env,
            )
            child_start_ticks = _proc_starttime(proc.pid)
            with _db(dbpath) as db:
                db.execute(
                    "UPDATE jobs SET child_pid=?,child_start_ticks=? "
                    "WHERE job_id=? AND status='running' AND pid=?",
                    (proc.pid, child_start_ticks, job_id, worker_pid),
                )
            _ready(ready_fd, {"ok": True, "child_pid": proc.pid,
                              "child_start_ticks": child_start_ticks})
            try:
                proc.stdin.write(row["prompt"].encode("utf-8"))
                proc.stdin.close()
            except (BrokenPipeError, OSError):
                # The child already exited; classification below records the
                # true outcome instead of inventing a success.
                pass
            outcome = _supervise_loop(dbpath, state, job_id, worker_pid, proc, row, audit_config)
    except OSError:
        if _terminal(dbpath, job_id, worker_pid, "failed", None, "failed_to_spawn",
                     "OpenCode CLI process could not be started"):
            AuditLog(state, audit_config).record(
                "opencode", "finish", job_id, "failed",
                {"transition_reason": "failed_to_spawn", "transition_actor": "worker"})
        _ready(ready_fd, {"ok": False, "error": "failed to start OpenCode CLI"})
        return 1
    status, exit_code, reason, result_reason = outcome
    _terminal(dbpath, job_id, worker_pid, status, exit_code, reason, result_reason)
    AuditLog(state, audit_config).record(
        "opencode", "finish", job_id, status,
        {"exit_code": exit_code, "transition_actor": "worker", "transition_reason": reason})
    return 0


def job_binary(state: Path, job_id: str) -> str:
    with _db(state / "opencode-tasks.sqlite3") as db:
        row = db.execute("SELECT binary FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    return row["binary"]


def _supervise_loop(dbpath: Path, state: Path, job_id: str, worker_pid: int,
                    proc: subprocess.Popen, row: sqlite3.Row, audit_config: dict | None):
    """Own cancellation, the runtime deadline, output caps, and exit observation."""
    max_output = int(row["max_output_bytes"])
    runtime_deadline = time.monotonic() + int(row["max_runtime_seconds"])
    leader_state = "pinned"
    outcome = None
    while True:
        try:
            result = os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        except ChildProcessError:
            leader_state = "unknown"
            outcome = ("unknown_exit", None, "worker_lost_ownership",
                       "The worker could no longer prove it owns the CLI process")
            break
        except InterruptedError:
            result = None
        if result is not None:
            break
        if _flag_set(dbpath, job_id, worker_pid):
            outcome = ("cancelled", None, "cancel_requested",
                       "Cancellation was requested and the CLI group was terminated")
            break
        if time.monotonic() >= runtime_deadline:
            if _log_has_permission_event(Path(row["log_path"])):
                outcome = ("permission_required", None, "runtime_deadline_with_permission_request",
                           "A native permission request remained unresolved at the runtime deadline")
            else:
                outcome = ("failed", None, "runtime_deadline",
                           "The job exceeded the configured runtime deadline")
            break
        if _oversize(Path(row["log_path"]), max_output) or _oversize(Path(row["err_path"]), max_output):
            outcome = ("failed", None, "output_cap_exceeded",
                       "The job output exceeded the configured byte limit")
            break
        time.sleep(POLL_SECONDS)

    if outcome is None:
        # Normal exit: reap exactly once, by handle, after observing.
        try:
            exit_code = proc.wait(timeout=opencode_core.KILL_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            exit_code = None
            leader_state = "unknown" if leader_state == "unknown" else "pinned"
            outcome = ("failed", None, "reap_timeout",
                       "The CLI exit status could not be reaped in time")
        except ChildProcessError:
            exit_code = None
            leader_state = "unknown"
        if outcome is None:
            permission = _log_has_permission_event(Path(row["log_path"]))
            failure = _classify_log(Path(row["log_path"]), row["session_id"])
            if permission:
                outcome = ("permission_required", exit_code, "permission_request_observed",
                           "A native permission request was observed in the CLI output")
            elif failure is not None:
                outcome = ("failed", exit_code, "output_invalid", failure)
            elif exit_code != 0:
                outcome = ("failed", exit_code, "nonzero_exit",
                           "The OpenCode CLI exited with a non-zero status")
            else:
                outcome = ("completed", exit_code, "response_completed", None)
    if outcome[0] in ("cancelled", "failed", "permission_required", "unknown_exit") and leader_state != "unknown":
        # All killpg calls happen while the leader is still an unreaped child
        # of this worker; the leader is reaped once, by handle, afterwards.
        try:
            opencode_core.OpenCodeRunner._signal_group(proc.pid, signal.SIGTERM)
            state_flag, _ = opencode_core.OpenCodeRunner._observe_leader(
                proc.pid, time.monotonic() + opencode_core.KILL_GRACE_SECONDS)
            if state_flag != "unknown":
                opencode_core.OpenCodeRunner._signal_group(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=opencode_core.KILL_GRACE_SECONDS)
        except (subprocess.TimeoutExpired, ChildProcessError):
            pass
    elif outcome[0] == "completed":
        try:
            proc.wait(timeout=opencode_core.KILL_GRACE_SECONDS)
        except (subprocess.TimeoutExpired, ChildProcessError):
            pass
    return outcome


def _oversize(path: Path, cap: int) -> bool:
    try:
        return path.stat().st_size > cap
    except OSError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--job-id", required=True)
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
        supervise(Path(args.state), args.job_id, args.ready_fd, audit_config)
    )


if __name__ == "__main__":
    main()
