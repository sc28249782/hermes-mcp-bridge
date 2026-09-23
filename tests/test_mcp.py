import asyncio
from pathlib import Path
import sys
import unittest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from version_core import report

class TestProtocol(unittest.TestCase):
    def test_stdio_initialize_discovery_lifecycle(self):
        async def run():
            params=StdioServerParameters(command=sys.executable,args=[str(Path(__file__).with_name('mock_mcp_server.py'))])
            async with stdio_client(params) as (read,write):
                async with ClientSession(read,write) as session:
                    await session.initialize()
                    listed=await session.list_tools()
                    byname={t.name:t for t in listed.tools}
                    self.assertEqual(len(byname),27)
                    self.assertFalse(byname['hermes_submit_task'].annotations.readOnlyHint)
                    self.assertNotIn('hermes_approve',byname)
                    self.assertIn('codex_submit_task',byname)
                    self.assertIn('bridge_version',byname)
                    self.assertIn('bridge_diagnostics',byname)
                    self.assertIn('bridge_audit_recent',byname)
                    self.assertIn('bridge_status',byname)
                    self.assertIn('bridge_context_create',byname)
                    self.assertIn('bridge_context_status',byname)
                    self.assertIn('bridge_context_recent',byname)
                    self.assertIn('bridge_context_close',byname)
                    self.assertIn('hands_health',byname)
                    self.assertIn('hands_list',byname)
                    self.assertIn('hands_read',byname)
                    self.assertTrue(byname['hands_read'].annotations.readOnlyHint)
                    self.assertFalse(byname['codex_submit_task'].annotations.readOnlyHint)
                    created=await session.call_tool('bridge_context_create',{'label':'protocol context'})
                    self.assertFalse(created.isError)
                    context_id=created.structuredContent['context_id']
                    recent_contexts=await session.call_tool('bridge_context_recent',{})
                    self.assertIn(context_id,[x['context_id'] for x in recent_contexts.structuredContent['contexts']])
                    model_info=await session.call_tool('hermes_model_info',{})
                    self.assertFalse(model_info.isError)
                    models=await session.call_tool('hermes_models',{})
                    self.assertFalse(models.isError)
                    health=await session.call_tool('hermes_health',{})
                    self.assertFalse(health.isError)
                    version=await session.call_tool('bridge_version',{})
                    self.assertFalse(version.isError)
                    self.assertEqual(version.structuredContent, report(Path(__file__).resolve().parents[1]))
                    diagnostics=await session.call_tool('bridge_diagnostics',{})
                    self.assertFalse(diagnostics.isError)
                    self.assertIn('audit', diagnostics.structuredContent['codex'])
                    audit=await session.call_tool('bridge_audit_recent',{})
                    self.assertFalse(audit.isError)
                    heartbeat=await session.call_tool('bridge_status',{})
                    self.assertTrue(heartbeat.structuredContent['ok'])
                    self.assertFalse(heartbeat.structuredContent['hermes']['upstream_checked'])
                    self.assertFalse(heartbeat.structuredContent['local_hands']['upstream_checked'])
                    hands_health=await session.call_tool('hands_health',{})
                    self.assertTrue(hands_health.structuredContent['ok'])
                    hands_list=await session.call_tool('hands_list',{'workspace':'fixture'})
                    self.assertIn({'name':'fixture.txt','kind':'file'}, hands_list.structuredContent['entries'])
                    hands_read=await session.call_tool('hands_read',{'workspace':'fixture','path':'fixture.txt'})
                    self.assertEqual(hands_read.structuredContent['content'],'hands fixture')
                    start=await session.call_tool('hermes_submit_task',{'prompt':'ทดสอบ','request_id':'protocol-test','context_id':context_id,'model':'deepseek/test','provider':'nous','model_options':{'reasoning_effort':'high'}})
                    self.assertFalse(start.isError)
                    rid=start.structuredContent['run_id']
                    self.assertEqual(start.structuredContent['requested_model'],'deepseek/test')
                    status=await session.call_tool('hermes_task_status',{'run_id':rid})
                    self.assertEqual(status.structuredContent['status'],'completed')
                    context=await session.call_tool('bridge_context_status',{'context_id':context_id})
                    self.assertEqual(context.structuredContent['hermes_session_id'], rid)
                    result=await session.call_tool('hermes_task_result',{'run_id':rid})
                    self.assertIn('ผลทดสอบ',result.structuredContent['output'])
                    denied=await session.call_tool('hermes_cancel_task',{'run_id':'foreign'})
                    self.assertTrue(denied.isError)
        asyncio.run(run())

if __name__=='__main__': unittest.main()
