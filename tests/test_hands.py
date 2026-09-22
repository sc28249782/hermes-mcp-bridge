import errno
import json
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from hands_core import HandsError, HandsRuntime
from config_schema import ConfigError, load_bridge_config


class TestHandsRuntime(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "workspace"
        self.root.mkdir()
        (self.root / "safe.txt").write_text("safe text")
        self.runtime = HandsRuntime({"enabled": True, "workspaces": [
            {"name": "work", "path": str(self.root)}]}, Path(self.tmp.name) / "state")
        if not self.runtime.health()["ok"]:
            self.skipTest("openat2 strict resolver is unavailable on this kernel")

    def tearDown(self):
        self.tmp.cleanup()

    def assert_code(self, code, fn, *args):
        with self.assertRaises(HandsError) as caught:
            fn(*args)
        self.assertEqual(caught.exception.code, code)

    def test_disabled_tools_have_stable_result(self):
        disabled = HandsRuntime({"enabled": False}, Path(self.tmp.name) / "disabled-state")
        self.assertEqual(disabled.health()["status"], "disabled")
        self.assertEqual(disabled.list("anything")["error_code"], "disabled")
        self.assertEqual(disabled.read("anything", "file.txt")["error_code"], "disabled")

    def test_schema_keeps_hands_additive_and_validates_known_fields(self):
        config = {"schema_version": 1, "api_url": "http://127.0.0.1:8642", "hermes_env": "x",
                  "hands": {"enabled": True, "workspaces": [
                      {"name": "work", "path": str(self.root)}], "unknown": True}}
        (Path(self.tmp.name) / "bridge-config.json").write_text(json.dumps(config))
        _, warnings = load_bridge_config(Path(self.tmp.name))
        self.assertTrue(any("hands.unknown" in warning for warning in warnings))
        config["hands"]["workspaces"][0]["path"] = "relative"
        (Path(self.tmp.name) / "bridge-config.json").write_text(json.dumps(config))
        with self.assertRaises(ConfigError):
            load_bridge_config(Path(self.tmp.name))

    def test_list_and_read_are_bounded_and_audited_without_content(self):
        listed = self.runtime.list("work")
        self.assertEqual(listed["entries"], [{"name": "safe.txt", "kind": "file"}])
        read = self.runtime.read("work", "safe.txt")
        self.assertEqual(read["content"], "safe text")
        audit = (Path(self.tmp.name) / "state" / "audit.jsonl").read_text()
        self.assertIn('"component":"hands"', audit)
        self.assertNotIn("safe text", audit)
        self.assertNotIn("safe.txt", audit)

    def test_workspace_secret_filename_is_not_listed_or_read(self):
        (self.root / ".ENV.production").write_text("API_KEY=not-for-mcp")
        (self.root / "credentials-prod.json").write_text('{"secret":true}')
        listed = self.runtime.list("work")
        self.assertEqual([entry["name"] for entry in listed["entries"]], ["safe.txt"])
        self.assert_code("policy_denied", self.runtime.read, "work", ".ENV.production")
        self.assert_code("policy_denied", self.runtime.read, "work", "credentials-prod.json")

    def test_user_protected_pattern_cannot_be_bypassed_by_case(self):
        (self.root / "Token.TXT").write_text("sensitive")
        runtime = HandsRuntime({"enabled": True, "protected_name_patterns": ["token.*"],
                                "workspaces": [{"name": "work", "path": str(self.root)}]},
                               Path(self.tmp.name) / "pattern-state")
        self.assertTrue(runtime.health()["ok"])
        self.assert_code("policy_denied", runtime.read, "work", "Token.TXT")

    def test_traversal_and_symlink_escape_are_denied(self):
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("outside")
        (self.root / "escape").symlink_to(outside)
        self.assert_code("invalid_path", self.runtime.read, "work", "../outside.txt")
        self.assert_code("policy_denied", self.runtime.read, "work", "escape")

    def test_binary_oversize_and_hard_link_are_denied(self):
        (self.root / "binary.txt").write_bytes(b"a\x00b")
        self.assert_code("policy_denied", self.runtime.read, "work", "binary.txt")
        small = HandsRuntime({"enabled": True, "max_read_bytes": 1024,
                              "workspaces": [{"name": "work", "path": str(self.root)}]},
                             Path(self.tmp.name) / "small-state")
        (self.root / "large.txt").write_text("x" * 1025)
        self.assert_code("limit_exceeded", small.read, "work", "large.txt")
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("outside")
        os.link(outside, self.root / "linked.txt")
        self.assert_code("policy_denied", self.runtime.read, "work", "linked.txt")

    def test_case_collisions_are_ambiguous(self):
        (self.root / "A.txt").write_text("a")
        (self.root / "a.txt").write_text("b")
        self.assert_code("policy_denied", self.runtime.list, "work")

    def test_strict_resolver_failure_makes_workspace_unavailable(self):
        with patch.object(HandsRuntime, "_openat2", side_effect=OSError(errno.ENOSYS, "missing")):
            runtime = HandsRuntime({"enabled": True, "workspaces": [
                {"name": "work", "path": str(self.root)}]}, Path(self.tmp.name) / "unavailable-state")
        self.assertEqual(runtime.health()["status"], "unavailable")
        self.assert_code("unavailable", runtime.read, "work", "safe.txt")


if __name__ == "__main__":
    unittest.main()
