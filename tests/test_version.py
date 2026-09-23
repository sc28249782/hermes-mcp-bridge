from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import bridge
from version_core import report

ROOT = Path(__file__).resolve().parents[1]


class TestVersionReport(unittest.TestCase):
    def test_worktree_report_is_local_and_uses_git_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / "bridge-config.json").write_text(json.dumps({"schema_version": 1}))
            with patch("version_core._runtime_git_revision",
                       return_value="a" * 40) as revision:
                result = report(root)
        self.assertEqual(result["source_kind"], "git-worktree")
        self.assertEqual(result["source_revision"], "a" * 40)
        self.assertEqual(result["revision_source"], "git")
        self.assertEqual(result["config_schema_version"], 1)
        self.assertEqual(result["mcp_discovery_count"], 27)
        revision.assert_called_once()

    def test_release_archive_and_bad_config_fail_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bridge-config.json").write_text("{broken")
            result = report(root)
        self.assertEqual(result["source_kind"], "release-archive")
        self.assertEqual(result["source_revision"], "unknown")
        self.assertEqual(result["revision_source"], "unknown")
        self.assertEqual(result["config_schema_version"], "unknown")

    def test_release_archive_uses_valid_embedded_build_input_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("version_core.EMBEDDED_SOURCE_REVISION",
                       "b" * 40):
                result = report(Path(tmp))
        self.assertEqual(result["source_revision"], "b" * 40)
        self.assertEqual(result["revision_source"], "embedded-build-input")

    def test_version_action_does_not_initialize_configured_backends(self):
        output = StringIO()
        with (
            patch.object(sys, "argv", ["bridge.py", "version"]),
            patch("bridge.HandsRuntime.from_config",
                  side_effect=AssertionError("Hands must not initialize")),
            patch("bridge.Bridge.from_config",
                  side_effect=AssertionError("Hermes must not initialize")),
            redirect_stdout(output),
        ):
            bridge.main()
        self.assertEqual(json.loads(output.getvalue()), report(ROOT))

    def test_cli_matches_local_report(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "bridge.py"), "version"],
            cwd=ROOT, text=True, capture_output=True, check=True, timeout=10,
        )
        self.assertEqual(json.loads(completed.stdout), report(ROOT))


if __name__ == "__main__":
    unittest.main()
