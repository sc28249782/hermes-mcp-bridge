# OpenCode source contract — current admission, context and Facts

Date: 3 November 2026. Input #117 `7fb2088f`.
**CONTRACT CANDIDATE / NOT IMPLEMENTED / NO CURRENT DEV FACTS OBSERVED.**
Companion: [snapshot contract](OPENCODE-HANDOFF-SNAPSHOT-CONTRACT.md).

## 1. Independent inputs and typed internal construction

The source-reviewed owner receives one current finite operator authorization
through a protected local authority resolver, independently of checkpoint bytes.
It resolves an already reviewed immutable task dossier with one original job,
goal/profile/evidence set and private identity mapping. Public input can name
only opaque references; it cannot supply arbitrary paths, SQL, models, caller
Facts, context_open, verifier_passed, approval snapshots or executable callbacks.
The existing planner remains pure and authorizes_actions=false in all outcomes.

Proposed internal records are Admission, Dossier, NativeSnapshot, ContextObservation,
CurrentIdentity and VerifiedEvidence. Names specify source interfaces, not new
effective runtime classes or serialized bearer tokens. Only the closed owner/
collector/verifier call graph may construct their trusted instances, from the
exact captured bytes and independently admitted handles. Type checks alone do
not resist malicious same-process/same-uid code; host/operator-owned resolver,
accepted sources and protected mappings are the explicit trust boundary.

No crypto/tool bootstrap is introduced or borrowed from #112. Actual authority
format/issuer/transport, source hashes, private refs/paths, original IDs and actual
Dev identity remain UNBOUND. Implementation must supply a closed schema, resolver
and threat assumptions before source acceptance; a file named approval is not
authority merely because it is owner-only or checksum-valid.

Admission binds exact Dev/source/interpreter/state/repo/workspace/job/session/
request/fingerprint/model/provider/binary/context/goal/profile identities, read
and optional new-output scope, physical shared DB access, read-lock contention
permission, expiry/revocation/generation, byte/time/attempt/stop/retention limits.
No implicit backend/network/submit/cancel/resume/permission or context mutation.

## 2. Current model/binary evidence versus historical invocation

| Field | Trusted source and comparison | Forbidden inference |
|---|---|---|
| Job/request/session | One exact native row, exact admitted dossier IDs, no recent/heuristic search | No guessed/replacement ID or foreign session |
| Input fingerprint | Protected pre-existing native value and reference mapping; private comparison only | No prompt read/recompute/new public fingerprint |
| Workspace | Reviewed resolver's canonical retained identity and native row; repo/head/dirty manifest bindings | A path string alone does not prove same worktree or sandbox |
| Model/provider | Exact native model string versus admitted canonical model/provider mapping and current allowed policy | Model name from checkpoint, old fixture or provider prefix alone is insufficient |
| Current binary | Dossier-resolved regular owned file/handle, exact permitted path identity and actual current digest/source/dependency profile | No health/version execution; current file digest is not original-run digest |
| Current config/policy | Independently resolved approved non-secret projection and generation, not native constructor | No entire secret-bearing config dump/hash in public receipts |
| Original invocation binary/source | Existing independently accepted original-run evidence if required by the locked goal/profile | Native jobs schema records binary PATH, not its execution-time content hash |

Current binary validation reads only under its own explicit file scope; no CLI,
plugin, wrapper, --version or provider execution. Unsupported script/interpreter/
dependency closure is UNBOUND/HOLD, not solved by executing it. No permission repair.

If original executable/source provenance is a criterion, missing original-run
evidence gives HOLD. Reading today's binary or matching its path cannot backfill
that evidence. If the accepted profile verifies only current exact artifact
properties, state that limited as-of goal explicitly and make no original-binary
provenance claim. Do not alter the original goal/profile to obtain a pass after
seeing its output; the profile is independently locked before observation.

## 3. Context association without native rebind

Source inspection of contexts.py at the pinned baseline shows context rows for
Hermes/Codex metadata; there is no OpenCode job/session binding column. Native
OpenCode rows likewise have no context_id. Therefore do not pretend such a native
association already exists or instantiate ContextRegistry (constructor creates
schema/chmods). Do not call its mutation/wrapper methods during observation.

The selected narrow contract requires a NON-NULL existing open handoff context
and a separately reviewed dossier association of that context with the exact
OpenCode original job. This association must be admitted before observation
authorization. It is metadata in the task dossier, not a new native backend
binding, registry write or checkpoint-derived assertion. If no such association
can be supplied, HOLD; this profile does not support “context not applicable”.

Read only exact context_id/closed metadata from the current contexts DB using
the same reviewed snapshot mechanism, with separate physical-file authority.
No label/session history or unrelated row is returned. Observe open state before
target/evidence capture and again immediately before advisory receipt admission;
a missing/closed/mismatched/unreadable context HOLDs and never becomes True.
No context creation/reopen/readback-driven rebind or automatic new context.

Each context/authority observation is individually coherent, not a cross-DB atomic
snapshot. Under accepted no-rollback/closed-is-irreversible semantics the checks
support that limited observation interval; a whole-store rollback or unsupported
external generation anchor invalidates that reasoning and HOLDs. The source must
bind its fresh owner/admission epoch and rollback limits, not inherit checkpoint
created_at/generation as a trusted external freshness anchor. Later handoff always
revalidates, and the current observation grants no continuing action authority.

## 4. Admission sequence and planner mapping

One observation attempt contains bounded pre/post validations, not a poll/retry:
1. Validate envelope/schema/checksum, original store head and dossier/profile.
   Permit the existing pinned-schema read; no Dev files or runtime constructors.
2. Obtain current authority/epoch; verify physical-file and read-lock scope,
   exact Dev/current identity/model/config/repo/workspace mappings and context
   pre-observation. Invalid/unknown authority stops before DB/result capture.
3. Capture one native target row. Unknown ID/mapping HOLD/JOB_ID_UNKNOWN.
   Preserve pending/running/unknown_exit as reported states but return restricted
   HOLD/RECONCILIATION_REQUIRED; do not test stored PIDs or reconcile.
   Failed/cancelled/permission_required remain native facts, never goal success.
4. For an admitted completed row with INTEGER exit_code=0, capture exactly the
   bound full evidence bytes and invoke only the independent locked verifier.
   Missing/changing evidence or rejection HOLDs; no callback supplied by input.
5. Recheck context/authority/epoch, store head, paths/handles and current identity
   before publishing. Expiry/revocation/clock anomaly/changed head rejects without
   retry or preserving a formerly successful verdict.
6. Construct Facts internally: job/request/session/fingerprint/workspace from the
   compared snapshot; repository/head/dossier/current authority from their trusted
   records; context_open=True only from accepted association and current reads;
   required_evidence and verifier_passed only from the independent verifier.
   Then call existing plan, keeping Decision and checkpoint authority false.

Any provider/model/binary/context field not represented in the old Facts/schema
must already have passed owner admission; no silent extension or default. Source
must prove every Facts-construction path uses all those checks. A generic
dictionary-to-Facts conversion is prohibited. Done is a bounded goal-verification
snapshot, not native resume, action permission, restored session or all-process
cessation. Failure/unknown labels are not new OpenCode backend statuses.

Private NativeSnapshot/Admission may include sensitive native IDs/comparison
values but never prompts or raw credential fields; they are not public receipts.
Public receipt is an allowlisted opaque-ref/native-state/advisory-reason summary,
with only approved source/evidence commitments. Do not publish source DB/config/
row/fingerprint hashes as a shortcut: they may commit to sensitive shared data.

## 5. Source/control acceptance boundary

Refines OC02/06/10/11/12/13/14/16/17. Required real fixtures:
- Wrong or expired authority before capture, revocation after capture, epoch/head/
  repo/model/provider/binary/context drift, plus independent mutation of every
  comparison field; assert downstream readers/verifier/planner are not reached.
- Legacy native row without original binary digest cannot satisfy a profile that
  requires it. A current matching executable must not cause a false historical pass.
- Missing/null/foreign/closed context and absent dossier association cannot mint
  context_open=True. Context creation/reopen/rebind hooks fail if called.
- Independent verifier rejects completed/exit-zero/reassuring text without exact
  original goal evidence; forged serialized Facts/booleans never enter admission.
- One supported joined fixture creates only advisory done, authorizes_actions=false;
  observed helper stop, native state and goal proof stay distinct.
No such controls have run in this contract delta; no source acceptance is claimed.

After contract review, the next source package implements the selected VFS/owner/
resolver/verifier and these fixtures together; no extra generic proposal layer is
required to start that bounded source work. Actual Dev/private bindings and pilot
OC18 remain NOT RUN/NOT AUTHORIZED until the six gates and separate finite action
approval. Unimplementable capture/authority/context/original-goal requirements must
be reported as blockers/infeasibility, not waived or silently redirected.
J0 PAUSED; #112/#80/#96/private bindings unchanged; R1 NOT AUTHORIZED / R2 HOLD.
