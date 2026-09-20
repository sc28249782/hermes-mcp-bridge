import asyncio
from pathlib import Path
import sys
import unittest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class TestProtocol(unittest.TestCase):
    def test_stdio_initialize_discovery_lifecycle(self):
        async def run():
            params=StdioServerParameters(command=sys.executable,args=[str(Path(__file__).with_name('mock_mcp_server.py'))])
            async with stdio_client(params) as (read,write):
                async with ClientSession(read,write) as session:
                    await session.initialize()
                    listed=await session.list_tools()
                    byname={t.name:t for t in listed.tools}
                    self.assertEqual(len(byname),18)
                    self.assertFalse(byname['hermes_submit_task'].annotations.readOnlyHint)
                    self.assertNotIn('hermes_approve',byname)
                    self.assertIn('codex_submit_task',byname)
                    self.assertIn('bridge_diagnostics',byname)
                    self.assertIn('bridge_audit_recent',byname)
                    self.assertFalse(byname['codex_submit_task'].annotations.readOnlyHint)
                    model_info=await session.call_tool('hermes_model_info',{})
                    self.assertFalse(model_info.isError)
                    models=await session.call_tool('hermes_models',{})
                    self.assertFalse(models.isError)
                    health=await session.call_tool('hermes_health',{})
                    self.assertFalse(health.isError)
                    diagnostics=await session.call_tool('bridge_diagnostics',{})
                    self.assertFalse(diagnostics.isError)
                    self.assertIn('audit', diagnostics.structuredContent['codex'])
                    audit=await session.call_tool('bridge_audit_recent',{})
                    self.assertFalse(audit.isError)
                    start=await session.call_tool('hermes_submit_task',{'prompt':'ทดสอบ','request_id':'protocol-test','model':'deepseek/test','provider':'nous','model_options':{'reasoning_effort':'high'}})
                    self.assertFalse(start.isError)
                    rid=start.structuredContent['run_id']
                    self.assertEqual(start.structuredContent['requested_model'],'deepseek/test')
                    status=await session.call_tool('hermes_task_status',{'run_id':rid})
                    self.assertEqual(status.structuredContent['status'],'completed')
                    result=await session.call_tool('hermes_task_result',{'run_id':rid})
                    self.assertIn('ผลทดสอบ',result.structuredContent['output'])
                    denied=await session.call_tool('hermes_cancel_task',{'run_id':'foreign'})
                    self.assertTrue(denied.isError)
        asyncio.run(run())

if __name__=='__main__': unittest.main()
