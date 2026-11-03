# Observer implementation package 2 — owned startup/ACK/arbitration

วันที่: 3 พฤศจิกายน 2026 (Asia/Bangkok)
Parent: `dc0199960f463759543d918ec2e32a138cfd691d`, draft PR #117
สถานะ: **OFFLINE STARTUP SOURCE CANDIDATE / รอ exact-source review / B4 OPEN**

## 1. Checkpoint และ finite profile

ผู้ใช้ส่งผลรีวิวรอบ 8 APPROVE preflight/claim/witness ณ parent ที่ระบุ
G ใน Reservation.capture() ยัง deny เสมอและ B4 ยัง OPEN
คำสั่ง “ทำขั้นถัดไป” ให้ทำ bounded offline startup/witness/pidfd/ACK/arbitration
ไม่มี exact approval timestamp; บันทึกเป็น operator-supplied review ไม่ impersonate submission

เพิ่ม [observer_startup.py](../acceptance/handoff/opencode/observer_startup.py),
[22 controls](../acceptance/handoff/opencode/test_observer_startup.py),
[manifest](../acceptance/handoff/opencode/observer-startup-hashes.json) และ
[workflow แยก](../.github/workflows/opencode_observer_startup.yml)
[contract](OPENCODE-HANDOFF-OBSERVER-ADOPTION-CONTRACT-TH.md) คง byte-identical
[preflight source](../acceptance/handoff/opencode/observer_preflight.py) มี exact-budget
correction ตาม CI failure ที่บันทึกใน section 6 ไม่ผ่อน assertion เดิม

**นี่คือ topology prototype ที่ใช้ inert Python H ไม่ใช่ native SQLite helper**
H fork จาก S ตาม fixed internal code; ไม่ exec OpenCode/CLI/native binary
H ทำได้เพียงอ่าน G หนึ่ง byte จาก stdin แล้วเขียน HG1 newline สี่ bytes ไป stdout
ไม่มี DB/context/evidence read, original job, verifier, Facts/planner หรือ checkpoint append
O เป็น fixed byte relay ไม่ใช่ Facts.Owner; S เป็น startup supervisor ใหม่ของ profile นี้
ไม่เปลี่ยน supervision.py/native VFS/accepted capture path เดิม

fixture G เป็น startup probe ของ inert H เท่านั้น
Reservation.capture() เดิมไม่ถูกเรียก/แก้/ปลด deny; protected capture_allowed=false เสมอ
FIXTURE_STARTUP_CONFIRMED ไม่ใช่ CAPTURE_COMPLETE/advisory Done หรือ production permission
ไม่มี public MCP/config/runtime entry ที่ dispatch profile นี้

## 2. Source path ที่ implement แล้ว

| ช่วง | Source behavior / หลักฐาน |
| --- | --- |
| R admission | fresh trusted fixture process เท่านั้น; FixtureIssuer ต้องถูกสร้างใน R และตรวจ current ก่อน claim; reserve single-use claim ก่อน O/S fork; source-file hash เทียบ fixture Binding; claim failure/previous consume ไม่ถูกบันทึกว่า unconsumed |
| R setup | process-local subreaper set+readback; RLIMIT_AS 256 MiB/core=0; existing timer ต้องว่าง; outer SIGALRM ผูก T0+45 ไม่ reset หลัง handoff; old handler คืนเมื่อจบ |
| O/S | เป็น direct children ใหม่ของ R พร้อม retained pidfds; O ถือ lease/write relay; S ถือ helper launcher และ private report writer; fixed FD allowlist ปิด descriptors อื่นด้วย closerange ไม่ scan /proc/process tree |
| H | S fork หนึ่งตัวและ retain pidfd; waitid WNOWAIT ยืนยัน direct child ก่อน witness; H stdin/stdout/stderr redirect ไป admitted gate/proof/error pipes จริง; ปิด FD อื่นก่อน inert body; ไม่ใช่ surrogate EOF channels |
| Witness | S ส่ง private atomic <=512-byte frame; kind/nonce/generation/role/source hash/parent S PID/child H PID ต้องตรงและ exact types; R channel สร้างเองและ S ถือ writer; S ไม่ reap H ระหว่างรอ ACK |
| Retain/ACK | R ตรวจ current O/S liveness และ deadline ก่อน/หลังเปิด H pidfd; ACK แล้วรอ ACKED จาก S; S ต้องเห็น H ยังไม่ exit; revalidate ก่อนส่ง G ไป O; ไม่มี G จาก READY/parsed witness อย่างเดียว |
| Inert proof/FINAL | O relay G; S ส่ง H ครั้งเดียวแล้วปิด stdin writer; H proof ต้อง HG1 newline, exit=0, exact S reap และ stdout/stderr EOF ก่อน S ส่ง typed FINAL; R ตรวจ nonce/types/current authority, O/S exit/reap และ report EOF |
| Failure | bounded CANCEL/owner EOF ก่อน TERM/KILL; O/S stop phase ร่วมกัน; หลัง S reap จึงตรวจ adopted direct-child eligibility ของ H ก่อน signal/reap; signal ใช้ retained pidfd เท่านั้น; unknown identity ไม่ใช้ host scan/PID/PGID fallback |

PID ใน witness เป็น private correlation จาก fixed S call graph ไม่ใช่ caller-supplied target
R ไม่รับ PID/path/argv/callback จาก checkpoint หรือ request JSON
file hash เป็น measured fixture identity ไม่พิสูจน์ loaded-code authenticity,
Python monkeypatch resistance, original-run provenance หรือ production issuer authentication
same-process/same-uid compromise ยังอยู่นอก trust model ตาม contract

## 3. Reaper arbitration และหลักฐานที่ไม่รวมกัน

S เป็น reaper หลักของ H ขณะ S ยังอยู่
R._signal(H) ต้องได้ ECHILD ก่อน adoption และไม่มี signal เกิดขึ้นใน control
หลัง exact S exit/reap: waitid(P_PID,WEXITED|WNOHANG|WNOWAIT) ของ H
ต้องยืนยัน adopted direct-child eligibility ก่อนทุก signal/reap
R ไม่ใช้ waitpid(-1) เป็น production cleanup หรือหา actor อื่นมาซ่อม binding

หาก valid witness ถึง R แล้ว S ตายก่อน capture pidfd acquisition:
ไม่ ACK/G; หลัง S reap และ adopted-child proof จึงเปิด pidfd ได้ **เพื่อ cleanup เท่านั้น**
ถ้า capture pidfd acquisition เคยล้มเหลว จะไม่ลองซ้ำใน cleanup
ถ้าไม่ยืนยัน identity/ownership/stop ได้ให้ STOP_UNCONFIRMED ไม่มี numeric fallback

S reap H ไปแล้วแต่ไม่มี valid FINAL: R เห็น pidfd exit/EOF ได้ แต่ helper_reaped_by=null
ไม่เติมเป็น S หรือ R จากการเดา; observation เดิม UNKNOWN
valid FINAL ของ S ในเอกสารนี้เป็น startup-only report ไม่ใช่ native job result
string true, malformed/duplicate witness, wrong proof หรือ missing FINAL ไม่สร้างผลสำเร็จ

Outcome แยก original_final/helper_launch_known/helper_exit_observed/helper_reaped_by/
stdout_eof/stderr_eof/actors_reaped; null=ยังไม่สังเกต ไม่ default true
actors_reaped นับ direct O/S เท่านั้น ไม่ใช่จำนวนทุก actor ที่หยุด
fixture_g_sent หมายถึง R เขียน G ไป O แล้ว; H รับ/รันจริงยืนยันใน positive path
ด้วย proof+S exit/reap/FINAL ไม่อนุมานจาก write สำเร็จเพียงอย่างเดียว
trace เป็น allowlisted phase labels ไม่มี PID/path/native IDs/raw output
capture_allowed/authorizes_actions/dev_observed/goal_verified=false ทุก Outcome

## 4. Actual controls

Author-local Python 3.12.14: **22/22 OK**, ResourceWarning-as-error, ไม่มี skips
preflight final suite **24/24 OK** รวม deterministic numeric regression เพิ่มหนึ่งข้อ
21 process cases ใช้ fresh isolated R และ fixture objects/anonymous pipes ใหม่เท่านั้น
test runner ตรวจ subreaper setting ของตนไม่เปลี่ยนและ reap R ด้วย retained pidfd
ใน fresh R ใช้ waitpid(-1,WNOHANG) เป็น **test-only** ECHILD oracle หลัง source จบ
ทุก case ที่รันต้องไม่มี live/unreaped fixture child เหลือ ไม่ใช่ universal kernel guarantee

| Family | Actual stimulus และ assertion |
| --- | --- |
| Normal/guard/reuse | actual R→O/S→H forks และ wire trace CLAIM/SUBREAPER/OWNER/SUPERVISOR/WITNESS/PIDFD/ACK/ACKED/FIXTURE_G/FINAL; normal H ถูก S reap; adoption guard deny ก่อน S ตาย; reused Startup object reject ไม่คืน stale FINAL/G |
| No actor admission | unbound containment/dev tag => no claim/no O/S/H; source drift => claim consumed แต่ไม่มี O/S/H; actual fsync failure => CLAIM_UNCONFIRMED+consumed ไม่อ้าง no claim |
| Pre-G rejects | wrong nonce/duplicate witness, revoked issuer หลัง witness, R helper-pidfd acquisition failure, O death, stalled ACK ถึง shared cutoff => no fixture G |
| S death at binding | SIGKILL S จริงหลัง valid witness ก่อน retain หรือก่อน ACK; no G; kernel adoption+retained-pidfd cleanup/reap โดย R |
| Post-G loss | inert H fixture ถึง actual private readiness marker แล้ว ignore TERM; SIGKILL S หรือ O/S จริง; R ยืนยัน adoption ก่อน TERM/KILL/reap และ stdout/stderr EOF; original FINAL หายยัง UNKNOWN |
| FINAL/proof | H เขียน wrong proof จริง => S ไม่ส่ง FINAL; S exit จริงหลัง reap H แต่ก่อน FINAL => UNKNOWN/no invented observer reap; helper_reaped='true' string reject |
| Late publication | หลัง actual FINAL/reap/EOF ครบ inject clock anomaly ก่อนสร้าง Outcome; source ต้อง UNKNOWN/BUDGET_EXHAUSTED ไม่ส่ง startup success ย้อน deadline |
| Identity | manifest ตรวจ actual source/workflow/P/accepted contract hashes และ byte lengths; no skip หาก platform/process support ไม่ตรง |

Fault hooks อยู่ใน controls เพื่อเปลี่ยน frame/เลือก crash boundary หรือใช้ inert H แบบค้าง
fork/death/pidfd readiness/waitid/reap/EOF เป็นเหตุการณ์ kernel จริง
control ที่เลือกจังหวะ post-G อ่านหนึ่ง-byte fixture marker จาก stderr เพื่อยืนยัน H active
ไม่ใช่ normal R data-consumption path และไม่สร้าง accepted capture/goal evidence
development iterations ก่อนสร้าง manifest ไม่ใช่ final pass/trials เพิ่ม
CI ต้องอ้าง exact candidate head/job logs แยก; local broad baseline ไม่ได้รันใหม่
historical local baseline NOT PASS และ root cause UNKNOWN ยังไม่เปลี่ยน

## 5. Budget/resource profile

R ใช้ T0+45 guard และ inherited single-use Budget; default fixture attempt=8 s,
constructor รับเฉพาะ shortened 3<seconds<=20 และไม่เลื่อน Ta
D_capture=min(original D_attempt,Ta+seconds)−3; cleanup ไม่เริ่มเวลาใหม่
stalled-ACK case ใช้ 3.5 s attempt จึงถึง capture cutoff 0.5 s ตาม clock เดิม
O/S/H มี absolute attempt timers; inert H gate read มี 1 s timeout
1 s นี้เป็น inert startup wait ไม่ใช่การพิสูจน์ native open/lock/query/close alarm
native SQLite source และ alarm 1 s เดิมไม่เปลี่ยนและยังไม่ได้ join package นี้

Cooperative CANCEL/owner EOF ใช้ <=0.2 s จาก control/drain reserve 0.6 s
O/S TERM<=0.2/KILL<=1 ร่วม phase deadline เดียว แล้ว H phase <=1.2 s
stop waits รวม <=2.4 s; control wait 0.2 s เหลือ drain/reap metadata <=0.4 s
ทุก phase clamp ด้วย absolute attempt deadline เดิม; late => STOP_UNCONFIRMED
RLIMIT_AS 256 MiB ของ R/O/S/H เป็น address-space caps ไม่ใช่ aggregate RSS/host guarantee
extra test runner ไม่ถูกอนุมัติเป็น production containment actor
private frames<=512, fixed message count; proof/output<=64 KiB/error<=4 KiB drain caps
uninterruptible I/O/scheduler/fork/exec-source closure ยังไม่ใช่ hard real-time proof

## 6. Exact-budget correction จาก CI จริง

initial candidate `cf37340d4c80b18c2935c1f3c44051a0e0247080` startup 21/21 ผ่าน
แต่ preflight run `41644122495`, Python 3.12 job `125944837128` ล้มที่ assertion เดิม
`attempt_deadline - ta <= 20` เพราะ binary-float cancellation ให้ 20.000000000000004
Python 3.14 ผ่านใน run เดียวกัน จึงไม่อ้างว่า initial candidate CI เขียวครบ
ไม่มีการ rerun เพื่อกลบผลหรือเพิ่ม tolerance/skip/relax assertion

แก้ Budget ให้เก็บ exact rational ของ input clock เดิมด้วย Fraction
แล้วบวก/ลบ 20/3/45 seconds แบบ exact; ค่า T0/Ta ที่รับไม่ถูกเลื่อน/round ใหม่
private dataclass endpoints เปลี่ยนเป็น Fraction ไม่ใช่ public schema/API change
Startup ใช้ exact endpoints ต่อ และแปลงเป็น POSIX float timeouts แบบ inward rounding
ไม่เริ่ม clock ใหม่หรือขยาย deadline; hard real-time/kernel assumptions ยังไม่ถูกพิสูจน์

เพิ่ม regression จาก `math.nextafter(17.0,-math.inf)` ที่ reproduce ผลลบเกิน 20 เดิม
และตรวจ exact 20/3/45 พร้อม preservation ของ input clock values
คง assertions ของ 23 controls เดิมครบ; final preflight 24 controls ไม่ใช่ 47 trials
อัปเดต strict workflow count 23→24 และ manifest ตาม actual changed bytes
จึงมี pre-existing files เปลี่ยน 4 ไฟล์: observer_preflight.py,
test_observer_preflight.py, opencode_observer_preflight.yml และ observer-preflight-hashes.json
new startup manifest ใช้ pinned_dependencies ไม่เรียก dependencies ที่แก้ว่า unchanged

## 7. OA disposition และ residual blockers

ไม่มี OA row ใดเป็น full PASS/CLOSED จาก inert startup profile นี้

| OA | New evidence / ยังเปิด |
| --- | --- |
| OA01 PARTIAL | reserve ก่อน actual actors, source/dev/containment/claim-failure gates; production issuer/anchor ยังไม่มี |
| OA02 PARTIAL | actual fixed-source witness→pidfd→ACKED→inert G trace; ยังไม่ใช่ native capture/full FD/dependency closure |
| OA03 PARTIAL | S ตายหลัง valid witness ก่อน retain/ACK, pidfd failure และ single-use guard; **actual post-fork/pre-witness unknown-child window ยังไม่แก้/ไม่รันแบบทิ้ง orphan** |
| OA04 PARTIAL | actual pre-adoption ECHILD/no-signal และ post-S-reap adopted stop/reap; hostile source/foreign-child/PID-reuse race corpus ยังไม่ exhaustive |
| OA05 PARTIAL | actual S-reaped-H-before-missing-FINAL และ independent stdout/stderr/report EOF; ไม่มี joined native receipt path |
| OA06 PARTIAL | actual O/S loss หลัง inert G กับ TERM-ignore H; native output/device/capture schedules ยังไม่รัน |
| OA07 PARTIAL | production/dev/unbound guard; actual R death กับ accepted external containment **NOT RUN/UNBOUND** |
| OA08 PARTIAL | actual duplicate/type/wrong-proof/missing-FINAL reject; all inherited-writer/full-pipe/over-cap/interleavings ไม่ exhaustive |
| OA09 PARTIAL | actual reservation join/failed claim consumed/object reuse; production rollback/revocation service ยัง UNBOUND |
| OA10 PARTIAL | absolute timers/cutoff/phase stop/caps ของ inert actors; aggregate physical resource/deployment/kernel bound ยัง UNBOUND |
| OA11 PARTIAL | fixed FD closure + private result redaction + retained claim; full evidence/audit/retention/output destination ยังไม่มี |
| OA12 NOT RUN | ไม่มี original goal/context/head/full evidence/verifier/Facts/planner/native FINAL path |

Launch gap ก่อนมี valid witness, O/S/H pidfd acquisition/uncertain fork return,
R death และ underlying uninterruptible stop ยังเป็น explicit feasibility blockers
unknown witness/helper_launch_known=false ไม่แปลว่า helper_started=false
source จะไม่แต่ง all-process-cessation หรือ no-orphan proof ให้สถานการณ์ที่ยังไม่มีหลักฐาน
การไม่เหลือ child ใน controls ที่รันไม่ปิดข้อจำกัดเหล่านี้

## 8. Review boundary

ขอ exact-source review เฉพาะ owned inert startup/ACK/arbitration profile นี้
ต่อไปต้องปิด launch-identity gap/accepted containment และวาง native capture/goal join
พร้อม actual source controls; ไม่เปิด protected capture โดยเปลี่ยนชื่อ fixture G
FixtureIssuer, catalog tag, file hash และ parent PID ไม่เป็น production authority
SPEC §14 และหก pre-pilot gates ต้องผ่านก่อน future implementation merge/action แยก

accepted native/supervision sources, 29/9/48 controls, schema/SPEC/receipts/OC definitions
ไม่เปลี่ยน; preflight 4 files เปลี่ยนเฉพาะ numeric correction/regression/pins ตาม section 6
PR #117 draft/unmerged; B1–B7 OPEN; J0 PAUSED; #112 ไม่เปลี่ยน
R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN
ไม่มี Dev/pilot/native job/model/API/key/config/archive invocation/evaluation arm/release/deployment
