"""Test-only MCP server with an enabled OpenCode adapter and a fake executable.

The fixture never contacts a real OpenCode CLI, Hermes, Codex, Tunnel, or any
network endpoint. It proves the enabled discovery contract of 28 tools.
"""
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
from opencode_core import OpenCodeRunner
from test_bridge import FakeHermes

with tempfile.TemporaryDirectory() as root:
    fake = Path(root) / "fake-opencode"
    fake.write_text("#!/usr/bin/env python3\nimport sys\nsys.stdout.write('2.0.32\\n')\n")
    fake.chmod(0o700)
    b = Bridge("http://127.0.0.1:8642", "test-secret-123", Path(root), httpx.MockTransport(FakeHermes()))
    c = CodexRunner({"binary": sys.executable, "allowed_workspaces": [root]}, Path(root))
    (Path(root) / "fixture.txt").write_text("hands fixture")
    h = HandsRuntime({"enabled": True, "workspaces": [{"name": "fixture", "path": root}]}, Path(root))
    oc = OpenCodeRunner({"enabled": True, "binary": str(fake)})
    import stdio_guard
    stdio_guard.run_stdio_guarded(server(b, c, h, ContextRegistry(b.state, b.audit), oc))
