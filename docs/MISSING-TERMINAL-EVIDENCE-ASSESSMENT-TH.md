# Missing terminal record — initial SPEC §23 evidence assessment

Date: 22 October 2026.
Status: **HOLD — evidence floor not met; no case disposition**.
Assessment base: main `3f1aab78e3fbf77c17c02bbf43a327b5375a84b7` (PR #82 merge).
This is a documentary assessment of existing reports. It is not a fresh local inventory, a frozen private dossier, an approval record, or a maintenance plan.

## Review and merge checkpoint

PR #81 merged at `6af7c0b36f195cf0ff6a5009b8c68a1efbe662c3`.
The operator-supplied external review approved the PR #82 amendment at `87abd9583064c1b601472d71a4059fb558c7ee3b`.
After retarget to main, CI run `39787772426` passed at that same head on Python 3.12 and 3.14.
The author performed the final main-target §14 check. The operator then instructed, verbatim:

> merge ได้

That instruction followed the explicit request to merge #82. The chat message has no exact approval timestamp; none is invented here.
PR #82 merged at `3f1aab78e3fbf77c17c02bbf43a327b5375a84b7`.
The review/merge prerequisite has passed. This does not approve a case disposition, local maintenance, or an acceptance repeat.
The PROPOSED headings in the merged amendment retain its authoring-stage wording; this checkpoint records the later review/merge result without changing the normative requirements.

## Evidence sources and limits

- [PR #80](https://github.com/sc28249782/hermes-mcp-bridge/pull/80), pinned head `3a566bb39f425aece9ababd5e9d7429cade44fa9`: the blocked acceptance record and its diagnosis.
- [Decision packet](MISSING-TERMINAL-DISPOSITION-PROPOSAL-TH.md): the documented alternatives and design-scope approval.
- [SPEC §23](SPEC.md#23-missing-terminal-operational-disposition-proposed) and the [operations procedure](OPERATIONS-TH.md#missing-terminal-manual-disposition-proposed): the evidence and local approval requirements.

PR #80 reports 25 baseline Hermes registrations: 8 current-API terminal confirmations, 16 prior positive terminal observations, and one unresolved registration with cached running/current HTTP 404.
The 24 supported terminal observations do not establish cessation of the remaining execution.
The report states that the checked authority stores lack a matching row/tombstone. It does not establish when or why the records disappeared.
The present assessment reads these reports. It does not independently reopen the private receipts, verify their hashes or provenance, or make a current runtime claim.
PR #80 remains draft and HOLD; its record is not incorporated into main by this assessment.

## Evidence-floor comparison

| SPEC requirement | Existing reported evidence | Assessment / missing evidence |
| --- | --- | --- |
| §23.2(1): exact execution, authority generation, and maintenance target | Private diagnosis reportedly correlates one run/request. No exact maintenance plan is approved. | Incomplete. A case review must verify the private identity chain, authority generation, and target. Public aggregates cannot replace that chain. |
| §23.2(2): positive cessation under every capable authority | Cached running, current 404, and no matching authority row/tombstone in the checked stores. | Not met. Require an execution-bound retirement/revocation record or a verified lifetime-bounded contract with matching lifecycle evidence. Absence alone is insufficient. |
| §23.2(3): complete ownership and cessation of all writers | Earlier worker checks were reported. Complete coverage of child, detached, remote, and external writers was not established. | Not met. Require a source-backed execution/ownership map and matching cessation evidence for every reachable writer. PID absence alone is insufficient. |
| §23.2(4): no uncovered execution or recovery edge | Authority and writer coverage remain incomplete. | HOLD. No action may manufacture the missing evidence. |
| §23.2(5): provenance, observation times, source version, and limits | PR #80 records source-backed findings and private receipts; lost-record cause/time remain unknown. | Partial report only. A case review must verify the exact private references, digests, versions, times, and limits. Store sequence/start time cannot fill the gap. |
| §23.2(6): preserve original records and observations | PR #80 reports preserved evidence and no status rewrite, cancellation, replay, resubmission, or restart during diagnosis. | Reported preservation is retained. No new local verification is claimed in this assessment. |

Result: **the case is not eligible for `maintenance_only_unknown_outcome`**.
The task outcome stays unknown. No completed, failed, cancelled, successful recovery, absence-of-effects, or Hermes `unknown_exit` inference is made.

## Next evidence work and stop condition

1. Identify an existing source that can provide execution-bound positive authority cessation. Document the source and its limits before any further collection.
2. Establish the complete writer/ownership map from the exact execution contract and matching records. Review coverage before treating any process observation as sufficient.
3. If either evidence family is unavailable, retain HOLD and record that limitation. Repeating the same 404 probe does not satisfy either requirement.
4. Only after the evidence floor passes can a separate case review consider a frozen private dossier, an explicitly scoped maintenance plan, and live local-terminal approval under §23.3. This assessment supplies none of those records or approvals.

No Hermes task, new API probe, receipt rescan, process inventory, fixture activation, runtime restart, registry change, cancellation, replay, or resubmission was performed for this assessment.
No acceptance result is changed. The first attempt's missed preflight is not retroactively repaired.
Production/Dev were not inspected or changed in this step. Release, deployment, automation, and systemd work remain separate.


## Later source-capability check — 22 October 2026

This checkpoint follows the initial documentary assessment above. A completed Hermes control task inspected installed source and the existing private diagnosis receipt within the named backup directory. It did not repeat the missing-run API request or collect a new process inventory. The earlier no-Hermes/no-receipt-rescan statement describes the initial assessment stage only.

The local task reports a clean source checkout at `4e58c721c8cf9b51c46636ea84ea6a5cb540880a`. The following are maintainer-side source findings returned by that task, not an independent external audit or proof of loaded process code:

| Source reference reported by the local task | Observation | Consequence for this case |
| --- | --- | --- |
| `hermes_state_runtime.py:227,245-246,264,271,293,302-306` | Claim, settlement, cancellation, and steering-only requeue have distinct lifecycle paths. | These rules support the existing distinction between positive terminal evidence and unresolved work. They do not supply a retirement record for the missing execution. |
| `hermes_state_runtime.py:449-459`; `api_server_authority_runs.py:73,170` | Recovery does not replay started work; unresolved started work becomes unknown rather than an observed terminal outcome. Live worker adoption is a separate operation. | General recovery behavior does not establish cessation under every authority for this exact historical run. |
| `agent/managed_worker.py:156-166` | Owner-death handling targets the worker's own process group. Tools that open a separate session are outside that group. | Owner death or an empty group cannot prove complete child/detached/external-writer cessation. |

The task reused the prior diagnosis for the target's absent authority/idempotency/tombstone records. It found no new positive record matched to the target. This is a bounded-source result, not a claim that every possible store or backup was searched.
The process-group limit does not prove that this run spawned detached work. It shows why that mechanism alone cannot establish complete coverage.
No current or historical execution chain for this run was reconstructed to the standard required by §23.2(2)–(3).

A separate private source-capability receipt was saved with reported file mode 0600 in a 0700 directory. The task reports exact source references, file hashes, observation time, and separated observations/inferences in that receipt. The parent received only a truncated receipt digest; no full-digest verification or frozen-dossier claim is made here. Private paths and run/request identities are omitted from this public record.

Result remains **HOLD**. Neither positive cessation of every capable authority nor complete writer coverage has been demonstrated. Do not prepare this report as an approval-ready dossier or request local maintenance approval on its basis.
Reopen the case only when a distinct, execution-bound evidence source becomes available. Further identical 404 checks, age checks, or process-absence checks cannot repair these gaps.
No maintenance or acceptance repeat was performed. The control task wrote its private evidence receipt and normal task bookkeeping; this is not a claim of zero production-state writes.
