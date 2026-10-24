"""Only newly created test children are controlled; no original runtime access."""
import argparse
import base64
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from parent_contract import Hold
import owned_child as control
import s24_fixture as fixture

CANDIDATE = None
ECHO = "import sys; print('READY',flush=True)\nfor line in sys.stdin: print(line.rstrip(),flush=True)"
STUBBORN = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('READY',flush=True); time.sleep(60)"


class ChildControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.children = []
        self.controls = []

    def tearDown(self):
        for item in self.controls:
            try:
                item.close()
            except Hold:
                pass
        for proc in self.children:
            if proc.poll() is None:
                fd = os.pidfd_open(proc.pid)
                try:
                    signal.pidfd_send_signal(fd, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                finally:
                    os.close(fd)
            proc.wait(timeout=3)
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                stream.close()
        self.tmp.cleanup()

    def spawn(self, script=ECHO):
        argv = [sys.executable, "-I", "-u", "-c", script]
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env={"PYTHONDONTWRITEBYTECODE": "1"})
        self.children.append(proc)
        return proc, argv

    def adopt(self, proc, argv, **kwargs):
        kwargs.setdefault("term_grace", 0.1)  # Small grace only for new offline test children.
        item = control.OwnedChild(proc, argv, self.root / (str(len(self.controls)) + ".jsonl"), **kwargs)
        self.controls.append(item)
        return item

    def records(self):
        rows = [json.loads(line) for line in (self.root / "0.jsonl").read_bytes().splitlines()]
        return {key: b"".join(base64.b64decode(r["data_base64"]) for r in rows if r["direction"] == key)
                for key in ("stdout", "stderr", "stdin_intent", "stdin_written")}

    def test_actual_bytes_trace_private_and_leader_reaped(self):
        proc, argv = self.spawn()
        item = self.adopt(proc, argv)
        self.assertEqual(item.readline(), b"READY\n")
        raw = b'{"marker":"offline"}\n'
        item.send(raw)
        self.assertEqual(item.readline(), raw)
        result = item.close()
        self.assertTrue(result["leader_reaped"])
        self.assertFalse(result["descendant_cessation_proved"])
        records = self.records()
        self.assertEqual(records["stdout"], b"READY\n" + raw)
        self.assertEqual(records["stdin_intent"], raw)
        self.assertEqual(records["stdin_written"], raw)
        self.assertEqual((self.root / "0.jsonl").stat().st_mode & 0o777, 0o600)
        self.assertEqual(item.identity["pid"], proc.pid)
        with self.assertRaises(Hold):
            item.send(raw)

    def test_lease_expires_without_reader_polling(self):
        proc, argv = self.spawn()
        item = self.adopt(proc, argv, lease=0.25, window=2, term_grace=0.1, allow_kill=True)
        self.assertEqual(item.readline(), b"READY\n")
        self.assertTrue(item.finished.wait(2))
        self.assertEqual(item.reason, "lease_expired")
        self.assertTrue(item.close()["leader_reaped"])

    def test_renewal_cannot_extend_absolute_window(self):
        proc, argv = self.spawn()
        item = self.adopt(proc, argv, lease=0.3, window=0.5, term_grace=0.1, allow_kill=True)
        item.readline()
        deadline = item.deadline
        while not item.finished.wait(0.04):
            try:
                item.renew()
            except Hold:
                pass
        self.assertEqual(item.deadline, deadline)
        self.assertEqual(item.reason, "window_expired")
        item.close()

    def test_term_then_opted_in_kill_only_adopted_pidfd(self):
        proc, argv = self.spawn(STUBBORN)
        other, _ = self.spawn()
        item = self.adopt(proc, argv, lease=1, window=2, term_grace=0.1, allow_kill=True)
        item.readline()
        item.stop("parent_lost")
        result = item.close()
        self.assertEqual(result["signals"], [signal.SIGTERM, signal.SIGKILL])
        self.assertEqual(proc.returncode, -signal.SIGKILL)
        self.assertIsNone(other.poll())

    def test_without_kill_stop_stays_unconfirmed(self):
        proc, argv = self.spawn(STUBBORN)
        item = self.adopt(proc, argv, lease=1, window=2, term_grace=0.05)
        item.readline()
        item.stop("observation_failed")
        self.assertTrue(item.finished.wait(2))
        with self.assertRaisesRegex(Hold, "unconfirmed"):
            item.close()
        self.assertEqual(item.signals, [signal.SIGTERM])
        self.assertIsNone(proc.poll())
        # Owner retains the exact pidfd for explicit test-only cleanup.
        signal.pidfd_send_signal(item.pidfd, signal.SIGKILL)
        proc.wait(timeout=2)
        item.close()

    def test_mismatched_argv_or_nonchild_cannot_be_adopted(self):
        proc, argv = self.spawn()
        with self.assertRaises(Hold):
            self.adopt(proc, argv + ["unexpected"])
        with patch("os.waitid", side_effect=ChildProcessError("not owned")):
            with self.assertRaises(ChildProcessError):
                self.adopt(proc, argv)
        self.assertIsNone(proc.poll())

    def test_existing_trace_is_never_overwritten(self):
        proc, argv = self.spawn()
        target = self.root / "0.jsonl"
        target.write_bytes(b"preserve\n")
        with self.assertRaises(FileExistsError):
            self.adopt(proc, argv)
        self.assertEqual(target.read_bytes(), b"preserve\n")
        self.assertIsNone(proc.poll())

    def test_bad_window_boolean_and_public_trace_parent_rejected(self):
        proc, argv = self.spawn()
        with self.assertRaises(Hold):
            self.adopt(proc, argv, window=True)
        with patch.object(proc, "text_mode", True):
            with self.assertRaisesRegex(Hold, "binary pipes"):
                self.adopt(proc, argv)
        public = self.root / "public"
        public.mkdir(mode=0o755)
        public.chmod(0o755)
        with self.assertRaises(Hold):
            control.OwnedChild(proc, argv, public / "trace")
        self.assertIsNone(proc.poll())

    def test_thread_start_failure_leaves_cleanup_with_owner(self):
        proc, argv = self.spawn()
        with patch("threading.Thread.start", side_effect=RuntimeError("thread unavailable")), \
                patch("signal.pidfd_send_signal", side_effect=AssertionError("must not signal")):
            with self.assertRaisesRegex(RuntimeError, "thread unavailable"):
                self.adopt(proc, argv)
        self.assertIsNone(proc.poll())

    def test_output_frame_and_trace_overflow_stop_child(self):
        for trace_overflow in (True, False):
            with self.subTest(trace_overflow=trace_overflow):
                proc, argv = self.spawn("import sys; print('READY',flush=True)\nfor line in sys.stdin: print('x'*200,flush=True)")
                item = self.adopt(proc, argv, term_grace=0.1, allow_kill=True)
                item.readline()
                with patch.object(control, "TRACE_LIMIT" if trace_overflow else "FRAME_LIMIT", 100):
                    try:
                        item.send(b"emit\n")
                    except Hold:
                        pass
                    self.assertTrue(item.finished.wait(2))
                self.assertIsNotNone(item.reason)
                self.assertTrue(item.close()["leader_reaped"])

    def test_incoherent_procfs_fails_before_adoption_or_signal(self):
        proc, argv = self.spawn()
        with patch("pathlib.Path.read_text", return_value="0 (test) S 0"), \
                patch("os.pidfd_open", side_effect=AssertionError("must not open target")), \
                patch("signal.pidfd_send_signal", side_effect=AssertionError("must not signal")):
            with self.assertRaisesRegex(Hold, "namespace mismatch"):
                self.adopt(proc, argv)
        self.assertIsNone(proc.poll())

    def test_identity_recheck_failure_prevents_term_and_kill(self):
        proc, argv = self.spawn(STUBBORN)
        item = self.adopt(proc, argv, term_grace=0.05, allow_kill=True)
        item.readline()
        with patch.object(item, "_identity_matches", return_value=False):
            item.stop("parent_lost")
            self.assertTrue(item.finished.wait(2))
        with self.assertRaises(Hold):
            item.close()
        self.assertEqual(item.signals, [])
        self.assertIsNone(proc.poll())
        signal.pidfd_send_signal(item.pidfd, signal.SIGKILL)
        proc.wait(timeout=2)
        item.close()

    def test_candidate_fixture_initialize_list_version_over_observed_pipes(self):
        from mcp.types import LATEST_PROTOCOL_VERSION
        argv = [sys.executable, "-B", str(Path(fixture.__file__).resolve()), "serve",
                "--candidate", str(CANDIDATE), "--state", str(self.root / "state")]
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env={"PYTHONDONTWRITEBYTECODE": "1"})
        self.children.append(proc)
        item = self.adopt(proc, argv, lease=5, window=10, term_grace=0.2, allow_kill=True)
        def send(value):
            item.send((json.dumps(value, separators=(",", ":")) + "\n").encode())
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": LATEST_PROTOCOL_VERSION, "capabilities": {},
            "clientInfo": {"name": "offline-control-test", "version": "1"}}})
        self.assertEqual(json.loads(item.readline())["id"], 1)
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        page = json.loads(item.readline())
        self.assertEqual(len(page["result"]["tools"]), 27)
        send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "bridge_version", "arguments": {}}})
        self.assertEqual(json.loads(item.readline())["result"]["structuredContent"]["version"], "1.2.8")
        item.close()
        records = self.records()
        replies = [json.loads(line) for line in records["stdout"].splitlines()]
        self.assertEqual([r["id"] for r in replies], [1, 2, 3])
        self.assertTrue(records["stderr"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    arguments, remaining = parser.parse_known_args()
    CANDIDATE = fixture.verify_candidate(arguments.candidate.resolve())
    unittest.main(argv=[sys.argv[0], *remaining])
