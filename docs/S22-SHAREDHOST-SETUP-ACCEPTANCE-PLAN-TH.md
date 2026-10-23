# SPEC §24 — shared-host setup and synthetic acceptance plan

Date: 23 October 2026.
Plan ID: `S22-SHAREDHOST-20261023-01`.
Status: **PROPOSED — no setup or activation authorization**.
Base: main `51a35d1acba59a3d354e6d6a91463015dc8a8c0d` (PR #86 merge).
Contract: [SPEC §24](SPEC.md#24-shared-host-synthetic-acceptance-proposed); stimulus contract: [SPEC §22](SPEC.md#22-context-binding-unresolved-proposed).

## 1. Scope and approval boundary

PR #86 passed the operator-supplied §14 external review at `5d47c684258311979ddb4f47d094c5e164c9d0ba`; exact-head CI `39942529086` passed. It merged at the base above after the operator instructed, verbatim:

> **merge #86**   ได้

The message has no exact approval timestamp; none is invented.
That instruction approved the amendment merge only. This plan requires separate review and explicit operator scope.
The shared host, host administrators, hypervisor and operator actions are trusted infrastructure. No isolation from host authority, historical cessation or global quiescence is claimed.
The historical registration remains unknown; PR #80 remains draft/HOLD and is never relabeled PASS by this plan.

Approval choices after review:
- **A only:** prepare the designated guest workspace, dependencies, and a reviewable fixture artifact; produce a readiness receipt. No connector provisioning or live acceptance.
- **B:** a later explicit activation approval bound to the reviewed artifact and completed private resource binding. A approval does not imply B.
- **Defer:** leave the current setup/activation HOLD.

Document merge selects none of these. No execution approval is recorded in this proposal.

## 2. Exact inputs and private resource binding

Candidate: PR #79 merge `71dcae67cbfa6f0b953ab8d81198d073d202ed2a`. Do not substitute current main, a release ZIP, or another tree without review.
The guest harness must exercise candidate `server()`, `Bridge`, and `ContextRegistry` with deterministic test-only hooks, synthetic Hermes transport, and stub Codex/Hands. Do not patch candidate runtime/stamp or introduce tools.
The old private fixture is not an approved input. Phase A must create a source-reviewable artifact and record its commit/content digest and source manifest. A missing artifact pin blocks B.
Candidate code/tests and harness source must be compared before B; unit helpers do not themselves establish transport coverage.

Before A starts, the operator records the nominated guest identity, verified SSH host key if SSH is used, operator access path, and new private workspace in a private binding for this plan ID.
Before B approval, complete the table below. Actual identifiers, endpoints, account names, paths, fingerprints and credentials stay private.

| Alias | Exact binding required | Authority / permitted role |
| --- | --- | --- |
| HOST | Shared host/management identity and resource observation method | Trusted operator management; not a test shutdown target |
| PROD / DEV | Original runtime/profile/config identities and redacted continuity baseline | Read-only continuity observations; no stop/switch/restore/retarget |
| GUEST | Nominated guest identity and operator access path | Setup only within the approved guest scope |
| ROOT / STATE / LOGS | New canonical guest paths and permissions; no overlap with original resources | Test-owned only; directories 0700 and evidence files 0600 |
| INPUT / HARNESS | Candidate pin, manifest, harness revision/digest and reviewer disposition | Immutable test input; no floating checkout |
| CONTROL / WORKERS | Exact executable/argv, owner, PID/start identity, lifetime and signal targets | Accounted test processes only |
| ROUTE | New tunnel/profile/connector identity, target command and authentication scope | No production/Dev alias reuse or credential copy |
| PORTS | Exact unused guest test listeners and approved network paths | Bind only as required by the new route; no existing listener replacement |

A host-key match establishes a matched key, not connector readiness or host isolation.
Unknown or changed binding, an occupied target, an unreviewed harness, missing local approval or unavailable continuity observations keeps HOLD.

## 3. Resource and time budgets

These are proposed limits, not observations about the nominated machine. They must pass review before use.
Do not resize the VM, change host policy or stop original services to meet them.

| Budget | Proposed limit / gate |
| --- | --- |
| New test workload | One serial fixture; no parallel test worker pool; combined observed test-process RSS at most 768 MiB |
| Available memory before each phase | Host available memory at least 1,536 MiB and guest MemAvailable at least 768 MiB; guest workspace at least 2 GiB free |
| Workspace growth | At most 2 GiB, including virtual environment, inputs and evidence; logs at most 128 MiB |
| Phase A | At most 30 minutes per approved preparation window |
| Phase B | At most 20 minutes from fixture activation, including evidence and stop; no automatic extension/retry |
| Controller | One designated controller; no dependent host-control job may be cut off |
| Monitoring | Resource/continuity checks before, at each case boundary and after; operator remains present |

These are monitored stop thresholds, not claimed kernel-enforced reservations or proof of no transient peak.
If a threshold fails or cannot be measured, stop new stimulus and quiesce only bound test processes. Preserve evidence and return HOLD.
A different budget requires reviewed plan revision and operator scope; it is not adjusted silently during execution.

## 4. Phase A — guest preparation only, after explicit A approval

1. Verify the private GUEST/ROOT binding and approval. Use the operator's guest console or manually authenticated SSH session. Keep passwords/private keys out of prompts and evidence. This plan creates no unattended access key and changes no SSH/host security setting.
2. Read guest identity, interpreter, mount types, available memory/disk and tool availability. Record observed versions and limitations. Host/guest sharing must be absent from the test data path; do not infer this solely from a filesystem-type list.
3. Create only the new bound private workspace and virtual environment. Fetch the public candidate at the exact pin into that workspace; copy no original state/config/authority store/credentials.
4. Use an installed Python 3.12 or 3.14 interpreter and pinned candidate dependencies in that environment. Missing system packages, another interpreter, package-manager changes or broader network requirements are blockers to report, not implicit install/upgrade permission.
5. Construct and review the fixture artifact as source separate from the immutable candidate. Include hooks, counters, stimulus driver, expected row-state assertions, exact signal/cleanup targeting and bounded evidence capture. Stubs must have no subprocess/native/backend execution path.
6. Run the candidate full suite and focused §22 matrix with ResourceWarning as errors in the guest environment. Record actual interpreter, test counts, skips/failures and exits; 234 total and 7 focused are expected from the reviewed candidate but are not predeclared results.
7. Produce a private readiness receipt with input/harness hashes, source comparison, dependency identity, resources and unfilled B bindings. Submit redacted artifact evidence for review. A failure, missing pin or incomplete observation keeps B HOLD.

A does not create a tunnel/connector, provision credentials, start a live fixture, or claim acceptance. Preserve the workspace; no deletion is included.

## 5. Phase B — connector and fresh acceptance, after separate B approval

B approval must name this reviewed plan revision, exact artifact digest, completed private binding, resource budgets, setup actions and the finite activation window. If exact route provisioning cannot be named in advance, obtain scoped provisioning approval first, then rebind/review before activation.
Only the operator provisions new scoped route authentication through the approved local path. Do not reuse original profiles or put credentials in task prompts. Validate the new route/target before any stimulus; a local SDK tool list is not a raw tunnel capture.

1. Capture read-only PROD/DEV identity/health and existing process/start continuity where observable. Record known unrelated work, the unresolved historical registration and shared-host interference limits. Do not poll the missing run again without new evidence.
2. Revalidate all bindings, hashes, permissions, budgets and approval. Inventory every new fixture backend, controller and actual writer; verify stubs cannot spawn native tasks. New empty state proves only fixture inventory, not global quiescence.
3. Verify candidate/harness bytes and fixture schema. Establish a fresh evidence baseline. Start only exact bound test processes and the independent route. Record their identities and begin the finite controller window.
4. Through the authenticated new connector, verify candidate identity and expected discovery without restamping. Clearly separate source revision from inherited release stamp. No released/deployed claim is created.
5. Execute the matrix below serially. Before/after each case verify expected state deltas, IDs, full allowed acknowledgement fields and backend call deltas. Keep parent observations distinct from raw wire evidence.
6. On any unexpected write, row/count/identifier drift, unknown writer, native/backend activity, identity mismatch, missing observation or resource/continuity issue: stop stimulus, preserve evidence, and mark HOLD. Trust does not prove absence of interference.
7. Finish or hand off the controller. Recheck each test PID/start identity, then stop only bound test processes with TERM. After 10 seconds, KILL is permitted only for the same still-matched, test-owned processes explicitly named in B approval; uncertainty means HOLD and operator inspection, not broad process matching.
8. After all fixture writers cease, capture private database/log snapshots and hashes. Verify final counts/integrity and PROD/DEV continuity. Keep the test route inactive and preserve evidence. No original state restore, host reboot, credential deletion, workspace deletion or unknown-run action is included.

## 6. Stimulus and integrity matrix

| Coverage | Required result / state observation |
| --- | --- |
| Both backends: normal ACK then bind | bound; exact expected binding; one backend call |
| Both backends: each allowlisted failure PRE / real transaction COMMIT / POST-commit | binding_unresolved with exact constant note and full ACK; PRE/COMMIT unbound, POST bound; no reconciliation call |
| Both backends: actual close after ACK before bind | closed_rejected; closed/unbound; subclass order preserved |
| Both backends: excluded ProgrammingError | Existing whole-request error; no conversion or binding |
| Closed precheck; no-context submit | Precheck adds zero backend calls; no-context response has neither binding field |
| Hermes known-ID guarded replay after an unresolved PRE case | Same backend identifier; heal only by normal bind after one-shot hook; no new POST; no uncertain-replay claim |
| Stub Codex approval payload | pending_local_approval and complete stub ACK preserved; no actual approval or child process |
| Additional excluded/fatal/submit-raise/malformed-ACK coverage | Candidate deterministic unit matrix; label unit-only unless separately exercised live |

Live PRE/COMMIT/POST coverage must exist for both OperationalError and ContextError to claim that expanded matrix. Real rollback/committed row state must be verified, not inferred from the response.
The reviewed harness must give the exact case order and expected create/close/submit/counter totals before B approval. This plan does not invent aggregate totals before the artifact exists.
Compare deep ACK snapshots and durable rows with the exact driver expectations. Snapshot only after writers stop. Record timestamps as observations, not proof of event order.
No real-backend, native, host-isolation, full-quiescence, continuous-no-interference or exactly-once claim is permitted.

## 7. Record and exit

Write a new shared-host acceptance record. Preserve first-attempt history and PR #80 HOLD.
Report each phase's scope/approval, exact pins, environment, stimuli, expected/observed deltas, observed continuity, omissions, incidents, stop/cleanup results and residual limits. Public evidence contains aggregates and redacted provenance only.
An independent evidence review and explicit operator acceptance are required before closing the scoped §22 synthetic gate. Plan review/merge and successful preparation do not close it.
Release readiness must explicitly consider these limitations; release, signing/publication and deployment remain separate decisions.
No operational action was performed while authoring this plan. §23 case-disposition evidence and old Dev stop/switch gates remain unchanged.


<a id="s24-revised-input-preparation"></a>

## Revised-input preparation checkpoint — 23 October 2026

The operator selected option ก of the [input decision packet](S22-PHASE-A-INPUT-DECISION-TH.md), after its merge at `686973b5240e30b8f9e5d274f75e918e0af5b76c`, with this complete message, verbatim:

> ก

No exact approval timestamp is available; none is invented. This selects preparation of a coupled input/manifest PR only; it is not approval to merge that PR, execute the revised guest input, declare readiness or activate B.
Prepared input: `d3144cc48437011830533ba0d4606b8d4644be3a`, tree `4b3a27e7d5f72589b02de69a45c1302144718d12`, sole parent original input `71dcae67cbfa6f0b953ab8d81198d073d202ed2a`.
It retains 104 blobs and changes only the focused-test file (+3/-3), using reviewed PR #89 blob `c9fae04df337699a679cbf994401c875428cc234`. Runtime, assertions, dependencies, stamp and file modes are unchanged.
This revision prepares the artifact PIN, 104-entry manifest and dedicated CI for that exact input. Independent review/merge and explicit guest scope bound to the revised artifact/input are required before use. At that point this scoped input checkpoint supersedes the original candidate instruction only for the new A-only measurement; the original paragraph and evidence remain history. No floating-main substitution or manual overlay is permitted.
Preserve the old checkout/logs and use a new private candidate/evidence location. Re-run full suite, focused section 22 and artifact checks; record actual counts/skips/exits and inspect combined output through interpreter shutdown. Exit zero alone does not clear ResourceWarnings.
Original guest results remain 234/7/10 tests OK with two focused finalizer warnings. Revised guest measurements, dependency identity, resource/continuity observations and the 0600 readiness receipt remain pending. A warning, missing observation or failed check keeps HOLD.
No normative SPEC behavior, matrix, budgets or B binding/gates are changed. Phase A remains incomplete; B and PR #80 remain HOLD.

<a id="s24-two-blob-preparation"></a>

## Two-blob preparation checkpoint — 23 October 2026

The operator explicitly approved PR #93 merge and option ก in one complete message, verbatim:

> Merge ได้ และเลือก ก

No exact approval timestamp is available; none is invented. The merge completed at `55f42de1c7c83f637b3979058386b5239911083a`. Option ก selects preparation of this revised #91 source/manifest delta only; it does not authorize merging #91, revised guest execution, readiness acceptance, B, release or deployment.
The [two-blob decision](S22-PHASE-A-TWO-BLOB-INPUT-DECISION-TH.md) selects prepared input `02d7e8bb1e1902ca33a574ab904a6e5b0f441785`, tree `e0a905fb5ec02b91c1a8e8c58351c316e94eadbd`, sole parent the earlier one-blob input `d3144cc...`.
This supersedes the candidate identity in the prior preparation checkpoint only for this revised preparation. Historical original/one-blob instructions and evidence remain unchanged. The 104-file manifest changes exactly the two reviewed test blobs relative to the original; runtime, assertions, dependencies, stamp, schema and modes do not change.
The revised artifact PIN/manifest and dedicated-CI checkout are coupled. All scanner markers, failure handling, synthetic matrix, counters, budgets, private bindings and B gates stay intact. Review/merge and explicit scope bound to the reviewed artifact/input remain required before any revised guest use.
Preserve prior candidate/evidence and use new private paths for future authorized measurements. Require fresh full/focused/artifact results, output inspection through process exit, dependency identity and actual resource/continuity observations before the private 0600 readiness receipt. Missing observations or warnings keep HOLD.
Earlier guest/CI warnings remain evidence; no exact historical connection-object attribution is established. Phase A remains incomplete; B and PR #80 remain HOLD.

## Phase A evidence checkpoint — 23 October 2026

The [Phase A readiness record](S22-SHAREDHOST-PHASE-A-READINESS-TH.md) reports fresh guest 234/7/10 OK with unchanged warning gates, 65 resource samples and discrete matching Production/Dev health/identity observations before/after under the original window. Guest/private receipt data are operator-reported; connector observations are author-observed parent evidence. The earlier round remains PENDING because its continuity observations were missing. Status is READY FOR INDEPENDENT REVIEW, not Phase A acceptance or B approval; all scope, budgets, private binding and historical HOLD gates remain unchanged.
