"""Read-only Linux resource sampler. No launcher, signal, network or approval API."""
import hashlib
import json
import os
from pathlib import Path
import stat
import time

from parent_contract import Hold, require

MIB = 1024 * 1024
MAX_PROCESSES = 4096
MAX_ENTRIES = 10000
MAX_DEPTH = 16
MAX_SAMPLE_SECONDS = 1.0
EVIDENCE_CLASS = "local-read-only-guest-observation"


def read_at(directory, name, limit=65536):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
    try:
        raw = os.read(fd, limit + 1)
        require(len(raw) <= limit, "kernel record oversized")
        return raw
    finally:
        os.close(fd)


def process_stamp(raw):
    try:
        pid = int(raw.split(b" ", 1)[0])
        fields = raw.rsplit(b")", 1)[1].split()
        ticks = int(fields[19])
        require(pid > 0 and ticks > 0, "invalid process identity")
        return pid, ticks
    except (ValueError, IndexError) as error:
        raise Hold("invalid process identity") from error


def available_memory(raw):
    values = {}
    for line in raw.splitlines():
        parts = line.split()
        if parts and parts[0] in (b"MemAvailable:", b"MemTotal:"):
            require(len(parts) == 3 and parts[2] == b"kB" and parts[1].isdigit()
                    and parts[0] not in values, "invalid guest memory record")
            values[parts[0]] = int(parts[1]) * 1024
    require(set(values) == {b"MemAvailable:", b"MemTotal:"}
            and 0 <= values[b"MemAvailable:"] <= values[b"MemTotal:"], "missing/invalid guest memory")
    return values[b"MemAvailable:"]


def resident_bytes(raw, page_size):
    parts = raw.split()
    require(type(page_size) is int and page_size > 0 and len(parts) == 7
            and all(p.isdigit() for p in parts), "invalid RSS record")
    return int(parts[1]) * page_size


def coherent_procfs():
    fd = os.open("/proc/self", os.O_RDONLY | os.O_DIRECTORY)
    try:
        require(process_stamp(read_at(fd, "stat"))[0] == os.getpid(), "procfs PID namespace mismatch")
    finally:
        os.close(fd)


def account_ids():
    """Recognized uid membership, not complete writer/descendant ownership."""
    found = set()
    seen = 0
    with os.scandir("/proc") as entries:
        for entry in entries:
            if not entry.name.isascii() or not entry.name.isdigit():
                continue
            seen += 1
            require(seen <= MAX_PROCESSES, "process scan limit")
            fd = os.open(entry.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                if os.fstat(fd).st_uid == os.geteuid():
                    stamp = process_stamp(read_at(fd, "stat"))
                    require(stamp[0] == int(entry.name), "process namespace mismatch")
                    found.add(stamp)
            finally:
                os.close(fd)
    return found


def process_rss(stamp):
    fd = os.open("/proc/" + str(stamp[0]), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        require(os.fstat(fd).st_uid == os.geteuid() and process_stamp(read_at(fd, "stat")) == stamp,
                "RSS ownership/identity changed")
        value = resident_bytes(read_at(fd, "statm"), os.sysconf("SC_PAGE_SIZE"))
        require(os.fstat(fd).st_uid == os.geteuid() and process_stamp(read_at(fd, "stat")) == stamp,
                "RSS ownership/identity changed")
        return value
    finally:
        os.close(fd)


def account_rss():
    before = account_ids()
    require(before, "empty account observation")
    total = sum(process_rss(stamp) for stamp in before)
    require(account_ids() == before, "account membership changed")
    digest = hashlib.sha256(json.dumps(sorted(before), separators=(",", ":")).encode()).hexdigest()
    return total, len(before), digest


def private_root(path):
    path = Path(path).absolute()
    require(path == path.resolve(strict=True), "root symlink boundary")
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(info.st_uid == os.geteuid() and info.st_mode & 0o077 == 0, "private owned root required")
        return path, (info.st_dev, info.st_ino)
    finally:
        os.close(fd)


def tree_usage(root, expected):
    """Metadata only, no file contents. Reject unmeasured links and special files."""
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    rows = []
    entries = allocated = logical = 0
    def walk(directory, prefix, depth):
        nonlocal entries, allocated, logical
        require(depth <= MAX_DEPTH, "tree depth limit")
        own = os.fstat(directory)
        require(own.st_uid == os.geteuid(), "tree owner mismatch")
        allocated += own.st_blocks * 512
        with os.scandir(directory) as listing:
            for entry in listing:
                entries += 1
                require(entries <= MAX_ENTRIES, "tree entry limit")
                info = os.stat(entry.name, dir_fd=directory, follow_symlinks=False)
                require(info.st_uid == os.geteuid() and info.st_dev == expected[0],
                        "tree owner/filesystem mismatch")
                relative = prefix + entry.name
                rows.append((relative, info.st_dev, info.st_ino, info.st_mode,
                             info.st_size, info.st_blocks, info.st_mtime_ns, info.st_ctime_ns))
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                    try:
                        actual = os.fstat(child)
                        require((actual.st_dev, actual.st_ino) == (info.st_dev, info.st_ino), "tree directory changed")
                        walk(child, relative + "/", depth + 1)
                    finally:
                        os.close(child)
                else:
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "unsupported tree entry")
                    allocated += info.st_blocks * 512
                    logical += info.st_size
    try:
        info = os.fstat(fd)
        require((info.st_dev, info.st_ino) == expected, "root identity changed")
        walk(fd, "", 0)
        free = os.fstatvfs(fd)
        digest = hashlib.sha256(json.dumps(sorted(rows), ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()
        return {"allocated_bytes": allocated, "logical_file_bytes": logical,
                "entries": entries, "metadata_sha256": digest,
                "disk_available_bytes": free.f_bavail * free.f_frsize}
    finally:
        os.close(fd)


def guest_limit_failures(sample):
    bounds = (("guest_available_bytes", 768 * MIB, True),
              ("account_rss_sampled_bytes", 768 * MIB, False),
              ("disk_available_bytes", 2048 * MIB, True),
              ("workspace_growth_bytes", 2048 * MIB, False),
              ("logs_logical_bytes", 128 * MIB, False))
    failed = []
    for key, threshold, minimum in bounds:
        value = sample.get(key)
        require(type(value) is int and (value >= 0 or key == "workspace_growth_bytes"),
                "invalid guest measurement type")
        if (minimum and value < threshold) or (not minimum and value > threshold):
            failed.append(key)
    return failed


class GuestObserver:
    """One-shot samples from fixed private roots; no background job or automatic retry.

    Each failure permanently closes this instance. A caller must stop stimulus and
    retain evidence; this sampler cannot stop a child or create a new attempt.
    """
    def __init__(self, workspace, logs):
        coherent_procfs()
        self.workspace, self.workspace_id = private_root(workspace)
        self.logs, self.logs_id = private_root(logs)
        require(self.logs != self.workspace and self.logs.is_relative_to(self.workspace), "logs must be nested")
        self.baseline = tree_usage(self.workspace, self.workspace_id)["allocated_bytes"]
        self.held = False

    def sample(self):
        try:
            require(not self.held, "observer closed")
            started = time.monotonic()
            coherent_procfs()
            # Revalidate private roots for every sample, not just constructor time.
            require(private_root(self.workspace)[1] == self.workspace_id
                    and private_root(self.logs)[1] == self.logs_id, "root identity changed")
            fd = os.open("/proc", os.O_RDONLY | os.O_DIRECTORY)
            try:
                memory = available_memory(read_at(fd, "meminfo"))
            finally:
                os.close(fd)
            rss, count, membership = account_rss()
            workspace = tree_usage(self.workspace, self.workspace_id)
            logs = tree_usage(self.logs, self.logs_id)
            coherent_procfs()
            finished = time.monotonic()
            require(0 <= finished - started <= MAX_SAMPLE_SECONDS, "late guest sample")
            result = {"evidence_class": EVIDENCE_CLASS, "started_monotonic": started,
                    "finished_monotonic": finished, "guest_available_bytes": memory,
                    "account_rss_sampled_bytes": rss, "account_process_count": count,
                    "account_membership_sha256": membership,
                    "disk_available_bytes": workspace["disk_available_bytes"],
                    "workspace_allocated_bytes": workspace["allocated_bytes"],
                    "workspace_growth_bytes": workspace["allocated_bytes"] - self.baseline,
                    "logs_logical_bytes": logs["logical_file_bytes"],
                    "workspace_metadata_sha256": workspace["metadata_sha256"],
                    "logs_metadata_sha256": logs["metadata_sha256"],
                    "host_observed": False, "complete_writer_coverage": False,
                    "full_checkpoint_pass": False}
            result["guest_limit_failures"] = guest_limit_failures(result)
            return result
        except BaseException:
            self.held = True
            raise
