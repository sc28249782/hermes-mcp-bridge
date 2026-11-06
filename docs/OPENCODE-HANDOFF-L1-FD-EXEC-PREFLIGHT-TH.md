# L1 FD-exec preflight and E-loss launch boundary

วันที่ 5 พฤศจิกายน 2026 (Asia/Bangkok)

Input: PR #117 `bb85c43405c0bfcc980b5ddfd52c73ddf726508d`.
ผลรอบ 28 APPROVE AS SOURCE PACKAGE เป็นผลรีวิวที่ operator ส่งมา.
สถานะ **PRE-LIVE / H LAUNCH HOLD** ตาม
[teardown admission](OPENCODE-HANDOFF-L1-TEARDOWN-ADMISSION-TH.md).

## FD-exec control

CI คอมไพล์ static ELF จาก source ของ inert probe โดยไม่ link E/H.
ควบคุม argv/environment และ stdio ใน test. คำนวณ digest จาก build
ใน test แล้ว stage ลง sealed memfd ผ่าน verifier เดิม. เปลี่ยน path
ต้นทางหลัง stage แล้วเรียก `os.execve` ด้วย fd ที่ผ่าน verifier.
Trampoline ส่งต่อ stdio กับ image fd และตั้ง image fd เป็น close-on-exec
ก่อน exec. Probe ตรวจ stdio, image fd และ FD sentinel ที่ระบุ.
หลักฐานนี้ยืนยัน fd-exec กับ artifact ที่ test สร้างขึ้น. Digest ที่คำนวณ
จาก test build ยังไม่ใช่ executable pin ที่ reviewer รับรองสำหรับ E.
FD oracle ตรวจเฉพาะ descriptor ที่ระบุ. ไม่มีการตรวจ inventory ทั้ง host.

## ขอบเขตก่อนเชื่อม runtime ของ H

| ช่วง | เจ้าของและหลักฐานที่ต้องมี |
|---|---|
| ก่อน E exec | B ต้องผูก reviewed executable pin กับ sealed image จริง ตรวจ build/link policy และระบุ allowlist ของ stdio กับ control ends ที่ส่งเข้า E. Runtime pin และ E entry point ยัง UNBOUND. |
| E สร้าง H | E ถือ original H pidfd, READY reader และ gate writer. H ถือ READY writer กับ gate reader และต้องปิด descriptor อื่นตาม FD map ที่รีวิวแล้ว. ต้องพิสูจน์ inherited absolute budget และไม่มี competing waiter. |
| E ยังอยู่ แต่ cleanup ไม่ยืนยัน | E เก็บ owner state และ handle ที่ยังถือไว้. รายงาน STOP_UNCONFIRMED; ห้ามใช้ผล READY เป็น reap receipt หรือเริ่ม attempt ซ้ำ. |
| E สูญหาย ก่อนหรือหลัง H birth | ผู้ถือ bounded H stop และผู้มีสิทธิ์ exact H reap ยัง UNBOUND. B ถือสิทธิ์รอ E ได้ตาม contract ของตนเท่านั้น. การยืนยัน exact E ไม่ยืนยัน H exit, reap หรือ EOF. |
| Terminal | แยก H exact consume, stream EOF และ B exact E. ข้อมูลขาดหรือช้าอยู่ที่ HOLD. |

การเปิด H ต้องมี profile ที่ระบุ **ใครหยุด H และใคร reap H** เมื่อ E สูญหาย
ทั้งก่อนและหลัง birth โดยครอบ launch gap, ใช้ deadline เดิม และผ่าน
[SPEC §14](SPEC.md#14-change-control). หากหา profile ที่ตรงข้อกำหนดไม่ได้
ให้คง HOLD. ไม่มี numeric signal, reacquisition, backup pidfd หรือ
watchdog เพิ่มในชุดนี้. Fixture chain คอมไพล์ได้สำหรับ source review
และไม่มี entry point ที่เปิด H. CI รัน model, pure predicates,
mocked attempt, image staging และ inert fd-exec เท่านั้น.

L1 UNPROVEN/HOLD · B4 OPEN · L1F/LH และ OA07/OA12 NOT RUN ·
J0 PAUSED · OC18 NOT RUN · R1 NOT AUTHORIZED / R2 HOLD.
