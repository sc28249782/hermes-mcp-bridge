#!/usr/bin/env python3
"""Legacy stdio boundary guard for unsupported `server/discover` probes.

Diagnosed behavior (mcp 1.30.0, bridge legacy stdio serve): the SDK validates
every inbound JSON-RPC request against the ClientRequest union in
mcp.shared.session.A modern discovery probe `server/discover` is not a union
member, so each probe gets -32602 "Invalid request parameters" plus a ~6 KB
"Failed to validate request: N validation errors for ClientRequest..." union
repr logged per probe. Normal tools/list works either way.

This module answers ONLY those probes, at the official SDK stdio stream
boundary exactly as specified in docs/SPEC.md section 17:

- an exact top-level-method `server/discover` REQUEST (typed JSONRPCRequest)
  is answered in place with JSONRPCError code -32601 (METHOD_NOT_FOUND),
  constant message "Method not found", the SAME request id (int or string
  preserved), and no echoed params; it never reaches the low-level server
  and its payload is never logged (one constant-text debug line is allowed);
- every other inbound item - supported requests, unrelated unknown methods,
  responses, notifications (including a notification-shaped
  `server/discover`), and transport parse errors - is forwarded unchanged as
  the same Python object with transport metadata preserved, leaving SDK
  union-validation behavior (including its -32602 replies and warnings)
  completely uncovered;
- initialize capabilities and tool registration are untouched: default
  discovery stays 27 tools (28 only with the explicitly enabled OpenCode
  health adapter), and no modern discovery protocol or capability is claimed.

The wrap is local to the bridge serve path (run_stdio_guarded); no site-
packages edit, no monkeypatch of SDK symbols, no dependency change.

Shape pin: run_stdio_guarded mirrors FastMCP.run_stdio_async verbatim for
mcp 1.30.0 (fastmcp/server.py lines 769-776) with only the streams wrapped:

    async with stdio_server() as (read_stream, write_stream):
        await self._mcp_server.run(
            read_stream, write_stream,
            self._mcp_server.create_initialization_options(),
        )

If a future SDK changes that method shape, guarded life must be updated and
the real-stdio tests re-run; tests/test_stdio_guard.py covers it.
"""
import contextlib
import functools
import logging
import typing

import anyio
import mcp.types as types
from anyio.streams.memory import MemoryObjectReceiveStream
from mcp.server.stdio import stdio_server
from mcp.shared.message import SessionMessage

logger = logging.getLogger(__name__)

#: Exact top-level JSON-RPC method intercepted at the legacy stdio boundary.
DISCOVER_METHOD = "server/discover"

_REPLY_MESSAGE = "Method not found"  # constant; matches SDK METHOD_NOT_FOUND text


def _is_legacy_discover_request(item: typing.Any) -> bool:
    """True only for an inbound typed SessionMessage whose root is a typed
    JSONRPCRequest with the exact top-level method. Notifications and any
    other message (including ones whose params merely mention the method)
    return False."""
    if isinstance(item, Exception) or not isinstance(item, SessionMessage):
        return False
    root = item.message.root
    return isinstance(root, types.JSONRPCRequest) and root.method == DISCOVER_METHOD


async def _reply_method_not_found(
    reply_stream: typing.Any,
    request_id: types.RequestId,
) -> None:
    """Send the constant -32601 error with the caller's request id and no
    echoed params (exclude_none drops the empty data field)."""
    message = types.JSONRPCMessage(
        root=types.JSONRPCError(
            jsonrpc="2.0",
            id=request_id,
            error=types.ErrorData(code=types.METHOD_NOT_FOUND, message=_REPLY_MESSAGE),
        )
    )
    await reply_stream.send(SessionMessage(message=message, metadata=None))


async def _forward_inbound(
    source: MemoryObjectReceiveStream,
    forward_writer: typing.Any,
    reply_stream: typing.Any,
) -> None:
    """Forward each inbound message to the session; intercept only exact
    server/discover requests. Swallows only expected shutdown errors; anything
    else is logged once and the forward stream is closed (the session then
    sees EOF instead of hanging). Cancellation propagates normally."""
    try:
        async with forward_writer:
            async for item in source:
                if _is_legacy_discover_request(item):
                    # Constant text only; the probe payload never enters logs.
                    logger.debug("stdio guard: %s answered with -32601", DISCOVER_METHOD)
                    await _reply_method_not_found(reply_stream, item.message.root.id)
                    continue
                await forward_writer.send(item)
    except (anyio.EndOfStream, anyio.ClosedResourceError, anyio.BrokenResourceError):
        pass  # stdin EOF or consumer closed first: normal shutdown paths
    except Exception:
        logger.exception("stdio guard: forwarder stopped")
    finally:
        with contextlib.suppress(Exception):
            await forward_writer.aclose()
        with contextlib.suppress(Exception):
            await source.aclose()


@contextlib.asynccontextmanager
async def guarded_stdio_streams(stdin: typing.Any = None, stdout: typing.Any = None) -> typing.AsyncIterator[tuple[
    MemoryObjectReceiveStream, typing.Any,
]]:
    """`stdio_server()` with the guarded read side.

    stdin/stdout simply pass through to stdio_server() (None = the process
    stdio). The returned streams have exactly the SDK boundary types: a
    MemoryObjectReceiveStream of SessionMessage | Exception for the session
    and the original MemoryObjectSendStream for replies, so all delivered
    messages are typed SDK objects and the raw write side stays untouched.
    """
    async with stdio_server(stdin=stdin, stdout=stdout) as (read_stream, write_stream):
        forward_writer, guarded_read = anyio.create_memory_object_stream(0)
        async with anyio.create_task_group() as tg:
            tg.start_soon(_forward_inbound, read_stream, forward_writer, write_stream)
            try:
                yield guarded_read, write_stream
            finally:
                # Stop the forwarder FIRST: it may be blocked waiting on stdin
                # (no EOF yet) or on a consumer that already stopped, and closing
                # the guarded read side alone does not wake it (SPEC.md section
                # 17: cancellation-safe, no detached tasks, no hang).
                tg.cancel_scope.cancel()
                with anyio.CancelScope(shield=True):
                    try:
                        await guarded_read.aclose()
                    except (anyio.ClosedResourceError, anyio.BrokenResourceError):
                        pass  # consumer closed the guarded stream first: normal
                    except Exception:
                        logger.error("stdio guard: guarded read close failed")
                        raise
                    # Wake the SDK stdout_writer (blocked receiving on this send
                    # side) so the inner stdio_server() task group unwinds instead
                    # of hanging: mcp's stdio_server has no exit cancel of its own.
                    try:
                        await write_stream.aclose()
                    except (anyio.ClosedResourceError, anyio.BrokenResourceError):
                        pass  # already closed: normal shutdown
                    except Exception:
                        logger.error("stdio guard: reply stream close failed")
                        raise


async def _serve_guarded(fastmcp_server: typing.Any) -> None:
    async with guarded_stdio_streams() as (read_stream, write_stream):
        lowlevel = fastmcp_server._mcp_server
        await lowlevel.run(
            read_stream,
            write_stream,
            lowlevel.create_initialization_options(),
        )


def run_stdio_guarded(fastmcp_server: typing.Any) -> None:
    """Run a FastMCP server on the stdio transport behind the legacy discover
    guard (verbatim mirror of FastMCP.run_stdio_async for mcp 1.30.0 with
    guarded read streams). The tunnel/HTTP transports keep using
    FastMCP.run() untouched."""
    anyio.run(functools.partial(_serve_guarded, fastmcp_server))
