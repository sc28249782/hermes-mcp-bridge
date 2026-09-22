import tempfile
import unittest
from pathlib import Path

from contexts import ContextError, ContextRegistry


class Audit:
    def __init__(self): self.events = []
    def record(self, *args): self.events.append(args)


class TestContexts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.audit = Audit()
        self.contexts = ContextRegistry(Path(self.tmp.name), self.audit)

    def tearDown(self):
        self.tmp.cleanup()

    def test_explicit_binding_and_close(self):
        created = self.contexts.create("OpenHDK validation")
        cid = created["context_id"]
        self.assertIsNone(created["hermes_session_id"])
        self.contexts.bind_hermes_run(cid, "run_1")
        self.contexts.observe_hermes("run_1", "session_1")
        self.contexts.bind_codex_job(cid, "/tmp/workspace", "job_1")
        status = self.contexts.status(cid)
        self.assertEqual(status["hermes_session_id"], "session_1")
        self.assertEqual(status["codex_workspace"], "/tmp/workspace")
        self.contexts.close(cid)
        with self.assertRaises(ContextError):
            self.contexts.hermes_session(cid)

    def test_rejects_invalid_or_unknown_context(self):
        with self.assertRaises(ContextError):
            self.contexts.create("bad\nlabel")
        with self.assertRaises(ContextError):
            self.contexts.status("foreign")


if __name__ == "__main__":
    unittest.main()
