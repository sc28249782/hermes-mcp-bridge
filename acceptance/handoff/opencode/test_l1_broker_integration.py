"""Execute a sealed C model image, with no real E or H."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from l1_retained_launcher import verified_image
from test_l1_retained_fd_exec import run_probe


class BrokerIntegrationControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        cls.image = Path(tmp.name) / "broker"
        subprocess.run(
            ["cc", "-static", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
             "l1_broker_integration_probe.c", "l1_broker_lifecycle.c", "-o", str(cls.image)],
            cwd=Path(__file__).resolve().parent, timeout=20, check=True,
        )
        cls.digest = hashlib.sha256(cls.image.read_bytes()).hexdigest()

    def test_sealed_image_drives_scripted_role_lifecycle(self):
        fd = verified_image(self.image, self.digest)
        try:
            result = run_probe(fd)
        finally:
            os.close(fd)
        self.assertEqual(result.stdout, b"L1_SEALED_C_BROKER_PREFLIGHT_HOLD\n")
        self.assertEqual(result.stderr, b"")

    def test_digest_mismatch_blocks_exec(self):
        with patch("subprocess.run", side_effect=AssertionError("unexpected exec")):
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                run_probe(verified_image(self.image, "0" * 64))


if __name__ == "__main__":
    unittest.main()
