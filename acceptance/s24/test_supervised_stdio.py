"""Linux supervisor controls use only new disposable fixture/owner processes."""
import argparse
import asyncio
from contextlib import contextmanager
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import supervised_stdio as supervised
from parent_contract import Hold, encode
import s24_fixture as fixture

CANDIDATE = None


class SupervisorChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="s24-super-")
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)

    def tearDown(self):
        self.tmp.cleanup()

    def argv(self):
        return [sys.executable, "-B", str(Path(fixture.__file__).resolve()), "serve",
                "--candidate", str(CANDIDATE), "--state", str(self.root / "state")]

    def test_rpc_gate_allows_only_fixture_protocol_and_rejects_duplicates(self):
        gate = supervised.RpcGate()
        for value in ({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}},
                      {"jsonrpc": "2.0", "method": "notifications/initialized"},
                      {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                      {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "bridge_version"}}):
            gate.accept(encode(value))
        for value in ({"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                      {"jsonrpc": "2.0", "id": True, "method": "tools/list"},
                      {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "hands_write_file"}},
                      {"jsonrpc": "2.0", "id": 3, "method": "resources/read"}):
            with self.assertRaises(Hold):
                gate.accept(encode(value))

    def test_rpc_before_initialization_and_duplicate_initialize_are_rejected(self):
        gate = supervised.RpcGate()
        with self.assertRaises(Hold):
            gate.accept(encode({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))
        gate.accept(encode({"jsonrpc": "2.0", "id": 2, "method": "initialize"}))
        with self.assertRaises(Hold):
            gate.accept(encode({"jsonrpc": "2.0", "id": 3, "method": "initialize"}))

    def test_private_evidence_is_exclusive_and_symlink_not_followed(self):
        supervised.private_json(self.root, "unit.json", {"unit": 1})
        self.assertEqual(supervised.read_private(self.root, "unit.json"), {"unit": 1})
        self.assertEqual((self.root / "unit.json").stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError):
            supervised.private_json(self.root, "unit.json", {"unit": 2})
        (self.root / "alias.json").symlink_to(self.root / "unit.json")
        with self.assertRaises(OSError):
            supervised.read_private(self.root, "alias.json")

    def test_parent_change_before_or_after_arming_is_rejected_without_numeric_signal(self):
        with patch.object(supervised.os, "getppid", return_value=101), \
                patch.object(supervised.ctypes, "CDLL", side_effect=AssertionError("must not arm")):
            with self.assertRaises(Hold):
                supervised.arm_parent_death(102)
        libc = Mock()
        libc.prctl.return_value = 0
        with patch.object(supervised.os, "getppid", side_effect=[101, 102]), \
                patch.object(supervised.ctypes, "CDLL", return_value=libc):
            with self.assertRaises(Hold):
                supervised.arm_parent_death(101)
        libc.prctl.assert_called_once_with(1, signal.SIGTERM, 0, 0, 0)

    def test_occupied_target_and_boolean_bound_fail_before_launch(self):
        factory = supervised.SupervisedSdkFactory(self.root, lease=True)
        with self.assertRaises(Hold):
            factory.prepare(time.monotonic() + 10)
        (self.root / supervised.CONTROL_NAME).write_bytes(b"unit-retained")
        factory = supervised.SupervisedSdkFactory(self.root)
        with self.assertRaises(Hold):
            factory.prepare(time.monotonic() + 10)
        self.assertFalse(factory.used)
        self.assertEqual((self.root / supervised.CONTROL_NAME).read_bytes(), b"unit-retained")

    def test_factory_requires_preparation_and_fixed_fixture_argv(self):
        async def run():
            factory = supervised.SupervisedSdkFactory(self.root)
            with self.assertRaises(Hold):
                async with factory(self.argv()):
                    self.fail("must not launch")
            factory.prepare(time.monotonic() + 10)
            with self.assertRaises(Hold):
                async with factory(["/bin/sh", "-c", "false"]):
                    self.fail("must not launch")
        asyncio.run(run())

    def test_actual_supervised_sdk_identity_and_stop_receipt(self):
        async def run():
            factory = supervised.SupervisedSdkFactory(self.root, term_grace=1, allow_kill=True)
            factory.prepare(time.monotonic() + 20)
            async with factory(self.argv()) as session:
                self.assertEqual((await session.call_tool("bridge_version", {})).structuredContent["version"], "1.2.8")
                self.assertEqual(len((await session.list_tools()).tools), 27)
                child_fd = os.pidfd_open(factory.ready["child"]["pid"])
            try:
                self.assertTrue(select.select([child_fd], [], [], 2)[0])
            finally:
                os.close(child_fd)
            self.assertEqual(factory.stop_receipt["reason"], "controller_stop")
            self.assertTrue(factory.stop_receipt["leader"]["leader_reaped"])
            self.assertFalse(factory.stop_receipt["cohort_coverage_proved"])
            self.assertTrue((self.root / supervised.CONTROL_NAME).exists())
            self.assertEqual(supervised.read_private(self.root, "supervisor-stop.json"), factory.stop_receipt)
        asyncio.run(run())

    @contextmanager
    def owner(self, *, window=20, lease=5):
        code = '''import asyncio, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from supervised_stdio import SupervisedSdkFactory
import s24_fixture as fixture
async def run():
    root, candidate = Path(sys.argv[2]), Path(sys.argv[3])
    factory = SupervisedSdkFactory(root, lease=float(sys.argv[5]), term_grace=1, allow_kill=True)
    factory.prepare(time.monotonic()+float(sys.argv[4]))
    argv=[sys.executable,"-B",str(Path(fixture.__file__).resolve()),"serve","--candidate",str(candidate),"--state",str(root/"state")]
    async with factory(argv) as session:
        await session.call_tool("bridge_version", {})
        print("OWNER_READY",flush=True)
        await asyncio.Event().wait()
asyncio.run(run())
'''
        proc = subprocess.Popen([sys.executable, "-I", "-B", "-c", code,
            str(Path(supervised.__file__).parent), str(self.root), str(CANDIDATE), str(window), str(lease)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        owner_fd = os.pidfd_open(proc.pid)
        other_fds = []
        try:
            require_ready = select.select([proc.stdout.fileno()], [], [], 10)[0]
            self.assertTrue(require_ready, "disposable owner startup timeout")
            line = proc.stdout.readline()
            self.assertEqual(line, b"OWNER_READY\n", "owner did not establish supervised fixture")
            ready = supervised.read_private(self.root, "supervisor-ready.json")
            child_fd = os.pidfd_open(ready["child"]["pid"])
            outer_fd = os.pidfd_open(ready["supervisor"]["pid"])
            other_fds.extend((child_fd, outer_fd))
            yield proc, owner_fd, child_fd, outer_fd
        finally:
            if proc.poll() is None:
                signal.pidfd_send_signal(owner_fd, signal.SIGKILL)
            proc.communicate(timeout=5)
            for fd in other_fds:
                os.close(fd)
            os.close(owner_fd)

    def test_owner_death_stops_fixture_from_independent_supervisor(self):
        with self.owner() as (proc, owner_fd, child_fd, outer_fd):
            signal.pidfd_send_signal(owner_fd, signal.SIGKILL)
            proc.wait(timeout=3)
            self.assertTrue(select.select([child_fd], [], [], 4)[0], "fixture stayed alive after owner death")
            self.assertTrue(select.select([outer_fd], [], [], 4)[0], "supervisor did not finish")
            receipt = supervised.read_private(self.root, "supervisor-stop.json")
            self.assertIn(receipt["reason"], ("owner_lost", "controller_eof"))
            self.assertTrue(receipt["leader"]["leader_reaped"])

    def test_lease_expiry_stops_fixture_while_owner_is_still_alive(self):
        with self.owner(lease=1.5) as (proc, owner_fd, child_fd, outer_fd):
            self.assertTrue(select.select([child_fd], [], [], 4)[0], "lease did not stop fixture")
            self.assertFalse(select.select([owner_fd], [], [], 0)[0])
            self.assertTrue(select.select([outer_fd], [], [], 3)[0])
            self.assertEqual(supervised.read_private(self.root, "supervisor-stop.json")["reason"], "lease_expired")

    def test_window_expiry_is_not_extended_by_control_activity(self):
        with self.owner(window=3, lease=5) as (proc, owner_fd, child_fd, outer_fd):
            self.assertTrue(select.select([child_fd], [], [], 5)[0])
            self.assertFalse(select.select([owner_fd], [], [], 0)[0])
            self.assertTrue(select.select([outer_fd], [], [], 3)[0])
            self.assertEqual(supervised.read_private(self.root, "supervisor-stop.json")["reason"], "window_expired")

    def test_supervisor_kill_uses_kernel_parent_death_signal_but_no_success_receipt(self):
        with self.owner() as (proc, owner_fd, child_fd, outer_fd):
            signal.pidfd_send_signal(outer_fd, signal.SIGKILL)
            self.assertTrue(select.select([child_fd], [], [], 3)[0], "fixture did not terminate after supervisor kill")
            self.assertFalse((self.root / "supervisor-stop.json").exists())
            self.assertFalse(select.select([owner_fd], [], [], 0)[0])

    def test_same_uid_different_process_cannot_renew_owner_lease(self):
        with self.owner() as (proc, owner_fd, child_fd, outer_fd):
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as peer:
                peer.settimeout(1)
                peer.connect(str(self.root / supervised.CONTROL_NAME))
                try:
                    peer.sendall(encode({"seq": 2, "op": "renew"}))
                    self.assertEqual(peer.recv(1024), b"")
                except ConnectionResetError:
                    pass
            self.assertTrue(select.select([child_fd], [], [], 3)[0])
            self.assertTrue(select.select([outer_fd], [], [], 3)[0])
            self.assertFalse((self.root / "supervisor-stop.json").exists())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    args, rest = parser.parse_known_args()
    CANDIDATE = fixture.verify_candidate(args.candidate)
    unittest.main(argv=[sys.argv[0], *rest])
