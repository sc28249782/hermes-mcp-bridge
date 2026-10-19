"""Enabled execution contract over the actual SDK stdio transport."""
import asyncio
from pathlib import Path
import sys
import unittest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class TestExecutionProtocol(unittest.TestCase):
    def test_discovery_and_lifecycle_over_stdio(self):
        async def run():
            params = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name("mock_opencode_execution_server.py"))])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    listed = {tool.name: tool for tool in (await client.list_tools()).tools}
                    self.assertEqual(len(listed), 33)
                    for name in ("submit_task", "task_status", "task_result", "cancel_task", "recent_tasks"):
                        self.assertIn("opencode_" + name, listed)
                    self.assertFalse(listed["opencode_submit_task"].annotations.readOnlyHint)
                    self.assertTrue(listed["opencode_task_result"].annotations.readOnlyHint)
                    health = (await client.call_tool("codex_health", {})).structuredContent
                    workspace = health["allowed_workspaces"][0]
                    async def call(name, arguments):
                        result = await client.call_tool("opencode_" + name, arguments)
                        self.assertFalse(result.isError, result.content)
                        return result.structuredContent
                    async def finished(job):
                        for _ in range(100):
                            result = await call("task_status", {"job_id": job})
                            if result["status"] not in ("pending", "running"):
                                return result
                            await asyncio.sleep(0.03)
                        self.fail("worker did not finish")
                    first = await call("submit_task", {"prompt": "ok", "workspace": workspace, "request_id": "mcp_first"})
                    self.assertEqual((await finished(first["job_id"]))["status"], "completed")
                    replay = await call("submit_task", {"prompt": "ok", "workspace": workspace, "request_id": "mcp_first"})
                    self.assertEqual(first["job_id"], replay["job_id"])
                    second = await call("submit_task", {"prompt": "ok", "workspace": workspace, "request_id": "mcp_second", "session_id": first["session_id"]})
                    self.assertEqual(first["session_id"], second["session_id"])
                    self.assertEqual((await finished(second["job_id"]))["status"], "completed")
                    result = await call("task_result", {"job_id": second["job_id"]})
                    self.assertIn("fixture-ok", result["content"])
                    slow = await call("submit_task", {"prompt": "slow", "workspace": workspace, "request_id": "mcp_cancel"})
                    await call("cancel_task", {"job_id": slow["job_id"]})
                    self.assertEqual((await finished(slow["job_id"]))["status"], "cancelled")
                    self.assertEqual(len((await call("recent_tasks", {}))["jobs"]), 3)
        asyncio.run(run())
