"""Offline-only B runner/IPC contract. No connector, observer, spawn or signal API.

The injected exchange is test data, never route capability or operational authority.
The immutable fixture matrix remains the source of stimuli and expected row deltas.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import math
import time
from types import SimpleNamespace

import s24_fixture as fixture

MAX_FRAME_BYTES = 65536
MAX_TRACE_BYTES = 8 * 1024 * 1024
REPLY_TIMEOUT_SECONDS = 5
FRESHNESS_SECONDS = 2
MAX_WINDOW_SECONDS = 1200
ROUTE = "offline-fixture-contract"
EVIDENCE_CLASS = "offline-ipc-contract"
ARTIFACT_PIN = "e7be0cc4e84b820eb8c7ac541325672d0f892fb2"
TOOLS = frozenset(("bridge_status", "bridge_context_recent", "bridge_context_create",
                   "bridge_context_status", "hermes_submit_task", "codex_submit_task"))
STAGES = ("before-matrix",) + tuple(
    fixture.label(backend, case) + ":" + side
    for backend in fixture.BACKENDS for case in fixture.CASES for side in ("before", "after")
) + ("replay:before", "replay:after", "hermes:precheck-plain:before",
     "hermes:precheck-plain:after", "codex:precheck-plain:before",
     "codex:precheck-plain:after", "after-matrix")
IDENTITY_KEYS = frozenset(("candidate", "artifact", "cohort", "production", "dev"))
RESOURCE_KEYS = frozenset(("host_available_mib", "guest_available_mib", "rss_mib",
                           "disk_free_mib", "workspace_growth_mib", "logs_mib"))


class Hold(RuntimeError):
    """Stop this contract instance permanently; no recovery/retry token is issued."""


def require(value, message):
    if not value:
        raise Hold(message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def encode(value):
    try:
        raw = json.dumps(value, ensure_ascii=True, allow_nan=False,
                         separators=(",", ":")).encode("utf-8") + b"\n"
    except (TypeError, ValueError, RecursionError) as error:
        raise Hold("non-JSON frame") from error
    require(len(raw) <= MAX_FRAME_BYTES, "oversized frame")
    return raw


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_FRAME_BYTES, "invalid frame size/type")
    require(raw.endswith(b"\n") and b"\n" not in raw[:-1], "one newline frame required")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(Hold("nonfinite JSON")))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise Hold("malformed JSON frame") from error
    require(type(value) is dict, "frame must be object")
    return value


class OfflineParentContract:
    """One-use, serial test contract with an injected bytes-to-bytes exchange.

    No CLI or live mode is provided. Times use one injected monotonic clock domain;
    this cannot authenticate observations or establish cross-machine clock parity.
    On any uncertain response, cancellation or timeout, the instance is latched HOLD.
    This class cannot stop a guest/client process: that remains a separate B source gate.
    """

    def __init__(self, exchange, identities, writers, *, clock=time.monotonic, window_seconds=1200):
        require(callable(exchange) and callable(clock), "exchange and clock required")
        require(type(identities) is dict and set(identities) == IDENTITY_KEYS,
                "complete identity binding required")
        require(all(type(v) is str and 0 < len(v) <= 256 for v in identities.values()),
                "invalid identity binding")
        require(identities["candidate"] == fixture.PIN, "wrong candidate binding")
        require(identities["artifact"] == ARTIFACT_PIN, "wrong artifact binding")
        require(type(writers) is list and writers and all(type(w) is str and w for w in writers)
                and len(set(writers)) == len(writers), "prebound writers required")
        require(number(window_seconds) and 0 < window_seconds <= MAX_WINDOW_SECONDS,
                "invalid finite window")
        self.exchange, self.clock = exchange, clock
        self.identities = deepcopy(identities)
        self.writers = deepcopy(writers)
        self.started = clock()
        require(number(self.started), "invalid clock")
        self.last_clock = self.started
        self.deadline = self.started + window_seconds
        self.sequence = self.trace_bytes = self.stage_index = 0
        self.trace = []
        self.contexts = {}
        self.last_observation = None
        self.held = self.busy = self.used = self.finished = False

    def now(self):
        current = self.clock()
        require(number(current) and current >= self.last_clock, "clock moved backwards")
        self.last_clock = current
        require(current < self.deadline, "window expired")
        return current

    def guard(self):
        require(not self.held and not self.finished, "contract closed")
        current = self.now()
        if self.last_observation is not None:
            require(0 <= current - self.last_observation <= FRESHNESS_SECONDS,
                    "observation stale")
        return current

    def args_allowed(self, name, args):
        require(name in TOOLS and type(args) is dict, "tool/arguments not allowed")
        stage = STAGES[self.stage_index - 1]
        require(stage == "before-matrix" or stage.endswith(":before"), "no stimulus after boundary")
        active_label = stage[:-len(":before")] if stage.startswith("S24_") else None
        if name == "bridge_status":
            require(args == {}, "status arguments")
        elif name == "bridge_context_recent":
            require(set(args) == {"limit"} and type(args["limit"]) is int
                    and args["limit"] == 100, "recent arguments")
        elif name == "bridge_context_create":
            require(set(args) == {"label"} and active_label is not None
                    and args["label"] == active_label,
                "create arguments")
            require(args["label"] not in self.contexts.values(), "duplicate context label")
        elif name == "bridge_context_status":
            require(set(args) == {"context_id"} and type(args["context_id"]) is str
                    and args["context_id"] in self.contexts, "unowned context")
            require(self.contexts[args["context_id"]] == ("S24_HERMES_OP_PRE"
                    if stage == "replay:before" else active_label), "wrong case context status")
        else:
            backend = name.split("_", 1)[0]
            keys = {"prompt", "request_id"} if backend == "hermes" else {
                "prompt", "workspace", "mode"}
            if "context_id" in args:
                keys.add("context_id")
                require(type(args["context_id"]) is str and args["context_id"] in self.contexts,
                        "unowned submit context")
                label = self.contexts[args["context_id"]]
                require(label.startswith("S24_" + backend.upper() + "_"), "backend context mismatch")
                case = label[len("S24_" + backend.upper() + "_"):]
            else:
                case = "plain"
            require(set(args) == keys and args["prompt"] == "S24_SYNTHETIC", "submit arguments")
            permitted = (active_label if active_label is not None else
                         "S24_HERMES_OP_PRE" if stage == "replay:before" else
                         fixture.label(backend, "CLOSED")
                         if stage == backend + ":precheck-plain:before" else None)
            require(permitted is not None and ((case == "plain" and
                    stage == backend + ":precheck-plain:before") or
                    self.contexts.get(args.get("context_id")) == permitted), "wrong case submit")
            if backend == "hermes":
                require(args["request_id"] == "s24-hermes-" + case, "request identity")
            else:
                require(args["workspace"] == "fixture-workspace" and args["mode"] == (
                    "read-only" if case == "plain" else "workspace-write"), "stub workspace/mode")

    async def request(self, kind, payload):
        if self.busy:
            self.held = True
            raise Hold("concurrent request")
        self.busy = True
        try:
            current = self.guard()
            self.sequence += 1
            frame = encode({"seq": self.sequence, "route": ROUTE, "kind": kind, "payload": payload})
            require(self.trace_bytes + len(frame) <= MAX_TRACE_BYTES, "trace budget")
            self.trace_bytes += len(frame)
            self.trace.append(frame)
            raw = await asyncio.wait_for(self.exchange(frame),
                timeout=min(REPLY_TIMEOUT_SECONDS, self.deadline - current))
            self.guard()
            require(type(raw) is bytes and self.trace_bytes + len(raw) <= MAX_TRACE_BYTES,
                    "reply trace budget/type")
            self.trace_bytes += len(raw)
            self.trace.append(raw)
            reply = decode(raw)
            require(set(reply) == {"seq", "route", "kind", "payload"}, "reply envelope")
            require(type(reply["seq"]) is int and reply["seq"] == self.sequence
                    and reply["route"] == ROUTE and reply["kind"] == kind, "reply binding/order")
            return reply["payload"]
        except BaseException:
            self.held = True
            raise
        finally:
            self.busy = False

    def observation(self, value, stage):
        require(type(value) is dict and set(value) == {
            "stage", "observed_at", "identities", "resources", "writers"}, "observation shape")
        require(value["stage"] == stage and value["identities"] == self.identities,
                "observation identity/stage")
        observed = value["observed_at"]
        require(number(observed) and self.started <= observed <= self.now()
                and self.last_clock - observed <= FRESHNESS_SECONDS, "observation age")
        if self.last_observation is not None:
            require(observed > self.last_observation, "reused observation")
        resources = value["resources"]
        require(type(resources) is dict and set(resources) == RESOURCE_KEYS
                and all(number(v) for v in resources.values()), "resource sample shape")
        require(resources["host_available_mib"] >= 1536
                and resources["guest_available_mib"] >= 768 and resources["rss_mib"] <= 768
                and resources["disk_free_mib"] >= 2048
                and resources["workspace_growth_mib"] <= 2048
                and resources["logs_mib"] <= 128, "resource threshold")
        writers = value["writers"]
        require(type(writers) is dict and set(writers) == {"expected", "observed"}
                and type(writers["expected"]) is list and writers["expected"]
                and all(type(w) is str and w for w in writers["expected"])
                and len(set(writers["expected"])) == len(writers["expected"])
                and writers["expected"] == writers["observed"] == self.writers,
                "writer inventory mismatch")
        self.last_observation = observed

    async def checkpoint(self, stage):
        try:
            require(self.stage_index < len(STAGES) and stage == STAGES[self.stage_index],
                    "checkpoint order")
            value = await self.request("checkpoint", {"stage": stage})
            self.observation(value, stage)
            self.stage_index += 1
            return True
        except BaseException:
            self.held = True
            raise

    async def call(self, name, args):
        try:
            require(0 < self.stage_index < len(STAGES), "call outside matrix checkpoints")
            self.args_allowed(name, args)
            result = await self.request("tool", {"name": name, "arguments": args})
            require(type(result) is dict and type(result.get("isError")) is bool
                    and type(result.get("content")) is list
                    and (result.get("structuredContent") is None
                         or type(result["structuredContent"]) is dict), "tool result shape")
            if name == "bridge_context_create" and not result["isError"]:
                out = result.get("structuredContent")
                require(type(out) is dict and type(out.get("context_id")) is str
                        and 0 < len(out["context_id"]) <= 128
                        and out["context_id"] not in self.contexts, "invalid new context identity")
                self.contexts[out["context_id"]] = args["label"]
            # Preserve all nested ACK/content/metadata fields from the decoded frame.
            return SimpleNamespace(**result)
        except BaseException:
            self.held = True
            raise

    async def run(self):
        try:
            require(not self.used, "one use only")
            self.used = True
            result = await fixture.matrix(self.call, "driver-observations", self.checkpoint)
            require(self.stage_index == len(STAGES), "incomplete checkpoints")
            self.guard()
            self.finished = True
            result["evidence_class"] = EVIDENCE_CLASS
            return {"matrix": result, "checkpoints": self.stage_index,
                    "frames": self.sequence * 2, "trace_bytes": self.trace_bytes,
                    "evidence_class": EVIDENCE_CLASS}
        except BaseException:
            self.held = True
            raise
