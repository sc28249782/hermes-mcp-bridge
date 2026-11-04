# PB02/PB03 — owned fork/pidfd birth-result feasibility package

## 1. Checkpoint และข้อสรุป

Parent `56fe33dee9bdba00bcdb749aca0ef54ce67bbfcc` ได้รับ operator-supplied
round-16 APPROVE (AS DESIGN) สำหรับ [alternate contract](OPENCODE-HANDOFF-PREENROLLED-BROKER-CONTRACT-TH.md)
เป็น record ของข้อความผู้ใช้ ไม่ใช่ GitHub review submission; ไม่มี timestamp จึงไม่เติมเอง
รอบนี้เป็น feasibility source ที่รอ exact-source review ไม่ใช่ effective amendment/runtime

ผลจำกัดตามที่วัด: **E ที่ได้รับ own fork-result และ retain pidfd ครบ ไม่ต้องพึ่ง R relay
เพื่อ cleanup H เมื่อ R ตายที่ named boundaries** แต่ **lost create-result / failed
pidfd acquisition ยัง unconfirmed** และต้อง diagnostic rescue ที่ไม่ใช่ candidate capability
จึงยังเป็น PROFILE UNBOUND ไม่ใช่ production-ready broker หรือ PB02/PB03 full PASS
ไม่อ้างว่าปิด E creator-side gap และไม่ปฏิเสธ birth primitive อื่นทุกแบบ

ใช้ **fork + pidfd_open** ใน owned fixture เท่านั้น ไม่มี clone/clone3/CLONE_PIDFD probe,
cgroup/service/VM/delegation/credential operation หรือ actual production profile selection
[round-15 registry-only counterexample](OPENCODE-HANDOFF-ANCESTOR-FEASIBILITY-REVIEW-TH.md)
คงข้อสรุปเดิม ไม่ถูกเปลี่ยนเป็น pass จาก package ใหม่นี้

## 2. Source scope และ exact topology

เพิ่ม [birth_probe.py](../acceptance/handoff/opencode/birth_probe.py),
[16 controls](../acceptance/handoff/opencode/test_birth_probe.py),
[manifest](../acceptance/handoff/opencode/birth-probe-hashes.json),
[new workflow](../.github/workflows/opencode_birth_probe.yml) และเอกสารนี้
ไม่มีการแก้ไฟล์เดิม รวมทั้ง broker contract, ancestor probe, native C/VFS,
startup/preflight/supervision, tests/workflows/manifests/SPEC/receipts/guards เดิม

B เป็น test driver สร้าง fresh isolated E; E **directly creates R และ H**
O/S **ไม่ถูกสร้าง** ใน package นี้ เป็น two-slot primitive subset ไม่ใช่ complete broker
R เป็น inert Python fault target; H เป็น inert Python gate/prefix fixture
ไม่มี native C/SQLite/CLI/Facts/Owner/Batch/planner/verifier/backend/model/config/network/key path

E/R/H=3 fixture actors + B แยก. E และเด็กมี per-actor RLIMIT_AS<=256MiB/core0
3 caps ไม่ใช่ approved768MiB physical aggregate; full E/R/O/S/H+B deployment ยัง UNBOUND
ไม่มี hidden watchdog/helper/manager process. Test B wait/reap exact E จริง
E ไม่ตั้ง host/shared subreaper; test B setting เดิมถูกตรวจหลังจบทุก case

E จอง slots `{R,H}` ก่อน create. แต่ละ slot create ได้ครั้งเดียว; shared object run ได้ครั้งเดียว
source subset implement RESERVED/CREATING/BOUND และ per-child status เท่านั้น
ไม่อ้าง full eight-state broker machine, cross-process/persisted claim หรือ B3 authority
`create_invocations` ใน test record นับ attempts ที่เรียก wrapper รวม injected error ก่อน kernel call
ไม่ใช่จำนวน successful kernel fork เสมอ; helper_create_calls ก็เป็น attempt count

## 3. Birth/identity/gate protocol ที่รันจริง

1. B ล็อก T0 ก่อน E launch; E ล็อก exact Ta/deadline ก่อน R fork
2. E create R ครั้งเดียวแล้วเก็บ returned child PID/pidfd ใน E; R ไม่มี launch role
3. E ตรวจ R/current cutoff ก่อนเริ่ม H create; reserve H slot/consume invocation ก่อน fork
4. Kernel fork H จริง; parent-side returned PID เป็น exact E-child correlation
   E ใช้ waitid WNOWAIT ตรวจ unreaped direct child แล้ว acquire pidfd หนึ่งครั้ง
   จากนั้น commit slot. ไม่มี child identity message จาก R/S ที่ E ต้องรอ
5. เฉพาะ committed H ที่ยัง alive + R ยัง alive/current เท่านั้นจึงส่ง inert G ครั้งเดียว
   H consume G จาก actual stdin และเขียน fixed `inert-birth` prefix ไป actual stdout
6. E cleanup retained **direct children** ด้วย existing eligibility/pidfd-only primitives
   exact reap กับ stdout/stderr EOF เป็นคนละ evidence; drain bounded ไม่ export prefix

การ check waitid/pidfd นี้เป็น named fresh single-thread fixture evidence
ไม่ใช่ proof ของทุก SIGCHLD/SA_NOCLDWAIT/concurrent-reaper/source-interruption condition
Test E ตั้ง SIGCHLD default; deployment ABI/handler/FD allocation/unsupported kernel assumptions
ยังต้องมี independent feasibility proof. ไม่มี numeric-PID/PGID signal หรือ PID retry/host scan

G เป็น **inert startup stimulus เท่านั้น** ไม่ใช่ protected capture/production approval
fixture_gate_sent คือ write ของ E; inert_ack แยกเฉพาะเมื่ออ่าน exact fixed prefix ครบ
R loss หลัง write ก่อนตรวจ prefix => cleanup-only, inert_ack=false
ไม่มี original FINAL/goal Done และไม่เปลี่ยน Reservation.capture() ที่ deny อยู่

## 4. Fault boundaries และ diagnostic separation

| Stimulus | Candidate actual result | ขอบเขตที่ยังไม่อ้าง |
| --- | --- | --- |
| Normal own create-result | Committed H, inert gate/prefix, exact R/H reap + EOF | Not production capability/whole broker/native proof |
| R SIGKILL ก่อน H create | helper_create_calls=0; helper_created=false; ไม่มี G | ไม่ครอบ unknown R creation |
| R SIGKILL หลัง actual H fork return ก่อน E เก็บ result | E ยัง bind/reap H จาก own result; ไม่มี G; R_LOST | เป็น user-space boundary ไม่ใช่ kernel syscall-entry trace |
| R SIGKILL หลัง H binding ก่อน gate | Known H cleanup; R_LOST, no G | Not arbitrary instruction-level coverage |
| R SIGKILL หลัง inert G | gate write=true แต่ inert_ack=false; known cleanup | ไม่อ้าง zero-effect native capture หรือ revoke races |
| Dropped user-space H result ก่อน storage | helper_created=null, binding unknown, no reap claim, cleanup_confirmed=false | Injection ไม่ใช่ actual interrupted kernel copyout |
| Dropped result + uncooperative nonreading H | H ยัง alive หลัง candidate return; no stdout/stderr EOF | Does not prove every unknown child stays live |
| pidfd_open failure หลัง known returned PID | helper_created=true แต่ retained binding unknown; one acquisition/no fallback | Error เป็น injected test fault ไม่ใช่ host FD exhaustion |
| Commit fault หลัง retained pidfd | Binding committed=false; no G; retained exact child cleanup-only ยืนยันได้ | ไม่ promote incomplete slot เป็น ready/permission |
| H exit ก่อน acquisition | Retain exact unreaped child แล้ว reap; signal trap กัน signal ซ้ำ; no G | Not all SIGCHLD/concurrent-reaper environments |
| Injected create error ก่อน H kernel call | Source conservatively reports unknown_creation/helper_created=null | Harness รู้ว่าไม่เรียก kernel แต่ source ไม่ใช้ test knowledge เป็น absent-child proof |
| Object reuse / slot reuse | Reject before second attempt/helper fork | Not cross-process restart/rollback protection |

R-death injections เป็น SIGKILL จริงผ่าน retained R pidfd; H fork/pidfd/wait/reap/EOF จริง
fault hooks เลือก boundary/body/exception เท่านั้น ไม่ mock successful kernel evidence

Harness รับ exact H PID จาก parent-side real fork result **ก่อน** injected loss
แล้วเก็บ independent diagnostic pidfd/read copies นอก candidate slots
ไม่มีการส่ง handle นี้กลับให้ candidate, ไม่มี candidate PID lookup จาก test state
Candidate frozen result คืนก่อน diagnostic stop/reap/EOF และไม่ถูกแก้ภายหลัง

Diagnostic ใช้เฉพาะ lost_result/lost_nonreading/pidfd_failure หลัง candidate return
ยืนยัน exact direct-child eligibility แล้ว cleanup ภายใน **original D เดิม**
`h_live_before` บันทึกค่าที่วัด ไม่บังคับว่า cooperative EOF case ต้องยัง live ทุก schedule
แต่ lost_nonreading **assert live จริง** และ source EOF=false ทั้งสอง stream
ถ้า cooperative child exit เอง/EOF มา ก็ยังไม่ใช่ candidate reap proof
Test-only no-child oracle ใช้ waitpid(-1,WNOHANG) หลัง source+diagnostic จบใน isolated E
ไม่มี oracle/extra pidfd ถูกนับเป็น production containment capability

## 5. Budget และ final local evidence

T0 ก่อน E launch; Ta ก่อน R fork; D_attempt=min(Ta+20,T0+45)
probe ใช้ stricter D=min(D_attempt,Ta+8), cutoff=D−3; no fresh timer at loss/binding/cleanup
E outer alarmถึง T0+45 และ children timersถึง original D; no native alarm claim เพราะไม่มี C capture
all known direct children หยุดใน shared phase เดิม TERM<=0.2s/KILL wait<=1s
new parentage/stop policy นี้ใช้เฉพาะ fixture subset ไม่แก้ accepted S/R runtime ownership

Author-local Python3.12.14, Linux x86_64, umask022: **16/16 OK, exit0**
ResourceWarning-as-error, no skip. 13 isolated E process cases + exact-budget/invalid-role,
AST source-path audit และ manifest. B exact E wait/reap + entire fixture completion< T0+8
ทุก case no_children=true, budget_preserved=true และ elapsed<8s
เป็น measured named schedules ไม่ใช่ proof ของ worst-case reserve3s/late budget/kernel I/O
Diagnostic original-deadline assertions ไม่ต่ออายุ slot/candidate result

Every candidate result: production_feasible/profile_selected/capture_allowed/
authorizes_actions/dev_observed/goal_verified=false แม้ known cleanup/inert ack สำเร็จ
candidate result เป็น closed frozen dataclass; test transport<=4096 bytes ไม่ใช่ runtime wire schema
internal helper prefix<=12 bytes; bounded drain stdout<=64KiB/stderr<=4KiB; no raw prefix in public log
sourceไม่มี caller-selected process/path/argv/SQL, process inventory, exec/subprocess หรือ backend dispatch

ก่อน manifest มี intermediate local FileNotFoundError ของ new hash file; หลังสร้าง pinsจึงรัน
final16/16 ตามข้างต้น. ไม่ลด assertion/skip/widen timer เพื่อผ่าน และไม่อ้าง intermediate pass
Exact-head CI ต้องอ้าง run/job logs แยก; source/head acceptance ไม่ได้มาจาก test count
Historical broad local baseline NOT PASS คงเดิม ไม่ได้ rerun หรืออ้าง local broad PASS

## 6. PB/OA disposition และ unresolved proof

| Obligation | Incremental evidence | ยังต้องมี |
| --- | --- | --- |
| PB02 / EC02,03 | PARTIAL own-result independence จาก R relay ที่ named boundaries | Actual in-kernel/asynchronous lost-result schedules/full R/O/S/H integration |
| PB03 / EC02,03 | PARTIAL injected result/pidfd/commit failures และ live counterexample | Accepted recoverable/atomic create-result primitive; real copyout/FD exhaustion/interrupt proof |
| PB01/04–11 | NOT RUN full obligations | Authority/anchor/no-descendants/native G/data+lifecycle join/E/B failure/resources/privacy profile |

Helper create-result หาย/failed acquisition ยังขาด exact bounded cleanup proof
pre-reserved slot ไม่แก้ด้วยตัวมันเอง; fork/pidfd subset **ยังไม่ production-ready**
ห้ามใช้ test diagnostic handle เป็น E recovery protocol หรือเปลี่ยน unknownให้ absent
CLONE_PIDFD/alternate result protocol ยัง NOT RUN/UNBOUND ไม่ถูกปฏิเสธหรือเลือกอัตโนมัติ
OA07 full accepted external-profile obligation และ OA12 ยัง NOT RUN; B4 OPEN
ไม่มี whole PB/EC/OA row PASS/CLOSED; existing registry-only infeasible verdictคงอยู่

| Evidence field | Record |
| --- | --- |
| ID/status/scope | PB02/PB03 PARTIAL feasibility / OA07 NOT RUN full obligation; B4 OPEN |
| Requirement | Alternative contract birth-result gap; no OC/OA definition change |
| Source SHA/path | Exact candidate commit + [manifest](../acceptance/handoff/opencode/birth-probe-hashes.json) |
| Task/control/stimulus | 13 process cases + three static/arithmetic/source checks ตาม §4/5 |
| Expected | R relayไม่จำเป็นเมื่อ E ได้ own result; ambiguous resultไม่กลายเป็น capability |
| Actual | Local16/16 OK; known cleanupสำเร็จ; three diagnostic-only uncertain-result cases |
| Environment/dependencies | Linux x86_64/Python3.12.14 local; CI3.12/3.14; unchanged pinned S/P/design |
| Private evidence locator | Original production/Dev bindings UNBOUND; owned workflow logsเท่านั้น |
| Privacy-safe summary | Fixed enum/booleans/counts/millisecond durations; no PID/path/raw output/error |
| Independent review | Parent round16 operator-supplied DESIGN APPROVE; new exact-source package PENDING |
| Unresolved limits | Real primitive interruption, authority/rollback, SIGCHLD/reaper semantics, native join/E availability/B6 |
| Handoff | Preserve HOLD; review next birth primitive scopeก่อน source integration |

Implementation integration/parentage/grant/FINAL changes ต้องผ่าน SPEC §14 amendmentก่อน merge
แพ็กเกจนี้ไม่แก้ SPEC/runtime/native/source guards ไม่ติดตั้ง service/cgroup/VM หรือใช้ credentials
PR117 draft/unmerged; B1–B7 OPEN; OA06/OA08 PARTIAL; J0 PAUSED (#112 e7142cf7)
OC18 NOT RUN; R1 NOT AUTHORIZED / R2 HOLD; no Dev/pilot/archive/model/API/release/deployment
