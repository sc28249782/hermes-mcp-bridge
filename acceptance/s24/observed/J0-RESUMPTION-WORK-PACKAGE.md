# J0 resumption — one bounded artifact-policy work package

Date: 2 November 2026 (Asia/Bangkok).
Reviewed input: draft #112 at `84b1ec3e0149be847d4f9d57ff095e6c1c190991`.
Main after operator-authorized #116 merge:
`d7515c5fb4e33b41f81a8535fb06a0ea2cd72255`.
The offline handoff package is now merged through delivery 4;
[closure](https://github.com/sc28249782/hermes-mcp-bridge/blob/d7515c5fb4e33b41f81a8535fb06a0ea2cd72255/docs/HANDOFF-OFFLINE-CLOSURE-TH.md).
This resumes J0 **preparation/design review only**, not environment activation.

## 1. Scope selected for this work package

Operator approved the proposed sequence with “ดำเนินการตามเสนอได้”.
Exact approval timestamp: NOT_PROVIDED. That sequence was: merge #116, return to
#112, select one bounded blocker and prepare source/design for review without
provisioning or another invocation. It did not select route A/B/C or approve V2.

The selected blocker is **the artifact-policy disposition after BACKSLASH HOLD**,
not a general expansion of all eighteen controls. Deliverable: one review packet
that can settle the existing actual-result/design/route decision before source work.
No new E counter, test, parser change, live request or activation wrapper is added.

## 2. Evidence boundary and static source cross-check

[Attempt-four record](CATALOG-ATTEMPT-FOUR.md) /
[JSON](CATALOG-ATTEMPT-FOUR.json) records run `41213711915`, attempt 1,
job `124573771376`: FAILURE/exit 2, ARCHIVE_PARSE/PREDICATE_REJECTED/BACKSLASH.
This resumption reads the committed record; it does not claim a fresh archive
inspection or a new live-log audit. FOUR consumed invocations, THREE recorded
digest matches; E12 remains UNKNOWN. No full catalog or inspection receipt.

At the input head, author static checks recomputed the exact V1 bytes:

| Role | SHA256 |
|---|---|
| catalog_join_artifact.py | `cc170eef2afabce715d1b0cb47f39e6a35b330f22fdbbe09d5835cb4bbb8dfb5` |
| gate_artifact_catalog.py | `266ef06341db67c95c069846967733c3bbc0cb4910e9898e5a4966f194332182` |

In that exact producer, member_name() lines 176–186 checks literal backslash at
line 182; selected() lines 190–193 uses its fixed name allowlist/regex.
This explains the reviewed policy's rejection, not the actual rejected member,
raw header, intent, corruption, security, import or Windows-path compatibility.
No producer/gate was executed for this static check. Existing selected() and V1
BACKSLASH rejection remain unchanged. Catalog and diagnostic jobs stay disabled.

## 3. One decision packet, not another policy implementation

Review the unchanged [BACKSLASH disposition and V2 contract](CATALOG-BACKSLASH-DISPOSITION.md)
alongside the actual-result record. Its A/B/C alternatives remain explicit:

| Choice | Candidate disposition | Boundaries |
|---|---|---|
| A | Retain V1 and review another exact artifact/source | No alternate artifact nominated or automatically fetched |
| B | Review separate literal-name V2 catalog | Engineering recommendation only; NOT SELECTED; strict/V1 unchanged |
| C | Defer the selected CI route | Joined obligations remain OPEN; no operator-VM fallback or waiver |

B remains the recommended design for review because it concerns non-materialized
catalog strings and retains the fixed artifact and selected-file identity.
That is not a diagnosis of any actual member or a promise the next parser pass
succeeds. Review must explicitly address:

1. Backslash remains a literal catalog character, including apparent drive/UNC/
   parent-looking synthetic strings; never rewrite, resolve, join or materialize it.
2. Slash traversal, absolute names, duplicate normalization, control/type/device/
   sparse/resource/selected-entry rules stay fixed; no name/index exception.
3. Policy-prefix digest and evidence classes are distinct; cross-policy receipts
   reject. Public output discloses no non-selected member/path/device values.
4. Synthetic tar/hash/selector/privacy/negative controls must prove these predicates;
   no substitution for actual artifact EOF, import or the joined Windows route.
5. A future HOLD returns to route-or-defer. No automatic sixth invocation, timer
   widening, fallback or further parser-policy increment.

Independent result/design acceptance and explicit operator route selection remain
OPEN. This author packet does not self-approve the record or contract.

## 4. Finite exit and source-preparation handoff

This work package ends when the actual HOLD has an independent disposition,
the existing design has an independent verdict, and operator selects A/B/C.
The verdict may be acceptance, requested changes or explicit deferral; it need
not produce a passing archive. No inventory row closes from this decision alone.

Only if B is accepted and explicitly selected may the next source deliverable
implement the already bounded separate V2 producer/gate/offline controls.
Exact paths/argv/source SHA256 are UNBOUND until those files exist and are reviewed;
no invented pin or executable setup instruction is included here. Required source
review exit: actual hashes/loader pins, unchanged strict/V1 regressions, literal-name
digest/selector/privacy/cross-policy controls, supported-interpreter/no-skips/warning
gates and explicit remaining limitations. A disabled finite-action proposal comes
after source acceptance; any live fifth invocation needs separate operator approval.

## 5. Remaining path to the joined target

| Dependency | Current state after this preparation |
|---|---|
| Catalog policy/result/route decision | This one bounded work package; design/result review and route choice pending |
| Full archive catalog/selected-entry evidence | OPEN; partial counts/digest equality do not supply it |
| Kernel/boot/virtualization, guest binaries and exact setup/lifecycle | UNBOUND/NOT_TESTED; no WSL/import/setup action |
| Native Windows SSH → guest collect → CIM in the same window | NOT PROVED; E4/E6/E7 remain separate |
| Full outer ownership/deadline/stop/writer coverage | OPEN; CI teardown is not cessation proof |
| Private A6/A7 / complete source acceptance | OPEN; no private values published |

[Current eighteen-row ledger](R1-INTEGRATION.md#current-closure-ledger) and
[join plan](WINDOWS-LINUX-JOIN-PLAN.md) remain the acceptance authority.
All eighteen dispositions stay OPEN; A2/A3 are the target, not accepted outcomes.
J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD; #80/#96 and private bindings unchanged.
No #112 merge, guest provisioning, model/backend call, release or deployment.
The input #112 at 84b1ec3e predates the handoff work on main. The resumption
integration brings the reviewed main history into #112 without editing either
parent's source bytes; ROADMAP keeps both dated prefixes. This is integration,
not independent S24 acceptance, and does not authorize any live action.
