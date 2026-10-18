"""Packaging regression for the release archive and installer.

`install.sh` does not copy files: it runs from the extracted release archive
and only creates the virtual environment and the default configuration. The
release archive is built with `git archive` over tracked files
(RELEASE-RUNBOOK-TH.md Phase B), so the archive ships exactly the tracked
tree. These tests derive the bridge's real import surface and prove that the
required root modules and the stdio fixture servers are present and tracked,
so a future rename or a forgotten `git add` cannot silently produce a release
archive that cannot start the bridge or run its tests.
"""
import ast
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Root modules bridge.py must import for the v1.2.4 scope (SPEC.md sections
# 16 and 17). The stdio guard import is function-scoped, so it is easy to
# drop from the tree by accident; the archive would then not start.
REQUIRED_ROOT_MODULES = {"opencode_core", "stdio_guard"}

# Fixture servers that tests launch as subprocesses from the extracted tree
# (tests/test_stdio_guard.py, tests/test_opencode.py, tests/test_mcp.py).
REQUIRED_FIXTURES = (
    "mock_mcp_server.py",
    "mock_hands_off_server.py",
    "mock_opencode_server.py",
)


def _imported_root_modules(path: Path) -> set:
    """Return absolute-import names in `path` that resolve to root .py files."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return {name for name in names if (ROOT / f"{name}.py").exists()}


class TestPackagingSurface(unittest.TestCase):
    def _tracked_files(self):
        """Tracked file set, or None when running from an extracted archive."""
        if not (ROOT / ".git").exists():
            return None
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, timeout=10, check=True,
        )
        return set(result.stdout.splitlines())

    def test_bridge_imports_required_root_modules(self):
        imported = _imported_root_modules(ROOT / "bridge.py")
        missing = REQUIRED_ROOT_MODULES - imported
        self.assertEqual(
            missing, set(),
            f"bridge.py no longer imports: {sorted(missing)}; "
            "update REQUIRED_ROOT_MODULES together with SPEC.md sections 16-17",
        )

    def test_required_root_modules_exist_and_are_tracked(self):
        tracked = self._tracked_files()
        for name in sorted(REQUIRED_ROOT_MODULES):
            module = ROOT / f"{name}.py"
            self.assertTrue(module.is_file(), f"{name}.py is missing from the tree")
            if tracked is not None:
                self.assertIn(
                    f"{name}.py", tracked,
                    f"{name}.py is not git-tracked; `git archive` would omit it "
                    "from the release archive and install.sh could not start the bridge",
                )

    def test_stdio_fixture_servers_exist_and_are_tracked(self):
        tracked = self._tracked_files()
        for fixture in REQUIRED_FIXTURES:
            path = ROOT / "tests" / fixture
            self.assertTrue(path.is_file(), f"tests/{fixture} is missing from the tree")
            if tracked is not None:
                self.assertIn(
                    f"tests/{fixture}", tracked,
                    f"tests/{fixture} is not git-tracked; the release archive "
                    "would omit it and its tests could not run",
                )


if __name__ == "__main__":
    unittest.main()
