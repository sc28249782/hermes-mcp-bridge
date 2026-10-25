"""Offline fixture-only process supervisor and SDK adapter, Linux only.

No Work route, arbitrary command launcher or complete cohort containment is
provided. The supervisor owns one fixture leader through unchanged OwnedChild.
"""
import argparse
import asyncio
from contextlib import asynccontextmanager
import ctypes
import json
import math
import os
from pathlib import Path
import select
import signal
import socket
import stat
import struct
import subprocess
import sys
import time

from launch_admission import private_directory
from owned_child import OwnedChild, finite
from parent_contract import Hold, TOOLS, decode, encode, require
import s24_fixture as fixture

EVIDENCE_CLASS = "offline-supervised-stdio"
CONTROL_NAME = "control.sock"
RETAINED_CHILDREN = []  # Unconfirmed cleanup remains owned; never claim cessation.


def identity(pid):
    require(int(Path("/proc/self/stat").read_text().split(" ", 1)[0]) == os.getpid(),
            "supervisor procfs PID namespace mismatch")
    path = Path("/proc") / str(pid)
    parts = (path / "stat").read_text().rsplit(")", 1)[1].split()
    return {"pid": pid, "start_ticks": int(parts[19]), "uid": path.stat().st_uid,
            "exe": os.readlink(path / "exe"),
            "argv": [os.fsdecode(v) for v in (path / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")]}


def private_json(root, name, value):
    _, directory, _ = private_directory(root)
    fd = None
    try:
        fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        require(stat.S_IMODE(os.fstat(fd).st_mode) == 0o600, "private supervisor evidence required")
        raw = encode(value)
        while raw:
            count = os.write(fd, raw)
            require(count > 0, "supervisor evidence write failed")
            raw = raw[count:]
        os.fsync(fd)
        os.fsync(directory)
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


def read_private(root, name):
    _, directory, _ = private_directory(root)
    fd = None
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1,
                "private supervisor result required")
        return decode(os.read(fd, 65537))
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


def arm_parent_death(parent):
    # The kernel setting is installed in the child itself; never signal a supplied PID.
    require(type(parent) is int and parent > 1 and os.getppid() == parent, "startup parent changed")
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    require(libc.prctl(1, signal.SIGTERM, 0, 0, 0) == 0, "parent-death signal unavailable")
    require(os.getppid() == parent, "startup parent changed after arming")


def child(candidate, root, parent, deadline):
    require(math.isfinite(deadline) and time.monotonic() < deadline <= time.monotonic() + 120,
            "finite child startup deadline required")
    _, directory, _ = private_directory(root)
    os.close(directory)
    require(not (root / "state").exists(), "fresh child state required")
    arm_parent_death(parent)
    current = identity(os.getpid())
    os.write(sys.stdout.fileno(), encode({"kind": "s24-startup", "identity": current,
                                         "parent": parent, "pdeathsig": signal.SIGTERM}))
    require(select.select([sys.stdin.fileno()], [], [], max(0, min(3, deadline - time.monotonic())))[0],
            "startup handoff expired")
    require(os.read(sys.stdin.fileno(), 1) == b"G", "startup handoff rejected")
    require(time.monotonic() < deadline, "startup window expired")
    # No exec, credential change or fork follows arming in this reviewed path.
    sys.argv = [str(Path(fixture.__file__).resolve()), "serve", "--candidate", str(candidate),
                "--state", str(root / "state")]
    fixture.main()


class RpcGate:
    """Coarse protocol allowlist; the parent still enforces matrix arguments/order."""
    def __init__(self):
        self.ids = set()
        self.initialized = self.notified = False

    def accept(self, raw):
        value = decode(raw)
        require(value.get("jsonrpc") == "2.0" and type(value.get("method")) is str,
                "supervisor RPC shape")
        method = value["method"]
        require(method in ("initialize", "notifications/initialized", "tools/list", "tools/call"),
                "supervisor RPC method not allowed")
        if method == "notifications/initialized":
            require(self.initialized and not self.notified and "id" not in value, "initialize notification order")
            self.notified = True
            return
        request_id = value.get("id")
        require(type(request_id) in (int, str) and request_id not in self.ids and len(self.ids) < 1024,
                "supervisor RPC id duplicate/type/budget")
        if method == "initialize":
            require(not self.initialized, "duplicate initialize")
            self.initialized = True
        else:
            require(self.notified, "RPC before initialized notification")
        params = value.get("params", {})
        require(type(params) is dict, "supervisor RPC params")
        if method == "tools/call":
            require(params.get("name") in TOOLS | {"bridge_version"}, "supervisor tool not allowed")
        self.ids.add(request_id)


def startup_frame(process, owner_fd, deadline):
    buffer = bytearray()
    until = min(deadline, time.monotonic() + 3)
    while time.monotonic() < until:
        ready, _, _ = select.select([process.stdout.fileno(), owner_fd], [], [], 0.02)
        require(owner_fd not in ready, "owner lost during startup")
        if process.stdout.fileno() in ready:
            part = os.read(process.stdout.fileno(), 4096)
            require(part, "fixture exited before startup handshake")
            buffer.extend(part)
            require(len(buffer) <= 65536, "startup frame limit")
            if b"\n" in buffer:
                return decode(bytes(buffer))
    raise Hold("startup handshake timeout")


def supervisor(candidate, root, deadline, lease, term_grace, allow_kill):
    require(math.isfinite(deadline) and time.monotonic() < deadline <= time.monotonic() + 120,
            "finite offline supervisor deadline required")
    require(finite(lease, 5) and finite(term_grace, 10) and type(allow_kill) is bool,
            "supervisor lease/grace bounds")
    fixture.verify_candidate(candidate)
    owner = identity(os.getppid())
    require(owner["uid"] == os.geteuid(), "controller owner mismatch")
    _, directory, _ = private_directory(root)
    os.close(directory)
    require(not (root / "state").exists(), "fresh supervisor state required")
    owner_fd = os.pidfd_open(owner["pid"])
    try:
        require(os.getppid() == owner["pid"] and identity(owner["pid"]) == owner
                and not select.select([owner_fd], [], [], 0)[0], "controller changed during pidfd binding")
    except BaseException:
        os.close(owner_fd)
        raise
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.setblocking(False)
    control = process = stop_connection = None
    reason = "supervisor_failure"
    signalled = []
    def request_stop(number, frame):
        signalled.append(number)  # No signal is sent from this handler.
    old_term = signal.signal(signal.SIGTERM, request_stop)
    old_int = signal.signal(signal.SIGINT, request_stop)
    try:
        listener.bind(str(root / CONTROL_NAME))  # Existing socket is never replaced/deleted.
        os.chmod(root / CONTROL_NAME, 0o600)
        listener.listen(1)
        argv = [sys.executable, "-B", str(Path(__file__).resolve()), "child", "--candidate", str(candidate),
                "--root", str(root), "--parent", str(os.getpid()), "--deadline", str(deadline)]
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env={"PYTHONDONTWRITEBYTECODE": "1"})
        frame = startup_frame(process, owner_fd, deadline)
        require(set(frame) == {"kind", "identity", "parent", "pdeathsig"}
                and frame["kind"] == "s24-startup" and frame["parent"] == os.getpid()
                and frame["pdeathsig"] == signal.SIGTERM
                and frame["identity"] == identity(process.pid), "startup identity mismatch")
        # Ready means the reviewed child code is executing, not a sleep/retry to
        # hide #100's observation. OwnedChild's exact adoption checks are unchanged.
        remaining = deadline - time.monotonic()
        require(remaining > 0, "supervisor deadline expired")
        control = OwnedChild(process, argv, root / "supervisor-pipes.jsonl", window=remaining,
                             lease=lease, term_grace=term_grace, allow_kill=allow_kill)
        control.deadline = min(control.deadline, deadline)
        control.lease_until = min(control.lease_until, deadline)
        private_json(root, "supervisor-ready.json", {"evidence_class": EVIDENCE_CLASS,
            "supervisor": identity(os.getpid()), "owner": owner, "child": control.identity,
            "startup": frame, "deadline": deadline, "complete_writer_coverage_proved": False})
        control.send(b"G")
        gate, buffer, sequence = RpcGate(), bytearray(), 0
        while True:
            ready, _, _ = select.select([sys.stdin.fileno(), owner_fd, listener], [], [], 0.02)
            if owner_fd in ready:
                reason = "owner_lost"
                break
            if signalled:
                reason = "supervisor_signal"
                break
            if time.monotonic() >= deadline:
                reason = "window_expired"
                break
            if control.reason is not None or control.finished.is_set():
                reason = control.reason or "child_exited"
                break
            if listener in ready:
                connection, _ = listener.accept()
                connection.settimeout(0.2)
                try:
                    pid, uid, _ = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                    require(pid == owner["pid"] and uid == owner["uid"] and identity(pid) == owner,
                            "controller peer identity mismatch")
                    request_bytes = bytearray()
                    read_until = time.monotonic() + 0.2
                    while not request_bytes.endswith(b"\n"):
                        remaining = read_until - time.monotonic()
                        require(remaining > 0, "controller frame timeout")
                        connection.settimeout(remaining)
                        part = connection.recv(1025 - len(request_bytes))
                        require(part and len(request_bytes) + len(part) <= 1024, "controller frame lost/large")
                        request_bytes.extend(part)
                    request = decode(bytes(request_bytes))
                    require(set(request) == {"seq", "op"} and type(request["seq"]) is int
                            and request["seq"] == sequence + 1 and request["op"] in ("renew", "stop"),
                            "controller message order/shape")
                    sequence += 1
                    if request["op"] == "stop":
                        reason, stop_connection = "controller_stop", connection
                        break
                    control.renew()
                    connection.sendall(encode({"seq": sequence, "ok": True}))
                finally:
                    if connection is not stop_connection:
                        connection.close()
            if sys.stdin.fileno() in ready:
                part = os.read(sys.stdin.fileno(), 4096)
                if not part:
                    reason = "controller_eof"
                    break
                buffer.extend(part)
                require(len(buffer) <= 65536, "supervisor stdin frame limit")
                while b"\n" in buffer:
                    end = buffer.index(b"\n") + 1
                    raw = bytes(buffer[:end])
                    del buffer[:end]
                    gate.accept(raw)
                    control.send(raw)
            while True:
                with control.lock:
                    available = bool(control.queue)
                if not available:
                    break
                raw = control.readline(timeout=0.1)
                view = memoryview(raw)
                while view:
                    count = os.write(sys.stdout.fileno(), view)
                    require(count > 0, "supervisor stdout failed")
                    view = view[count:]
        control.stop("parent_lost" if reason in ("owner_lost", "controller_eof") else "operator_stop")
        outcome = control.close()
        receipt = {"evidence_class": EVIDENCE_CLASS, "reason": reason, "leader": outcome,
                   "supervisor_pid": os.getpid(), "owner_pid": owner["pid"],
                   "complete_writer_cessation_proved": False, "cohort_coverage_proved": False}
        private_json(root, "supervisor-stop.json", receipt)
        if stop_connection is not None:
            stop_connection.sendall(encode({"seq": sequence, "ok": True, "receipt": receipt}))
        return receipt
    finally:
        if stop_connection is not None:
            stop_connection.close()
        listener.close()
        os.close(owner_fd)
        signal.signal(signal.SIGTERM, old_term)
        signal.signal(signal.SIGINT, old_int)
        if control is not None and control.trace_fd is not None:
            try:
                control.stop("observation_failed")
                control.close()
            except BaseException:
                RETAINED_CHILDREN.append(control)
        elif control is None and process is not None and process.poll() is None:
            # Before handoff the reviewed child waits for G. EOF rejects that
            # handoff without signaling an unadopted target.
            process.stdin.close()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                RETAINED_CHILDREN.append(process)
        # If cleanup is still unconfirmed, CLI exit triggers the armed child's
        # parent-death TERM. This is not confirmation or a numeric-PID fallback.
        if process is not None and process.poll() is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()


class SupervisedSdkFactory:
    """Fixture-only SDK proxy; explicit stop completes before SDK context exit."""
    def __init__(self, root, *, lease=5, term_grace=10, allow_kill=False):
        self.root = Path(root).absolute()
        self.lease, self.term_grace, self.allow_kill = lease, term_grace, allow_kill
        self.deadline = None
        self.sequence = 0
        self.used = self.held = False
        self.stop_receipt = None
        self.ready = None

    def prepare(self, deadline):
        require(self.deadline is None and math.isfinite(deadline) and time.monotonic() < deadline,
                "fresh supervisor deadline required")
        require(type(self.allow_kill) is bool and finite(self.lease, 5) and finite(self.term_grace, 10),
                "supervised SDK bounds")
        _, fd, _ = private_directory(self.root)
        os.close(fd)
        require(len(os.fsencode(self.root / CONTROL_NAME)) < 108, "controller socket path too long")
        require(not (self.root / "state").exists() and not (self.root / "state").is_symlink(),
                "fresh supervised fixture state required")
        for name in (CONTROL_NAME, "supervisor-ready.json", "supervisor-stop.json", "supervisor-pipes.jsonl"):
            require(not (self.root / name).exists() and not (self.root / name).is_symlink(), "supervisor target occupied")
        self.deadline = deadline

    def _control(self, op):
        require(not self.held or op == "stop", "supervised SDK held")
        self.sequence += 1
        try:
            info = (self.root / CONTROL_NAME).lstat()
            require(stat.S_ISSOCK(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
                    and info.st_uid == os.geteuid(), "private controller socket required")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(self.term_grace + 3 if op == "stop" else 1)
                connection.connect(str(self.root / CONTROL_NAME))
                pid, uid, _ = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                require(self.ready is not None and pid == self.ready["supervisor"]["pid"]
                        and uid == os.geteuid() and identity(pid) == self.ready["supervisor"],
                        "supervisor peer changed")
                connection.sendall(encode({"seq": self.sequence, "op": op}))
                response = bytearray()
                while not response.endswith(b"\n"):
                    part = connection.recv(4096)
                    require(part and len(response) + len(part) <= 65536, "supervisor control response lost/large")
                    response.extend(part)
                value = decode(bytes(response))
                require(value.get("seq") == self.sequence and value.get("ok") is True,
                        "supervisor control response mismatch")
                return value
        except BaseException:
            self.held = True
            raise

    @asynccontextmanager
    async def __call__(self, argv):
        require(not self.used and self.deadline is not None, "supervised SDK factory not fresh/prepared")
        self.used = True
        require(len(argv) == 8 and argv[:4] == [sys.executable, "-B", str(Path(fixture.__file__).resolve()), "serve"]
                and argv[4] == "--candidate" and argv[6] == "--state"
                and Path(argv[7]) == self.root / "state", "only bound offline fixture argv allowed")
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        args = ["-B", str(Path(__file__).resolve()), "supervisor", "--candidate", argv[5],
                "--root", str(self.root), "--deadline", str(self.deadline),
                "--lease", str(self.lease), "--term-grace", str(self.term_grace)]
        if self.allow_kill:
            args.append("--allow-kill")
        params = StdioServerParameters(command=sys.executable, args=args, env={"PYTHONDONTWRITEBYTECODE": "1"})
        factory = self
        try:
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    self.ready = read_private(self.root, "supervisor-ready.json")
                    require(self.ready["owner"] == identity(os.getpid()), "supervisor owner binding changed")
                    class Proxy:
                        async def call_tool(proxy, name, arguments):
                            await asyncio.to_thread(factory._control, "renew")
                            return await session.call_tool(name, arguments)
                        async def list_tools(proxy, cursor=None):
                            await asyncio.to_thread(factory._control, "renew")
                            return await session.list_tools(cursor=cursor)
                    try:
                        yield Proxy()
                    finally:
                        value = await asyncio.to_thread(self._control, "stop")
                        receipt = value.get("receipt")
                        require(type(receipt) is dict and receipt.get("reason") == "controller_stop"
                                and receipt.get("leader", {}).get("leader_reaped") is True,
                                "supervisor stop uncertain")
                        self.stop_receipt = receipt
        except BaseException:
            self.held = True
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("child", "supervisor"))
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--parent", type=int)
    parser.add_argument("--lease", type=float, default=5)
    parser.add_argument("--term-grace", type=float, default=10)
    parser.add_argument("--allow-kill", action="store_true")
    args = parser.parse_args()
    if args.role == "child":
        child(args.candidate, args.root, args.parent, args.deadline)
    else:
        supervisor(args.candidate, args.root, args.deadline, args.lease, args.term_grace, args.allow_kill)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        # Child and supervisor stderr expose no raw local exception or path.
        print("HOLD: offline supervised fixture stopped or unavailable", file=sys.stderr)
        sys.exit(2)
