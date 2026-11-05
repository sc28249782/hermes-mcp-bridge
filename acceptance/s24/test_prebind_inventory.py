"""Synthetic private-file controls; no operator guest/credential/route evidence."""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import prebind_inventory as inventory


class InventoryControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "private"
        self.root.mkdir(mode=0o700)
        self.attempt = self.root / "r1-remaining-synthetic"
        self.attempt.mkdir(mode=0o700)
        self.executable = self.root / "fake-python"
        self.write(self.executable, b"\x7fELFsynthetic-not-executable", 0o700)
        self.python = str(self.root / "candidate/.venv/bin/python")
        Path(self.python).parent.mkdir(parents=True)
        Path(self.python).symlink_to(self.executable)
        client = b"synthetic client; not executed"
        peer = b"synthetic peer; not executed"
        manifest = b'{"synthetic":true}'
        self.write(self.root / "client/tunnel-client", client, 0o700)
        self.write(self.root / "peer/route_prebind.py", peer)
        self.write(self.root / "peer/discovery_manifest.json", manifest)
        for name, raw in (("CLIENT_SHA256", client), ("PEER_SHA256", peer),
                          ("MANIFEST_SHA256", manifest)):
            p = patch.object(inventory, name, hashlib.sha256(raw).hexdigest())
            p.start()
            self.addCleanup(p.stop)
        version = f"0.0.18+{inventory.VERSION_REF} (git sha: {inventory.VERSION_REF})\n"
        self.write(self.root / "inspection/version.stdout", version.encode())
        identity = {"argv_python": self.python, "real_executable": str(self.executable),
                    "executable_sha256": hashlib.sha256(self.executable.read_bytes()).hexdigest(),
                    "is_venv": True, "python_version": "3.14.4"}
        self.write(self.root / "inspection-continuation/python.stdout", json.dumps(identity).encode())
        deps = {"is_venv": True, "python_version": "3.14.4", "distributions": [
            {"name": n, "version": v} for n, v in (
                ("mcp", "1.30.0"), ("httpx", "0.28.1"),
                ("python-dotenv", "1.2.3"), ("PyYAML", "6.0.3"))]}
        self.write(self.attempt / "dependencies.json", json.dumps(deps).encode())
        self.profile = {
            "config_version": 1,
            "control_plane": {"base_url": "https://api.openai.com",
                              "tunnel_id": "tunnel_" + "a" * 32,
                              "api_key": "env:S24_PREBIND_RUNTIME_KEY"},
            "health": {"listen_addr": "127.0.0.1:18081"},
            "admin_ui": {"open_browser": False}, "log": {"level": "info", "format": "json"},
            "mcp": {"max_concurrent_requests": 1, "stdio_send_initialized_notification": True,
                    "commands": [{"channel": "main", "command":
                        f"{self.python} -I -B {self.root}/peer/route_prebind.py --metadata-only"}]}}
        self.write_profile()
        self.write(self.root / "runtime-api-key", b"SYNTHETIC_SECRET_SENTINEL_DO_NOT_READ\n")
        self.system = {
            "/sys/class/dmi/id/product_name": "VMware synthetic unit fixture\n",
            "/proc/meminfo": "MemAvailable: 1048576 kB\n",
            "/proc/net/tcp": "header\n", "/proc/net/tcp6": "header\n",
            "/proc/self/cgroup": "0::/synthetic-unit-only\n"}

    @staticmethod
    def write(path, raw, mode=0o600):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(mode)

    def write_profile(self):
        self.write(self.attempt / "profile.yaml", json.dumps(self.profile).encode())

    def collect(self, **kwargs):
        return inventory.collect(str(self.root), self.attempt.name, self.python,
                                 health_port=18081, system_read=self.system.__getitem__, **kwargs)

    def test_success_never_opens_key_or_spawns_or_connects(self):
        original = os.open
        seen = []

        def guarded(path, *args, **kwargs):
            seen.append(os.fspath(path))
            self.assertNotEqual(Path(path).name, "runtime-api-key")
            return original(path, *args, **kwargs)

        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        with patch.object(os, "open", side_effect=guarded), \
                patch.object(subprocess, "Popen", side_effect=AssertionError("spawn forbidden")), \
                patch.object(socket, "socket", side_effect=AssertionError("socket forbidden")):
            report = self.collect()
        self.assertTrue(seen)
        for name in inventory.FALSE_FLAGS:
            self.assertIs(report[name], False)
        self.assertTrue(report["saved_dependencies_only"])
        self.assertNotIn("SYNTHETIC_SECRET_SENTINEL", json.dumps(report))
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*")))

    def test_private_exclusive_record_and_no_secret_projection(self):
        report = self.collect()
        sha = inventory.record(report)
        output = self.attempt / inventory.OUTPUT_NAME
        self.assertEqual(sha, hashlib.sha256(output.read_bytes()).hexdigest())
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
        self.assertNotIn(b"SYNTHETIC_SECRET_SENTINEL", output.read_bytes())
        original = output.read_bytes()
        with self.assertRaises(FileExistsError):
            inventory.record(report)
        with self.assertRaises(inventory.Hold):
            self.collect()
        self.assertEqual(original, output.read_bytes())

    def test_changed_pinned_inputs_rejected(self):
        for relative in ("client/tunnel-client", "peer/route_prebind.py", "peer/discovery_manifest.json"):
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(original + b"drift")
                with self.assertRaises(inventory.Hold):
                    self.collect()
                path.write_bytes(original)

    def test_profile_rejects_active_extra_channel_literal_key_and_bool(self):
        original = deepcopy(self.profile)
        changes = [
            lambda p: p["mcp"]["commands"][0].update(command="/synthetic/active"),
            lambda p: p["mcp"]["commands"].append({"channel": "extra", "command": "bad"}),
            lambda p: p["control_plane"].update(api_key="SYNTHETIC_SECRET_LITERAL"),
            lambda p: p.update(config_version=True),
            lambda p: p["mcp"].update(max_concurrent_requests=True),
            lambda p: p["control_plane"].update(base_url="https://invalid.example"),
        ]
        for change in changes:
            self.profile = deepcopy(original)
            change(self.profile)
            self.write_profile()
            with self.assertRaises(inventory.Hold):
                self.collect()
        self.profile = original

    def test_tunnel_syntax_plain_and_namespaced_and_invalid(self):
        for tunnel in ("tunnel_" + "a" * 32, "tunnel_ab12_" + "0" * 32):
            self.profile["control_plane"]["tunnel_id"] = tunnel
            self.write_profile()
            self.assertEqual(self.collect()["tunnel_id_syntax_only"], tunnel)
        self.profile["control_plane"]["tunnel_id"] = "tunnel_unknown"
        self.write_profile()
        with self.assertRaises(inventory.Hold):
            self.collect()

    def test_duplicate_json_nonfinite_and_oversized_profile_rejected(self):
        path = self.attempt / "profile.yaml"
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e400}', b"x" * 16385):
            path.write_bytes(raw)
            with self.assertRaises(inventory.Hold):
                self.collect()

    def test_key_symlink_hardlink_fifo_and_wrong_mode_rejected_without_open(self):
        key = self.root / "runtime-api-key"
        key.unlink()
        key.symlink_to(self.executable)
        with self.assertRaises(inventory.Hold):
            self.collect()
        key.unlink()
        os.link(self.executable, key)
        with self.assertRaises(inventory.Hold):
            self.collect()
        key.unlink()
        os.mkfifo(key, 0o600)
        with self.assertRaises(inventory.Hold):
            self.collect()
        key.unlink()
        self.write(key, b"synthetic", 0o644)
        with self.assertRaises(inventory.Hold):
            self.collect()

    def test_symlink_ancestors_and_attempt_and_output_rejected(self):
        alias = self.root.parent / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            inventory.collect(str(alias), self.attempt.name, self.python,
                              health_port=18081, system_read=self.system.__getitem__)
        attempt_alias = self.root / "r1-remaining-alias"
        attempt_alias.symlink_to(self.attempt, target_is_directory=True)
        with self.assertRaises(OSError):
            inventory.collect(str(self.root), attempt_alias.name, self.python,
                              health_port=18081, system_read=self.system.__getitem__)
        output = self.attempt / inventory.OUTPUT_NAME
        output.symlink_to(self.executable)
        with self.assertRaises(inventory.Hold):
            self.collect()

    def test_existing_output_checked_before_any_key_metadata(self):
        self.write(self.attempt / inventory.OUTPUT_NAME, b"preserve")
        with patch.object(inventory, "_file", side_effect=AssertionError("no read expected")):
            with self.assertRaisesRegex(inventory.Hold, "output_exists"):
                self.collect()

    def test_root_modes_paths_and_attempt_traversal_rejected(self):
        self.root.chmod(0o755)
        with self.assertRaises(inventory.Hold):
            self.collect()
        self.root.chmod(0o700)
        for attempt in ("../outside", "r1-remaining-a/b", "unknown"):
            with self.assertRaises(inventory.Hold):
                inventory.collect(str(self.root), attempt, self.python,
                                  health_port=18081, system_read=self.system.__getitem__)
        with self.assertRaises(inventory.Hold):
            inventory.collect(str(self.root), self.attempt.name, "/arbitrary/python",
                              health_port=18081, system_read=self.system.__getitem__)

    def test_python_resolution_or_content_drift_rejected(self):
        self.executable.write_bytes(b"\x7fELFchanged")
        with self.assertRaises(inventory.Hold):
            self.collect()

    def test_python_alias_to_key_is_rejected_before_secret_open(self):
        key = self.root / "runtime-api-key"
        Path(self.python).unlink()
        Path(self.python).symlink_to(key)
        identity_file = self.root / "inspection-continuation/python.stdout"
        data = json.loads(identity_file.read_bytes())
        data["real_executable"] = str(key)
        identity_file.write_text(json.dumps(data))
        original = os.open

        def guarded(path, *args, **kwargs):
            self.assertNotEqual(Path(path).name, "runtime-api-key")
            return original(path, *args, **kwargs)

        with patch.object(os, "open", side_effect=guarded):
            with self.assertRaisesRegex(inventory.Hold, "key_is_not_executable"):
                self.collect()

    def test_saved_dependency_drift_duplicate_or_version_mismatch_rejected(self):
        path = self.attempt / "dependencies.json"
        original = json.loads(path.read_bytes())
        for mode in ("duplicate", "version", "not_venv"):
            data = deepcopy(original)
            if mode == "duplicate":
                data["distributions"].append(data["distributions"][0])
            elif mode == "version":
                data["distributions"][0]["version"] = "0.0"
            else:
                data["is_venv"] = False
            path.write_text(json.dumps(data))
            with self.assertRaises(inventory.Hold):
                self.collect()

    def test_missing_system_observation_low_resources_and_port_occupied(self):
        original = dict(self.system)
        variants = [
            ("/sys/class/dmi/id/product_name", "not-vmware"),
            ("/proc/meminfo", "MemAvailable: 786431 kB\n"),
            ("/proc/meminfo", "MemAvailable: 1 MB\n"),
            ("/proc/net/tcp", "header\n0: 0100007F:46A1 00000000:0000\n"),
        ]
        for path, value in variants:
            self.system = dict(original)
            self.system[path] = value
            with self.assertRaises(inventory.Hold):
                self.collect()
        self.system = dict(original)
        self.system.pop("/proc/self/cgroup")
        with self.assertRaises(KeyError):
            self.collect()
        self.system = original
        with patch.object(os, "fstatvfs", return_value=type("FS", (), {"f_bavail": 0, "f_frsize": 4096})()):
            with self.assertRaises(inventory.Hold):
                self.collect()

    def test_clock_expiry_is_rejection_not_scope_extension(self):
        ticks = iter((0, 31))
        with self.assertRaisesRegex(inventory.Hold, "inventory_time"):
            self.collect(clock=lambda: next(ticks))

    def test_unreadable_observation_does_not_write_or_invent_partial_success(self):
        with patch.object(inventory, "_private_dir", wraps=inventory._private_dir):
            def unreadable(path):
                raise PermissionError("synthetic private detail")
            with self.assertRaises(PermissionError):
                inventory.collect(str(self.root), self.attempt.name, self.python,
                                  health_port=18081, system_read=unreadable)
        self.assertFalse((self.attempt / inventory.OUTPUT_NAME).exists())

    def test_private_health_port_nomination_must_match_profile(self):
        for port in (True, 0, 65536, "18081", 18082):
            with self.subTest(port=port), self.assertRaises(inventory.Hold):
                inventory.collect(str(self.root), self.attempt.name, self.python,
                                  health_port=port, system_read=self.system.__getitem__)

    def test_wrong_guest_architecture_rejected_before_file_reads(self):
        uname = os.uname_result(("Linux", "synthetic", "unit", "unit", "aarch64"))
        with patch.object(os, "uname", return_value=uname), \
                patch.object(inventory, "_open_dir", side_effect=AssertionError("no file read")):
            with self.assertRaisesRegex(inventory.Hold, "guest_architecture"):
                self.collect()

    def test_read_detects_opened_file_identity_change(self):
        original = os.fstat

        def changed(fd):
            info = original(fd)
            if stat.S_ISREG(info.st_mode):
                class Changed:
                    def __getattr__(self, name):
                        return info.st_ino + 1 if name == "st_ino" else getattr(info, name)
                return Changed()
            return info

        with patch.object(os, "fstat", side_effect=changed):
            with self.assertRaisesRegex(inventory.Hold, "file_changed"):
                self.collect()

    def test_changed_directory_and_forged_scope_flags_rejected(self):
        report = self.collect()
        for name in inventory.FALSE_FLAGS:
            changed = deepcopy(report)
            changed[name] = True
            with self.assertRaisesRegex(inventory.Hold, "report_scope"):
                inventory.record(changed)
        moved = self.root / "old-attempt"
        self.attempt.rename(moved)
        self.attempt.mkdir(mode=0o700)
        with self.assertRaisesRegex(inventory.Hold, "directory_changed"):
            inventory.record(report)
        self.assertFalse((self.attempt / inventory.OUTPUT_NAME).exists())

    def test_write_failure_preserves_partial_without_success(self):
        report = self.collect()
        real_write = os.write
        calls = []

        def fail_after_partial(fd, data):
            calls.append(1)
            if len(calls) == 1:
                return real_write(fd, data[:12])
            raise OSError("synthetic detail must not be public")

        with patch.object(os, "write", side_effect=fail_after_partial):
            with self.assertRaises(OSError):
                inventory.record(report)
        self.assertEqual((self.attempt / inventory.OUTPUT_NAME).stat().st_size, 12)
        with self.assertRaises(inventory.Hold):
            self.collect()

    def test_cli_failures_print_no_private_input(self):
        for argv in (("tool", "--secret=SYNTHETIC_SECRET_LITERAL"), ("tool",)):
            with patch.object(sys, "argv", list(argv)), \
                    patch.object(sys, "stderr", new_callable=io.StringIO) as stderr:
                self.assertEqual(inventory.main(), 2)
                self.assertEqual(stderr.getvalue(),
                    "HOLD: private inventory incomplete; preserve files; no automatic retry.\n")


if __name__ == "__main__":
    unittest.main()
