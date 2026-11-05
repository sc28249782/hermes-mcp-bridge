# SPEC §24 — Phase B adapter and control implementation plan

Date: 24 October 2026.
Status: **DESIGN PROPOSAL — no provisioning, activation or acceptance approval**.
Base: main `7e28518a475616e4b1f95cba884141dc96a924b8` (PR #94 merge).
Parent plan: [S22-SHAREDHOST-20261023-01](S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md).
Contract: [SPEC §24](SPEC.md#24-shared-host-synthetic-acceptance-proposed).

## 1. Current gates and fixed inputs

[Phase A evidence](S22-SHAREDHOST-PHASE-A-READINESS-TH.md) passed the operator-supplied independent review at PR #94 head `ba5a0b134428902d267d33e54ac80250ec52c1b2` and merged at this base. That review assesses attribution/limits; the operator has not explicitly accepted Phase A readiness in the conversation recorded here.
Planning can continue while that acceptance is pending. No acceptance is inferred from merge or a request to continue. A readiness acceptance covers guest/artifact preparation only; closing the section 22 scoped synthetic acceptance gate requires a completed Phase B attempt, its independent evidence review and explicit operator acceptance.

Candidate remains `02d7e8bb1e1902ca33a574ab904a6e5b0f441785`.
Reviewed fixture remains PR #91 head `e7be0cc4e84b820eb8c7ac541325672d0f892fb2`; its [matrix and limits](../acceptance/s24/README.md) remain the behavioral input.
No revised guest input or fixture code is introduced by this document. Any B source additions or fixture instrumentation require their own exact revision, diff, offline checks and independent review before they enter a later activation scope.
The previous preparation window is historical; it is not reused or extended for B.

## 2. Proposed components and unresolved route proof

| Component | Proposed responsibility | Boundary / required proof |
| --- | --- | --- |
| Parent matrix runner | Reuse reviewed Python matrix with parent-route-observations and a real checkpoint callback | No local SDK fallback for a live run; offline evidence stays separately labeled |
| Connector adapter | Map data-only requests to the exact independently authenticated test connector | Prove an available supported invocation path; no assumed generic API, copied production namespace or invented endpoint |
| Guest supervisor | Own one fixture cohort, record identities/lease and observe guest resources/writers | New test resources only; immutable source checks and one fresh state path |
| Host/continuity observer | Supply fresh host resource and original-runtime observations at checkpoints | Separately reviewed and approved read-only method; guest metrics cannot substitute for host RAM or host process observations |
| Stopped-state verifier | Compare stopped fixture state to the runner's actual expected rows/registration/audit projection | Read-only databases; no bind/replay/rewrite or new fixture invocation |
| Operator | Review private bindings and execute scoped setup/activation/handoff | No credential in prompts or evidence; observations/receipt hashes do not grant authority |

Preferred deployment shape for review: a separately identified guest-local tunnel client starts the fixture through stdio. This avoids making an original production/Dev profile the test launch target.
It remains a proposal, not proof that a supported client/connector/adapter is available in this guest. Installation source/version/digest, a supported invocation interface, authentication path and lifecycle/resource requirements must be reviewed before executable setup is approved. Static interface proof is separate from actual new-route validation: namespace/discovery/lifecycle observations occur only during a separately approved first activation, before matrix stimulus.
SSH reachability, a free local port, a local SDK call or a host-key match does not establish a Work-chat connector. No unattended SSH key or host policy change is authorized here.
If the approved parent cannot invoke the actual new connector through a supported interface, the route stays HOLD. Do not substitute the existing local SDK transport, another plugin or a mocked response and call it live evidence.

## 3. Matrix transport interface

The source PR should provide a narrow asynchronous adapter for the existing matrix callable. The adapter returns the actual CallToolResult shape, including structuredContent/isError, without removing or rewriting ACK fields.
For the matrix, allow only bridge_status, bridge_context_recent, bridge_context_create, bridge_context_status, hermes_submit_task and codex_submit_task. Permit bridge_version and protocol tools/list only for separately identified identity/discovery probes.
Bind these calls to the new fixture connector namespace. Original Production/Dev observations use separate read-only bindings; they are never acceptance-stimulus targets. Add no MCP tool, bind operation, Codex request_id or runtime contract.

A proposed local runner/parent IPC is data-only: sequence, action kind, tool name/arguments or checkpoint stage. It is not a guest MCP endpoint or new authority.
Validate message type/sequence, tool allowlist, expected case arguments and a reviewed maximum frame size before dispatch. Reject duplicates, out-of-order replies, malformed/oversized frames and missing observations. Bound the total trace within the existing 128 MiB evidence budget.
The actual IPC framing/limits and parent-to-connector binding must be source-reviewed; this document does not claim an implemented adapter.
Do not automatically retry/reconnect/resubmit after a lost response or uncertain acceptance. Preserve partial evidence and HOLD. The planned known-ID Hermes replay is a named matrix case, not transport retry or uncertain-outcome recovery.

## 4. Checkpoints, observations and source identity

The current driver calls checkpoints before/after the matrix, both sides of each of 18 cases, both sides of replay and both sides of the two precheck/plain groups: 44 ordered callbacks for a completed run.
Each callback must validate actual observation data before returning True. A callable or hard-coded True is not evidence.
The source implementation must define numeric freshness/lease/sampling bounds and failure behavior, then bind those reviewed values before activation. Missing numeric bounds, stale data or an observer that cannot inspect a required resource keeps HOLD.

At each required boundary check the selected source/harness/cohort, permitted row/counter deltas, writer inventory, elapsed budget, guest/host resources and original-runtime continuity. Keep direct observations separate from operator statements and inferences.
The reviewed matrix already checks rows, exact constant notes, full ACK digests, precheck call deltas and guarded replay. Reuse its case order and expectations unchanged. A source change to those expectations needs separate review.
Expected successful one-fixture totals remain contexts 18 (closed 2/open 16/bound 7), Hermes POSTs/registrations 10, memory-only Codex submits 10, audit 30 = 18 create + 2 close + 10 submit.
These are future assertions, not observed B results.

Capture source/manifest/harness identities through an approved independent management observation before start and after stop. Keep operational identity metadata separate from the candidate's inherited release stamp.
Discovery must be observed through the actual selected connector; bridge_version's reported count or a parent aggregate inventory is not a raw tools/list capture.
Every trace/receipt must label local SDK/unit, parent connector observation and actual captured protocol evidence accurately. Preserve the shared-host trust assumption; do not infer continuous absence of interference.

## 5. Lifecycle and failure behavior

A separately approved local operator control path is preferred. No dependent host-control job may be cut off by fixture shutdown. Any normal control-plane job/audit registrations must be disclosed outside stimulus totals.
Inventory the tunnel client, fixture, adapter/controller, observers and every actual worker/log writer with executable/argv, owner, PID/start identity and lifetime. A missing/unaccounted writer keeps HOLD.
A guest-side finite supervisor must stop new stimulus when the parent disconnects/stalls, a lease expires, the 20-minute activation window ends or an observation fails. The reviewed implementation must show how the parent is blocked from further calls and how only exact bound processes are quiesced.
Automatic client reconnect, refresh, respawn or a second fixture launch must not silently create a new state or reset a deadline. Prove the chosen client's discovery/process lifecycle; an unexpected cohort restart or occupied state path keeps HOLD.

Use the existing resource limits: serial workload, observed combined test RSS at most 768 MiB, host available at least 1536 MiB, guest available at least 768 MiB, disk free at least 2 GiB, workspace growth at most 2 GiB and logs at most 128 MiB. These remain monitored thresholds, not kernel reservations.
Recheck exact stop identities before TERM. KILL after ten seconds is permitted only for the same matched test-owned targets explicitly included in B approval; otherwise HOLD for operator inspection. Never use substring matching or signal an original runtime.
Record partial execution, stop outcome and inspection limits on failure. Do not delete state/evidence, restore old snapshots, poll the unresolved historical run or edit ownership/outcomes.

After all actual fixture writers cease, run a separate read-only verifier using the driver's saved actual expected rows, registration mapping and audit projection. Do not use the offline command, which would start another fixture.
Capture snapshots/hashes and original-runtime observations, keep the test route inactive, and preserve evidence. A read-only verifier is not a repair tool; a mismatch remains HOLD.

## 6. Source work and validation before setup/activation

| Work item | Required independent review evidence |
| --- | --- |
| Route capability proof | Supported interface/namespace binding and offline lifecycle controls before setup review; actual new-route discovery/cohort proof during separately approved activation, before matrix stimulus |
| Data-only runner/adapter | Correct namespace, deep ACK preservation, sequence/framing limits, no fallback or implicit retry |
| Observers/checkpoint validation | Missing/stale/changed identity, resource threshold, continuity failure and hard-coded-success negative controls block before the next stimulus |
| Supervisor and stop targeting | Parent loss, expiry, duplicate start, PID reuse and writer uncertainty fail closed; only matched test cohort can be signaled |
| Stopped-state verifier | Real row/registration/audit comparison; tampering fails; no write or spawn path |
| Offline regression | Unchanged candidate full/focused suites, reviewed artifact checks and new negative controls on Python 3.12/3.14; no claimed B result |

The source PR may name proposed files under acceptance/s24, but must not alter production runtime or the immutable candidate tree. Keep new test inventory separate from the 234/7/10 historical measurements.
Use synthetic transports and test-owned processes for offline controls; do not obtain capability evidence by starting a real backend task or modifying original services.

## 7. Separate provisioning and activation gates

1. Record explicit operator Phase A readiness acceptance, with its limits. Review this design and then each exact source delta. No selection/acceptance is recorded here.
2. Complete private HOST/PROD/DEV/GUEST/ROOT/STATE/LOGS/INPUT/HARNESS/CONTROL/WORKERS/ROUTE/PORTS bindings, observer methods and all numeric lease/framing/freshness values. Keep credentials/actual local inventory private.
3. If new client installation, route/profile/credential/connector provisioning is needed, present exact reversible setup actions and obtain separate scope first. Only the operator provisions new authentication through the approved local path.
4. Provisioning must leave the target inactive. The first client start, refresh/autodiscovery or reconnect that can spawn the fixture counts as activation, even before a matrix call. Obtain B scope before that event; do not use refresh as an unapproved readiness probe. Under that finite activation scope, validate actual route/discovery/cohort behavior before permitting the first matrix stimulus; a failed proof ends at HOLD.
5. Bind the exact reviewed source/digest, completed private map, budgets, controller/stop policy, setup actions and finite B window in explicit operator approval. Missing capability/observer/authority binding keeps HOLD.
6. A completed B attempt requires its own record, independent evidence review and explicit operator acceptance before closing the scoped section 22 synthetic gate. Phase A readiness or this design merge cannot close it.

This proposal authorizes no VM/host/SSH change, installation, credential creation, profile/connector setup, activation or guest test. No operator approval timestamp or Phase A acceptance is invented.
PR #80 remains HOLD, historical outcomes remain unknown as recorded, and release/signing/publication/deployment remain separate decisions.

## Phase B route feasibility checkpoint — 24 October 2026

The [route assessment](S22-PHASE-B-ROUTE-FEASIBILITY-TH.md) establishes a documented product path for a separate Work custom plugin and guest-local tunnel client. Actual fixture namespace/invocation, full result/capture provenance, observers and finite lifecycle remain HOLD. No new route, account action, guest measurement or activation occurred. The prior source/design checkpoints retain their historical wording and all original gates remain unchanged.

## Metadata prebinding stage proposal — 25 October 2026

The [staged plan](S24-METADATA-PREBIND-PLAN-TH.md) pins the reviewed permanently inactive peer at `70eca6dc` and proposes separate read-only inventory, inactive preparation and one bounded metadata attempt. It remains NOT EXECUTION-READY: compatibility disposition, any required §14 amendment, guest/private bindings, client/asset verification, observers/stop controls and separate operator scopes are open. No setup, credentials, client start, namespace, candidate discovery, B acceptance or original-runtime action is approved. Historical text and PR #80 HOLD remain unchanged.
