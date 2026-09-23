"""Local-only bridge identity and provenance reporting."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from version_info import (
    BRIDGE_VERSION,
    BUILD_PROVENANCE,
    CONFIG_SCHEMA_VERSION,
    EMBEDDED_SOURCE_REVISION,
    MCP_DISCOVERY_COUNT,
    RELEASE_IDENTIFIER,
)

_REVISION = re.compile(r"^[0-9a-f]{40}$")


def _runtime_git_revision(root: Path) -> str | None:
    """Best-effort enrichment; never needed to report a version."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, timeout=2, shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and _REVISION.fullmatch(revision) else None


def _config_schema_version(root: Path) -> int | str:
    try:
        raw = json.loads((root / "bridge-config.json").read_text())
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "unknown"
    value = raw.get("schema_version") if isinstance(raw, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else "unknown"


def report(root: Path) -> dict:
    """Return bounded local identity without contacting any backend or network."""
    root = Path(root)
    source_kind = "git-worktree" if (root / ".git").exists() else "release-archive"
    runtime_revision = _runtime_git_revision(root) if source_kind == "git-worktree" else None
    embedded = EMBEDDED_SOURCE_REVISION if _REVISION.fullmatch(EMBEDDED_SOURCE_REVISION) else None
    if runtime_revision:
        source_revision, revision_source = runtime_revision, "git"
    elif embedded:
        source_revision, revision_source = embedded, "embedded"
    else:
        source_revision, revision_source = "unknown", "unknown"
    return {
        "ok": True,
        "version": BRIDGE_VERSION,
        "release_identifier": RELEASE_IDENTIFIER,
        "build_provenance": BUILD_PROVENANCE,
        "source_kind": source_kind,
        "source_revision": source_revision,
        "revision_source": revision_source,
        "config_schema_version": _config_schema_version(root),
        "embedded_config_schema_version": CONFIG_SCHEMA_VERSION,
        "mcp_discovery_count": MCP_DISCOVERY_COUNT,
    }
