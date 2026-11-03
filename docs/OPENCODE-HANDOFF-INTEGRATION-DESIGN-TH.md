# OpenCode handoff integration — passive observation v0.1 design

Date: 3 November 2026 (Asia/Bangkok). Base main
`d7515c5fb4e33b41f81a8535fb06a0ea2cd72255` (merged through #116).
**DESIGN / SOURCE-REVIEW CANDIDATE; NO DEV OR BACKEND EXECUTION.**

## 1. Explicit selection and finite delivery

After J0 pause-record review, the operator selected this separate work verbatim:
> เลือกให้เริ่ม OpenCode integration design ชุดนี้ได้

Exact approval timestamp: NOT_PROVIDED. The date records this document, not an
invented approval time. Scope: OpenCode integration design/source analysis only,
on a separate draft PR based on main. No pilot, health/status/result/reconcile,
submit/cancel/resume, model/provider, filesystem inventory of Dev, MCP/config
change, implementation merge or release is authorized. No OpenAI/provider API key
or runtime credentials are needed or accessed for this design.

J0 stays PAUSED on draft [#112 at e7142cf7](https://github.com/sc28249782/hermes-mcp-bridge/blob/e7142cf71792475af9375140df39acd55944d8d1/acceptance/s24/observed/J0-ROUTE-PAUSE.md).
This design is independent of its unmerged source and seed/tool prerequisites.
It neither resumes that route nor closes any S24 row; R1 NOT AUTHORIZED / R2 HOLD.

Proposed first implementation: one internal, non-dispatching passive collector
for ONE explicitly bound existing OpenCode job, an admission wrapper producing
trusted Facts only after current authority/binding checks, and an independent
artifact verifier. It feeds the existing pure advisory planner. No public MCP
tool, bridge dispatcher, polling/replay scheduler or backend-write capability.

First pilot, if later separately approved, is observation/verification of ONE
known existing completed job and its bound evidence. It creates no OpenCode job,
session or model turn. Unknown job ID, active/uncertain native state or unsupported
snapshot semantics ends HOLD; it is not a recovery-by-resubmission trial.
No claim of runtime recovery gain follows from one observation.

## 2. Pinned current source and consequences

[Source evidence](examples/opencode-handoff-source-evidence.json) records actual
SHA256 of six inspected baseline files and exact SPEC revision. These are repository
source pins, not identities of installed Dev binaries, state or live capabilities.
No AGENTS.md blob exists in the inspected base tree; project/chat instructions apply.

| Source at the pinned base | Finding | Design consequence |
|---|---|---|
| opencode_tasks.py:57–116 | Enabled constructor validates binary/workspaces, creates/chmods state/log directories and DB, initializes audit and schema | Do not instantiate OpenCodeTasks or load it via from_config for collection |
| opencode_tasks.py:158–165 | _reconcile scans ALL pending/running rows; after grace, lost worker identity writes unknown_exit and audit | A single-job observation grant cannot authorize this global mutation |
| opencode_tasks.py:249–255 | status starts BEGIN IMMEDIATE and _reconcile BEFORE target row lookup | Even an unknown target can trigger other-row changes; no call from collector |
| opencode_tasks.py:257–271 | result calls status, then reads bounded raw output with UTF-8 replacement/character pagination | Not a pure read; page assembly is not independent full-byte artifact proof |
| opencode_tasks.py:289–295 | recent also begins a write transaction and reconciles | Do not discover job IDs through recent or prose/prompt matching |
| opencode_tasks.py:175–220 | submit does durable request/fingerprint admission; session continuation is also submit and creates a new job | Preserve existing native contract; no new request ID, retry or continuation in this profile |
| opencode_tasks.py:273–287 | cancel reconciles globally, then edits pending state or running cancel_flag | No cancel or stored-PID signalling; observational HOLD never triggers cancellation |
| opencode_worker.py:81–92,95–232 | Direct-parent worker owns cleanup and terminal commit; completed is native response/exit evidence | Metadata is a reported lifecycle fact, not independent goal or all-process cessation proof |
| checkpoint.py:153–263 | Facts is supplied externally; plan is advisory and always authorizes_actions=false | Production provenance/admission must be outside the existing planner |
| Existing checkpoint schema | Backend has no model/binary identity field; Facts does not enforce them | Bind model/binary/provider in a trusted external dossier before Facts construction; no silent schema extension |

SPEC sections 14,18,21,22,24 remain authoritative. Existing methods and read
annotations are not changed by this attachment. It records their actual side
effects, not a defect verdict or a waiver. A future runtime/privacy/authority
interface must follow section 14 before implementation merge. Native statuses
and terminal immutability remain unchanged; no dependency on event subscription.

## 3. Proposed data flow and current authority

Proposed sequence: validate checkpoint/store head and reviewed dossier -> resolve
CURRENT authority and exact Dev/job identities -> gate passive capture -> obtain
one consistent target-row snapshot and exact bound evidence bytes -> independent
goal verification -> construct Facts in trusted code -> pure plan -> private
bounded advisory receipt. Revalidate head/authority/bindings before publishing;
expiry/revocation/changed generation discards the result, never retries.

Checkpoint/Decision/output text cannot authorize the capture, approve a tool,
supply credentials, choose a file path or mint trusted Facts. A caller dictionary,
caller verifier_passed=true or serialized Facts is not an admissible authority.
Python dataclass/type privacy alone is not a hostile same-process security boundary.
Trusted implementation/closed call graph, private resolver and controlled host
remain assumptions; external caller input may only name reviewed opaque references.

Authority must explicitly bind the physical private state-file access as well as
the single logical target. SQLite may read pages containing other jobs/prompt
bytes even when SELECT projects only allowed columns. Do not claim byte-level
single-row isolation or absence of prompt bytes from the SQLite process memory.
The source must never select/deserialize prompt text into application data, echo
fingerprints, hash prompt material anew, or export the whole database.

The checkpoint's scope_handoff_observe is necessary but not sufficient. A proposed
admission record must separately permit exact state/evidence reads and any NEW
private receipt/checkpoint write, with owner, expiry, revocation/generation and
byte/attempt limits. These are future internal capabilities, not new effective
MCP scopes. Actual authority format/resolver and live values are UNBOUND.

## 4. Identity, capture and native uncertainty

Require an already known job_id, request_id, bridge-owned session, protected
existing fingerprint reference, canonical workspace, exact model/provider and
binary/source/config identities. Compare the protected original native record to
the dossier, not checkpoint claims alone. Do not recompute prompt fingerprints,
accept a foreign session, infer ownership by PID or mint replacement IDs.
A missing ID/mapping produces HOLD/JOB_ID_UNKNOWN. No request-ID replay in v0.1.

Choose a separate passive database reader; do not call native task methods, health,
contexts wrappers with unknown effects or private _row helpers. Exact schema,
journal/locking and retained-file identity must be reviewed in its source.
Requirement: consistent SQLite read snapshot, no source row/schema/journal/audit/
permission changes, and bounded physical DB access. Proposed SELECT is an exact
whitelist for the bound target, excluding prompt and raw output fields.
Only protected comparisons may access the existing fingerprint; public receipts
use its opaque reference, never the raw digest.

A mode=ro URI or query_only pragma alone is not proof of safe/no-write capture:
WAL/SHM, hot journals, symlink/path races, SQLite schema features and concurrent
writers must be handled explicitly. Do NOT use immutable=1 on a changing live DB,
copy live DB bytes and assume consistency, create a full prompt-bearing backup,
or repair permissions/recover a journal. The concrete supported SQLite/filesystem
capture method is a source-acceptance blocker. If safe capture cannot be proved,
HOLD/SOURCE_CAPTURE_UNAVAILABLE (proposed adapter-only reason), no fallback.
This document does not claim a capture algorithm has already met these conditions.

Output/evidence: resolve only exact dossier-bound private objects beneath retained
trusted directories; no arbitrary checkpoint/log_path dereference. Require regular
single-link owned files, no-follow/owner/mode/size/source identity checks, full
bounded byte capture and before/after bindings. Changing/truncated/incomplete
output yields HOLD, never a stable prefix accepted as complete. UTF-8 replacement
or result pages cannot substitute for exact-byte verification. A stable hash
pair alone does not prove global quiescence, producer ownership or full-store
rollback resistance.

Preserve all seven OpenCode native states exactly. v0.1 positive eligibility
requires a bound completed row with integer exit_code=0 plus full independent
criteria/evidence verification; permission_required/failed/cancelled never become
goal success. pending/running/unknown_exit are retained as reported native states
but yield HOLD/RECONCILIATION_REQUIRED in this restricted observer profile.
Do not call _reconcile, wait for a worker to finish, poll, signal or declare an
unobserved worker alive/dead. Unknown_exit remains unresolved.

Context-open policy is also a blocker: native OpenCode rows have no context_id,
whereas planner Facts requires context_open. The trusted dossier/resolver must
supply the approved handoff/context association and current registry semantics;
never default True for null/missing context or auto-bind/reopen native contexts.
If no compatible association can be specified, HOLD; no planner/schema patch
inside this profile to fabricate eligibility.

## 5. Goal verifier and receipt semantics

Before any pilot, lock one independent acceptance profile for the original job:
goal/criteria refs, exact evidence objects and expected kind/content/size/hash
properties, verifier source/version and rejection semantics. No model-generated
summary, native completed flag, exit zero, response text or checkpoint verdict
is its own success oracle. A profile that cannot prove its original goal HOLDs;
do not invent a convenient new goal after observing the output.

Trusted collector/verifier constructs Facts only after provider/model/binary,
workspace/repo/head, job/request/session/fingerprint, current authority/context
and evidence checks. Facts construction is not a public API. The existing
Decision remains advisory, with authorizes_actions=false even for done.
A done result means a goal-verification snapshot for this exact dossier/evidence,
not resumed work, operational recovery, native permission approval or cessation
of every process. Next handoff must revalidate freshness and evidence again.

Native lifecycle, verified goal, owned-helper stop confirmation and action
authority are four separate receipt fields/concepts. No source amendment assigns
new backend terminal states. Proposed public receipt is metadata-only: opaque
refs, exact source/evidence commitments, counts, native state, advisory outcome
and bounded reason. Raw prompt/output, model prose, raw native IDs/paths/config,
fingerprint digest, exception text and credentials stay out of public/audit output.
Full permitted evidence remains private, bounded, with separate retention/cleanup
authority. A checksum is not authentication or a store rollback anchor.

## 6. Actors, budgets and stop boundary — proposals, not measurements

Initial source target is Linux/WSL2 private POSIX storage only; native Windows,
DrvFS and operator-specific paths are not assumed supported. Do not reuse the
S24 guest/bootstrap actors or any unmerged #112 implementation.

| Proposed actor/resource | Bound and authority |
|---|---|
| Private observation helper | One owned child, fixed reviewed argv/source/interpreter, <=20 s absolute monotonic deadline including capture/verifier, <=256 MiB memory; no network/model/CLI subprocess |
| Outer source-reviewed owner | <=45 s total, starts first; TERM/KILL/reap only its provably retained direct helper, no stored backend PID/PGID signalling |
| State/evidence | DB physical read cap proposed 64 MiB; native output <= row configured cap and <=8 MiB; additional profile evidence <=8 MiB total; metadata <=64 KiB/depth16 |
| Attempts | One capture + one verification, zero polling/replay/submit/cancel/resume/approval/health calls; unknown execution consumes the future observation scope |
| New owned output | Only separately approved private receipt/checkpoint destination; 0700/0600, exclusive creation/no permission repair; optional checkpoint commit retains existing CAS semantics |
| Stop evidence | Confirm the observer helper by retained ownership and reap; cannot claim to own or have stopped the original OpenCode worker/provider |

Bounds require enforcement source and positive feasibility evidence. They do not
modify existing worker runtime/output/cleanup timers or assert current Dev fits.
No widening, worker delay/SIGSTOP, retry or sandbox claim from workspace allowlists.
Native OpenCode still runs unsandboxed when separately used; this design starts
no OpenCode process and changes no native config/permissions.

## 7. Six gates before a finite Dev observation proposal

| Gate from offline closure | Binding required / status |
|---|---|
| 1. Backend/Dev identity | Exact Dev endpoint/profile/process/source/interpreter, native contract and existing job/session identities; NOT OBSERVED / UNBOUND |
| 2. Current authority + Facts | Physical DB access, logical job/dossier/repo/workspace/model/provider/fingerprint/context and current expiry/revocation/rollback policy; UNBOUND |
| 3. Side-effect contract | No native calls; reviewed consistent/no-source-write SQLite and evidence capture method, full journal/locking/native identity controls; UNBOUND |
| 4. Ownership/resources | Exact actors/argv/private paths/retention/stop, memory/deadline/byte budgets and actual helper cessation proof; UNBOUND |
| 5. Independent verifier | Original goal/profile/evidence lock, exact verifier source, positive/negative oracle and scoped done semantics; UNBOUND |
| 6. Finite action | Exact accepted implementation/control receipts and one separately approved observation scope; NOT PROPOSED / NOT AUTHORIZED |

This design selects OpenCode only; it does not fill live bindings using remembered
ports/models/version strings or the old fixture receipts. The [control plan](OPENCODE-HANDOFF-CONTROLS-TH.md)
is preregistration, not executed evidence. Design exit: independent acceptance of
this narrow profile and explicit blockers. Next source package must resolve capture,
authority/context and verifier contracts, implement fixtures against real SQLite/
output bytes and preserve all baseline tests; no public runtime integration yet.
A later pilot requires all six gates and its own operator action approval.

Handoff offline deliveries 1–4 stay closed at offline scope; the measured
development/heldout tie and budgets/receipts stay frozen. This work supplies no
new gain/evaluation/release claim. J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD;
#112/#80/#96/private bindings unchanged. Latest recorded release/deployment remains
signed v1.2.8; no new version/date, production observation or implementation merge.
