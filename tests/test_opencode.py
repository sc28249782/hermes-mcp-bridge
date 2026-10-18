"""Fake-executable tests for the disabled-by-default OpenCode health adapter."""
from pathlib import Path
import asyncio
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bridge import server
from codex_core import CodexRunner
from config_schema import ConfigError, load_bridge_config
from contexts import ContextRegistry
from core import Bridge
from hands_core import HandsRuntime
from opencode_core import OpenCodeError, OpenCodeRunner
from test_bridge import FakeHermes

BASE_CONFIG = {"schema_version": 1, "api_url": "http://127.0.0.1:8642", "hermes_env": "x"}
MARKER_ENV = "OPENCODE_TEST_MARKER"
ARGV_ENV = "OPENCODE_TEST_ARGV"


def write_executable(path, body):
    path.write_text("#!/usr/bin/env python3\n" + body)
    path.chmod(0o700)
    return path


def set_test_env(**values):
    for key, value in values.items():
        os.environ[key] = str(value)


def clear_test_env():
    for key in (MARKER_ENV, ARGV_ENV):
        os.environ.pop(key, None)


def pid_gone(pid, deadline=15.0):
    """Wait until /proc no longer reports the PID as alive."""
    end = time.monotonic() + deadline
    while time.monotonic() < end:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        time.sleep(0.05)
    return False


class RecordingOrder:
    """Record opencode_core's killpg / Popen.wait / Popen.poll call order.

    killpg and Popen.wait are pass-through recorders: the real functions
    still run, so cleanup behavior is exercised for real while the ordering
    is captured. os.waitid is left real unless a test patches it separately,
    because the nonreaping observation must not be faked in ordering tests.
    """

    def __init__(self):
        self.events = []

    def __enter__(self):
        real = {"killpg": os.killpg, "wait": subprocess.Popen.wait, "poll": subprocess.Popen.poll}

        def rec_killpg(pgid, sig):
            self.events.append(("killpg", sig))
            return real["killpg"](pgid, sig)

        def rec_wait(*args, **kwargs):
            self.events.append(("wait",))
            return real["wait"](*args, **kwargs)

        def rec_poll(*args, **kwargs):
            self.events.append(("poll",))
            return real["poll"](*args, **kwargs)

        self._patches = [
            patch("opencode_core.os.killpg", rec_killpg),
            patch("subprocess.Popen.wait", rec_wait),
            patch("subprocess.Popen.poll", rec_poll),
        ]
        for target in self._patches:
            target.start()
        return self

    def __exit__(self, *exc):
        for target in reversed(self._patches):
            target.stop()
        return False

    def assert_single_reap_after_final_killpg(self, testcase):
        """Exactly TERM, KILL, then one reap; no wait/poll before the KILL."""
        reaps = [i for i, event in enumerate(self.events) if event[0] in ("wait", "poll")]
        kills = [i for i, event in enumerate(self.events) if event[0] == "killpg"]
        testcase.assertEqual([self.events[i] for i in kills],
                             [("killpg", signal.SIGTERM), ("killpg", signal.SIGKILL)])
        testcase.assertEqual(len(reaps), 1, f"expected one reap event, saw {self.events}")
        testcase.assertGreater(reaps[0], kills[-1],
                               f"leader reaped before the final killpg: {self.events}")


class TestOpenCodeConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def store(self, opencode):
        (self.root / "bridge-config.json").write_text(
            json.dumps({**BASE_CONFIG, "opencode": opencode}))

    def test_section_is_absent_by_default(self):
        (self.root / "bridge-config.json").write_text(json.dumps(BASE_CONFIG))
        config, warnings = load_bridge_config(self.root)
        self.assertNotIn("opencode", config)
        self.assertEqual(warnings, [])

    def test_unknown_key_is_warned_not_rejected(self):
        self.store({"enabled": False, "typo": 1})
        _, warnings = load_bridge_config(self.root)
        self.assertTrue(any("opencode.typo" in value for value in warnings))

    def test_invalid_forms_are_rejected(self):
        cases = [
            {"enabled": "yes"},
            {"enabled": True},
            {"enabled": True, "binary": "opencode"},
            {"enabled": True, "binary": ""},
            {"enabled": True, "binary": 7},
            {"enabled": True, "binary": "/tmp/x\n"},
            {"enabled": True, "binary": "/tmp/x\t"},
            {"enabled": True, "binary": "/tmp/x\x01"},
            {"enabled": True, "binary": "/tmp/x\x1b"},
            {"enabled": True, "binary": "/tmp/x\x7f"},
            {"enabled": True, "binary": "/tmp/x", "version_timeout_seconds": 0},
            {"enabled": True, "binary": "/tmp/x", "version_timeout_seconds": 121},
            {"enabled": True, "binary": "/tmp/x", "version_timeout_seconds": "10"},
            {"enabled": True, "binary": "/tmp/x", "max_output_bytes": 1023},
            {"enabled": True, "binary": "/tmp/x", "max_output_bytes": 1_048_577},
        ]
        for opencode in cases:
            with self.subTest(opencode=opencode):
                self.store(opencode)
                with self.assertRaises(ConfigError):
                    load_bridge_config(self.root)

    def test_valid_enabled_section_passes(self):
        self.store({"enabled": True, "binary": "/opt/opencode", "version_timeout_seconds": 5,
                    "max_output_bytes": 8192})
        config, warnings = load_bridge_config(self.root)
        self.assertEqual(config["opencode"]["binary"], "/opt/opencode")
        self.assertEqual(warnings, [])


class TestOpenCodeRunner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(clear_test_env)

    def tearDown(self):
        self.tmp.cleanup()

    def test_disabled_fails_closed_without_spawning(self):
        with patch("opencode_core.subprocess.Popen") as spawn:
            runner = OpenCodeRunner({"enabled": False, "binary": str(self.root / "missing")})
            with self.assertRaises(OpenCodeError):
                runner.health()
        spawn.assert_not_called()

    def test_absent_section_fails_closed(self):
        (self.root / "bridge-config.json").write_text(json.dumps(BASE_CONFIG))
        runner = OpenCodeRunner.from_config(self.root)
        self.assertFalse(runner.enabled)
        with self.assertRaises(OpenCodeError):
            runner.health()

    def test_enabled_requires_regular_executable(self):
        missing = self.root / "missing-opencode"
        with self.assertRaises(OpenCodeError):
            OpenCodeRunner({"enabled": True, "binary": str(missing)})
        directory = self.root / "directory"
        directory.mkdir()
        with self.assertRaises(OpenCodeError):
            OpenCodeRunner({"enabled": True, "binary": str(directory)})
        plain = self.root / "plain"
        plain.write_text("#!/usr/bin/env python3\n")
        plain.chmod(0o644)
        with self.assertRaises(OpenCodeError):
            OpenCodeRunner({"enabled": True, "binary": str(plain)})

    def test_valid_version_probe_reports_version_and_fixed_argv(self):
        marker = self.root / "argv.json"
        fake = write_executable(self.root / "fake-opencode",
                                "import json,os,sys\n"
                                f"open(os.environ['{ARGV_ENV}'],'w').write(json.dumps(sys.argv))\n"
                                "sys.stdout.write('2.0.32\\n')\n")
        set_test_env(**{ARGV_ENV: marker})
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake), "version_timeout_seconds": 5,
                                 "max_output_bytes": 4096})
        health = runner.health()
        self.assertTrue(health["ok"])
        self.assertEqual(health["version"], "2.0.32")
        self.assertEqual(health["enabled"], True)
        argv = json.loads(marker.read_text())
        self.assertEqual(argv, [str(fake), "--version"])

    def test_symlink_to_regular_executable_is_accepted(self):
        fake = write_executable(self.root / "fake-opencode",
                                "import sys\nsys.stdout.write('2.0.32\\n')\n")
        link = self.root / "opencode-link"
        link.symlink_to(fake)
        runner = OpenCodeRunner({"enabled": True, "binary": str(link)})
        self.assertEqual(runner.health()["version"], "2.0.32")

    def test_malformed_version_is_rejected(self):
        bodies = [
            "import sys\nsys.stdout.buffer.write(bytes([255,254,0,1]))\n",
            "import sys\nsys.stdout.buffer.write(b'\\x01\\x02 beep boop')\n",
            "sys.stdout.write('   \\n')\n",
            "sys.stdout.write('no digits here\\n')\n",
        ]
        for body in bodies:
            with self.subTest(body=body):
                fake = write_executable(self.root / "fake-opencode", body)
                runner = OpenCodeRunner({"enabled": True, "binary": str(fake)})
                with self.assertRaises(OpenCodeError):
                    runner.health()

    def test_nonzero_exit_is_rejected_without_output_leak(self):
        fake = write_executable(self.root / "fake-opencode",
                                "sys.stdout.write('2.0.32\\n')\nsys.exit(3)\n")
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake)})
        with self.assertRaises(OpenCodeError) as caught:
            runner.health()
        self.assertNotIn("2.0.32", str(caught.exception))

    def test_timeout_terminates_the_hung_leader(self):
        marker = self.root / "leader.pid"
        fake = write_executable(self.root / "fake-opencode",
                                "import os,time\n"
                                f"open(os.environ['{MARKER_ENV}'],'w').write(str(os.getpid()))\n"
                                "time.sleep(30)\n")
        set_test_env(**{MARKER_ENV: marker})
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake), "version_timeout_seconds": 1})
        with self.assertRaises(OpenCodeError) as caught:
            runner.health()
        self.assertIn("timed out", str(caught.exception))
        self.assertTrue(pid_gone(int(marker.read_text())))

    def test_oversize_stdout_is_rejected(self):
        fake = write_executable(self.root / "fake-opencode",
                                "import sys\nsys.stdout.write('a' * 200000)\n")
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake), "max_output_bytes": 1024})
        with self.assertRaises(OpenCodeError) as caught:
            runner.health()
        self.assertIn("memory limit", str(caught.exception))

    def test_oversize_stderr_is_rejected(self):
        fake = write_executable(self.root / "fake-opencode",
                                "import sys\nsys.stderr.write('b' * 200000)\n")
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake), "max_output_bytes": 1024})
        with self.assertRaises(OpenCodeError) as caught:
            runner.health()
        self.assertIn("memory limit", str(caught.exception))

    def test_descendant_holding_pipes_is_killed_after_leader_exit(self):
        marker = self.root / "child.pid"
        done = self.root / "child.argv"
        fake = write_executable(self.root / "fake-opencode",
                                "import os,subprocess,sys\n"
                                "sys.stdout.write('2.0.32\\n')\n"
                                "sys.stdout.flush()\n"
                                "child = subprocess.Popen([sys.executable, '-c',\n"
                                "    \"import os,signal,time\\n\"\n"
                                "    \"signal.signal(signal.SIGTERM, signal.SIG_IGN)\\n\"\n"
                                f"    \"open(os.environ['{MARKER_ENV}'],'w').write(str(os.getpid()))\\n\"\n"
                                "    \"time.sleep(30)\\n\"])\n"
                                f"open(os.environ['{ARGV_ENV}'],'w').write(str(child.pid))\n")
        set_test_env(**{MARKER_ENV: marker, ARGV_ENV: done})
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake), "version_timeout_seconds": 2})
        with self.assertRaises(OpenCodeError) as caught:
            runner.health()
        self.assertIn("timed out", str(caught.exception))
        self.assertTrue(pid_gone(int(done.read_text())))

    def test_missing_executable_fails_closed_at_probe(self):
        fake = write_executable(self.root / "fake-opencode", "sys.stdout.write('2.0.32\\n')\n")
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake)})
        fake.unlink()
        with self.assertRaises(OpenCodeError):
            runner.health()


class TestOpenCodeCleanupOrdering(unittest.TestCase):
    """Regression tests for the leader-reap invariant.

    The old probe reaped the leader with `proc.wait(timeout=1)` after EOF and
    again inside cleanup between TERM and KILL, so a later `killpg` could hit
    a reused PGID. These tests prove the fixed ordering: every killpg happens
    while the leader is unreaped, observation is nonreaping waitid, and the
    single reap follows the final KILL.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(clear_test_env)

    def tearDown(self):
        self.tmp.cleanup()

    def test_success_path_reaps_only_after_final_killpg(self):
        fake = write_executable(self.root / "fake-opencode",
                                "import sys\nsys.stdout.write('2.0.32\\n')\n")
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake)})
        with RecordingOrder() as order:
            health = runner.health()
        self.assertTrue(health["ok"])
        self.assertEqual(health["version"], "2.0.32")
        order.assert_single_reap_after_final_killpg(self)

    def test_nonzero_exit_reaps_only_after_final_killpg(self):
        fake = write_executable(self.root / "fake-opencode",
                                "sys.stdout.write('2.0.32\\n')\nsys.exit(3)\n")
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake)})
        with RecordingOrder() as order:
            with self.assertRaises(OpenCodeError):
                runner.health()
        order.assert_single_reap_after_final_killpg(self)

    def test_timeout_reaps_only_after_final_killpg(self):
        marker = self.root / "leader.pid"
        fake = write_executable(self.root / "fake-opencode",
                                "import os,time\n"
                                f"open(os.environ['{MARKER_ENV}'],'w').write(str(os.getpid()))\n"
                                "time.sleep(30)\n")
        set_test_env(**{MARKER_ENV: marker})
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake), "version_timeout_seconds": 1})
        with RecordingOrder() as order:
            with self.assertRaises(OpenCodeError) as caught:
                runner.health()
        self.assertIn("timed out", str(caught.exception))
        order.assert_single_reap_after_final_killpg(self)
        self.assertTrue(pid_gone(int(marker.read_text())))

    def test_descendant_ignoring_term_reaps_only_after_final_killpg(self):
        marker = self.root / "child.pid"
        done = self.root / "child.argv"
        fake = write_executable(self.root / "fake-opencode",
                                "import os,subprocess,sys\n"
                                "sys.stdout.write('2.0.32\\n')\n"
                                "sys.stdout.flush()\n"
                                "child = subprocess.Popen([sys.executable, '-c',\n"
                                "    \"import os,signal,time\\n\"\n"
                                "    \"signal.signal(signal.SIGTERM, signal.SIG_IGN)\\n\"\n"
                                f"    \"open(os.environ['{MARKER_ENV}'],'w').write(str(os.getpid()))\\n\"\n"
                                "    \"time.sleep(30)\\n\"])\n"
                                f"open(os.environ['{ARGV_ENV}'],'w').write(str(child.pid))\n")
        set_test_env(**{MARKER_ENV: marker, ARGV_ENV: done})
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake), "version_timeout_seconds": 2})
        with RecordingOrder() as order:
            with self.assertRaises(OpenCodeError) as caught:
                runner.health()
        self.assertIn("timed out", str(caught.exception))
        order.assert_single_reap_after_final_killpg(self)
        self.assertTrue(pid_gone(int(done.read_text())))

    def test_unknown_ownership_sends_no_signal_and_still_reaps(self):
        fake = write_executable(self.root / "fake-opencode",
                                "import sys\nsys.stdout.write('2.0.32\\n')\n")
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake)})
        with RecordingOrder() as order:
            with patch("opencode_core.os.waitid", side_effect=ChildProcessError()):
                with self.assertRaises(OpenCodeError) as caught:
                    runner.health()
        self.assertIn("could not be verified", str(caught.exception))
        # Ownership unknown: not one signal; only the handle-based reap.
        self.assertEqual([event[0] for event in order.events], ["wait"])

    def test_waitid_eintr_is_retried_without_reaping_or_hanging(self):
        fake = write_executable(self.root / "fake-opencode",
                                "import sys\nsys.stdout.write('2.0.32\\n')\n")
        runner = OpenCodeRunner({"enabled": True, "binary": str(fake)})
        real_waitid = os.waitid
        calls = []

        def flaky_waitid(idtype, ident, options):
            calls.append(options)
            if len(calls) <= 2:
                raise InterruptedError()
            return real_waitid(idtype, ident, options)

        with patch("opencode_core.os.waitid", side_effect=flaky_waitid):
            health = runner.health()
        self.assertTrue(health["ok"])
        self.assertEqual(health["version"], "2.0.32")
        self.assertGreaterEqual(len(calls), 3)
        self.assertEqual(calls[0], os.WEXITED | os.WNOHANG | os.WNOWAIT)

    def test_observe_leader_reports_exit_without_reaping(self):
        proc = subprocess.Popen([sys.executable, "-c", "pass"], stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True, close_fds=True)
        time.sleep(0.3)  # let it exit and become a zombie
        state, result = OpenCodeRunner._observe_leader(proc.pid, time.monotonic() + 5)
        self.assertEqual(state, "exited")
        self.assertEqual(result.si_code, os.CLD_EXITED)
        self.assertEqual(result.si_status, 0)
        stat = Path(f"/proc/{proc.pid}/stat").read_text()
        # WNOWAIT left the child waitable: still a zombie, NOT reaped.
        self.assertEqual(stat.rsplit(")", 1)[1].split()[0], "Z")
        self.assertEqual(proc.wait(), 0)  # reap by handle afterwards

    def test_observe_leader_returns_running_at_deadline_without_hanging(self):
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
        deadline = time.monotonic()
        state, result = OpenCodeRunner._observe_leader(proc.pid, deadline)
        self.assertEqual((state, result), ("running", None))
        self.assertLess(time.monotonic() - deadline, 1.0)
        proc.kill()
        proc.wait()

    def test_cleanup_group_escalates_to_kill_before_reaping(self):
        marker = self.root / "trap.pid"
        set_test_env(**{MARKER_ENV: marker})
        proc = subprocess.Popen([sys.executable, "-c",
                                 "import os,signal,time\n"
                                 "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                                 f"open(os.environ['{MARKER_ENV}'],'w').write(str(os.getpid()))\n"
                                 "time.sleep(30)\n"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
        # TERM must not race the child's signal setup: wait for the readiness
        # marker written after SIG_IGN is installed.
        end = time.monotonic() + 5
        while time.monotonic() < end and not marker.exists():
            time.sleep(0.05)
        self.assertTrue(marker.exists())
        runner = OpenCodeRunner({"enabled": True, "binary": sys.executable})
        with RecordingOrder() as order:
            runner._cleanup_group(proc, "pinned")
        order.assert_single_reap_after_final_killpg(self)
        self.assertEqual(proc.returncode, -signal.SIGKILL)

    def test_cleanup_group_never_signals_unknown_ownership(self):
        proc = subprocess.Popen([sys.executable, "-c", "pass"], stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True, close_fds=True)
        runner = OpenCodeRunner({"enabled": True, "binary": sys.executable})
        with RecordingOrder() as order:
            runner._cleanup_group(proc, "unknown")
        # Ownership unknown: not one signal; only the handle-based reap.
        self.assertEqual([event[0] for event in order.events], ["wait"])
        self.assertEqual(proc.returncode, 0)


class TestOpenCodeRegistration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bridge = Bridge("http://127.0.0.1:8642", "test-secret-123", self.root,
                             httpx.MockTransport(FakeHermes()))
        self.codex = CodexRunner({"binary": sys.executable, "allowed_workspaces": [str(self.root)]},
                                 self.root / "codex-state")
        (self.root / "fixture.txt").write_text("hands fixture")
        self.hands = HandsRuntime({"enabled": True, "workspaces": [{"name": "fixture", "path": str(self.root)}]},
                                  self.root / "hands-state")
        self.contexts = ContextRegistry(self.bridge.state, self.bridge.audit)
        self.fake = write_executable(self.root / "fake-opencode", "sys.stdout.write('2.0.32\\n')\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_registration_keeps_27_tools(self):
        m = server(self.bridge, self.codex, self.hands, self.contexts)
        tools = set(m._tool_manager._tools)
        self.assertEqual(len(tools), 27)
        self.assertNotIn("opencode_health", tools)

    def test_disabled_registration_keeps_27_tools(self):
        disabled = OpenCodeRunner({"enabled": False})
        m = server(self.bridge, self.codex, self.hands, self.contexts, disabled)
        tools = set(m._tool_manager._tools)
        self.assertEqual(len(tools), 27)
        self.assertNotIn("opencode_health", tools)

    def test_enabled_registration_adds_opencode_health(self):
        enabled = OpenCodeRunner({"enabled": True, "binary": str(self.fake)})
        m = server(self.bridge, self.codex, self.hands, self.contexts, enabled)
        tools = set(m._tool_manager._tools)
        self.assertEqual(len(tools), 28)
        self.assertIn("opencode_health", tools)


class TestOpenCodeMcpContract(unittest.TestCase):
    def test_stdio_discovery_and_health_with_enabled_fake(self):
        async def run():
            params = StdioServerParameters(
                command=sys.executable, args=[str(Path(__file__).with_name("mock_opencode_server.py"))])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    names = {t.name for t in listed.tools}
                    self.assertEqual(len(names), 28)
                    self.assertIn("opencode_health", names)
                    health = await session.call_tool("opencode_health", {})
                    self.assertFalse(health.isError)
                    self.assertTrue(health.structuredContent["ok"])
                    self.assertEqual(health.structuredContent["version"], "2.0.32")
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
