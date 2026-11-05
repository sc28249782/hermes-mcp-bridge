# Live-handle loss — safe experiment admission / feasibility decision

วันที่: 5 พฤศจิกายน 2026 (Asia/Bangkok)
Input: PR117 `6873b5030b7ef569a3a83a51855771ad9fc45285`
สถานะ: **DESIGN ONLY / CURRENT-PROFILE EXPERIMENT HOLD / NO NEW GRANT**

## 1. Checkpoint and bounded conclusion

Round-21 APPROVE AS FEASIBILITY EVIDENCE at input head เป็น operator-supplied
review, not a GitHub submission; no review timestamp supplied or invented.
[Cell/view source packet](OPENCODE-HANDOFF-CELL-VIEW-REVIEW-TH.md) และ
[slot contract](OPENCODE-HANDOFF-SLOT-METADATA-CONTRACT-TH.md) คง bytes เดิม
SM02–SM05 ยัง PARTIAL; live H handle loss/full cell erasure/E death ยัง NOT RUN.

รอบนี้ออกแบบ experiment admission ก่อนทำ destructive live-close test
**L0: sole pidfd lost + existing retained-pidfd-only exact stop/reap profile
cannot currently supply the required safe teardown proof → INFEASIBLE/HOLD
for that experiment under the unchanged profile.**
นี่เป็น design inference จาก capability inventory/requirements ไม่ใช่ live counterexample
ใหม่ ไม่ใช่ theorem ว่า Linux หรือทุก possible profile ทำไม่ได้ และไม่ปิด SM04/B4.

No child launched, pidfd closed, process signalled, host inventory inspected or
new syscall probe run for this document. No source/test/manifest/workflow/SPEC change.
No production profile/capability selected; original job/Dev/pilot remain untouched.

## 2. Fault partition — ห้ามเรียกทุกกรณีว่า handle loss

| Fault class | Available retained object | Existing evidence / remaining obligation |
| --- | --- | --- |
| View erased, cell intact | Original exact H pidfd still held by E | Same-E cleanup-only subset exists; no production issuer proof |
| Cell proof field corrupted, FD intact | Original open pidfd remains | Current test-only diagnostic uses SAME handle after frozen result |
| H already exact-reaped, then pidfd closed/reused | No live H requiring teardown | Existing SM04 post-reap pipe-reuse subset only |
| Last H pidfd actually closed while H live | No retained H pidfd anywhere in admitted roster | Live-loss teardown NOT RUN; cannot reuse intact-handle diagnostic |
| FD number overwritten/substituted | Number may now identify unrelated object/child | Unreported replacement detection NOT RUN; number equality is insufficient |
| Full cell/FD metadata erased | Existence and authority may both be unknown | Never infer absent/stopped; no scan or serialized-handle repair |
| E dies | E state/handles/completion unavailable to trusted source path | External containment profile still UNBOUND; B reap is E-only evidence |

A saved integer FD value is not a backup capability once closed or reused.
An unclosed original pidfd with forgotten metadata is a different fault from
closing the last pidfd; a duplicate retained by B/E/diagnostic is an additional
handle even if labelled test-only. Existing atomic lost-slot diagnostic controls
must retain their own disclosed scope; they are not silently selected for L0.

## 3. Required admission before any live-close experiment

All items are required, not alternate ways to declare cleanup complete:
1. Fresh fixed inert E/H plus B only, exact source/role/FD map and original deadlines
   bound before launch; no native helper/database/backend/host target.
2. Independent oracle observes H live BEFORE close and records the actual fault
   boundary; post-reap close cannot satisfy the live-loss stimulus.
3. Candidate sees no retained pidfd/valid target capability after fault and freezes
   UNKNOWN/unconfirmed lifecycle facts before any diagnostic action.
4. A separately reviewed finite test teardown capability covers the exact H AFTER
   loss, including stop/exit, ownership, exact consuming reap and distinct pipe EOF.
5. Teardown still fits original attempt/outer budgets; failure/late I/O remains
   STOP_UNCONFIRMED/HOLD. No kernel responsiveness guarantee inferred from timers.
6. Diagnostic result never repairs candidate cell/grant, reopens G, fabricates FINAL,
   upgrades UNKNOWN or becomes production containment evidence.
7. Oracle and cleanup roles/handles/resources/authority are completely inventoried,
   including B overhead; no hidden fifth role/watchdog or host census.
8. Relevant SPEC §14/profile change has completed its required review before any
   implementation integration/merge; this document is not that amendment or grant.

Under L0 item4 has no accepted binding. Do not create H and remove the last
capability merely to reproduce a predictable cleanup gap. The experiment is
NOT RUN, not a skipped/expected-failure test labelled full acceptance.

## 4. Why existing routes do not discharge L0

| Route | What might be observed | Missing proof / disposition |
| --- | --- | --- |
| Close stdin gate writer | Cooperative H may observe EOF if every writer is closed | Does not force nonreading H exit or prove exact reap/stream closure |
| Existing H self-deadline/alarm | Named fixture may terminate under its source conditions | Not an independent hard-stop guarantee; cannot restore lost wait target |
| Wait on stdout/stderr EOF | Writers closed under the exact FD map | Not identity, exit status, consuming reap or original goal |
| Existing intact-handle diagnostic | Uses same open pidfd for named proof-field faults | Not applicable once the actual last handle is closed |
| B exact-E subprocess wait | E terminated and was waited by B | No independent H inventory/reap/host-wide no-orphans proof |
| Saved PID/FD/current hash/checkpoint | Correlation or metadata | No new retained handle/grant/rollback anchor |
| Exit E to trigger adoption | Parent changes under kernel rules | No accepted exact H cleanup owner or finite terminal proof |
| Any-child wait or host scan | May enumerate/consume unrelated wait state | Not an admitted target discovery/repair mechanism |

No numeric-PID/PGID SIGNAL fallback, pidfd_open/reacquire, duplicate pidfd, /proc
scan, SCM_RIGHTS/pidfd_getfd, respawn, service/cgroup/VM install or E2 chain is
authorized. P_ALL stays only an isolated-E oracle, never a discovery/reap repair.
Current source chooses P_PIDFD for exact child waits; numeric child WAIT is not
a signal, but substituting it changes this specific reviewed reaper profile.

## 5. Alternatives for separate review — none selected

| Candidate | Explicit proposed delta | Open admission requirement |
| --- | --- | --- |
| L0 unchanged | No new capability | HOLD; do not run destructive live-close experiment |
| L1 non-signalling exact-child wait | Preserve E's trusted birth-return correlation and separately admit exact P_PID consuming wait; no numeric signal or any-child search | New reaper/record profile; SIGCHLD/no-other-reaper/identity/reuse controls; independent stop route still required |
| L2 independent retained cleanup handle | Add a declared diagnostic/guardian pidfd before fault | Conflicts with current one-handle/no-backup boundary; separate grant/accounting, not current candidate |
| L3 external containment | Explicit accepted domain stop plus exact reaper/EOF protocol | OA07/EC obligations and SPEC14; no concrete domain selected or installed |
| L4 other workstream | Keep live-loss HOLD and address another already bounded source obligation | Does not close SM04/SM05/PB02/PB03 or waive production requirements |

L1 is only a question for contract review, not a selected safe protocol: even if
exact wait were accepted, it does not itself stop a nonresponsive H or settle E
death/FD substitution. It must not be implemented by silently retaining a numeric
birth target or relabelling numeric signalling as reaping. L2 contradicts the
current candidate's premise and cannot count as evidence that L0 was feasible.
No alternative is promoted through its appearance in this table.

## 6. LH01–LH08 preregistration — all NOT RUN

LH IDs describe admission/evidence obligations, not SM/PB row replacements.

| ID / mapping | Required stimulus or audit / oracle | Acceptance-or-HOLD |
| --- | --- | --- |
| LH01 / SM04 | Actual last-handle close while H independently observed live | Distinguish actual closed object from view loss/post-reap close |
| LH02 / SM04,11 | Complete post-fault handle/role inventory | No undisclosed duplicate/reacquisition/actor or PID/FD target repair |
| LH03 / SM04,05 | Frozen candidate loss result, then separately admitted teardown | Candidate remains UNKNOWN/no lifecycle upgrade; diagnostic separately labelled |
| LH04 / SM07 | Exact owner/reaper, auto-reap/concurrent waiter/FD reuse negatives | Separate exit/consuming wait/EOF facts, no ECHILD-only receipt |
| LH05 / SM09 | E or B death during/after live-close | No trusted completion reconstructed; external scope unbound => HOLD |
| LH06 / SM10 | Late fault/nonreading H/retained writer/full pipe/I/O failure | Same D/reserve; explicit stop/reap/EOF unconfirmed if missing |
| LH07 / SM11 | All actors/handles/CPU/RSS/FD/privacy/records | No hidden budget/guardian; caps not aggregate proof |
| LH08 / SM12, OA12 | Cleanup success with missing native data/original FINAL/goal | No Done/FAIL replacement, original goal join stays NOT RUN |

No new controls executed; prior cell14/atomic16/birth16 are input evidence only.
Next deliverable requires explicit review of a selected alternative's precise
reaper AND stop authority before source work; otherwise retain L0 HOLD and move
to another scoped blocker without weakening live-loss requirements.

## 7. Envelope, references and status

D=min(Ta+20,T0+45), cutoff≤D−3, stricter8s subset only where inherited; no fresh
3/8/20/45s at close/handoff/diagnostic. Shared TERM≤0.2/KILL≤1 phases do not grant
signal authority without target capability. Existing alarm1s/native limits remain
requirements, not new tests here. Actor/FD/RSS/B overhead for alternatives UNBOUND.
No raw private IDs/paths/prompt/output/config/credentials introduced.

Primary Linux interface background checked for this design:
[pidfd objects](https://man7.org/linux/man-pages/man2/pidfd_open.2.html),
[wait/P_PID/P_PIDFD/WNOWAIT](https://man7.org/linux/man-pages/man2/waitpid.2.html),
[pipe EOF](https://man7.org/linux/man-pages/man7/pipe.7.html).
They document interfaces; they do not accept a Hermes authority/profile or prove
deployment feasibility. L0 conclusion above is project-scope reasoning, not a
new measured Linux failure. The [OA07 design](OPENCODE-HANDOFF-OA07-CONTAINMENT-DESIGN-TH.md)
and [SPEC §14](SPEC.md#14-change-control) remain unchanged.

Evidence: requirement=SM04 live-loss safe teardown; expected=full named safety
proof before launch; actual=unbound under L0, no experiment; environment/private
locator=UNBOUND; independent review of this packet=PENDING.
SM02–SM05 PARTIAL; SM01/06–12 NOT RUN; PB02/PB03 PARTIAL; PB01/04–11 NOT RUN;
LH01–LH08 NOT RUN; B1–B7/B4 OPEN; OA07/OA12 NOT RUN; draft/unmerged.
J0 PAUSED (#112 e7142cf7); OC18 NOT RUN; R1 NOT AUTHORIZED / R2 HOLD.
No Dev/pilot/original job/model/API/credential/config/checkpoint/archive/release/
deployment. Historical broad local baseline NOT PASS unchanged. Source/design/CI
review is not action approval, effective amendment or full production acceptance.
