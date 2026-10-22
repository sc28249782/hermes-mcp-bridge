# SPEC §22 — feasibility design and unresolved prerequisites

Date: 22 October 2026.
Status: **design only; no resource selected; setup/activation HOLD**.
Stack base: reviewed PR #84 head `c4faf5e9087fb8e1c6a894f24f70818b4503cfc6`; PR #84 is not merged.
Candidate proposal: PR #79 merge `71dcae67cbfa6f0b953ab8d81198d073d202ed2a`.

## Authorization and publication scope

Operator message, verbatim:

> เลือก ข

The message has no exact approval timestamp; none is invented.
This selects feasibility design in the [decision packet](S22-SEPARATE-ACCEPTANCE-DECISION-TH.md). It does not authorize merge, resource selection, cost, credentials, setup, connector provisioning, activation, maintenance, acceptance, release or deployment.
This choice checkpoint was not part of the reviewed parent tree.

This public design uses the already published packet requirements. It contains no local capability inventory, private receipt content or digest, resource capacity, installed product/version inventory, account membership, access-control observation, or private path.
A bounded private design-support check was completed separately. This document does not publish its findings or use them as proof of a verified resource boundary.

## Proposed resource and authority map

These are requirements for an unselected future resource, not observations about an existing machine.

| Resource / authority | Required ownership or separation | Evidence needed before setup consideration |
| --- | --- | --- |
| Original production/Dev runtimes, state and profiles | Remain under their existing authority and unchanged by this proposal. | Reviewed scope proving the new plan neither depends on nor modifies those resources. |
| Historical unresolved execution and possible writers | No terminal or cessation inference. | Complete proof of separation from the proposed test resources; absence or a new empty registry is insufficient. |
| Test compute and management plane | Management principals must be outside the original execution authorities' control. | Management-access map, reachable credentials/control sockets, lifecycle ownership and enforced denial of original-authority access. |
| Candidate, fixture state, ports and logs | New exact identities with no original state/secret copy or shared writable resource. | Complete resource inventory and access proof in both directions. |
| Test controller and every writer | Finite, accounted ownership with an explicit handoff and cleanup boundary. | Reviewed lifecycle/containment design and fresh preflight for the exact plan. |
| Independent authenticated connector | Separate scope and profile; no retarget of production/Dev routes. | Approved provisioning plan, route availability, authentication and network constraints. |
| Test-to-original network/storage access | Denied by an enforceable boundary. | Verification plan for mounts, host integration, sockets, management access, shared credentials and network paths. |

A directory, Python environment, process group or product name alone proves none of these boundaries.
A disposable VM or independently administered compute is a candidate architecture only. No architecture is selected, available, priced, installed, or proven by this report.
A separate host with management credentials reachable by the original authorities would also fail the stated requirement.

## Comparison with the eight packet requirements

| Requirement | Design status |
| --- | --- |
| Independent resources/authority | Required; no exact resource selected or approved. |
| Enforced two-way isolation | Required; no verification result is claimed. |
| Independent authenticated route | Required; no provisioning or authentication result claimed. |
| Candidate and synthetic scope | Candidate remains pinned above; real server/Bridge/ContextRegistry with synthetic Hermes and stub Codex/Hands proposed; no activation. |
| Complete new-plan ownership inventory | Required; conceptual map above is not a deployed inventory. |
| Contract compatibility | Existing gates remain in force. Any normative scope/gate change requires a separate §14 amendment before action. |
| Preflight and control handoff | Required in a separately reviewed executable plan; not performed. |
| Separate acceptance evidence | Not collected. PR #80 remains draft/HOLD; no retroactive PASS. |

## Design outcome and remaining input

No evidence published in this report establishes a ready environment. Setup and activation remain HOLD.
Further design requires an operator-nominated compute/management boundary and authorization for the scoped information needed to assess it. No resource nomination is inferred from option ข.
Prefer evaluating a suitable existing resource before considering new expenditure; no cost ranking is established.
If complete ownership separation and contract compatibility cannot be proven, defer this acceptance path. Do not relax §23, infer cessation, clear a registry, or change the old stop/switch scope to make a candidate fit.
Any later feasibility evidence, executable plan, provisioning, connector/secret handling and acceptance need their own review and explicit scope.
This report grants no local maintenance, historical disposition, runtime automation, release or deployment authority.
