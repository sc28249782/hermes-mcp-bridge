"""Real stdio fixture with execution enabled; no real provider or service."""
from pathlib import Path
import sys
import tempfile
import httpx
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge import server
from codex_core import CodexRunner
from contexts import ContextRegistry
from core import Bridge
from hands_core import HandsRuntime
from opencode_core import OpenCodeRunner
from opencode_tasks import OpenCodeTasks
from test_bridge import FakeHermes
from stdio_guard import run_stdio_guarded

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    workspace = root / "workspace"
    workspace.mkdir()
    state = root / "state"
    binary = str(Path(__file__).parent / "fixtures" / "opencode_fixture_cli.py")
    config = {"enabled": True, "binary": binary, "execution": {"enabled": True, "allowed_workspaces": [str(workspace)], "allowed_models": ["fixture/model"], "max_runtime_seconds": 2}}
    b = Bridge("http://127.0.0.1:8642", "test-secret-123", state, httpx.MockTransport(FakeHermes()))
    c = CodexRunner({"binary": sys.executable, "allowed_workspaces": [str(workspace)]}, state)
    h = HandsRuntime({"enabled": False}, state)
    # Publish only this fixture's nonsecret workspace through the existing
    # codex health metadata, so the client need not guess a temporary path.
    run_stdio_guarded(server(b, c, h, ContextRegistry(state, b.audit), OpenCodeRunner(config), OpenCodeTasks(config, state)))
