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

class PrivacyFakeHermes(FakeHermes):
    def __call__(self, request):
        response = super().__call__(request)
        if request.method == 'GET' and request.url.path.startswith('/v1/runs/') and response.status_code == 200:
            value = response.json()
            value.update(status='waiting_for_approval',
                         error='PRIVATE_MCP_FIXTURE' * 10000,
                         approval={'command': 'PRIVATE_MCP_FIXTURE', 'description': 'x' * 100000},
                         usage={'total_tokens': 7, 'private': 'PRIVATE_MCP_FIXTURE'})
            return httpx.Response(200, json=value)
        return response

with tempfile.TemporaryDirectory() as root:
    fake = PrivacyFakeHermes() if '--privacy-fixture' in sys.argv else FakeHermes()
    b=Bridge('http://127.0.0.1:8642','test-secret-123',Path(root),httpx.MockTransport(fake))
    c=CodexRunner({'binary':sys.executable,'allowed_workspaces':[root]},Path(root))
    (Path(root)/'fixture.txt').write_text('hands fixture')
    h=HandsRuntime({'enabled':True,'workspaces':[{'name':'fixture','path':root}]},Path(root))
    contexts = ContextRegistry(b.state, b.audit, soft_cap=1)
    if '--context-unavailable' in sys.argv:
        contexts.path.unlink()
    import stdio_guard
    stdio_guard.run_stdio_guarded(server(b,c,h,contexts))

