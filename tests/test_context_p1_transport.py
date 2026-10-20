"""P1 acceptance over actual SDK stdio; this is not Secure MCP Tunnel evidence."""
import asyncio
import json
from pathlib import Path
import sys
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mock_context_p1_server import FAULT_LABEL, NoBackend
from contexts import ContextError

FIXTURE = str(Path(__file__).with_name('mock_context_p1_server.py'))
FIELDS = {'state', 'soft_cap', 'rows_lower_bound', 'count_capped', 'soft_cap_reached', 'warning'}


class TestContextP1Transport(unittest.TestCase):
    def registry(self, value, count=None, unavailable=False):
        self.assertEqual(set(value), FIELDS)
        self.assertEqual(value['soft_cap'], 3)
        self.assertEqual(value['state'], 'unavailable' if unavailable else 'ok')
        self.assertEqual(value['rows_lower_bound'], count)
        self.assertEqual(value['count_capped'], None if unavailable else count == 4)
        self.assertEqual(value['soft_cap_reached'], None if unavailable else count >= 3)
        warning = ('context_registry_unavailable' if unavailable else
                   'context_soft_cap_reached' if count >= 3 else None)
        self.assertEqual(value['warning'], warning)
        encoded = json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode('ascii')
        self.assertLessEqual(len(encoded), 512)
        self.assertNotIn(b'PRIVATE', encoded)

    def test_threshold_create_failure_ack_and_followup_over_stdio(self):
        async def run():
            params = StdioServerParameters(command=sys.executable, args=[FIXTURE])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    names = {t.name for t in (await session.list_tools()).tools}
                    self.assertEqual(len(names), 27)
                    self.assertNotIn('context_prune_preview', names)
                    status = await session.call_tool('bridge_status', {})
                    self.assertFalse(status.isError)
                    self.assertTrue(status.structuredContent['ok'])
                    self.registry(status.structuredContent['contexts']['registry'], 0)
                    for number in range(1, 6):
                        created = await session.call_tool('bridge_context_create', {'label': 'fixture'})
                        self.assertFalse(created.isError)
                        self.registry(created.structuredContent['registry'], min(number, 4))
                        status = await session.call_tool('bridge_status', {})
                        self.assertFalse(status.isError)
                        self.assertTrue(status.structuredContent['ok'])
                        self.assertTrue(status.structuredContent['contexts']['explicit_only'])
                        self.registry(status.structuredContent['contexts']['registry'], min(number, 4))
                        for name in ('hermes', 'codex', 'local_hands'):
                            self.assertTrue(status.structuredContent[name]['fixture_only'])
                    created = await session.call_tool('bridge_context_create', {'label': FAULT_LABEL})
                    self.assertFalse(created.isError)
                    self.registry(created.structuredContent['registry'], unavailable=True)
                    self.assertNotIn('PRIVATE_FIXTURE_STORAGE_ERROR', json.dumps(created.structuredContent))
                    cid = created.structuredContent['context_id']
                    stored = await session.call_tool('bridge_context_status', {'context_id': cid})
                    self.assertFalse(stored.isError)
                    self.assertEqual(stored.structuredContent['context_id'], cid)
                    self.assertNotIn('registry', stored.structuredContent)
                    recent = await session.call_tool('bridge_context_recent', {'limit': 100})
                    self.assertFalse(recent.isError)
                    rows = recent.structuredContent['contexts']
                    self.assertEqual(len(rows), 6)
                    self.assertEqual(sum(r['context_id'] == cid for r in rows), 1)
                    status = await session.call_tool('bridge_status', {})
                    self.assertTrue(status.structuredContent['ok'])
                    self.registry(status.structuredContent['contexts']['registry'], 4)
                    # Prove the fixture refuses a backend operation without contacting one.
                    denied = await session.call_tool('hermes_health', {})
                    self.assertTrue(denied.isError)
        asyncio.run(run())

    def test_real_missing_and_exclusive_lock_failures_over_stdio(self):
        async def run(scenario):
            params = StdioServerParameters(command=sys.executable,
                                           args=[FIXTURE, '--scenario', scenario])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.assertEqual(len((await session.list_tools()).tools), 27)
                    for _ in range(2):
                        status = await session.call_tool('bridge_status', {})
                        self.assertFalse(status.isError)
                        value = status.structuredContent
                        self.assertFalse(value['ok'])
                        self.assertTrue(value['contexts']['explicit_only'])
                        self.registry(value['contexts']['registry'], unavailable=True)
                        self.assertNotIn('PRIVATE', json.dumps(value))
        for scenario in ('missing', 'locked'):
            with self.subTest(scenario=scenario):
                asyncio.run(run(scenario))

    def test_backend_stubs_deny_every_nonlocal_operation(self):
        backend = NoBackend()
        for method in ('health', 'submit', 'start', 'stop', 'cancel', 'result', 'approve_local'):
            with self.subTest(method=method), self.assertRaises(ContextError):
                getattr(backend, method)
        self.assertEqual(backend.local_status(), {'fixture_only': True, 'backend_initialized': False})


if __name__ == '__main__':
    unittest.main()
