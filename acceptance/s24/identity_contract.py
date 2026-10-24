"""Offline identity/discovery data validator. No transport or activation interface.

Supplied JSON-RPC-shaped records are test inputs, not authenticated wire captures.
No result grants authority or enables the separate matrix runner.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from parent_contract import ARTIFACT_PIN, Hold, decode, encode, require
import s24_fixture as fixture

MANIFEST_SHA256 = "ef081b19445fa9132f54f434254c04fbf4532b716ad1f994bbc1415261702ab9"
MAX_PAGES = 8
MAX_CAPTURE_BYTES = 1024 * 1024
EVIDENCE_CLASS = "offline-identity-discovery-contract"
EMBEDDED_INPUT = "887436f359683f0215f1993d7cb0c9035ec93571"
SCHEMA_FIELDS = ("inputSchema", "outputSchema", "annotations")


def load_manifest():
    """Read the reviewed local manifest only; never an operator-supplied URL/path."""
    path = Path(__file__).with_name("discovery_manifest.json")
    require(not path.is_symlink(), "discovery manifest symlink")
    with path.open("rb") as stream:
        raw = stream.read(65537)
    require(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256,
            "discovery manifest integrity")
    value = json.loads(raw)
    require(value["candidate_commit"] == fixture.PIN and value["artifact_commit"] == ARTIFACT_PIN
            and len(value["tools"]) == 27, "discovery manifest input")
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":"))


def expected_version(source_kind):
    require(source_kind in ("git-worktree", "release-archive"), "unsupported source kind")
    git = source_kind == "git-worktree"
    return {"ok": True, "version": "1.2.8", "release_identifier": "v1.2.8",
            "build_provenance": "release", "source_kind": source_kind,
            "source_revision": fixture.PIN if git else EMBEDDED_INPUT,
            "revision_source": "git" if git else "embedded-build-input",
            "config_schema_version": "unknown", "embedded_config_schema_version": 1,
            "mcp_discovery_count": 27}


class OfflineIdentityContract:
    """One version result then bounded, cursor-linked discovery pages, offline only.

    The two source shapes model the pinned checkout and a no-.git tree. An inherited
    embedded revision never substitutes for independent candidate content checks.
    Source-kind selection, JSON-RPC ids and schema hashes are not authentication.
    """

    def __init__(self, source_kind):
        self._manifest = load_manifest()
        self._version_expected = expected_version(source_kind)
        self._pending = None
        self._sequence = self._pages = self._bytes = 0
        self._cursor = None
        self._seen_cursors = set()
        self._tools = {}
        self._version = None
        self._held = self._finished = False
        self._capture = []

    def _open(self):
        require(not self._held and not self._finished, "identity contract closed")

    def request(self):
        """Return one data frame. This method never sends it or starts a client."""
        try:
            self._open()
            require(self._pending is None, "request already outstanding")
            self._sequence += 1
            if self._version is None:
                params = {"name": "bridge_version", "arguments": {}}
                method = "tools/call"
            else:
                require(self._pages < MAX_PAGES, "discovery page limit")
                params = {} if self._cursor is None else {"cursor": self._cursor}
                method = "tools/list"
            value = {"jsonrpc": "2.0", "id": self._sequence, "method": method, "params": params}
            raw = encode(value)
            self._record(raw)
            self._pending = value
            return raw
        except BaseException:
            self._held = True
            raise

    def _record(self, raw):
        require(type(raw) is bytes and self._bytes + len(raw) <= MAX_CAPTURE_BYTES,
                "identity capture budget/type")
        self._bytes += len(raw)
        self._capture.append(raw)

    def accept(self, raw):
        """Validate a supplied reply; no fallback, retry or external dispatch."""
        try:
            self._open()
            require(self._pending is not None, "unsolicited reply")
            reply = decode(raw)
            self._record(raw)
            require(set(reply) == {"jsonrpc", "id", "result"} and reply["jsonrpc"] == "2.0"
                    and type(reply["id"]) is int and reply["id"] == self._pending["id"],
                    "identity reply envelope/order")
            if self._pending["method"] == "tools/call":
                self._accept_version(reply["result"])
            else:
                self._accept_page(reply["result"])
            self._pending = None
            return self.summary() if self._finished else None
        except BaseException:
            self._held = True
            raise

    def _accept_version(self, result):
        require(type(result) is dict and result.get("isError") is False
                and type(result.get("content")) is list, "version tool error/shape")
        actual = result.get("structuredContent")
        # Canonical JSON comparison distinguishes bool from int (True != schema 1).
        require(type(actual) is dict and canonical(actual) == canonical(self._version_expected),
                "version identity mismatch")
        self._version = deepcopy(result)

    def _accept_page(self, result):
        require(type(result) is dict and set(result) <= {"tools", "nextCursor", "_meta"}
                and type(result.get("tools")) is list, "discovery page shape")
        tools = result["tools"]
        require(len(tools) <= 27, "too many tools in page")
        for tool in tools:
            require(type(tool) is dict and type(tool.get("name")) is str, "tool entry shape")
            name = tool["name"]
            require(name in self._manifest["tools"] and name not in self._tools,
                    "unknown/duplicate discovery tool")
            observed = {field: tool.get(field) for field in SCHEMA_FIELDS}
            require(canonical(observed) == canonical(self._manifest["tools"][name]),
                    "tool schema/annotation mismatch")
            self._tools[name] = deepcopy(tool)
        self._pages += 1
        cursor = result.get("nextCursor")
        if cursor is not None:
            require(type(cursor) is str and 0 < len(cursor) <= 256
                    and cursor.isprintable() and cursor not in self._seen_cursors,
                    "invalid/repeated discovery cursor")
            require(self._pages < MAX_PAGES, "discovery page limit")
            self._seen_cursors.add(cursor)
            self._cursor = cursor
        else:
            require(set(self._tools) == set(self._manifest["tools"]), "incomplete discovery")
            self._finished = True

    def summary(self):
        require(not self._held and self._finished and self._pending is None,
                "identity contract incomplete/held")
        return {"evidence_class": EVIDENCE_CLASS, "candidate": fixture.PIN,
                "artifact": ARTIFACT_PIN, "schema_manifest_sha256": MANIFEST_SHA256,
                "reported_version": deepcopy(self._version["structuredContent"]),
                "decoded_tools_count": len(self._tools), "pages": self._pages,
                "capture_bytes": self._bytes,
                "capture_sha256": hashlib.sha256(b"".join(self._capture)).hexdigest()}

    def decoded_results(self):
        """Copies preserve metadata/content; these are decoded data, not wire bytes."""
        self.summary()
        return {"version_result": deepcopy(self._version), "tools": deepcopy(self._tools)}
