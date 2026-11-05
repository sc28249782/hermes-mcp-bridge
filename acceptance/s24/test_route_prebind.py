"""Offline metadata peer checks. No plugin, tunnel, VM or fixture activation."""
import ast
import asyncio
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import route_prebind as route


def frame(value):
    return (json.dumps(value, separators=(",", ":")) + "\n").encode()


class PrebindChecks(unittest.TestCase):
    def initialized(self):
        peer = route.MetadataOnlyPeer()
        reply = self.call(peer, "initialize", {"protocolVersion": "2025-11-25"})
        self.assertEqual(reply["result"]["serverInfo"]["name"], "s24-inactive-metadata")
        self.assertIn("not candidate discovery", reply["result"]["instructions"])
        peer.handle(frame({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        return peer

    def call(self, peer, method, params=None, request_id=0):
        return json.loads(peer.handle(frame({"jsonrpc": "2.0", "id": request_id,
                                            "method": method, "params": params or {}})))

    def test_advertised_schema_bytes_match_reviewed_manifest_without_candidate_identity(self):
        peer = self.initialized()
        tools = self.call(peer, "tools/list")["result"]["tools"]
        expected = route.load_manifest()["tools"]
        self.assertEqual({tool["name"] for tool in tools}, set(expected))
        self.assertEqual(len(tools), 27)
        for tool in tools:
            name = tool.pop("name")
            self.assertIn("INACTIVE", tool.pop("description"))
            self.assertEqual(tool, expected[name])
        self.assertEqual(self.call(peer, "tools/call", {"name": "bridge_version"})["result"], route.DENIED)
        self.assertNotIn("version", route.DENIED["structuredContent"])

    def test_every_tool_and_active_looking_arguments_are_denied_without_dispatch(self):
        peer = self.initialized()
        with ExitStack() as stack:
            for target in ("subprocess.Popen", "subprocess.run", "os.system", "sqlite3.connect", "socket.create_connection"):
                stack.enter_context(patch(target, side_effect=AssertionError("forbidden test-side effect")))
            for name in list(peer.manifest["tools"]) + ["unknown", "activate", "serve"]:
                result = self.call(peer, "tools/call", {"name": name, "arguments": {
                    "active": True, "candidate": "/unit/no-source", "command": "unit-do-not-execute",
                    "request_id": "unit-no-submit", "context_id": "unit-no-bind"}})["result"]
                self.assertEqual(result, route.DENIED)
                result["structuredContent"]["fixture_started"] = True
                self.assertFalse(route.DENIED["structuredContent"]["fixture_started"])

    def test_legacy_discover_fails_without_poisoning_initialize_or_requiring_unique_completed_ids(self):
        peer = route.MetadataOnlyPeer()
        reply = self.call(peer, "server/discover")
        self.assertEqual(reply["error"], {"code": -32601, "message": "Method not found"})
        self.assertFalse(peer.initialized)
        self.call(peer, "initialize", {"protocolVersion": "2025-11-25"})
        peer.handle(frame({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(len(self.call(peer, "tools/list")["result"]["tools"]), 27)

    def test_malformed_uninitialized_and_oversized_frames_hold_permanently(self):
        values = (b'[]\n', b'{"jsonrpc":"2.0","id":true,"method":"initialize"}\n',
                  b'{"jsonrpc":"2.0","id":0,"id":1,"method":"initialize"}\n',
                  b'{"jsonrpc":"2.0","id":0,"method":"ping","params":{"x":1e400}}\n',
                  frame({"jsonrpc": "2.0", "id": 0, "method": "tools/list"}),
                  b'{}', b'{}\n{}\n', b'x' * (route.FRAME_LIMIT + 1))
        for raw in values:
            with self.subTest(raw=raw[:64]):
                peer = route.MetadataOnlyPeer()
                with self.assertRaises((route.Hold, ValueError)):
                    peer.handle(raw)
                self.assertTrue(peer.held)
                with self.assertRaises(route.Hold):
                    self.call(peer, "initialize", {"protocolVersion": "2025-11-25"})

    def test_request_output_and_duplicate_initialize_limits_do_not_reset(self):
        for kind in ("requests", "bytes", "initialize", "cursor"):
            with self.subTest(kind=kind):
                peer = self.initialized()
                if kind == "requests":
                    peer.requests = route.REQUEST_LIMIT
                elif kind == "bytes":
                    peer.output_bytes = route.OUTPUT_LIMIT
                with self.assertRaises(route.Hold):
                    if kind == "initialize":
                        self.call(peer, "initialize", {"protocolVersion": "2025-11-25"})
                    else:
                        self.call(peer, "tools/list", {"cursor": "not-a-page"} if kind == "cursor" else {})
                self.assertTrue(peer.held)

    def test_inactive_version_cannot_pass_candidate_identity_validator(self):
        # Validator imports are test-side only, never part of the metadata peer.
        from identity_contract import OfflineIdentityContract
        from parent_contract import Hold
        validator = OfflineIdentityContract("release-archive")
        request = json.loads(validator.request())
        peer = self.initialized()
        reply = peer.handle(frame(request))
        self.assertEqual(json.loads(reply)["result"], route.DENIED)
        with self.assertRaises(Hold):
            validator.accept(reply)

    def test_read_and_write_readiness_expiry_hold_without_touching_real_fds(self):
        from unittest.mock import Mock
        for mode in ("input", "output"):
            with self.subTest(mode=mode), patch.object(route.sys, "stdin", Mock()), \
                    patch.object(route.sys, "stdout", Mock()), patch.object(route.os, "set_blocking"), \
                    patch.object(route.os, "read", return_value=frame({"jsonrpc": "2.0", "id": 0,
                                                                   "method": "server/discover"})), \
                    patch.object(route.os, "write", side_effect=AssertionError("must not write")), \
                    patch.object(route.select, "select", side_effect=[([], [], [])] if mode == "input"
                                      else [([101], [], []), ([], [], [])]) as readiness:
                route.sys.stdin.fileno.return_value = 101
                route.sys.stdout.fileno.return_value = 102
                with self.assertRaises(route.Hold):
                    route.serve()
                self.assertEqual(readiness.call_count, 1 if mode == "input" else 2)
                for call in readiness.call_args_list:
                    self.assertGreaterEqual(call.args[3], 0)
                    self.assertLessEqual(call.args[3], route.WINDOW_SECONDS)

    def test_manifest_drift_or_symlink_is_not_accepted(self):
        with patch.object(Path, "is_symlink", return_value=True), self.assertRaises(route.Hold):
            route.MetadataOnlyPeer()
        from io import BytesIO
        with patch.object(Path, "open", return_value=BytesIO(b'{}')), self.assertRaises(route.Hold):
            route.MetadataOnlyPeer()

    def test_actual_sdk_stdio_in_empty_cwd_is_metadata_only_and_creates_no_files(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        async def run(cwd):
            params = StdioServerParameters(command=sys.executable, args=["-B", str(Path(route.__file__).resolve()),
                "--metadata-only"], cwd=cwd, env={"PYTHONDONTWRITEBYTECODE": "1"})
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    initialized = await session.initialize()
                    self.assertEqual(initialized.serverInfo.version, "0.0.0-prebind")
                    self.assertEqual(len((await session.list_tools()).tools), 27)
                    for name in route.load_manifest()["tools"]:
                        result = await session.call_tool(name, {"active": True})
                        self.assertTrue(result.isError)
                        self.assertEqual(result.structuredContent, route.DENIED["structuredContent"])
        with tempfile.TemporaryDirectory() as cwd:
            asyncio.run(asyncio.wait_for(run(cwd), 10))
            self.assertEqual(list(Path(cwd).iterdir()), [])

    def test_cli_has_no_active_candidate_state_or_credentials_switch(self):
        path = str(Path(route.__file__).resolve())
        for extra in ([], ["--metadata-only", "--active"], ["--metadata-only", "--candidate", "/unit/no-source"],
                      ["--metadata-only", "--state", "/unit/no-state"]):
            process = subprocess.run([sys.executable, "-B", path, *extra], input=b"", capture_output=True, timeout=5)
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(process.stdout, b"")
            self.assertEqual(process.stderr, b"HOLD: inactive metadata peer unavailable\n")
        process = subprocess.run([sys.executable, "-B", path, "--metadata-only"], input=b'{',
                                 capture_output=True, timeout=5)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stderr, b"HOLD: inactive metadata peer unavailable\n")
        # Static defense complements real SDK controls, not a general noninterference proof.
        source = ast.parse(Path(route.__file__).read_text())
        imports = {alias.name.split(".")[0] for node in ast.walk(source)
                   if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in
                   (node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")])}
        self.assertFalse(imports & {"s24_fixture", "bridge", "core", "codex_core", "sqlite3", "subprocess", "socket", "httpx"})


if __name__ == "__main__":
    unittest.main()
