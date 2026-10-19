"""Execution contract, with real detached workers and deterministic native CLI."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opencode_tasks import OpenCodeTasks, OpenCodeTaskError, _proc_starttime
from opencode_worker import Events

FIXTURE = str(Path(__file__).parent / "fixtures" / "opencode_fixture_cli.py")

class TestOpenCodeTasks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ws = self.root / "workspace"
        self.ws.mkdir()
        self.other = self.root / "other"
        self.other.mkdir()
        self.config = {"enabled": True, "binary": FIXTURE, "execution": {"enabled": True, "allowed_workspaces": [str(self.ws), str(self.other)], "allowed_models": ["fixture/model", "fixture/other"], "max_runtime_seconds": 2, "max_output_bytes": 65536}}
        self.tasks = OpenCodeTasks(self.config, self.root / "state")
        self.addCleanup(self.stop_jobs)

    def stop_jobs(self):
        for row in self.tasks.recent()["jobs"]:
            if row["status"] in ("pending", "running"):
                self.tasks.cancel(row["job_id"])
                self.wait(row["job_id"])

    def wait(self, job, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.tasks.status(job)
            if status["status"] not in ("pending", "running"):
                return status
            time.sleep(0.02)
        self.fail("worker did not reach terminal status")

    def run_prompt(self, prompt, request="one", **kwargs):
        ack = self.tasks.submit(prompt, str(self.ws), request, **kwargs)
        return ack, self.wait(ack["job_id"])

    def test_disabled_no_files_or_process(self):
        path = self.root / "disabled"
        disabled = OpenCodeTasks({}, path)
        with mock.patch("subprocess.Popen", side_effect=AssertionError("spawn")):
            for invoke in (lambda: disabled.submit("p", str(self.ws), "r"), lambda: disabled.status("x"), lambda: disabled.result("x"), lambda: disabled.cancel("x"), disabled.recent):
                with self.assertRaises(OpenCodeTaskError):
                    invoke()
        self.assertFalse(path.exists())

    def test_invalid_direct_configuration(self):
        for section, key, value in (("root", "enabled", False), ("root", "binary", "relative"), ("execution", "enabled", "true"), ("execution", "allowed_workspaces", []), ("execution", "allowed_models", []), ("execution", "allowed_models", ["p/m\x1b"]), ("execution", "allowed_models", ["-p/m"]), ("execution", "allowed_workspaces", ["relative"]), ("execution", "allowed_workspaces", [str(self.ws) + "\x1b"]), ("execution", "max_prompt_chars", True), ("execution", "max_runtime_seconds", 0), ("execution", "max_output_bytes", 1)):
            with self.subTest(key=key, value=value):
                config = json.loads(json.dumps(self.config))
                (config if section == "root" else config["execution"])[key] = value
                with self.assertRaises(OpenCodeTaskError):
                    OpenCodeTasks(config, self.root / "invalid")

    def test_state_must_be_outside_workspace(self):
        with self.assertRaises(OpenCodeTaskError):
            OpenCodeTasks(self.config, self.ws / "state")

    def test_private_state_files(self):
        ack, status = self.run_prompt("ok")
        self.assertEqual(status["status"], "completed")
        for path in (self.tasks.state, self.tasks.logs):
            self.assertEqual(path.stat().st_mode & 0o777, 0o700)
        for path in (self.tasks.dbpath, *self.tasks.logs.iterdir()):
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_fixed_native_argv_stdin_and_environment(self):
        with mock.patch.dict(os.environ, {"OPENCODE_CONFIG_CONTENT": "operator-test-policy"}):
            ack, status = self.run_prompt("inspect")
        self.assertEqual(status["status"], "completed")
        event = json.loads(self.tasks.result(ack["job_id"])["content"])
        output = json.loads(event["part"]["text"])
        self.assertEqual(output["argv"], ["run", "--standalone", "--format", "json", "--session", ack["session_id"], "--model", "fixture/model"])
        self.assertEqual(output["stdin"], "inspect")
        self.assertEqual(output["native_config"], "operator-test-policy")

    def test_large_prompt_delivered_without_pipe_deadlock(self):
        prompt = "length:" + "p" * 100000
        self.tasks.max_prompt = len(prompt)
        ack, status = self.run_prompt(prompt)
        self.assertEqual(status["status"], "completed")
        self.assertEqual(json.loads(self.tasks.result(ack["job_id"])["content"])["part"]["text"], str(len(prompt)))

    def test_child_never_reads_stdin_still_times_out(self):
        self.tasks.max_prompt = 131072
        self.tasks.max_runtime = 1
        start = time.monotonic()
        with mock.patch.dict(os.environ, {"HMB_FIXTURE_NOREAD": "1"}):
            _, result = self.run_prompt("x" * 131072)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["transition_reason"], "runtime_deadline")
        self.assertLess(time.monotonic() - start, 6)

    def test_retry_without_session_does_not_mint_or_spawn_again(self):
        first, _ = self.run_prompt("ok")
        with mock.patch.object(self.tasks, "_start", side_effect=AssertionError("duplicate spawn")):
            replay = self.tasks.submit("ok", str(self.ws), "one")
        self.assertEqual(first["job_id"], replay["job_id"])
        self.assertEqual(first["session_id"], replay["session_id"])

    def test_request_conflict(self):
        self.run_prompt("ok")
        with self.assertRaises(OpenCodeTaskError):
            self.tasks.submit("different", str(self.ws), "one")

    def test_owned_session_reuse(self):
        first, _ = self.run_prompt("ok")
        second, result = self.run_prompt("ok", "two", session_id=first["session_id"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(first["session_id"], second["session_id"])
        self.assertNotEqual(first["job_id"], second["job_id"])

    def test_unknown_session_denied(self):
        with self.assertRaises(OpenCodeTaskError):
            self.tasks.submit("ok", str(self.ws), "r", session_id="ses_unknown123")

    def test_resume_cannot_switch_even_allowlisted_workspace(self):
        first, _ = self.run_prompt("ok")
        with self.assertRaises(OpenCodeTaskError):
            self.tasks.submit("ok", str(self.other), "two", session_id=first["session_id"])

    def test_resume_cannot_switch_even_allowlisted_model(self):
        first, _ = self.run_prompt("ok")
        with self.assertRaises(OpenCodeTaskError):
            self.tasks.submit("ok", str(self.ws), "two", session_id=first["session_id"], model="fixture/other")

    def test_latest_failed_turn_prevents_resume(self):
        first, _ = self.run_prompt("ok")
        self.run_prompt("error0", "two", session_id=first["session_id"])
        with self.assertRaises(OpenCodeTaskError):
            self.tasks.submit("ok", str(self.ws), "three", session_id=first["session_id"])

    def test_atomic_concurrent_admission(self):
        barrier = threading.Barrier(2)
        def submit(index):
            instance = OpenCodeTasks(self.config, self.tasks.state)
            barrier.wait()
            try:
                return instance.submit("ok", str(self.ws), "request" + str(index))["job_id"]
            except OpenCodeTaskError:
                return None
        with mock.patch.object(OpenCodeTasks, "_start", lambda obj, job: obj._ack(obj._row(job))):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(submit, (1, 2)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(len(self.tasks.recent()["jobs"]), 1)

    def test_atomic_concurrent_idempotency(self):
        barrier = threading.Barrier(2)
        calls = []
        def start(obj, job):
            calls.append(job)
            return obj._ack(obj._row(job))
        def submit(_):
            barrier.wait()
            return self.tasks.submit("ok", str(self.ws), "same")["job_id"]
        with mock.patch.object(OpenCodeTasks, "_start", start), ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, (1, 2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(len(calls), 1)

    def test_bad_streams_fail_even_when_exit_zero(self):
        for prompt in ("empty", "error0", "tool_error", "wrong_session", "missing_session", "malformed", "truncated", "tool_calls_only", "nonzero"):
            with self.subTest(prompt=prompt):
                _, status = self.run_prompt(prompt, prompt)
                self.assertEqual(status["status"], "failed")

    def test_stdout_stderr_caps_bound_actual_files(self):
        for prompt in ("flood", "stderr_flood"):
            ack, status = self.run_prompt(prompt, prompt)
            self.assertEqual(status["status"], "failed")
            row = self.tasks._row(ack["job_id"])
            for key in ("log_path", "err_path"):
                self.assertLessEqual(Path(row[key]).stat().st_size, self.tasks.max_output)

    def test_permission_event_stops_promptly(self):
        start = time.monotonic()
        _, status = self.run_prompt("permission")
        self.assertEqual(status["status"], "permission_required")
        self.assertLess(time.monotonic() - start, 2)

    def test_permission_word_in_text_is_not_permission_request(self):
        _, status = self.run_prompt("permission_word")
        self.assertEqual(status["status"], "completed")

    def test_cancel_running_and_repeat(self):
        ack = self.tasks.submit("slow", str(self.ws), "slow")
        result = self.tasks.cancel(ack["job_id"])
        self.assertIn(result["status"], ("running", "cancelled"))
        self.assertEqual(self.wait(ack["job_id"])["status"], "cancelled")
        self.assertEqual(self.tasks.cancel(ack["job_id"])["status"], "cancelled")

    def test_cancel_pending_never_spawns(self):
        with mock.patch.object(self.tasks, "_start", lambda job: self.tasks._ack(self.tasks._row(job))):
            ack = self.tasks.submit("ok", str(self.ws), "pending")
        self.assertEqual(self.tasks.cancel(ack["job_id"])["status"], "cancelled")

    def test_terminal_state_immutable(self):
        ack, _ = self.run_prompt("ok")
        self.tasks.cancel(ack["job_id"])
        self.assertFalse(self.tasks._set_terminal(ack["job_id"], "failed", last_known_state="running", actor="test", reason="change"))
        self.assertEqual(self.tasks.status(ack["job_id"])["status"], "completed")

    def test_normal_exit_kills_own_term_ignoring_descendant(self):
        ack, status = self.run_prompt("descendant")
        self.assertEqual(status["status"], "completed")
        event = json.loads(self.tasks.result(ack["job_id"])["content"])
        child = int(event["part"]["text"].split("=")[1])
        deadline = time.monotonic() + 2
        while _proc_starttime(child) is not None and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertIsNone(_proc_starttime(child))

    def test_new_controller_reads_detached_worker(self):
        ack = self.tasks.submit("slow", str(self.ws), "slow")
        replacement = OpenCodeTasks(self.config, self.tasks.state)
        self.assertEqual(replacement.status(ack["job_id"])["session_id"], ack["session_id"])
        replacement.cancel(ack["job_id"])
        self.assertEqual(self.wait(ack["job_id"])["status"], "cancelled")

    def test_lost_worker_identity_becomes_unknown_without_signal(self):
        with mock.patch.object(self.tasks, "_start", lambda job: self.tasks._ack(self.tasks._row(job))):
            ack = self.tasks.submit("ok", str(self.ws), "pending")
        with self.tasks.db() as db:
            db.execute("UPDATE jobs SET status='running',created=0,pid=?,worker_start_ticks=-1 WHERE job_id=?", (os.getpid(), ack["job_id"]))
        with mock.patch("os.killpg", side_effect=AssertionError("foreign signal")):
            self.assertEqual(self.tasks.status(ack["job_id"])["status"], "unknown_exit")
            with self.assertRaises(OpenCodeTaskError):
                self.tasks.submit("ok", str(self.ws), "two")

    def test_unicode_pagination_is_lossless(self):
        ack, _ = self.run_prompt("unicode")
        content, offset = "", 0
        while True:
            page = self.tasks.result(ack["job_id"], offset, 7)
            content += page["content"]
            offset = page["next_offset"]
            if not page["truncated"]:
                break
        self.assertEqual(content, self.tasks.result(ack["job_id"])["content"])
        self.assertIn("ภาษาไทย 😀 中文", content)
        self.assertNotIn("\ufffd", content)

    def test_redacted_metadata_and_pagination_validation(self):
        ack, _ = self.run_prompt("sensitive-prompt")
        metadata = json.dumps([self.tasks.status(ack["job_id"]), self.tasks.recent()])
        self.assertNotIn("sensitive-prompt", metadata)
        self.assertNotIn(str(self.ws), metadata)
        for offset, size in ((-1, 10), (True, 10), (0, False), (0, 24001)):
            with self.assertRaises(OpenCodeTaskError):
                self.tasks.result(ack["job_id"], offset, size)

    def test_controller_spawn_failure_releases_slot(self):
        with mock.patch("opencode_tasks.subprocess.Popen", side_effect=OSError("private error")):
            with self.assertRaises(OpenCodeTaskError):
                self.tasks.submit("ok", str(self.ws), "spawn_fail")
        _, result = self.run_prompt("ok", "after_failure")
        self.assertEqual(result["status"], "completed")

    def test_signals_precede_the_only_reap_on_success_and_failure(self):
        from opencode_core import OpenCodeRunner
        from opencode_worker import _run, _finish
        import subprocess
        original_popen = subprocess.Popen
        original_signal = OpenCodeRunner._signal_group
        for prompt in ("ok", "error0"):
            with self.subTest(prompt=prompt):
                with mock.patch.object(self.tasks, "_start", lambda job: self.tasks._ack(self.tasks._row(job))):
                    ack = self.tasks.submit(prompt, str(self.ws), "ordering_" + prompt)
                with self.tasks.db() as db:
                    db.execute("UPDATE jobs SET status='running',pid=?,worker_start_ticks=? WHERE job_id=?", (os.getpid(), _proc_starttime(os.getpid()), ack["job_id"]))
                waits, signals = [], []
                def popen(*args, **kwargs):
                    proc = original_popen(*args, **kwargs)
                    original_wait = proc.wait
                    def wait(*args, **kwargs):
                        self.assertEqual(signals[-1], signal.SIGKILL)
                        waits.append(1)
                        return original_wait(*args, **kwargs)
                    proc.wait = wait
                    return proc
                def send(pgid, sig):
                    self.assertFalse(waits, "group signaled after leader reap")
                    signals.append(sig)
                    original_signal(pgid, sig)
                with mock.patch("opencode_worker.subprocess.Popen", side_effect=popen), mock.patch.object(OpenCodeRunner, "_signal_group", side_effect=send):
                    outcome = _run(self.tasks._row(ack["job_id"]), self.tasks.dbpath, ack["job_id"], os.getpid())
                self.assertEqual(waits, [1])
                self.assertEqual(signals, [signal.SIGTERM, signal.SIGKILL])
                _finish(self.tasks.dbpath, ack["job_id"], os.getpid(), *outcome)

    def test_cancel_admitted_before_terminal_commit_wins(self):
        from opencode_worker import _finish
        with mock.patch.object(self.tasks, "_start", lambda job: self.tasks._ack(self.tasks._row(job))):
            ack = self.tasks.submit("ok", str(self.ws), "race")
        with self.tasks.db() as db:
            db.execute("UPDATE jobs SET status='running',pid=?,cancel_flag=1 WHERE job_id=?", (os.getpid(), ack["job_id"]))
        self.assertEqual(_finish(self.tasks.dbpath, ack["job_id"], os.getpid(), "completed", 0, "response_completed"), "cancelled")
        self.assertIsNone(_finish(self.tasks.dbpath, ack["job_id"], os.getpid(), "failed", 1, "late_failure"))
        self.assertEqual(self.tasks.status(ack["job_id"])["status"], "cancelled")

class TestExecutionEvents(unittest.TestCase):
    def test_oversize_line_rejected_before_unbounded_accumulation(self):
        events = Events("ses_test123")
        events.feed(b"x" * 65537)
        self.assertEqual(events.error, "output_line_limit")

if __name__ == "__main__":
    unittest.main()
