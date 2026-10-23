# SPEC §24 Phase A — candidate input decision

Date: 23 October 2026.
Status: **PROPOSAL — no input substitution or guest action authorized by this packet**.
Plan: [S22-SHAREDHOST-20261023-01](S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md).
Artifact: [reviewed source](../acceptance/s24/README.md), PR #88 head `4179631d13046fb4da5b6ebcba5209cb24eee201`.
This packet is stacked on PR #89 head `ef02f1abc458f514341509f2f37bebc1dd31e2ae`; merge #89 first, retarget this packet to main, and require exact-head CI before its merge.

## 1. Evidence and remaining gate

The operator approved A only in the earlier chat; this packet records no new approval or exact approval timestamp.
Operator-reported guest results on Python 3.14.4 at original input `71dcae67cbfa6f0b953ab8d81198d073d202ed2a`:
- Full suite: 234 tests OK, exit 0.
- Focused section 22: 7 tests OK, exit 0, followed by two unclosed-database ResourceWarnings.
- Artifact: 10 tests OK, exit 0.
- A tracemalloc diagnostic attributed the two allocations to the synthetic Codex job-store connections in the focused test, at original lines 262 and 273.

The finalizer warnings remain evidence even though the test process returned zero. Neither that run nor the warning-enabled diagnostic establishes a clean ResourceWarning gate or guest readiness.
The operator-supplied independent review approved PR #89 at `ef02f1a`. That review covers the test repair, not an input substitution, corrected guest result, or approval to merge.
Its CI run `39955551059` passed on Python 3.12/3.14. This is not CI for the proposed input below.

## 2. Proposed exact input

| Item | Immutable identity |
| --- | --- |
| Original input / sole parent | `71dcae67cbfa6f0b953ab8d81198d073d202ed2a` |
| Proposed input commit | `d3144cc48437011830533ba0d4606b8d4644be3a` |
| Proposed tree | `4b3a27e7d5f72589b02de69a45c1302144718d12` |
| Changed path | `tests/test_context_binding_unresolved.py` |
| Replacement blob, identical to reviewed PR #89 | `c9fae04df337699a679cbf994401c875428cc234` |

The proposed input is a separate review input commit, not a new release, stamp or replacement main branch. Fetch by full commit SHA; its branch name is not an immutable input.
The source comparison is one test file, +3/-3: import closing and wrap both connections with closing while retaining transaction contexts.
Runtime, other tests/assertions, dependencies, stamp, schema and tracked file modes are unchanged. The proposed tree has 104 blobs; no fixture artifact or newer main documentation is imported.
The input commit was materialized for source review only. It has not been installed or run in the guest, and no fresh CI/full-suite result at that commit is claimed.

## 3. Operator choices after review

- **ก — recommended:** select the exact proposed input for a later source/manifest preparation PR. That PR must append a scoped input checkpoint to the plan, preserve the original history, update the artifact PIN and the one changed entry in its 104-file manifest, and update the dedicated CI input. Review all coupled pin references and artifact checks together. Do not change normative SPEC behavior or assertions.
- **ข — defer:** retain the original input and evidence. Phase A remains incomplete; no warning waiver or readiness PASS.

The recommendation limits the candidate difference to the reviewed test cleanup. Using current main would add unrelated files and is not proposed.
Neither option is selected by authoring, review or merge of this packet. No operator selection or timestamp is invented.

## 4. Sequence and execution boundary

1. Merge PR #89 only on explicit operator order. Retarget/review this packet and pass exact-head CI before its separately ordered merge.
2. Obtain an explicit input decision. Choice ก authorizes preparation of the coupled source/manifest PR only; that PR requires independent review and a separate merge order.
3. After that review, bind the exact revised artifact/input and obtain explicit scope to use them in the already approved A-only guest preparation. Preserve the original checkout, logs and warning trace; use a new private candidate/evidence location. No manual test overlay or manifest bypass is permitted.
4. Revalidate resource, time, identity and continuity gates. Run the full suite, focused section 22 and artifact checks again on the exact new input; record exits, skips, warnings and dependency identity. Inspect captured stderr through interpreter shutdown: exit zero alone is insufficient for finalizer warnings. A missing observation, warning or failure keeps readiness HOLD.
5. Produce the private 0600 readiness receipt only from observed evidence. Resource-monitoring coverage and unfilled B bindings must be explicit; a missing resource observation cannot be replaced by test success.

This packet changes no effective pin or manifest. It creates no guest readiness PASS, live acceptance or historical disposition.
Phase B, PR #80 and all original stop/switch gates remain HOLD/unchanged. No connector, credential, production/Dev change, release or deployment is authorized.

<a id="s24-input-option-a-selection"></a>

## Operator selection checkpoint — 23 October 2026

After this packet merged at `686973b5240e30b8f9e5d274f75e918e0af5b76c`, the operator's complete response was:

> ก

This selects option ก above for coupled source/manifest PR preparation only. No exact approval timestamp is available; none is invented. This later checkpoint was not in the packet head `8f05802` covered by its prior review; the historical proposal text remains unchanged.
The [plan checkpoint](S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md#s24-revised-input-preparation) and revised artifact prepare input `d3144cc48437011830533ba0d4606b8d4644be3a`. Review/merge of this coupled preparation and explicit revised guest execution scope remain separate. No guest pin/checkout/manifest is changed by recording this selection. Phase A remains incomplete; B and PR #80 remain HOLD.
