"""Offline integration coordinator. No Work mode, route fallback or B authority.

The executable SDK path is exclusively offline synthetic evidence. Operational
integration remains HOLD until the same PR has reviewed route/collector/cohort
implementations and a separately approved activation scope.
"""
import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import secrets
import sys
import time

from identity_contract import OfflineIdentityContract
from launch_admission import LaunchAdmission
from observer_channel import SignedHostProvider, SignedRuntimeProvider, SignedInventoryProvider
from supervised_stdio import SupervisedSdkFactory
from supervised_stdio import identity as process_identity
from parent_contract import ARTIFACT_PIN, FRESHNESS_SECONDS, STAGES, Hold, OfflineParentContract, decode, encode, require
import s24_fixture as fixture

EVIDENCE_CLASS = "offline-sdk-integration"
TRACE_LIMIT = 8 * 1024 * 1024
RECEIPT_LIMIT = 1024 * 1024
MIB = 1024 * 1024
LEADER_CLASS = "local-known-fixture-leaders"
LEADER_NAMES = ["owned-controller", "owned-supervisor", "owned-fixture-leader"]


class OwnedLeaderInventory:
    """Read only three known live leaders; never claim all writers or cessation.

    The first checkpoint binds the already initialized factory's private ready
    data. There is no caller-supplied PID list, global process scan or stop API.
    """
    def __init__(self, factory):
        require(type(factory) is SupervisedSdkFactory, "owned fixture factory required")
        self.factory = factory
        self.bound = None
        self.sequence = 0
        self.nonces = set()
        self.held = False

    @staticmethod
    def _read(expected, parent):
        pid = expected["pid"]
        first = process_identity(pid)
        # /proc stat's state is field0 after ')'; ppid is field1.
        parts = (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()
        require(first == expected and int(parts[19]) == expected["start_ticks"]
                and (parent is None or int(parts[1]) == parent)
                and process_identity(pid) == first, "known leader identity/parent changed")
        return {"identity": first, "parent_pid": int(parts[1])}

    async def __call__(self, stage, nonce):
        try:
            require(not self.held and self.sequence < len(STAGES)
                    and stage == STAGES[self.sequence], "known leader observation held/order")
            require(type(nonce) is str and len(nonce) == 64 and all(c in "0123456789abcdef" for c in nonce)
                    and nonce not in self.nonces, "known leader nonce")
            self.sequence += 1
            self.nonces.add(nonce)  # Consumed before reads; no retry after failure.
            ready = self.factory.ready
            require(self.factory.used and not self.factory.held and type(ready) is dict
                    and self.factory.stop_receipt is None, "live bound supervisor required")
            require(ready["owner"]["pid"] == os.getpid(), "inventory controller mismatch")
            if self.bound is None:
                self.bound = deepcopy(ready)
            require(ready == self.bound, "supervisor ready binding changed")
            owner, supervisor, raw_child = ready["owner"], ready["supervisor"], ready["child"]
            child = {"pid": raw_child["pid"], "start_ticks": raw_child["start_ticks"],
                     "uid": raw_child["owner_uid"], "exe": raw_child["executable"], "argv": raw_child["argv"]}
            expected = (owner, supervisor, child)
            require(all(type(item["pid"]) is int and item["pid"] > 1 and item["uid"] == os.geteuid()
                        for item in expected) and len({item["pid"] for item in expected}) == 3,
                    "three distinct owned leaders required")
            started = time.monotonic()
            observed = [self._read(item, parent) for item, parent in
                        zip(expected, (None, owner["pid"], supervisor["pid"]))]
            elapsed = time.monotonic() - started
            require(0 <= elapsed <= 1, "known leader sample stale")
            return {"writers": LEADER_NAMES[:], "leader_observation": {
                "evidence_class": LEADER_CLASS, "stage": stage, "nonce": nonce,
                "sequence": self.sequence, "elapsed_seconds": elapsed,
                "leaders": observed, "complete_writer_coverage": False,
                "descendant_cessation_proved": False, "original_runtimes_observed": False}}
        except BaseException:
            self.held = True
            raise


def source_identity():
    root = Path(__file__).resolve().parent
    names = ("integration.py", "parent_contract.py", "identity_contract.py", "launch_admission.py",
             "s24_fixture.py", "candidate_manifest.json", "discovery_manifest.json", "observer_channel.py",
             "supervised_stdio.py", "owned_child.py")
    result = {}
    for name in names:
        path = root / name
        require(not path.is_symlink(), "integration source symlink")
        with path.open("rb") as stream:
            raw = stream.read(65537)
        require(len(raw) <= 65536, "integration source byte limit")
        result[name] = hashlib.sha256(raw).hexdigest()
    return result


class OfflineObservationJoin:
    """Join guest sampler + Windows sampler data + continuity/writer inputs.

    All inputs remain offline/local producer data, not authenticated collectors.
    This latch is deliberately separate from HostMemory's stateless sampler.
    The caller owns the transport; this class opens no network or host session.
    """

    def __init__(self, guest, host, continuity, inventory, identities, writers, binding_sha256):
        require(callable(getattr(guest, "sample", None)) and all(callable(p) for p in
                (host, continuity, inventory)), "all offline observers required")
        require(type(binding_sha256) is str and len(binding_sha256) == 64
                and all(c in "0123456789abcdef" for c in binding_sha256), "observer binding digest")
        self.guest, self.host, self.continuity, self.inventory = guest, host, continuity, inventory
        self.identities, self.writers = deepcopy(identities), writers[:]
        self.binding = binding_sha256
        self.signed_checkpoints = isinstance(continuity, SignedRuntimeProvider) or isinstance(inventory, SignedInventoryProvider)
        if self.signed_checkpoints:
            require(type(host) is SignedHostProvider and type(continuity) is SignedRuntimeProvider
                    and type(inventory) is SignedInventoryProvider, "complete signed checkpoint providers required")
            clients = [provider.client for provider in (host, continuity, inventory)]
            require(all(client.binding == self.binding and client.attempt == clients[0].attempt for client in clients)
                    and len({client.producer for client in clients}) == 3
                    and len({client._key for client in clients}) == 3,
                    "distinct role keys/producers and common attempt binding required")
        self.held = self.busy = False
        self.last_inputs = None

    async def __call__(self, stage):
        require(not self.held, "observation join held")
        if self.busy:
            self.held = True
            raise Hold("concurrent observation join")
        self.busy = True
        try:
            started = time.monotonic()
            challenge = secrets.token_hex(32)  # Correlation, not a credential or approval.
            guest = self.guest.sample()
            host = await self.host(stage, self.binding, challenge)
            proofs = {}
            leader_observation = None
            if self.signed_checkpoints:
                continuity_raw = await self.continuity(stage, self.binding, challenge)
                inventory_raw = await self.inventory(stage, self.binding, challenge)
                require(set(continuity_raw) == {"production", "dev", "healthy", "observer_message_proof"}
                        and set(inventory_raw) in ({"writers", "observer_message_proof"},
                            {"writers", "leader_observation", "observer_message_proof"}),
                        "signed checkpoint payload shape")
                proofs = {"runtime-continuity": continuity_raw["observer_message_proof"],
                          "writer-inventory": inventory_raw["observer_message_proof"]}
                continuity = {key: value for key, value in continuity_raw.items() if key != "observer_message_proof"}
                writers = inventory_raw["writers"]
                if "leader_observation" in inventory_raw:
                    leader_observation = inventory_raw["leader_observation"]
                    require(type(leader_observation) is dict
                            and leader_observation.get("evidence_class") == LEADER_CLASS
                            and leader_observation.get("complete_writer_coverage") is False
                            and leader_observation.get("descendant_cessation_proved") is False
                            and leader_observation.get("original_runtimes_observed") is False
                            and leader_observation.get("stage") == stage and leader_observation.get("nonce") == challenge
                            and type(leader_observation.get("elapsed_seconds")) in (int, float)
                            and math.isfinite(leader_observation["elapsed_seconds"])
                            and 0 <= leader_observation["elapsed_seconds"] <= 1
                            and type(leader_observation.get("sequence")) is int
                            and leader_observation["sequence"] == inventory_raw["observer_message_proof"]["sequence"]
                            and type(leader_observation.get("leaders")) is list
                            and len(leader_observation["leaders"]) == 3 and writers == LEADER_NAMES,
                            "known leader observation scope/binding")
            else:
                # Legacy injected offline tests only; never a fallback after a signed failure.
                continuity = await self.continuity()
                writers = await self.inventory()
            require(type(host) is dict and host.get("binding_sha256") == self.binding
                    and host.get("challenge") == challenge, "host correlation mismatch")
            require(host.get("evidence_class") == "local-read-only-windows-host-memory"
                    and host.get("full_checkpoint_pass") is False
                    and host.get("authenticated") is False
                    and host.get("host_identity_proved") is False,
                    "host sampler input scope mismatch")
            elapsed = host.get("elapsed_seconds")
            require(type(elapsed) in (int, float) and math.isfinite(elapsed)
                    and 0 <= elapsed <= 1, "host sample duration")
            require(type(host.get("host_available_bytes")) is int
                    and host["host_available_bytes"] >= 1536 * MIB, "host threshold")
            require(type(guest) is dict and guest.get("full_checkpoint_pass") is False
                    and guest.get("host_observed") is False
                    and guest.get("complete_writer_coverage") is False
                    and guest.get("guest_limit_failures") == [], "guest sampler input scope/limits")
            keys = ("guest_available_bytes", "account_rss_sampled_bytes", "disk_available_bytes",
                    "workspace_growth_bytes", "logs_logical_bytes")
            require(all(type(guest.get(k)) is int for k in keys), "guest byte counter types")
            require(type(continuity) is dict and set(continuity) == {"production", "dev", "healthy"}
                    and continuity["production"] == self.identities["production"]
                    and continuity["dev"] == self.identities["dev"]
                    and continuity["healthy"] is True, "offline continuity input changed")
            require(type(writers) is list and writers == self.writers, "offline writer input changed")
            require(time.monotonic() - started <= FRESHNESS_SECONDS, "joined observation stale")
            self.last_inputs = deepcopy({"stage": stage, "guest": guest, "host": host,
                                         "continuity": continuity, "writers": writers,
                                         "checkpoint_message_proofs": proofs,
                                         "leader_observation": leader_observation,
                                         "evidence_class": "offline-inputs-with-local-leaders" if leader_observation
                                         else "injected-offline-observer-inputs"})
            return {"stage": stage, "observed_at": started, "identities": deepcopy(self.identities),
                    "resources": {"host_available_mib": host["host_available_bytes"] / MIB,
                                  "guest_available_mib": guest["guest_available_bytes"] / MIB,
                                  "rss_mib": guest["account_rss_sampled_bytes"] / MIB,
                                  "disk_free_mib": guest["disk_available_bytes"] / MIB,
                                  "workspace_growth_mib": max(0, guest["workspace_growth_bytes"]) / MIB,
                                  "logs_mib": guest["logs_logical_bytes"] / MIB},
                    "writers": {"expected": self.writers[:], "observed": writers[:]}}
        except BaseException:
            self.held = True
            raise
        finally:
            self.busy = False

    def attach_journal(self, journal):
        for provider in (self.host, self.continuity, self.inventory):
            if isinstance(provider, SignedHostProvider):
                role = provider.client.role
                def record(direction, raw, role=role):
                    # Keep the original host event names for existing evidence readers.
                    kind = "observer-message-" if role == "host-memory" else role + "-message-"
                    journal.record(kind + direction, {"frame_ascii": raw.decode("ascii")})
                provider.attach_record(record)


class PrivateJournal:
    """Exclusive bounded private trace, with both file and directory sync barriers."""

    def __init__(self, root):
        self.root = Path(root).absolute()
        require(self.root == self.root.resolve(strict=True), "canonical evidence root")
        self.root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.fd = None
        self.count = 0
        self.receipt_attempted = False
        self.hasher = hashlib.sha256()
        try:
            info = os.fstat(self.root_fd)
            require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700,
                    "private evidence root required")
            self.identity = (info.st_dev, info.st_ino)
            self.fd = self._create("integration-trace.jsonl")
        except BaseException:
            if self.fd is not None:
                os.close(self.fd)
            os.close(self.root_fd)
            raise

    def _create(self, name):
        fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                     0o600, dir_fd=self.root_fd)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
                    and info.st_uid == os.geteuid() and info.st_nlink == 1,
                    "private evidence file required")
            os.fsync(self.root_fd)
            return fd
        except BaseException:
            os.close(fd)
            raise

    @staticmethod
    def _write(fd, raw):
        remaining = memoryview(raw)
        while remaining:
            count = os.write(fd, remaining)
            require(count > 0, "evidence write failed")
            remaining = remaining[count:]

    def record(self, kind, value):
        require(self.fd is not None, "journal closed")
        raw = (json.dumps({"kind": kind, "value": value}, sort_keys=True,
                          ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n").encode()
        require(self.count + len(raw) <= TRACE_LIMIT, "integration trace limit")
        self._write(self.fd, raw)
        self.count += len(raw)
        self.hasher.update(raw)
        os.fsync(self.fd)  # Preserve each request before dispatch, not just on success.

    def receipt(self, value):
        require(self.fd is not None, "journal closed")
        require(not self.receipt_attempted, "receipt already attempted; no retry")
        self.receipt_attempted = True
        info = self.root.stat()
        require((info.st_dev, info.st_ino) == self.identity and not self.root.is_symlink()
                and stat.S_IMODE(info.st_mode) == 0o700, "evidence root changed")
        raw = (json.dumps(value, sort_keys=True, ensure_ascii=True,
                          allow_nan=False, separators=(",", ":")) + "\n").encode()
        require(len(raw) <= RECEIPT_LIMIT, "receipt byte limit")
        fd = self._create("integration-receipt.json")
        try:
            self._write(fd, raw)
            os.fsync(fd)
            os.fsync(self.root_fd)
        finally:
            os.close(fd)

    def close(self):
        if self.fd is not None:
            try:
                os.fsync(self.fd)
            finally:
                os.close(self.fd)
                os.close(self.root_fd)
                self.fd = None


def decoded(value):
    """SDK-decoded data only. Never fabricate a raw transport-capture claim."""
    return value.model_dump(mode="json", by_alias=True, exclude_none=True)


@asynccontextmanager
async def sdk_session(argv):
    """One actual offline SDK child, with its own context-managed shutdown."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=argv[0], args=argv[1:],
                                  env={"PYTHONDONTWRITEBYTECODE": "1"})
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            yield session


class OfflineIntegration:
    """One-use SDK/identity/matrix/admission/journal/stop/verifier integration.

    Observation callables are mandatory labeled offline inputs. They do not
    authenticate the host or prove complete writer coverage. Any failure latches
    this coordinator before cleanup; the session context is exited before any
    stopped-state read. No operational Work route can be selected here.
    """

    def __init__(self, candidate, root, observation, identities, writers, *, source_kind,
                 window=120, session_factory=sdk_session):
        require(callable(observation) and callable(session_factory), "offline providers required")
        require(type(window) in (int, float) and 0 < window <= 120, "offline window at most 120s")
        self.candidate = fixture.verify_candidate(candidate)
        self.root = Path(root).absolute()
        require(self.root == self.root.resolve(strict=True), "canonical attempt root")
        require(not (self.root / "state").exists(), "fresh fixture state required")
        self.identity_contract = OfflineIdentityContract(source_kind)
        self.observation = observation
        self.identities, self.writers = deepcopy(identities), deepcopy(writers)
        self.window, self.factory = window, session_factory
        self.used = self.held = False
        self.phase = "PREPARED"
        self.phases = [self.phase]
        self.journal = None
        self.matrix = None
        self.tool_calls = self.checkpoints = 0
        self.session_exited = False

    def _phase(self, phase):
        self.phase = phase
        self.phases.append(phase)
        self.journal.record("phase", phase)

    async def _identity(self, session):
        result = None
        while result is None:
            raw = self.identity_contract.request()
            req = decode(raw)
            self.journal.record("identity-request-data", req)
            if req["method"] == "tools/call":
                data = decoded(await session.call_tool("bridge_version", {}))
            else:
                data = decoded(await session.list_tools(cursor=req["params"].get("cursor")))
            # The envelope belongs to the offline validator, not the SDK wire.
            reply = {"jsonrpc": "2.0", "id": req["id"], "result": data}
            self.journal.record("identity-reply-data", reply)
            result = self.identity_contract.accept(encode(reply))
        return result

    async def _exchange(self, session, raw):
        request = decode(raw)
        self.journal.record("parent-request-data", request)
        if request["kind"] == "checkpoint":
            data = await self.observation(request["payload"]["stage"])
            if isinstance(self.observation, OfflineObservationJoin):
                self.journal.record("offline-observer-inputs", self.observation.last_inputs)
            self.checkpoints += 1
        else:
            payload = request["payload"]
            self.tool_calls += 1
            data = decoded(await session.call_tool(payload["name"], payload["arguments"]))
        response = {**request, "payload": data}
        self.journal.record("parent-reply-data", response)
        return encode(response)

    async def run(self):
        require(not self.used, "one use only")
        self.used = True
        try:
            return await self._run()
        except BaseException:
            self.held = True
            raise

    async def _run(self):
        deadline = asyncio.get_running_loop().time() + self.window
        if isinstance(self.factory, SupervisedSdkFactory):
            require(self.factory.root == self.root, "supervisor attempt root mismatch")
            self.factory.prepare(deadline)
        before = fixture.artifact_identity()
        sources = source_identity()
        argv = [sys.executable, "-B", str(Path(fixture.__file__).resolve()), "serve",
                "--candidate", str(self.candidate), "--state", str(self.root / "state")]
        # Validate all parent input bindings before reservation or child launch.
        contract = OfflineParentContract(lambda raw: self._exchange(self.session, raw),
                                         self.identities, self.writers, window_seconds=self.window)
        claim = LaunchAdmission(self.root, attempt_id="offline-integration",
                                binding_sha256=fixture.digest({"identities": self.identities,
                                                               "writers": self.writers}),
                                candidate_commit=fixture.PIN, fixture_commit=ARTIFACT_PIN,
                                argv=argv, window=self.window)
        self.journal = PrivateJournal(self.root)
        stopped = False
        try:
            self._phase("RESERVED")
            if isinstance(self.observation, OfflineObservationJoin):
                self.observation.attach_journal(self.journal)
            manager = claim.dispatch_once(self.factory)
            try:
                async with asyncio.timeout_at(deadline):
                    async with manager as session:
                        self.session = session
                        self._phase("IDENTITY")
                        identity = await self._identity(session)
                        self._phase("MATRIX")
                        self.matrix = await contract.run()
                        self._phase("STOPPING")
                self.session_exited = True
                stopped = True
            except BaseException:
                self.held = True
                # If __aexit__ itself failed, cessation is not inferred.
                raise
            self._phase("VERIFYING_OFFLINE_STATE")
            fixture.verify_candidate(self.candidate)
            require(fixture.artifact_identity() == before, "fixture source drift")
            require(source_identity() == sources, "integrated source drift")
            durable = fixture.inspect_stopped_state(self.root / "state", self.matrix["matrix"])
            require(self.tool_calls == 124 and self.checkpoints == 44, "integration inventory mismatch")
            self._phase("OFFLINE_CHECKED")
            receipt = self._receipt("OFFLINE_INTEGRATION_CHECKED", stopped)
            receipt.update(identity=identity, matrix=self.matrix, durable=durable, source_sha256=sources)
            if isinstance(self.factory, SupervisedSdkFactory):
                receipt["direct_fixture_supervisor"] = self.factory.stop_receipt
            self.journal.receipt(receipt)
            return receipt
        except BaseException:
            self.held = True
            self.phase = "HOLD"
            self.phases.append("HOLD")
            self.journal.record("phase", "HOLD")
            if not self.journal.receipt_attempted:
                self.journal.receipt(self._receipt("HOLD", stopped))
            raise
        finally:
            self.journal.close()

    def _receipt(self, status, stopped):
        return {"status": status, "evidence_class": EVIDENCE_CLASS,
                "candidate": fixture.PIN, "artifact": ARTIFACT_PIN,
                "phases": self.phases[:], "matrix_tool_calls": self.tool_calls,
                "checkpoints": self.checkpoints, "sdk_context_exited_normally": stopped,
                "trace_sha256": self.journal.hasher.hexdigest(), "trace_bytes": self.journal.count,
                "observations": "injected offline inputs; not authenticated live collectors",
                "raw_wire_capture": False, "complete_writer_cessation_proved": False,
                "operational_b_ready": False, "scoped_gate_closed": False,
                "outer_supervisor_integrated": False, "actual_observer_carrier_proved": False,
                "observer_key_host_binding_proved": False,
                "direct_fixture_supervisor_used": isinstance(self.factory, SupervisedSdkFactory)}
