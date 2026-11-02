# Literal-name catalog V2 — exact-source candidate for review

Date: 2 November 2026. Input #112:
`87d0b6cd9b5ee458009512abb807239e08ab3215`.
Status: **SOURCE CANDIDATE / OFFLINE CONTROLS ONLY — NO LIVE ACTION**.
No new E counter. Existing [literal-name design](CATALOG-BACKSLASH-DISPOSITION.md)
and [bounded work package](J0-RESUMPTION-WORK-PACKAGE.md) remain the contract.

## 1. Operator choice and scope

After the operator-supplied round-21 APPROVE of the resumption/decision packet,
the operator replied “ดำเนินการตามที่แนะนำได้” to recommendation B.
Exact approval timestamp: NOT_PROVIDED. This selects B **for preparing separate
V2 producer/gate/offline controls and exact-source review**. It is not source
acceptance, a fifth invocation, setup/provisioning, merge or R1/R2 approval.
Earlier NOT SELECTED statements describe their named prior checkpoints.

## 2. Exact source bindings

| Role / path in this directory | SHA256 |
|---|---|
| catalog_join_artifact_literal.py | `16d1953d2094281d39c328dd54bada15de6be3e1b3f84cbddf8b69acbf39fc90` |
| gate_artifact_catalog_literal.py | `f7cf5136f8aaedecbe640fe960e0ae4f7c9fe5b7daf9f5992e410830ad53d4ba` |
| test_artifact_catalog_literal.py | `b91c78c8427c1d752c79aa38b677e3252bbf6198ea6da4656231e634d9655e39` |

Producer's distinct argv is
`--download-and-catalog-literal-metadata`; gate retains its bounded log-path /
producer-exit interface. These are source interface bindings, not commands to run.
No workflow step invokes this producer CLI against the provider.
The only new CI step runs the offline unittest entry, with an exact 46-test /
OK / no-skips / post-exit warning gate.

Fixed policy: `ROOTFS_METADATA_CATALOG_V2_LITERAL_NAMES`.
Distinct result/diagnostic/gate classes:
`j0-rootfs-literal-metadata-catalog-only`,
`j0-literal-metadata-catalog-diagnostic-only`,
`j0-literal-metadata-catalog-gate-only`,
`j0-literal-metadata-catalog-gate-hold`.
Fallback diagnostic has its own literal-lane unavailable class and remains
unacceptable as a completed checked receipt.

## 3. Narrow implementation delta and unchanged boundaries

The new producer is a separately named copy of reviewed V1. Author AST comparison,
normalizing only fixed policy/class/argv strings and removing the single V1
BACKSLASH predicate, finds the rest of the producer identical. The new gate's
whole AST is identical to V1 after normalizing only policy/evidence-class strings.
This is an implementation-scope check, not evidence of a provider member.

Backslash stays one literal catalog character. No replacement, unescaping,
filesystem normalization or path materialization. Apparent drive/UNC/parent
strings are synthetic catalog data, not path authority. Existing leading ./,
trailing slash, slash-component, root/control/duplicate/type/device/sparse/
selected/resource predicates and their order remain the same. BACKSLASH remains
in the closed 21-reason vocabulary for schema stability, not a new V2 rejection.

The selector is unchanged. Only admitted selected REGULAR TarInfo objects reach
extractfile for a bounded content hash; no decoded member name is opened as a path.
Non-selected names/device values remain aggregate-hash-only; selected links remain
unresolved metadata, not executable proof. V2 hash starts with its own policy prefix.
V1/strict keep their original bytes and reject the same backslash-bearing fixture.

Fixed provider URL/digest/receipt pins, CI-only guard, no proxy/redirect/retry/
fallback, hash-before-parser, TemporaryFile cleanup, 120 s / 512 MiB / no core and
all archive/member/logical/selected/name/link limits remain unchanged.
No new service, privilege, host/guest actor, timer widening or operational stop claim.
The new gate retains strict key sets, two-frame/byte/marker/duplicate/nonfinite
checks, six-class count/cross-frame rules, false flags and failure exit 2.
Cross-policy success/HOLD frames and mixed class/policy combinations reject.

## 4. Meaningful controls and substitutions

Local Python 3.12.14, ResourceWarning-as-error:
**46/46 OK** in the new offline entry; unchanged V1 **36/36 OK** and original
strict artifact **13/13 OK**. These are local checks; exact-head CI is separate.

The 46 tests comprise 14 literal-lane controls, 22 applicable methods from a private
copy of unchanged V1 controls, and 10 applicable methods from a private E11 copy.
They use real synthetic tar/hash/parser/gate paths; header faults, HTTP faults and
main's provider digest/receipt/network/process limits are explicitly substituted.
No actual provider download, resource-limit change, guest/import or device operation.

Three V1 methods intentionally assert old name rejection, old evidence class or
old success argv; these are not rebound to V2. New literal-name, frame/class and
main controls cover those changed contracts. E11's original special-file,
one-line main and backslash traversal methods are not rebound; V2 tests cover
six classes, two-frame main and all unchanged slash rejection predicates.
**No original test file/assertion is changed, removed or skipped**: all original
36 V1 and 13 E11 tests still run in their unchanged CI steps. Applicability lists
have exact expected inventories; they are not unittest skip mechanisms.

New controls specifically prove literal/slash distinction and canonical policy
digest; aliases still duplicate; slash/control/root rejection; no non-selected
content/member-path operation; fixed-selector near-match rejection; V1/strict
same-tar BACKSLASH rejection; cross-policy success/HOLD rejection; offline main
success/failure and argv/CI guards; unchanged critical functions/budgets; output
privacy; unresolved literal links/device metadata without reads.
Existing inherited controls retain six-class/device/sparse/collision/cap/HTTP
cleanup/fallback/framing/false-flag/error/count checks.

## 5. Preserved evidence, finite exit and next boundary

FOUR actual invocations remain consumed; THREE recorded full digest matches;
E12 UNKNOWN. Attempt four remains HOLD/BACKSLASH with partial counts.
No provider archive was read in this delta and no actual result is relabelled V2.
Strict/V1 sources/tests, prior actual records, selectors and both catalog/diagnostic
job false guards stay unchanged; handoff experiment jobs also stay disabled.
CI changes only by adding the offline literal unittest step.

Exit for this source candidate: independent exact-source/hash/control review plus
exact-head Python 3.12/3.14 count/no-skips/warning evidence, with no blocking finding.
After that, a separately reviewed **disabled** finite-action wrapper/proposal
would precede any separately approved fifth invocation. No such wrapper or selector
is introduced here. A future HOLD returns to route-or-defer, not automatic policy
increments or a sixth invocation. No completed V2 receipt or J0 readiness is claimed.

All eighteen acceptance rows stay OPEN; joined Windows/native-SSH/collect/CIM,
kernel/boot/guest/setup/ownership/deadline/stop and private A6/A7 remain unclosed.
Same draft #112, no merge. J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD; #80/#96 unchanged.
