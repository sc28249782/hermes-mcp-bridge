"""Dev-only MCP Events probe fixture.

This module is intentionally not the bridge runtime event implementation.  It is
started only through the BRIDGE_EVENTS_PROBE=1 wrapper switch on the Dev tunnel.
It keeps subscriptions only in memory and emits exactly one redacted probe event
after callback verification.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import socket
import sys
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

import httpx

PROTOCOL_VERSION = "2026-07-28"
EVENT_NAME = "bridge.probe.ready"
MAX_CALLBACK_URL = 2048
MAX_RESPONSE_BYTES = 4096
TRACE_METHODS = frozenset({
    "initialize", "notifications/initialized", "server/discover",
    "tools/list", "events/list", "events/subscribe", "events/unsubscribe",
})


def _trace(method: Any, outcome: str, code: int | None = None) -> None:
    """Write fixed metadata to stderr; never serialize IDs, params, or payloads."""
    record: dict[str, Any] = {
        "component": "events_probe",
        "time": _now(),
        "method": method if isinstance(method, str) and method in TRACE_METHODS else "other",
        "outcome": outcome,
    }
    if code is not None:
        record["code"] = code
    print(json.dumps(record, separators=(",", ":")), file=sys.stderr, flush=True)


class ProbeError(ValueError):
    def __init__(self, message: str, code: int = -32602, reason: str | None = None):
        super().__init__(message)
        self.code = code
        self.reason = reason


def _canonical_dns(name: str) -> str:
    if not isinstance(name, str) or not name or len(name) > 253:
        raise ProbeError("callback denied")
    try:
        value = name.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ProbeError("callback denied") from exc
    labels = value.split(".")
    if (not value or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                         for label in labels)):
        raise ProbeError("callback denied")
    return value


def _parse_allowlist(raw: str) -> tuple[str, ...]:
    entries: list[str] = []
    for value in raw.split(","):
        value = value.strip()
        if not value:
            continue
        wildcard = value.startswith("*.")
        host = value[2:] if wildcard else value
        # Permit exactly an ASCII/IDNA hostname, with one optional wildcard prefix.
        if "/" in host or ":" in host or "@" in host or "*" in host:
            raise ProbeError("invalid Dev probe allowlist")
        canonical = _canonical_dns(host)
        entries.append("*." + canonical if wildcard else canonical)
    return tuple(dict.fromkeys(entries))


def _is_allowed(host: str, entries: tuple[str, ...]) -> bool:
    for entry in entries:
        if entry.startswith("*."):
            suffix = entry[2:]
            if host.endswith("." + suffix):
                return True
        elif hmac.compare_digest(host, entry):
            return True
    return False


def _callback_url(value: Any, allowlist: tuple[str, ...], *, resolve_public: bool = True) -> str:
    if not isinstance(value, str) or not value or len(value) > MAX_CALLBACK_URL:
        raise ProbeError("callback denied")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ProbeError("callback denied") from exc
    if (parsed.scheme != "https" or not parsed.netloc or parsed.username or
            parsed.password or parsed.fragment or port not in (None, 443)):
        raise ProbeError("callback denied")
    host = parsed.hostname
    if not host:
        raise ProbeError("callback denied")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        canonical = _canonical_dns(host)
    else:
        raise ProbeError("callback denied")
    if not allowlist or not _is_allowed(canonical, allowlist):
        raise ProbeError("callback denied")
    if resolve_public:
        _require_public_dns(canonical)
    return value


def _require_public_dns(host: str) -> None:
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ProbeError("callback denied") from exc
    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise ProbeError("callback denied")
    try:
        if any(not ipaddress.ip_address(value).is_global for value in addresses):
            raise ProbeError("callback denied")
    except ValueError as exc:
        raise ProbeError("callback denied") from exc


def _secret(value: Any) -> bytes:
    if not isinstance(value, str) or not value.startswith("whsec_"):
        raise ProbeError("invalid callback secret")
    encoded = value[6:]
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ProbeError("invalid callback secret") from exc
    if not 24 <= len(data) <= 64:
        raise ProbeError("invalid callback secret")
    return data


def _canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _signature(secret: bytes, message_id: str, timestamp: str, body: bytes) -> str:
    signed = message_id.encode() + b"." + timestamp.encode() + b"." + body
    digest = hmac.new(secret, signed, hashlib.sha256).digest()
    return "v1," + base64.b64encode(digest).decode("ascii")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class EventsProbe:
    def __init__(self, allowed_hosts: tuple[str, ...],
                 sender: Any | None = None):
        self.allowed_hosts = allowed_hosts
        self.sender = sender or self._send
        self.subscriptions: dict[str, dict[str, Any]] = {}

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method")
        if not isinstance(method, str):
            _trace("other", "error", -32600)
            return self._error(request_id, ProbeError("invalid request"))
        if method == "notifications/initialized":
            _trace(method, "notification")
            return None
        try:
            if method == "initialize":
                result = self.initialize(request.get("params"))
            elif method == "server/discover":
                result = self.discover(request.get("params"))
            elif method == "tools/list":
                result = {"tools": []}
            elif method == "events/list":
                result = self.list_events(request.get("params"))
            elif method == "events/subscribe":
                result = self.subscribe(request.get("params"))
            elif method == "events/unsubscribe":
                result = self.unsubscribe(request.get("params"))
            else:
                raise ProbeError("method not found", code=-32601)
        except ProbeError as exc:
            _trace(method, "error", exc.code)
            return self._error(request_id, exc)
        _trace(method, "ok")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: Any, exc: ProbeError) -> dict[str, Any]:
        error: dict[str, Any] = {"code": exc.code, "message": str(exc)}
        if exc.reason:
            error["data"] = {"reason": exc.reason}
        return {"jsonrpc": "2.0", "id": request_id, "error": error}

    @staticmethod
    def initialize(params: Any) -> dict[str, Any]:
        if params is not None and not isinstance(params, dict):
            raise ProbeError("invalid initialize parameters")
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "events": {}},
            "serverInfo": {"name": "Hermes Local Bridge Dev Events Probe",
                           "version": "0"},
        }

    @staticmethod
    def discover(params: Any) -> dict[str, Any]:
        if params is not None and not isinstance(params, dict):
            raise ProbeError("invalid discover parameters")
        return {
            "resultType": "complete",
            "supportedVersions": [PROTOCOL_VERSION],
            "capabilities": {"tools": {}, "events": {}},
        }

    @staticmethod
    def list_events(params: Any) -> dict[str, Any]:
        if params not in (None, {}) and not isinstance(params, dict):
            raise ProbeError("invalid event-list parameters")
        return {
            "events": [{
                "name": EVENT_NAME,
                "description": "Dev-only signed callback probe; contains no bridge task data.",
                "delivery": ["webhook"],
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                "payloadSchema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                    },
                    "required": ["status"],
                    "additionalProperties": False,
                },
            }],
            "nextCursor": None,
        }

    def subscribe(self, params: Any) -> dict[str, Any]:
        if not isinstance(params, dict):
            raise ProbeError("invalid subscription parameters")
        if params.get("name") != EVENT_NAME or params.get("arguments") != {}:
            raise ProbeError("unsupported event subscription")
        delivery = params.get("delivery")
        if not isinstance(delivery, dict) or set(delivery) != {"mode", "url", "secret"}:
            raise ProbeError("invalid subscription delivery")
        if delivery.get("mode") != "webhook":
            raise ProbeError("unsupported delivery mode")
        url = _callback_url(delivery.get("url"), self.allowed_hosts)
        secret = _secret(delivery.get("secret"))
        identity = _canonical_json({"name": EVENT_NAME, "arguments": {}, "url": url})
        subscription_id = "sub_probe_" + hashlib.sha256(identity).hexdigest()[:24]
        try:
            self._verify(url, secret, subscription_id)
            self._deliver(url, secret, subscription_id)
        except ProbeError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise ProbeError("callback endpoint error", code=-32015,
                             reason="transport_failed") from exc
        self.subscriptions[subscription_id] = {"name": EVENT_NAME, "arguments": {}}
        return {
            "id": subscription_id,
            "refreshBefore": None,
            "cursor": None,
            "truncated": False,
        }

    def unsubscribe(self, params: Any) -> dict[str, Any]:
        if not isinstance(params, dict):
            raise ProbeError("invalid unsubscribe parameters")
        if params.get("name") != EVENT_NAME or params.get("arguments") != {}:
            raise ProbeError("unsupported event subscription")
        delivery = params.get("delivery")
        if not isinstance(delivery, dict) or set(delivery) != {"mode", "url"}:
            raise ProbeError("invalid unsubscribe delivery")
        if delivery.get("mode") != "webhook":
            raise ProbeError("unsupported delivery mode")
        url = _callback_url(delivery.get("url"), self.allowed_hosts, resolve_public=False)
        identity = _canonical_json({"name": EVENT_NAME, "arguments": {}, "url": url})
        subscription_id = "sub_probe_" + hashlib.sha256(identity).hexdigest()[:24]
        self.subscriptions.pop(subscription_id, None)
        return {}

    def _verify(self, url: str, secret: bytes, subscription_id: str) -> None:
        challenge = secrets.token_urlsafe(24)
        response = self._post(url, secret, subscription_id, "msg_verification_" + secrets.token_hex(12),
                              {"type": "verification", "challenge": challenge})
        if not 200 <= response.status_code < 300:
            raise ProbeError("callback endpoint error", code=-32015,
                             reason="challenge_failed")
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise ProbeError("callback endpoint error", code=-32015,
                             reason="challenge_failed")
        try:
            returned = response.json()
        except ValueError as exc:
            raise ProbeError("callback endpoint error", code=-32015,
                             reason="challenge_failed") from exc
        if not isinstance(returned, dict) or not isinstance(returned.get("challenge"), str):
            raise ProbeError("callback endpoint error", code=-32015,
                             reason="challenge_failed")
        if not hmac.compare_digest(returned["challenge"], challenge):
            raise ProbeError("callback endpoint error", code=-32015,
                             reason="challenge_failed")

    def _deliver(self, url: str, secret: bytes, subscription_id: str) -> None:
        event_id = "evt_probe_" + secrets.token_hex(12)
        response = self._post(url, secret, subscription_id, event_id, {
            "eventId": event_id,
            "name": EVENT_NAME,
            "timestamp": _now(),
            "data": {"status": "accepted"},
            "cursor": None,
        })
        if not 200 <= response.status_code < 300:
            raise ProbeError("callback endpoint error", code=-32015,
                             reason="delivery_failed")

    @staticmethod
    def _send(url: str, secret: bytes, subscription_id: str, message_id: str,
              payload: dict[str, Any]) -> httpx.Response:
        body = _canonical_json(payload)
        if len(body) > 256 * 1024:
            raise ProbeError("callback endpoint error", code=-32015,
                             reason="payload_too_large")
        timestamp = str(int(time.time()))
        headers = {
            "Content-Type": "application/json",
            "webhook-id": message_id,
            "webhook-timestamp": timestamp,
            "webhook-signature": _signature(secret, message_id, timestamp, body),
            "X-MCP-Subscription-Id": subscription_id,
        }
        with httpx.Client(timeout=10.0, follow_redirects=False, trust_env=False) as client:
            return client.post(url, content=body, headers=headers)

    def _post(self, url: str, secret: bytes, subscription_id: str, message_id: str,
              payload: dict[str, Any]) -> httpx.Response:
        return self.sender(url, secret, subscription_id, message_id, payload)


def serve_stdio() -> None:
    allowlist = _parse_allowlist(os.environ.get("BRIDGE_EVENTS_PROBE_ALLOWED_HOSTS", ""))
    probe = EventsProbe(allowlist)
    for raw in sys.stdin:
        try:
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise ProbeError("invalid request")
            response = probe.handle(request)
        except (json.JSONDecodeError, UnicodeError, ProbeError):
            _trace("other", "error", -32600)
            response = {"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32600, "message": "invalid request"}}
        if response is not None:
            print(json.dumps(response, separators=(",", ":"), ensure_ascii=False),
                  flush=True)
