# B4 — supervisor ตายหลัง spawn: controls และ disposition

วันที่: 3 พฤศจิกายน 2026 (Asia/Bangkok)
Parent: `62356920f6ff15088b4eb21caf1eac5821c85511` บน draft PR #117
สถานะ: **OFFLINE CONTROL CANDIDATE / รอ exact-source review / B4 ยัง OPEN**

## 1. Checkpoint และสิ่งที่เพิ่ม

ผู้ใช้ส่งผลรีวิวรอบ 5 ว่า supervision primitive ผ่าน exact-source review
ณ parent ข้างต้น โดย B4 ยัง OPEN และเสนอ supervisor-own-death หลัง helper spawn
คำสั่ง “ทำขั้นถัดไป” ให้ทำ control package นี้ ไม่มี exact approval timestamp
ผลรีวิวเป็น operator-supplied ไม่ใช่ GitHub review submission ที่ผู้เขียนสร้างแทน

เพิ่ม [test_supervisor_loss.py](../acceptance/handoff/opencode/test_supervisor_loss.py),
[source/dependency manifest](../acceptance/handoff/opencode/supervisor-loss-hashes.json) และ
[workflow เฉพาะ](../.github/workflows/opencode_supervisor_loss.yml)
เอกสารนี้เป็นไฟล์ที่สี่ของ delta ไม่มีการเปลี่ยน source primitive, tests 29/48,
workflow/hash manifest เดิม, Facts/Batch/planner, schema/SPEC/config หรือ receipts เดิม
ไม่เชื่อม production observer, ไม่รัน Dev/pilot, archive หรือ evaluation arm

เอกสาร [B4 source review เดิม](OPENCODE-HANDOFF-B4-SOURCE-REVIEW-TH.md)
ยังเป็นประวัติของ parent ที่รับแล้ว ข้อความว่า post-spawn supervisor loss ยังไม่พิสูจน์
ตรงตามขอบเขตของ head นั้น ผลใหม่ข้างล่างเพิ่ม control evidence ไม่รีไรต์ประวัติ

## 2. วิธี observe โดยไม่ทิ้ง orphan

แต่ละ case fork **observer process ใหม่** แล้วตั้ง Linux child-subreaper
เฉพาะใน observer นั้นด้วย PR_SET_CHILD_SUBREAPER และตรวจกลับด้วย PR_GET_CHILD_SUBREAPER
test runner ตรวจว่าค่าของ process ตนไม่เปลี่ยนหลังทุก case
ไม่มีการเปลี่ยน bridge/host service/global setting หรือ enumerate process เดิม
observer ใช้เฉพาะ descendants ที่ fixture ของตนสร้างใหม่

| Actor / handle | หน้าที่ที่ตรวจจริง |
| --- | --- |
| Test runner | เป็น direct parent ของ observer; retain observer pidfd และ reap; ไม่มีสิทธิ์ cleanup runtime เดิม |
| Isolated observer | สร้าง owner/supervisor ด้วย launcher fixture เดิม; retain owner/supervisor pidfds; เมื่อ supervisor ตายจึงรับ helper เป็น adopted direct child; ตรวจ ownership ก่อน cleanup/reap |
| Supervisor fixture | เรียก source primitive เดิม; test-only wrapper แจ้ง helper PID ผ่าน private pipe หลัง actual spawn และอาจพักที่ named boundary; SIGKILL supervisor จริง ไม่ mock ผลตาย |
| Helper | native C เดิม หรือ compiled disposable TERM-ignore/partial-prefix/nonreading/TERM-responsive fixtures; ไม่สร้าง descendant ของตนและไม่ใช่ backend process |

private launch witness ให้ observer เปิด retained helper pidfd **ก่อน** ฆ่า supervisor
ขณะที่ original parent ยังมีชีวิตและยังไม่ได้ reap helper
PID เป็น private correlation เท่านั้น ไม่ใช่ authority และไม่ปรากฏใน public receipt
ก่อน adoption เรียก actual cleanup guard ภายใต้ signal trap ต้องได้ ECHILD
โดยไม่มี signal เกิดขึ้น หลัง supervisor ถูก SIGKILL และ reap แล้ว
waitid(P_PID, WEXITED|WNOHANG|WNOWAIT) ต้องยืนยัน adopted direct-child eligibility
จากนั้นส่ง TERM/KILL ด้วย retained pidfd เท่านั้น ไม่มี numeric-PID/PGID signal

test-only precreated pipes ทำให้ observer retain **read ends เท่านั้น** ของ helper
stdout/stderr; ปิด write ends ของ observer ก่อน capture
source _spawn ใช้ ordinary pipes ชุดนี้ตามเดิม ไม่แก้ primitive หรือ helper argv
owner ไม่ได้รับ launch/observer/report handles; helper exec ปิด fd อื่นตาม source เดิม
จึงตรวจ helper pipe EOF แยกจาก original report-pipe EOF ได้จริงโดยไม่มี socket,
SCM_RIGHTS, pidfd_getfd หรือการอ่าน /proc ของ process อื่น

observer cleanup ของ adopted fixture เป็น **ความสามารถเฉพาะ test**
ไม่ถูกใส่ใน production path และไม่พิสูจน์ production admission/source authentication
waitpid(-1, WNOHANG) ใช้เป็น cleanup oracle เฉพาะใน isolated observer ที่สร้างใหม่
และต้องได้ ECHILD หลัง reap owner/supervisor/helper ทั้งหมด
จึงไม่ถือว่า process หายเพียงเพราะ timeout, pipe ปิด หรือ signal ส่งสำเร็จ

## 3. Controls 9 ข้อและผลที่ต้องเห็น

| Case | Actual stimulus / assertion |
| --- | --- |
| post_spawn | SIGKILL supervisor หลัง actual helper spawn ก่อน READY/helper pidfd acquisition ใน supervisor; native idle helper เห็น stdin EOF, exit และ observer adopt/reap ได้โดยไม่ต้อง signal helper |
| idle | SIGKILL หลัง READY แต่ก่อน G; native helper exit จาก EOF; observer เห็น helper stdout/stderr EOF และ reap |
| hung | หลัง helper รับ input แล้ว witness ยืนยันว่าอยู่ใน TERM-ignore body จึง SIGKILL supervisor; helper ยังไม่ exit; adopted observer TERM แล้ว KILL ภายใน budget จึง reap ได้ |
| prefix | helper เขียน actual valid context-frame prefix ก่อน witness แล้วค้าง; supervisor ตาย; prefix ไม่เป็น FINAL/goal/Done; observer cleanup และ discard output |
| blocked | fixture ไม่อ่าน stdin และค้าง; supervisor ตายไม่ทำให้ helper หยุดเอง; adopted pidfd cleanup ต้องจบและ reap |
| term | TERM-responsive fixture รอดจาก supervisor death; observer ส่ง TERM ครั้งเดียวและยืนยัน exit/reap ไม่ส่ง KILL เพิ่ม |
| pre_final | source เดิมถึง CAPTURE_COMPLETE, helper_reaped=true และ pipes_eof=true จริงแล้ว แต่พักก่อนเขียน FINAL; SIGKILL supervisor ทำให้ไม่มี FINAL; observer เห็น helper exit แต่ ECHILD เพราะ supervisor reap ไปแล้ว จึงไม่อ้าง observer adoption/reap หรือ signal ซ้ำ |
| both | ฆ่า owner และ supervisor จริงขณะ TERM-ignore helper active; isolated observer adopt/stop/reap helper; ไม่ทิ้ง live descendant หรือ zombie ใน fixture observer |
| identity | new test/workflow และ unchanged dependencies ตรง SHA256/byte lengths ใน manifest; ไม่ skip unsupported platform/native capture |

8 process cases ตรวจ adoption guard, report EOF, helper stdout/stderr EOF,
supervisor reap, no remaining children, unchanged parent subreaper setting,
bounded duration และ flags false เหมือนกัน; case ที่ supervisor reap helper ไปแล้ว
แยก helper_exit_observed=true จาก helper_reaped_by_observer=false อย่างชัดเจน
test-only hook เลือกจังหวะ crash แต่ fork/exec, SIGKILL, pidfd readiness,
kernel adoption, EOF และ waitpid/reap เป็นเหตุการณ์จริง
ไม่ได้ mock ว่า helper ตายหรือว่าการ cleanup ผ่าน

## 4. ผลและความหมายที่จำกัด

Author-local Python 3.12.14 + native SQLite 3.45.1: **9/9 OK**,
ResourceWarning-as-error, ไม่มี skips; ผล CI ต้องอ้าง exact candidate head/job logs
การรัน development ก่อนสร้าง manifest พบ missing manifest ตามจริง
ไม่ถือเป็น final pass และไม่รวมเป็น trial count เพิ่ม
source/hash validation ต้องผ่านใน final suite

ทุก process case ให้ **UNKNOWN** สำหรับ observation เดิม เพราะไม่มี FINAL
แม้ observer จะยืนยัน helper exit/reap/pipe EOF ภายหลังได้
report_eof กับ helper_pipes_eof เป็นคนละหลักฐาน
ไม่มีการสังเคราะห์ FINAL แทน supervisor หรือ commit checkpoint/receipt ใหม่
goal_verified=false, authorizes_actions=false, dev_observed=false เสมอ

ผลสำคัญ: **supervisor death ไม่รับประกันให้ active TERM-ignore/nonreading helper
หยุดอัตโนมัติ**; fixture ต้องอาศัย independent observer ที่รับ ownership และมี
cleanup authority จึงหยุด/reap ได้ การผ่าน control เป็นหลักฐานของข้อจำกัดนี้
ไม่ใช่หลักฐานว่า production recovery ติดตั้ง/พร้อมแล้ว
native idle-helper EOF exit พิสูจน์ได้เฉพาะ idle profile ไม่ขยายเป็นทุก I/O state

การพิมพ์ per-case receipt ใน CI ใช้ allowlisted case refs/booleans/counts/exit reason/
elapsed duration เท่านั้น ไม่มี PID, native job/request/session IDs, paths,
prompt/output/fingerprint/config/credentials หรือ exception text จาก private runtime
build hashes เป็น measured identity ไม่ใช่ authenticity proof

## 5. Budget และ residual blockers

source primitive เดิมคง native alarm 1 s, attempt <=20 s, outer <=45 s และ memory caps เดิม
ใหม่เฉพาะ test fixture: supervisor ใช้ shortened lifetime 8 s, observer case deadline 12 s,
observer fail-safe alarm 20 s; cleanup TERM grace <=0.2 s / KILL wait <=1 s
ไม่มีการขยาย timer ของ source หรือหน่วง backend เพื่อสร้าง observation window
test runner มี exit-watch guard 22 s เพื่อรับผลของ isolated observer; ไม่ใช่ action budget ใหม่
extra observer process และ subreaper role ไม่ได้ถูกอนุมัติเป็น production actor/resource model

Disposition ที่ขอรับ: **supervisor-loss post-spawn controls ผ่านใน named fixture profile**
โดยเก็บ pre-arm control เดิมไว้เป็นประวัติและ regression
เพิ่ม coverage ของ B4/OC15–16 และ B6; ไม่เปลี่ยน [B1–B7](OPENCODE-HANDOFF-BLOCKER-CLOSURE-TH.md)
เป็น CLOSED และไม่เปลี่ยน OC18
ยังเปิด production observer/adoption protocol, authority/one-attempt binding,
observer death, joined Facts/planner/full verifier/receipt commit,
aggregate actor/memory feasibility และ uninterruptible kernel I/O
ผล STOP_UNCONFIRMED/UNKNOWN ไม่ก่อ retry/respawn/submit/resume/cancel action

ขั้นถัดไปคือ independent exact-source review และเลือกว่าจะออกแบบ production
ownership/observer contract ที่เข้ากับ authority/rollback gates อย่างไร
เอกสารนี้ยังไม่เริ่ม contract หรือ integration รอบนั้น
PR #117 draft/unmerged; J0 PAUSED; #112 ไม่เปลี่ยน
R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN; ไม่มี Dev/pilot/release/deployment
