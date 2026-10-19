"""Direct-parent supervisor: bounded I/O, WNOWAIT, then group cleanup, then reap."""
from __future__ import annotations
from contextlib import contextmanager
import argparse
import json
import os
from pathlib import Path
import selectors
import sqlite3
import subprocess
import time
from audit import AuditLog
from opencode_core import OpenCodeRunner

POLL_SECONDS = 0.05
MAX_LINE_BYTES = 65536
PERMISSION_EVENTS = {"permission", "permission_request", "permission.asked", "permission.requested"}

@contextmanager
def _db(path):
    db = sqlite3.connect(path, timeout=2)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()

class Events:
    def __init__(self, session):
        self.session = session
        self.pending = bytearray()
        self.completion = False
        self.error = None
        self.permission = False

    def feed(self, data):
        self.pending.extend(data)
        while b"\n" in self.pending:
            line, _, tail = self.pending.partition(b"\n")
            self.pending = bytearray(tail)
            if len(line) > MAX_LINE_BYTES:
                self.error = "output_line_limit"
                return
            try:
                event = json.loads(line.decode("utf-8"))
            except (ValueError, UnicodeError):
                self.error = "malformed_output"
                return
            if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                self.error = "malformed_event"
                return
            if event["type"] == "error":
                self.error = "cli_error_event"
                return
            if event.get("sessionID") != self.session:
                self.error = "session_mismatch"
                return
            part = event.get("part", {})
            if not isinstance(part, dict) or ("sessionID" in part and part["sessionID"] != self.session):
                self.error = "malformed_part"
                return
            if event["type"] in PERMISSION_EVENTS:
                self.permission = True
            if part.get("type") == "error" or (isinstance(part.get("state"), dict) and part["state"].get("status") == "error"):
                self.error = "tool_error_event"
            if event["type"] == "text" and part.get("type") == "text" and isinstance(part.get("text"), str) and part["text"]:
                self.completion = True
            if part.get("type") == "step-finish" and part.get("reason") in ("stop", "end_turn", "stop_sequence"):
                self.completion = True
        if len(self.pending) > MAX_LINE_BYTES:
            self.error = "output_line_limit"

    def finish(self):
        if self.pending:
            self.error = "truncated_output"
        if not self.error and not self.completion:
            self.error = "no_response_evidence"


def _finish(dbpath, job_id, pid, status, code, reason):
    with _db(dbpath) as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT status,cancel_flag FROM jobs WHERE job_id=? AND pid=?", (job_id, pid)).fetchone()
        if not row or row["status"] != "running":
            return None
        # A cancellation admitted before the terminal commit wins the race.
        # Cleanup is already finished before this function is called.
        if row["cancel_flag"] and status == "completed":
            status, reason = "cancelled", "cancel_requested"
        db.execute("UPDATE jobs SET status=?,finished=?,exit_code=?,last_known_state='running',last_transition_at=?,transition_actor='worker',transition_reason=?,result_reason=? WHERE job_id=? AND status='running' AND pid=?", (status, time.time(), code, time.time(), reason, None if status == "completed" else reason, job_id, pid))
    return status


def _run(row, dbpath, job_id, worker_pid):
    deadline = time.monotonic() + row["max_runtime_seconds"]
    argv = [row["binary"], "run", "--standalone", "--format", "json", "--session", row["session_id"], "--model", row["model"]]
    proc = None
    cleaner = OpenCodeRunner({})
    ownership = "unknown"
    selector = selectors.DefaultSelector()
    events = Events(row["session_id"])
    status, reason, code = "failed", "worker_failure", None
    sizes = {"stdout": 0, "stderr": 0}
    output = {}
    normal_exit = False
    prompt = memoryview(row["prompt"].encode("utf-8"))
    sent = 0
    try:
        for name, key in (("stdout", "log_path"), ("stderr", "err_path")):
            output[name] = open(row[key], "ab", buffering=0)
        # Inherit operator native config unchanged. The caller cannot supply
        # environment variables or flags. This adds no permission sandbox.
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=row["workspace"], shell=False, start_new_session=True, close_fds=True)
        ownership = "pinned"
        with _db(dbpath) as db:
            db.execute("UPDATE jobs SET child_pid=? WHERE job_id=? AND status='running' AND pid=?", (proc.pid, job_id, worker_pid))
        for stream, name, mode in ((proc.stdin, "stdin", selectors.EVENT_WRITE), (proc.stdout, "stdout", selectors.EVENT_READ), (proc.stderr, "stderr", selectors.EVENT_READ)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, mode, name)

        def pump(timeout):
            nonlocal sent, reason
            for key, _ in selector.select(timeout):
                stream, name = key.fileobj, key.data
                if name == "stdin":
                    try:
                        sent += os.write(stream.fileno(), prompt[sent:sent + 65536])
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        events.error = "prompt_delivery_failed"
                        sent = len(prompt)
                    if sent == len(prompt):
                        selector.unregister(stream)
                        stream.close()
                    continue
                try:
                    data = os.read(stream.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not data:
                    selector.unregister(stream)
                    stream.close()
                    continue
                room = row["max_output_bytes"] - sizes[name]
                output[name].write(data[:room])
                sizes[name] += min(room, len(data))
                if name == "stdout":
                    events.feed(data[:room])
                if len(data) > room:
                    reason = "output_cap_exceeded"
                    return False
            return True

        while True:
            with _db(dbpath) as db:
                current = db.execute("SELECT cancel_flag,status FROM jobs WHERE job_id=? AND pid=?", (job_id, worker_pid)).fetchone()
            if not current or current["status"] != "running":
                reason = "reservation_lost"
                break
            if current["cancel_flag"]:
                status, reason = "cancelled", "cancel_requested"
                break
            if time.monotonic() >= deadline:
                reason = "runtime_deadline"
                break
            if not pump(min(POLL_SECONDS, max(0, deadline - time.monotonic()))):
                break
            if events.error:
                reason = events.error
                break
            if events.permission:
                status, reason = "permission_required", "native_permission_request"
                break
            try:
                observed = os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            except InterruptedError:
                continue
            except ChildProcessError:
                ownership = "unknown"
                status, reason = "unknown_exit", "child_ownership_lost"
                break
            if observed is not None:
                normal_exit = True
                break

        # Always clean descendants, including after a normal leader exit.
        # No poll(), wait(), communicate() or SIGCHLD reaper before this call.
        cleaner._cleanup_group(proc, ownership)
        ownership = "unknown"  # cleanup reaped; never signal this PGID again
        code = proc.returncode
        if code is None:
            normal_exit = False
            status, reason = "unknown_exit", "cleanup_unconfirmed"
        if not proc.stdin.closed:
            selector.unregister(proc.stdin)
            proc.stdin.close()
        # Drain only bounded pipe buffers after cleanup, not an unbounded file.
        drain_deadline = time.monotonic() + 1
        while selector.get_map() and time.monotonic() < drain_deadline:
            if not pump(POLL_SECONDS):
                normal_exit = False
                break
        if normal_exit:
            events.finish()
            if events.permission:
                status, reason = "permission_required", "native_permission_request"
            elif events.error:
                status, reason = "failed", events.error
            elif selector.get_map():
                status, reason = "failed", "output_drain_incomplete"
            elif code != 0:
                status, reason = "failed", "nonzero_exit"
            else:
                status, reason = "completed", "response_completed"
    except Exception:
        status, reason = "failed", "worker_io_failure"
    finally:
        if proc is not None and ownership != "unknown":
            cleaner._cleanup_group(proc, ownership)
            code = proc.returncode
        selector.close()
        if proc is not None:
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                if stream is not None:
                    stream.close()
        for handle in output.values():
            handle.close()
    return status, code, reason


def supervise(state, job_id, audit_config=None):
    dbpath, pid = state / "opencode-tasks.sqlite3", os.getpid()
    wait_until = time.monotonic() + 5
    row = None
    while time.monotonic() < wait_until:
        with _db(dbpath) as db:
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row and row["status"] == "running" and row["pid"] == pid:
            break
        if not row or row["status"] != "pending":
            return 2
        time.sleep(0.01)
    else:
        return 2
    status, code, reason = _run(row, dbpath, job_id, pid)
    final = _finish(dbpath, job_id, pid, status, code, reason)
    if final:
        AuditLog(state, audit_config).record("opencode", "finish", job_id, final, {"transition_reason": reason, "exit_code": code})
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--audit-config-json", default="null")
    args = parser.parse_args()
    raise SystemExit(supervise(args.state, args.job_id, json.loads(args.audit_config_json)))

if __name__ == "__main__":
    main()
