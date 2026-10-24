"""Offline identity controls; synthesized JSON-RPC envelopes are not wire evidence."""
import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import identity_contract as identity
from parent_contract import Hold, decode, encode
import s24_fixture as fixture

CANDIDATE = None


class IdentityChecks(unittest.TestCase):
    def setUp(self):
        manifest = identity.load_manifest()
        self.tools = [{"name": name, **deepcopy(fields)} for name, fields in manifest["tools"].items()]

    def version(self, kind="release-archive"):
        return {"isError": False, "structuredContent": identity.expected_version(kind),
                "content": [{"type": "text", "text": "offline test data"}],
                "_meta": {"test": ["preserved"]}}

    def response(self, request, result):
        return encode({"jsonrpc": "2.0", "id": decode(request)["id"], "result": result})

    def ready(self, kind="release-archive"):
        contract = identity.OfflineIdentityContract(kind)
        request = contract.request()
        self.assertEqual(decode(request)["params"], {"name": "bridge_version", "arguments": {}})
        self.assertIsNone(contract.accept(self.response(request, self.version(kind))))
        return contract

    def assert_held(self, contract):
        with self.assertRaises(Hold):
            contract.request()
        with self.assertRaises(Hold):
            contract.summary()

    def test_both_source_shapes_keep_embedded_input_separate_from_candidate(self):
        for kind in ("release-archive", "git-worktree"):
            with self.subTest(kind=kind):
                contract = self.ready(kind)
                request = contract.request()
                result = contract.accept(self.response(request, {"tools": self.tools}))
                self.assertEqual(result["evidence_class"], identity.EVIDENCE_CLASS)
                self.assertEqual(result["candidate"], fixture.PIN)
                self.assertEqual(result["decoded_tools_count"], 27)
                expected = fixture.PIN if kind == "git-worktree" else identity.EMBEDDED_INPUT
                self.assertEqual(result["reported_version"]["source_revision"], expected)
                with self.assertRaises(Hold):
                    contract.request()

    def test_actual_sdk_decoded_identity_and_discovery_without_stimulus(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        async def exercise():
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                root.chmod(0o700)
                params = StdioServerParameters(command=sys.executable, args=["-B", str(Path(fixture.__file__).resolve()),
                    "serve", "--candidate", str(CANDIDATE), "--state", str(root / "state")],
                    env={"PYTHONDONTWRITEBYTECODE": "1"})
                kind = "git-worktree" if (CANDIDATE / ".git").exists() else "release-archive"
                contract = identity.OfflineIdentityContract(kind)
                async with stdio_client(params) as (reader, writer):
                    async with ClientSession(reader, writer) as session:
                        await session.initialize()
                        request = contract.request()
                        value = await session.call_tool("bridge_version", {})
                        # SDK has decoded the reply. These envelopes are synthesized test data.
                        contract.accept(self.response(request, value.model_dump(mode="json", exclude_none=True)))
                        request = contract.request()
                        page = await session.list_tools()
                        result = contract.accept(self.response(request, page.model_dump(mode="json", exclude_none=True)))
                        self.assertEqual(result["decoded_tools_count"], 27)
                        self.assertEqual(result["pages"], 1)
                # No submit or context-create call occurred. No matrix totals are claimed.
        asyncio.run(exercise())

    def test_paginated_requests_link_exact_cursor_and_preserve_fields(self):
        contract = self.ready()
        self.tools[0]["description"] = "test presentation"
        self.tools[0]["_meta"] = {"extra": [1, {"keep": True}]}
        request = contract.request()
        self.assertEqual(decode(request)["params"], {})
        contract.accept(self.response(request, {"tools": self.tools[:10], "nextCursor": "cursor-1"}))
        request = contract.request()
        self.assertEqual(decode(request)["params"], {"cursor": "cursor-1"})
        result = contract.accept(self.response(request, {"tools": self.tools[10:]}))
        self.assertEqual(result["pages"], 2)
        out = contract.decoded_results()
        self.assertEqual(out["tools"][self.tools[0]["name"]], self.tools[0])
        self.assertEqual(out["version_result"], self.version())
        out["tools"].clear()
        self.assertEqual(len(contract.decoded_results()["tools"]), 27)

    def test_version_field_drift_and_bool_integer_confusion_fail(self):
        changes = {"ok": False, "version": "1.2.7", "release_identifier": "v1.2.7",
                   "build_provenance": "unknown", "source_kind": "git-worktree",
                   "source_revision": fixture.PIN, "revision_source": "git",
                   "config_schema_version": 1, "embedded_config_schema_version": True,
                   "mcp_discovery_count": True}
        for key, value in changes.items():
            with self.subTest(key=key):
                contract = identity.OfflineIdentityContract("release-archive")
                request = contract.request()
                result = self.version()
                result["structuredContent"][key] = value
                with self.assertRaises(Hold):
                    contract.accept(self.response(request, result))
                self.assert_held(contract)

    def test_reported_count_does_not_substitute_for_discovery(self):
        contract = self.ready()
        with self.assertRaises(Hold):
            contract.summary()
        request = contract.request()
        with self.assertRaises(Hold):
            contract.accept(self.response(request, {"tools": self.tools[:-1]}))
        self.assert_held(contract)

    def test_unknown_duplicate_or_schema_annotation_drift_fail(self):
        mutations = [lambda tools: tools.append(deepcopy(tools[0])),
                     lambda tools: tools[0].update(name="unexpected_tool"),
                     lambda tools: tools[0].update(inputSchema={"type": "object"}),
                     lambda tools: tools[0].update(outputSchema={"type": "string"}),
                     lambda tools: tools[0].update(annotations={"readOnlyHint": False})]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                contract = self.ready()
                request = contract.request()
                tools = deepcopy(self.tools)
                mutate(tools)
                with self.assertRaises(Hold):
                    contract.accept(self.response(request, {"tools": tools}))
                self.assert_held(contract)

    def test_duplicate_across_pages_and_cursor_cycles_fail(self):
        for duplicate in (True, False):
            with self.subTest(duplicate=duplicate):
                contract = self.ready()
                request = contract.request()
                contract.accept(self.response(request, {"tools": self.tools[:1], "nextCursor": "x"}))
                request = contract.request()
                result = {"tools": self.tools[:1] if duplicate else [], "nextCursor": "x"}
                with self.assertRaises(Hold):
                    contract.accept(self.response(request, result))
                self.assert_held(contract)

    def test_page_bound_and_bad_cursor_types_fail(self):
        for cursor in (True, 1, "", "x" * 257, "line\nbreak"):
            with self.subTest(cursor=cursor):
                contract = self.ready()
                request = contract.request()
                with self.assertRaises(Hold):
                    contract.accept(self.response(request, {"tools": [], "nextCursor": cursor}))
                self.assert_held(contract)
        contract = self.ready()
        for number in range(identity.MAX_PAGES):
            request = contract.request()
            if number + 1 == identity.MAX_PAGES:
                with self.assertRaises(Hold):
                    contract.accept(self.response(request, {"tools": [], "nextCursor": str(number)}))
            else:
                contract.accept(self.response(request, {"tools": [], "nextCursor": str(number)}))
        self.assert_held(contract)

    def test_envelopes_duplicate_reply_and_outstanding_request_fail(self):
        bad = [b'{"jsonrpc":"2.0","id":1,"id":1,"result":{}}\n',
               encode({"jsonrpc": "2.0", "id": True, "result": {}}),
               encode({"jsonrpc": "2.0", "id": 2, "result": {}}),
               encode({"jsonrpc": "2.0", "id": 1, "error": {"code": -32601}})]
        for raw in bad:
            contract = identity.OfflineIdentityContract("release-archive")
            contract.request()
            with self.assertRaises(Hold):
                contract.accept(raw)
            self.assert_held(contract)
        contract = self.ready()
        with self.assertRaises(Hold):
            contract.accept(encode({"jsonrpc": "2.0", "id": 1, "result": self.version()}))
        self.assert_held(contract)
        contract = self.ready()
        contract.request()
        with self.assertRaises(Hold):
            contract.request()
        self.assert_held(contract)

    def test_frame_and_capture_limits_fail_closed(self):
        contract = self.ready()
        contract.request()
        with self.assertRaises(Hold):
            contract.accept(b"x" * 65537)
        self.assert_held(contract)
        contract = self.ready()
        contract._bytes = identity.MAX_CAPTURE_BYTES
        with self.assertRaises(Hold):
            contract.request()
        self.assert_held(contract)

    def test_local_manifest_tamper_rejected_before_requests(self):
        with patch("pathlib.Path.open", unittest.mock.mock_open(read_data=b"tampered")):
            with self.assertRaises(Hold):
                identity.OfflineIdentityContract("release-archive")

    def test_wrong_source_kind_and_missing_version_result_rejected(self):
        with self.assertRaises(Hold):
            identity.OfflineIdentityContract("unknown")
        for result in ({"content": [], "isError": True}, {"content": [], "isError": False}, True):
            contract = identity.OfflineIdentityContract("release-archive")
            request = contract.request()
            with self.assertRaises(Hold):
                contract.accept(self.response(request, result))
            self.assert_held(contract)

    def test_key_order_is_not_identity_or_schema_drift(self):
        contract = identity.OfflineIdentityContract("release-archive")
        request = contract.request()
        value = self.version()
        value["structuredContent"] = dict(reversed(list(value["structuredContent"].items())))
        contract.accept(self.response(request, value))
        request = contract.request()
        tools = [dict(reversed(list(t.items()))) for t in reversed(self.tools)]
        self.assertEqual(contract.accept(self.response(request, {"tools": tools}))["decoded_tools_count"], 27)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    arguments, remaining = parser.parse_known_args()
    CANDIDATE = fixture.verify_candidate(arguments.candidate.resolve())
    unittest.main(argv=[sys.argv[0], *remaining])
