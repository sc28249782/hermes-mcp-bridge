import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


class TestTunnelScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.bin = self.home / ".local" / "bin"
        self.config = self.root / "config"
        self.bin.mkdir(parents=True)
        self.script = Path(__file__).resolve().parents[1] / "tunnel.sh"
        self._write_executable("tunnel-client", """#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  doctor|run) test "${CONTROL_PLANE_API_KEY:-}" = "runtime-test-key"; echo "$1-ok" ;;
  init) echo init-ok ;;
  *) exit 2 ;;
esac
""")
        self._write_executable("systemctl", """#!/usr/bin/env bash
set -euo pipefail
test "${1:-}" = "--user"
shift
printf '%s\\n' "$*" >> "${SYSTEMCTL_LOG:?}"
""")

    def tearDown(self):
        self.tmp.cleanup()

    def _write_executable(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o700)

    def run_script(self, *args, input_text=None):
        env = os.environ | {
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.config),
            "SYSTEMCTL_LOG": str(self.root / "systemctl.log"),
        }
        return subprocess.run(["bash", str(self.script), *args], input=input_text, text=True,
                              env=env, capture_output=True, check=False)

    def test_key_set_loads_key_for_run_and_uses_mode_600(self):
        saved = self.run_script("key-set", input_text="runtime-test-key\n")
        self.assertEqual(saved.returncode, 0, saved.stderr)
        key_file = self.config / "hermes-mcp-bridge" / "openai-runtime-api-key"
        self.assertEqual(key_file.read_text(), "runtime-test-key")
        self.assertEqual(stat.S_IMODE(key_file.stat().st_mode), 0o600)
        status = self.run_script("key-status")
        self.assertEqual(status.returncode, 0, status.stderr)
        started = self.run_script("run")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertIn("doctor-ok", started.stdout)
        self.assertIn("run-ok", started.stdout)
        self.assertNotIn("runtime-test-key", started.stdout + started.stderr)

    def test_service_install_writes_unit_without_embedding_key(self):
        self.run_script("key-set", input_text="runtime-test-key\n")
        result = self.run_script("service-install")
        self.assertEqual(result.returncode, 0, result.stderr)
        unit = self.config / "systemd" / "user" / "hermes-mcp-tunnel.service"
        text = unit.read_text()
        self.assertIn("ExecStart=/bin/bash", text)
        self.assertIn("tunnel.sh run", text)
        self.assertNotIn("runtime-test-key", text)
        self.assertIn("daemon-reload", (self.root / "systemctl.log").read_text())


if __name__ == "__main__":
    unittest.main()
