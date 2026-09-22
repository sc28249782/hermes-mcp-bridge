"""Test-only MCP server with a fake Hermes API; never contacts real Hermes."""
from pathlib import Path
import sys
import tempfile
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import Bridge
from bridge import server
from codex_core import CodexRunner
from hands_core import HandsRuntime
from contexts import ContextRegistry
from test_bridge import FakeHermes
with tempfile.TemporaryDirectory() as root:
    b=Bridge('http://127.0.0.1:8642','test-secret-123',Path(root),httpx.MockTransport(FakeHermes()))
    c=CodexRunner({'binary':sys.executable,'allowed_workspaces':[root]},Path(root))
    (Path(root)/'fixture.txt').write_text('hands fixture')
    h=HandsRuntime({'enabled':True,'workspaces':[{'name':'fixture','path':root}]},Path(root))
    server(b,c,h,ContextRegistry(b.state,b.audit)).run(transport='stdio')
