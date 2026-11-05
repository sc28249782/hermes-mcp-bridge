# L1 feasibility contract — exact-child WAIT and pre-armed inert-H exit

วันที่: 5 พฤศจิกายน 2026 (Asia/Bangkok)
Input: PR117 `69fe8874ab33fd5ecfa1cf396209182238149593`
สถานะ: **PROPOSED DESIGN / NOT IMPLEMENTED / L1 UNPROVEN-HOLD**

## 1. Checkpoint / authorized scope

Round-22 APPROVE AS DESIGN (bounded correctness decision) at input head is
operator-supplied review, not GitHub submission; no review timestamp invented.
ผู้ใช้สั่งขั้นถัดไปหลังข้อเสนอ L1 feasibility contract จึงเดิน **contract investigation**
นี้เท่านั้น ไม่ใช่เลือก production profile, grant numeric targeting หรือ run experiment.
[Live-loss decision](OPENCODE-HANDOFF-LIVE-HANDLE-LOSS-DESIGN-TH.md) ยังคงเดิม:
L0 destructive live-close experiment HOLD; LH01–LH08 NOT RUN.

L1 proposes a separately admitted non-signalling exact-child wait path plus a
source-bound inert H exit route installed before any destructive fault.
Neither source/runtime/SPEC nor previous contracts/tests/manifests/workflows change.
No child launch, signal, timer installation, pidfd close or host inspection occurs.
This is not an effective amendment or evidence that L1 is safe/production-feasible.

## 2. Fixed actors and proposed authority split

Fresh B launches E; E directly creates one inert H with one pidfd. No R/O/S/native
SQLite helper/CLI/model/backend/G; E/H=2 fixture actors plus B, no guardian process.
No extra pidfd held by B/diagnostic. Proposed single-thread E alone owns child wait.
H has no descendants/exec/arbitrary input and follows a reviewed closed fixture path.

| Role/path | Proposed finite authority | Explicitly absent authority |
| --- | --- | --- |
| B | Launch/wait/reap its exact E and collect bounded report | Not H owner/reaper, host census or external containment |
| E pre-fault candidate | Existing exact retained-pidfd lifecycle path and freeze loss outcome | No signal after last pidfd loss; no reacquire/backup |
| E test teardown path | After frozen result, separately admitted waitid(P_PID, trusted_birth_pid, ...) for that sole direct H | No kill/killpg/tgkill/numeric signal, arbitrary PID, any-child wait/discovery |
| H | Close itself on gate EOF or pre-armed local expiry under fixed source | No signal to another actor, timer reset/replacement, external work |

This is an explicit change from reviewed P_PIDFD-only exact reaping, NOT the old
profile in disguise. Numeric WAIT is different from numeric SIGNAL; both still
need their own project authority. Production candidate cannot obtain this private
test path just because an implementation shares E's address space.
That logical separation is not hostile-code/kernel isolation.

## 3. Birth identity / no-reuse conditions

E must record a one-shot immutable-in-source birth record from its OWN successful
create return before readiness/fault admission: exact child PID correlation,
E lifetime, role, attempt/generation/source/FD-map, original T0/Ta/D and consumed bit.
It is not caller/checkpoint PID input. Failure to retain a coherent record means
do not close the pidfd; no scan/retry/alternate birth or guessed-number repair.

Before close, exact pidfd wait observation and the stored birth result must agree
on the direct child where observable; readiness/live evidence and source binding
must be recorded without keeping a second handle. A not-ready poll alone is not
proof of correct identity or a future stop guarantee. The pre-close live oracle
must distinguish H alive from exited/unreaped and record actual fault ordering.

Required E conditions: SIGCHLD explicitly set/read back without SIG_IGN or
SA_NOCLDWAIT, no other thread/handler/waiter consumes child status, no E restart/
exec/fork-copy/adoption and no unaccounted child creation. The exact unreaped-child
correlation must remain valid until this path consumes it once.
These are source/runtime proof obligations, not implied by a saved integer.
If a concurrent reap/auto-reap invalidates provenance, reject; never reinterpret
another child with a reused number as H. No PID namespace/host-scan workaround.

The birth record is proposed private test metadata, not a restored pidfd, current
issuer/cleanup grant or rollback-resistant B3 anchor. Arbitrary corruption of both
record and authority remains outside demonstrated protection and production OPEN.

## 4. Stop route before destructive close — experiment subset only

The proposed H is a fixed inert userspace fixture, not a possibly blocking native
DB/helper. It must install/read back its signal disposition, unblocked expiry
signal and one-shot local exit timer before READY. READY also binds source/role/
attempt and original expiry reference. E checks source-bound fields and remaining
budget; a readiness claim alone is not independent kernel timer attestation.

Proposed schedule, all charged to the inherited deadline:
- D=min(Ta+20s,T0+45s), or inherited stricter min(Ta+8s,T0+45s).
- Destructive close must complete before D−3s; late close admission is denied.
- H's fixed expiry is D_H=D−2s, installed from remaining original time before READY.
- Gate writer closure may end a cooperative H earlier; the nonreading fixture
  waits in its reviewed userspace path for its already-armed local expiry.
- Remaining interval until D is for exact wait consumption, stream EOF, record
  and E/B closure. The two seconds are an allocation of existing reserve, not
  a new guaranteed cleanup allowance or proof that cleanup fits.

The H timer deadline is earlier than existing cell fixture's D alarm: this is a
proposed fixture-source/timer delta, NOT a statement that old source implements it.
No timer begins at close or after loss; no heartbeat, extension/re-arm or retry.
It does not modify the original native helper alarm1s or production stop budget.
Expiry handler may only perform reviewed local exit; no parent/foreign targeting.

Timer delivery/scheduling, blocked signal, altered handler, uninterruptible I/O,
unexpected library/syscall or E/B failure can defeat completion. No real-time
guarantee is asserted. Negative timer/source-readiness controls must reject BEFORE
closing the sole pidfd, while the admitted original cleanup route remains intact.
Deliberately disabling H expiry AFTER destructive close is NOT an admissible test
without another reviewed stop/containment capability.

**Residual admission gap remains:** this cooperative/self-expiry proposal is not
an independently enforced hard stop. If LH admission requires fault coverage it
cannot supply, L1 experiment stays HOLD even if the reaper contract is accepted.
Do not run first and rely on host cleanup, E exit/adoption or an undisclosed signal.

## 5. Freeze / exact wait / EOF ordering

1. Validate finite profile, original deadlines, source/FD map and consumed birth
   record; confirm H live and stop-route readiness before close.
2. Close the actual last H pidfd once; record fault. Candidate denies target
   operations and freezes UNKNOWN/unconfirmed lifecycle result. No G/next launch.
3. Test teardown may close its fixed gate writer, then wait non-signallingly for
   that bound H under the pre-armed exit schedule. This is test-only data.
4. Use bounded waitid(P_PID, birth_pid, WEXITED|WNOHANG|WNOWAIT) observations.
   Nonterminal/no-event results are not reap receipts. Repeated matching
   pid/code/status observation precedes ONE consuming wait for that SAME child.
5. Retire birth record after consumption; subsequent ECHILD may corroborate
   consumed status but cannot replace the successful matching wait record.
6. Independently verify actual helper stdout/stderr EOF and all retained writers
   closed; compare frozen candidate before/after teardown, publish separate facts.

Concrete implementation must define a finite wait-observation count/readiness
schedule before source review. No busy wait/unbounded poll/retry is admitted here;
WNOHANG flags by themselves do not make the outer loop bounded.
No waitpid(-1), P_ALL consuming wait, PID/PGID signal, pidfd_open, duplicate handle,
SCM_RIGHTS/pidfd_getfd, /proc scan, role respawn or E2 watchdog fallback.
P_ALL remains only the isolated-E no-children oracle, if used, not target discovery.

Missing exit/matching consuming wait/stream EOF => STOP_UNCONFIRMED/HOLD in lifecycle
report; candidate observation stays UNKNOWN even if test teardown fully succeeds.
No data/native/original FINAL, goal result or source authority is synthesized.
no_children=true remains isolated E's own waitable children at that point; B's
exact E reap is not independent H/host-wide no-orphans proof.

## 6. L1F01–L1F12 preregistration — all NOT RUN

| ID / mapping | Required owned stimulus / oracle | Acceptance-or-HOLD |
| --- | --- | --- |
| L1F01 / LH01,02 | Actual H-live observation, sole pidfd inventory, ordered last-close | No post-reap substitution or backup; source-bound admission before close |
| L1F02 / LH04 | Correct/forged/missing/stale birth record and generation/source | Only E's exact unreaped direct child; invalid records reject pre-close |
| L1F03 / LH04 | SIGCHLD SIG_IGN/SA_NOCLDWAIT and competing waiter conditions | Reject before destructive close; no numerical reuse inference |
| L1F04 / LH01,03 | Cooperative H EOF after actual live-close | Frozen candidate UNKNOWN; exact P_PID reap and separate EOF |
| L1F05 / LH01,06 | Nonreading userspace H reaches pre-armed D_H | No numeric signal; real exit/wait/EOF within original D or HOLD |
| L1F06 / LH06 | Missing/blocked/late/changed expiry readiness | Pre-close rejection while original pidfd retained; no unsafe post-close sabotage |
| L1F07 / LH04 | Early H exit, repeated WNOWAIT, duplicate consume attempt | Separate not-live stimulus from live test; one consume, record retired |
| L1F08 / LH04 | Closed fd reused for unrelated pipe/child metadata | No FD/PID substitution targeting; if safe fixture unavailable, HOLD/NOT RUN |
| L1F09 / LH05 | E/B loss around record/close/wait phases | No containment claim; destructive case requires separate safe profile or remains NOT RUN |
| L1F10 / LH06 | Late fault/full or retained writer/resource/I/O conditions | No fresh time; partial wait/EOF/stop evidence stays unconfirmed |
| L1F11 / LH02,07 | Source-call graph, finite waits/messages/FDs/actors/resources/privacy | No hidden cleanup, unbounded loop or raw PID/path exposure |
| L1F12 / LH03,08, OA12 | Teardown success with missing original FINAL/goal | Frozen UNKNOWN unchanged, no action/capture/goal upgrade |

All expected outcomes above are preregistration, not measured results.
L1F01–L1F12 and LH01–LH08 NOT RUN. SM02–SM05/PB02/PB03 remain PARTIAL.
No prior cell14/atomic16/CI count substitutes for new obligations.

## 7. Change control / source delivery gate

| Proposed delta | Required before implementation integration/merge |
| --- | --- |
| E retains trusted numerical birth correlation for test reap | SPEC §14 security/reaper boundary review, closed schema/provenance and no-signal audit |
| P_PID wait instead of P_PIDFD in test teardown | Named finite grant, no-auto/concurrent-reap proof and exact consuming status controls |
| H pre-armed D_H expiry/READY fields | Closed fixture source/timer/FD map, source binding, original reserve accounting |
| Candidate vs test teardown result | Fixed private records, freeze checks, no public-state/goal semantics change |
| E/B/timer failure | Accepted extra boundary or explicit residual HOLD; not waived by narrower positive test |

This document does not amend [SPEC §14](SPEC.md#14-change-control), select a
deployment profile or authorize the proposed source path. No production numeric
wait recovery or stopping mechanism is introduced. Runtime guards remain intact.
Next source package is permitted only after the specific reaper AND stop-route
admission gaps are resolved in review; contract approval alone is not ARM/run.
If a finite safe teardown cannot be demonstrated, retain L1 UNPROVEN/HOLD and
return to another scoped obligation. L0 unchanged-profile HOLD is not reversed.

E/H/B and any added FD/timer/message/stack/CPU/RSS overhead must be measured.
Per-actor256MiB/core0 caps are not aggregate/B6 proof; control≤512bytes and ≤24
messages, stdout≤64KiB/stderr≤4KiB bounds remain requirements. No new actor allowed
by this paper. Actual numeric birth correlations remain private; public evidence
uses role/attempt refs, expected/actual facts and safe locators only.

## 8. Evidence provenance / history / status

Primary interface background:
[waitid P_PID/P_PIDFD/WNOWAIT](https://man7.org/linux/man-pages/man2/waitpid.2.html),
[unreaped-child correlation conditions](https://man7.org/linux/man-pages/man2/pidfd_open.2.html),
[timer signal semantics](https://man7.org/linux/man-pages/man2/setitimer.2.html).
These document Linux interfaces, not a Hermes grant, timer hard-stop guarantee or
production feasibility. L1 safety reasoning is explicitly a proposed contract.

The prior PR body approached its size limit. Its exact UTF-8 snapshot is preserved
in [history at 69fe8874](OPENCODE-HANDOFF-PR117-HISTORY-69FE8874.md), without adding
a heading/newline or rewriting old failures/results. Bytes=64468,
SHA256=8a4e536f60a7984e19f8c3b862aaf5f303a3eff6be4bd1543896bb033f502580.
The snapshot intentionally retains the original final blank line: diff --check
reports new blank line at EOF there. Contract whitespace is clean; snapshot bytes
are preserved rather than silently normalized. This is a disclosed archive exception.
New-head CI belongs in the current PR body, never relabelled as old-head evidence.

Evidence record: requirement=L1/LH exact-reap plus safe stop admission; expected=
finite owned inert protocol; actual=design only; source/runtime/private locator=
UNBOUND; new contract independent review=PENDING. No local runtime rerun.
Broad local baseline NOT PASS unchanged. B1–B7/B4 OPEN; SM01/06–12 NOT RUN;
SM02–SM05 PARTIAL; PB02/PB03 PARTIAL; PB01/04–11 NOT RUN; OA07/OA12 NOT RUN.
Draft/unmerged; J0 PAUSED (#112 e7142cf7); OC18 NOT RUN;
R1 NOT AUTHORIZED / R2 HOLD. No Dev/pilot/original invocation, backend/model/API/
credential/config/checkpoint/archive trial/release/deployment.
Design acceptance/green regression is not an effective amendment or action approval.
