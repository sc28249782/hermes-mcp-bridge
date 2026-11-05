"""Stage the preparation-only checkout with its historical SPEC input."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

FROZEN_REVISION = "d7515c5fb4e33b41f81a8535fb06a0ea2cd72255"
FROZEN_SPEC_SHA256 = "d0f97851b7d1984cc6f2b249541f4b54bcd8f6f2e2f0c9f238d21055bcdccc65"
REPOSITORY = "https://github.com/sc28249782/hermes-mcp-bridge.git"
SPEC_PATH = "docs/SPEC.md"
MAX_SPEC_BYTES = 262144
MAX_FILES = 4096
MAX_COPY_BYTES = 32 * 1024 * 1024
EVIDENCE_PATHS = tuple(
    f"acceptance/handoff/evaluation/{name}"
    for name in ("protocol.json", "harness.py", "development-receipt.json", "heldout-receipt.json")
)


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, stdout=subprocess.PIPE, timeout=60
    ).stdout


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stage(repo, history, head, destination):
    repo, history, destination = (Path(p).resolve() for p in (repo, history, destination))
    if not re.fullmatch(r"[0-9a-f]{40}", head) or git(repo, "rev-parse", "HEAD").decode().strip() != head:
        raise ValueError("PR head mismatch")
    if destination.is_relative_to(repo) or destination.is_relative_to(history):
        raise ValueError("preparation copy must be outside both repositories")
    frozen_object = f"{FROZEN_REVISION}:{SPEC_PATH}"
    if git(history, "cat-file", "-t", frozen_object).strip() != b"blob":
        raise ValueError("frozen SPEC is not a blob")
    size = int(git(history, "cat-file", "-s", frozen_object))
    if not 0 < size <= MAX_SPEC_BYTES:
        raise ValueError("frozen SPEC size outside limit")
    frozen = git(history, "cat-file", "blob", frozen_object)
    if len(frozen) != size or digest(frozen) != FROZEN_SPEC_SHA256:
        raise ValueError("frozen SPEC SHA-256 mismatch")
    for path in EVIDENCE_PATHS:
        if git(repo, "rev-parse", f"{head}:{path}") != git(history, "rev-parse", f"{FROZEN_REVISION}:{path}"):
            raise ValueError(f"frozen evidence changed: {path}")

    entries = git(repo, "ls-tree", "-rlz", head).split(b"\0")
    files = {}
    total = 0
    for entry in entries[:-1]:
        metadata, name = entry.split(b"\t", 1)
        mode, kind, oid, count = metadata.split()
        path = PurePosixPath(name.decode("utf-8"))
        if kind != b"blob" or mode not in (b"100644", b"100755"):
            raise ValueError("preparation copy accepts regular Git files only")
        if path.is_absolute() or ".." in path.parts or ".git" in path.parts or path in files:
            raise ValueError("unsafe preparation path")
        count = int(count)
        total += count
        if len(files) >= MAX_FILES or total > MAX_COPY_BYTES:
            raise ValueError("preparation copy exceeds size limit")
        files[path] = (mode, oid.decode("ascii"), count)
    spec_key = PurePosixPath(SPEC_PATH)
    if spec_key not in files or not 0 < files[spec_key][2] <= MAX_SPEC_BYTES:
        raise ValueError("current SPEC missing or outside size limit")
    if total - files[spec_key][2] + size > MAX_COPY_BYTES:
        raise ValueError("preparation copy exceeds size limit with frozen SPEC")

    destination.mkdir(mode=0o700)
    current_spec_sha256 = None
    for path, (mode, oid, count) in files.items():
        data = git(repo, "cat-file", "blob", oid)
        if len(data) != count:
            raise ValueError("Git blob size mismatch")
        if path == spec_key:
            current_spec_sha256 = digest(data)
            data = frozen
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        if mode == b"100755":
            target.chmod(0o700)

    return {
        "pr_head": head,
        "frozen_spec_revision": FROZEN_REVISION,
        "frozen_spec_sha256": FROZEN_SPEC_SHA256,
        "current_spec_sha256": current_spec_sha256,
        "evaluation_arms_executed": 0,
    }


def main():
    head, scratch = sys.argv[1:]
    repo = Path.cwd().resolve()
    scratch = Path(scratch).resolve()
    if not scratch.is_dir() or scratch.is_relative_to(repo):
        raise ValueError("scratch directory must be outside the checkout")
    history = scratch / "history"
    history.mkdir(mode=0o700)
    git(history, "init", "--bare", "--quiet")
    git(history, "fetch", "--no-tags", "--depth=1", REPOSITORY, FROZEN_REVISION)
    print(json.dumps(stage(repo, history, head, scratch / "copy"), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(f"HOLD: preparation staging failed: {exc}")
