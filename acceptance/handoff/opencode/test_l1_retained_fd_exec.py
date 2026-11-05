"""Run the separately linked inert probe, never the retained H fixture."""
import fcntl
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from l1_retained_launcher import verified_image


# The trampoline receives only stdio plus the reviewed image fd. Mark the
# image close-on-exec again before Linux consumes it as the executable.
TRAMPOLINE = """\
import os, sys
fd = int(sys.argv[1])
os.set_inheritable(fd, False)
os.execve(fd, ["l1-inert-fd-probe", str(fd)], {})
"""


def run_probe(fd):
    if os.execve not in os.supports_fd:
        raise RuntimeError("fd exec unavailable")
    return subprocess.run(
        [sys.executable, "-I", "-S", "-c", TRAMPOLINE, str(fd)],
        pass_fds=(fd,), close_fds=True, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={},
        timeout=3, check=True,
    )


class FdExecControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        cls.build = Path(tmp.name) / "probe"
        source = Path(__file__).with_name("l1_retained_exec_probe.c")
        subprocess.run(
            ["cc", "-static", "-std=c11", "-Wall", "-Wextra", "-Werror",
             "-O2", str(source), "-o", str(cls.build)], check=True, timeout=20,
        )
        cls.data = cls.build.read_bytes()
        cls.digest = hashlib.sha256(cls.data).hexdigest()

    def test_exec_uses_sealed_bytes_after_path_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe"
            path.write_bytes(self.data)
            fd = verified_image(path, self.digest)
            self.addCleanup(os.close, fd)
            replacement = path.with_suffix(".other")
            replacement.write_bytes(b"replacement")
            replacement.replace(path)
            # The fixed sentinel probes must not mutate other parent fds.
            low = fcntl.fcntl(fd, fcntl.F_DUPFD, 127)
            self.addCleanup(os.close, low)
            high = fcntl.fcntl(fd, fcntl.F_DUPFD, 511)
            self.addCleanup(os.close, high)
            self.assertEqual((low, high), (127, 511))
            self.assertTrue(os.get_inheritable(low))
            self.assertTrue(os.get_inheritable(high))
            result = run_probe(fd)
            self.assertEqual(result.stdout, b"L1_INERT_FD_EXEC\n")
            self.assertEqual(result.stderr, b"")

    def test_digest_mismatch_cannot_reach_exec(self):
        with patch("subprocess.run", side_effect=AssertionError("unexpected exec")):
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                run_probe(verified_image(self.build, "0" * 64))


if __name__ == "__main__":
    unittest.main()
