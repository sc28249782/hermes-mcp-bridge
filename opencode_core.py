"""Disabled-by-default OpenCode CLI health adapter.

This module is a foundation only. It exposes one bounded, read-only version
probe. It does not implement task submission, sessions, events, cancellation,
or permission handling for OpenCode.
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
VERSION_MAX_CHARS = 300


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
        proc = None
        try:
            try:
                proc = subprocess.Popen(
                    [self.binary, "--version"], stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    shell=False, start_new_session=True, close_fds=True)
            except OSError:
                raise OpenCodeError("OpenCode CLI version probe failed to start") from None
            chunks, overflow, timed_out = self._drain(proc)
            if overflow:
                raise OpenCodeError("OpenCode CLI version output exceeded the configured memory limit")
            if timed_out:
                raise OpenCodeError("OpenCode CLI version probe timed out; the process group was terminated")
            try:
                returncode = proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                # Both pipes closed but the leader still hangs; fail closed.
                raise OpenCodeError("OpenCode CLI version probe timed out; the process group was terminated") from None
            if returncode:
                raise OpenCodeError("OpenCode CLI version probe failed")
            return self._parse_version(bytes(chunks["stdout"]))
        finally:
            try:
                self._cleanup_group(proc)
            finally:
                if proc is not None:
                    for stream in (proc.stdout, proc.stderr):
                        if stream is not None:
                            stream.close()

    def _drain(self, proc):
        """Read both pipes until EOF, the deadline, or a stream cap, with bounded memory."""
        deadline = time.monotonic() + self.timeout
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
    def _parse_version(raw: bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise OpenCodeError("OpenCode CLI reported an unreadable version string") from None
        text = text.strip()
        if not text or not VERSION_TEXT.fullmatch(text) or not any(c.isdigit() for c in text):
            raise OpenCodeError("OpenCode CLI reported an unreadable version string")
        return text[:VERSION_MAX_CHARS]

    @staticmethod
    def _cleanup_group(proc):
        """Terminate the probe process group, escalate TERM to KILL, then reap.

        `start_new_session=True` makes the leader's PID the group ID. Every
        `killpg` call happens while the leader is not yet reaped: its zombie
        status pins the group ID, so no unrelated process can own it and PID
        reuse cannot redirect the signal. Escalation also covers a leader that
        exits quickly while a descendant keeps living (for example a
        descendant that holds a pipe open or ignores SIGTERM).
        """
        if proc is None:
            return
        pgid = proc.pid
        try:
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=KILL_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=KILL_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            pass
