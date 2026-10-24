"""Offline direct-child watchdog and private byte recorder; no launcher or CLI.

Only a new unreaped child passed by its direct parent can be adopted. This is not
a complete guest supervisor, collector, containment proof or Work-route adapter.
"""
import base64
from collections import deque
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import threading
import time

from parent_contract import Hold, require

EVIDENCE_CLASS = "offline-owned-child-control"
FRAME_LIMIT = 65536
QUEUE_LIMIT = 1024 * 1024
TRACE_LIMIT = 8 * 1024 * 1024
TICK_SECONDS = 0.02


def finite(value, maximum):
    return type(value) in (int, float) and math.isfinite(value) and 0 < value <= maximum


class OwnedChild:
    """One-use Linux pidfd control, with a watchdog separate from the caller thread.

    The caller supplies an existing Popen child and its exact approved argv. This
    object never spawns/adopts by stored PID and never sends a process-group signal.
    A lease is liveness data only, not an approval. Only this direct leader is owned.
    """

    def __init__(self, process, expected_argv, trace, *, window=30, lease=5,
                 term_grace=10, allow_kill=False):
        require(isinstance(process, subprocess.Popen), "direct Popen child required")
        require(type(expected_argv) is list and expected_argv and process.args == expected_argv,
                "argv binding mismatch")
        require(finite(window, 1200) and finite(lease, 30) and finite(term_grace, 10)
                and type(allow_kill) is bool, "invalid control bounds")
        require(not process.text_mode and all(getattr(process, k) is not None
                for k in ("stdin", "stdout", "stderr")),
                "private binary pipes required")
        require(hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"),
                "Linux pidfd support required")
        require(int(Path("/proc/self/stat").read_text().split(" ", 1)[0]) == os.getpid(),
                "procfs PID namespace mismatch")
        # WNOWAIT confirms direct-parent ownership without reaping before pidfd_open.
        require(os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None,
                "child already exited")
        proc = Path("/proc") / str(process.pid)
        actual_argv = (proc / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")
        require(actual_argv == [os.fsencode(a) for a in expected_argv], "live argv mismatch")
        require(proc.stat().st_uid == os.geteuid(), "child owner mismatch")
        require(Path(expected_argv[0]).is_absolute() and
                os.readlink(proc / "exe") == str(Path(expected_argv[0]).resolve(strict=True)),
                "child executable mismatch")
        self.pidfd = os.pidfd_open(process.pid)
        self.process, self.allow_kill = process, allow_kill
        self.started = time.monotonic()
        self.deadline, self.lease_until = self.started + window, self.started + lease
        self.lease_seconds, self.term_grace = lease, term_grace
        self.reason = None
        self.signals = []
        self.queue, self.queue_bytes = deque(), 0
        self.trace_bytes = 0
        self.finished = threading.Event()
        self.stop_event = threading.Event()
        self.lock = threading.RLock()
        self.send_lock = threading.Lock()
        self.trace_fd = None
        try:
            path = Path(trace).absolute()
            require(path.parent == path.parent.resolve(strict=True)
                    and path.parent.stat().st_mode & 0o077 == 0, "private trace parent required")
            self.trace_fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            stat = (proc / "stat").read_text().rsplit(")", 1)[1].split()
            self.identity = {"pid": process.pid, "start_ticks": int(stat[19]),
                             "owner_uid": proc.stat().st_uid,
                             "executable": os.readlink(proc / "exe"), "argv": expected_argv[:]}
            self._record("identity", json.dumps(self.identity, sort_keys=True).encode())
            for stream in (process.stdin, process.stdout, process.stderr):
                os.set_blocking(stream.fileno(), False)
        except BaseException:
            if self.trace_fd is not None:
                os.close(self.trace_fd)
            os.close(self.pidfd)
            # Adoption failure never authorizes a signal. The original owner retains cleanup.
            raise
        self.thread = threading.Thread(target=self._watch, name="s24-owned-child", daemon=True)
        try:
            self.thread.start()
        except BaseException:
            os.close(self.trace_fd)
            os.close(self.pidfd)
            # The caller still owns the child and all pipes; no signal is authorized.
            raise

    def _record(self, direction, data):
        with self.lock:
            raw = (json.dumps({"direction": direction, "data_base64": base64.b64encode(data).decode()},
                              separators=(",", ":")) + "\n").encode()
            require(self.trace_bytes + len(raw) <= TRACE_LIMIT, "trace budget")
            view = memoryview(raw)
            while view:
                wrote = os.write(self.trace_fd, view)
                require(wrote > 0, "trace write failed")
                self.trace_bytes += wrote
                view = view[wrote:]

    def renew(self):
        with self.lock:
            require(self.reason is None and not self.finished.is_set(), "control closed")
            now = time.monotonic()
            require(now < self.deadline and now < self.lease_until, "lease/window expired")
            self.lease_until = min(self.deadline, now + self.lease_seconds)

    def stop(self, reason="operator_stop"):
        require(reason in ("operator_stop", "parent_lost", "observation_failed"), "stop reason")
        self._hold(reason)

    def _hold(self, reason):
        with self.lock:
            if self.reason is None:
                self.reason = reason
            self.stop_event.set()

    def send(self, raw):
        """Bounded raw stdin bytes; protocol/tool policy must be enforced upstream."""
        if not self.send_lock.acquire(blocking=False):
            self._hold("concurrent_send")
            raise Hold("concurrent send")
        try:
            require(type(raw) is bytes and 0 < len(raw) <= FRAME_LIMIT, "input byte limit")
            with self.lock:
                require(self.reason is None and not self.finished.is_set(), "control closed")
                self._record("stdin_intent", raw)
            until = min(self.deadline, self.lease_until, time.monotonic() + 2)
            view = memoryview(raw)
            while view:
                require(not self.stop_event.is_set() and time.monotonic() < until, "stdin blocked/closed")
                try:
                    count = os.write(self.process.stdin.fileno(), view[:4096])
                    require(count > 0, "stdin write failed")
                    self._record("stdin_written", bytes(view[:count]))
                    view = view[count:]
                except BlockingIOError:
                    self.stop_event.wait(TICK_SECONDS)
        except BaseException:
            self._hold("send_failed")
            raise
        finally:
            self.send_lock.release()

    def readline(self, timeout=2):
        require(finite(timeout, 30), "invalid read timeout")
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            with self.lock:
                require(self.reason is None, "control held")
                if self.queue:
                    raw = self.queue.popleft()
                    self.queue_bytes -= len(raw)
                    return raw
                require(not self.finished.is_set(), "child output ended")
            self.finished.wait(TICK_SECONDS)
        self._hold("read_timeout")
        raise Hold("read timeout")

    def _signal(self, number):
        # pidfd names the adopted process instance even if a numeric PID is reused.
        if self.process.poll() is not None:
            return
        if not self._identity_matches():
            self._hold("stop_identity_unconfirmed")
            return
        try:
            signal.pidfd_send_signal(self.pidfd, number)
            self.signals.append(number)
        except ProcessLookupError:
            pass

    def _identity_matches(self):
        proc = Path("/proc") / str(self.identity["pid"])
        try:
            stat = (proc / "stat").read_text().rsplit(")", 1)[1].split()
            return (int(stat[19]) == self.identity["start_ticks"]
                    and proc.stat().st_uid == self.identity["owner_uid"]
                    and os.readlink(proc / "exe") == self.identity["executable"]
                    and (proc / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")
                    == [os.fsencode(a) for a in self.identity["argv"]])
        except (OSError, ValueError, IndexError):
            return False

    def _watch(self):
        selector = selectors.DefaultSelector()
        buffer = bytearray()
        stop_at = None
        try:
            for stream, label in ((self.process.stdout, "stdout"), (self.process.stderr, "stderr")):
                selector.register(stream, selectors.EVENT_READ, label)
            while True:
                now = time.monotonic()
                if self.reason is None and now >= min(self.deadline, self.lease_until):
                    self._hold("window_expired" if now >= self.deadline else "lease_expired")
                if self.stop_event.is_set() and stop_at is None:
                    self._signal(signal.SIGTERM)
                    stop_at = now
                if stop_at is not None and now >= stop_at + self.term_grace:
                    if self.process.poll() is None and self.allow_kill:
                        self._signal(signal.SIGKILL)
                    break
                if self.process.poll() is not None and not selector.get_map():
                    if buffer:
                        self._hold("partial_stdout_frame")
                    break
                for key, _ in selector.select(TICK_SECONDS):
                    data = os.read(key.fileobj.fileno(), 4096)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    try:
                        self._record(key.data, data)
                    except BaseException:
                        self._hold("trace_failed")
                        continue
                    if key.data == "stdout":
                        buffer.extend(data)
                        while b"\n" in buffer:
                            end = buffer.index(b"\n") + 1
                            require(end <= FRAME_LIMIT, "stdout frame limit")
                            line = bytes(buffer[:end])
                            del buffer[:end]
                            with self.lock:
                                require(self.queue_bytes + len(line) <= QUEUE_LIMIT, "stdout queue limit")
                                self.queue.append(line)
                                self.queue_bytes += len(line)
                        require(len(buffer) <= FRAME_LIMIT, "stdout frame limit")
        except BaseException:
            self._hold("watch_failed")
            self._signal(signal.SIGTERM)
            if self.allow_kill:
                # Preserve TERM grace even after a reader/trace failure.
                try:
                    self.process.wait(timeout=self.term_grace)
                except subprocess.TimeoutExpired:
                    self._signal(signal.SIGKILL)
        finally:
            selector.close()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._hold("stop_unconfirmed")
            self.finished.set()

    def close(self):
        self.stop()
        self.thread.join(timeout=self.term_grace + 2)
        require(not self.thread.is_alive(), "watchdog did not finish")
        require(self.process.returncode is not None, "leader stop unconfirmed; retain owner handle")
        with self.lock:
            if self.trace_fd is not None:
                try:
                    os.fsync(self.trace_fd)
                finally:
                    os.close(self.trace_fd)
                    self.trace_fd = None
                    os.close(self.pidfd)
                    for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                        stream.close()
        return {"evidence_class": EVIDENCE_CLASS, "reason": self.reason,
                "leader_reaped": True, "exit_code": self.process.returncode,
                "trace_bytes": self.trace_bytes, "signals": self.signals[:],
                "descendant_cessation_proved": False}
