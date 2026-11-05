"""Pre-live executable staging for the retained-pidfd fixture.

The caller supplies an independently reviewed digest. This module has no
activation entry point. A future launcher must execute the returned fd itself
and separately establish the inherited FD inventory and E/H containment.
"""
import fcntl
import hashlib
import os
import re
import stat


MAX_EXECUTABLE = 4 * 1024 * 1024
SEALS = (fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW |
         fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)


def verified_image(path, expected_sha256):
    """Return an owned sealed memfd or raise before granting a launch image."""
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise ValueError("invalid reviewed executable digest")
    source = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    image = -1
    try:
        info = os.fstat(source)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_EXECUTABLE:
            raise ValueError("invalid executable source")
        image = os.memfd_create("l1-reviewed-image", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
        remaining = info.st_size
        while remaining:
            block = os.read(source, min(remaining, 65536))
            if not block or os.write(image, block) != len(block):
                raise ValueError("incomplete executable copy")
            remaining -= len(block)
        if os.read(source, 1):
            raise ValueError("executable grew during copy")
        os.fchmod(image, 0o500)
        fcntl.fcntl(image, fcntl.F_ADD_SEALS, SEALS)
        if fcntl.fcntl(image, fcntl.F_GET_SEALS) != SEALS:
            raise ValueError("executable seals incomplete")
        with os.fdopen(os.dup(image), "rb") as snapshot:
            snapshot.seek(0)
            if snapshot.read(4) != b"\x7fELF":
                raise ValueError("expected an ELF image")
            snapshot.seek(0)
            if hashlib.file_digest(snapshot, "sha256").hexdigest() != expected_sha256:
                raise ValueError("reviewed executable digest mismatch")
        os.lseek(image, 0, os.SEEK_SET)
        verified = image
        image = -1
        return verified
    finally:
        if image >= 0:
            os.close(image)
        os.close(source)
