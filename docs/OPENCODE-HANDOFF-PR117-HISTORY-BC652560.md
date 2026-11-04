## Observer package 4 — native O/S loss controls candidate

Head `bc6525608731128f6cd12d3d22630b1308e0c4c4`; parent `83aacfc10eb9fb2ddf704d1883eee07eb922e78e`
received operator-supplied round-10 APPROVE. This records supplied review, not a
GitHub review submission. New candidate awaits independent exact-source review.

[Source review packet / evidence and OA disposition](https://github.com/sc28249782/hermes-mcp-bridge/blob/bc6525608731128f6cd12d3d22630b1308e0c4c4/docs/OPENCODE-HANDOFF-NATIVE-LOSS-REVIEW-TH.md).

Adds eight actual native loss schedules: nonreading C process, live SQLite read
lock, first complete native frame, and all three completed frames before process
exit; each with back-to-back O→S and S→O retained-pidfd SIGKILL sends, no reap/wait
between sends. Before source R resumes, fixture harness confirms BOTH O/S exited
and H still alive. R then adopts/stops/reaps H using unchanged source protocol.
All eight remain UNKNOWN without FINAL despite confirmed reap/EOF/no children.
The phase pipe/barrier and C hooks are TEST ONLY, with four internal R/O/S/H
actors; no hidden watchdog, numeric-PID/PGID signal or host inventory. Native 1-s
alarm is retained in the read-lock schedule; budgets/assertions are not widened.

**Local native 44/44 OK**, Python 3.12.14, umask 022,
ResourceWarning-as-error/no skips. 42 actual process cases + manifest + AST audit.
Original 36 test methods and assertions are AST-identical. State bytes and parent
subreaper setting unchanged; new stimulus booleans confirm measured phase and
both-death/H-live conditions. All capture/action/Dev/goal flags remain false.

Round-10 whitespace fix included: observer_native.py differs by ONE terminal newline
byte only, identical AST/behavior; updated actual source hash. No C/header/startup/
preflight/supervision/baseline/schema/SPEC/receipt/guard change. Remote comparison:
**1 commit, 5 files +214/-8**; exactly four existing files touched plus new review
packet. All five tested Git blobs match published tree. Pins/links/whitespace checked.

OA06 gains PARTIAL named fixture evidence only; no OA/B row closed. Actual R death /
external containment and original goal/Facts join remain NOT RUN/UNBOUND.
Keep draft/unmerged; B1–B7 OPEN; J0 PAUSED (#112 same draft e7142cf7);
R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN. No Dev/pilot/backend/credential/model
invocation, checkpoint append, release or deployment. Historical broad local
baseline NOT PASS unchanged; no local broad rerun/pass claimed.

### Exact-head CI

All **9 workflows SUCCESS** at `bc6525608731128f6cd12d3d22630b1308e0c4c4`.
Inspected actual job logs for both interpreters:

| Workflow | Job IDs / observed test counts |
| --- | --- |
| [OpenCode observer preflight offline controls 41820705370](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41820705370) | preflight (3.12): 126542805337, **24 OK**; preflight (3.14): 126542805754, **24 OK** |
| [OpenCode observer startup offline controls 41820705344](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41820705344) | startup (3.12): 126542805463, **22 OK**; startup (3.14): 126542806062, **22 OK** |
| [OpenCode supervisor-loss offline controls 41820705270](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41820705270) | supervisor-loss (3.12): 126542805281, **9 OK**; supervisor-loss (3.14): 126542805580, **9 OK** |
| [Handoff evaluation preparation controls 41820705275](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41820705275) | preparation (3.12): 126542805311, **26+18 OK**; preparation (3.14): 126542805721, **26+18 OK** |
| [OpenCode B4 offline supervision controls 41820705319](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41820705319) | supervision (3.12): 126542804831, **29 OK**; supervision (3.14): 126542805616, **29 OK** |
| [OpenCode observer native offline controls 41820705572](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41820705572) | native (3.12): 126542806033, **44 OK**; native (3.14): 126542805488, **44 OK** |
| [Handoff offline source controls 41820705541](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41820705541) | offline (3.12): 126542805578, **26 OK**; offline (3.14): 126542805060, **26 OK** |
| [OpenCode passive observation source controls 41820705407](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41820705407) | source (3.12): 126542805483, **48 OK**; source (3.14): 126542806237, **48 OK** |
| [Tests 41820705333](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41820705333) | test (3.12): 126542805300, **1+234 OK**; test (3.14): 126542805741, **1+234 OK** |

Both native jobs: **44/44**, 42 process records, eight measured native O/S loss
records each. All eight phase_seen/both_exited/h_live_after_loss=true;
state UNKNOWN, original_final=false, R reap + both stream EOFs, no_children=true.
All 42 have capture/action/Dev/goal flags false. Component gates: exit=0,
complete_without_skips=true, warning_markers=[]. Preparation arms_executed=0;
heldout **126542807187** and development **126542807370** SKIPPED.
Tests: migration1 + baseline234 OK both versions. No broad local baseline pass
claimed; old local NOT PASS remains. Component warning gates do not assert all
third-party Actions deprecation warnings are absent. No new source acceptance,
OA closure, Dev/pilot or original-goal trial is claimed.


---

## Historical package 3 and earlier checkpoints

## Observer package 3 — owned offline native integration candidate

Head `83aacfc10eb9fb2ddf704d1883eee07eb922e78e`; accepted parent `8b41102ce9ed9a87a6df208ad6970f3381f90c6e`
received operator-supplied round-9 APPROVE for inert startup + exact-budget fix.
This records the supplied review, not a GitHub review submission. Candidate 3 awaits
independent exact-source review; fixture success is not source acceptance or action approval.

[Exact-source review packet / OA disposition](https://github.com/sc28249782/hermes-mcp-bridge/blob/83aacfc10eb9fb2ddf704d1883eee07eb922e78e/docs/OPENCODE-HANDOFF-OBSERVER-NATIVE-REVIEW-TH.md)
/ [Pinned source and dependencies](https://github.com/sc28249782/hermes-mcp-bridge/blob/83aacfc10eb9fb2ddf704d1883eee07eb922e78e/acceptance/handoff/opencode/observer-native-hashes.json).

Adds actual retained-FD exec of unchanged C SQLite helper under fresh owned R/O/S/H
fixture topology. H first waits for witness/pidfd/ACK/ACKED/G; exec replaces that
same H, no fifth actor. Fixed --batch argv/env and synthetic ctx_fixture/oct_fixture
only. S reads context/job/context with cumulative 64-KiB cap, strict decoder and
independently locked fixture tuple digest; exit=0 + exact reap + both actual stream
EOFs are required before original typed fixture FINAL. R revalidates bindings and
retained bundle, reaps O/S and validates report EOF before fixture publication.

Outcome **OFFLINE_NATIVE_FIXTURE_CONFIRMED** is synthetic state capture only,
not production capture or original goal Done. capture_allowed/authorizes_actions/
dev_observed/goal_verified remain false. Existing Reservation.capture() still
always denies PIDFD_ACK_UNBOUND. No Facts/Owner/Batch/planner/receipt integration,
public CLI/MCP/config surface, backend job or Dev/pilot action is introduced.
FixtureIssuer/FixtureBundle are trusted bootstrap, not production authentication,
rollback anchor, original executable provenance or observer-loss containment.

**Local 36/36 native controls OK** (34 isolated process cases + manifest + AST
source-path audit), Python 3.12.14, ResourceWarning-as-error/no skip. Every process
case confirms no fixture children and unchanged parent subreaper setting; synthetic
state bytes unchanged. Startup **22/22**, preflight **24/24** unchanged regressions OK.
Coverage includes actual native WAL/EXCLUSIVE writer/schema failures; fixture oracle
negatives; partial/oversized/stderr/ill-typed/missing frames; full native prefix then
exit 2/trailing stdout/late stderr/hang; actual native H surviving actual S SIGKILL
and adopted retained-pidfd reap; exec failure/no retry; late publication denial.
Test-only C post-main wrappers and Python fault hooks are explicitly separated from
the unchanged positive C production-helper build. Missing FINAL remains UNKNOWN;
cleanup does not manufacture reaper identity, goal verification or replacement FINAL.

Fraction 20/3/45-second bounds and inward float conversion are unchanged; fixture
attempts 8 s or shortened 3.5 s. Native 1-s open/lock/query/close alarm unchanged.
No fresh deadline at ACK/adoption; no numeric-PID/PGID signal or old Owner._stop.
Four per-actor RLIMIT_AS caps are not aggregate physical-memory proof.
Unknown pre-witness launch/R loss/external containment, production authority/anchor,
original goal/Facts join, aggregate resources and hard kernel I/O remain blockers.
OA obligations remain PARTIAL or NOT RUN; OA07 actual R loss and OA12 joined goal
are NOT RUN. B1–B7 OPEN; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN.

Delta against accepted parent: **1 commit, 5 new files +886/-0**; recursive tree
comparison shows **zero changed existing blobs**, all five tested files match remote
Git blob IDs. Source/pins/AST/links/whitespace checked. #112 freshly confirmed draft
at e7142cf71792475af9375140df39acd55944d8d1. Keep draft/unmerged; SPEC section 14
still required before any runtime/security interface implementation merge.
Historical broad local baseline NOT PASS is unchanged; no local broad PASS claimed.

### Exact-head CI

All **nine workflows SUCCESS** at `83aacfc10eb9fb2ddf704d1883eee07eb922e78e`.
Actual job logs inspected for both interpreters:

| Workflow | Jobs / observed counts |
| --- | --- |
| [OpenCode observer startup offline controls 41819051815](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41819051815) | startup (3.12): 126537244212 **22 OK**; startup (3.14): 126537243730 **22 OK** |
| [OpenCode observer native offline controls 41819051832](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41819051832) | native (3.12): 126537243310 **36 OK**; native (3.14): 126537243165 **36 OK** |
| [OpenCode observer preflight offline controls 41819051768](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41819051768) | preflight (3.12): 126537243448 **24 OK**; preflight (3.14): 126537243947 **24 OK** |
| [Handoff evaluation preparation controls 41819051851](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41819051851) | preparation (3.12): 126537260748 **26+18 OK**; preparation (3.14): 126537244483 **26+18 OK** |
| [OpenCode passive observation source controls 41819051730](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41819051730) | source (3.12): 126537243221 **48 OK**; source (3.14): 126537242494 **48 OK** |
| [Handoff offline source controls 41819052101](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41819052101) | offline (3.12): 126537247449 **26 OK**; offline (3.14): 126537252681 **26 OK** |
| [OpenCode supervisor-loss offline controls 41819051871](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41819051871) | supervisor-loss (3.12): 126537243308 **9 OK**; supervisor-loss (3.14): 126537243097 **9 OK** |
| [OpenCode B4 offline supervision controls 41819051797](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41819051797) | supervision (3.12): 126537243337 **29 OK**; supervision (3.14): 126537243424 **29 OK** |
| [Tests 41819051736](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41819051736) | test (3.12): 126537243757 **1+234 OK**; test (3.14): 126537253520 **1+234 OK** |

Native jobs: 34 actual per-case records each; all no_children=true and all four
capture/action/Dev/goal flags false. Normal native fixture confirmed; actual native
S-loss retains UNKNOWN with R-reaped H; late publication UNKNOWN despite valid
fixture FINAL/reap/EOF. All component gates have exits=0,
complete_without_skips=true, warning_markers=[]. Preparation evaluation_arms_executed=0;
heldout-once **126537244757** and development-once **126537250895** SKIPPED.
Baseline full suite 234/234 and migration 1/1 on both Python versions. Component
warning gates do not claim all third-party Actions deprecation warnings are absent.

These are GitHub-owned synthetic regressions, not Dev/pilot/original goal trials.
No full OA/B closure; native candidate still awaits independent source review.
Historical broad local baseline NOT PASS remains unchanged.


---

## Historical package 2 and earlier checkpoints

## Observer package 2 — inert R/O/S/H startup and arbitration source candidate

Final head `8b41102ce9ed9a87a6df208ad6970f3381f90c6e`; parent accepted package 1
`dc0199960f463759543d918ec2e32a138cfd691d` received operator-supplied round-8
APPROVE at its stated scope. No GitHub review submission is impersonated.

[Exact-source review packet and OA disposition](https://github.com/sc28249782/hermes-mcp-bridge/blob/8b41102ce9ed9a87a6df208ad6970f3381f90c6e/docs/OPENCODE-HANDOFF-OBSERVER-STARTUP-REVIEW-TH.md)
/
[Actual source and pinned dependency identities](https://github.com/sc28249782/hermes-mcp-bridge/blob/8b41102ce9ed9a87a6df208ad6970f3381f90c6e/acceptance/handoff/opencode/observer-startup-hashes.json).

Implements actual fresh fixture R parent of O/S, S parent of inert Python H,
retained pidfds, process-local subreaper, source-bound private witness and
ACK/ACKED-before-inert-G. S proves its unreaped direct H before witness; R validates
nonce/generation/role/source/parent/child and S/O liveness before/after H pidfd
retention. O is a fixed relay. H stdin/stdout/stderr are the actual redirected
pipes; its fixed body only reads one G and writes HG1 newline. No native/SQLite/
OpenCode/CLI/model/evidence/Facts/planner path is started.

**The new G byte is an inert startup probe, not protected capture.**
Reservation.capture() remains byte-identical and always denies.
FIXTURE_STARTUP_CONFIRMED is not goal Done; capture_allowed/authorizes_actions/
dev_observed/goal_verified stay false. No public bridge tool/config/MCP entry.

Actual controls cover pre-adoption ECHILD/no-signal, S death after witness before
retain/ACK, O loss, O/S loss after inert G with TERM-ignore H, retained-pidfd adopted
cleanup/reap/EOF, helper-pidfd failure/no retry, revoke, wrong/duplicate witness,
wrong actual H proof, missing/ill-typed FINAL, failed consumed claim, object reuse,
stalled ACK cutoff and late-publication rejection after actual FINAL/reap/EOF.
S-reaped H with missing FINAL has unknown reaper in the receiving record; no
replacement FINAL or fabricated observer-reap/goal claim.

**Local final controls: startup 22/22; preflight 24/24 OK**, Python 3.12.14,
ResourceWarning-as-error/no skips. Twenty-one startup process cases use fresh
isolated R and assert no remaining fixture child and unchanged parent subreaper
setting. Fault hooks choose frames/crash/clock stimulus; kernel fork/SIGKILL/pidfd/
adoption/waitid/reap/EOF are real. Source uses no host process scan, numeric-PID/
PGID signal, waitpid(-1) cleanup or caller callbacks. waitpid(-1) appears only as
a test oracle in each freshly isolated R.

### Required numerical correction — failure retained, assertions unchanged

Initial candidate `cf37340d` had startup workflow SUCCESS but preflight
[41644122495](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41644122495)
failed Python 3.12 job **125944837128**:
`20.000000000000004 not less than or equal to 20`.
The source/test was unchanged at that initial head; Python 3.14 passed.
No blind rerun, tolerance increase, skip or assertion relaxation was used.

Budget endpoints now use exact Fraction representations of the original input
clock values, with exact 20/3/45-second arithmetic. POSIX float timeouts round
inward. Added deterministic `nextafter(17,-inf)` regression preserves every
existing 23-control assertion; preflight workflow strictly requires 24.
A later guard rejects startup publication past the absolute attempt deadline even
after actual lifecycle proof. Original T0/Ta are not shifted and no timer widens.

Compared with accepted parent: **9 files +1040/-15**, three commits: five new
startup files plus four modified preflight files (source, additive regression,
strict workflow count, actual hash manifest). All native/VFS/supervision, old
29/9/48 suites, main runtime/schema/SPEC/receipts/OC definitions/experiment guards
remain identical. Source/pin/AST/whitespace/link checks passed.
Historical broad local baseline NOT PASS is unchanged; no local broad pass claimed.

Production issuer/anchor/containment, actual post-fork/pre-witness identity gap,
R death, full native goal/context/receipt join, aggregate physical resources and
uninterruptible I/O remain OPEN. OA01–OA11 have partial fixture evidence only;
OA12 NOT RUN. No full OA/B row PASS/CLOSED. Exact final-head CI is complete
below; old failed run is not converted into a pass.

Ready for independent exact-source review of this inert profile and numerical
delta. Keep draft/unmerged; B1–B7 OPEN; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD;
OC18 NOT RUN. No Dev/pilot, actual backend/job, model/API/key/config action,
archive/arm trial, release or deployment.

### Exact final package-2 CI — all eight workflows SUCCESS

At `8b41102ce9ed9a87a6df208ad6970f3381f90c6e`:

| Workflow | Inspected Python 3.12 / 3.14 jobs |
|---|---|
| [Startup 41647276724](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41647276724) | 125955806688 / 125955806901: **22/22 OK** |
| [Preflight 41647276848](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41647276848) | 125955808975 / 125955808581: **24/24 OK** |
| [Supervisor loss 41647276672](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41647276672) | 125955807504 / 125955808200: **9/9 OK** |
| [Supervision 41647276914](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41647276914) | 125955808073 / 125955807440: **29/29 OK** |
| [OpenCode source 41647276813](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41647276813) | 125955807623 / 125955807260: **48/48 OK** |
| [Tests 41647276664](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41647276664) | 125955806362 / 125955807313: **234/234 OK**, migration 1/1 |
| [Handoff offline 41647276981](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41647276981) | 125955807821 / 125955808637: **26/26 OK** |
| [Preparation 41647276692](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41647276692) | 125955807226 / 125955807364: **26+18 OK** |

Inspected component gates: exits=0, complete_without_skips=true,
warning_markers=[], capture/action/Dev/goal flags false where emitted.
Preparation evaluation_arms_executed=0. Development-once **125955809363** and
heldout-once **125955809281** SKIPPED. Target-suite gates do not claim all
third-party Actions runtime deprecation warnings are absent.

Both startup jobs emit **21 actual per-case results**, all no_children=true and
capture_allowed/authorizes_actions/dev_observed/goal_verified=false.
Normal inert startup has source-validated ACK-before-G and S-reaped H with FINAL;
late-publication case remains UNKNOWN despite actual FINAL/reap/EOF.
Missing FINAL and loss cases do not manufacture original observation success.
The isolated test oracle is not a production containment/observer-death guarantee.

All nine tested local Git blob IDs equal the final published tree. Against accepted
parent dc019996: three commits, 9 files +1040/-15; precisely four old preflight
files changed for exact arithmetic/additive deterministic regression/count/pins.
Native/VFS/supervision, original 29/9/48 suites, main runtime/schema/SPEC/receipts/
OC definitions/experiment guards remain unchanged. Hash/AST/link/whitespace checks pass.
The failed initial cf37340d run stays recorded above; no assertion was relaxed.

Historical broad local baseline NOT PASS remains unchanged; this is GitHub-owned
regression evidence, not a claimed local broad rerun. OA rows remain partial or
NOT RUN as stated in the review packet; no full OA/B row accepted/closed.
Ready for independent exact-source review of inert package 2 and the precision delta.
Same draft/unmerged; B1–B7 OPEN; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN.
No Dev/pilot/native capture, original goal evaluation, release or deployment.

---

## Historical package 1 and earlier checkpoints

## Observer implementation package 1 — offline preflight/reservation source review

Head `dc0199960f463759543d918ec2e32a138cfd691d`; parent contract
`baf0c196693da54ac4bad665a3e20f89b2350c8b` received operator-supplied round-7
APPROVE at contract scope. This records that review, not a GitHub submission.
[Source review and per-OA disposition](https://github.com/sc28249782/hermes-mcp-bridge/blob/dc0199960f463759543d918ec2e32a138cfd691d/docs/OPENCODE-HANDOFF-OBSERVER-PREFLIGHT-REVIEW-TH.md)
/
[Actual source/contract hashes](https://github.com/sc28249782/hermes-mcp-bridge/blob/dc0199960f463759543d918ec2e32a138cfd691d/acceptance/handoff/opencode/observer-preflight-hashes.json).

Implements a stdlib-only **trusted-fixture preflight/reservation component**:
closed Binding registry, current epoch/expiry/revocation/scope/cleanup/containment
checks before claim, exclusive retained-root O_EXCL claim with file/directory
fsync, preserved partial/unknown claims, one shared 20/45 s Budget with 3 s
cleanup reserve, and bounded single-read strict private witness framing.
No caller dictionary-to-authority/Facts, runtime dispatcher, O/S/H launch, pidfd/
adoption, DB/evidence read, model/API/config/secret action or checkpoint append.

**FixtureIssuer is not production authentication/authority/anchor/containment.**
Its Binding/type/frozen-object/owner-only-file/hash checks do not authenticate a
hostile same-process caller. Production-tag input is rejected; a fixture catalog
tag is not production observer-loss containment. Valid reservation is a consumed
fixture claim, not actual ARM or an executable capability.
A parsed witness lacks authenticated parent/channel/pidfd ACK; **capture always
rejects PIDFD_ACK_UNBOUND**. Cleanup status is OWNERSHIP_UNBOUND and grants no
signal/reap authority. All Result capture/action/Dev flags remain false.

Author-local **23/23 OK**, Python 3.12.14, ResourceWarning-as-error/no skips.
Copied in-memory issuers after fork now reject ISSUER_PROCESS_CHANGED before any claim.
The issuer registry is process-local, not a cross-process authority/revocation service.
Actual two-process race, with fresh trusted fixture issuers per child, yields exactly
one reservation; actual child crash after
exclusive create leaves a zero-byte consumed claim; fsync-failure evidence remains;
new issuer/Binding plus data-file rollback cannot redeem retained-root claim again.
Real pipes reject wrong/partial/duplicate/over-cap/EOF/type-invalid witness frames.
Source AST has no process/backend/signal/repair dispatch; public Result is redacted.
The rollback case is a limited separate-root experiment, **not full native store/
authority/dossier/context rollback or independently authenticated B3 closure**.

**OA disposition:** OA01/02/07/08/09/10/11 have named PARTIAL fixture component
evidence; OA03/04/05/06/12 NOT RUN in this source path. No whole OA row PASS/CLOSED.
Existing 29/9/48 are unchanged input/regression suites. B1–B7 remain OPEN.
Next bounded source work after review is actual offline R/O/S/H witness/pidfd/
ACK/arbitration, without silently turning FixtureIssuer into production admission.

Exact delta: **5 new files +768/-0**, two commits. Remote recursive comparison:
**zero changed pre-existing blobs**. Existing source/tests/workflows/manifests/
schema/SPEC/OC definitions/receipts/guards unchanged. New contents:read workflow
runs only private claim/pipe/race fixtures on Python 3.12/3.14.
Manifest/AST/5 relative links/whitespace checked. Exact final-head CI is complete below.
Development pre-manifest run failed manifest lookup and is not a final pass/trial.
Historical broad local baseline NOT PASS is unchanged and not rerun here.
#112 freshly read: same draft `e7142cf71792475af9375140df39acd55944d8d1`.

Ready for independent exact-source review of this foundation only.
No production integration, OA closure, Dev/pilot, archive/arm trial, release or
deployment. Keep draft/unmerged; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN.

Initial candidate e0ed7a58 had 22 controls. The follow-up process-identity guard
adds one control; final suite is 23, not 45 trials. It changes no pre-existing baseline
blob. Exact final-head CI must be attributed to this head, not the initial candidate.

### Exact final preflight source-head validation — seven workflows SUCCESS

At `dc0199960f463759543d918ec2e32a138cfd691d`, attempt 1:

| Workflow | Inspected Python 3.12 / 3.14 jobs |
|---|---|
| [Observer preflight 41638125819](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41638125819) | 125924408876 / 125924407508: **23/23 OK** |
| [Supervisor loss 41638125781](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41638125781) | 125924407412 / 125924407090: **9/9 OK** |
| [B4 supervision 41638125789](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41638125789) | 125924407553 / 125924407014: **29/29 OK** |
| [OpenCode source 41638125885](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41638125885) | 125924407763 / 125924407361: **48/48 OK** |
| [Tests 41638125857](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41638125857) | 125924407661 / 125924407298: **234/234 OK**, migration 1/1 |
| [Handoff offline 41638125805](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41638125805) | 125924408915 / 125924407150: **26/26 OK** |
| [Preparation 41638125818](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41638125818) | 125924408331 / 125924408722: **26+18 OK** |

Inspected component gate records: exits=0, complete_without_skips=true,
warning_markers=[], action/Dev flags false; preparation evaluation_arms_executed=0.
Development-once **125924410274**, heldout-once **125924410254** SKIPPED.
These are GitHub-owned offline fixtures. Target-suite warning gates do not assert
all third-party Actions runtime logs are free of deprecation warnings.

Local final preflight 23/23 OK; exact Git blob comparison confirms all five tested
local files equal the published final tree. Remote comparison against accepted
contract head: two commits, five new files +768/-0, zero changed pre-existing blobs.
Source/contract manifest, AST, relative links and whitespace checked.
No baseline assertion/guard/timer or accepted source/test blob changed.

The seven successful workflows are component/source regression, not production
issuer/anchor/revocation/containment authentication or actual observer startup.
OA01/02/07/08/09/10/11 remain PARTIAL fixture evidence; OA03/04/05/06/12 NOT RUN
in this source path. No whole OA row PASS/CLOSED; all B1–B7 OPEN.
Capture G still denies PIDFD_ACK_UNBOUND after a valid witness. No launch/stop/
reap/DB/Facts/planner or runtime capability is provided by this component.
Historical broad local baseline NOT PASS remains unchanged.
Ready for independent exact-source review of package 1 only; same held boundaries.

---

## Historical accepted contract and earlier checkpoints

## Production observer/adoption contract candidate — design review requested

Documentation head `baf0c196693da54ac4bad665a3e20f89b2350c8b`; input
`48716cbc07af3430b56a4edc738664d357a7eb5e` received operator-supplied round-6
APPROVE for supervisor-loss controls at fixture scope. This records that supplied
review, not a GitHub review submission. B4 remains OPEN.

[Observer/adoption contract](https://github.com/sc28249782/hermes-mcp-bridge/blob/baf0c196693da54ac4bad665a3e20f89b2350c8b/docs/OPENCODE-HANDOFF-OBSERVER-ADOPTION-CONTRACT-TH.md)
defines a candidate fresh per-attempt observer/subreaper topology, finite current
authority plus separate terminal-cleanup capability, single-use rollback-aware
admission, witness/pidfd/ACK-before-G, parent/reaper arbitration and explicit
UNKNOWN/STOP_UNCONFIRMED dispositions. No production binding or implementation exists.

The observer may stop helper only after exact supervisor exit/reap and adopted
direct-child proof. ECHILD is denial, not observer-reap evidence. No numeric-PID/
PGID signals, host process scan, replay/respawn or fixture authority promoted to
production. Missing original supervisor FINAL remains UNKNOWN even after observer
cleanup; native completion/output and goal verification are separate evidence.

**Observer death is not solved by subreaper/EOF/pdeath signals.** Actual ARM/G
requires separately accepted external containment/control and current B1/B3 issuer/
anchor bindings. These remain UNBOUND; no systemd/cgroup/daemon/VM action selected
or authorized. Launch identity uncertainty, containment and aggregate resources
are explicit feasibility gates, not waived by this document.

**No widened timer:** proposed production profile shares T0+45 s and one attempt
<=20 s, with capture cutoff <=attempt deadline minus 3 s. O/S stop concurrently
when admitted, then adopt/stop H; two bounded phases total <=2.4 s plus <=0.6 s
drain/reap/metadata reserve. This is a stricter proposed allocation, not a change
to accepted source timers or a claim of proven worst-case kernel latency.
Four internal actors' proposed <=256 MiB address-space caps are not an aggregate
physical-memory guarantee; external actor cost/enforcement/headroom remain UNBOUND.

OA01–OA12 preregister authority, witness/adoption races, observer death, malformed
reports/EOF, attempts/rollback, shared resources, privacy and joined Facts/goal
obligations with B/OC mappings. They are **NOT RUN**, not new OC trials or test
acceptance. Existing 9/29/48 suites remain historical/source regression evidence.

Exact delta: **one new Markdown file +277/-0**, one commit.
Seven relative link paths and whitespace checked; remote recursive tree confirms
zero changed pre-existing blobs. No runtime/source/test/workflow/schema/SPEC/
manifest/receipt/guard change. No new tests added or local runtime controls run.
Exact-head automatic regression is complete below; it cannot accept this contract.
#112 freshly read: same draft `e7142cf71792475af9375140df39acd55944d8d1`.

Next is independent contract/feasibility review before bounded offline source
work, with actual containment/authority still held. SPEC section-14 change control
is required before future implementation merge. No Dev/pilot/current bindings,
archive/arm trial, model/API/key/config action, release or deployment.
Keep draft/unmerged; all B1–B7 OPEN; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN.

### Exact contract documentation-head regression — six workflows SUCCESS

At `baf0c196693da54ac4bad665a3e20f89b2350c8b`, attempt 1:

| Workflow | Inspected Python 3.12 / 3.14 jobs |
|---|---|
| [Supervisor loss 41629675754](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41629675754) | 125895745992 / 125895746329: **9/9 OK** |
| [B4 supervision 41629675715](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41629675715) | 125895745833 / 125895746484: **29/29 OK** |
| [OpenCode source 41629675949](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41629675949) | 125895747262 / 125895746940: **48/48 OK** |
| [Tests 41629675920](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41629675920) | 125895746946 / 125895747378: **234/234 OK** plus migration 1/1 |
| [Handoff offline 41629675817](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41629675817) | 125895745844 / 125895746876: **26/26 OK** |
| [Preparation 41629675674](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41629675674) | 125895746516 / 125895745988: **26+18 OK** |

Inspected component gate records: exits=0, complete_without_skips=true,
warning_markers=[], action/Dev flags false where emitted; preparation
evaluation_arms_executed=0. Development-once **125895748169** and heldout-once
**125895747992** SKIPPED. These are existing GitHub-owned regression fixtures.
Historical local baseline NOT PASS is unchanged; no local baseline rerun claimed.

Exact remote compare: one new Markdown file +277/-0, zero changed old blobs.
No new test/assertion/predicate/guard/timer changed. OA01–OA12 remain NOT RUN.
CI is not contract acceptance, production implementation, observer-loss containment,
aggregate memory feasibility, B4 closure or action authority.
Ready only for independent contract/feasibility review; same draft/unmerged and held boundaries.

---

## Historical supervisor-loss controls and earlier checkpoints

## Post-spawn supervisor-loss control candidate — exact-source review requested

Head `48716cbc07af3430b56a4edc738664d357a7eb5e`; parent source
`62356920f6ff15088b4eb21caf1eac5821c85511` received operator-supplied round-5
APPROVE at its declared primitive scope. This records that supplied review, not
a GitHub review submission. B4 remains OPEN.

[Supervisor-loss review packet](https://github.com/sc28249782/hermes-mcp-bridge/blob/48716cbc07af3430b56a4edc738664d357a7eb5e/docs/OPENCODE-HANDOFF-SUPERVISOR-LOSS-REVIEW-TH.md)
/
[Actual source/dependency hashes](https://github.com/sc28249782/hermes-mcp-bridge/blob/48716cbc07af3430b56a4edc738664d357a7eb5e/acceptance/handoff/opencode/supervisor-loss-hashes.json).

Adds **9 owned offline controls**: eight real supervisor-SIGKILL process cases plus
manifest validation. Cases cover immediately post-spawn, READY-before-G, active
TERM-ignore, actual success prefix, nonreading helper, TERM-responsive helper,
both owner/supervisor loss, and completed capture paused before FINAL write.
Test hooks choose the crash boundary; fork/exec, SIGKILL, pidfd readiness, kernel
adoption, stream EOF and waitpid/reap are real, not mocked cessation verdicts.

Each case uses a new isolated test observer with process-local child-subreaper
setting. The parent test runner's setting is checked unchanged. A private witness
lets the observer retain helper pidfd before supervisor death; ECHILD denies the
actual cleanup guard before adoption with zero signals. After supervisor reap,
adopted direct-child proof precedes retained-pidfd TERM/KILL/reap. Independently
retained helper stdout/stderr read ends prove their EOF separately from original
report-pipe EOF. No socket, numeric-PID/PGID signal or orphan-producing test method.

**Observed limitation:** an active TERM-ignore/nonreading helper can survive
supervisor death. It ceases only after the independently owned test observer
adopts and cleans it up. The native idle helper exits on pipe EOF.
All original observations remain **UNKNOWN without FINAL**, including capture
that completed/reaped before its FINAL was written. No replacement FINAL/Done,
checkpoint or backend action is generated. Per-case allowlisted CI receipts
separate adoption, exit, observer reap, both EOF channels, cleanup signals and
no-remaining-children, with goal_verified/authorizes_actions/dev_observed=false.

Author-local **9/9 OK**, Python 3.12.14/native SQLite 3.45.1,
ResourceWarning-as-error/no skips. Development pre-manifest runs failed only
manifest-file lookup and are not final passes/additional trials. Exact-head CI is complete below.
This package did not rerun or repair the historical broad local baseline NOT PASS.

Exact delta: **4 new files +712/-0**, one commit; recursive remote tree comparison
finds **zero changed pre-existing blobs**. Existing supervision source, 29/48 tests,
workflows/hash manifests/Facts/Batch/planner/schema/SPEC/config/receipts/OC definitions/
experiment guards remain identical. New contents:read workflow runs only disposable
supervisor-loss fixtures on Python 3.12/3.14. Hash/AST/links/whitespace passed.
#112 freshly read, same draft `e7142cf71792475af9375140df39acd55944d8d1`.

The observer/adoption/cleanup role is **test-only**, not production recovery wiring
or an approved deployment actor/resource model. Existing 1/20/45 s source bounds
are unchanged; fixture uses shortened 8 s supervisor / 12 s case / 20 s observer
alarm, with bounded retained-pidfd cleanup. Production observer authority, observer
death, joined Facts/verifier/receipt commit, aggregate resource feasibility and
uninterruptible I/O remain OPEN. Pre-arm regression is retained; new evidence
adds post-spawn disposition without rewriting the parent review.

Ready for independent exact-source/control review only. All B1–B7 OPEN.
Keep draft/unmerged; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN.
No Dev/pilot, new archive/arm trial, model/API/key/config action, release or deployment.

### Exact supervisor-loss head — all six workflows SUCCESS

At `48716cbc07af3430b56a4edc738664d357a7eb5e`, attempt 1:

| Workflow | Inspected Python 3.12 / 3.14 jobs and results |
|---|---|
| [Supervisor loss 41623981358](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41623981358) | 125876557402 / 125876557645: **9/9 OK**, supervisor_loss_exit=0, complete_without_skips=true, warning_markers=[] |
| [B4 supervision 41623981229](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41623981229) | 125876557303 / 125876557753: **29/29 OK**, b4_exit=0, complete_without_skips=true, warning_markers=[] |
| [OpenCode source 41623981227](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41623981227) | 125876557328 / 125876557624: **48/48 OK**, source_exit=0, complete_without_skips=true, warning_markers=[] |
| [Tests 41623981348](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41623981348) | 125876557498 / 125876557862: **234/234 OK** plus migration 1/1 each |
| [Handoff offline 41623981523](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41623981523) | 125876558529 / 125876558971: **26/26 OK**, offline_exit=0, complete_without_skips=true, warning_markers=[] |
| [Preparation 41623981276](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41623981276) | 125876557196 / 125876557520: **26+18 OK**, both exits=0, complete_without_skips=true, warning_markers=[], evaluation_arms_executed=0 |

Development-once **125876559186** and heldout-once **125876559355** SKIPPED.
Target-suite warning gates are clean; third-party Actions runtime deprecations are
not represented as an absence of all warnings in the entire job log.

Both new jobs emitted **eight actual per-case receipts**. Independently inspected:
all disposition=UNKNOWN, final_received=false, report_eof/helper_pipes_eof/
supervisor_reaped/adoption_guard_denied/no_children=true; goal/action/Dev flags false.
Seven cases have adopted helper reaped by observer. The pre_final case correctly
has helper_adopted=false/helper_reaped_by_observer=false because the supervisor
already reaped it before being killed. Native idle/post_spawn need no helper signal;
term needs TERM only; hung/blocked/prefix/both need TERM then KILL.
Observed case durations: **24–230 ms (3.12)** / **22–228 ms (3.14)**; these are
fixture measurements, not worst-case kernel I/O or deployment bounds.

Exact tested local blob IDs match all four published files. Remote recursive-tree
comparison against parent confirms zero pre-existing blob changes.
CI/source identity does not convert the test-only observer into a production
recovery path, close B4, prove observer-death/uninterruptible-I/O feasibility, or
authorize Dev/pilot. Historical broad local baseline NOT PASS remains unchanged.
Ready for independent exact-source/control review of the named new fixture scope.
All B1–B7 OPEN; draft/unmerged; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN.

---

## Historical B4 primitive and earlier checkpoints

## B4 offline supervision source candidate — exact-source review requested

Head `62356920f6ff15088b4eb21caf1eac5821c85511`; parent accepted plan
`1dd77c131e8f3bee2fd61b8285ed9a150f4c793f`.
[Source review and explicit limits](https://github.com/sc28249782/hermes-mcp-bridge/blob/62356920f6ff15088b4eb21caf1eac5821c85511/docs/OPENCODE-HANDOFF-B4-SOURCE-REVIEW-TH.md)
/
[actual source/dependency manifest](https://github.com/sc28249782/hermes-mcp-bridge/blob/62356920f6ff15088b4eb21caf1eac5821c85511/acceptance/handoff/opencode/supervision-hashes.json).

Adds an isolated trusted-fixture supervisor that directly creates/retains/reaps one
native helper independently of an external disposable owner. Owner pidfd death or
lease EOF cancels the attempt; signals target only the retained helper pidfd.
A/READY/G barriers, one fork/no retry/respawn, fixed retained-ELF exec/argv, inherited
45 s envelope, <=20 s attempt, unchanged native 1 s alarm, bounded nonblocking
reports and explicit reap/pipe-EOF fields. No numeric-PID/PGID signal fallback.
Post-fork setup preserves child identity; uncertain fork return reports
helper_started=null / STOP_UNCONFIRMED, never falsely no helper.

**Author-local 29/29 B4 controls OK** on Python 3.12.14 with ResourceWarning-as-error
and no skips; unchanged source 48/48 OK separately. Real SIGKILL/deadline/TERM-ignore/
partial-success/blocked-input/owner-lease/report-loss fixtures; actual retained pipe
write end proves reaped helper without EOF remains STOP_UNCONFIRMED.
Only the interrupted-fork-return boundary is injected without creating an unowned
process; ordinary post-fork failure uses an actual child. Development socket-based
fixture attempt hit local EPERM and was replaced by socket-free real-pipe retention
without weakening the EOF assertion; final source has no socket/network operation.

**Narrow primitive, not whole B4 closure:** no Facts.Owner/Batch/planner integration
or production admission/observer. CAPTURE_COMPLETE is frame/exit/reap/EOF evidence,
never goal success; goal_verified/authorizes_actions/dev_observed stay false.
Supervisor SIGKILL after helper creation, observer death, uninterruptible kernel I/O,
production trust/retention, joined integration and aggregate actor/resource approval
remain OPEN. Supervisor/helper each have a 256 MiB address-space cap, not a combined
256 MiB cap; the primitive does not enforce or terminate the external owner's lifetime.
No native/Dev invocation, model/provider/API/key/config action or checkpoint append.

Exact incremental delta **5 new files +1071/-0**, one commit.
Fresh recursive-tree comparison: **zero pre-existing blob changes**.
All old source/tests/workflows/hash manifests/schema/OC definitions/receipts/guards
are unchanged; source manifest/AST/links/whitespace checked. New dedicated
contents:read GitHub workflow runs only owned B4 fixtures on Python 3.12/3.14.
Exact-head CI is complete below; no new broad local baseline pass is claimed.
#112 freshly read: same draft `e7142cf71792475af9375140df39acd55944d8d1`.

Ready for independent exact-source review only. All B1–B7 remain OPEN.
Keep draft/unmerged; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN.
No pilot, new archive invocation/arm trial, release or deployment.

### Exact B4 source-head CI — all five workflows SUCCESS

At `62356920f6ff15088b4eb21caf1eac5821c85511`, attempt 1:

| Workflow | Inspected Python 3.12 / 3.14 jobs and results |
|---|---|
| [B4 supervision 41619743185](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41619743185) | 125862146263 / 125862145970: **29/29 OK**, b4_exit=0, complete_without_skips=true, warning_markers=[], dev_observed=false, authorizes_actions=false |
| [OpenCode source 41619743153](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41619743153) | 125862145776 / 125862146088: **48/48 OK**, source_exit=0, complete_without_skips=true, warning_markers=[] |
| [Tests 41619743100](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41619743100) | 125862145905 / 125862145525: **234/234 OK** plus migration 1/1 each |
| [Handoff offline 41619743103](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41619743103) | 125862145919 / 125862145662: **26/26 OK**, offline_exit=0, complete_without_skips=true, warning_markers=[] |
| [Preparation 41619743174](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41619743174) | 125862146142 / 125862146686: **26+18 OK**, both exits=0, complete_without_skips=true, warning_markers=[], evaluation_arms_executed=0 |

Development-once **125862148299** and heldout-once **125862148452** are SKIPPED.
These are GitHub-owned component fixtures, not operator-host/Dev observations.
Target-suite warning gates are clean; this is not a claim every third-party
Actions runtime emits no deprecation warning.

All five tested local file Git blob IDs equal the published tree entries.
Recursive comparison against parent finds **zero changed pre-existing blobs**.
Manifest controls verify actual SHA256/byte lengths for new source/workflow and
the unchanged dependencies. Links/AST/whitespace passed.
Local broad baseline history remains NOT PASS; this candidate did not rerun it
locally or establish its historical process-assertion root cause.

CI supplies component regression evidence, not independent source acceptance,
complete B4/OC15–16 closure, production observer/admission, joined Facts integration,
supervisor-death-after-spawn or uninterruptible-I/O feasibility.
Ready for exact-source review of the stated fixture profile only.
All B1–B7 OPEN; draft/unmerged; held action boundaries unchanged.

---

## Historical reviewed plan and source checkpoints

## Current checkpoint — source review accepted at fixture scope; blocker plan added

Current documentation head `1dd77c131e8f3bee2fd61b8285ed9a150f4c793f`.
The operator supplied round-3 **APPROVE** for exact source head
`0e79bd00f54e33e4c462a2a37228b89316161794`, limited to its offline fixture profile.
This records the supplied review; it is not a new GitHub review submission or
whole-integration acceptance. Later source changes require their own review.

[Blocker closure plan](https://github.com/sc28249782/hermes-mcp-bridge/blob/1dd77c131e8f3bee2fd61b8285ed9a150f4c793f/docs/OPENCODE-HANDOFF-BLOCKER-CLOSURE-TH.md)
adds B1–B7: authority/bindings, original-invocation provenance, independent rollback
anchor, external-owner death/stop, original-goal verifier, coverage/resources and
the eventual finite pilot packet. Each has acceptance criteria, required evidence,
HOLD conditions and OC/six-gate mapping. All remain OPEN; reviewer observations
OC02/04/05 and the Facts construction boundary are follow-up targets.

Incremental delta: **one Markdown file, +104/-0**. Seven relative links resolve
against the exact input tree; whitespace checked. Existing source/test/workflow/
schema/hash/receipt blobs unchanged. No new test cases or arm trials added by this documentation change.
Existing offline regression suites ran automatically on GitHub at the new head.
The later historical CI section still belongs to its named original source head. #112 freshly read, still draft at `e7142cf7`.

Next proposed source package is bounded offline ownership/death supervision (B4),
with real owned-process controls and the existing 1 s / 20 s / 45 s limits.
This plan does not execute that package or authorize Dev.
Keep draft/unmerged; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN.
No Dev/pilot, new archive invocation, runtime/config/key action, release or deployment.

### Exact documentation-head regression

At `1dd77c131e8f3bee2fd61b8285ed9a150f4c793f`, all four workflows SUCCESS:
[Tests 41615341596](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41615341596),
[OpenCode source 41615341428](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41615341428),
[Handoff offline 41615341427](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41615341427),
[Preparation 41615341442](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41615341442).

Inspected both Python job logs: baseline jobs 125847284140/125847284575
report 234 tests; source jobs 125847284047/125847283593 report 48/48,
exit=0, complete_without_skips=true, warning_markers=[];
offline jobs 125847284939/125847284715 report 26/26 with the same clean gates;
preparation jobs 125847284019/125847283847 report 26+18 with exits=0,
complete_without_skips=true, warning_markers=[], evaluation_arms_executed=0.
Development-once 125847285728 and heldout-once 125847285821 are SKIPPED.

Exact GitHub compare confirms one added Markdown file +104/-0 and one commit.
This is documentation/component regression, not new blocker closure, Dev capability
or pilot approval. Historical local baseline NOT PASS remains unchanged.
No source acceptance beyond operator-supplied review of `0e79bd00`.
All B1–B7 OPEN; same draft and held boundaries.

---

## Historical source submission and exact-source CI

## Offline OpenCode observation source candidate — review requested, no Dev action

Head `0e79bd00f54e33e4c462a2a37228b89316161794`; parent reviewed contract `a8008dfc`.
[Exact source-review packet and OC01–OC18 disposition](https://github.com/sc28249782/hermes-mcp-bridge/blob/0e79bd00f54e33e4c462a2a37228b89316161794/acceptance/handoff/opencode/SOURCE-REVIEW.md)
/
[Actual source/dependency SHA256 identities](https://github.com/sc28249782/hermes-mcp-bridge/blob/0e79bd00f54e33e4c462a2a37228b89316161794/acceptance/handoff/opencode/source-hashes.json).

Implements one native retained-FD SQLite unix-VFS helper, one private batch child (context-before → job → context-after), fixture-only trusted admission/dossier/Facts, independent exact-full-artifact verifier and existing advisory planner. **This is an offline fixture profile, not the whole integration or production authority service.** No OpenCodeTasks/ContextRegistry constructor/native method, actual backend/CLI/model/API/secret/config action, checkpoint append or new evaluation. Success OFFLINE_ADVISORY_DONE always has authorizes_actions=false/dev_observed=false.

Native source supports only 64-bit Linux x86_64 + SQLite 3.45.1, fixed native schema/projection/authorizer, RO descriptors, no recovery/WAL/SHM/extensions/mmap, no busy retry, real 1-second open/lock/query/close alarm. Helper ≤20 s, owner ≤45 s. **SHARED-lock writer contention and read-atime effects are explicit**, not a zero-effect claim. Native unix O_NOFOLLOW rejected the initial proc-fd open; this source adds a narrowly checked named unix `open` syscall bridge that ONLY duplicates the retained RO descriptor. No mutable pathname/native-open fallback; normal unix read/POSIX locking remains. This detail and the authored limited SQLite ABI header require exact-source review. Existing host compiler/shared library are measured, not independently authenticated.

**48/48 author-local source controls OK**, ResourceWarning-as-error/no skips; actual hot journal/WAL/schema/entry-swap, read-lock contention/coherent snapshot, native 1-s alarm, owner timer, owned-child stop, evidence/authority/context/head races, post-capture failure and privacy controls. Existing handoff 26/26 + preparation 18/18 OK locally; no arm trials. Exact-head GitHub CI is now complete; inspected results are recorded below.

**Local broad baseline did NOT pass:** 98 discovered, 4 failures/14 errors, missing httpx/mcp/anyio imports plus four existing Codex process assertions. Their process-assertion root cause is not established; no dependency-only explanation or local234-pass claim. No test/predicate was relaxed. CI regression will be independently attributed to GitHub, not operator/Dev host.

14 incremental files +1956/-0: new internal acceptance source/tests/hash manifest/review packet + dedicated contents:read workflow, two additive doc pointers. Native runtime/schema/SPEC/config, old handoff source/protocol/receipts/tests/workflows and consumed experiment guards unchanged. Relative paths11 OK; whitespace clean. No source acceptance claimed by author or test count.

**Still OPEN:** actual production authority/model/provider/current Dev bindings; original-invocation proof; independent full-store rollback anchor; abrupt external-owner death/complete stop supervision; independent original Dev goal verifier; exhaustive remaining OC stimuli and six pre-pilot gates. OC18 NOT RUN. Source review may accept only the demonstrated scope; no pilot/merge authority.

Keep draft/unmerged. J0 PAUSED, #112 untouched; R1 NOT AUTHORIZED / R2 HOLD; no sixth archive invocation, release or deployment.

---

## Exact source-head validation (author-triggered GitHub CI)

At `0e79bd00f54e33e4c462a2a37228b89316161794`, **all four workflows SUCCESS, attempt 1**:

| Workflow | Actual inspected result |
|---|---|
| [OpenCode source 41609460911](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41609460911) | Jobs 125827401540 / 125827401283: **48/48 OK** on Python 3.12.15 / 3.14.9, source_exit=0, complete_without_skips=true, warning_markers=[]; dev_observed=false, authorizes_actions=false |
| [Tests 41609460828](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41609460828) | Jobs 125827401531 / 125827400949: **234/234 OK** each plus migration 1/1; warning gates passed |
| [Handoff offline 41609460830](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41609460830) | Both interpreters **26/26 OK**, no skips/warnings |
| [Preparation 41609460815](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41609460815) | Both interpreters **26+18 OK**, evaluation_arms_executed=0; development-once and heldout-once both SKIPPED |

Both new source jobs actually compiled against native SQLite **3.45.1**, source ID
`2024-01-30 16:01:20 e876e51a0ed5c5b3126f52e532044363a014bc594cfefa87ffb5b82257ccalt1`.
Measured CI shared-library SHA256
`85265a9d4afca6f4b325ceb078b669c754fb881abed4cafe91ccebe9d625d975`;
production-variant helper SHA256
`ab61b04fa0facb9a53df3656d15ca2fead8db89d576ef430b138d722bcbbe3f9`
in both jobs. These are actual build facts, not authenticity proofs. CI and local
library/build digests differ; no claim of reproducible cross-environment binary identity.

The local failure remains recorded in the source packet above; GitHub success
does not retroactively turn that local run into a pass or establish its root cause.
The remote source tree `6fd2b7eb36d243a28d197d78e4568bcd569e05f6` equals the tested local tree.
14 files +1956/-0, all source/dependency manifest identities checked; relative paths11 OK,
changed whitespace clean. No native runtime/SPEC/config/schema/old test/workflow/evaluation receipt changes.
Fresh read confirms #112 remains draft at `e7142cf71792475af9375140df39acd55944d8d1`.

**Ready only for independent exact-source review of this fixture-scoped candidate.**
No whole-integration/source-acceptance assertion, OC18, Dev/pilot, merge, new arm trial,
J0 resumption, R1/R2, release/deployment or measured gain is authorized by these results.
Keep draft; production authority/ownership/rollback/original-goal blockers remain.

---

## Historical contract/design checkpoints (unchanged)

## SQLite capture + current Facts source contracts — candidate, not implementation

Head `a8008dfc537114babbe68c966af4c1decbf1da3f`; input operator-supplied APPROVE AS DESIGN at `7fb2088f`.
[Retained-FD read-only VFS / snapshot / TOCTOU contract](https://github.com/sc28249782/hermes-mcp-bridge/blob/a8008dfc537114babbe68c966af4c1decbf1da3f/docs/OPENCODE-HANDOFF-SNAPSHOT-CONTRACT.md)
/
[Current authority/context/model/binary Facts contract](https://github.com/sc28249782/hermes-mcp-bridge/blob/a8008dfc537114babbe68c966af4c1decbf1da3f/docs/OPENCODE-HANDOFF-FACTS-CONTRACT.md).

Selected candidate is a native read-only shim around SQLite's standard unix VFS, retained main-DB descriptors, normal read transaction, fixed schema/queries and denial of secondary opens, mutation, recovery, WAL/SHM/mmap/extensions. No new locking protocol/default Python live capture/copy/immutable/nolock fallback. Exact descriptor alias/native locking behavior and dependencies must be source-proved, not presumed implemented.

**SHARED locks can contend with writer commits.** This ordinary effect requires explicit independent review/read authority; literal zero-blocking requirements would HOLD. Proposed <=1 s lock residence lies inside existing helper20/owner45 s; no busy retry/wait loop, no worker-delay observation trick or widened native timers. Read-access timestamps are also disclosed; no zero-metadata-effect claim.

Current admission is independent of checkpoints/caller dictionaries. Original native row records binary path, not execution-time digest: today's file cannot backfill historical provenance. ContextRegistry has no OpenCode binding columns; selected contract needs a pre-admitted dossier association to a non-null existing open handoff context, checked before/after capture. Null/unknown never becomes context_open=True, no native rebind/create/reopen. Six current authority/model/provider/binary/repo/workspace/goal/verifier gates remain source/pilot obligations.

Five docs/data files **+375/-0 versus 7fb2088f**: two new contracts, one source evidence record (contexts.py actual SHA256 `dab9aab464b3090464efccc7e156c298bfe1eb51deb43f00d3b8514c1a0fb5e0`), additive notes in reviewed design/control docs. Their original bodies and OC01–OC18 definitions remain unchanged. Runtime/schema/SPEC/tests/workflows/old source pins/protocol/receipts unchanged. Ten relative link paths resolve, changed whitespace clean; primary SQLite mechanisms checked read-only. No new tests for docs/data-only change.

**No helper/VFS/authority resolver/Facts adapter implemented or tested. OC controls executed=0; no current Dev or backend values observed.** No live calls, native OpenCode method/constructor, compiler/dependency install, pilot, model/provider/API/key/custody, merge/release or #112 change. Next: independent contract review, then one bounded source package with real SQLite/native/filesystem/resolver/verifier controls; actual pilot still requires all six gates and separate finite approval.
Keep draft; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; #80/#96/private bindings unchanged.

---

## Earlier named-head design checkpoint (historical)

## OpenCode handoff — passive observation design, no runtime action

Head `7fb2088f3fb312438cbc70e47c33160a985818db`; base main `d7515c5fb4e33b41f81a8535fb06a0ea2cd72255` (merged through #116).
Operator explicitly selected **“เลือกให้เริ่ม OpenCode integration design ชุดนี้ได้”**; exact timestamp NOT_PROVIDED.
Separate from paused draft #112; no J0 resumption, Dev/backend call, pilot or merge approval.

[Design and six pre-pilot gates](https://github.com/sc28249782/hermes-mcp-bridge/blob/7fb2088f3fb312438cbc70e47c33160a985818db/docs/OPENCODE-HANDOFF-INTEGRATION-DESIGN-TH.md)
/
[Preregistered OC01–OC18 controls](https://github.com/sc28249782/hermes-mcp-bridge/blob/7fb2088f3fb312438cbc70e47c33160a985818db/docs/OPENCODE-HANDOFF-CONTROLS-TH.md).

Existing status/result/recent reconcile ALL pending/running jobs, and the enabled constructor creates/chmods state/schema/audit. Therefore proposed first source profile does not call native methods or instantiate OpenCodeTasks. It passively observes ONE already-known original completed job, checks current authority/dossier/job/request/session/fingerprint/workspace/model/provider/binary/context identities, independently verifies exact goal evidence, then feeds the existing pure advisory planner. No submit/replay/cancel/resume/health/model/network or stored-PID signalling; unknown ID/active/uncertain state HOLDs.

SQLite mode=ro/query_only alone is not proof of no-write safe capture. Concrete consistent snapshot/journal/retained-identity method remains a source blocker: no immutable=1 on live DB, unsafe DB copy/full prompt-bearing backup, recovery or permission repair. Physical shared DB page access requires explicit authority even with logical single-row SELECT. Output pages/replacement-decoded text cannot prove full-byte artifacts.

Current authority/Facts resolver, missing model/binary fields in old schema, null/unknown context policy and independent original-goal profile are explicit blockers, not silently filled. No default context_open=True, caller Facts/verifier bool, raw prompt/ID/path/output/fingerprint disclosure, schema/runtime amendment or false goal/cessation claim. Proposed owned helper/owner budgets require source enforcement/feasibility before a separately approved one-observation pilot.

Docs/data only: design + control preregistration + six actual baseline source SHA256 pins + additive ROADMAP/offline-closure notes. **333 additions, zero deletions, five files.** Old history/source/schema/tests/workflows/protocol/400 arm-trial receipts unchanged. 102 relative paths resolve; changed whitespace clean. No new tests for docs-only design, no runtime test/pilot/evaluation or measured gain; exact-head CI reported separately.

No OpenCode live version/model/endpoint/job/session/path facts are observed or invented. All six execution gates remain UNBOUND/NOT AUTHORIZED. No MCP/bridge config/tool surface/SPEC change; section 14 review required before implementation merge for new runtime/privacy/authority interfaces. No provider API/key/tool/secret action.
J0 PAUSED at #112 e7142cf7; R1 NOT AUTHORIZED / R2 HOLD; #80/#96/private bindings, S24 rows and recorded signed v1.2.8 release/deployment unchanged.
Keep draft; ready for independent DESIGN/source-analysis review only.


### Exact design-head validation

At `7fb2088f3fb312438cbc70e47c33160a985818db`,
[Tests 41597039766](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41597039766) SUCCESS.
Inspected jobs 125786716607 (3.12) and 125786716965 (3.14) each report **Ran 234 tests / OK**.

Only the five docs/data files changed (+333/-0); runtime/source/schema/test/workflow/protocol/receipt blobs remain byte-identical to base main. Handoff offline/evaluation and S24 workflows are path-filtered, not disabled/edited or claimed newly run. Development/heldout guards remain false in unchanged source. No OC01–OC18 execution, Dev/backend probe, model call or pilot.

102 relative link paths and changed whitespace checked; source pin record uses six actual SHA256 values, including unchanged schema pin 3dc3f73a…. Existing #112 independently re-read: draft at e7142cf71792475af9375140df39acd55944d8d1 unchanged, J0 still paused.

CI is baseline regression, not design acceptance, live capability, safe SQLite capture or runtime recovery proof. Ready for independent design/source-analysis review; keep draft/unmerged. Source/capture/authority/context/goal-verifier and the six finite-action gates stay OPEN/UNBOUND.


### Exact contract-head CI and isolation

At `a8008dfc537114babbe68c966af4c1decbf1da3f`,
[Tests 41599870348](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41599870348) SUCCESS.
Inspected jobs 125795814445 (3.12) / 125795814256 (3.14): **234/234 OK** each.
Other S24/handoff workflows are path-filtered by this docs/data delta; no workflow or consumed experiment guard changed.

Exact incremental diff five files +375/-0; original reviewed design and OC definitions preserved underneath additive notes. Runtime/schema/SPEC/source/tests/old source-pin record/protocol/receipts unchanged. No new controls executed and no capture/adapter/Dev/pilot result. Relative paths and changed whitespace checked.

Fresh #112 read confirms same draft e7142cf71792475af9375140df39acd55944d8d1, still J0 paused. CI is baseline regression only. Contracts require independent review, including shared-read-lock contention, VFS/dependency/retained-FD feasibility and Facts/current-versus-historical/context semantics, before source implementation acceptance. Keep draft; R1 NOT AUTHORIZED / R2 HOLD.
