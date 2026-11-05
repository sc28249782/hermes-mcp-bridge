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

Candidate content, fixture hashes and ten integrated source/manifest SHA-256
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

Seventeen coordinator controls cover the actual SDK/identity/complete matrix/stop/read-only
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

## Independent direct-fixture supervisor delta

`SupervisedSdkFactory` is an optional offline factory for the same coordinator.
It launches a separate supervisor process; that process alone launches/adopts
the fixed synthetic fixture child through the unchanged `OwnedChild` primitive.
No arbitrary executable/command or supplied PID can be launched or signaled.
The complete SDK identity/matrix path is forwarded through this process, without
a Work mode, alternate backend or unsigned observation fallback.

Before fixture state exists, the new child arms Linux parent-death SIGTERM and
checks its expected parent on both sides of that syscall. It emits a bounded
startup frame, then waits for a one-byte handoff. The supervisor compares that
frame with live procfs identity and performs all original OwnedChild checks
before handoff. This is an explicit ready-code barrier, not an adoption retry,
sleep, weakened identity predicate or retrospective diagnosis of #100's issue.
The candidate itself still runs unchanged; the prelude is supervisor IPC, not
an MCP tool, notification or new candidate contract. No exec, credential change
or new fork occurs in the reviewed child path after arming.

The supervisor holds a pidfd for its rechecked direct controller, watches EOF,
an absolute deadline passed before reservation, the fixture lease and termination
signals. Renew/stop IPC uses a fresh private 0600 Unix socket under the 0700
attempt root, Linux SO_PEERCRED and the exact controller PID/start/uid/exe/argv.
A same-uid different process cannot renew. Sequence/type/size/time limits apply;
bad control input ends at HOLD rather than reauthentication or retry. The socket
and records are retained after stop; occupied paths cannot be reused. This is
local process binding, not encryption or authentication of the actual Work route.

Each SDK tool/list call renews the finite lease before dispatch. There is no idle
heartbeat that would keep a stalled caller alive forever. Factory shutdown sends
an explicit stop and waits for a synced receipt before allowing SDK context exit,
so SDK cleanup is not used as a premature kill of a still-stopping supervisor.
Normal stop uses OwnedChild's pidfd identity recheck, TERM and bounded grace;
KILL remains off by default and only an explicit test/scope may enable it.
Unit tests shorten grace for their new disposable fixtures only. The offline
deadline is <=120 seconds, lease <=5, default TERM grace 10; no B budget is changed.

If the supervisor is killed, the armed child's kernel parent-death TERM is a
direct-leader fallback only. It does not propagate to forked descendants, can be
cleared by credential changes, depends on the creating parent thread, and does
not prove a process actually exited. A child that ignores TERM or is blocked may
remain unconfirmed. No successful final receipt is invented after that crash.
Startup/adoption errors close the owned pre-handoff input pipe and retain unknown
cleanup; there is no fallback numeric-PID signal or process-group kill.

New private evidence separates startup/owner/child identities, actual pipe chunks
(including the non-MCP handoff byte) and the stop outcome. This is not end-to-end
Work/MCP capture correlation. The coordinator verifies the real offline durable
state only after a confirmed normal supervisor stop. Receipts may report
direct_fixture_supervisor_used=true, while outer_supervisor_integrated=false,
complete_writer_cessation_proved=false and operational_b_ready=false remain:
client/observer/descendant/external-writer coverage is still unproved.

Twelve additional controls cover the coarse RPC gate, exclusive private records,
parent-arm races, invalid/occupied startup, actual supervised SDK identity/stop,
controller death, idle lease/window expiry, supervisor kill and same-uid wrong
controller rejection. Kernel exit observations use retained pidfds, not PID
absence/age. The coordinator also adds a full supervised 124/44 case. Development
procfs/PID mismatch remains failed/unsupported evidence, not a reason for a skip
or fallback; coherent Linux CI must pass every positive case at the exact head.

```bash
python -W error::ResourceWarning -B acceptance/s24/test_supervised_stdio.py --candidate .s24-candidate -v
```

Linux interface references (general semantics, not proof about the operator's host):
- [PR_SET_PDEATHSIG](https://man7.org/linux/man-pages/man2/PR_SET_PDEATHSIG.2const.html)
- [Unix sockets / SO_PEERCRED](https://man7.org/linux/man-pages/man7/unix.7.html)

## Offline RPC frame correlation delta

`RpcCapture` records accepted controller/fixture ingress frames in a separate
exclusive 0600 `supervisor-rpc.jsonl` under the private attempt root. It retains
exact newline frame bytes as base64, frame SHA-256, direction and sequence. Each
record is synced before forwarding is attempted. Its encoded trace has a separate
8 MiB cap; the cap includes base64/JSON expansion. The startup handoff is not an
RPC frame and stays in the previous pipe evidence only. Invalid frames rejected
before recording are not represented as captured accepted frames.

Responses must match a pending request with the exact integer/string ID type.
Unknown/duplicate IDs, malformed result/error envelopes, server-initiated messages,
nonfinite/duplicate-key JSON and initialization-order violations cause HOLD.
Out-of-order replies for distinct pending IDs are allowed. A protocol error reply
is retained without changing its data; an initialize error cannot enable later
requests. The gate is deliberately limited to this fixture protocol; it is not a
policy for an actual Work client. The parent still enforces case arguments/order.

A record means this proxy observed a frame, not that forwarding, SDK delivery or
fixture consumption succeeded. OwnedChild's separate stdin_written evidence still
means only pipe acceptance. The new trace digest/size and request/response counts
are included in the direct-leader stop receipt. A normal controller-stop receipt
requires successful initialization, no pending responses and a healthy capture;
loss/expiry may preserve an incomplete summary but cannot claim complete pairs.
Capture errors latch permanently. Storage failure preserves partial files and
may prevent even a HOLD receipt; there is no overwrite, retry or resume.

The full supervised SDK test correlates actual initialization/discovery and the
124-call matrix before the same stopped-state verifier (audit30). It checks the
saved trace digest/length. Eight new data/storage controls exercise exact bytes,
integer-versus-string IDs, out-of-order/error replies, rejected replies and HOLD,
initialization order, pending requests, failed fsync, budget and base64 expansion.
The supervisor suite now has 20 controls; the coordinator suite retains 17.

This is `offline-proxy-framed-rpc`, not end-to-end Work capture, delivery proof,
connector invocation proof or an operational attempt receipt. Existing raw-wire,
operational-B, outer-cohort and scoped-gate flags remain false. The session's
available tool metadata shows Production/Dev namespaces but no bound fixture
namespace; this is not a global statement that a route is unavailable. No bridge
tool, client refresh, plugin setup, SSH, credential or guest action was used.

## Signed continuity and inventory checkpoint integration

`SignedRuntimeProvider` and `SignedInventoryProvider` reuse the existing bounded
message channel for runtime-continuity and writer-inventory roles. They do not
read original runtimes or enumerate actual writers. A matching MAC only proves
possession of the supplied key; it does not make provider data true or complete.
The new full SDK test still fabricates all observer measurements and identities.

When either new adapter is supplied, the join requires the entire signed set:
host, continuity and inventory, with the same attempt/private-binding digest,
distinct producers and distinct caller-supplied key bytes. Wrong/missing role,
reused role key or mismatched attempt is rejected before dispatch. No keys are
generated, provisioned or printed. This check is not private machine/method
binding, and shared-host trusted code can still bypass cooperative controls.

At each of 44 checkpoints all three roles receive the same fresh challenge and
stage. Each has its own sequence/nonce history, recorder and existing timeout.
The complete join still has the same two-second freshness limit: three message
exchanges do not extend it. A signed failure propagates to the HOLD latch; it
never falls back to the legacy injected offline providers. Original host-only
and unsigned data paths remain explicitly offline test interfaces, not Work
modes or recovery paths.

The journal retains both exact message directions for every role. The original
host event names remain; continuity/inventory have role-specific event names.
Verified message proofs remain separate from continuity values and writer lists.
The existing exact identity/healthy/list comparisons still apply after MAC
verification. A signed unhealthy runtime or changed writer list produces HOLD.
Provider binding/reserved-proof/cancellation errors now also permanently hold
the adapter's client, including the existing host adapter; no retry is added.

The full independently supervised SDK matrix checks 124 tool calls, 44 checkpoints,
audit30, complete RPC pairs and 44 request/response stage-sequence-nonce matches
per new role. Three message roles produce 132 exchanges (264 recorded frames)
for that completed offline case; no operational observation count is inferred.
Four added coordinator controls cover that flow, forged continuity/inventory
before the first matrix tool, bad role/key/attempt bindings and valid-MAC data
that fails continuity/writer checks. Three added channel controls cover role
adapters, byte record attachment and reserved-proof rejection. Current suites
are channel23 and coordinator21, plus unchanged supervisor20 and earlier suites.

The source work does not invoke Production/Dev tools, VM/SSH or host samplers.
Current session metadata still has no bound fixture namespace; it does not prove
global route unavailability. Actual collectors/carriers, private key/producer
identity binding, Work handoff and complete cohort/stopped-writer proof remain
HOLD on this same PR. Every operational readiness/acceptance flag stays false.

## Read-only known-leader inventory collector

`OwnedLeaderInventory` reads actual Linux process identity for only the current
controller and the supervisor/fixture leader in its SupervisedSdkFactory ready
binding. It accepts no arbitrary PID list, starts/stops no process, scans no
account or global process table, and reads no original Production/Dev runtime.
The first checkpoint binds ready data after SDK initialization; this is not a
pre-start inventory or approval. The ready map must remain unchanged afterward.

Each sample checks three distinct same-uid PIDs and the current controller PID,
then reads PID/start ticks/uid/executable/argv through the existing coherent-procfs
identity check. It reads/rechecks start ticks and parent links between two full
identity reads. Supervisor must still be a child of the controller; fixture must
still be a child of that supervisor. Failure, changed binding, duplicate/reordered
stage/nonce, stopped factory or unreadable process permanently holds the collector.
No retry or last-known-value substitution is provided. The one-second collection
cap is post-hoc, not interruption of blocked procfs I/O. The outer supervision and
two-second total join deadline remain necessary and unchanged.

The result names three known leaders only. It records complete_writer_coverage,
descendant_cessation_proved and original_runtimes_observed as false. It does not
search for children that detached, discover external writers, authenticate the
operator's host, prove continuous liveness or prove cessation after a later stop.
A matching three-name writer list cannot open an operational B or verifier gate.
Full cohort/descendant/external-writer coverage remains HOLD.

The signed inventory message can now carry leader_observation metadata alongside
the three labels. The join retains these actual observations separately from its
fabricated test host/guest/runtime inputs and MAC proofs. It validates stage,
nonce, sequence, duration and the required false scope flags. Claimed complete
coverage is rejected even with a valid MAC. A MAC does not authenticate where a
producer obtained its process data; private producer/carrier binding is still open.
The enclosing record is labeled offline-inputs-with-leader-metadata. Presence of
producer-supplied metadata never upgrades its provenance to a verified local read.
Only the independently run CI case establishes that its supplied collector actually
read those CI-local processes; the join alone does not establish that fact.

Five new coordinator controls cover the actual supervised SDK matrix with 44 live
three-leader samples, pre-read binding rejection, permanent failure/ready drift,
parent and second-identity checks, and rejection of a signed full-coverage claim.
The real CI case still asserts124/44/audit30 and retains every false operational
flag. Its process observations are CI-local only; every other observer input is
explicitly fabricated. Unit controls patch reads and label identities as synthetic.
Current coordinator suite has26 tests; channel23 and supervisor20 are unchanged.

No new module, workflow, dependency, runtime, fixture or candidate is introduced.
No operator-host/VM/SSH/credential/client/connector action occurred. Actual Work
route, remaining collectors/carriers, whole-cohort supervision, operational receipts
and stopped-writer proof remain work on this same draft PR.

## Proposed manifest-only prebinding route

`route_prebind.py` is a separate, permanently inactive stdio metadata peer. It
advertises the reviewed discovery_manifest.json schemas/annotations for 27 names,
with INACTIVE descriptions and initialization instructions. It checks the fixed
manifest SHA-256 and input pins. It does not import candidate/fixture/backend
modules, open a database, read operator configuration or start another process.
No active mode, candidate/state path, command, credential or forwarding argument
exists. All tools, including bridge_version, submit and unknown names, return the
same isError=true S24_ROUTE_INACTIVE result. It cannot pass the candidate identity
validator, and exposes no activation tool or configuration transition.

The peer implements only the bounded metadata subset exercised by the pinned SDK:
initialize/initialized, tools/list, denial of tools/call, ping and method-not-found.
Legacy server/discover returns -32601; completed JSON-RPC IDs can be reused because
this synchronous metadata peer has no pending requests or accepted backend action.
Malformed/duplicate-key/nonfinite/oversized frames or incorrect initialize order
hold the instance. Do not reuse this metadata policy as the matrix/RPC contract.

Linux pipe I/O is nonblocking with select bounded by one 30-second process window
from before manifest loading, at most 128 input frames, 64 KiB per frame and 1 MiB total
output. Neither initialize nor a tool call resets the window. These are metadata
peer bounds, not an extension/replacement of the B activation budget or a kernel
reservation. File loading/imports are still synchronous; their I/O is not preempted
by that select deadline. No client/cohort supervisor, duplicate-client/respawn
prevention, credentials, private receipt or operational capture is provided here.
A future tunnel may restart a target: that remains unproved and must not silently
become an authorized repeat or evidence of a single operational attempt.

### Staged path for review, not setup authorization

This source proposes a way to obtain platform-assigned namespace/capability data
without letting this executable start a fixture. It does not prove that the
operator's client/plugin can use it. No tunnel/plugin is created, installed,
connected or refreshed, and no namespace or supported Work invocation is claimed.
The plan review must decide whether this separate bounded stage fits existing
§24/plan gates. If a normative change is needed, its §14 amendment must precede
use. A source merge is not an exception, setup instruction or activation approval.

Before any operational use, review a separate exact inactive-stage plan: bind this
source digest, client binary/config/authentication method, new private profile and
route identity; complete resource/process inventory, stop/cleanup policy and finite
operator scope. Keep the target inactive until that scope is approved. Do not use
Production/Dev profiles or copy their credentials. Discovery/client start is never
an implicit approval, even for this no-fixture peer.

If such a stage is later approved, its evidence must say manifest-advertised route
metadata, not candidate discovery, live submit acceptance or B PASS. A later change
to an active executable/profile is a new source/route binding and possible fixture
activation; it requires full B gates and separate approval. Do not assume namespace
stability across such a change. Actual fixture identity/discovery/forwarding must
be proved again on the final active path before matrix stimulus; no SDK fallback.
The current peer has no code that can perform that later active handoff.

Ten offline controls use the real SDK stdio client in an empty temporary CWD,
compare all 27 schemas, deny every tool with active-looking inputs, forbid direct
spawn/database/network calls during handler checks, reject CLI activation/state
switches, detect manifest drift/symlinks and verify permanent framing/budget HOLD.
They also check legacy discovery, candidate-identity rejection, partial EOF and
bounded read/write readiness. Static import checks complement these tests; neither
is a general proof about a modified interpreter/host. The candidate, fixture,
manifests and all existing integration/observer/supervisor source remain unchanged.
All existing suites and warning gates stay enabled; this adds only metadata 10.

## Remaining work on this same integration PR

| Gate | Current state / required closure |
| --- | --- |
| Actual Work handoff/namespace | HOLD; no bound fixture namespace or supported invocation instance has been proved; never fall back to this SDK path as live evidence |
| Inactive setup / first activation binding | HOLD; review exact client identity, private route/config/authentication and any staged binding before requesting separate operational scope |
| Host/guest/continuity collectors | HOLD; scoped shared-key messages join offline and reject replay; actual protected carrier, producer/key/method binding and original-runtime collection remain unimplemented/unproved |
| Outer supervisor / complete cohort | Direct-fixture owner/lease supervision is integrated offline; full client/observer/descendant/external-writer coverage and operational stop targeting remain HOLD |
| RPC and durable attempt evidence | Offline parent policy/journal tested; actual route mapping, raw-capture correlation and private operational attempt receipt remain HOLD |
| Stopped-writer proof | Offline SDK context exit only; operational complete writer cessation must precede the same read-only verification logic |

Keep the #100 adoption observation open. Do not add a delay/retry or weaken its
identity check to obtain a pass. Phase A readiness acceptance remains the actual
operator statement recorded in the separate unmerged #96; this PR does not merge
it or extend that acceptance. PR #80 remains a separate historical HOLD. There is
no VM/host/SSH action, new guest window, credential, profile/plugin setup,
activation, release or deployment authorization from this source work.
