# PR117: owned offline cell/view primitive subset

## 1. Checkpoint / scope

Parent 299045fe474c75196665887d760e567587defdc1 received operator-supplied
round-20 APPROVE AS DESIGN, not a capability grant/effective amendment. This records
supplied review, not GitHub submission; no timestamp invented. New source awaits
independent exact-source review. [Contract](OPENCODE-HANDOFF-SLOT-METADATA-CONTRACT-TH.md)
and [atomic birth evidence](OPENCODE-HANDOFF-ATOMIC-BIRTH-REVIEW-TH.md) remain unchanged.

This package implements an isolated fixture model only: B launches fresh C E;
E directly creates exactly one inert H by clone3(CLONE_PIDFD), with one retained
pidfd and no alternate birth/handle fallback. No R/O/S, full broker, issuer, external
anchor, actual native SQLite helper, CLI, Facts/Batch/planner/verifier/backend or G.
E/H=2 fixture actors plus B; this is not the five-role production topology.

- [C fixture](../acceptance/handoff/opencode/cell_view_probe.c)
- [Controls](../acceptance/handoff/opencode/test_cell_view.py)
- [Pins](../acceptance/handoff/opencode/cell-view-hashes.json)
- [CI](../.github/workflows/opencode_cell_view.yml)

## 2. Implemented model and boundaries

Capability cell holds the sole kernel pidfd, creator PID correlation, consumed/
closed/revoked/reaped bits and a fixed admission tuple. View holds marker, fixed
slot/version and tuple. Attempt/generation/source/role/FD-map/deadlines are compared
as a complete initialized tuple against E's local fixture admission. Source=17 is
a fixture token, NOT an executable hash, authenticated issuer or source attestation.
Same-address-space tuple comparison is not protection against arbitrary corruption,
malicious same-uid code, ABA/FD replacement or changes to both admission and cell.

Creation consumes the sole slot before syscall; no replay/second child. Closed
startup gate prevents work. Initial publication validates complete fields; named
fault modes omit publication, corrupt a field before marker or publish stale generation.
These are synchronous source fault injections, NOT asynchronous interruption or
hardware atomicity proof. Commit marker alone is insufficient. Accepted rebuild
copies only a view from the intact cell, once (second invocation is rejected before
copy), within the original cutoff. It does not allocate/duplicate/reacquire a pidfd.

Wrong generation rejects restore and the fixture conservatively revokes the attempt
before candidate cleanup; revoked/corrupt proof likewise denies candidate target
operations. That local revocation is a fixture action, not production authority.
Bound-unpublished H remains cleanup-eligible only through intact fixture cell proof;
publication rejection never grants G. All outcomes retain state UNKNOWN, including
positive cleanup/rebuild cases. No FINAL, goal, Done or FAIL is reconstructed.

## 3. Actual stimuli and limits

| Cases | Expected outcome / observed local result |
| --- | --- |
| normal | Sole bound H exact reap/EOF; no capture or goal claim |
| view_erased | Actual memset view to zero; rebuild validated tuple from existing cell; cleanup-only |
| restore_twice | First rebuild succeeds, second invocation denied; only one clone operation |
| before_publish | No valid initial publication; intact cell cleanup-only |
| partial_publish | Marker with wrong source field rejected; no valid initial publication |
| stale_publish | Old generation rejected; intact cell cleanup-only |
| wrong_generation; revoked | Restore rejected; candidate target calls zero, no reap/EOF proof; diagnostic separate |
| cell_corrupt | Actual cell source field corruption plus erased view; candidate remains unknown/no cleanup |
| closed_handle; closed_reused | H exact-reaped FIRST, then actual pidfd close; latter dup2s unrelated owned pipe onto same number and verifies pipe I/O; no subsequent candidate target call |
| deadline_guard | Actual negative expired T0 rejected before child; expected exit6 |

**SM04 limitation**: actual handle close/FD reuse occurs AFTER H was already exact
reaped. This proves rejection of a deliberately invalidated closed cell even when
that number now names a real pipe. It does NOT prove cleanup after losing a live
H handle, detect an unreported close/reuse, or reject a substituted live child pidfd.
Live-loss experiment is NOT RUN: it would require a separately reviewed safe
cleanup protocol; no backup handle or numeric target repair is silently introduced.

**SM05 limitation**: the cell proof field is corrupted while its original FD field
and kernel handle remain intact. Three negative cases use TEST-ONLY cleanup on
that SAME handle after candidate result freeze; no second handle, pidfd_open,
SCM_RIGHTS/pidfd_getfd, host scan or cell repair. The live-H observation, exact
reap and subsequent EOF are separate diagnostic fields; memcmp confirms frozen
candidate facts unchanged. This diagnostic bypass of failed fixture proof is NOT
available production authority and never changes candidate cleanup_confirmed=false.
Full cell erasure/FD-field corruption, actual lost copyout and E death are NOT RUN
here; old atomic erase/close controls remain prior separate evidence, not new passes.

The candidate_target counter (post_fault_target_calls in output) counts admission
to candidate_cleanup's target path; guarded invalid cases never enter it. It is
not a syscall trace or count of diagnostic wait/poll/signal operations. Source
policy audit and the closed fixture path complement this limited instrumentation.

## 4. Bounds / evidence

Signed exact integer ns: T0 before E launch, Ta before H create,
D=min(Ta+8s,T0+45s) is a stricter subset of min(Ta+20,T0+45); rebuild cutoff D−3s.
Candidate cleanup uses remaining D (not cutoff), preserving the reserve. TERM≤0.2s,
KILL≤1s phases clamp to same D, including diagnostic; no fresh restore/cleanup budget.
E alarm uses remaining original outer; H alarm uses remaining D. B asserts elapsed
subprocess completion/reap<8s; expired negative case separately expects rejection.
This is not hard real-time/uninterruptible-I/O/deployment proof. E/H per-actor
RLIMIT_AS256MiB/core0/NOFILE64; caps are not aggregate RSS/B6 proof. B overhead
unbound. Reads stdout≤64KiB/stderr≤4KiB; closed JSON≤4096bytes. No raw PID/fd/T0,
private paths/IDs/prompt/output/config/credentials in public record.

P_PIDFD/retained original handle is the sole exact child signal/reap path, with
SIGCHLD set/readback, WNOWAIT twice, consuming wait and ECHILD separately checked.
Numeric clone return is never retained as target. P_ALL occurs once in E as test
no_children oracle only; isolated E's own waitable children after diagnostic cleanup,
not host census, no-orphans proof or E-loss containment. B waits/reaps its exact E.
Unsupported clone3 yields UNSUPPORTED at first create without fallback, not positive
primitive coverage. CI reports supported and unsupported counts separately from
passing classification tests; deadline preflight is NOT_PROBED.

Local final suite: 14 tests (12 process cases + source-policy + manifest), Python
3.12.14, umask022, ResourceWarning-as-error/no skips. Strict cc C11/Wall/Wextra/
Werror/O2 compilation. Actual final elapsed/count and exact-head CI go in PR body.
Development strict compile initially caught one unused inherited notice function;
removed before final run. No failed/intermediate run is claimed as final pass.
All prior sources/tests/manifests/workflows/contracts unchanged; broad local
baseline NOT PASS remains unchanged, no broad local rerun claimed.

## 5. Disposition / next boundary

| Obligation | Current scope / disposition |
| --- | --- |
| SM02 | PARTIAL: erased-view same-E tuple rebuild and bounded cleanup-only in one-H fixture |
| SM03 | PARTIAL: named synchronous pre-publication/tuple/marker faults; no async atomic commit proof |
| SM04 | PARTIAL: actual post-reap close/pipe reuse only; live H loss/substituted pidfd NOT RUN |
| SM05 | PARTIAL: corrupted source proof/erased view with intact sole handle and separate diagnostic; full cell/FD loss NOT RUN |
| SM01, SM06–SM12 | Full obligations NOT RUN; local negative inputs do not close these rows |
| PB02/PB03 | PARTIAL unchanged; no full PB/EC/OA acceptance |
| B4 / B1–B7 | OPEN; aggregate budgets/current authority/rollback/E containment unproven |
| OA07/OA12 | NOT RUN full obligations |

All records production_feasible/profile_selected/capture_allowed/authorizes_actions/
dev_observed/goal_verified/full_atomicity_proven=false. The six private overlay
labels do not change any public state/status/schema. No actual grant/resolver/profile,
SPEC amendment, production restore or joined receipt integration is selected.
SPEC §14 remains prerequisite before security-boundary/persistence/status integration
merge; acceptance of a fixture does not make the proposed contract effective.
Next review must assess those partial limits before any expansion. Where proof
requires a backup/extra actor/handle reacquisition, report infeasible/HOLD or propose
separate authority boundary; do not label test cleanup as production recovery.

Keep draft/unmerged; J0 PAUSED (#112 e7142cf7); OC18 NOT RUN;
R1 NOT AUTHORIZED / R2 HOLD. No Dev/pilot/original invocation, service/cgroup/VM,
credential/config/checkpoint/archive/release/deployment. Design/source/CI acceptance
is not action authorization. Current source candidate independent review=PENDING.
