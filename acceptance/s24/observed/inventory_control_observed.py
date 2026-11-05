"""One-shot, stdlib-only controller for the exact reviewed private inventory.

No client/peer/fixture command or credential loader. Scope timestamps are caller
data, not approval. A controller receipt never completes R1 or authorizes R2.
"""
import argparse
import base64
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import selectors
import signal
import stat
import subprocess
import sys
import time
import types

# Exact checked protocol bytes, never current-directory imports.
import stat as _stat
import types as _types

def _load_observation_protocol():
    path = Path(__file__).absolute().with_name('observation_protocol.py')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not (_stat.S_ISREG(info.st_mode) and info.st_uid in (0, os.getuid())
                and info.st_nlink == 1 and not info.st_mode & 0o022 and info.st_size <= 131072):
            raise RuntimeError('protocol source')
        raw = bytearray()
        while True:
            part = os.read(fd, 131073 - len(raw))
            if not part:
                break
            raw.extend(part)
            if len(raw) > 131072:
                raise RuntimeError('protocol size')
        after = os.fstat(fd)
        if hashlib.sha256(raw).hexdigest() != '34100540890928ac24e621543aee01abc0026e10c43d95c346e57b371894fc2f' or any(
                getattr(info, key) != getattr(after, key) for key in
                ('st_dev','st_ino','st_uid','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')):
            raise RuntimeError('protocol hash')
    finally:
        os.close(fd)
    module = _types.ModuleType('bound_observation_protocol')
    module.__file__ = str(path)
    exec(compile(bytes(raw), str(path), 'exec'), module.__dict__)
    return module


OBS = None

INVENTORY_SHA256 = "515d9ed26dd5b189a10cf1562a37064ce3f21528c83dc6dd902bd3675c36ddce"
CLAIM = "inventory-control-claim.json"
TRACE = "inventory-control-trace.jsonl"
RECEIPT = "inventory-control-receipt.json"
CONTROL_SECONDS = 60
STOP_AT_SECONDS = 48
WORKER_SECONDS = 40
TRACE_LIMIT = 1048576
SCOPE_FLAGS = {"scope_granted": False, "r1_complete": False, "r2_authorized": False,
               "complete_writer_coverage": False, "descendant_cessation_proved": False,
               "key_contents_read": False, "host_observed": False, "authenticated": False,
               "original_runtime_continuity_observed": False,
               "containment_or_delegation_proved": False}


class Hold(RuntimeError):
    pass


class StopUnconfirmed(Hold):
    def __init__(self, process, target):
        super().__init__("worker stop unconfirmed")
        self.process, self.target = process, target


def require(value, code):
    if not value:
        raise Hold(code)


def bounded(value, maximum):
    return type(value) in (int, float) and math.isfinite(value) and 0 < value <= maximum


def load_inventory():
    """Compile the exact checked bytes, rather than re-open after a hash check."""
    path = Path(__file__).absolute().with_name("prebind_inventory_observed.py")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and info.st_uid in (0, os.getuid())
                and not info.st_mode & 0o022 and info.st_size <= 65536, "inventory source")
        raw = b""
        while True:
            chunk = os.read(fd, 65537 - len(raw))
            if not chunk:
                break
            raw += chunk
            require(len(raw) <= 65536, "inventory source size")
        require(hashlib.sha256(raw).hexdigest() == INVENTORY_SHA256, "inventory source hash")
    finally:
        os.close(fd)
    module = types.ModuleType("s24_bound_inventory")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def identity(pid):
    require(int(Path("/proc/self/stat").read_text().split(" ", 1)[0]) == os.getpid(),
            "procfs coherence")
    root = Path("/proc") / str(pid)
    raw = (root / "stat").read_text()
    require(int(raw.split(" ", 1)[0]) == pid, "process identity")
    fields = raw.rsplit(")", 1)[1].split()
    return {"pid": pid, "start_ticks": int(fields[19]), "ppid": int(fields[1]),
            "uid": root.stat().st_uid, "exe": os.readlink(root / "exe"),
            "argv": [os.fsdecode(a) for a in (root / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")]}


class Target:
    """Retained pidfd for one new unreaped direct Popen child, never a stored PID."""
    def __init__(self, process, argv):
        require(isinstance(process, subprocess.Popen) and process.args == argv
                and type(argv) is list and Path(argv[0]).is_absolute(), "owned child")
        require(hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"), "pidfd")
        require(os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None,
                "child ended")
        expected = identity(process.pid)
        require(expected["ppid"] == os.getpid() and expected["uid"] == os.getuid()
                and expected["argv"] == argv
                and expected["exe"] == str(Path(argv[0]).resolve(strict=True)), "adoption identity")
        fd = os.pidfd_open(process.pid)
        try:
            require(not select.select([fd], [], [], 0)[0] and identity(process.pid) == expected,
                    "adoption changed")
        except BaseException:
            os.close(fd)
            raise
        self.process, self.identity, self.fd, self.signals = process, expected, fd, []

    def send_signal(self, number):
        require(number in (signal.SIGTERM, signal.SIGKILL), "stop signal")
        if select.select([self.fd], [], [], 0)[0]:
            return
        require(identity(self.identity["pid"]) == self.identity, "stop identity changed")
        try:
            signal.pidfd_send_signal(self.fd, number)
            self.signals.append(int(number))
        except ProcessLookupError:
            pass

    def close(self):
        require(self.process.returncode is not None, "retain unconfirmed target")
        os.close(self.fd)


def ready_frame(process, deadline):
    fd = process.stdout.fileno()
    os.set_blocking(fd, False)
    raw = b""
    while time.monotonic() < deadline:
        if not select.select([fd], [], [], min(0.05, max(0, deadline - time.monotonic())))[0]:
            continue
        chunk = os.read(fd, 513 - len(raw))
        require(chunk, "startup EOF")
        raw += chunk
        require(len(raw) <= 512, "startup size")
        if b"\n" in raw:
            require(raw.endswith(b"\n") and raw.count(b"\n") == 1, "startup frame")
            value = strict_json(raw)
            require(type(value) is dict and set(value) == {"event", "pid", "parent"}
                    and type(value["pid"]) is int and type(value["parent"]) is int
                    and value == {"event": "inventory_ready", "pid": process.pid, "parent": os.getpid()},
                    "startup identity")
            return raw
    raise Hold("startup deadline")


def result_frame(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 65536
            and raw.endswith(b"\n") and raw.count(b"\n") == 1, "result frame")
    value = strict_json(raw)
    require(type(value) is dict and set(value) == {
        "event", "status", "sha256", "key_contents_read", "r1_complete", "r2_authorized"}, "result shape")
    require(value["event"] == "inventory_result"
            and value["status"] == "INVENTORY_RECORDED_PENDING_REVIEW"
            and type(value["sha256"]) is str and re.fullmatch("[a-f0-9]{64}", value["sha256"])
            and all(value[k] is False for k in ("key_contents_read", "r1_complete", "r2_authorized")),
            "result scope")
    return value


def _unique(items):
    value = {}
    for key, data in items:
        require(key not in value, "duplicate result key")
        value[key] = data
    return value


def strict_json(raw):
    def invalid(_):
        raise Hold("nonfinite JSON")
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=invalid)


def write_json(directory_fd, name, value):
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    require(len(raw) <= 65536, "record size")
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory_fd)
    try:
        require(stat.S_IMODE(os.fstat(fd).st_mode) == 0o600, "record mode")
        view = memoryview(raw)
        while view:
            n = os.write(fd, view)
            require(n > 0, "record write")
            view = view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.fsync(directory_fd)
    return hashlib.sha256(raw).hexdigest()


class Trace:
    def __init__(self, directory_fd):
        self.fd = os.open(TRACE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                          0o600, dir_fd=directory_fd)
        self.size = 0
        try:
            require(stat.S_IMODE(os.fstat(self.fd).st_mode) == 0o600, "trace mode")
            os.fsync(self.fd)
            os.fsync(directory_fd)
        except BaseException:
            os.close(self.fd)
            raise

    def append(self, direction, data):
        raw = (json.dumps({"direction": direction,
                           "bytes_base64": base64.b64encode(data).decode()}) + "\n").encode()
        require(self.size + len(raw) <= TRACE_LIMIT, "trace budget")
        view = memoryview(raw)
        while view:
            n = os.write(self.fd, view)
            require(n > 0, "trace write")
            self.size += n
            view = view[n:]
        os.fsync(self.fd)

    def close(self):
        os.close(self.fd)


def monitor(target, trace, started, *, stop_after=STOP_AT_SECONDS, grace=10, allow_kill=False):
    require(bounded(stop_after, STOP_AT_SECONDS) and bounded(grace, 10)
            and type(allow_kill) is bool, "monitor bounds")
    process = target.process
    selector = selectors.DefaultSelector()
    stdout, stderr = bytearray(), bytearray()
    held = False
    stopped_at = None
    drain_until = None
    try:
        for stream, label in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while True:
            now = time.monotonic()
            if now - started >= stop_after and stopped_at is None:
                held = True
                target.send_signal(signal.SIGTERM)
                stopped_at = now
            if stopped_at is not None and now - stopped_at >= grace and drain_until is None:
                if allow_kill:
                    target.send_signal(signal.SIGKILL)
                drain_until = now + 0.5
            if process.poll() is not None and not selector.get_map():
                break
            if drain_until is not None and now >= drain_until:
                raise StopUnconfirmed(process, target)
            for key, _ in selector.select(0.02):
                data = os.read(key.fileobj.fileno(), 4096)
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                trace.append(key.data, data)
                output = stdout if key.data == "stdout" else stderr
                output.extend(data)
                require(len(output) <= 65536, "output budget")
        process.wait(timeout=0.5)
        return bytes(stdout), bytes(stderr), held
    finally:
        selector.close()


def settle(process, target, *, allow_kill, grace=10, send_term=True):
    """Drain failed evidence without claiming it is complete; retain on uncertainty.

    No signal is sent if adoption or identity validation failed. Closing the G
    pipe lets the real worker fail its barrier. Its independent timer remains.
    """
    if process.stdin and not process.stdin.closed:
        process.stdin.close()
    selector = selectors.DefaultSelector()
    deadline = time.monotonic() + grace
    killed = False
    try:
        for stream in (process.stdout, process.stderr):
            if not stream.closed:
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ)
        if send_term and target is not None and process.poll() is None:
            try:
                target.send_signal(signal.SIGTERM)
            except (Hold, OSError):
                pass  # Retain the handle; never target an unvalidated identity.
        while True:
            if process.poll() is not None and not selector.get_map():
                return
            if time.monotonic() >= deadline:
                if not killed and allow_kill and target is not None:
                    try:
                        target.send_signal(signal.SIGKILL)
                    except (Hold, OSError):
                        pass
                    killed = True
                    deadline = time.monotonic() + 0.5
                else:
                    raise StopUnconfirmed(process, target)
            for key, _ in selector.select(0.02):
                if not os.read(key.fileobj.fileno(), 4096):
                    selector.unregister(key.fileobj)
    finally:
        selector.close()


def close_reaped(process, target):
    require(process.returncode is not None, "retain unreaped process")
    if target is not None:
        target.close()
    for stream in (process.stdin, process.stdout, process.stderr):
        if stream and not stream.closed:
            stream.close()


def absent(directory_fd, names):
    for name in names:
        try:
            os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            continue
        raise Hold("existing evidence")


def verify_directories(helper, root, attempt, ids):
    """Compare current named paths as well as the retained directory handles."""
    root_fd = helper._open_dir(root)
    try:
        require(list(helper._private_dir(root_fd)) == ids["root"], "root replaced")
        attempt_fd = os.open(attempt, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
        try:
            require(list(helper._private_dir(attempt_fd)) == ids["attempt"], "attempt replaced")
        finally:
            os.close(attempt_fd)
    finally:
        os.close(root_fd)


def arm_worker(parent):
    require(os.getppid() == parent, "worker parent")
    require(signal.getitimer(signal.ITIMER_REAL)[0] == 0, "existing worker timer")
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, WORKER_SECONDS)
    libc = ctypes.CDLL(None, use_errno=True)
    require(libc.prctl(1, int(signal.SIGTERM), 0, 0, 0) == 0, "parent death arm")
    require(os.getppid() == parent, "worker parent changed")


def worker(args):
    global OBS
    arm_worker(args.parent)
    OBS = _load_observation_protocol()
    OBS.correlation(args.binding_sha256, args.challenge)
    helper = load_inventory()
    raw = (json.dumps({"event": "inventory_ready", "pid": os.getpid(), "parent": args.parent}) + "\n").encode()
    require(os.write(sys.stdout.fileno(), raw) == len(raw), "ready write")
    require(select.select([sys.stdin.fileno()], [], [], 5)[0], "handoff deadline")
    require(os.read(sys.stdin.fileno(), 2) == b"G", "handoff denied")
    require(0 <= time.time() - args.scope_start_epoch < 900, "scope expired")
    marker = OBS.Marker(args.observation_fd, args.binding_sha256, args.challenge)
    report = helper.collect(args.root, args.attempt_name, args.python_argv,
                            health_port=args.health_port, observation=marker)
    require({k: list(v) for k, v in report["directory_identities"].items()}
            == strict_json(args.directory_identities), "worker directory binding")
    sha = helper.record(report)
    value = {"event": "inventory_result", "status": "INVENTORY_RECORDED_PENDING_REVIEW",
             "sha256": sha, "key_contents_read": False, "r1_complete": False, "r2_authorized": False}
    raw = (json.dumps(value) + "\n").encode()
    require(os.write(sys.stdout.fileno(), raw) == len(raw), "result write")
    return 0


def run_once(args):
    started = time.monotonic()
    require(type(args.scope_start_epoch) is float and math.isfinite(args.scope_start_epoch)
            and 0 <= time.time() - args.scope_start_epoch <= 840, "scope timing")
    require(type(args.allow_kill) is bool and type(args.health_port) is int
            and 1024 <= args.health_port <= 65535, "controller arguments")
    helper = load_inventory()
    require(re.fullmatch(r"r1-remaining-[A-Za-z0-9_-]{1,64}", args.attempt_name), "attempt")
    root_fd = helper._open_dir(args.root)
    attempt_fd, process, target, trace = None, None, None, None
    confirmed, held, result, signals = False, False, None, []
    stage, failure_stage, failure_class = "preparation", None, None
    inventory_verified = False
    try:
        root_id = helper._private_dir(root_fd)
        attempt_fd = os.open(args.attempt_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
        attempt_id = helper._private_dir(attempt_fd)
        ids = {"root": list(root_id), "attempt": list(attempt_id)}
        absent(attempt_fd, (helper.OUTPUT_NAME, CLAIM, TRACE, RECEIPT))
        write_json(attempt_fd, CLAIM, {"evidence_class": "inventory-control-claim", **SCOPE_FLAGS,
                                      "scope_start_epoch_caller_data": args.scope_start_epoch,
                                      "inventory_sha256": INVENTORY_SHA256})
        trace = Trace(attempt_fd)
        require(time.monotonic() - started < 5, "preparation deadline")
        argv = [sys.executable, "-I", "-S", "-B", str(Path(__file__).absolute()), "--worker",
                "--parent", str(os.getpid()), "--root", args.root, "--attempt-name", args.attempt_name,
                "--python-argv", args.python_argv, "--health-port", str(args.health_port),
                "--scope-start-epoch", str(args.scope_start_epoch), "--directory-identities", json.dumps(ids),
                "--observation-fd", str(args.observation_fd), "--binding-sha256", args.binding_sha256,
                "--challenge", args.challenge]
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, bufsize=0, cwd="/",
                                   env={"PATH": "/usr/bin:/bin", "LANG": "C"}, close_fds=True,
                                   pass_fds=(args.observation_fd,))
        try:
            stage = "startup"
            ready = ready_frame(process, min(started + 10, time.monotonic() + 5))
            stage = "adoption"
            target = Target(process, argv)
            trace.append("ready", ready)
            trace.append("owned_identity", json.dumps(target.identity).encode())
            marker = OBS.Marker(args.observation_fd, args.binding_sha256, args.challenge)
            marker.emit("worker_bound", target.identity, True)
            os.close(args.observation_fd)
            args.observation_fd = -1
            require(time.monotonic() - started < 10, "adoption deadline")
            stage = "handoff"
            trace.append("handoff_intent", b"G")
            require(os.write(process.stdin.fileno(), b"G") == 1, "handoff write")
            trace.append("handoff_written_not_consumption", b"G")
            process.stdin.close()
            stage = "worker"
            stdout, stderr, held = monitor(target, trace, started, allow_kill=args.allow_kill)
            confirmed = process.returncode is not None
            require(process.returncode == 0 and stderr == b"" and not held, "worker failed")
            stage = "result validation"
            result = result_frame(stdout)
        except StopUnconfirmed:
            raise
        except BaseException as error:
            held = True
            failure_stage, failure_class = stage, type(error).__name__
            settle(process, target, allow_kill=args.allow_kill)
            confirmed = process.returncode is not None
            if not confirmed:
                raise StopUnconfirmed(process, target)
        require(confirmed, "stop confirmation")
        if target is not None:
            signals = target.signals[:]
        close_reaped(process, target)
        target = None
        if not held:
            try:
                def tick():
                    require(time.monotonic() - started < CONTROL_SECONDS, "verification deadline")
                raw, metadata = helper._file(attempt_fd, helper.OUTPUT_NAME, 1048576, tick)
                inventory = helper.decode(raw)
                require(metadata["mode"] == "0o600" and metadata["sha256"] == result["sha256"]
                        and inventory.get("evidence_class") == "private-prebind-inventory"
                        and inventory.get("root") == args.root
                        and inventory.get("attempt_name") == args.attempt_name
                        and inventory.get("python_argv") == args.python_argv
                        and type(inventory.get("health_port_nomination")) is int
                        and inventory["health_port_nomination"] == args.health_port
                        and inventory.get("directory_identities") == ids
                        and all(inventory.get(k) is False for k in helper.FALSE_FLAGS), "inventory evidence")
                inventory_verified = True
            except Exception as error:
                held, failure_stage, failure_class = True, "stopped inventory verification", type(error).__name__
        require(time.monotonic() - started < CONTROL_SECONDS
                and 0 <= time.time() - args.scope_start_epoch < 900, "final deadline")
        require(helper._private_dir(root_fd) == root_id and helper._private_dir(attempt_fd) == attempt_id,
                "final directory identity")
        verify_directories(helper, args.root, args.attempt_name, ids)
        receipt = {"evidence_class": "inventory-direct-worker-control",
                   "status": "HOLD" if held else "CONTROL_COMPLETE_PENDING_REVIEW",
                   "leader_reaped": True, "exit_code": process.returncode, "signals": signals,
                   "failure_stage": failure_stage, "failure_class": failure_class,
                   "inventory_bytes_verified_after_stop": inventory_verified,
                   "result": result, "inventory_sha256": INVENTORY_SHA256,
                   "elapsed_seconds": time.monotonic() - started, **SCOPE_FLAGS}
        sha = write_json(attempt_fd, RECEIPT, receipt)
        return {"status": receipt["status"], "receipt_sha256": sha, **SCOPE_FLAGS}, 2 if held else 0
    finally:
        if trace is not None:
            trace.close()
        if attempt_fd is not None:
            os.close(attempt_fd)
        os.close(root_fd)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Hold("arguments")


def main():
    global OBS
    armed = False
    try:
        parser = Parser(description=__doc__)
        parser.add_argument("--root", required=True)
        parser.add_argument("--attempt-name", required=True)
        parser.add_argument("--python-argv", required=True)
        parser.add_argument("--health-port", required=True, type=int)
        parser.add_argument("--scope-start-epoch", required=True, type=float)
        parser.add_argument("--allow-kill", action="store_true")
        parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
        parser.add_argument("--parent", type=int, help=argparse.SUPPRESS)
        parser.add_argument("--directory-identities", help=argparse.SUPPRESS)
        parser.add_argument("--observation-fd", type=int, required=True)
        parser.add_argument("--binding-sha256", required=True)
        parser.add_argument("--challenge", required=True)
        args = parser.parse_args()
        if args.worker:
            require(type(args.parent) is int and args.parent > 0
                    and type(args.directory_identities) is str and not args.allow_kill, "worker role")
            return worker(args)
        require(args.parent is None and args.directory_identities is None, "role")
        require(signal.getitimer(signal.ITIMER_REAL)[0] == 0
                and signal.getsignal(signal.SIGALRM) == signal.SIG_DFL, "existing controller timer")
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, CONTROL_SECONDS)
        armed = True
        OBS = _load_observation_protocol()
        OBS.correlation(args.binding_sha256, args.challenge)
        OBS.Marker(args.observation_fd, args.binding_sha256, args.challenge)
        summary, code = run_once(args)
        print(json.dumps(summary))
        return code
    except StopUnconfirmed as error:
        print("HOLD: worker stop unconfirmed; no receipt; preserve files.", file=sys.stderr, flush=True)
        # Keep Popen, pipes and pidfd alive. The already-armed absolute controller
        # timer ends this wait; worker parent-death and 40s timer remain armed.
        # If reap and EOF become certain, release handles, but never invent a receipt.
        settle(error.process, error.target, allow_kill=False, grace=CONTROL_SECONDS, send_term=False)
        close_reaped(error.process, error.target)
        return 2
    except SystemExit as error:
        return error.code
    except BaseException:
        print("HOLD: inventory control incomplete; preserve files; no automatic retry.", file=sys.stderr)
        return 2
    finally:
        if armed:
            signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    raise SystemExit(main())
