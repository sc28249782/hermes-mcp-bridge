"""MCP connection-path coverage for synthetic metadata faults and approvals."""
import asyncio
import json
from pathlib import Path
import sys
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class TestPrivacyBoundaryProtocol(unittest.TestCase):
    def test_exact_metadata_boundaries_and_approval_shapes(self):
        async def run():
            params = StdioServerParameters(command=sys.executable,
                args=[str(Path(__file__).with_name('mock_privacy_boundary_server.py'))])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = {tool.name for tool in (await session.list_tools()).tools}
                    self.assertEqual(len(tools), 27)
                    self.assertNotIn('hermes_approve', tools)
                    for target in (8191, 8192, 8193):
                        case = f'boundary-{target}'
                        start = await session.call_tool('hermes_submit_task',
                            {'prompt': case, 'request_id': case})
                        self.assertFalse(start.isError)
                        rid = start.structuredContent['run_id']
                        result = await session.call_tool('hermes_task_status', {'run_id': rid})
                        if target > 8192:
                            self.assertTrue(result.isError)
                            self.assertIsNone(result.structuredContent)
                            self.assertEqual(result.content[0].text,
                                             'Error executing tool hermes_task_status: '
                                             'Hermes metadata exceeds the bridge limit.')
                            self.assertNotIn('PRIVATE_BOUNDARY_FIXTURE', result.content[0].text)
                        else:
                            self.assertFalse(result.isError)
                            encoded = json.dumps(result.structuredContent, ensure_ascii=True,
                                                 separators=(',', ':')).encode('ascii')
                            self.assertEqual(len(encoded), target)
                            self.assertNotIn(b'PRIVATE_BOUNDARY_FIXTURE', encoded)
                    for shape in ('object', 'list', 'scalar', 'null', 'absent'):
                        case = f'approval-{shape}'
                        start = await session.call_tool('hermes_submit_task',
                            {'prompt': case, 'request_id': case})
                        rid = start.structuredContent['run_id']
                        status = await session.call_tool('hermes_task_status', {'run_id': rid})
                        self.assertFalse(status.isError)
                        value = status.structuredContent
                        self.assertEqual(value['approval'], {'required': True})
                        self.assertEqual(value['error'], 'Hermes reported an error; inspect Hermes locally.')
                        self.assertEqual(value['usage'], {'total_tokens': 7})
                        self.assertNotIn('fixture_padding', value)
                        self.assertIn('review locally', value['next'])
                        self.assertNotIn('PRIVATE_BOUNDARY_FIXTURE', json.dumps(value))
                        result = await session.call_tool('hermes_task_result', {'run_id': rid})
                        self.assertFalse(result.isError)
                        self.assertNotIn('approval', result.structuredContent)
                        self.assertNotIn('PRIVATE_BOUNDARY_FIXTURE', json.dumps(result.structuredContent))
                        self.assertEqual(result.structuredContent['output'], 'ผลทดสอบ [REDACTED_HERMES_KEY]')
        asyncio.run(run())
