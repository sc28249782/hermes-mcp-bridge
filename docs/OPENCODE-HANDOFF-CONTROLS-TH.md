# OpenCode handoff passive observation — preregistered controls

## Source-contract refinements — proposed, not run

The [snapshot/VFS contract](OPENCODE-HANDOFF-SNAPSHOT-CONTRACT.md) refines
OC03/04/07/08/09/15 with retained native descriptor identity, real standard-unix
read transactions, explicit SHARED-lock contention and denial of mutation/
secondary/recovery/WAL/SHM operations. No default Python SQLite or unsafe-copy fallback.

The [Facts/admission contract](OPENCODE-HANDOFF-FACTS-CONTRACT.md) refines
OC02/06/10/11/12/13/14/16/17, including current-versus-original binary proof,
pre-admitted non-null handoff-context association and non-caller-mintable admission.
Exact shim/runtime dependencies, authority schema/resolver, native identity and
original goal/verifier are implementation/acceptance obligations, not filled by
these proposals. All OC01–OC18 remain NOT RUN; no Dev/pilot action or original
control/assertion change. Review contracts before their bounded source package.


Date: 3 November 2026. Companion to the
[integration design](OPENCODE-HANDOFF-INTEGRATION-DESIGN-TH.md).
**DESIGN ONLY: controls executed=0; Dev/backend calls=0; pilot NOT AUTHORIZED.**

These are OC identifiers for this design, not S24 ledger rows, E checkpoints,
a new H01–H10 corpus or measured trial counts. Each future case needs exact source/
stimulus/receipt with provenance; early rejection cannot claim downstream coverage.

| ID | Required stimulus and assertion | Evidence lane |
|---|---|---|
| OC01 | Invalid/duplicate/oversized/schema/checksum checkpoint rejected before capture; no runtime constructor or Dev/state/output access; pinned schema reads are allowed | Offline source |
| OC02 | Missing/expired/revoked/wrong-generation current authority prevents even DB capture; authorization snapshot/checkpoint success bool cannot fill it | Offline source |
| OC03 | Physical shared-DB access not authorized but logical job ref valid => HOLD; no claim that column projection isolates underlying pages | Offline source |
| OC04 | Bound single job among unrelated pending/running rows, including identity-lost fixtures; all original rows/audit/files unchanged; no _reconcile/native status/result/recent invocation | Real SQLite fixture |
| OC05 | Constructor/from_config/health/submit/cancel/session continuation hooks raise if reached; no CLI/model/network process started by collector | Offline import/call audit |
| OC06 | Missing/foreign job/request/session/fingerprint/workspace/model/provider/binary/source binding rejects; IDs never guessed via recent/prose; no prompt decode/hash/export | Real native-schema fixture |
| OC07 | Mode/owner/nlink/symlink/reparse/existing destination/source-swap and DB schema drift reach actual I/O gates, fail without repair | Supported filesystem fixture |
| OC08 | WAL/SHM/hot-journal/concurrent writer/locking/truncated DB and unsafe immutable-read attempts reach supported capture controls; consistency and no unapproved source writes proved, otherwise HOLD | Real SQLite concurrency fixture |
| OC09 | Output append/truncation/replacement/invalid UTF-8/over-cap/partial page during capture fails; full exact bytes bound, no accepted prefix or replacement-decoded proof | Real file fixture |
| OC10 | Every native state preserved. pending/running/unknown_exit => restricted HOLD without liveness inference; failed/cancelled/permission_required cannot become done | Offline source |
| OC11 | No or closed/unresolved/drifted context binding, including null context_id, fails rather than constructing context_open=True or rebind/reopen | Trusted resolver fixture |
| OC12 | Completed + exit zero + reassuring text with absent/changed evidence or verifier rejection does not prove goal; every required evidence object verified independently | Verifier fixture |
| OC13 | Source/binary/model/provider identities bound and each mutated independently; raw caller Facts/Decision/verifier_passed/auth dictionary cannot construct trusted admission | Offline source |
| OC14 | Checkpoint CAS/head race, full-store rollback without independent anchor, and expiry/revocation between capture and receipt cause HOLD/no publish; no duplicate action or retry | Store/authority fixture |
| OC15 | Blocked helper/output/SQLite I/O, owner death and deadline enforce bounded failure; only owned helper signalled/reaped; unconfirmed stop reported honestly | Real owned process fixture |
| OC16 | Raw prompt/model output/fingerprint/IDs/paths/exception/credential sentinels absent from public receipt/audit; private retention/cleanup touches only new owned files | Privacy/ownership fixture |
| OC17 | One eligible original completed fixture job with independent accepted criterion produces advisory done only; authorizes_actions remains false and no native call/dispatch occurs | Joined local fixture, NOT Dev |
| OC18 | After six gates and separate finite approval: exact Dev original job, independently accepted evidence, no source DB/audit mutation or new CLI/model/session invocation, helper stop and bounded receipt | Actual Dev, NOT RUN |

All legacy OpenCode tests remain required, including durable idempotency/conflict,
owned session/model/workspace gates, unknown_exit, terminal immutability, cleanup/
cancellation race, output redaction and stdio discovery. Existing handoff 26 source
and 18 preparation controls stay unchanged. The prior 400 arm-trials remain frozen;
no retuning/re-run or automatic experiment job activation.

Source acceptance must include an explicit disposition for every OC row and the
six design gates. Source-only cases can be accepted at that scope while OC18 stays
NOT RUN, but they cannot label the actual Dev integration accepted. Unsupported
capture/context/ownership/goal semantics are blockers, not optional controls.
Record actual source/head/environment, count/no-skips/warnings and failures; no
assumed hash, clock-synchronization claim, waived assertion or widened timer.

After exact-source review the finite pilot proposal must name one bound original
job/evidence set, current authority and its expiry, trusted dossier/profile,
actors/argv/read-write inventory, absolute deadline/stop/retention and one-attempt
budget. No IDs/paths are supplied by this design. Pilot outcome may be supported
goal-verification snapshot, correct HOLD or inconclusive/stop-unconfirmed; none
authorizes submit/resume or establishes general recovery gain.

Privacy-safe source/result review precedes any public runtime/MCP/config change.
A new execution feature needs its own SPEC section-14 change control and release
scope. J0 stays PAUSED; #112 remains separate, R1 NOT AUTHORIZED / R2 HOLD.


## Offline source candidate — 3 November 2026

The [source-review packet](../acceptance/handoff/opencode/SOURCE-REVIEW.md)
adds a fixture-scoped retained-FD native VFS/helper, private batch owner,
fixture-only admission/Facts and exact-artifact verifier plus 48 owned source
controls. Original design/preregistration text above is historical and unchanged;
current per-row disposition is in that packet. This is not whole-integration
source acceptance: production authority/bindings, external-owner death/stop,
independent rollback anchor and original Dev goal gates remain OPEN. OC18 NOT RUN.
No Dev/pilot/merge, J0 resumption or R1/R2 authorization.
