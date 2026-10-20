"""Test-only metadata boundary faults; no real Hermes or native approval.

Boundary cases add a synthetic field AFTER normal status filtering. This is
deliberate fault injection into the real size guard, not allowlisted metadata.
Approval cases use the unmodified Bridge and an in-process fake upstream.
"""
import json
from pathlib import Path
import sys
import tempfile

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge import server
from codex_core import CodexRunner
from contexts import ContextRegistry
from core import Bridge
from test_bridge import FakeHermes


MARKER = 'PRIVATE_BOUNDARY_FIXTURE'
APPROVALS = {
    'approval-object': {'command': MARKER, 'request_id': MARKER,
                        'description': MARKER * 10000, 'required': False},
    'approval-list': [{'command': MARKER}],
    'approval-scalar': MARKER,
    'approval-null': None,
    'approval-absent': None,
}


class BoundaryFakeHermes(FakeHermes):
    def __init__(self):
        super().__init__()
        self.cases = {}

    def __call__(self, request):
        if request.method != 'GET' and not (request.method == 'POST' and request.url.path == '/v1/runs'):
            raise AssertionError('Fixture must not resolve approval or stop a run')
        response = super().__call__(request)
        if request.method == 'POST' and request.url.path == '/v1/runs' and response.status_code == 202:
            self.cases[response.json()['run_id']] = json.loads(request.content)['input']
        if request.method == 'GET' and request.url.path.startswith('/v1/runs/') and response.status_code == 200:
            value = response.json()
            case = self.cases[value['run_id']]
            value.update(status='waiting_for_approval', error={'private': MARKER},
                         usage={'total_tokens': 7, 'private': MARKER})
            if case in APPROVALS and case != 'approval-absent':
                value['approval'] = APPROVALS[case]
            return httpx.Response(200, json=value)
        return response


class BoundaryBridge(Bridge):
    def status(self, run_id):
        value = super().status(run_id)
        case = self.fixture_cases[run_id]
        if case in ('boundary-8191', 'boundary-8192', 'boundary-8193'):
            target = int(case.split('-')[1])
            value['fixture_padding'] = ''
            size = len(json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode('ascii'))
            if size > target:
                raise AssertionError('Fixture base exceeds boundary target')
            value['fixture_padding'] = 'x' * (target - size)
            self._check_metadata_size(value)
        return value


def main():
    with tempfile.TemporaryDirectory() as root:
        fake = BoundaryFakeHermes()
        bridge = BoundaryBridge('http://127.0.0.1:8642', 'test-secret-123', Path(root),
                                httpx.MockTransport(fake))
        bridge.fixture_cases = fake.cases
        codex = CodexRunner({'binary': sys.executable, 'allowed_workspaces': [root]}, Path(root))
        import stdio_guard
        try:
            stdio_guard.run_stdio_guarded(server(bridge, codex, None,
                                                ContextRegistry(bridge.state, bridge.audit)))
        finally:
            bridge.client.close()


if __name__ == '__main__':
    main()
