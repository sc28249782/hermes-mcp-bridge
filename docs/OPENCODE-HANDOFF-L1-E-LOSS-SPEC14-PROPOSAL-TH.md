# SPEC §14 proposal — retained-pidfd fixture after E loss

วันที่ 5 พฤศจิกายน 2026 (Asia/Bangkok)

Input: draft PR #117 `187f80a0a40a5d8d9c3d7b286d8dbcff129e3d86`.
Round 31 APPROVE AS RUNNER PREFLIGHT เป็นผลรีวิวที่ operator ส่งมา.
เอกสารนี้เสนอ amendment สำหรับรีวิวตาม [SPEC §14](SPEC.md#14-change-control).
**PROPOSED / H LAUNCH HOLD**. Runner เดิมยังคืน HOLD แม้ preflight ผ่าน.

## 1. Profile ที่เสนอ

ให้ B เป็น direct parent และ sole lifecycle owner ของทั้ง E และ H ใน
owned inert fixture ที่มี B/E/H เท่านั้น. B สร้าง E และ H เองด้วย
`clone3(CLONE_PIDFD)` และเก็บ original pidfd ของแต่ละ role. E ทำหน้าที่
ตรวจ readiness และส่งผลที่ผูกกับ attempt; H ทำหน้าที่ inert helper.
ถ้า E สูญหาย B ยังเป็น direct parent ของ H และถือ pidfd เดิมของ H.
ข้อนี้เปลี่ยน parentage และ FD map จาก candidate รอบ 31 ที่ให้ E สร้าง H.
ต้องออกแบบ launcher/runner รุ่นถัดไปให้สอดคล้องก่อนนำไปรีวิว source.

| ความรับผิดชอบ | B | E | H |
|---|---|---|---|
| สร้าง role | สร้าง E และ H อย่างละไม่เกินหนึ่งครั้ง | ไม่มีสิทธิ์สร้าง H | ไม่มีสิทธิ์สร้างลูก |
| Stop | ส่งสัญญาณเฉพาะ original pidfd ที่ bind สำเร็จ | แจ้งผลหรือขอยุติผ่าน control channel | ออกเองผ่าน gate EOF หรือ pre-armed expiry |
| Exact reap | `waitid(P_PIDFD)` ต่อ direct child ที่ bind แล้ว แยก E/H | ไม่มี child wait | ไม่มี child wait |
| Control FDs | ถือ pidfds ทั้งสอง, gate writer, ช่องรับผล E และ terminal read ends ตาม FD map | ถือ READY reader และช่องส่งผล E เท่านั้นนอกเหนือ stdio | ถือ READY writer, gate reader และ stream writers ตาม FD map |

FD map ระดับ descriptor, pinned E/H executable และวิธีตรวจ read-end handoff
ต้องอยู่ใน source package ถัดไป. B ต้องเริ่ม terminal drain หลังยืนยันว่า E
สิ้นสุดการอ่าน READY หรือหลัง reap E ตาม fault schedule. ห้าม reader สองตัว
แข่งขันกันรับ READY. H ต้องไม่มี writer ที่ทำให้ gate EOF ค้าง. การมี pidfd
เดิมช่วยกำหนดเป้าหมาย stop ส่วน reap ต้องมี matching consuming wait แยก.

## 2. ข้อความ normative ที่เสนอ

1. B MUST จอง slot ตาม role/attempt/generation ก่อน create และเก็บ
   original pidfd กับ lifecycle state ใน B ก่อนส่งต่อ readiness.
   B MUST NOT ใช้ PID ที่ E หรือ H รายงานเป็น authority. ถ้า create
   outcome หรือ binding ยังไม่ชัด ให้ consume slot, ปิด admission
   และคืน STOP_UNCONFIRMED/HOLD. ห้าม retry, reacquire หรือ declare absent.
2. B MUST ตรวจ executable pin, FD map, เวลาเดิม และ E liveness ก่อน
   สร้าง H และก่อนยอมรับ readiness. ถ้า E สูญหายก่อนสร้าง H
   ให้ยุติ admission. หาก E สูญหายระหว่าง H create หรือก่อน READY,
   B ใช้ผล birth จาก slot ของตนเท่านั้น. เมื่อ bind สำเร็จให้เข้า
   cleanup-only โดยไม่รอ witness จาก E. ถ้า bind ไม่สำเร็จ ให้ HOLD.
3. B MUST freeze candidate เป็น UNKNOWN เมื่อ E สูญหายก่อน terminal
   evidence ครบ. B ใช้ retained pidfd สำหรับ stop และตรวจ exact
   `P_PIDFD` observation/consume ของแต่ละ child. EOF และผล wait
   ต้องบันทึกแยก. `ECHILD`, pidfd readability หรือ B exit เพียงอย่างเดียว
   ให้หลักฐาน exact reap ไม่พอ. H self-expiry ให้หลักฐานแยกจาก stop ของ B.
4. B MUST รักษา `D=min(Ta+20s,T0+45s)` หรือ inherited stricter
   `Ta+8s` subset. Readiness/admission ปิดก่อน `D−3s`; ไม่มี fresh timer
   เมื่อ E สูญหาย. Source review ต้องแสดงว่า stop, exact reap, EOF และ
   terminal report อยู่ในเวลาที่เหลือ. ถ้า proof ขาดหรือช้าให้
   STOP_UNCONFIRMED/HOLD. B ห้ามออกตาม normal-success path ขณะยังมี
   child custody ที่ไม่ยืนยัน; failure disposition และผู้รับผิดชอบ
   หลัง D ต้องมีคำตอบก่อนอนุมัติให้รัน.
5. Profile นี้ MUST จำกัด claim ที่ **E loss โดย B ยังมีชีวิตและถือ
   capability intact**. B loss, creator-side ambiguous result,
   loss ของ original handle และ kernel stall ยังเป็น residual blockers.
   การแก้ E relay gap ไม่ปิด creator-side gap. การรัน fault ที่
   containment ยังไม่ผ่านต้องอยู่ที่ HOLD. ห้ามเพิ่ม B2, watchdog,
   backup pidfd, numeric signal, pidfd reacquisition หรือ host scan.

## 3. Acceptance matrix — proposal only

| Case | Expected oracle |
|---|---|
| E loss ก่อน H birth | H create calls = 0; exact E reap แยก |
| E loss ระหว่าง H birth ก่อนเผยแพร่ slot | ถ้า B bind original pidfd ได้ ให้ stop และ exact reap โดยไม่พึ่ง E; ambiguous outcome ต้อง HOLD และห้ามทดสอบ destructive case ก่อนมี reviewed cleanup |
| E loss หลัง H bound ก่อน READY หรือระหว่าง READY | cleanup-only; exact H และ E reap แยก; EOF แยก; UNKNOWN |
| E loss หลัง READY ก่อน terminal evidence ครบ | UNKNOWN แม้ H exit code เป็น 0; ไม่มี FINAL สังเคราะห์ |
| E สูญหายพร้อม H exit | ยืนยัน H exact consume ครั้งเดียว; ห้ามใช้ exit/EOF แทน consume |
| Retained writer หรือ late cleanup | STOP_UNCONFIRMED/HOLD; ไม่มี budget reset หรือ fallback |
| B loss, lost handle หรือ kernel stall | ไม่มี profile ที่ยืนยัน stop/reap; NOT RUN จนกว่าจะมี containment ที่รีวิวแยก |

ทุกแถว NOT RUN. CI regression ของ runner เดิมไม่ใช่ evidence ของ matrix นี้.
ข้อเสนอไม่ได้เปิด G, แก้ runtime, เลือก production profile หรือปลด L1F/LH.
ขั้นถัดไปหลัง review คือประเมินความเป็นไปได้ของ source/FD map และ
failure disposition ก่อนขออนุมัติ fixture run แยก.

L1 UNPROVEN/HOLD · B4 OPEN · L1F/LH และ OA07/OA12 NOT RUN ·
J0 PAUSED · OC18 NOT RUN · R1 NOT AUTHORIZED / R2 HOLD.
