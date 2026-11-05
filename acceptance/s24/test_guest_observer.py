"""Resource controls: fabricated proc inputs are unit data, never guest evidence."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from parent_contract import Hold
import guest_observer as observer


class GuestControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.logs = self.root / "logs"
        self.logs.mkdir(mode=0o700)

    def tearDown(self):
        self.tmp.cleanup()

    def unit_observer(self):
        # Explicit unit injection; no claim that the real proc namespace was accepted.
        with patch.object(observer, "coherent_procfs"):
            return observer.GuestObserver(self.root, self.logs)

    def unit_sample(self, instance):
        with patch.object(observer, "coherent_procfs"), \
                patch.object(observer, "account_rss", return_value=(10 * observer.MIB, 2, "unit-membership")):
            return instance.sample()

    def test_actual_kernel_self_identity_memory_and_rss(self):
        # This positive platform test fails in the known incoherent development container.
        observer.coherent_procfs()
        fd = os.open("/proc/self", os.O_RDONLY | os.O_DIRECTORY)
        try:
            stamp = observer.process_stamp(observer.read_at(fd, "stat"))
        finally:
            os.close(fd)
        self.assertEqual(stamp[0], os.getpid())
        self.assertGreater(observer.process_rss(stamp), 0)
        fd = os.open("/proc", os.O_RDONLY | os.O_DIRECTORY)
        try:
            self.assertGreater(observer.available_memory(observer.read_at(fd, "meminfo")), 0)
        finally:
            os.close(fd)

    def test_memory_parser_rejects_missing_duplicate_units_and_over_total(self):
        self.assertEqual(observer.available_memory(b"MemTotal: 20 kB\nMemAvailable: 10 kB\n"), 10240)
        for raw in (b"MemTotal: 20 kB\n", b"MemTotal: 20 kB\nMemAvailable: 21 kB\n",
                    b"MemTotal: 20 kB\nMemAvailable: 1 MB\n",
                    b"MemTotal: 20 kB\nMemAvailable: 1 kB\nMemAvailable: 1 kB\n",
                    b"MemTotal: 20 kB\nMemAvailable: -1 kB\n"):
            with self.subTest(raw=raw), self.assertRaises(Hold):
                observer.available_memory(raw)

    def test_process_and_rss_parsers_handle_comm_parentheses(self):
        raw = b"7 (test ) name) S " + b"0 " * 18 + b"123\n"
        self.assertEqual(observer.process_stamp(raw), (7, 123))
        self.assertEqual(observer.resident_bytes(b"9 3 1 2 0 1 0\n", 4096), 12288)
        for raw in (b"9 3\n", b"9 -3 1 2 0 1 0", b"9 NaN 1 2 0 1 0"):
            with self.assertRaises(Hold):
                observer.resident_bytes(raw, 4096)
        with self.assertRaises(Hold):
            observer.resident_bytes(b"9 3 1 2 0 1 0", True)
        with self.assertRaises(Hold):
            observer.process_stamp(b"malformed")

    def test_real_filesystem_measurements_and_explicit_incomplete_scope(self):
        instance = self.unit_observer()
        payload = b"x" * 8192
        (self.logs / "trace").write_bytes(payload)
        sample = self.unit_sample(instance)
        self.assertEqual(sample["logs_logical_bytes"], len(payload))
        self.assertGreaterEqual(sample["workspace_growth_bytes"], len(payload))
        self.assertGreater(sample["disk_available_bytes"], 0)
        self.assertFalse(sample["host_observed"])
        self.assertFalse(sample["complete_writer_coverage"])
        self.assertFalse(sample["full_checkpoint_pass"])
        self.assertEqual(sample["evidence_class"], observer.EVIDENCE_CLASS)

    def test_links_and_special_files_hold_without_retry(self):
        for kind in ("symlink", "hardlink", "fifo"):
            with self.subTest(kind=kind):
                instance = self.unit_observer()
                target = self.root / "unsupported"
                if kind == "symlink":
                    target.symlink_to("/unobserved-target")
                elif kind == "hardlink":
                    source = self.root / "source"
                    source.write_text("unit")
                    target.hardlink_to(source)
                else:
                    os.mkfifo(target)
                with self.assertRaises(Hold):
                    self.unit_sample(instance)
                target.unlink()
                if kind == "hardlink":
                    source.unlink()
                with self.assertRaisesRegex(Hold, "closed"):
                    self.unit_sample(instance)

    def test_root_replacement_or_public_mode_is_rejected(self):
        instance = self.unit_observer()
        self.logs.rename(self.root / "oldlogs")
        self.logs.mkdir(mode=0o700)
        with self.assertRaises(Hold):
            self.unit_sample(instance)
        instance = self.unit_observer()
        self.root.chmod(0o755)
        with self.assertRaises(Hold):
            self.unit_sample(instance)
        self.root.chmod(0o700)

    def test_membership_churn_and_rss_identity_failure_hold(self):
        with patch.object(observer, "account_ids", side_effect=[{(1, 2)}, {(1, 3)}]), \
                patch.object(observer, "process_rss", return_value=100):
            with self.assertRaisesRegex(Hold, "membership changed"):
                observer.account_rss()
        instance = self.unit_observer()
        with patch.object(observer, "coherent_procfs"), \
                patch.object(observer, "account_rss", side_effect=PermissionError("unit unreadable")):
            with self.assertRaises(PermissionError):
                instance.sample()
        with self.assertRaisesRegex(Hold, "closed"):
            self.unit_sample(instance)

    def test_stable_synthetic_account_is_sum_of_all_members(self):
        with patch.object(observer, "account_ids", return_value={(2, 20), (3, 30)}), \
                patch.object(observer, "process_rss", side_effect=lambda stamp: stamp[0] * 100):
            total, count, digest = observer.account_rss()
        self.assertEqual((total, count), (500, 2))
        self.assertEqual(len(digest), 64)

    def test_late_sample_is_not_returned_or_retried(self):
        instance = self.unit_observer()
        with patch.object(observer.time, "monotonic", side_effect=[10, 12]):
            with self.assertRaisesRegex(Hold, "late"):
                self.unit_sample(instance)
        with self.assertRaisesRegex(Hold, "closed"):
            self.unit_sample(instance)

    def test_tree_count_and_depth_limits_are_fail_closed(self):
        with patch.object(observer, "MAX_PROCESSES", 0):
            with self.assertRaisesRegex(Hold, "process scan limit"):
                observer.account_ids()
        (self.logs / "a").write_text("a")
        instance = self.unit_observer()
        with patch.object(observer, "MAX_ENTRIES", 1):
            with self.assertRaisesRegex(Hold, "entry limit"):
                self.unit_sample(instance)
        instance = self.unit_observer()
        with patch.object(observer, "MAX_DEPTH", 0):
            with self.assertRaisesRegex(Hold, "depth"):
                self.unit_sample(instance)

    def test_guest_thresholds_reject_each_breach_and_boolean(self):
        good = {"guest_available_bytes": 768 * observer.MIB,
                "account_rss_sampled_bytes": 768 * observer.MIB,
                "disk_available_bytes": 2048 * observer.MIB,
                "workspace_growth_bytes": 2048 * observer.MIB,
                "logs_logical_bytes": 128 * observer.MIB}
        self.assertEqual(observer.guest_limit_failures(good), [])
        for key in good:
            value = good[key] - 1 if key in ("guest_available_bytes", "disk_available_bytes") else good[key] + 1
            with self.subTest(key=key):
                self.assertEqual(observer.guest_limit_failures({**good, key: value}), [key])
                with self.assertRaises(Hold):
                    observer.guest_limit_failures({**good, key: True})

    def test_namespace_mismatch_prevents_root_or_account_sampling(self):
        with patch.object(observer, "process_stamp", return_value=(0, 1)), \
                patch.object(observer, "private_root", side_effect=AssertionError("must not inspect roots")), \
                patch.object(observer, "account_rss", side_effect=AssertionError("must not inspect account")):
            with self.assertRaisesRegex(Hold, "namespace mismatch"):
                observer.GuestObserver(self.root, self.logs)


if __name__ == "__main__":
    unittest.main()
