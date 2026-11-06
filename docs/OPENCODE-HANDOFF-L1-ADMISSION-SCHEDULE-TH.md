# L1 admission proposal — finite WAIT schedule and pre-close readiness

วันที่ 5 พฤศจิกายน 2026 (Asia/Bangkok)

Input head: `818da0ec6cf32a6afbe20a5ca688b771cd1f7b7d`.
Round 23 APPROVE AS DESIGN เป็นผลรีวิวที่ operator ส่งมา.
เอกสารนี้ขยาย [L1 exact-child WAIT contract](OPENCODE-HANDOFF-L1-WAIT-CONTRACT-TH.md)
เพื่อรีวิวสองเงื่อนไขก่อนพิจารณา source package. ตัวเลขในตารางเป็นข้อเสนอ
สำหรับ fixture และยังไม่มีผลวัด. **L1 UNPROVEN/HOLD.**

## 1. เวลาและขอบเขต

ใช้ monotonic clock เดียวกับ `T0`, `Ta` และ deadline เดิม.
`D = min(Ta + 20 s, T0 + 45 s)` หรือใช้ cutoff ที่เข้มกว่า `Ta + 8 s`
เมื่อ profile ที่รับรองระบุไว้แล้ว. เวลา close, การ freeze ผล candidate เป็น
`UNKNOWN` และการปิด gate ต้องครบก่อน `D − 3 s`.
H ต้อง arm one-shot self-expiry ที่ `D_H = D − 2 s` ก่อน READY.
E ต้องตรวจเวลาที่เหลือซ้ำก่อน destructive close และปฏิเสธเมื่อเงื่อนไข
pre-close ข้อใดไม่ครบ. ใช้ deadline เดิมทุก phase รวม B ที่รอ exact E.

| ขอบเวลาเสนอ | การกระทำของ test teardown |
|---|---|
| `D − 3000 ms + i × 125 ms` สำหรับ `i = 0…15` | E ตรวจ exact H ที่ `waitid(P_PID, birth_pid, WEXITED\|WNOHANG\|WNOWAIT)` ไม่เกินหนึ่งครั้งต่อ slot. เปิดรับการเริ่มตรวจใน 25 ms แรกของ slot. ข้าม slot ที่พลาดและบันทึกสาเหตุ. |
| ก่อน `D − 1000 ms` | หลังพบ terminal event ครั้งแรก ทำ WNOWAIT ยืนยันอีกครั้ง แล้ว consume exact H ด้วย `waitid(P_PID, birth_pid, WEXITED\|WNOHANG)` ครั้งเดียว เมื่อผลยืนยันตรงและเวลายังเหลือ. หยุดตารางเมื่อพบ terminal event หรือพบความผิดปกติ. |
| ก่อน `D − 500 ms` | ตรวจ EOF ของช่องที่กำหนดแยกจาก reap. เก็บ bounded read/byte evidence ภายใต้ caps เดิม. ตรวจ EOF ได้ระหว่างรอ slot และหลัง reap ตามสิทธิ์เดิม. |
| ก่อน `D` | บันทึก terminal evidence ของ fixture และผล exact-E ของ B ภายใน deadline เดิม. Late/missing evidence คง `HOLD`. |

จำนวน wait ของ H **หลัง close ไม่เกิน 18 ครั้ง** (16 probes, 1
confirmation, 1 consuming wait). ใช้ absolute slot times. ตรวจนาฬิกาก่อนและ
หลัง wait แต่ละครั้ง. ไม่มี catch-up burst, EINTR retry, any-child wait,
การเปลี่ยน target หรือการรอแบบ blocking. หาก completion ล่าช้าหรือหยุดค้าง
ให้ถือว่า timetable นี้ยังพิสูจน์ hard stop ไม่ได้. ถ้า consume เกิดขึ้นแต่
ผลกลับช้า ให้แยกข้อเท็จจริงว่า syscall เกิดแล้วออกจาก acceptance และห้าม consume ซ้ำ.

ก่อนทุก probe ให้ zero-initialize siginfo. ค่ากลับสำเร็จโดยไม่มี event ใช้ slot ถัดไป.
terminal event ต้องตรง exact child และ expected exit class ของ stimulus.
ผล WNOWAIT สองครั้งและผล consume ต้องตรงกันที่ `si_pid/si_code/si_status`.
`ECHILD`, `EINTR`, error อื่น, identity mismatch, missing confirmation
หรือ consume ที่ตรวจรับไม่ได้ ให้ freeze teardown verdict เป็น HOLD.
ไม่มี post-consume wait เพื่อเปลี่ยน `ECHILD` เป็นหลักฐาน reap.
B exact-E wait มีหลักฐานแยกและใช้พิสูจน์เฉพาะ E.

## 2. เกณฑ์ pre-close

E ต้องมี birth record แบบ one-shot จาก create ของตนเอง, direct-child custody,
original pidfd ที่ยังถืออยู่, SIGCHLD policy ตาม contract และไม่มี competing
waiter. ตรวจ live pidfd และ readiness ของ H ก่อน close. ถ้าเกิด exit ระหว่าง
live check กับ close ให้จัด schedule เป็น inconclusive เมื่อ oracle ที่ต้องการ
live-at-loss พิสูจน์ไม่ได้. ห้ามนับ live check เป็นการรับประกันแบบ atomic.

สำหรับ source package ในอนาคต เสนอให้ bind executable ที่ผ่านรีวิวจาก
retained launch handle แล้วตรวจ source digest ก่อน launch. READY มาจาก
ช่องที่ผูกกับ H นั้นเท่านั้น, รับครั้งเดียวตาม closed schema, และต้องตรง
attempt/generation/role/source/FD map/deadlines. READY เป็นหลักฐาน protocol
ภายใน fixture. การระบุ digest ใน READY เองให้หลักฐาน source identity ไม่พอ.

ข้อเสนอ timer คือ POSIX one-shot บน `CLOCK_MONOTONIC` ตั้ง absolute target
`D_H` ก่อน READY. H ต้องตั้ง handler และตรวจ disposition กับ mask ของ expiry
signal ก่อน READY. ตรวจ `timer_gettime` ให้ interval เป็นศูนย์และ remaining
เป็นบวก. เมื่อคร่อม readback ด้วย monotonic samples `a` และ `b` ให้ตรวจ
`b − a ≤ 20 ms` และ `D_H ∈ [a + remaining, b + remaining]`.
นี่เป็นเกณฑ์เสนอเพื่อ review บน platform fixture ก่อนใช้จริง. Readback
ไม่วัด signal delivery หรือยืนยันว่า H จะ exit ทันเวลา. E ปฏิเสธเมื่อ
หลักฐานหาย, ล่าช้า, ไม่ตรง tuple หรือ cleanup reserve ก่อน close ไม่พอ.

| Negative control ที่จะเสนอใน source review | Oracle ก่อน close |
|---|---|
| Timer create/arm/readback ล้มเหลวหรือไม่มีหลักฐาน | Reject และ destructive-close count เป็น 0 |
| Clock หรือ target ผิด, disarmed/expired, ตั้ง interval, readback ไม่อยู่ใน bracket | Reject และ destructive-close count เป็น 0 |
| Expiry signal ถูก block หรือ disposition ไม่ตรง fixture | Reject และ destructive-close count เป็น 0 |
| Launch source unknown/changed, READY ปลอม/ซ้ำ/ผิด schema หรือ tuple | Reject และ destructive-close count เป็น 0 |
| Birth record/custody/liveness ไม่ครบ หรือ readiness มาหลัง cutoff | Reject และ destructive-close count เป็น 0 |

แต่ละ negative ต้อง inject ก่อน destructive close, ตรวจ oracle ที่ขอบ
close จริง และบันทึก original pidfd ยังอยู่ในการครอบครองเมื่อ reject.
ใช้ทาง cleanup เดิมที่ผ่าน admission ด้วย original pidfd ภายใน deadline เดิม.
ถ้า pre-close cleanup เองยังยืนยันไม่ได้ ให้ระบุ case ว่า NOT RUN/HOLD.
สำหรับ WAIT review ให้แยก schedule ที่ terminal event มาทัน, no-event
จนหมด slot, wake ล่าช้า, mismatch/ECHILD และ EOF ค้าง. ห้ามปิดหรือทำลาย
expiry route หลัง close เพื่อบังคับ negative.

## 3. Review gate

เวลา slot, deadline, readback tolerance และหลักฐาน live-at-loss ต้องผ่าน
exact-design review. การเปลี่ยน fixture timer, exact numeric child WAIT
และ private teardown grant ยังอยู่ภายใต้ SPEC §14 ตาม contract เดิม.
ห้าม numeric signal, pidfd reacquisition/duplicate, host scan,
re-arm หลัง close หรือเพิ่ม actor. หากต้องการ independent hard stop
ครอบคลุม timer failure หลัง close, E loss หรือ kernel stall ต้องมี
containment ที่ผ่าน review แยกก่อน.

Candidate result คง `UNKNOWN` หลัง destructive close แม้ private
teardown ยืนยัน reap และ EOF ครบ. ไม่มี FINAL หรือ goal authority ใหม่.
L1F01–L1F12 และ LH01–LH08 ยัง NOT RUN. B4 OPEN, OA07/OA12 NOT RUN,
J0 PAUSED, OC18 NOT RUN, R1 NOT AUTHORIZED และ R2 HOLD.

อ้างอิง interface สำหรับ source review
[waitid](https://man7.org/linux/man-pages/man2/waitpid.2.html) และ
[POSIX timer readback](https://man7.org/linux/man-pages/man2/timer_settime.2.html).
