"""Disabled-by-default OpenCode CLI health adapter.

This module is a foundation only. It exposes one bounded, read-only version
probe. It does not implement task submission, sessions, events, cancellation,
or permission handling for OpenCode.

Platform assumptions (Linux / WSL2): cleanup relies on `start_new_session=True`
(the leader's PID is its process-group ID) and on Linux `os.waitid` semantics.
With `WNOHANG | WNOWAIT`, waitid returns None while the child is still
running, returns a waitid_result once the child exited while leaving it
waitable (a zombie that still pins the PID/PGID), and raises ChildProcessError
only when the target is no longer a waitable child of this process. Every
`killpg` therefore happens while the leader is an unreaped child of this
process, and the leader is reaped exactly once, by handle, after the final
group signal.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import select
import signal
import stat as stat_module
import subprocess
import time

from config_schema import ConfigError, load_bridge_config

VERSION_TEXT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._/+-]{0,199}$")
READ_CHUNK = 65_536
KILL_GRACE_SECONDS = 2
OBSERVE_POLL_SECONDS = 0.01


class OpenCodeError(RuntimeError):
    pass


class OpenCodeRunner:
    """Bounded health probe for one explicitly configured OpenCode executable.

    The integration is disabled by default. When disabled, no process is ever
    spawned and every health check fails closed. The runner adds no sandbox:
    the configured executable runs with the full privileges of the bridge
    process and can read global configuration and credentials.
    """

    def __init__(self, config: dict):
        config = config or {}
        self.enabled = bool(config.get("enabled", False))
        raw_binary = config.get("binary", "")
        self.binary = str(Path(raw_binary).expanduser()) if isinstance(raw_binary, str) and raw_binary else ""
        self.timeout = int(config.get("version_timeout_seconds", 10))
        self.max_output = int(config.get("max_output_bytes", 65_536))
        self.config_warnings: list[str] = []
        if not 1 <= self.timeout <= 120:
            raise OpenCodeError("opencode.version_timeout_seconds must be 1-120")
        if not 1024 <= self.max_output <= 1_048_576:
            raise OpenCodeError("opencode.max_output_bytes must be 1024-1048576")
        if self.enabled:
            if not self.binary:
                raise OpenCodeError("opencode.enabled requires an explicit opencode.binary path")
            self._validate_regular_executable()

    @classmethod
    def from_config(cls, root: Path):
        try:
            config, warnings = load_bridge_config(Path(root))
        except ConfigError as exc:
            raise OpenCodeError(str(exc)) from exc
        runner = cls(config.get("opencode", {}))
        runner.config_warnings = warnings
        return runner

    def _validate_regular_executable(self):
        path = Path(self.binary)
        try:
            info = path.stat()
        except OSError:
            raise OpenCodeError("opencode.binary is not a regular executable file") from None
        if not stat_module.S_ISREG(info.st_mode) or not os.access(path, os.X_OK):
            raise OpenCodeError("opencode.binary is not a regular executable file")

    def health(self):
        """Probe the configured executable with `--version` and report bounded metadata."""
        if not self.enabled:
            # Fail closed before any filesystem, process, network, model, or
            # authentication access. This path never spawns a process.
            raise OpenCodeError("OpenCode integration is disabled in bridge-config.json; review docs/SECURITY.md before enabling it")
        self._validate_regular_executable()
        version = self._version_probe()
        return {"ok": True, "enabled": True, "version": version,
                "binary": self.binary,
                "version_timeout_seconds": self.timeout,
                "max_output_bytes": self.max_output,
                "probe": "bounded --version with fixed argv, shell disabled, process-group cleanup",
                "execution_scope": ("The probe runs the configured executable with the full privileges of "
                                    "the bridge process. The bridge adds no sandbox and makes no network, "
                                    "model, or authentication calls."),
                "runner_scope": ("health only; task submission, sessions, events, cancellation, and "
                                 "permission handling are not implemented")}

    def _version_probe(self):
        # leader_state tracks whether the leader is still an unreaped child of
        # this process ("pinned": running or zombie, so its PGID cannot be
        # reused and the group may be signaled) or ownership is lost
        # ("unknown": never signal).
        proc = None
        leader_state = "unknown"
        try:
            deadline = time.monotonic() + self.timeout
            try:
                proc = subprocess.Popen(
                    [self.binary, "--version"], stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    shell=False, start_new_session=True, close_fds=True)
            except OSError:
                raise OpenCodeError("OpenCode CLI version probe failed to start") from None
            leader_state = "pinned"
            chunks, overflow, timed_out = self._drain(proc, deadline)
            if overflow:
                raise OpenCodeError("OpenCode CLI version output exceeded the configured memory limit")
            if timed_out:
                raise OpenCodeError("OpenCode CLI version probe timed out; the process group was terminated")
            state, exit_state = self._observe_leader(proc.pid, deadline)
            leader_state = "unknown" if state == "unknown" else "pinned"
            if state == "running":
                # Pipes closed but the leader still hangs at the overall
                # deadline; fail closed and let the finally block terminate
                # the group.
                raise OpenCodeError("OpenCode CLI version probe timed out; the process group was terminated")
            if state == "unknown":
                # Ownership unknown: report failure; the finally block will
                # not signal and will only reap by handle.
                raise OpenCodeError("OpenCode CLI version probe could not be verified")
            if not self._exit_state_is_success(exit_state):
                raise OpenCodeError("OpenCode CLI version probe failed")
            return self._parse_version(bytes(chunks["stdout"]))
        finally:
            try:
                self._cleanup_group(proc, leader_state)
            finally:
                if proc is not None:
                    for stream in (proc.stdout, proc.stderr):
                        if stream is not None:
                            stream.close()

    def _drain(self, proc, deadline):
        """Read both pipes until EOF, the deadline, or a stream cap, with bounded memory.

        `deadline` is the probe's overall wall-clock budget, anchored at
        spawn and shared with the exit observation; no extra wait is added
        after EOF.
        """
        fds = [proc.stdout.fileno(), proc.stderr.fileno()]
        chunks = {"stdout": bytearray(), "stderr": bytearray()}
        by_fd = {proc.stdout.fileno(): "stdout", proc.stderr.fileno(): "stderr"}
        overflow = False
        while fds:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return chunks, overflow, True
            ready, _, _ = select.select(fds, [], [], min(remaining, self.timeout))
            for fd in ready:
                bucket = chunks[by_fd[fd]]
                capacity = self.max_output - len(bucket)
                data = os.read(fd, max(1, min(READ_CHUNK, capacity + 1)))
                if not data:
                    fds.remove(fd)
                    continue
                if len(data) > capacity:
                    overflow = True
                else:
                    bucket.extend(data)
            if overflow:
                return chunks, overflow, False
        return chunks, overflow, False

    @staticmethod
    def _observe_leader(pid, deadline):
        """Observe one direct child's exit WITHOUT reaping it (Linux).

        Polls `os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | WNOWAIT)`
        with a short sleep until the child exits or the monotonic `deadline`
        passes. WNOWAIT leaves an exited child waitable, so observing never
        reaps: the zombie keeps the PID/PGID pinned for a later `killpg`.
        Returns ("exited", waitid_result_or_None); ("running", None) when the
        child is still alive at the deadline; ("unknown", None) when the
        child is no longer a waitable child of this process, so ownership
        (and any process group the PID number may now name) is foreign.
        """
        while True:
            try:
                result = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            except ChildProcessError:
                return "unknown", None
            except InterruptedError:
                # EINTR: retry conservatively without reaping.
                result = None
            if result is not None:
                return "exited", result
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return "running", None
            time.sleep(min(OBSERVE_POLL_SECONDS, remaining))

    @staticmethod
    def _exit_state_is_success(exit_state):
        """Success is a normal exit only: CLD_EXITED with status 0 (Linux)."""
        return (exit_state is not None
                and exit_state.si_code == os.CLD_EXITED
                and exit_state.si_status == 0)

    @staticmethod
    def _parse_version(raw: bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise OpenCodeError("OpenCode CLI reported an unreadable version string") from None
        text = text.strip()
        if not text or not VERSION_TEXT.fullmatch(text) or not any(c.isdigit() for c in text):
            raise OpenCodeError("OpenCode CLI reported an unreadable version string")
        return text

    def _cleanup_group(self, proc, leader_state):
        """Terminate the probe process group, escalate TERM to KILL, then reap once.

        Invariant: every `killpg` happens while the leader is an unreaped
        child of this process (`leader_state == "pinned"`). A running leader
        pins the group by being alive; an exited but unreaped leader pins it
        as a zombie, so PID/PGID reuse cannot redirect a signal to an
        unrelated group. The leader is reaped exactly once, by handle, after
        the final KILL; `proc.wait` never gates a signal. When ownership is
        unknown, no signal is sent at all. The TERM grace is a nonreaping
        `waitid` observation, so escalation cannot reap the leader early.
        Escalation also covers a leader that exits quickly while a descendant
        keeps living (for example a descendant that holds a pipe open or
        ignores SIGTERM). Linux assumptions: `start_new_session=True` makes
        the leader's PID the group ID; see the module docstring for the
        `os.waitid` semantics this relies on.
        """
        if proc is None:
            return
        pgid = proc.pid
        if leader_state != "unknown":
            self._signal_group(pgid, signal.SIGTERM)
            state, _ = self._observe_leader(pgid, time.monotonic() + KILL_GRACE_SECONDS)
            if state != "unknown":
                self._signal_group(pgid, signal.SIGKILL)
        try:
            proc.wait(timeout=KILL_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            # SIGKILL to the group did not finish in time; give up bounded.
            pass
        except ChildProcessError:
            # Our child was reaped elsewhere; nothing left to reap by handle.
            pass

    @staticmethod
    def _signal_group(pgid, sig):
        try:
            os.killpg(pgid, sig)
        except (ProcessLookupError, PermissionError):
            pass
