# PR117: kernel pidfd birth-result feasibility (PB02/PB03 PARTIAL)

## 1. Checkpoint and scope

Parent `2e89221ca58f3cbe2343d1a6bd795cfdcc8bf513` received operator-supplied
round-17 APPROVE AS FEASIBILITY EVIDENCE. This records that supplied review,
not a GitHub review submission. No review timestamp was supplied or invented.
This new source candidate requires independent exact-source review.

The previous package used fork followed by pidfd_open. This package tests real
Linux x86_64 clone3(CLONE_PIDFD): kernel copyout into a preallocated E-owned
pidfd slot, with no pidfd_open or alternate primitive fallback. It does not select
a production primitive, implement the full broker or make SPEC §14 effective.
All old source/tests/workflows/manifests/contracts remain byte-unchanged.

Round-17 clarification against actual previous results: R loss after H fork but
before result storage did permit E's own result binding/cleanup without relay.
Injected pidfd failure recorded helper_created=true with unknown binding; commit
fault after retained pidfd recorded known binding/cleanup-only, not unknown H.
The supplied `-V`/`WSIGCHLD` suggestion was ambiguous and is not assigned invented
semantics. This package instead records concrete SIGCHLD and waitid evidence.

## 2. Files and fixed actors

- [Owned C fixture](../acceptance/handoff/opencode/atomic_birth_probe.c)
- [Sixteen controls](../acceptance/handoff/opencode/test_atomic_birth.py)
- [Source/dependency pins](../acceptance/handoff/opencode/atomic-birth-hashes.json)
- [Offline CI](../.github/workflows/opencode_atomic_birth.yml)

B launches one fresh inert C E per case. E directly creates only R and H, both
with clone3(CLONE_PIDFD) and SIGCHLD, with no shared VM/files/thread flags.
Three fixture actors E/R/H plus B are counted; no O/S or hidden watchdog actor.
R ignores TERM and waits. H redirects actual stdin/stdout/stderr to fixture pipes,
announces readiness on a separate bounded pipe, and either waits for gate EOF,
exits early or remains nonreading for the two lost-slot controls. E never sends G.
This C fixture is not the SQLite/OpenCode native helper, CLI or protected capture.
No Facts/Owner/Batch/planner/verifier/backend/model/network invocation exists.

Numeric clone return values are correlation only, never stop/reap targets. Named
cases discard that numeric return while retaining the kernel-written pidfd slot.
All candidate signals use pidfd_send_signal after exact P_PIDFD child eligibility;
all exact reaps use P_PIDFD. There is no numeric-PID/PGID signal, scan, pidfd_open,
legacy clone/fork fallback, retry, respawn, arbitrary target or helper executable.
P_ALL occurs once only as a test no-children oracle expecting ECHILD; it does not
consume status, discover targets or repair candidate cleanup.

## 3. Preregistered stimuli and actual local outcomes

Expected outcomes were asserted separately from actual records. Local final run:
16/16 OK, Python 3.12.14, umask 022, ResourceWarning-as-error, no skips.
There are 14 isolated process cases, one source policy check and one manifest check.
Strict cc C11/Wall/Wextra/Werror/O2 compilation succeeded. This count is not PB
acceptance or evidence that all kernel interruption schedules have been exercised.

| Cases | Expected / observed local evidence |
| --- | --- |
| normal; forget_pid | Kernel pidfd copyout observed; discarded numeric return still permits exact reap and both EOFs |
| r_loss; r_loss_forget_pid | Real SIGKILL of R after H readiness; E cleans its own H without R relay |
| signal_flag | Real nonthrowing SIGUSR1 handler after syscall return; slot survives; numeric return discarded |
| early_exit | Exited H observed twice with WNOWAIT, consumed once; subsequent ECHILD; zero helper signals |
| repeat_slot | Same slot rejects reuse before third clone syscall; no replacement H |
| bad_copyout | Real invalid copyout address yields EFAULT; candidate conservatively unknown creation and no cleanup proof |
| fd_exhaustion | Actual E-local FD exhaustion yields clone3 EMFILE; candidate unknown, no retry/fallback |
| erase_copyout; close_copyout | Kernel copyout first observed, then slot erased/closed; H live, candidate UNKNOWN and no EOF/reap proof |
| sigchld_ignore; sigchld_nocldwait | Actual sigaction readback rejects before any child creation |
| deadline_guard | Actually expired T0 rejects before children; exit 6 expected, not an in-budget success |

Local classification: 11 SUPPORTED kernel cases, zero UNSUPPORTED, three
NOT_PROBED preflight cases. All cases end with test no_children=true. Real EFAULT
and EMFILE observations do not prove that a child existed before those errors or
that all interrupted copyout/creator-side schedules are safe. signal_flag raises
SIGUSR1 only after clone3 returned, not while the kernel creates the child.

Both lost-slot cases retain an extra duplicate diagnostic pidfd before fault.
Candidate result is frozen before diagnostic cleanup; live H is independently
checked through that extra handle, then exact reap/EOF is obtained. memcmp checks
candidate result did not change. The duplicate and erased original FD record are
test-only capabilities, not a production recovery method or isolation guarantee.
These cases preserve the counterexample: successful kernel copyout alone does not
protect user-space slot metadata against later erasure, close or creator failure.

SIGCHLD is set and read back inside fresh E, rejecting SIG_IGN/SA_NOCLDWAIT.
waitid(P_PIDFD, WNOWAIT) is repeated with matching pid/code/status, followed by one
consuming wait and ECHILD. ECHILD alone is not treated as a receipt. This verifies
these fixture conditions only, not deployment signal policy or concurrent reapers.

## 4. Bounds, availability and evidence handling

B supplies monotonic T0 before E launch; E locks Ta before R creation. Integer
nanoseconds give D=min(Ta+8 s,T0+45 s), a stricter subset of min(Ta+20,T0+45).
Creation/readiness cutoff is D−3 s. Cleanup waits TERM≤0.2 s and KILL≤1 s are
shared across known actors and clamped to the same D. Remaining alarm/poll units
round inward; no fault, loss, reap or diagnostic starts a new attempt budget.
B asserts actual subprocess completion/reap before T0+8 s; expired-T0 negative
case separately asserts rejection. These observations are not hard real-time or
uninterruptible-kernel-I/O guarantees. Signal/stop/reap/EOF remain distinct facts.
Per-actor limits: RLIMIT_AS 256 MiB, core=0, NOFILE=64. E's bounded pipe reads use
stdout≤64 KiB/stderr≤4 KiB; emitted closed JSON≤4096 B. Caps are not aggregate RSS
or approved deployment budget; B/host overhead and B6 remain unbound.

If clone3 is unavailable/denied, the first R attempt reports UNSUPPORTED with no
fallback, no exercised kernel case and no positive binding/cleanup claim. The
harness may pass classification assertions; CI reports supported/unsupported
counts separately. Such a green harness run is not positive primitive coverage.
The three preflight cases are NOT_PROBED, not silently included in supported count.
Build hashes and machine/kernel metadata are fixture evidence, not source-to-launch
attestation. No raw PIDs/fds/T0/native/private paths or credential values are logged.

Development history: initial strict compile caught misleading indentation; fixed
before tests. Initial test execution lacked the not-yet-generated new manifest;
that run was not a final pass. The final run above includes matching pins. Historical
broad local baseline NOT PASS remains unchanged; no broad local rerun is claimed.
First published head c5649b4b passed local16 and CI3.12 but CI3.14 failed the
expired-T0 case: negative monotonic origin input was read by strtoull and rejected
as malformed (exit2 instead of expected budget rejection exit6). The fix uses
signed integer nanoseconds/strtoll, with deterministic negative expired-T0 regression; assertions and 8/20/45/3 budgets are unchanged.
This failed first-head run is not relabeled as a pass.
CI at the final new commit must be recorded separately in the PR body; old CI is not
relabeled as evidence for this source. Warning gates concern component logs, not
third-party Actions deprecation notices.

## 5. Disposition and next boundary

PB02/PB03 remain PARTIAL. This tests kernel-written pidfd slot vs discarded numeric
return and concrete error/slot-loss controls; it does not prove full atomicity,
creator-side crash/interruption safety, complete four-role ledger, full broker
channels/arbitration, E loss containment, deployment ABI/security policy or original
goal/Facts join. PB01/04–11 full obligations NOT RUN; no EC/OA row closes.
OA07 accepted external-profile obligation and OA12 remain NOT RUN; B1–B7 OPEN,
B4 OPEN. Registry-only profile remains infeasible; no replacement profile selected.
All records set full_atomicity_proven/production_feasible/profile_selected/
capture_allowed/authorizes_actions/dev_observed/goal_verified=false.

Keep draft/unmerged, J0 PAUSED (#112 at e7142cf7), OC18 NOT RUN,
R1 NOT AUTHORIZED / R2 HOLD. No Dev/pilot/original invocation, private binding,
service/cgroup/VM installation, credential/config action, checkpoint or release.
Any future full broker integration needs its named PB obligations and SPEC §14
approval; this evidence package does not grant those capabilities. Next source
review must assess the residual creator-state/failure-domain proof before promotion.

Primary interface references (background, not machine/deployment evidence):
[clone3 and CLONE_PIDFD](https://www.man7.org/linux/man-pages/man2/clone.2.html),
[waitid/P_PIDFD/WNOWAIT](https://www.man7.org/linux/man-pages/man2/waitpid.2.html),
[pidfd conditions](https://www.man7.org/linux/man-pages/man2/pidfd_open.2.html).
