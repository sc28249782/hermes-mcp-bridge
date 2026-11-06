# Observer package 5 — OA08 pipe/FINAL source controls candidate

## 1. Checkpoint และขอบเขต

Parent `bc6525608731128f6cd12d3d22630b1308e0c4c4` ได้รับ operator-supplied
round-11 APPROVE ตามข้อความที่ผู้ใช้ส่งมา ไม่ใช่ GitHub review submission
ไม่มี timestamp ของ review จึงไม่เติมเอง. Candidate นี้รอ independent review

Docs-only follow-up: operator-supplied round-12 APPROVE ณ source head
`256c5e40570a11b45422fe20c0a9b050e7166da4` ยอมรับ package 5 ตาม scope ที่รีวิว
พร้อม nonblocking interpreter note ด้านล่าง; ไม่ใช่ GitHub review submission
และไม่เปลี่ยน source/runtime/manifest หรือยกระดับ OA/B acceptance

ข้อแก้ความคลาดเคลื่อนของ round-11: สี่ phases ของ package 4 คือ native
nonreading / SQLite read lock / first frame / complete three-frame prefix
ทุก loss schedule อยู่หลัง G ไม่ใช่ก่อน/ระหว่าง ACK หรือหลัง original FINAL
[เอกสาร package 4](OPENCODE-HANDOFF-NATIVE-LOSS-REVIEW-TH.md) คง bytes เดิม

เพิ่ม OA08 controls เท่านั้น ไม่เปลี่ยน native runner, C/VFS/headers,
startup/preflight/supervision, baseline/schema/SPEC/receipts/experiment guards
original 44 test methods/ทุก assertion เป็น AST เดิม; เพิ่มเก้าชุดเป็น 53
ปรับ strict workflow count และ actual source manifest ตาม bytes ใหม่

PR #117 body เดิมยาว 63,653 characters ใกล้ขีดจำกัด จึงเก็บ snapshot **byte-identical**
ใน [history ณ parent](OPENCODE-HANDOFF-PR117-HISTORY-BC652560.md)
UTF-8 63,795 bytes, SHA256
`d975a26fb7563fde947ef7588f4e9b7d8a9ac4d574e5ea38befed3b05991a21c`
แล้วใช้ PR body ปัจจุบันสำหรับ candidate/CI ใหม่พร้อมลิงก์ประวัติ
ไม่มีการแก้ผลทดสอบเก่าหรือเปลี่ยน CI ที่เคย fail ให้ผ่านย้อนหลัง

Draft/unmerged; B1–B7 OPEN; OA ไม่มี whole-row PASS/CLOSED; J0 PAUSED;
OC18 NOT RUN; R1 NOT AUTHORIZED / R2 HOLD. ไม่มี Dev/pilot/backend/model/API/
credential/config action, original-goal evaluation, checkpoint append หรือ deployment

## 2. เก้าสถานการณ์ใหม่

| Control | Actual stimulus | Expected publication |
| --- | --- | --- |
| held_stdout | fixture R เก็บ duplicated actual H stdout write-end; C ส่งสามเฟรมและ S reap H แล้ว แต่ EOF ไม่มา | UNKNOWN/STOP_UNCONFIRMED; ไม่มี FINAL; stdout_eof ยัง unknown |
| held_stderr | R เก็บ duplicated actual stderr write-end; C/S จบ native data/reap แต่ stderr EOF ไม่มา | UNKNOWN/STOP_UNCONFIRMED; ไม่มี FINAL; stdout EOF true, stderr unknown |
| held_report | R เก็บ actual report write-end; valid S FINAL มาถึงและ H ถูก reap/stream EOF ครบ แต่ report EOF ไม่มา | UNKNOWN/STOP_UNCONFIRMED แม้ original_final=true; ไม่ publish success |
| full_stdout | actual C fault helper เติม stdout ถึง EAGAIN; S consumer ถูก test barrier ค้างก่อน read | R รอถึง original cutoff แล้ว cleanup; UNKNOWN ไม่มี FINAL |
| full_stderr | actual C fault helper เติม stderr ถึง EAGAIN; S consumer ถูก test barrier ค้างก่อน read | UNKNOWN; source retained-pidfd stop/reap/EOF ต้องครบใน attempt เดิม |
| full_report | R เติม report หลัง ACKED/G; ไม่อ่านจน S ส่ง FINAL แล้ว source nonblocking write ได้ EAGAIN จริง | UNKNOWN; ไม่มี accepted FINAL; ไม่ block หรือ retry FINAL |
| duplicate_final | S test hook write สอง complete FINAL ใน atomic write เดียว <=512 bytes | bounded strict framing reject |
| trailing_final | complete FINAL ตามด้วย byte เกิน | reject ไม่ accept valid prefix |
| partial_final | S write ครึ่ง FINAL ไม่มี newline แล้วจบ | reject ไม่เติม/ประกอบ FINAL ทดแทน |

Retained-writer fault อยู่ใน **fixture R actor เดิม** ไม่เพิ่มลูก/descendant/watchdog
เป็น parent-retained duplicate ของ write-end ที่ส่งสืบทอดไป S/H จริง
ไม่ใช่ proof ครอบ arbitrary escaped descendants หรือ production FD inheritance
Reader duplicate อีกอันให้ harness วัด channel เดิมโดยไม่ปลอม EOF
หลัง source run คืนผลแล้ว harness ตรวจ no-EOF, ปิด test writer และยืนยัน EOF
ภายใน read-only probe 0.2 s; **ไม่**ต่ออายุ attempt หรือแก้ outcome ที่คืนไปแล้ว

S H-reap witness เป็น test hook หลัง actual exact waitpid คืน rc=0 ส่ง byte ใน
private pipe; source outcome ไม่ใช้ witness นี้เป็น authority หรือ replacement FINAL
held stdout/stderr ยังคง helper_reaped_by=null เพราะ R ไม่ได้รับ original FINAL
แม้ independent test hook จะรู้ว่า S reap แล้ว; held_report รับ FINAL จึงรายงาน S
reap กับ EOF/report completion เป็นหลักฐานคนละส่วนตาม contract

## 3. Full-pipe และ fault instrumentation

เฉพาะหก pipe controls ใช้ F_SETPIPE_SZ=4096 กับ actual stdout/stderr/report pipes
R ตรวจ FIONREAD=4096 และ F_GETPIPE_SZ=4096 จริงก่อนปล่อย source ทำต่อ
full stdout/stderr เป็น **test-only C fault executables**: exec จริงใน H ตัวเดิม,
เติม stream แบบ nonblocking จน EAGAIN, แจ้ง phase byte แล้วคืน blocking mode
และพยายาม write อีกหนึ่ง byte. S read hook ค้างที่ private barrier เพื่อไม่ drain
จึงวัด backpressure จริง ไม่ mock ค่าจำนวน bytes หรือ EAGAIN
notification เกิดก่อน blocking write; ไม่อ้างว่ามี kernel syscall-entry trace
หรือพิสูจน์ exact instruction ที่กำลัง block

C fault executables ไม่เรียก accepted_main/SQLite ในสอง full-stream controls นี้
จึงไม่ใช่หลักฐาน VFS/query/native alarm ของ valid native capture
positive และ retained-writer/report/final controls ยังใช้ unchanged C helper build
full_report ตรวจ source _emit จริง: nonblocking write ล้มด้วย BlockingIOError,
test hook แจ้งหลังจับ exception แล้ว re-raise; R จึงอ่าน queued invalid bytes
ไม่มี test hook แปลง write failure เป็น FINAL สำเร็จ

Private FD 201 (event write) / 202 (stall read) retained เฉพาะ test closure hooks
R ถือ stall write-end เพื่อไม่ให้ EOF ปลด consumer ก่อน cleanup
ไม่มี extra actor; source ไม่เปิด callback/config/FD option นี้ให้ public caller
original four-actor source closure policy ไม่เปลี่ยน
Test harness รอ finite event <=1 s และ fixture parent <=15 s ต่อ case
source ใช้ shortened attempt 3.5 s ในหก pipe cases, cutoff attempt−3,
Fraction T0+45 / maximum20 และ native capture alarm1s เดิมไม่เปลี่ยน
ไม่มี fresh timer ที่ handoff/cleanup, no numeric-PID/PGID signal หรือ fallback

## 4. หลักฐานที่วัดและ OA disposition

**Interpreter scope ของ controls ชุดนี้: ตรวจรับบน Python 3.12/3.14 เท่านั้น; Python 3.11 ไม่รับประกัน — reviewer รายงาน Python 3.11.15 compile ไม่ผ่าน (`SyntaxError: too many statically nested blocks` ใน `test_observer_native.py`); เป็น operator-supplied evidence ไม่ใช่ผล reproduce ใหม่ของ author และไม่ใช่ข้อจำกัดที่อ้างครอบ bridge ทั้งโครงการ.**

Author-local Python 3.12.14, Linux x86_64/SQLite 3.45.1, umask 022:
**53/53 OK, exit0**, ResourceWarning-as-error, ไม่มี skip
มี 51 isolated R process cases + manifest + source-path audit
ทุก case ตรวจ no remaining fixture child, parent subreaper setting เดิม,
synthetic state bytes เดิม และ capture/action/Dev/goal flags false
privacy assertions เดิมตรวจไม่มี fixture IDs/nonce/path/prompt/workspace/fingerprint

Measured หก pipe cases:

| Case | Actual independent pipe evidence | Source result |
| --- | --- | --- |
| held stdout/stderr/report | s_reap_observed=true; eof_before_release=false; eof_after_release=true | UNKNOWN/STOP_UNCONFIRMED; report case มี original_final=true แต่ไม่มี success |
| full stdout/stderr | full=true, capacity=queued=4096, h_live=true, consumer_stalled=true | UNKNOWN/BUDGET_EXHAUSTED; R-reaped H, both stream EOF true |
| full report | capacity=queued=4096, final_write_eagain=true | UNKNOWN ไม่มี FINAL; reap และ both stream EOF แยกจาก report failure |

สาม malformed FINAL cases เป็น UNKNOWN ไม่มี accepted original FINAL
no-child oracle ไม่ใช่ universal production no-orphan guarantee
ก่อน final source freeze local development run failed manifest length
35716/26544 เพราะ test file เปลี่ยนแต่ pin ยังเก่า; อัปเดต pins แล้วรัน final53/53
ไม่ลด assertion, skip หรือยืด timer ให้ผ่าน; intermediate run ไม่ใช่ final pass
exact-head CI ต้องอ้าง run/job logs แยกใน PR body ไม่ใช้ old-head/local counts แทน
historical broad local baseline NOT PASS คงเดิม ไม่ได้ rerun/อ้าง local broad PASS

OA08 ได้ **PARTIAL** evidence เพิ่มสำหรับ named pipe/FINAL faults เท่านั้น
ไม่ใช่ exhaustive arbitrary inherited-FD/full-pipe/partial-message coverage
OA06 คง PARTIAL; OA07 actual R death + accepted external containment ยัง NOT RUN;
OA12 original authority/context/evidence/full-goal/Facts/planner/receipt join NOT RUN
unknown pre-witness launch, issuer/rollback anchor/containment, aggregate physical
resources/external actors และ uninterruptible I/O ยังเป็น blockers; B4 OPEN

## 5. Evidence record

| Field | Record |
| --- | --- |
| ID/status/scope | B4 OPEN / OA08 PARTIAL; owned offline source controls |
| Requirement | OA08 / B4 / OC09,15,16 ตาม observer/adoption contract เดิม |
| Source SHA/path | Exact PR candidate commit + [manifest](../acceptance/handoff/opencode/observer-native-hashes.json) |
| Task/control/stimulus | [53 controls](../acceptance/handoff/opencode/test_observer_native.py), nine added cases ตาม §2 |
| Expected | Missing required EOF หรือ malformed/refused FINAL ไม่ publish success |
| Actual | Local 53/53 OK และ measured pipe facts ตาม §4; CI ใหม่แยกใน PR |
| Environment/dependencies | Compiler/library/helper commitments ใน suite log; unchanged dependencies ใน manifest |
| Private evidence locator | Original Dev/private bindings UNBOUND ไม่ได้อ่าน; owned CI logs จาก PR |
| Privacy-safe summary | Finite counts/booleans/capacity; ไม่มี raw frame/IDs/paths/errors |
| Independent review | Parent operator-supplied round-11 APPROVE; candidate PENDING review |
| Unresolved limits | OA07/OA12 NOT RUN; production/ownership/resource limits ตาม §4 |
| Handoff | Keep draft; no OA/B closure; source review/green CI ไม่ใช่ action approval |

Runtime/security/interface implementation merge ในอนาคตยังต้องผ่าน
[SPEC §14](SPEC.md#14-change-control). แพ็กเกจนี้ไม่เปลี่ยน runtime/public schema
