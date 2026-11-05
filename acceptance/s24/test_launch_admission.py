"""Offline controls with private temporary claims and disposable helper processes."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import launch_admission as admission
from parent_contract import Hold


class LaunchControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.options = dict(attempt_id="offline-attempt", binding_sha256="a" * 64,
                            candidate_commit="b" * 40, fixture_commit="c" * 40,
                            argv=[str(Path(sys.executable).resolve()), "-I", "-B", "-c", "pass"])

    def tearDown(self):
        self.tmp.cleanup()

    def claim(self, **updates):
        return admission.LaunchAdmission(self.root, **(self.options | updates))

    def helper(self, code):
        # No original process, route or fixture is targeted by these offline helpers.
        return subprocess.Popen([sys.executable, "-I", "-B", "-c", code,
                                 str(Path(admission.__file__).parent), str(self.root),
                                 json.dumps(self.options)], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_durable_reservation_precedes_one_exact_dispatch(self):
        events = []
        real_sync = os.fsync

        def sync(fd):
            events.append("sync")
            real_sync(fd)

        with patch.object(admission.os, "fsync", side_effect=sync):
            claim = self.claim()
        argv = self.options["argv"][:]
        self.options["argv"].append("mutated-after-reservation")

        def launch(actual):
            events.append("launch")
            self.assertEqual(actual, argv)
            actual.clear()
            return "offline-result"

        self.assertEqual(claim.dispatch_once(launch), "offline-result")
        self.assertEqual(events, ["sync", "sync", "launch"])
        with self.assertRaises(Hold):
            claim.dispatch_once(launch)
        record = json.loads((self.root / admission.CLAIM_NAME).read_bytes())
        self.assertEqual(record["argv"], argv)
        self.assertEqual(record["state"], "reserved-no-outcome")
        self.assertFalse(record["approval_authenticated"])
        self.assertFalse(record["writer_cessation_proved"])
        self.assertEqual((self.root / admission.CLAIM_NAME).stat().st_mode & 0o777, 0o600)

    def test_existing_claim_blocks_new_object_even_with_new_identifier_or_window(self):
        self.claim()
        for update in ({}, {"attempt_id": "different"}, {"window": 1}, {"binding_sha256": "d" * 64}):
            with self.subTest(update=update), self.assertRaises(Hold):
                self.claim(**update)

    def test_concurrent_dispatch_calls_invoke_only_one_callback(self):
        claim = self.claim()
        entered, release = threading.Event(), threading.Event()
        calls = []

        def launch(argv):
            calls.append(argv)
            entered.set()
            self.assertTrue(release.wait(5))
            return "one"

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(claim.dispatch_once, launch)
            try:
                self.assertTrue(entered.wait(5))
                second = pool.submit(claim.dispatch_once, launch)
                with self.assertRaises(Hold):
                    second.result(timeout=5)
            finally:
                release.set()
            self.assertEqual(first.result(timeout=5), "one")
        self.assertEqual(len(calls), 1)

    def test_independent_processes_arbitrate_one_claim(self):
        code = '''import json, sys
sys.path.insert(0, sys.argv[1])
from launch_admission import LaunchAdmission, Hold
print("ready", flush=True)
sys.stdin.buffer.readline()
try:
    LaunchAdmission(sys.argv[2], **json.loads(sys.argv[3]))
except Hold:
    print("blocked", flush=True)
else:
    print("reserved", flush=True)
'''
        with self.helper(code) as first, self.helper(code) as second:
            self.assertEqual(first.stdout.readline(), b"ready\n")
            self.assertEqual(second.stdout.readline(), b"ready\n")
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda child: child.communicate(b"go\n", timeout=10),
                                        (first, second)))
            self.assertEqual(sorted(out.strip() for out, _ in results), [b"blocked", b"reserved"])
            self.assertTrue(all(not err for _, err in results))
            self.assertEqual([first.returncode, second.returncode], [0, 0])

    def test_process_exit_after_reservation_does_not_restore_admission(self):
        code = '''import json, os, sys
sys.path.insert(0, sys.argv[1])
from launch_admission import LaunchAdmission
LaunchAdmission(sys.argv[2], **json.loads(sys.argv[3]))
os._exit(0)
'''
        with self.helper(code) as child:
            out, err = child.communicate(timeout=10)
            self.assertEqual((child.returncode, out, err), (0, b"", b""))
        with self.assertRaises(Hold):
            self.claim()

    def test_copied_serialized_or_fork_inherited_object_cannot_dispatch(self):
        claim = self.claim()
        for clone in (copy.copy, copy.deepcopy, pickle.dumps):
            with self.subTest(clone=clone), self.assertRaises(Hold):
                clone(claim)
        # A separate private directory is only an offline test input, not new approval.
        other = self.root / "fork-helper"
        other.mkdir(mode=0o700)
        code = '''import json, os, sys
sys.path.insert(0, sys.argv[1])
from launch_admission import LaunchAdmission, Hold
claim = LaunchAdmission(os.path.join(sys.argv[2], "fork-helper"), **json.loads(sys.argv[3]))
pid = os.fork()
if pid == 0:
    try:
        claim.dispatch_once(lambda argv: None)
    except Hold:
        os._exit(3)
    os._exit(4)
_, status = os.waitpid(pid, 0)
assert os.waitstatus_to_exitcode(status) == 3
assert claim.dispatch_once(lambda argv: "creator-only") == "creator-only"
'''
        with self.helper(code) as child:
            out, err = child.communicate(timeout=10)
            self.assertEqual((child.returncode, out, err), (0, b"", b""))

    def test_callback_exception_never_retries_or_erases_claim(self):
        claim = self.claim()
        callback = Mock(side_effect=RuntimeError("offline launch uncertainty"))
        with self.assertRaises(RuntimeError):
            claim.dispatch_once(callback)
        with self.assertRaises(Hold):
            claim.dispatch_once(callback)
        self.assertEqual(callback.call_count, 1)
        with self.assertRaises(Hold):
            self.claim()

    def test_file_or_directory_sync_failure_preserves_blocking_marker(self):
        for fail_at in (1, 2):
            with self.subTest(fail_at=fail_at), tempfile.TemporaryDirectory(dir=self.root) as path:
                os.chmod(path, 0o700)
                calls = 0
                real_sync = os.fsync

                def sync(fd):
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        raise OSError("offline injected fsync failure")
                    real_sync(fd)

                with patch.object(admission.os, "fsync", side_effect=sync), self.assertRaises(Hold):
                    admission.LaunchAdmission(path, **self.options)
                self.assertTrue((Path(path) / admission.CLAIM_NAME).exists())
                with self.assertRaises(Hold):
                    admission.LaunchAdmission(path, **self.options)

    def test_partial_write_failure_is_not_recovered_and_short_writes_complete(self):
        real_write = os.write
        calls = 0

        def partial(fd, raw):
            nonlocal calls
            calls += 1
            if calls == 1:
                return real_write(fd, raw[:5])
            raise OSError("offline write failure")

        with patch.object(admission.os, "write", side_effect=partial), self.assertRaises(Hold):
            self.claim()
        self.assertEqual((self.root / admission.CLAIM_NAME).stat().st_size, 5)
        with self.assertRaises(Hold):
            self.claim()
        other = self.root / "short-writes"
        other.mkdir(mode=0o700)
        with patch.object(admission.os, "write", side_effect=lambda fd, raw: real_write(fd, raw[:7])):
            claim = admission.LaunchAdmission(other, **self.options)
        self.assertEqual(claim.dispatch_once(lambda argv: "short-write-complete"), "short-write-complete")

    def test_expired_window_or_invalid_callback_consumes_instance(self):
        with patch.object(admission.time, "monotonic", return_value=100):
            claim = self.claim(window=1)
        callback = Mock()
        with patch.object(admission.time, "monotonic", return_value=101), self.assertRaises(Hold):
            claim.dispatch_once(callback)
        with patch.object(admission.time, "monotonic", return_value=100), self.assertRaises(Hold):
            claim.dispatch_once(callback)
        callback.assert_not_called()
        with tempfile.TemporaryDirectory(dir=self.root) as path:
            os.chmod(path, 0o700)
            other = admission.LaunchAdmission(path, **self.options)
            with self.assertRaises(Hold):
                other.dispatch_once(None)
            with self.assertRaises(Hold):
                other.dispatch_once(callback)

    def test_changed_claim_bytes_inode_permissions_or_links_block_before_callback(self):
        for mutation in ("bytes", "inode", "permissions", "hardlink", "symlink", "fifo"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(dir=self.root) as path:
                os.chmod(path, 0o700)
                claim = admission.LaunchAdmission(path, **self.options)
                marker = Path(path) / admission.CLAIM_NAME
                if mutation == "bytes":
                    with marker.open("ab") as output:
                        output.write(b"x")
                elif mutation == "inode":
                    marker.rename(Path(path) / "old")
                    marker.write_bytes((Path(path) / "old").read_bytes())
                    marker.chmod(0o600)
                elif mutation == "permissions":
                    marker.chmod(0o644)
                elif mutation == "hardlink":
                    os.link(marker, Path(path) / "extra-link")
                else:
                    marker.rename(Path(path) / "old")
                    if mutation == "symlink":
                        marker.symlink_to(Path(path) / "old")
                    else:
                        os.mkfifo(marker, 0o600)
                callback = Mock()
                with self.assertRaises(Hold):
                    claim.dispatch_once(callback)
                callback.assert_not_called()
                with self.assertRaises(Hold):
                    claim.dispatch_once(callback)

    def test_replaced_attempt_directory_and_symlink_paths_rejected(self):
        path = self.root / "attempt"
        path.mkdir(mode=0o700)
        claim = admission.LaunchAdmission(path, **self.options)
        path.rename(self.root / "retained")
        path.mkdir(mode=0o700)
        callback = Mock()
        with self.assertRaises(Hold):
            claim.dispatch_once(callback)
        callback.assert_not_called()
        link = self.root / "alias"
        link.symlink_to(path, target_is_directory=True)
        with self.assertRaises(Hold):
            admission.LaunchAdmission(link, **self.options)
        path.chmod(0o755)
        with self.assertRaises(Hold):
            admission.LaunchAdmission(path, **self.options)

    def test_invalid_bindings_and_bounds_make_no_claim(self):
        for update in ({"attempt_id": "../escape"}, {"binding_sha256": "not-a-digest"},
                       {"candidate_commit": "main"}, {"fixture_commit": "x" * 40},
                       {"argv": []}, {"argv": ["relative"]}, {"argv": ["/bin/x", "a\0b"]},
                       {"argv": ["/bin/x", "a" * 4097]}, {"argv": ["/x"] * 33},
                       {"argv": ["/x"] + ["a" * 4096] * 4},
                       {"window": True}, {"window": 0}, {"window": 1201},
                       {"window": float("nan")}, {"window": float("inf")}):
            with self.subTest(update=update), self.assertRaises(Hold):
                self.claim(**update)
            self.assertFalse((self.root / admission.CLAIM_NAME).exists())


if __name__ == "__main__":
    unittest.main()
