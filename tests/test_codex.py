from pathlib import Path
import os
import signal
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch
import json
import time

from codex_core import CodexRunner, CodexError


class TestCodexRunner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "allowed"
        self.root.mkdir()
        self.runner = CodexRunner({"allowed_workspaces": [str(self.root)]}, Path(self.tmp.name) / "state")

    def tearDown(self):
        self.tmp.cleanup()

    def test_outside_workspace_is_rejected(self):
        with self.assertRaises(CodexError):
            self.runner.submit("inspect", self.tmp.name, "read-only")

    def test_symlink_escape_is_rejected(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        (self.root / "escape").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(CodexError):
            self.runner.submit("inspect", str(self.root / "escape"), "read-only")

    def test_write_waits_for_local_approval(self):
        with patch.object(self.runner, "_start") as start:
            result = self.runner.submit("edit README", str(self.root), "workspace-write")
        self.assertEqual(result["status"], "pending_local_approval")
        start.assert_not_called()

    def test_read_only_starts_immediately(self):
        with patch.object(self.runner, "_start") as start:
            result = self.runner.submit("inspect", str(self.root), "read-only")
        self.assertEqual(result["status"], "running")
        start.assert_called_once()

    def test_invalid_mode_is_rejected(self):
        with self.assertRaises(CodexError):
            self.runner.submit("x", str(self.root), "danger-full-access")

    def test_cancel_pending_is_deny(self):
        result = self.runner.submit("edit", str(self.root), "workspace-write")
        self.assertEqual(self.runner.cancel(result["job_id"])["status"], "denied")

    def test_subprocess_uses_fixed_argv_and_captures_result(self):
        fake = Path(self.tmp.name) / "fake-codex"
        fake.write_text("#!/usr/bin/env python3\nimport json,sys,time\nprint(json.dumps({'argv':sys.argv[1:],'prompt':sys.stdin.read()}))\ntime.sleep(0.1)\n")
        fake.chmod(0o700)
        runner = CodexRunner({"binary": str(fake), "allowed_workspaces": [str(self.root)]},
                             Path(self.tmp.name) / "state2")
        job = runner.submit("inspect safely", str(self.root), "read-only")
        for _ in range(100):
            status = runner.status(job["job_id"])
            if status["status"] != "running":
                break
            time.sleep(0.01)
        self.assertEqual(status["status"], "completed")
        payload = json.loads(runner.result(job["job_id"])["output"])
        self.assertEqual(payload["prompt"], "inspect safely")
        self.assertEqual(payload["argv"][:4], ["exec", "--json", "--sandbox", "read-only"])

    def test_model_and_reasoning_override_are_policy_gated_and_forwarded(self):
        fake = Path(self.tmp.name) / "fake-codex-model"
        fake.write_text("#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps({'argv':sys.argv[1:]}))\n")
        fake.chmod(0o700)
        runner = CodexRunner({"binary": str(fake), "workspaces": [{
            "path": str(self.root), "allowed_models": ["gpt-5.6"],
            "allowed_reasoning_efforts": ["medium", "high"]}]},
            Path(self.tmp.name) / "model-state")
        job = runner.submit("inspect", str(self.root), "read-only", "gpt-5.6", "high")
        for _ in range(100):
            status = runner.status(job["job_id"])
            if status["status"] != "running":
                break
            time.sleep(0.01)
        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["model"], "gpt-5.6")
        self.assertEqual(status["reasoning_effort"], "high")
        argv = json.loads(runner.result(job["job_id"])["output"])["argv"]
        self.assertIn("--model", argv)
        self.assertIn("gpt-5.6", argv)
        self.assertIn("model_reasoning_effort=high", argv)
        with self.assertRaises(CodexError):
            runner.submit("inspect", str(self.root), "read-only", "other-model", "high")
        with self.assertRaises(CodexError):
            runner.submit("inspect", str(self.root), "read-only", "gpt-5.6", "ultra")

    def test_model_override_is_disabled_without_an_allowlist(self):
        with self.assertRaises(CodexError):
            self.runner.submit("inspect", str(self.root), "read-only", "gpt-5.6", None)

    def test_health_exposes_model_policy_without_guessing_available_models(self):
        runner = CodexRunner({"workspaces": [{"path": str(self.root),
                                                "allowed_models": ["gpt-5.6"],
                                                "allowed_reasoning_efforts": ["high"]}]},
                             Path(self.tmp.name) / "model-health")
        with patch("codex_core.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "codex 0.test"
            policy = runner.health()["workspace_policies"][0]
        self.assertEqual(policy["allowed_models"], ["gpt-5.6"])
        self.assertEqual(policy["allowed_reasoning_efforts"], ["high"])

    def test_audit_is_redacted_and_records_lifecycle(self):
        job = self.runner.submit("very sensitive prompt", str(self.root), "workspace-write")
        self.runner.deny_local(job["job_id"])
        text = (Path(self.tmp.name) / "state" / "audit.jsonl").read_text()
        self.assertIn('"action":"submit"', text)
        self.assertIn('"action":"deny"', text)
        self.assertIn('"prompt_chars":21', text)
        self.assertNotIn("very sensitive prompt", text)

    def test_audit_rotates(self):
        runner = CodexRunner({"allowed_workspaces": [str(self.root)],
                              "audit": {"max_bytes": 32768, "retention_files": 2}},
                             Path(self.tmp.name) / "state3")
        for _ in range(350):
            runner.audit.record("codex", "test", "job", "ok", {"padding": "x" * 128})
        self.assertTrue((Path(self.tmp.name) / "state3" / "audit.jsonl.1").exists())

    def test_running_job_reports_recovery_after_runner_restart(self):
        job = self.runner.submit("edit", str(self.root), "workspace-write")
        with self.runner.db() as db:
            db.execute("UPDATE jobs SET status='running',started=?,pid=? WHERE job_id=?",
                       (time.time(), os.getpid(), job["job_id"]))
        restarted = CodexRunner({"allowed_workspaces": [str(self.root)]}, Path(self.tmp.name) / "state")
        self.assertTrue(restarted.status(job["job_id"])["recovered_after_restart"])

    def test_dead_recovered_job_is_unknown_not_completed(self):
        job = self.runner.submit("edit", str(self.root), "workspace-write")
        with self.runner.db() as db:
            db.execute("UPDATE jobs SET status='running',started=?,pid=? WHERE job_id=?",
                       (time.time(), 999999, job["job_id"]))
        status = self.runner.status(job["job_id"])
        self.assertEqual(status["status"], "unknown_exit")
        self.assertIsNone(status["exit_code"])
        self.assertTrue(status["recovered_after_restart"])

    def test_start_failure_is_persisted_as_failed(self):
        runner = CodexRunner({"binary": "/missing/codex", "allowed_workspaces": [str(self.root)]},
                             Path(self.tmp.name) / "start-failure")
        with self.assertRaises(CodexError):
            runner.submit("inspect", str(self.root), "read-only")
        with runner.db() as db:
            row = db.execute("SELECT status FROM jobs").fetchone()
        self.assertEqual(row["status"], "failed")
        self.assertIn('"action":"start_failed"', (Path(self.tmp.name) / "start-failure" / "audit.jsonl").read_text())

    def test_cancel_does_not_claim_terminal_while_process_lives(self):
        job = self.runner.submit("edit", str(self.root), "workspace-write")
        with self.runner.db() as db:
            db.execute("UPDATE jobs SET status='running',started=?,pid=? WHERE job_id=?",
                       (time.time(), 12345, job["job_id"]))
        with patch.object(self.runner, "_terminate", return_value=False):
            result = self.runner.cancel(job["job_id"])
        self.assertEqual(result["status"], "running")
        self.assertTrue(result["cancellation_pending"])
        self.assertEqual(self.runner._row(job["job_id"])["status"], "running")

    def test_terminate_escalates_to_sigkill_after_grace_period(self):
        with patch.object(self.runner, "_alive", side_effect=[True, True, True, False, False]), \
             patch("codex_core.os.killpg") as killpg, \
             patch("codex_core.time.monotonic", side_effect=[0, 3, 4]), \
             patch("codex_core.time.sleep"):
            self.assertTrue(self.runner._terminate(12345, None))
        self.assertEqual(killpg.call_args_list[0].args[1], signal.SIGTERM)
        self.assertEqual(killpg.call_args_list[1].args[1], signal.SIGKILL)

    def test_timeout_race_stays_running_until_termination_is_confirmed(self):
        runner = CodexRunner({"workspaces": [{"path": str(self.root), "max_runtime_seconds": 1}]},
                             Path(self.tmp.name) / "timeout-race")
        job = runner.submit("edit", str(self.root), "workspace-write")
        with runner.db() as db:
            db.execute("UPDATE jobs SET status='running',started=?,pid=? WHERE job_id=?",
                       (0, 12345, job["job_id"]))
        with patch.object(runner, "cancel", return_value={"status": "running"}):
            status = runner.status(job["job_id"])
        self.assertEqual(status["status"], "running")
        self.assertTrue(status["timeout_enforcement_pending"])

    def test_watchdog_enforces_workspace_runtime_without_status_poll(self):
        runner = CodexRunner({"workspaces": [{"path": str(self.root), "max_runtime_seconds": 1}]},
                             Path(self.tmp.name) / "watchdog")
        job = runner.submit("edit", str(self.root), "workspace-write")
        with runner.db() as db:
            db.execute("UPDATE jobs SET status='running',started=?,pid=? WHERE job_id=?",
                       (0, 12345, job["job_id"]))
        with patch.object(runner, "cancel", return_value={"status": "timed_out"}) as cancel:
            report = runner.enforce_timeouts()
        cancel.assert_called_once_with(job["job_id"], final_status="timed_out")
        self.assertEqual(report["outcomes"][0]["status"], "timed_out")

    def test_concurrency_reservation_is_atomic(self):
        runner = CodexRunner({"workspaces": [{"path": str(self.root), "max_concurrency": 1}]},
                             Path(self.tmp.name) / "atomic")
        def submit():
            try:
                return runner.submit("inspect", str(self.root), "read-only")["status"]
            except CodexError as exc:
                return str(exc)
        with patch.object(runner, "_start"):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: submit(), range(2)))
        self.assertEqual(results.count("running"), 1)
        self.assertEqual(results.count("workspace policy concurrency limit is reached"), 1)

    def test_approval_preview_is_public_cli_contract(self):
        job = self.runner.submit("edit README", str(self.root), "workspace-write")
        preview = self.runner.approval_preview(job["job_id"])
        self.assertEqual(preview["job_id"], job["job_id"])
        self.assertEqual(preview["prompt"], "edit README")

    def test_workspace_policy_rejects_disallowed_mode_and_pattern(self):
        runner = CodexRunner({"workspaces": [{"path": str(self.root), "modes": ["read-only"],
                                                "deny_prompt_patterns": ["deploy production"]}]},
                             Path(self.tmp.name) / "policy-state")
        with self.assertRaises(CodexError):
            runner.submit("inspect", str(self.root), "workspace-write")
        with self.assertRaises(CodexError):
            runner.submit("deploy production now", str(self.root), "read-only")

    def test_workspace_policy_concurrency_is_enforced(self):
        runner = CodexRunner({"workspaces": [{"path": str(self.root), "max_concurrency": 1}]},
                             Path(self.tmp.name) / "concurrency-state")
        with patch.object(runner, "_start"):
            runner.submit("inspect one", str(self.root), "read-only")
            with self.assertRaises(CodexError):
                runner.submit("inspect two", str(self.root), "read-only")

    def test_pending_write_expiry_is_enforced(self):
        runner = CodexRunner({"allowed_workspaces": [str(self.root)], "approval_ttl_seconds": 60},
                             Path(self.tmp.name) / "expiry-state")
        job = runner.submit("edit", str(self.root), "workspace-write")
        with runner.db() as db:
            db.execute("UPDATE jobs SET approval_expires=0 WHERE job_id=?", (job["job_id"],))
        status = runner.status(job["job_id"])
        self.assertEqual(status["status"], "expired")
        with self.assertRaises(CodexError):
            runner.approve_local(job["job_id"])

    def test_audit_recent_is_redacted(self):
        job = self.runner.submit("sensitive detail", str(self.root), "workspace-write")
        events = self.runner.audit.recent()["events"]
        self.assertEqual(events[-1]["subject"], job["job_id"])
        self.assertNotIn("sensitive detail", json.dumps(events))


if __name__ == "__main__":
    unittest.main()
