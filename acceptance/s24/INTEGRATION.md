# SPEC §24 — integration work package

Date: 25 October 2026.
Status: **WORK IN PROGRESS — operational Phase B HOLD**.
Base: main `f93b90f39eab9b70afa6c6259edf3de51a606f97` (PR #103 merge).
Plan: [Phase B adapter/control](../../docs/S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md).

This is the single integration work package for the remaining B implementation.
Keep follow-up integration changes on this PR; do not treat another isolated
helper or green CI as completion of the operational system. This first delta
implements and tests the offline coordinator. It is not an executable setup or
activation packet and is not ready to close the B integration work package.

## Executed offline path

`OfflineIntegration` validates the immutable candidate and the identity manifest,
requires observation providers and parent bindings, reserves one durable launch
claim, and opens one SDK stdio session against the existing synthetic fixture.
It checks the 27-tool discovery schemas and inherited stamp using the existing
identity validator, then runs the unchanged parent contract and fixture matrix.
The successful matrix performs 124 tool calls and 44 ordered checkpoints.
Identity/discovery/initialization and lifecycle activity are outside that count.

`OfflineObservationJoin` consumes the guest sampler's byte fields and the Windows
sampler's data shape, plus explicit continuity and writer inputs. It supplies the
stateful HOLD latch missing from the one-shot Windows sampler. It checks the
per-request challenge/digest, host sample duration/floor, guest types/limits,
continuity identity and exact writer list. The complete join must finish within
the existing two-second parent freshness bound; its parent timestamp starts
before collection. A challenge is correlation data, not authentication. No
Windows/guest clock equality is assumed.

The actual guest/Windows providers are not invoked by this test coordinator.
Tests fabricate both sides and label them as offline inputs, even when a test
object uses the producer's normal evidence-class string. The raw joined inputs
are retained separately in the private trace. Negative guest workspace growth
is retained there; zero is used as a conservative new-growth upper bound in the
parent's nonnegative resource contract. No reading, boolean or matching list
proves live continuity, host identity or complete writer coverage.

The SDK session context exits before stopped-state reads. The existing verifier
compares actual rows, registrations, counters and audit projection with the
matrix's saved expectations. This uses the reviewed offline fixture's one-child
writer model. Context exit is not a new proof of detached-writer cessation or a
substitute for the operational cohort supervisor. A failed/uncertain exit blocks
the verifier. No second fixture is started to inspect state.

Candidate content, fixture hashes and eight integrated source/manifest SHA-256
values are checked before/after. These hashes detect recorded byte drift; they
are not approval or authenticated source provenance. No candidate, manifest,
fixture, old validator, sampler or OwnedChild source is modified here.

## Evidence and failure behavior

The fixed-name trace and receipt use exclusive creation, private 0600 files,
short-write handling and file/directory fsync. Every parent request is synced
before dispatch. Encoded trace is limited to 8 MiB; receipt to 1 MiB. The trace
contains SDK-decoded results and synthesized validator/parent envelopes, not raw
MCP transport bytes. Request data, full decoded response fields, joined inputs
and lifecycle transitions remain distinguishable. Actual private artifacts must
not be copied into public review text.

Failure or cancellation consumes the instance and launch claim, latches HOLD,
exits the session context and preserves partial evidence. There is no retry,
reconnect, automatic stale-claim removal or new attempt. SDK/AnyIO exception
groups are preserved, including cleanup failures. If evidence writes/fsync/close
fail, the API fails and available partial files remain; a complete HOLD receipt
cannot be guaranteed on a failed storage device. A partial or otherwise present
receipt is not authority. No field grants operational readiness or acceptance.

The deadline starts before reservation and is not reset at SDK start. It is an
offline cooperative asyncio limit (at most 120 seconds), not the B activation
window or an interrupt for blocked I/O. SDK ownership is not integration of the
pidfd watchdog. Every receipt explicitly retains operational_b_ready=false,
scoped_gate_closed=false, complete_writer_cessation_proved=false,
outer_supervisor_integrated=false and raw_wire_capture=false.

## Validation

Run only in an authorized offline test environment:

```bash
python -W error::ResourceWarning -B acceptance/s24/test_integration.py --candidate .s24-candidate -v
```

Sixteen coordinator controls cover the actual SDK/identity/complete matrix/stop/read-only
verification chain; joined observations and latch; identity/continuity/resource/
challenge errors; cancellation; finite-window expiry; uncertain stop; actual
post-stop SQLite row tampering; integrated-source drift; exclusive evidence,
trace limits and storage failure. Negative fixture writes are private disposable
test mutations after SDK shutdown, never candidate or original state changes.
The positive case asserts 124/44, all phases, actual audit 30, private file modes,
trace hash/length and explicit incomplete operational fields.

## Shared-key observation message delta

`observer_channel.py` adds a concrete HMAC-SHA-256 request/response format with
version/domain separation, exact attempt/private-binding/producer/role/stage/
sequence binding, a fresh 256-bit nonce and constant-time MAC comparison. Both
directions are signed. The responder checks the signature before collecting;
the client checks it before accepting a sample. A valid MAC for another role,
attempt, stage or sequence is still rejected. Echoing or replaying an old signed
message is not a fresh response. Payload fields are retained, not repaired. MACs
use this module's fixed domain and sorted-key, ASCII, finite JSON encoding; a
different-language producer needs independent byte-parity tests before use.

Each endpoint requires a caller-supplied exact 32-byte key, byte carrier/provider,
and recorder. No key is generated, loaded from an operator file, logged or
provisioned by this module. Tests use deliberately public unit bytes only. Actual
key provisioning and private mapping to an independently verified producer/method
require separate setup scope. Different producer/role bindings require dedicated
key scope; no isolation from a shared key holder or trusted same-user code is
claimed. MAC verification proves possession of that key, not machine identity,
authentic approval, correct measurement, authorization or an encrypted carrier.

The existing 64 KiB parent frame decoder rejects duplicate keys/nonfinite data;
each endpoint also enforces an 8 MiB message budget and the 44-stage sequence.
The client measures a <=2-second round trip using its own monotonic clock; the
responder bounds collection to <=1 second using its clock. Clock origins need
not match. These are cooperative/post-hoc limits, not process interruption or
measured Work-route latency guarantees. The surrounding join still has its own
two-second total freshness bound; the message layer never extends it.

Failure, cancellation, concurrent use, recorder failure, wrong metadata or a
bad/replayed message latches that endpoint permanently; an in-flight result is
rejected if a concurrent call held the instance. There is no retry, fallback,
reconnect or durable resume. Replay/sequence state is process-local. Restarting
an endpoint is not recovery: the outer one-use attempt/control policy must stop
the attempt, preserve evidence and require a fresh approved binding rather than
reconstructing endpoints with old state/key/attempt. No listener or protected
network carrier is implemented here, and an invalid frame can deliberately hold
the endpoint. Availability and whole-cohort supervision remain separate.

`SignedHostProvider` connects this message client to the join with a stage-bound
host request. It preserves the original Windows sampler's authenticated=false,
host_identity_proved=false and other incomplete flags. A separate
`observer_message_proof.message_mac_verified=true` records only the verified MAC.
The producer cannot supply this reserved proof field itself. The coordinator
attaches its existing private journal before the first exchange; the old recorder
is retained, and both exact ASCII message frames are recorded at the codec
boundary. These frames are not a Work/MCP wire capture or proof of a protected
carrier. Receipts additionally retain actual_observer_carrier_proved=false and
observer_key_host_binding_proved=false.

Twenty channel controls cover all stages, deep payload preservation, wrong MAC/
key/context, reflection, replay, timing/clock failures, concurrency at each end,
actual cooperative timeouts, recorder/size/schema/type failures, and an actual
new disposable stdio peer completing all 44 exchanges. The full SDK integration
positive uses signed host inputs with fabricated measurements. A forged response
MAC test confirms channel + join + coordinator HOLD before the first matrix tool,
with no unsigned fallback. This delta does not invoke Windows or original runtimes.

```bash
python -W error::ResourceWarning -B acceptance/s24/test_observer_channel.py -v
```

## Remaining work on this same integration PR

| Gate | Current state / required closure |
| --- | --- |
| Actual Work handoff/namespace | HOLD; no bound fixture namespace or supported invocation instance has been proved; never fall back to this SDK path as live evidence |
| Inactive setup / first activation binding | HOLD; review exact client identity, private route/config/authentication and any staged binding before requesting separate operational scope |
| Host/guest/continuity collectors | HOLD; scoped shared-key messages join offline and reject replay; actual protected carrier, producer/key/method binding and original-runtime collection remain unimplemented/unproved |
| Outer supervisor / complete cohort | HOLD; OwnedChild is still a separate direct-leader primitive; owner loss, client/observer/descendant/external-writer coverage and stop targeting must be integrated |
| RPC and durable attempt evidence | Offline parent policy/journal tested; actual route mapping, raw-capture correlation and private operational attempt receipt remain HOLD |
| Stopped-writer proof | Offline SDK context exit only; operational complete writer cessation must precede the same read-only verification logic |

Keep the #100 adoption observation open. Do not add a delay/retry or weaken its
identity check to obtain a pass. Phase A readiness acceptance remains the actual
operator statement recorded in the separate unmerged #96; this PR does not merge
it or extend that acceptance. PR #80 remains a separate historical HOLD. There is
no VM/host/SSH action, new guest window, credential, profile/plugin setup,
activation, release or deployment authorization from this source work.
