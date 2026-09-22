import asyncio
from pathlib import Path
import sys
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class TestHandsFallbackProtocol(unittest.TestCase):
    def test_hands_read_only_operations_ignore_unavailable_backends(self):
        async def run():
            params = StdioServerParameters(
                command=sys.executable,
                args=[str(Path(__file__).with_name("mock_hands_off_server.py"))],
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    self.assertEqual(len(listed.tools), 22)
                    health = await session.call_tool("hands_health", {})
                    self.assertFalse(health.isError)
                    self.assertTrue(health.structuredContent["ok"])
                    result = await session.call_tool("hands_list", {"workspace": "fixture"})
                    self.assertFalse(result.isError)
                    self.assertIn({"name": "fixture.txt", "kind": "file"},
                                  result.structuredContent["entries"])
                    content = await session.call_tool("hands_read", {
                        "workspace": "fixture", "path": "fixture.txt"})
                    self.assertFalse(content.isError)
                    self.assertEqual(content.structuredContent["content"],
                                     "hands survives backend outage")
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
