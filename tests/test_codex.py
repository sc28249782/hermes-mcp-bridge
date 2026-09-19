from pathlib import Path
import tempfile
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
        fake.write_text("#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps({'argv':sys.argv[1:],'prompt':sys.stdin.read()}))\n")
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


if __name__ == "__main__":
    unittest.main()
