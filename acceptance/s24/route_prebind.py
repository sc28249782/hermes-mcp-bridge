"""Manifest-only MCP metadata peer. No fixture import, launcher or active mode.

This source is for review/offline tests, not permission to install or start a
tunnel/plugin. Advertised schemas are not candidate discovery or route proof.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import select
import sys
import time

MANIFEST_SHA256 = "ef081b19445fa9132f54f434254c04fbf4532b716ad1f994bbc1415261702ab9"
FRAME_LIMIT = 65536
OUTPUT_LIMIT = 1024 * 1024
REQUEST_LIMIT = 128
WINDOW_SECONDS = 30
INSTRUCTIONS = ("INACTIVE: manifest-only prebinding metadata, not candidate discovery. "
                "Every tool call is rejected. No fixture, task or state is started. "
                "No activation mode exists; setup and later source/route binding need separate review and approval.")
DENIED = {"content": [{"type": "text", "text": "S24_ROUTE_INACTIVE"}], "isError": True,
          "structuredContent": {"error": "S24_ROUTE_INACTIVE", "evidence_class": "manifest-only-prebinding",
                                "fixture_started": False, "operational_b_ready": False}}


class Hold(RuntimeError):
    pass


def require(value):
    if not value:
        raise Hold("inactive metadata peer held")


def object_pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value)
        value[key] = item
    return value


def loads(raw):
    value = json.loads(raw, object_pairs_hook=object_pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(Hold("nonfinite metadata input")))
    # Re-encode to reject overflow floats such as 1e400 in otherwise unused args.
    json.dumps(value, allow_nan=False)
    return value


def load_manifest():
    path = Path(__file__).with_name("discovery_manifest.json")
    require(not path.is_symlink())
    with path.open("rb") as stream:
        raw = stream.read(FRAME_LIMIT + 1)
    require(len(raw) <= FRAME_LIMIT and hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256)
    value = loads(raw)
    require(value["candidate_commit"] == "02d7e8bb1e1902ca33a574ab904a6e5b0f441785"
            and value["artifact_commit"] == "e7be0cc4e84b820eb8c7ac541325672d0f892fb2"
            and len(value["tools"]) == 27)
    return value


class MetadataOnlyPeer:
    def __init__(self):
        self.manifest = load_manifest()
        self.initialized = self.notified = self.held = False
        self.requests = self.output_bytes = 0

    def handle(self, raw):
        try:
            require(not self.held and type(raw) is bytes and 0 < len(raw) <= FRAME_LIMIT
                    and raw.endswith(b"\n") and b"\n" not in raw[:-1] and self.requests < REQUEST_LIMIT)
            self.requests += 1
            value = loads(raw.decode("utf-8"))
            require(type(value) is dict and value.get("jsonrpc") == "2.0"
                    and type(value.get("method")) is str and type(value.get("params", {})) is dict)
            method, params = value["method"], value.get("params", {})
            if "id" not in value:
                if method == "notifications/initialized":
                    require(self.initialized and not self.notified)
                    self.notified = True
                return None
            require(type(value["id"]) in (str, int))
            response = {"jsonrpc": "2.0", "id": value["id"]}
            if method == "initialize":
                require(not self.initialized and type(params.get("protocolVersion")) is str)
                # Read pinned SDK constants only. This never imports fixture/candidate code.
                from mcp.shared.version import SUPPORTED_PROTOCOL_VERSIONS
                from mcp.types import LATEST_PROTOCOL_VERSION
                version = params["protocolVersion"]
                self.initialized = True
                response["result"] = {"protocolVersion": version if version in SUPPORTED_PROTOCOL_VERSIONS
                                      else LATEST_PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "s24-inactive-metadata", "version": "0.0.0-prebind"},
                    "instructions": INSTRUCTIONS}
            elif method in ("tools/list", "tools/call"):
                require(self.initialized and self.notified)
                if method == "tools/list":
                    require(params.get("cursor") is None)
                    response["result"] = {"tools": [{"name": name,
                        "description": "INACTIVE manifest metadata. Every call is rejected; no fixture is running.",
                        **deepcopy(schema)} for name, schema in sorted(self.manifest["tools"].items())]}
                else:
                    require(type(params.get("name")) is str and type(params.get("arguments", {})) is dict)
                    response["result"] = deepcopy(DENIED)  # Includes version/submit/unknown tools. No dispatch table.
            elif method == "ping":
                require(self.initialized)
                response["result"] = {}
            else:
                # Legacy server/discover can fail without starting or poisoning a fixture.
                response["error"] = {"code": -32601, "message": "Method not found"}
            reply = (json.dumps(response, ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n").encode()
            require(len(reply) <= FRAME_LIMIT and self.output_bytes + len(reply) <= OUTPUT_LIMIT)
            self.output_bytes += len(reply)
            return reply
        except BaseException:
            self.held = True
            raise


def serve():
    deadline = time.monotonic() + WINDOW_SECONDS  # Never reset at initialize/reconnect.
    peer = MetadataOnlyPeer()
    incoming, outgoing = sys.stdin.fileno(), sys.stdout.fileno()
    os.set_blocking(incoming, False)
    os.set_blocking(outgoing, False)
    buffer = bytearray()
    while time.monotonic() < deadline:
        if not select.select([incoming], [], [], max(0, deadline - time.monotonic()))[0]:
            raise Hold("inactive peer deadline")
        part = os.read(incoming, 4096)
        if not part:
            require(not buffer)
            return
        buffer.extend(part)
        require(len(buffer) <= FRAME_LIMIT)
        while b"\n" in buffer:
            end = buffer.index(b"\n") + 1
            raw = bytes(buffer[:end])
            del buffer[:end]
            reply = peer.handle(raw)
            view = memoryview(reply or b"")
            while view:
                require(time.monotonic() < deadline)
                require(select.select([], [outgoing], [], max(0, deadline - time.monotonic()))[1])
                try:
                    wrote = os.write(outgoing, view[:4096])
                    require(wrote > 0)
                    view = view[wrote:]
                except BlockingIOError:
                    continue  # Nonblocking pipe readiness, not a tool/transport retry.
    raise Hold("inactive peer deadline")


def main():
    class ConstantParser(argparse.ArgumentParser):
        def error(self, message):
            raise Hold("metadata-only arguments required")
    parser = ConstantParser(description=__doc__)
    parser.add_argument("--metadata-only", required=True, action="store_true")
    try:
        parser.parse_args()  # No candidate/state/credential/active/forwarding arguments exist.
        serve()
    except SystemExit as result:
        return result.code  # --help only; parser errors use the constant HOLD path.
    except BaseException:
        print("HOLD: inactive metadata peer unavailable", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
