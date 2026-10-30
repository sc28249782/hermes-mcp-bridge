"""Private, offline preparation inventory; no launch or scope authority.

Reads nominated files and fixed guest metadata. Never opens the runtime-key file
for reading. A successful inventory cannot complete R1 or authorize R2.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import time

CLIENT_SHA256 = "55c48566e682473a602eea4951978d27acc0f2c8de2340b684a8b114feba7a83"
PEER_SHA256 = "f031f36c02f0eae7b1ce0c5e1baa8abaf996bb20e99d2c94e0a04a0f1d4bc1e3"
MANIFEST_SHA256 = "ef081b19445fa9132f54f434254c04fbf4532b716ad1f994bbc1415261702ab9"
VERSION_REF = "274a5588414819f063d27100a4fb1096aae3830f"
OUTPUT_NAME = "binding-inventory.json"
MAX_SECONDS = 30
O_READ = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
FALSE_FLAGS = ("key_contents_read", "scope_granted", "host_observed",
               "original_runtime_continuity_observed", "authenticated", "complete_writer_coverage",
               "containment_or_delegation_proved", "r1_complete", "r2_authorized")


class Hold(RuntimeError):
    """Constant failure code only; no raw input or exception text."""


def require(value, code):
    if not value:
        raise Hold(code)


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "json")
        result[key] = value
    return result


def _finite(text):
    number = float(text)
    require(math.isfinite(number), "json")
    return number


def decode(raw):
    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_float=_finite,
                          parse_constant=lambda _: (_ for _ in ()).throw(Hold("json")))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise Hold("json") from error


def _signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _open_dir(path):
    path = os.fspath(path)
    require(os.path.isabs(path) and path == os.path.normpath(path), "path")
    current = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.split("/")[1:]:
            if not part:
                continue
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            os.close(current)
            current = nxt
        return current
    except BaseException:
        os.close(current)
        raise


def _private_dir(fd):
    info = os.fstat(fd)
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o700, "directory")
    return (info.st_dev, info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode))


def _file(root_fd, relative, maximum, tick, *, read=True, private=True):
    parts = relative.split("/")
    require(all(p not in ("", ".", "..") for p in parts), "path")
    current = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            os.close(current)
            current = nxt
        tick()
        before = os.stat(parts[-1], dir_fd=current, follow_symlinks=False)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and 0 < before.st_size <= maximum, "file")
        if private:
            require(before.st_uid == os.getuid()
                    and stat.S_IMODE(before.st_mode) in (0o600, 0o700), "file_mode")
        else:
            require(before.st_uid in (0, os.getuid()) and not before.st_mode & 0o022
                    and before.st_mode & 0o111,
                    "executable_mode")
        metadata = {"device": before.st_dev, "inode": before.st_ino,
                    "owner": before.st_uid, "mode": oct(stat.S_IMODE(before.st_mode)),
                    "bytes": before.st_size}
        if not read:
            require(stat.S_IMODE(before.st_mode) == 0o600, "key_mode")
            return None, metadata
        fd = os.open(parts[-1], O_READ, dir_fd=current)
        try:
            require(_signature(os.fstat(fd)) == _signature(before), "file_changed")
            chunks, size = [], 0
            while True:
                tick()
                chunk = os.read(fd, min(262144, maximum + 1 - size))
                if not chunk:
                    break
                size += len(chunk)
                require(size <= maximum, "file_size")
                chunks.append(chunk)
            require(_signature(os.fstat(fd)) == _signature(before), "file_changed")
            require(_signature(os.stat(parts[-1], dir_fd=current, follow_symlinks=False))
                    == _signature(before) and size == before.st_size, "file_changed")
            raw = b"".join(chunks)
            metadata["sha256"] = hashlib.sha256(raw).hexdigest()
            return raw, metadata
        finally:
            os.close(fd)
    finally:
        os.close(current)


def _system_read(path, maximum=262144):
    # Fixed procfs/sysfs paths only; ancestor links are not an isolation claim.
    fd = os.open(path, O_READ)
    try:
        require(stat.S_ISREG(os.fstat(fd).st_mode), "system_file")
        raw = b""
        while True:
            chunk = os.read(fd, min(65536, maximum + 1 - len(raw)))
            if not chunk:
                break
            raw += chunk
            require(len(raw) <= maximum, "system_size")
        return raw.decode("utf-8")
    finally:
        os.close(fd)


def _profile(raw, python, peer, health_port):
    value = decode(raw)
    require(type(value) is dict and type(value.get("control_plane")) is dict, "profile")
    tunnel = value["control_plane"].get("tunnel_id")
    require(type(tunnel) is str and re.fullmatch(
        r"tunnel_(?:[a-z0-9]{4}_)?[a-z0-9]{32}", tunnel), "tunnel_syntax")
    expected = {
        "config_version": 1,
        "control_plane": {"base_url": "https://api.openai.com", "tunnel_id": tunnel,
                          "api_key": "env:S24_PREBIND_RUNTIME_KEY"},
        "health": {"listen_addr": f"127.0.0.1:{health_port}"},
        "admin_ui": {"open_browser": False},
        "log": {"level": "info", "format": "json"},
        "mcp": {"max_concurrent_requests": 1, "stdio_send_initialized_notification": True,
                "commands": [{"channel": "main", "command": f"{python} -I -B {peer} --metadata-only"}]}}
    # Canonical JSON comparison keeps bool distinct from int (True != schema 1).
    require(json.dumps(value, sort_keys=True, allow_nan=False)
            == json.dumps(expected, sort_keys=True), "profile")
    return tunnel


def _collect_body(root, attempt_name, python, *, health_port, clock=time.monotonic, system_read=_system_read):
    """No writes. Injected readers/clocks are test interfaces, not operational proof."""
    start = clock()
    require(type(health_port) is int and 1024 <= health_port <= 65535, "health_port")
    uname = os.uname()
    require(uname.sysname == "Linux" and uname.machine == "x86_64", "guest_architecture")

    def tick():
        elapsed = clock() - start
        require(0 <= elapsed <= MAX_SECONDS, "inventory_time")

    require(re.fullmatch(r"r1-remaining-[A-Za-z0-9_-]{1,64}", attempt_name), "attempt")
    require(type(python) is str and os.path.isabs(python)
            and python == os.path.normpath(python) and python.endswith("/.venv/bin/python")
            and not any(c.isspace() or c in "'\"\\" for c in python), "python_path")
    root = os.fspath(root)
    require(not any(c.isspace() or c in "'\"\\" for c in root), "path")
    root_fd = _open_dir(root)
    attempt_fd = None
    try:
        root_id = _private_dir(root_fd)
        attempt_fd = os.open(attempt_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                             dir_fd=root_fd)
        attempt_id = _private_dir(attempt_fd)
        try:
            os.stat(OUTPUT_NAME, dir_fd=attempt_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise Hold("output_exists")
        _, key = _file(root_fd, "runtime-api-key", 4097, tick, read=False)
        files = {}
        for name, maximum, wanted in (
            ("client/tunnel-client", 33554432, CLIENT_SHA256),
            ("peer/route_prebind.py", 65536, PEER_SHA256),
            ("peer/discovery_manifest.json", 65536, MANIFEST_SHA256)):
            raw, files[name] = _file(root_fd, name, maximum, tick)
            require(files[name]["sha256"] == wanted, "input_hash")
        version, files["version"] = _file(root_fd, "inspection/version.stdout", 1024, tick)
        require(version == f"0.0.18+{VERSION_REF} (git sha: {VERSION_REF})\n".encode(), "version")
        saved, files["saved_python_identity"] = _file(
            root_fd, "inspection-continuation/python.stdout", 65536, tick)
        saved = decode(saved)
        require(type(saved) is dict and saved.get("argv_python") == python
                and saved.get("is_venv") is True and saved.get("python_version") == "3.14.4",
                "saved_python_identity")
        real_python = str(Path(python).resolve(strict=True))
        require(real_python == saved.get("real_executable"), "python_resolution")
        executable_info = os.stat(real_python, follow_symlinks=False)
        require((executable_info.st_dev, executable_info.st_ino) != (key["device"], key["inode"]),
                "key_is_not_executable")
        executable_dir = _open_dir(str(Path(real_python).parent))
        try:
            executable, files["python_executable"] = _file(
                executable_dir, Path(real_python).name, 67108864, tick, private=False)
            require(executable.startswith(b"\x7fELF")
                    and files["python_executable"]["sha256"] == saved.get("executable_sha256"),
                    "python_hash")
        finally:
            os.close(executable_dir)
        raw, files["profile"] = _file(attempt_fd, "profile.yaml", 16384, tick)
        tunnel = _profile(raw, python, str(Path(root) / "peer/route_prebind.py"), health_port)
        deps, files["saved_dependencies"] = _file(attempt_fd, "dependencies.json", 65536, tick)
        deps = decode(deps)
        require(type(deps) is dict and deps.get("is_venv") is True
                and deps.get("python_version") == "3.14.4", "saved_dependencies")
        versions = {}
        for item in deps["distributions"]:
            require(type(item) is dict and type(item.get("name")) is str
                    and type(item.get("version")) is str, "saved_dependencies")
            name = item["name"].lower().replace("_", "-")
            require(name not in versions, "saved_dependencies")
            versions[name] = item["version"]
        require(all(versions.get(n) == v for n, v in {
            "mcp": "1.30.0", "httpx": "0.28.1", "python-dotenv": "1.2.3",
            "pyyaml": "6.0.3"}.items()), "saved_dependencies")
        tick()
        product = system_read("/sys/class/dmi/id/product_name").strip()
        require(product.startswith("VMware"), "guest_kind")
        memory = dict(line.split(":", 1) for line in system_read("/proc/meminfo").splitlines())
        tokens = memory["MemAvailable"].split()
        require(len(tokens) == 2 and tokens[0].isdigit() and tokens[1] == "kB", "memory")
        available = int(tokens[0]) * 1024
        require(available >= 768 * 1024**2, "guest_memory")
        fs = os.fstatvfs(root_fd)
        free_bytes = fs.f_bavail * fs.f_frsize
        require(free_bytes >= 2 * 1024**3, "disk")
        occupied = False
        for name in ("tcp", "tcp6"):
            for line in system_read("/proc/net/" + name).splitlines()[1:]:
                if int(line.split()[1].rsplit(":", 1)[1], 16) == health_port:
                    occupied = True
        require(not occupied, "port_occupied")
        cgroup = system_read("/proc/self/cgroup")
        tick()
        require(_private_dir(root_fd) == root_id and _private_dir(attempt_fd) == attempt_id,
                "directory_changed")
        elapsed = clock() - start
        require(0 <= elapsed <= MAX_SECONDS, "inventory_time")
        return {"evidence_class": "private-prebind-inventory",
                "root": root, "attempt_name": attempt_name,
                "directory_identities": {"root": root_id, "attempt": attempt_id},
                "files": files, "runtime_key_metadata": key, "key_contents_read": False,
                "python_argv": python, "python_real_executable": real_python,
                "saved_dependencies_only": True, "distribution_count": len(versions),
                "tunnel_id_syntax_only": tunnel, "health_port_nomination": health_port,
                "port_free_snapshot_only": True,
                "guest_available_bytes": available, "disk_free_bytes": free_bytes,
                "guest_architecture": uname.machine, "guest_kernel": uname.release,
                "self_cgroup_metadata_only": cgroup,
                "elapsed_seconds": elapsed, "scope_granted": False,
                "host_observed": False, "original_runtime_continuity_observed": False,
                "authenticated": False, "complete_writer_coverage": False,
                "containment_or_delegation_proved": False, "r1_complete": False,
                "r2_authorized": False}
    finally:
        if attempt_fd is not None:
            os.close(attempt_fd)
        os.close(root_fd)


def collect(root, attempt_name, python, *, health_port, observation,
            clock=time.monotonic, system_read=_system_read):
    """Observed invocation. Missing boundary is fatal, never a recoverable error."""
    def boundary(kind, ok):
        try:
            observation.boundary(kind, ok)
        except BaseException:
            os._exit(72)
    boundary('collect_entered', True)
    ok = False
    try:
        report = _collect_body(root, attempt_name, python, health_port=health_port,
                               clock=clock, system_read=system_read)
        ok = True
        return report
    finally:
        boundary('collect_leaving', ok)


def record(report):
    """Write one new private evidence file; never modify any prepared input."""
    require(report.get("evidence_class") == "private-prebind-inventory"
            and all(report.get(name) is False for name in FALSE_FLAGS), "report_scope")
    raw = (json.dumps(report, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= 1048576, "report_size")
    root_fd = _open_dir(report["root"])
    attempt_fd = None
    try:
        attempt_fd = os.open(report["attempt_name"], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                             dir_fd=root_fd)
        require(list(_private_dir(root_fd)) == list(report["directory_identities"]["root"])
                and list(_private_dir(attempt_fd)) == list(report["directory_identities"]["attempt"]),
                "directory_changed")
        fd = os.open(OUTPUT_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=attempt_fd)
        try:
            require(stat.S_IMODE(os.fstat(fd).st_mode) == 0o600, "output_mode")
            offset = 0
            while offset < len(raw):
                written = os.write(fd, raw[offset:])
                require(written > 0, "output_write")
                offset += written
            os.fsync(fd)
        finally:
            os.close(fd)
        os.fsync(attempt_fd)
        return hashlib.sha256(raw).hexdigest()
    finally:
        if attempt_fd is not None:
            os.close(attempt_fd)
        os.close(root_fd)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Hold("arguments")


def main():
    try:
        parser = Parser(description=__doc__)
        parser.add_argument("--root", required=True)
        parser.add_argument("--attempt-name", required=True)
        parser.add_argument("--python-argv", required=True)
        parser.add_argument("--health-port", required=True, type=int)
        args = parser.parse_args()
        report = collect(args.root, args.attempt_name, args.python_argv, health_port=args.health_port)
        sha = record(report)
        print(json.dumps({"status": "INVENTORY_RECORDED_PENDING_REVIEW", "sha256": sha,
                          "key_contents_read": False, "r1_complete": False, "r2_authorized": False}))
        return 0
    except Exception:
        print("HOLD: private inventory incomplete; preserve files; no automatic retry.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    print("HOLD: observed helper is controller-only.", file=sys.stderr)
    raise SystemExit(2)
