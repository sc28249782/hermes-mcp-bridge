"""One-use local launch admission; no launcher, CLI or operational authority.

The approved caller must use the same bound private attempt directory. A new
directory is a new attempt requiring its own approval, not automatic recovery.
"""
import json
import math
import os
from pathlib import Path
import re
import stat
import threading
import time

from parent_contract import Hold, require

EVIDENCE_CLASS = "offline-single-use-launch-admission"
CLAIM_NAME = "launch-claim.json"
LIMIT = 65536


def private_directory(path):
    require(isinstance(path, (str, Path)), "directory path required")
    path = Path(path).absolute()
    require(path == path.resolve(strict=True), "canonical attempt directory required")
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700,
                "private owned attempt directory required")
        return path, fd, (info.st_dev, info.st_ino)
    except BaseException:
        os.close(fd)
        raise


class LaunchAdmission:
    """Reserve a fixed name durably, then dispatch one injected callback at most once.

    A claim is never deleted, unlocked, resumed or treated as a receipt. Existing,
    partial and stale claims all block. The binding digest is data, not approval
    authentication. The callback's process lifecycle belongs to its caller.
    """

    def __init__(self, directory, *, attempt_id, binding_sha256, candidate_commit,
                 fixture_commit, argv, window=1200):
        require(type(attempt_id) is str and re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", attempt_id),
                "attempt identifier")
        for value, length in ((binding_sha256, 64), (candidate_commit, 40), (fixture_commit, 40)):
            require(type(value) is str and re.fullmatch(r"[0-9a-f]{%d}" % length, value),
                    "exact binding digest and commits required")
        require(type(argv) is list and 0 < len(argv) <= 32 and all(
                type(arg) is str and 0 < len(arg.encode("utf-8")) <= 4096
                and "\0" not in arg for arg in argv), "bounded exact argv required")
        require(sum(len(arg.encode("utf-8")) for arg in argv) <= 16384
                and Path(argv[0]).is_absolute(), "absolute executable and argv budget required")
        require(type(window) in (int, float) and math.isfinite(window) and 0 < window <= 1200,
                "finite admission window required")
        self._used = True
        self._lock = threading.Lock()
        self._creator_pid = os.getpid()
        self._argv = tuple(argv)
        self._deadline = time.monotonic() + window
        self._raw = (json.dumps({
            "evidence_class": EVIDENCE_CLASS, "format": 1,
            "attempt_id": attempt_id, "binding_sha256": binding_sha256,
            "candidate_commit": candidate_commit, "fixture_commit": fixture_commit,
            "argv": list(self._argv), "window_seconds": window,
            "state": "reserved-no-outcome", "approval_authenticated": False,
            "writer_cessation_proved": False,
        }, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        require(len(self._raw) <= LIMIT, "claim byte limit")
        self._path, directory_fd, self._directory_identity = private_directory(directory)
        claim_fd = None
        try:
            # O_EXCL is the cross-process arbitration. Never remove an existing claim.
            claim_fd = os.open(CLAIM_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                               | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory_fd)
            info = os.fstat(claim_fd)
            require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
                    and info.st_nlink == 1 and info.st_uid == os.geteuid()
                    and info.st_dev == self._directory_identity[0], "private claim file required")
            self._claim_identity = (info.st_dev, info.st_ino)
            remaining = memoryview(self._raw)
            while remaining:
                count = os.write(claim_fd, remaining)
                require(count > 0, "claim write failed")
                remaining = remaining[count:]
            os.fsync(claim_fd)
            os.fsync(directory_fd)
            self._used = False
        except OSError as exc:
            raise Hold("claim reservation failed; retain evidence, no automatic retry") from exc
        finally:
            if claim_fd is not None:
                os.close(claim_fd)
            os.close(directory_fd)

    def __copy__(self):
        raise Hold("admission cannot be copied")

    def __deepcopy__(self, memo):
        raise Hold("admission cannot be copied")

    def __reduce_ex__(self, protocol):
        raise Hold("admission cannot be serialized")

    def dispatch_once(self, launcher):
        """Call launcher(exact_argv_copy) once; never spawn, retry or stop on its behalf.

        The pre-dispatch clock check is not a supervisor or an interruptible
        deadline. A blocked/delayed callback needs independent lifecycle control.
        """
        # Check before touching a lock inherited across fork from another thread.
        require(os.getpid() == self._creator_pid, "admission belongs to its creating process")
        with self._lock:
            require(not self._used, "admission consumed")
            self._used = True  # All subsequent failures consume this instance too.
        require(callable(launcher), "launcher callback required")
        require(time.monotonic() < self._deadline, "admission window expired")
        _, directory_fd, identity = private_directory(self._path)
        claim_fd = None
        try:
            require(identity == self._directory_identity, "attempt directory changed")
            claim_fd = os.open(CLAIM_NAME, os.O_RDONLY | os.O_NOFOLLOW
                               | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory_fd)
            info = os.fstat(claim_fd)
            require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
                    and info.st_uid == os.geteuid() and info.st_nlink == 1
                    and (info.st_dev, info.st_ino) == self._claim_identity,
                    "claim identity or permissions changed")
            raw = os.read(claim_fd, LIMIT + 1)
            require(raw == self._raw, "claim bytes changed")
        except OSError as exc:
            raise Hold("claim recheck failed") from exc
        finally:
            if claim_fd is not None:
                os.close(claim_fd)
            os.close(directory_fd)
        require(time.monotonic() < self._deadline, "admission window expired")
        return launcher(list(self._argv))
