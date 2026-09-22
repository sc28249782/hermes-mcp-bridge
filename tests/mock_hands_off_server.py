"""MCP fixture proving Hands works while Hermes and Codex are unusable."""
from pathlib import Path
import sys
import tempfile

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bridge import server
from codex_core import CodexRunner
from core import Bridge
from hands_core import HandsRuntime
from contexts import ContextRegistry


def unreachable(_: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("Hermes intentionally unavailable")


with tempfile.TemporaryDirectory() as root:
    root_path = Path(root)
    (root_path / "fixture.txt").write_text("hands survives backend outage")
    hands = HandsRuntime({"enabled": True, "workspaces": [
        {"name": "fixture", "path": root}]}, root_path / "hands-state")
    hermes = Bridge("http://127.0.0.1:8642", "test-secret-123", root_path / "hermes-state",
                    httpx.MockTransport(unreachable))
    codex = CodexRunner({"binary": "/definitely-missing-codex", "allowed_workspaces": [root]},
                        root_path / "codex-state")
    server(hermes, codex, hands, ContextRegistry(hermes.state, hermes.audit)).run(transport="stdio")
