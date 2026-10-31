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

## E4 — joined collect/local carrier fixture delta

`joined_collect_fixture.py` reuses the pinned baseline synthetic input builder,
then calls the unchanged observed helper collect with real Marker writes. Hash
constants and fixed system-read results are injected only for those synthetic
inputs, as in E1. The synthetic ELF input includes a bounded 16 MiB read/hash
workload within the existing input limit; it is never executed. No sleep, SIGSTOP,
ACK wait inside collect or production timer change is introduced. A ten-second
fixture alarm is independent of, and does not extend, production budgets.

`test_joined_collect.py` uses real procfs/pidfd admission and actual entry/leaving
pipe events. Its fixture coordinator drains, calls Window.pre, reads real local
Linux MemAvailable through a bounded JSON pipe frame, then drains and calls
Window.post only after the sample finishes. The natural case records either a
confirmed fixture-only causal window or explicit fast-collect HOLD without retry.
There is no requirement that a naturally fast worker produce a passing window.

The exit-during-sample case stops only the test-owned Popen child from inside the
sample producer. The leaving-before-post case waits for actual worker exit before
post. Both must reach an opened window and complete a sample, then reject post;
fast completion before their stimulus is a test failure, not substitute coverage.
Each prints an outcome/sequence receipt with false R1/R2 flags, checks pipe EOF and
worker reap, and retains the original mandatory coherence controls. Suite count:
66 + 3 = 69. Existing tests remain unchanged.

This adds fixture-based joined evidence for rows 3/5/6/17, not acceptance closure.
The carrier is a local Linux pipe; coordinator is test code, not Observe-S24Host or
the guest wrapper run loop. It does not prove Windows CIM inside an inventory
window, SSH transport, operational source pins/inputs, host identity, production
stop authority or full writer cessation. Actual joined production-carrier and
coordinator/provider/output/log/deadline/stop obligations remain OPEN. No ledger
row is closed or reclassified here; continue this same draft PR.

## E5 — checked host coordinator and failure matrix (source change)

This increment changes production PowerShell: Observe-S24Host now loads the
separate HostCoordinator function from exact checked bytes with a new SHA pin and
private-ACL admission. Bootstrap/config/path/support/sampler admission stays in
the entry script. The coordinator retains the same before/during/after sample
and transport checks, 3 s child/1 s reported sample checks, and 92/95 s bounds.
Its state object retains the actual children for the entry script's existing
scope-controlled cleanup. The same coordinator instance cannot be invoked twice;
reuse after success or failure latches HOLD before another process factory call.

Test-WindowsCoordinator invokes that production function with only process
creation and new-fixture-config writing substituted. All fixture processes are
real, owned pwsh children. The factory never invokes SSH/CIM, even if a configured
executable is unexpected; source/hash/ACL bootstrap of the main entry point is
outside these tests. E3 remains the separate actual pinned-CIM/ACL evidence.
This delta is not a joined production SSH/collect/Windows-sample route.

The 16-case matrix covers successful frame/sample/log order; low/late-reported/
missing/corrupt/stderr/blocked/wrong-binding providers; wrong-challenge/EOF/
corrupt/partial/flood transport; closed log before/during and log budget exhaustion.
Negative cases require HOLD, no after sample, no accepted fixture post, and no new
launch on repeated invocation. The blocked provider exercises the unchanged 3 s
I/O deadline. Test cleanup verifies no-termination permission refusal for that
still-live owned sample child, then explicitly permits only fixture-child stop.
It does not approve operational termination flags or prove a blocked CIM service
has stopped. Log write faults use actual disposed streams; log Flush/fsync and
blocked-output/start/outer-owner/deadline enforcement obligations remain OPEN.

The first matrix run exposed a real exited-transport cleanup defect: buffered
stdin disposal could raise IOException after failed post delivery and bypass the
remaining handle disposals. HostSupport now tolerates that stdin cleanup error
only after the retained child is known exited, and always attempts remaining
handle disposal in finally blocks. This grants no input-delivery proof; the
coordinator's failed exchange remains HOLD. KILL(false) authority and start/handle
revalidation are unchanged. Dependent support/sampler pins are recomputed, not
relaxed. Earlier reviewed unchanged-PowerShell statements describe earlier deltas,
not E5. Existing 14/9/10 Windows suites and Linux 69 controls stay enabled.

Exact runtime source hashes for this increment:

- Observe-S24Host.ps1: `8ea28ed095904039b778bdd0c9b97b65a369b7cd1148447a1657674a22eaca8c`
- HostCoordinator.ps1: `38d8c10208b8816c95f46c21c7448db4f905d8967e2bc29bc4f8ec5392dc6151`
- HostSupport.ps1: `9724d3ce4fb68f2172ce18ae9ed6006443077de94358aa46d1a23846f95f8180`
- Read-S24HostSample.ps1: `79ed818637b4a26a07f36fca4c8645446a2a5eab7a6882f37cab610f130cc3b3`

Rows 9–14 and A3 receive coordinator-level fixture evidence only. Source acceptance,
actual SSH transport/collect join, operational deadlines/stop and A6/A7 private
bindings stay OPEN pending independent exact-source/evidence review. Keep this
same PR draft; no matrix disposition or runtime scope is issued by E5.

## E6 — real OpenSSH loopback / production coordinator contract fixture

The CI-only carrier job runs the existing HostCoordinator and HostSupport on
Linux PowerShell Core with an actual OpenSSH client; its process factory is not
replaced. Only new-config writing is substituted because Windows ACL admission
is outside this Linux fixture. Sample and remote peer are protocol fixtures, not
CIM or inventory. This connects the production coordinator's exact hardened SSH
argv to a real encrypted/authenticated loopback transport, without asserting the
R1/Tunnel authenticated flag or host identity. E4 collect and E3 CIM evidence are
still separate, not a complete production collect/Windows-sample join.

The harness refuses execution outside root on GitHub-hosted Linux CI. It creates
one fresh fixture account with an empty private home and /bin/sh, new Ed25519
host/client keys, exact known_hosts and a foreground sshd bound only to loopback
port 22229. The invalid password hash is not a password; password/keyboard/PAM
and root login are disabled. Existing accounts, SSH config, services, keys and
authorized_keys are never edited. The new account must not exist before the test.
ForceCommand runs only the copied fixture peer, which rejects an unexpected
SSH_ORIGINAL_COMMAND. The peer can exchange frames but cannot run inventory,
backend tools or arbitrary original commands. Its wait is not a collect delay.

Actors include the root CI harness/foreground sshd and SSH privilege-separation
children, owned PowerShell driver/sample/client processes, and the fresh-account
forced peer. This is disposable CI infrastructure, not an operational stop model.
Teardown stops only the retained sshd pidfd and newly owned driver/child instances;
the new account is removed only after its UID has no processes. A driver timeout
stops only its own new session and fails without retry. No key bytes or server
logs are printed/uploaded; private fixture files remain for runner teardown.
The stock /run/sshd directory is created only if absent, never repaired/replaced.
If required tools/account isolation/bind/host trust are unavailable, the job fails;
there is no package installation, alternate port, existing-account fallback or
host-key acceptance. No SSH/account/key operation is performed on an operator host.

Three independent cases use the same one-job fixture server: successful frame
exchange with exact post trace, wrong challenge yielding HOLD without post, and
wrong known host key yielding HOLD before the forced peer starts. Each records
false scope flags, requires no after sample on failure, and rejects coordinator
reuse. ResourceWarning is fatal and the complete harness output is scanned after
process exit for ResourceWarning/finalizer markers, even when it fails. The
three-case completion marker is mandatory. There is no automatic connection retry.
These are carrier-contract tests,
not authorization for a finite operator R1/R2 attempt. Keep actual Windows entry
bootstrap/ACL/CIM, collect join, operational supervision/cessation, real identity
transitions and A6/A7 bindings OPEN pending independent review.

## E7 — exact Windows entry/bootstrap/ACL/config-write/CIM path

Test-WindowsEntry runs byte-pinned copies of Observe-S24Host, HostCoordinator,
HostSupport, Read-S24HostSample and HostMemory as real Windows processes. It
replaces no functions, process factory, source loader, config writer or CIM
provider. The only transport is a compiled console fixture selected as the cfg.ssh
executable; it validates the hardened argv, exchanges the existing frame contract
and has no SSH/CIM/inventory/backend execution capability. Its receipt hash is a
fixture value, not an inventory receipt. E6 is still the separate actual SSH test;
E4 is the separate collect test. This does not join them into one production path.

The new CI driver is guarded to GitHub-hosted Windows. EntryFixtureOwner sets
only that new driver's token default owner to its existing user SID, inherited
by its children; it does not change user, groups or privileges, impersonate,
modify another token, or install a runtime helper. This is a test precondition
for elevated CI's default Administrators ownership, analogous to explicit fixture
file ownership. A newly created probe must already have the correct owner without
repair. Only new fixture-directory ACLs are prepared; no existing file/account/
service/credential or operator host is touched. Production ACL gates remain exact.
If token setup or the installed .NET Framework compiler is unavailable, fail;
there is no policy relaxation, package installation or unreviewed fallback.

Six cases require: success with three actual pinned-CIM samples, six log records
and a post-received peer trace; wrong challenge with before-only observation and
HOLD; broad config ACL, coordinator drift, sampler drift and preexisting log
rejected before any sample config or transport peer. The existing log bytes must
be preserved. The real entry's termination flags are both false. Test teardown may
stop only its newly owned entry child on failure; this is not operational cohort
or provider-cessation proof. Entry output/exit and source-created sample files,
log and peer trace distinguish success from HOLD. Existing budget/false-flag gates
are unchanged; all runtime sources/pins remain byte-identical to reviewed E5.

The runner adds six entry cases after the existing Windows 14/9/10/16 suites.
It queries CIM on the CI machine only. No real SSH, collect, operator resource,
host identity, R1 completion, R2 authorization or A6/A7 binding is claimed.
Operational joined carrier, outer deadline/stop/writer coverage and identity
transition/reuse disposition remain OPEN. No row closes automatically; keep draft.

## E8 — real identity transitions/reuse and CI carrier capability facts

The namespace-only Linux job runs on both supported Python versions. It requires
root on GitHub-hosted Linux CI and creates private PID and mount namespaces with
new procfs. Before the only ns_last_pid write, require PID 1, namespace inode
changes from the outer harness and /proc/self/stat PID coherence. The setting is
virtualized per PID namespace ([Linux man-pages](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html));
there is no host sysctl write, host PID-max change, existing account/service action
or fallback. Unavailable namespace privileges fail the control, never skip it.
Root-owned NEW exact-hash source copies satisfy the unchanged loader owner gate;
the checkout and runtime predicates are not repaired/relaxed.

Actual ReadOnlyWorker admission/pidfd/identity reads are used throughout. Three
cases require real exec to a different binary/argv with the same PID/start ticks;
real UID/GID drop to 65534 while the worker remains live (false or unreadable
identity must fail closed); and exact numeric PID reuse after exit/reap with
changed start ticks, new live adoption and a still-dead old retained handle.
No mocks supply identity/liveness/start ticks. Cleanup uses a separate parent-
owned pidfd for the test's direct child, never signal authority on the read-only
observer handle. The 10-second child and 35-second namespace deadlines are fixture
bounds; no inventory worker/collect executes or is delayed. The unshare parent
uses kill-child containment on its own namespace init; outer timeout is 45 s.
Post-exit warning scans and the three-case completion marker are mandatory.
These are identity primitive controls, not full wrapper/SSH/cessation acceptance.

WindowsCarrierCapabilities records only CI image client/server file presence,
service status and WSL/VirtualMachinePlatform feature states. UNKNOWN values stay
unknown; no guest or SSH server is started, no feature enabled, package installed,
service changed or operator machine queried. Binary/feature presence is not a
working route. Actual results must guide the next Windows join design before
adding another substitute-path test. This inventory is not a passing R1 control.

Existing Linux 69, Windows 14/9/10/16/6 and E6 carrier controls remain unchanged.
A4 receives real exec/UID/reuse evidence only after exact-head CI and independent
review. No ledger row closes automatically. Full Windows/collect/CIM route,
operational supervision/stop/writer coverage and A6/A7 bindings stay OPEN.

## E9 — next joined-path design, before provisioning

[Windows/Linux join proposal](WINDOWS-LINUX-JOIN-PLAN.md) corrects the direction:
Windows needs the SSH client; sshd belongs in the Linux guest, so missing Windows
sshd is not a production prerequisite. It proposes conditional fresh-WSL2 CI
setup with UNBOUND rootfs/kernel/source/lifecycle controls, declares fixture-only
controller/readers versus operational R1, and requires measured causal timing
before any sampler actor/lifetime change. It adds no controls/runtime/provisioning
or gate closure. Review route/actors/failure/stop design before setup source;
continue on #112. Existing operational and A6/A7 gaps remain OPEN.

## E10 — partial J0 capability and provider-source binding

[E10 review packet](J0-CAPABILITY-SOURCE-REVIEW.md) binds the Microsoft WSL metadata
commit/blob/bytes and selected Ubuntu-24.04 amd64 URL/provider-reported archive
digest. No archive bytes were downloaded/verified or contents inspected. The
CI-only Windows capability script adds bounded fixed-path file/image snapshots;
it invokes no WSL/SSH binary or guest. These snapshots do not establish configured
kernel/client admission, boot/pidfd/route readiness or existing-distro inactivity.
J0 remains NOT READY, with exact artifact/setup/lifecycle/source bindings still
UNBOUND. Review this source/capability checkpoint before preparing setup source,
then review provisioning separately. No ledger row/source acceptance/operational
scope closes; runtime/pins and existing suites stay unchanged. Keep #112 draft.

## E11 — artifact-preparation source before guest setup

[Exact preparation-source review](ARTIFACT-PREPARATION-REVIEW.md) supplies a fixed
provider URL/digest/receipt pin, bounded HTTPS/temporary-file/hash-before-parser
inspection driver and thirteen offline synthetic controls. CI executes those
controls only; the live download command is not wired in or executed. The driver
cannot extract, install, invoke WSL or provision even on success. Header catalog
and selected regular-file hashes are not a complete content tree/prepared image;
links remain unresolved. Actual archive evidence, guest package/image/setup
source and Windows kernel/coexistence/owner/stop bindings remain missing. This is
the artifact-preparation portion for source review, not completion of setup or
J0. No row closes and runtime/pins/timers remain unchanged; keep #112 draft.

## E12 — operator-directed single CI archive inspection

[Single-attempt record](ARTIFACT-ATTEMPT-RECORD.md) adds one exact-source-pinned
CI execution of the approved E11 preparation driver. A unique checkpoint subject
and run_attempt=1 prevent later commits/reruns from silently downloading again.
The actual live outcome must be appended; source wiring alone establishes no
archive evidence. No provisioning/extraction/setup, retry or alternative route
is included. Reviewed runtime/pins/preparation source and existing tests remain
unchanged; keep all outstanding J0/operational bindings and #112 draft status.

E12 actual result at `2bf5741a`: run 41170222586 / artifact job 124446375046
returned constant HOLD, preparation exit 2, warning markers empty; the exit gate
failed correctly. Failure stage/download/hash/parser progress remain UNKNOWN and
no archive receipt was emitted. See the attempt record/JSON; no retry or local
fallback occurred. Setup remains BLOCKED. The following docs-only checkpoint
skips the consumed live action; green regression CI cannot replace failed live
archive evidence. R1 NOT AUTHORIZED; R2 HOLD; no row closes.

## E13 — diagnostic source candidate, no second attempt

[Finite diagnostic contract](ARTIFACT-DIAGNOSTIC-REVIEW.md) introduces a separately
named E11 variant with bounded stage/error enums and byte/hash milestones; the
old source/controls/pins and E12 failed record remain unchanged. Twenty-five
synthetic offline controls run separately from mandatory 69+13 and do not contact
the provider. No new live selector/wrapper/action is installed. E12 cannot be
retrospectively diagnosed. Review this source/output-contract delta before any
separately scoped/approved attempt; J0/setup/operational/private gaps stay open.

## E14 — disabled two-line CI wrapper proposal

[Finite diagnostic attempt proposal](DIAGNOSTIC-ATTEMPT-PROPOSAL.md) prepares a
strict two-frame gate and exact-source CI wrapper with literal job-level false.
No second attempt is activated. Ten offline synthetic controls supplement the
unchanged 69/13/25 suites. Both wrapper source review and separate finite action
approval precede activation; E12 selector/result and E13 source/pins remain
unchanged. Successful gate evidence would still be inspection-only, not setup/
J0/R1/R2 completion. Keep #112 draft and every outstanding binding/row open.

E14 actual authorized second attempt: activation `a579d7a5`, run 41195199976 / job
124519859911, exit 2/HOLD. Download/hash completed for 388,975,696 bytes with exact
provider digest `bb415d82…`; ARCHIVE_PARSE/PREDICATE_REJECTED at parsed_members=5.
This is a byte/hash milestone, not a complete inspection/catalog/selected-hash or
J0 pass. Specific predicate/member remains UNKNOWN. Exact frame is preserved in
ARTIFACT-ATTEMPT-E14.json. Budget consumed; result commit restores job-level false.
No third attempt/local fallback or parser relaxation. Guest setup and all other
outstanding source/operational/private bindings remain BLOCKED/open.

## E16 — predicate-reason source/schema delta, no third attempt

[Source review](PREDICATE-REASON-REVIEW.md) adds nineteen closed parser reason labels
in diagnostic schema 2, with exact gate validation and unchanged rejection rules.
Current diagnostic producer/gate and disabled proposal pins CHANGE; earlier E13/
E14 source hashes are historical, not current claims. Old attempt records/E11 and
operational runtime/pins stay unchanged. Eleven offline tests cover every label
with real synthetic tar cases or explicitly disclosed reader faults. No third
attempt/activation or parser relaxation is included; all J0/inspection/setup/
operational/private gaps remain and #112 stays draft/unmerged.

## E17 — actual third attempt, type predicate rejected

[Third-attempt record](ARTIFACT-ATTEMPT-E17.md): operator separately approved ONE
E17 CI request. Activation `0a2b07ae` / run 41200750250 / job 124535893803 returned
schema-2 TYPE_REJECTED at ARCHIVE_PARSE, parsed_members=5; full 388,975,696-byte
archive hash again matched provider `bb415d82…`. Gate kept HOLD/exit 2. This gives
an actual rejected predicate, not a specific entry subtype/path or complete
inspection/catalog/selected-hash evidence. Older E14 UNKNOWN is not backfilled.
Budget consumed and job false-guard restored; no fourth attempt/parser relaxation
or setup follows. Review type inspection/admission policy before additional source
or action scope. All J0/operational/private/lifecycle gaps stay open; keep draft.
