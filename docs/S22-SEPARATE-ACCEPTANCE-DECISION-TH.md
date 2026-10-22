# SPEC §22 — separate acceptance environment decision packet

Date: 22 October 2026.
Status: **PROPOSAL — no option selected; no setup or acceptance authorized**.
Base: main `de773eceda598b522a8a7e4b45aabcfef6dddb54` (PR #83 merge).

## Problem and retained boundaries

The [evidence assessment](MISSING-TERMINAL-EVIDENCE-ASSESSMENT-TH.md) found no sufficient positive authority cessation or complete writer coverage for the historical unresolved run.
PR #80 remains draft and HOLD. Its first attempt's missed preflight remains part of the record.
Do not repeat the same 404/age/process-absence checks without a distinct evidence source.
The existing Dev stop/switch plan remains blocked. This packet does not adjudicate the run or approve a disposition under [SPEC §23](SPEC.md#23-missing-terminal-operational-disposition-proposed).

## Operator choices

| Choice | Scope | Tradeoff |
| --- | --- | --- |
| ก — defer acceptance | Keep the current HOLD and take no setup action. Reopen only on new execution-bound evidence. | No new environment cost; §22 remains unreleased and without completed scoped acceptance. |
| ข — authorize feasibility design only (recommended) | Review whether a separate disposable environment can support a new §22 synthetic acceptance without stopping, reconfiguring, or using the existing production/Dev runtimes or their state. | May permit independent progress, but requires demonstrated isolation, a reviewed new plan, and separate setup/activation approval. Feasibility may fail. |

The recommendation is to investigate a new resource boundary, not to treat the historical run as terminal or harmless.
Choosing ข approves design only. It does not approve a particular VM/container, cost, credentials, connector, configuration, execution command, setup, maintenance, acceptance run, release, or deployment.
Merging this packet selects neither choice. No operator quote or approval timestamp is recorded because no specific choice has been made.

## Feasibility requirements for choice ข

A later design must establish all of the following before proposing an executable plan:

1. **Independent resources and authority.** Identify the disposable environment, test owner, candidate tree, fixture state, profile, logs, ports, and connector route. No original registry, authority store, runtime, credential profile, or backup is copied, reset, reclassified, or silently replaced. A new empty registry does not resolve old ownership.
2. **Enforced isolation.** A new directory, Python virtual environment, process group, or same-user profile is not sufficient. Evaluate a disposable VM or an equivalently enforced boundary. Demonstrate that historical authorities/writers cannot reach test resources and that the test cannot reach production/Dev control surfaces, storage, or credentials. Check mounts, host integration, shared directories, sockets, networking, and inherited secrets. If any relevant access remains unproved, HOLD.
3. **A viable authenticated test route.** The new route must be independently identified and must not reuse or retarget the production/Dev tunnel/profile. Any tunnel or connector provisioning requires a separate explicit scope. Restricted network access must still support the required authenticated test route. Do not assume that an available local port creates a Work-chat connector.
4. **Candidate and stimulus scope.** Use the reviewed runtime at PR #79 merge `71dcae67cbfa6f0b953ab8d81198d073d202ed2a`, or separately verify and review a replacement input. Use real candidate server/Bridge/ContextRegistry paths with synthetic Hermes transport and stub Codex/Hands. No real model task, Codex approval, native execution, or new MCP tool is part of the proposed stimulus.
5. **Complete new-plan ownership inventory.** Enumerate every backend, authority, controller, worker, writer, and shared resource in the proposed test scope. Prove the boundary from the historical execution rather than excluding it by name or by using an empty state directory. Record why each original resource remains untouched. A reviewer must reject an unproved dependency or ownership edge.
6. **Contract compatibility review.** Existing maintenance/quiescence gates remain in force. Determine whether the new plan is compatible with SPEC and previously approved plans. If it changes a normative requirement or the authorized meaning of the maintenance scope, submit and merge a §14 amendment first. This packet grants no exemption from full inventory or §23 evidence.
7. **Preflight and control handoff.** Define fresh full preflight, exact process/start identities, finite controller lifetime, scoped quiescence, private snapshots, and cleanup/restore verification. A control job must finish or hand off before its dependent process stops. Do not use this packet as authority to stop either original runtime or any unresolved execution.
8. **Separate acceptance evidence.** Define the live matrix, row-state assertions, backend call counts, receipt provenance, identity checks, and original-runtime continuity checks. Label mock-backend observations separately from unit, local SDK, raw tunnel, native, and production evidence. A completed new run would have its own record; it would not retroactively make PR #80 PASS.

These are unverified design requirements. No available machine, isolation product, access rule, connector route, or installed capability is claimed to meet them.

## Proposed decision sequence

1. External review and operator choice of this packet.
2. If ข is selected, produce a feasibility report and exact resource/authority map. Stop at HOLD if isolation or contract compatibility cannot be demonstrated.
3. Review a separate executable setup/acceptance plan and any required §14 amendment. Record explicit operator scope before provisioning, connector changes, or activation.
4. Only after those gates pass may the authorized setup and a fresh acceptance attempt be considered. Verify all required preflight gates immediately before that attempt.
5. Keep PR #80 and the historical task outcome unchanged. Review any new acceptance record independently. Release/deployment remain separate decisions.

## Work performed for this packet

Read GitHub PR metadata and the merged SPEC/operations text. PR #83 is merged at the base above; PR #80 is still draft and unmerged.
No Hermes task, private evidence rescan, status probe, source/runtime test, isolation setup, environment creation, tunnel/connector change, state copy, maintenance, or acceptance was performed.
This packet contains no executable setup commands and claims no feasibility result.
