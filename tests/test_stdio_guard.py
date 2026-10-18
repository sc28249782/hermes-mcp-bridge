"""Tests for the legacy stdio server/discover boundary guard (SPEC.md section 17).

Two parts:
1. Synthetic in-memory: the boundary pump is driven with typed SDK messages
   over memory streams; no network, no model, no real subprocess.
2. Real stdio subprocess: the fixture bridge (fake Hermes/Codex/Hands backends)
   is launched over real stdio pipes and probed with raw JSON-RPC lines,
   including the pre-initialize probe that the original repro could not test.
"""
import asyncio
import contextlib
import dataclasses
import io
import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream
import mcp.types as types
from mcp.shared.message import SessionMessage

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from stdio_guard import (  # noqa: E402
    DISCOVER_METHOD,
    _forward_inbound,
    guarded_stdio_streams,
)

PY = sys.executable
FIXTURE = Path(__file__).with_name("mock_mcp_server.py")
_ERROR_REPLY = {"code": -32601, "message": "Method not found"}


def _request(msg_id: Any, method: str, params: Any = None) -> SessionMessage:
    root = types.JSONRPCRequest(jsonrpc="2.0", id=msg_id, method=method, params=params)
    return SessionMessage(message=types.JSONRPCMessage(root=root), metadata=None)


def _notification(method: str) -> SessionMessage:
    root = types.JSONRPCNotification(jsonrpc="2.0", method=method, params=None)
    return SessionMessage(message=types.JSONRPCMessage(root=root), metadata=None)


def _probe(msg_id: Any, params: Any = None) -> SessionMessage:
    return _request(msg_id, DISCOVER_METHOD, params)


def _discover_reply(msg_id: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": dict(_ERROR_REPLY)}


async def _drive(messages: List[Any], patch_reply_failure: bool = False
                 ) -> Tuple[List[Any], List[Any], List[logging.LogRecord]]:
    """Feed the boundary pump over memory streams and collect what it
    forwards and what it replies."""
    source_writer, source_reader = anyio.create_memory_object_stream(0)
    forward_writer, forward_reader = anyio.create_memory_object_stream(0)
    reply_writer, reply_reader = anyio.create_memory_object_stream(0)

    forwarded: List[Any] = []
    replies: List[Any] = []
    records: List[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    capture = Capture(level=logging.ERROR)
    logging.getLogger("stdio_guard").addHandler(capture)

    fwd_done = anyio.Event()
    reply_done = anyio.Event()

    async def collect(stream: Any, sink: List[Any], done: anyio.Event) -> None:
        try:
            async for item in stream:
                sink.append(item)
        except anyio.EndOfStream:
            pass
        finally:
            with contextlib.suppress(Exception):
                await stream.aclose()
            done.set()
    feed_broken = False
    if patch_reply_failure:
        import stdio_guard

        async def broken_reply(stream: Any, request_id: Any) -> None:
            raise RuntimeError("injected reply failure")

        original_reply = stdio_guard._reply_method_not_found
        stdio_guard._reply_method_not_found = broken_reply

    try:
        async with anyio.create_task_group() as tg:
            tg.start_soon(_forward_inbound, source_reader, forward_writer, reply_writer)
            tg.start_soon(collect, forward_reader, forwarded, fwd_done)
            tg.start_soon(collect, reply_reader, replies, reply_done)
            with contextlib.suppress(anyio.BrokenResourceError):
                for item in messages:
                    await source_writer.send(item)
                    await anyio.lowlevel.checkpoint()
            try:
                await source_writer.aclose()
            except anyio.BrokenResourceError:
                feed_broken = True
            with anyio.fail_after(5):
                await fwd_done.wait()
                await reply_writer.aclose()
                await reply_done.wait()
    finally:
        logging.getLogger("stdio_guard").removeHandler(capture)
        if patch_reply_failure:
            import stdio_guard

            stdio_guard._reply_method_not_found = original_reply
    return forwarded, replies, records


class TestDiscoverGuardInMemory(unittest.TestCase):
    """Synthetic boundary-pump contract on typed SDK messages."""

    def _run(self, messages: List[Any], **kw) -> Tuple[List[Any], List[Any], List[Any]]:
        return anyio.run(lambda: _drive(messages, **kw))

    def test_intercepts_probe_int_id_with_exact_reply(self):
        ping = _request(2, "ping")
        forwarded, replies, _ = self._run([_probe(1, {"q": 1}), ping])
        self.assertEqual(len(forwarded), 1)
        self.assertIs(forwarded[0], ping)
        self.assertEqual(len(replies), 1)
        root = replies[0].message.root
        self.assertEqual(root.id, 1)
        self.assertIsInstance(root.id, int)
        self.assertEqual(root.error.code, types.METHOD_NOT_FOUND)
        self.assertEqual(root.error.message, "Method not found")
        # Serialized exactly as the SDK stdout writer would emit it.
        line = replies[0].message.model_dump_json(by_alias=True, exclude_none=True)
        self.assertEqual(json.loads(line), _discover_reply(1))
        self.assertNotIn("params", json.loads(line))
        self.assertNotIn("_meta", line)
        self.assertEqual(replies[0].metadata, None)

    def test_intercepts_probe_string_id_preserved(self):
        forwarded, replies, _ = self._run(
            [_probe("client-probe-42", {"detail": "x"}), _request(3, "ping")])
        self.assertEqual([r.message.root.id for r in replies], ["client-probe-42"])
        line = replies[0].message.model_dump_json(by_alias=True, exclude_none=True)
        self.assertEqual(json.loads(line), _discover_reply("client-probe-42"))
        # No echoed request params anywhere in the reply.
        self.assertNotIn("detail", line)

    def test_repeated_probes_same_process_answer_every_time(self):
        probes = [_probe(1), _probe("str-9"), _probe(10)]
        forwarded, replies, records = self._run(probes + [_request(11, "ping")])
        self.assertEqual([m.message.root.id for m in replies], [1, "str-9", 10])
        self.assertEqual(len(forwarded), 1)
        self.assertFalse([r for r in records if r.levelno >= logging.ERROR])

    def test_notification_not_intercepted_nor_dropped(self):
        note = _notification(DISCOVER_METHOD)
        forwarded, replies, _ = self._run([note])
        self.assertEqual(forwarded, [note])  # passed to SDK validation unchanged
        self.assertEqual(replies, [])

    def test_supported_request_arg_mentioning_method_not_intercepted(self):
        call = _request(4, "tools/call",
                        {"name": "bridge_status", "arguments": {"method": DISCOVER_METHOD}})
        forwarded, replies, _ = self._run([call])
        self.assertIs(forwarded[0], call)
        self.assertEqual(replies, [])

    def test_unrelated_unknown_method_forwarded_unchanged(self):
        request = _request(5, "example/unknown/probe", {})
        forwarded, replies, _ = self._run([request])
        self.assertIs(forwarded[0], request)
        self.assertEqual(replies, [])

    def test_metadata_preserved_on_forwarded_message(self):
        base = _request(6, "ping")
        marked = dataclasses.replace(base, metadata="sentinel")
        forwarded, _, _ = self._run([marked])
        self.assertIs(forwarded[0], marked)
        self.assertEqual(forwarded[0].metadata, "sentinel")

    def test_transport_parse_error_object_forwarded(self):
        err = ValueError("malformed line")
        forwarded, replies, _ = self._run([err])
        self.assertIs(forwarded[0], err)
        self.assertEqual(replies, [])

    def test_forward_failure_logged_once_and_no_hang(self):
        forwarded, replies, records = self._run(
            [_probe(1), _request(7, "ping")], patch_reply_failure=True)
        errors = [r for r in records if r.levelno == logging.ERROR]
        self.assertEqual(len(errors), 1)
        self.assertIn("forwarder stopped", errors[0].getMessage())
        # Session still sees EOF instead of hanging: ping fallen through.
        self.assertGreaterEqual(len(forwarded), 0)

    def test_eof_closes_forward_stream_promptly(self):
        forwarded, replies, records = self._run([])
        self.assertEqual(forwarded, [])
        self.assertEqual(replies, [])
        self.assertEqual(records, [])


class _GuardedBoundaryScenario(unittest.TestCase):
    """Full guarded_stdio_streams boundary over normal StringIO transports."""

    def test_guarded_stdio_streams_in_memory(self):
        probe_line = json.dumps({"jsonrpc": "2.0", "id": 1,
                                 "method": DISCOVER_METHOD,
                                 "params": {"probe": "pre-init"}}) + "\n"
        ping_line = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"}) + "\n"
        out = io.StringIO()
        seen: List[Any] = []

        async def scenario():
            stdin_file = anyio.wrap_file(io.StringIO(probe_line + ping_line))
            stdout_file = anyio.wrap_file(out)
            async with guarded_stdio_streams(stdin=stdin_file, stdout=stdout_file) as (
                    guarded_read, _write):
                async def consume():
                    async with guarded_read:
                        async for item in guarded_read:
                            seen.append(item)

                async with anyio.create_task_group() as tg:
                    tg.start_soon(consume)
                    # guarded_read's producer closes after stdin EOF; consumer
                    # exits on its own once the forwarded stream closes.

        anyio.run(scenario)
        self.assertEqual(len(seen), 1)  # ping forwarded; probe intercepted
        self.assertEqual(seen[0].message.root.id, 2)
        lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0]), _discover_reply(1))
        self.assertNotIn("_meta", lines[0])


class _RawStdioProbe(unittest.TestCase):
    """Real-stdio probe harness: fixture bridge over pipes, raw JSON-RPC."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.stderr_path = Path(self.tmp.name) / "stderr.log"
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        self.errfile = open(self.stderr_path, "wb")
        self.proc = subprocess.Popen(
            [PY, str(Path(__file__).with_name("mock_mcp_server.py"))],
            cwd=str(REPO), env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.errfile, text=True, bufsize=1)
        self.replyq: List[str] = []
        self.reader = threading.Thread(target=self._read_out, daemon=True)
        self.reader.start()
        self.addCleanup(self.shutdown)

    def _read_out(self) -> None:
        assert self.proc.stdout is not None
        try:
            for line in self.proc.stdout:
                if line.strip():
                    self.replyq.append(line.strip())
        except Exception:
            pass

    def _send(self, obj: Dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _recv(self, want_id: Any, timeout: float = 20.0) -> Dict[str, Any]:
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() > deadline:
                self.fail("timed out waiting for reply id=%r" % (want_id,))
            if not self.replyq:
                time.sleep(0.02)
                if self.proc.poll() is not None and not self.replyq:
                    self.fail("fixture exited rc=%s waiting for id=%r"
                              % (self.proc.returncode, want_id))
                continue
            line = self.replyq.pop(0)
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                self.fail("non-JSON stdout contamination: %r" % line[:120])
            if obj.get("id") == want_id:
                return obj
            # skipping unrequested notification/log entries is expected

    def shutdown(self) -> None:
        proc = self.proc
        errfile, self.errfile = self.errfile, None
        if getattr(self, "stdin_closed", False) is False:
            try:
                if proc.stdin is not None:
                    proc.stdin.close()
            except Exception:
                pass
            self.stdin_closed = True
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
        if self.proc.stdout is not None:
            self.proc.stdout.close()
        if proc.stderr is not None:
            proc.stderr.close()
        self.reader.join(timeout=5)
        if errfile is not None:
            errfile.close()
            self.tmp.cleanup()

    def stderr_text(self) -> str:
        with open(self.stderr_path, "r", errors="replace") as handle:
            return handle.read()

    def initialize_legacy(self) -> Dict[str, Any]:
        self._send({"jsonrpc": "2.0", "id": 2, "method": "initialize",
                    "params": {"protocolVersion": "2025-11-25", "capabilities": {},
                               "clientInfo": {"name": "legacy-probe", "version": "0.0"}}})
        return self._recv(2)

    def notify_initialized(self) -> None:
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def probe_discover(self, msg_id: Any) -> Dict[str, Any]:
        self._send({"jsonrpc": "2.0", "id": msg_id, "method": DISCOVER_METHOD,
                    "params": {"unit": "probe"}})
        return self._recv(msg_id)


class TestDiscoverGuardRealStdio(_RawStdioProbe):
    """Isolated real-stdio sequence: probe BEFORE initialize, legacy session,
    repeat probes, unchanged SDK validation for everything else."""

    def test_pre_init_probe_then_legacy_session_full_sequence(self):
        # 1. Pre-initialize probe: answered -32601 at the boundary, same id.
        reply = self.probe_discover(1)
        self.assertEqual(reply, _discover_reply(1))

        # 2. Legacy initialize + initialized notification + tools/list.
        init = self.initialize_legacy()
        self.assertEqual(init["result"]["serverInfo"]["name"], "Hermes Local Bridge")
        self.assertEqual(init["result"]["protocolVersion"], "2025-11-25")
        self.notify_initialized()
        self._send({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}})
        listed = self._recv(3)
        self.assertEqual(len(listed["result"]["tools"]), 27)

        # 3. Repeat probes: same id shapes, no flood, int and string ids.
        self.assertEqual(self.probe_discover(4), _discover_reply(4))
        self.assertEqual(self.probe_discover("probe-str-9"), _discover_reply("probe-str-9"))

        # 4. tools/call whose argument merely names the method: served normally.
        self._send({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                    "params": {"name": "bridge_status",
                               "arguments": {"method": DISCOVER_METHOD}}})
        heartbeat = self._recv(5)
        self.assertTrue(heartbeat["result"]["structuredContent"]["ok"])

        # 5. Unrelated unknown method: SDK union validation unchanged (-32602).
        self._send({"jsonrpc": "2.0", "id": 6, "method": "example/unknown/probe",
                    "params": {}})
        unknown = self._recv(6)
        self.assertEqual(unknown["error"]["code"], -32602)

        # 6. Malformed SUPPORTED request: SDK validation error unchanged.
        self._send({"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                    "params": {"arguments": {}}})
        malformed = self._recv(7)
        self.assertEqual(malformed["error"]["code"], -32602)

        # 7. Invalid envelope: process stays alive for valid traffic.
        self._send({"jsonrpc": "2.0", "id": 8, "method": 123})
        self._send({"jsonrpc": "2.0", "id": 9, "method": "ping"})
        self.assertEqual(self._recv(9)["id"], 9)

        # 8. Reply-shape discipline: no params echo, no sentinel metadata.
        for obj in (reply, listed, malformed):
            self.assertNotIn("params", json.dumps(obj))
        self.assertEqual("server/discover" not in json.dumps(_discover_reply(1)), True)

        # 9. Warning accounting: recognize probes log NOTHING; the two genuinely
        #    invalid requests still carry their SDK warnings (no broad hide).
        text = self.stderr_text()
        warnings = [ln for ln in text.splitlines()
                    if "Failed to validate request" in ln]
        self.assertEqual(len(warnings), 2, "unexpected warning flood:\n%s" % "\n".join(warnings[:2]))

        # 10. EOF shutdown: clean exit, stdout stayed parseable throughout.
        self.proc.stdin.close()
        self.stdin_closed = True
        self.proc.wait(timeout=15)
        self.assertEqual(self.proc.returncode, 0)

    def test_probe_reply_has_no_meta_when_repeatedly_probed(self):
        for msg_id in (1, "s-1", 2):
            reply = self.probe_discover(msg_id)
            self.assertEqual(reply, _discover_reply(msg_id))
            self.assertNotIn("_meta", json.dumps(reply))
        self.proc.stdin.close()
        self.stdin_closed = True
        self.proc.wait(timeout=15)
        self.assertEqual(self.proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
