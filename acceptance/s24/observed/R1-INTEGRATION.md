# R1 observer integration — consolidated source-acceptance work package

Status: **DRAFT / INCOMPLETE — NO SOURCE ACCEPTANCE OR EXECUTION AUTHORITY**.
Base: main `93e9601f74b3e0bc1d963d65635d82f7083eca8a` (merged #110/#111).
Delivery criteria: [A1–A5](../../../docs/S24-DELIVERY-CLOSURE-TH.md).
This is the continuing integration PR, not a request to merge another small
control increment. Keep it draft until the blocker ledger is reviewed and closed.

## Evidence types and added integration paths

| ID | Source / scope | What it does not prove |
| --- | --- | --- |
| E0 | Existing `test_observation.py`, 43 controls, unchanged | Existing mock/fixture limits remain; no operator observations |
| E1 | `test_r1_integration.py`: all 22 unchanged baseline helper tests, hash-checked, rebound to the observed helper with a recording boundary sink | Input hashes/system reads remain synthetic test injections; sink is not a real marker pipe or host sampler |
| E2 | Same module: actual controller CLI → owned worker → actual collect → missing-input failure, real marker pipe, trace and HOLD receipt | No successful inventory, wrapper/host sampler or real private inputs; no manufactured observation window |
| E3 | `Test-WindowsIntegration.ps1`: ten mandatory CI checks: private ACL admission, before/during/after pinned sampler+CIM, broad ACL and junction rejection, bad phase/schema/config ACL/module pin rejection | CI machine only; no SSH, operator machine, cross-machine causal sample, production timeout/stop coverage or host authentication |

E1 supplies the new required observation argument only in its test module; it
does not edit original tests or either helper. It checks entry/leaving order on
every invocation, including rejected inputs. Baseline hash pins remain unchanged.
E2 does not mock source loading, identity, pidfd, marker writes, collect, result
verification or cleanup. Missing runtime-key input is intentional; no key exists.
It requires one bound/entered/failed-leaving sequence, no inventory result file,
worker exit 2/reap, EOF, false scope flags and a hash-matched HOLD receipt.
It rejects incoherent procfs before launching; the control stays mandatory in CI.
E3 creates ACLs only on new disposable test files. Production ACL validators
remain validation-only. Its twenty-second test I/O deadline is not proof of the
production three-second sample-child budget or an extension of that budget.
All old tests and warning gates remain. Linux suite: 43 + 22 + 1 = 66; Windows:
14 offline + 9 process + 10 integration checks, each independently enforced.

## A1 — disposition ledger for all eighteen design groups

Every row below remains PARTIAL/OPEN until independent exact-source/evidence
review supplies the stated disposition. Coverage does not mean acceptance.
References to E1–E3 require passing exact-head CI; local failure/unrun evidence
must not be silently replaced. No required row is made optional by this ledger.

| # | Existing/new evidence | Remaining R1 blocking obligation / requested disposition |
| --- | --- | --- |
| 1 | E0 real no-G + protocol no-entry | Review integrated worker/host failure path before sample permission |
| 2 | E0 bound-only rejection; E2 real admission | Real wrapper/host observation must reject before actual collect entry |
| 3 | E0 local pipe handshake; E3 actual CI sampler | Join real collect boundaries with host sample invocation through bound carrier; reject outside-window samples |
| 4 | E0 real pidfd exit + injected UID/argv; E2 real worker | Actual UID/exec/PID reuse obligations remain unproved; evidence or explicit reviewer disposition under approved contract required |
| 5 | E0 false-liveness/fast-completion; E2 failed collect | Real worker exit during host sample and post-check must HOLD without retry |
| 6 | E0 atomically buffered leaving rejection | Actual host/worker scheduling and post-drain race coverage still needed |
| 7 | E0 real full/short/closed pipe fatal exits | Preserve fatal behavior in combined path; no success without boundary |
| 8 | E0 return/exception/fatal finally; E1 boundary checks; E2 real failure | Review combined normal/exception/fatal path coverage and limitations |
| 9 | E0 parser/pipe/local handshake | Bound actual transport framing, EOF/oversize/flood behavior end to end |
| 10 | E0 wrong/duplicate post; E3 local sample correlation | Actual carrier must reject changed correlation/worker identity; no authentication claim from digest |
| 11 | E0 host rules; E3 pinned CIM sampler | Missing/slow/low/corrupt provider injection through host coordinator; no false PASS |
| 12 | E0 disposable child + EOF; E2 actual worker reap/EOF | Actual transport cancellation/adoption/stop matrix and confirmation still open |
| 13 | E0 parser/output budgets/alarms | Blocked provider/output/start and independently effective deadline/stop tests remain |
| 14 | E0 private-log fsync faults; E1 record faults | Wrapper/host logging failure injection and partial-evidence retention end to end |
| 15 | E0 no-ACK marker + fast-run fixture; E2 unmodified real collect failure | Real fast inventory may HOLD; never delay production worker or enlarge timers to force sampling |
| 16 | E0 AST/flags; E1 all 22 baseline regressions; E2 receipt flags | Review regression adapter scope and combined receipt/source/false-flag enforcement |
| 17 | E0 real adoption; E2 real controller/worker/pipe/failure receipt | Coherent-Linux wrapper/host joined execution remains open; no complete-chain success claim |
| 18 | E0 unchanged offline runner; E3 separate CI-only CIM step | Review offline/live separation; bind operator host/control later in private packet |

## A2–A5 — remaining implementation and review gates

| Gate | Current state and required next deliverable |
| --- | --- |
| A2 worker/window/sample integration | E2 connects controller+worker+collect on a real failure path; E3 runs actual sampler separately. Joining them through the reviewed wrapper/host carrier with correct sample boundaries remains OPEN |
| A3 host transport/failure/ACL/stop | E3 adds real ACL/CIM checks, not coordinator/SSH integration. Exact carrier/framing, provider/output blockage, log failures, deadline and stop confirmation remain OPEN |
| A4 identity/regression | E1 reuses the complete baseline helper suite; E0 identity tests retain disclosed injections. Actual transitions/reuse and full wrapper handling remain OPEN pending evidence/review disposition |
| A5 immutable package/source acceptance | Production Python/PowerShell/loader pin bytes unchanged. New tests/workflow/docs require exact-head CI + reviewer acceptance; no source-acceptance PASS is issued here |

Before further code, bind each proposed change to a ledger row and its acceptance
predicate. Continue source and controls on this draft integration PR. Do not
split by test count, call separate CI sampling a during-inventory proof, close
rows from design approval alone, or use an unreviewed actor/stop fallback.
The private A6/A7 binding and scope review gates remain separate and unfilled;
their values do not belong in this public package. Unknown operator values are
not inferred from CI and do not authorize a probe to collect them.

## Acceptance and operational boundaries

This draft supplies evidence for review, not disposition of the ledger. An
independent reviewer must assess every row, remaining blockers and exact source
package. Normative changes require the existing §14 procedure; no waiver occurs
through a table edit. If host/transport capability cannot be implemented within
the approved design, stop and present that concrete gap for design disposition.
R1 PENDING_BINDINGS / NOT AUTHORIZED; R2 HOLD. No VM/SSH/operator CIM or key action,
Phase B acceptance, #80/#96 disposition, release or deployment is performed.
