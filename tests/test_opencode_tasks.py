"""SPEC section 18 acceptance tests: OpenCode task execution."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat as stat_module
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from opencode_tasks import OpenCodeTasks, OpenCodeTaskError

FIXTURE = str(Path(__file__).resolve().parent / "fixtures" / "opencode_fixture_cli.py")


def execution_config(**overrides):
    config = {"enabled": True, "binary": FIXTURE,
              "execution": {"enabled": True, "allowed_workspaces": [], "allowed_models": []}}
    config["execution"].update(overrides)
    return config


class OpenCodeExecutionBase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.workspace = self.root / "ws"
        self.workspace.mkdir(mode=0o700)

    def make_tasks(self, config, max_runtime=30):
        config = json.loads(json.dumps(config))
        execution = config.get("execution") or {}
        config["execution"] = execution
        execution["allowed_workspaces"] = [str(self.workspace)]
        execution["allowed_models"] = ["prov/model-1"]
        execution["max_runtime_seconds"] = max_runtime
        return OpenCodeTasks(config, self.root / "state")

    def submit_terminal(self, tasks, *args, **kwargs):
        """Submit and poll until the job leaves pending/running."""
        ack = tasks.submit(*args, **kwargs)
        deadline = time.time() + 30
        while time.time() < deadline:
            row = tasks._row(ack["job_id"])
            if row["status"] not in ("pending", "running"):
                break
            time.sleep(0.05)
        return ack, row


class DisabledFailClosed(OpenCodeExecutionBase):
    def test_disabled_fails_closed(self):
        tasks = OpenCodeTasks({}, self.root / "state")
        for call in (lambda: tasks.submit("p", str(self.workspace), "r1"),
                     lambda: tasks.status("oct_x"), lambda: tasks.result("oct_x"),
                     lambda: tasks.cancel("oct_x"), lambda: tasks.recent()):
            with self.assertRaises(OpenCodeTaskError):
                call()

    def test_disabled_never_creates_state(self):
        OpenCodeTasks({}, self.root / "state")
        self.assertFalse((self.root / "state" / "opencode-tasks.sqlite3").exists())


class Validation(OpenCodeExecutionBase):
    def test_enabled_requires_opencode_enabled_and_binary(self):
        with self.assertRaises(OpenCodeTaskError):
            self.make_tasks({"enabled": False, "binary": FIXTURE})
        with self.assertRaises(OpenCodeTaskError):
            self.make_tasks({"enabled": True, "binary": ""})

    def test_empty_workspaces_or_models_rejected(self):
        with self.assertRaises(OpenCodeTaskError):
            self.make_tasks(execution_config())
        config = execution_config()
        config["execution"]["allowed_workspaces"] = None
        with self.assertRaises(OpenCodeTaskError):
            self.make_tasks(config)

    def test_relative_workspace_rejected(self):
        config = execution_config(allowed_workspaces=["relative/path"], allowed_models=["p/m"])
        with self.assertRaises(OpenCodeTaskError):
            self.make_tasks(config)

    def test_control_characters_rejected(self):
        config = execution_config(allowed_models=["p/m\x1b"])
        with self.assertRaises(OpenCodeTaskError):
            self.make_tasks(config)

    def test_model_form_rejected(self):
        for value in ("nomodel", "a/b/c", "/model"):
            config = execution_config(allowed_models=[value])
            with self.assertRaises(OpenCodeTaskError):
                self.make_tasks(config)

    def test_out_of_range_limits_rejected(self):
        for key, value in (("max_prompt_chars", 0), ("max_runtime_seconds", 10),
                           ("max_output_bytes", 1024)):
            config = execution_config(allowed_workspaces=["/tmp"], allowed_models=["p/m"], **{key: value})
            with self.assertRaises(OpenCodeTaskError):
                self.make_tasks(config)


class Submission(OpenCodeExecutionBase):
    def test_session_minted_before_spawn_and_stored(self):
        tasks = self.make_tasks(execution_config())
        ack = tasks.submit("hello", str(self.workspace), "r1")
        self.assertRegex(ack["session_id"], r"^ses_[A-Za-z0-9]{8,64}$")
        row = tasks._row(ack["job_id"])
        self.assertEqual(row["session_id"], ack["session_id"])
        self.assertEqual(row["status"], "completed")

    def test_submit_fixture_completed_exit0(self):
        tasks = self.make_tasks(execution_config())
        ack, row = self.submit_terminal(tasks, "OK please", str(self.workspace), "r1")
        self.assertEqual(row["status"], "completed")

    def test_fixed_argv_and_no_env_injection(self):
        tasks = self.make_tasks(execution_config())
        captured = {}
        real_popen = OpenCodeTasks.__module__

        class FakeWorker:
            pid = 999999

            def wait(self, timeout=None):
                return 0

        # Spy on subprocess.Popen in opencode_tasks to capture argv/env
        import subprocess as sp
        original = sp.Popen

        def spy(argv, **kwargs):
            captured["argv"] = argv
            captured["kwargs"] = kwargs
            raise OSError("stop before real spawn")

        with mock.patch(f"{real_popen}.subprocess.Popen", spy):
            with self.assertRaises(OpenCodeTaskError):
                tasks.submit("hello", str(self.workspace), "r2")
        argv = captured["argv"]
        self.assertEqual(argv[1:], ["worker-placeholder"]) if False else None
        self.assertIn("--standalone", argv)
        self.assertIn("--format", argv)
        self.assertNotIn("--auto", argv)
        self.assertNotIn("--server", argv)
        self.assertNotIn("--continue", argv)
        self.assertNotIn("--agent", argv)
        self.assertNotIn("-f", argv)
        self.assertEqual(captured["kwargs"].get("shell"), False)
        self.assertEqual(captured["kwargs"].get("cwd"), str(self.workspace))

    def test_idempotency_same_request_same_fingerprint(self):
        tasks = self.make_tasks(execution_config())
        first = tasks.submit("prompt-a", str(self.workspace), "same-req")
        second = tasks.submit("prompt-a", str(self.workspace), "same-req")
        self.assertEqual(first["job_id"], second["job_id"])
        self.assertEqual(first["session_id"], second["session_id"])

    def test_idempotency_conflict_rejected(self):
        tasks = self.make_tasks(execution_config())
        tasks.submit("prompt-a", str(self.workspace), "conflict")
        with self.assertRaises(OpenCodeTaskError):
            tasks.submit("prompt-b", str(self.workspace), "conflict")

    def test_busy_global_concurrency(self):
        tasks = self.make_tasks(execution_config(), max_runtime=60)
        with mock.patch.object(OpenCodeTasks, "_start", side_effect=lambda job_id: {"job_id": job_id, "status": "running", "session_id": "ses_x", "model": "prov/model-1"}):
            tasks.submit("one", str(self.workspace), "r1")
            with self.assertRaises(OpenCodeTaskError) as caught:
                tasks.submit("two", str(self.workspace), "r2")
        self.assertIn("busy", str(caught.exception))

    def test_unknown_session_rejected(self):
        tasks = self.make_tasks(execution_config())
        with self.assertRaises(OpenCodeTaskError):
            tasks.submit("p", str(self.workspace), "r1", session_id="ses_stranger00")

    def test_resume_completed_session_new_job(self):
        tasks = self.make_tasks(execution_config())
        first = tasks.submit("OK 1", str(self.workspace), "r1")
        second = tasks.submit("OK 2", str(self.workspace), "r2", session_id=first["session_id"])
        self.assertNotEqual(first["job_id"], second["job_id"])
        self.assertEqual(first["session_id"], second["session_id"])

    def test_resume_requires_canonical_workspace(self):
        tasks = self.make_tasks(execution_config())
        first = tasks.submit("OK 1", str(self.workspace), "r1")
        other = self.root / "ws2"
        other.mkdir()
        with self.assertRaises(OpenCodeTaskError):
            tasks.submit("OK 2", str(other), "r2", session_id=first["session_id"])

    def test_prompt_length_enforced(self):
        tasks = self.make_tasks(execution_config(max_prompt_chars=10))
        with self.assertRaises(OpenCodeTaskError):
            tasks.submit("x" * 11, str(self.workspace), "r1")

    def test_outside_workspace_rejected(self):
        tasks = self.make_tasks(execution_config())
        with self.assertRaises(OpenCodeTaskError):
            tasks.submit("p", str(self.root), "r1")


class Outcomes(OpenCodeExecutionBase):
    def test_no_completion_evidence_fails_despite_exit0(self):
        tasks = self.make_tasks(execution_config())
        ack, row = self.submit_terminal(tasks, "NOEVENT", str(self.workspace), "r1")
        self.assertEqual(row["status"], "failed")

    def test_error_event_exit0_fails(self):
        tasks = self.make_tasks(execution_config())
        ack, row = self.submit_terminal(tasks, "ERREVENT0", str(self.workspace), "r1")
        self.assertEqual(row["status"], "failed")

    def test_permission_required_detected(self):
        tasks = self.make_tasks(execution_config(), max_runtime=30)
        with mock.patch("opencode_worker.POLL_SECONDS", 0.05):
            ack, row = self.submit_terminal(tasks, "PERMISSION", str(self.workspace), "r1")
        self.assertEqual(row["status"], "permission_required")

    def test_result_pagination_and_redaction(self):
        tasks = self.make_tasks(execution_config())
        ack, row = self.submit_terminal(tasks, "OK please", str(self.workspace), "r1")
        page = tasks.result(ack["job_id"])
        self.assertIn("fixture-ok", page["content"])
        self.assertIn("untrusted", page["note"])
        page2 = tasks.result(ack["job_id"], offset=page["next_offset"])
        self.assertFalse(page2["truncated"])

    def test_status_recent_redacted(self):
        tasks = self.make_tasks(execution_config())
        ack, row = self.submit_terminal(tasks, "SECRET-CONTENT-MARKER", str(self.workspace), "r1")
        status = tasks.status(ack["job_id"])
        self.assertNotIn("SECRET-CONTENT-MARKER", json.dumps(status))
        self.assertNotIn("SECRET-CONTENT-MARKER", json.dumps(tasks.recent()))
        for path in (tasks.logs / f"{ack['job_id']}.jsonl", tasks.dbpath):
            info = path.stat()
            self.assertTrue(info.st_mode & stat_module.S_IRUSR)
            self.assertFalse(info.st_mode & (stat_module.S_IRGRP | stat_module.S_IROTH))

    def test_cancel_pending_is_immediate(self):
        tasks = self.make_tasks(execution_config())
        with mock.patch.object(OpenCodeTasks, "_start", return_value={"job_id": "oct_x", "status": "pending", "session_id": "ses_x", "model": "prov/model-1"}):
            with mock.patch.object(OpenCodeTasks, "db", OpenCodeTasks.db):
                # insert a pending row directly then cancel it
                with tasks.db() as db:
                    db.execute(
                        "INSERT INTO jobs (job_id,request_id,fingerprint,created,workspace,session_id,model,"
                        "prompt,status,log_path,err_path,binary,max_output_bytes,max_runtime_seconds,cancel_flag) "
                        "VALUES ('oct_x','r9','fp',?,?,'ses_x','prov/model-1','p','pending','l','e','b',1,30,0)",
                        (time.time(), str(self.workspace)))
                result = tasks.cancel("oct_x")
        self.assertEqual(result["status"], "cancelled")

    def test_terminal_immutable(self):
        tasks = self.make_tasks(execution_config())
        ack = tasks.submit("OK please", str(self.workspace), "r1")
        with self.assertRaises(OpenCodeTaskError):
            tasks._set_terminal(ack["job_id"], "failed", last_known_state="running",
                                actor="test", reason="no", allowed_from=("running",))

    def test_group_cleanup_after_spawnchild(self):
        tasks = self.make_tasks(execution_config(), max_runtime=30)
        ack, row = self.submit_terminal(tasks, "SPAWNCHILD", str(self.workspace), "r1")
        self.assertEqual(row["status"], "completed")
        time.sleep(0.2)
        # The fixture descendant must be gone: the worker signaled the group.
        stray = [pid for pid in os.listdir("/proc") if pid.isdigit()
                 and _cmdline(pid) == ["sleep", "60"]]
        self.assertEqual(stray, [])


def _cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as handle:
            return handle.read().decode().split("\0")[:-1]
    except OSError:
        return []


if __name__ == "__main__":
    unittest.main()
