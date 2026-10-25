"""Bounded shared-key observation messages; no socket, key setup or host identity proof.

The byte carrier and producer method are injected. MAC verification establishes
possession of the bound shared key, not machine identity, encryption or approval.
Sequence/nonce state is process-local; no resume/reconnect interface is provided.
"""
import asyncio
from copy import deepcopy
import hashlib
import hmac
import json
import math
import secrets
import time

from parent_contract import FRESHNESS_SECONDS, MAX_FRAME_BYTES, Hold, STAGES, decode, encode, require

EVIDENCE_CLASS = "shared-key-observer-message"
DOMAIN = b"s24-observer-message-v1\0"
ROLES = frozenset(("host-memory", "guest-resources", "runtime-continuity", "writer-inventory"))
MESSAGE_KEYS = frozenset(("v", "direction", "attempt", "binding", "producer", "role",
                          "seq", "stage", "nonce", "payload", "sample_seconds"))
BYTE_LIMIT = 8 * 1024 * 1024
PRODUCER_SECONDS = 1


def hex64(value):
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def signed(key, message):
    canonical = json.dumps(message, sort_keys=True, ensure_ascii=True, allow_nan=False,
                           separators=(",", ":")).encode("ascii")
    mac = hmac.new(key, DOMAIN + canonical, hashlib.sha256).hexdigest()
    return encode({"message": message, "mac_sha256": mac})


def verified(key, raw):
    envelope = decode(raw)
    require(set(envelope) == {"message", "mac_sha256"} and hex64(envelope["mac_sha256"]),
            "observer envelope shape")
    message = envelope["message"]
    require(type(message) is dict and set(message) == MESSAGE_KEYS, "observer message shape")
    require(type(message["v"]) is int and message["v"] == 1
            and type(message["seq"]) is int and 1 <= message["seq"] <= len(STAGES)
            and hex64(message["nonce"]) and type(message["payload"]) is dict
            and finite(message["sample_seconds"]), "observer message types")
    expected = decode(signed(key, message))["mac_sha256"]
    require(hmac.compare_digest(envelope["mac_sha256"], expected), "observer MAC mismatch")
    return message


class BoundMessages:
    def __init__(self, key, *, attempt, binding, producer, role, record, clock=time.monotonic):
        require(type(key) is bytes and len(key) == 32, "32-byte prebound observer key required")
        require(type(attempt) is str and 0 < len(attempt) <= 64
                and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in attempt),
                "observer attempt binding")
        require(hex64(binding) and type(producer) is str and 0 < len(producer) <= 64
                and producer.isascii() and producer.isalnum() and role in ROLES,
                "observer producer/role binding")
        require(callable(record) and callable(clock), "observer recorder and clock required")
        self._key = key
        self.attempt, self.binding, self.producer, self.role = attempt, binding, producer, role
        self.record, self.clock = record, clock
        self.sequence = self.byte_count = 0
        self.nonces = set()
        self.held = self.busy = False
        self.last_clock = self.clock()
        require(finite(self.last_clock), "observer local clock")

    def now(self):
        current = self.clock()
        require(finite(current) and current >= self.last_clock, "observer clock moved backwards")
        self.last_clock = current
        return current

    def enter(self):
        require(not self.held, "observer channel held")
        if self.busy:
            self.held = True
            raise Hold("concurrent observer message")
        self.busy = True

    def save(self, direction, raw):
        require(type(raw) is bytes and 0 < len(raw) <= MAX_FRAME_BYTES
                and self.byte_count + len(raw) <= BYTE_LIMIT,
                "observer byte budget/type")
        self.byte_count += len(raw)
        self.record(direction, raw)  # A recorder failure blocks dispatch/acceptance.

    def check_binding(self, message, direction):
        require(message["direction"] == direction and message["attempt"] == self.attempt
                and message["binding"] == self.binding and message["producer"] == self.producer
                and message["role"] == self.role, "observer binding/direction mismatch")
        require(self.sequence < len(STAGES) and message["seq"] == self.sequence + 1
                and message["stage"] == STAGES[self.sequence]
                and message["nonce"] not in self.nonces, "observer sequence/stage/replay")


class ObserverClient(BoundMessages):
    def __init__(self, exchange, key, **binding):
        require(callable(exchange), "observer byte carrier required")
        super().__init__(key, **binding)
        self.exchange = exchange

    async def observe(self, stage, *, nonce=None):
        self.enter()
        try:
            require(self.sequence < len(STAGES) and stage == STAGES[self.sequence], "observer stage order")
            nonce = secrets.token_hex(32) if nonce is None else nonce
            require(hex64(nonce) and nonce not in self.nonces, "observer nonce reuse/type")
            started = self.now()
            message = {"v": 1, "direction": "request", "attempt": self.attempt,
                       "binding": self.binding, "producer": self.producer, "role": self.role,
                       "seq": self.sequence + 1, "stage": stage, "nonce": nonce,
                       "payload": {}, "sample_seconds": 0}
            raw = signed(self._key, message)
            self.save("request", raw)
            reply_raw = await asyncio.wait_for(self.exchange(raw), timeout=FRESHNESS_SECONDS)
            require(not self.held, "observer channel held during exchange")
            require(self.now() - started <= FRESHNESS_SECONDS, "observer round trip stale")
            self.save("response", reply_raw)
            reply = verified(self._key, reply_raw)
            self.check_binding(reply, "response")
            require(reply["nonce"] == nonce and reply["sample_seconds"] <= PRODUCER_SECONDS,
                    "observer response nonce/duration")
            self.sequence += 1
            self.nonces.add(nonce)
            return {"payload": deepcopy(reply["payload"]), "message_proof": {
                "evidence_class": EVIDENCE_CLASS, "message_mac_verified": True,
                "attempt": self.attempt, "binding_sha256": self.binding,
                "producer": self.producer, "role": self.role, "stage": stage,
                "sequence": self.sequence, "nonce": nonce,
                "round_trip_seconds": self.last_clock - started,
                "host_identity_proved": False, "encrypted_carrier_proved": False,
                "approval_authenticated": False, "raw_wire_capture": False}}
        except BaseException:
            self.held = True
            raise
        finally:
            self.busy = False


class ObserverResponder(BoundMessages):
    def __init__(self, provider, key, **binding):
        require(callable(provider), "observer provider required")
        super().__init__(key, **binding)
        self.provider = provider

    async def respond(self, raw):
        self.enter()
        try:
            self.save("request", raw)
            request = verified(self._key, raw)
            self.check_binding(request, "request")
            require(request["payload"] == {} and type(request["sample_seconds"]) is int
                    and request["sample_seconds"] == 0, "observer request payload")
            self.sequence += 1  # Consumed before collecting, even if provider fails.
            self.nonces.add(request["nonce"])
            started = self.now()
            payload = await asyncio.wait_for(self.provider(request["stage"], request["nonce"]),
                                             timeout=PRODUCER_SECONDS)
            require(not self.held, "observer responder held during collection")
            elapsed = self.now() - started
            require(elapsed <= PRODUCER_SECONDS and type(payload) is dict, "observer provider duration/shape")
            response = {**request, "direction": "response", "payload": payload, "sample_seconds": elapsed}
            reply = signed(self._key, response)
            self.save("response", reply)
            return reply
        except BaseException:
            self.held = True
            raise
        finally:
            self.busy = False


class SignedHostProvider:
    """Adapter for OfflineObservationJoin; retains the sampler's false scope flags."""

    ROLE = "host-memory"

    def __init__(self, client):
        require(isinstance(client, ObserverClient) and client.role == self.ROLE, "matching observer client required")
        self.client = client
        self._record_attached = False

    def attach_record(self, record):
        require(callable(record) and not self._record_attached and self.client.sequence == 0
                and not self.client.busy and not self.client.held, "fresh observer channel recorder required")
        previous = self.client.record
        def combined(direction, raw):
            previous(direction, raw)
            record(direction, raw)
        self.client.record = combined
        self._record_attached = True

    async def __call__(self, stage, binding, challenge):
        try:
            require(binding == self.client.binding, "observer provider binding mismatch")
            result = await self.client.observe(stage, nonce=challenge)
            payload = result["payload"]
            require("observer_message_proof" not in payload, "reserved observer proof field")
            return {**payload, "observer_message_proof": result["message_proof"]}
        except BaseException:
            self.client.held = True
            raise


class SignedRuntimeProvider(SignedHostProvider):
    """Stage-bound continuity data; MAC verification is not runtime observation."""

    ROLE = "runtime-continuity"


class SignedInventoryProvider(SignedHostProvider):
    """Stage-bound writers payload; matching data does not prove complete coverage."""

    ROLE = "writer-inventory"
