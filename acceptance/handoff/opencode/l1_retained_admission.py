"""Review-only L1 runner. Every result is HOLD; this module cannot launch H."""

import argparse
import hashlib
import json
import os
import re
import stat
import time

from l1_retained_launcher import verified_image


MS = 1_000_000
MAX_MANIFEST = 4096
FD_ROLES = {
    "E": ["stdio", "ready-read", "gate-write", "original-h-pidfd"],
    "H": ["stdio", "ready-write", "gate-read"],
}
FIELDS = {"kind", "image_sha256", "fd_roles", "t0_ns", "ta_ns", "deadline_ns"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


def read_manifest(path, expected_sha256):
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise ValueError("invalid manifest digest")
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("manifest is not a regular file")
        raw = stream.read(MAX_MANIFEST + 1)
    if not 0 < len(raw) <= MAX_MANIFEST:
        raise ValueError("invalid manifest size")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("manifest digest mismatch")
    manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if type(manifest) is not dict or manifest.keys() != FIELDS:
        raise ValueError("invalid manifest schema")
    if manifest["kind"] != "l1-retained-preflight-v1" or manifest["fd_roles"] != FD_ROLES:
        raise ValueError("invalid kind or FD role map")
    if type(manifest["image_sha256"]) is not str:
        raise ValueError("invalid image digest")
    return manifest


def check_deadline(manifest, now):
    t0, ta, deadline = (manifest[k] for k in ("t0_ns", "ta_ns", "deadline_ns"))
    if any(type(value) is not int for value in (t0, ta, deadline)):
        raise ValueError("invalid deadline type")
    if not (0 <= t0 <= ta <= now < deadline <= min(ta + 8000 * MS, t0 + 45000 * MS)
            and deadline - now > 3000 * MS):
        raise ValueError("invalid deadline or insufficient reserve")


def inspect(manifest_path, manifest_digest, image_path, clock=time.monotonic_ns):
    """Check proposed inputs and discard the sealed fd before returning HOLD."""
    try:
        manifest = read_manifest(manifest_path, manifest_digest)
        check_deadline(manifest, clock())
        fd = verified_image(image_path, manifest["image_sha256"])
        try:
            check_deadline(manifest, clock())
        finally:
            os.close(fd)
    except (OSError, ValueError, RecursionError):
        return "INPUT_REJECTED"
    return "E_LOSS_STOP_REAP_UNBOUND"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("manifest_sha256")
    parser.add_argument("image")
    args = parser.parse_args()
    reason = inspect(args.manifest, args.manifest_sha256, args.image)
    print(json.dumps({"status": "HOLD", "reason": reason, "h_launched": False}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
