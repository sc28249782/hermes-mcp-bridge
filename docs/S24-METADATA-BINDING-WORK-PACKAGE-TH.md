# SPEC §24 — metadata R2 binding and control work package

Date: 25 October 2026.
Status: **OFFLINE METHOD PROPOSAL / R1 INCOMPLETE / R2 HOLD**.
Base: PR #105 merge `3b96610d6921def4a3334bb2b067f53d233bad17`.
Parent: [staged plan](S24-METADATA-PREBIND-PLAN-TH.md).
Evidence: [R0/R1 record](S24-PREBIND-R0-R1-RECORD-TH.md#s24-prebind-r0-r1-preparation-record).

<a id="s24-metadata-binding-work-package"></a>

## 1. Result and scope

The operator-supplied independent review approved PR #105 head `bced5155d56424dd731976c346d30577d6624e14`.
The operator then authorized its merge. That review covered the public record.
It did not inspect or approve the private dossier, complete R1 or authorize R2.
The reported preparation remains `INACTIVE_PREPARATION_RECORDED_PENDING_BINDINGS`.

This work package specifies how to resolve the remaining fields together.
Keep later control source, offline checks and private binding review in this work
package until its prerequisites are complete. This initial document is not package
completion and does not require an early merge. No guest window is opened here.
Any normative conflict needs separate §14 review/merge before use.

The target remains the permanently inactive metadata peer at `70eca6dc0895cc208cb3823e947f306c7f30bd26`.
Do not substitute the candidate, fixture, current main or an active adapter.
No fixture/backend/matrix or original-runtime stop/switch belongs to metadata R2.

## 2. Binding methods proposed for review

Every private field needs an exact value, observation time, method/source revision,
evidence location, verification result and limitation. A proposed method is not a
completed field. Hash exact final UTF-8 dossier bytes, including the final newline.
The digest is correlation, not authentication or an approval token.

| Binding | Proposed method and evidence | HOLD condition |
| --- | --- | --- |
| HOST / GUEST / CONTROL | Operator console records exact trusted Windows/WSL/VM identities and control ownership privately. Guest reads virtualization, boot identity, kernel/architecture and current account. Operator confirms the console remains independent of all test processes | Ambiguous machine/control path, original-runtime dependency or missing shared-host trust declaration |
| ROOT / LOGS / PROFILE / INPUT | Inspect canonical private roots, owner/mode/inode and ancestor/symlink boundaries. Compare client/peer/manifest/interpreter/dependency/profile bytes to the reviewed pins and exact approved argv. Preserve original files and previous failed records | Drift, overlap with originals, unsafe links/modes, placeholder or active target; no repair in the checking step |
| ROUTE / AUTH | Operator locally verifies new tunnel ID, intended Platform organization/workspace and key principal's Read + Use grants in the authoritative UI. Record redacted method/results privately. A later separately scoped, source-reviewed one-shot authenticated GET for this known tunnel may test key/read validity | Unknown entitlement, wrong scope, missing authoritative observation or any unapproved request. Read success alone does not prove Use or connector readiness |
| ENVIRONMENT / KEY LOADING | Build an explicit child environment map from an empty map. Preserve the exact venv argv. Bind only reviewed required values and the named runtime-key variable loaded locally from the confirmed private file through a reviewed helper | Inherited config/profile/backend/key/proxy/channel overrides, shell export/source/eval, CLI-literal key, plaintext logging or unreviewed loader |
| PORTS / NETWORK | Bind one exact new guest loopback health endpoint and the pinned control-plane HTTPS endpoint. Read-only TCP tables are a snapshot; recheck immediately before the approved launch. No host mapping/firewall/SSH change | Occupied/unknown port, unexpected endpoint/redirect/proxy or need to change host policy; no automatic alternate port |
| PROD / DEV CONTINUITY | Bind exact independently identified read-only health/version observation methods for both original runtimes. Record expected identities, transport, time bounds and allowed response projection. Observe before/during/after R2 through independent control | Missing/unhealthy/changed/stale response or unavailable control. An aggregate heartbeat, process age or a healthy guest is insufficient |
| RESOURCES / OBSERVERS | Bind actual Windows CIM and guest samplers, clocks, source hashes, writer inventory and private output paths. Retain discrete host/guest/RSS/disk/growth/log observations and explicit cadence/gap limits | Missing or late sample, exceeded threshold or unaccounted observer/log writer; no stopping original services to free resources |
| PROCESSES / SUPERVISION / STOP | A reviewed outer controller must account for client, peer, controller, observers, descendants and external log writers. Bind exact executable/argv/owner/start identity, launch counts, expiry/owner-loss behavior and stop/confirmation method | Unimplemented supervision, unobservable/escaping writer, ambiguous stop target, second launch, respawn, missing confirmed exit or insufficient stop time |

UI observations and guest reports retain operator attribution. MAC success, a form
field, a local parse or a file mode cannot upgrade them to independent observations.
Do not publish credentials, raw account/tunnel IDs, paths, PIDs or host identities.

## 3. Credential and doctor boundaries

The selected client is v0.0.18/source `274a5588414819f063d27100a4fb1096aae3830f`.
Its pinned [doctor source](https://github.com/openai/tunnel-client/blob/274a5588414819f063d27100a4fb1096aae3830f/cmd/client/doctor_command.go)
shows that the stdio branch checks the command and skips target network/OAuth probes.
Its API-key check follows config loading; it is not an authenticated tunnel request.
A doctor PASS cannot fill credential validity, Read/Use entitlement or route proof.

The same source's `doctorHealthListenerCheck` actually calls `net.Listen` and closes
the listener. Its Unix-socket branch can create directories and remove its test socket.
Thus doctor is not a pure read-only inventory command. Do not run it in a read-only
scope or point its socket/config paths at originals. No doctor command is run here.

For a future known-tunnel GET, review the exact endpoint/method, authorization header
loader, TLS trust, response allowlist and bounded lifetime before scope approval.
Disable redirect following, retries, environment proxy inheritance and raw HTTP logs.
Permit no tunnel listing, polling, registration, mutation, plugin operation or MCP
request. A timeout/uncertain response ends the check; it does not authorize another
request. No such helper or authenticated call is implemented/performed by this document.
If authoritative Use evidence cannot be established before launch, keep HOLD.
Do not silently defer a required prelaunch proof to R2 to bypass its prerequisite.

## 4. Source/control closure before any launch

The [integration source](../acceptance/s24/INTEGRATION.md) supplies offline contracts,
direct-fixture supervision and a three-known-leader inventory. It does not supply
complete metadata-client/peer/observer cohort control.
The fixture supervisor has a fixed fixture startup path; do not repurpose it as a
metadata launcher or treat its tests as installed-client supervision proof.

Review and implement the metadata controller as one coordinated source delta.
It must enforce one launch and the original absolute R2 deadline, block further
stimulus after HOLD, and retain partial evidence without automatic reconnect,
refresh, retry, respawn, profile switching or stale-claim removal.
Bind the actual installed client's restart behavior rather than assuming source
shutdown requests imply a complete exit or prevent an external restart.

A process group, known leaders, two process snapshots or closed pipes alone do not
prove complete writer coverage. A separately scoped read-only capability inventory
may inspect existing procfs/cgroup visibility, namespace/delegation information and
the nominated account's processes. Visibility is not enforcement/delegation proof.
This proposal chooses no unproved cgroup or containment mechanism and performs no
cgroup write, process migration, service setup or disposable process launch.
If complete coverage requires such setup, review exact source/actions and obtain
the separate setup scope first. Missing capability keeps R2 HOLD; no weaker fallback.

The outer owner-loss/deadline path must remain operational when the Work client or
parent stalls. Recheck exact identities before TERM. KILL after 10 seconds requires
explicit scope and the same matched test targets. Do not signal an original process.
Record actual exits and all remaining writers; PID absence alone is insufficient.
A stopped receipt is issued only when its stated coverage has been proved.

## 5. Observation and timing proposal

Retain the staged plan's resource floors/caps and one 30-second peer window.
R2 remains at most 120 seconds from before client launch, including at least
10 seconds for TERM grace and sufficient observation/receipt time. No deadline reset.
No new matrix/B 20-minute window is granted by metadata setup.

For source review, propose independent resource/continuity sampling at most 1 second
apart, parent receipt age at most 2 seconds and a 1-second per-sample limit.
These are proposed rejection bounds, not measured latency or interruption guarantees.
A blocking sampler needs independently reviewed supervision; a post-hoc timeout
cannot enforce shutdown. Cross-clock correlation needs a reviewed method, not
subtraction of unrelated timestamps. Missing/gapped observations latch HOLD.
No sampling implementation or operational timing validation is claimed here.

Peer expiry or inability to complete UI/discovery within its unchanged 30 seconds
ends the attempt. Do not extend the peer timer or run a second client to obtain
a namespace. R2 permits only initialization/ping/list metadata, never tools/call,
including a deliberately denied version or submit.

## 6. Combined closure and proposed next scope

1. Independently review this method proposal and the exact private review form.
   No field is marked complete by document merge.
2. Present one finite R1 binding-inventory scope with the exact reviewed helper(s):
   nominated-file metadata/hash/static config checks, local authority observations,
   guest capability/resource inventory and independently scoped original-runtime
   read-only observations. No client/peer start, doctor, active probe or key rewrite.
   Collect missing values together; do not reset any prior marker.
3. Review that result and finish the controller/collectors/key-loader source and
   negative controls in this same work package. Any authenticated GET or additional
   setup requires its own explicit actions/authority in the proposed scope.
4. Validate scope-specific source offline on both supported interpreters.
   Cover wrong authority/input/env, stale/missing samples, duplicate launch, expiry,
   controller loss, PID reuse, unexpected descendants/writers and incomplete stop.
   A guest capability read or injected unit value cannot replace these controls.
5. Review exact source and completed private bindings together. Only then present
   a finite R2 approval request with all hashes, control/stop methods and limits.
   No R2 command, activation token or approval is provided here.

The R0/R1 public record review passed. Private binding review remains open.
No new guest command, API request, credential read/write, profile change, bridge
tool, account action, provisioning or activation occurs in this offline work.
PR #80 remains HOLD; #96 stays separate/unmerged. Metadata R2 cannot close Phase B
or scoped §22; later release/deployment and active acceptance remain separate.
