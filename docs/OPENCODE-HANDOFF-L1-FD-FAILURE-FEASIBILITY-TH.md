# L1 feasibility review — B/E/H FD ownership and failure disposition

วันที่ 5 พฤศจิกายน 2026 (Asia/Bangkok)

Input head `91922383db30bf88e99395365a8e7d58eba00162`.
Round 32 APPROVE AS A §14 PROPOSAL เป็นผลรีวิวที่ operator ส่งมา.
ต่อจาก [ข้อเสนอ E-loss](OPENCODE-HANDOFF-L1-E-LOSS-SPEC14-PROPOSAL-TH.md).
**SOURCE DESIGN FEASIBLE IN PART / H LAUNCH HOLD.**

## 1. การเปลี่ยน source ที่ต้องรีวิว

`l1_retained_owner.c` ปัจจุบันให้ actor เดียวสร้าง H, อ่าน READY,
ส่งสัญญาณและ reap. การย้ายชื่อ E เป็น B อย่างเดียวใช้ไม่ได้ เพราะ
profile ใหม่กำหนดให้ E อ่าน READY และรายงานผล ส่วน B ถือ stop/reap
authority ตลอดช่วง. ต้องแยก lifecycle ของ B ออกจาก READY reader
ของ E. คง parser/tuple/timer arithmetic ที่ใช้ร่วมกันได้ แต่การตรวจ
liveness ผ่าน pidfd ต้องอยู่กับ B. Runner เดิมยังคืน HOLD และ FD map
เดิมของ runner ใช้เป็น runtime map ของ proposal นี้ไม่ได้.

## 2. FD map ที่เสนอ

W/R หมายถึง write/read end. ช่องต่าง ๆ มี owner ฝั่ง writer เดียวหลัง
ผ่าน startup verification. ตารางเป็น inventory หลัง trusted child stub
ปิด FD ส่วนเกิน และก่อนเข้า role body.

| FD/slot | B | E | H |
|---|---|---|---|
| E pidfd / H pidfd | original ทั้งสองเมื่อสร้างสำเร็จ | — | — |
| H READY | R สำรองสำหรับ terminal drain เท่านั้น | R, sole protocol reader | W |
| H gate | W | — | R |
| E control | R | W สำหรับ STARTED และผล READY | — |
| H stdout/stderr | R แยกแต่ละ stream | — | W เป็น stdio |
| stdin และ stdio ของ B/E | fixed mapping ตาม launch manifest | fixed mapping | stdin แบบ inert |
| Verified image | sealed FD เฉพาะช่วง staging/exec | ปิดหลัง exec | ปิดหลัง exec |

ขั้น E birth ต้องให้ E ปิด H READY W, gate W, และ stream ends
ที่ไม่ได้ใช้ ก่อนส่ง STARTED. B ต้องตรวจ receipt ที่ผูก slot และ
ตรวจ E liveness ก่อนเริ่ม H birth. STARTED เป็นผลจาก pinned source
ภายใน fixture และ source review ต้องแสดง closed FD allowlist.
E ที่ตายหลังจุดตรวจแต่ก่อน H birth เป็น schedule แบบ interleaving
และต้องประเมินจากผล create ของ B. การอ้าง H create calls = 0 จำกัดที่
กรณี B สังเกต E loss ก่อนเรียก create.

ตอนสร้าง H แบบ clone โดยไม่ share FD table ต้องจัดการ FD ที่
child stub ได้รับชั่วคราว รวมถึง E pidfd และ gate W. ต้องปิดก่อน
H role body, ห้ามส่งสัญญาณหรือทำงานอื่นใน stub และต้อง fail closed
เมื่อ remap/close ผิด. การปิดใน stub เป็น trust boundary ของ source.
หาก requirement บังคับให้ H ไม่มี descriptor เหล่านี้แม้ในช่วง stub
กลไกนี้ยังไม่ผ่าน และต้องเสนอ launch primitive อื่นแยก.
ต้องทดสอบ FD collision ที่ stdin/stdout/stderr และ FD ที่อยู่สูงกว่า
allowlist ปกติ. B ปิด H-side writers/readers ของตนหลัง bind;
failure ก่อน handoff ต้องมีรายการปิด ends แยกตาม slot state.

**READY arbitration.** E เป็น reader เดียวจนปิด READY R ของตน
แล้วส่ง terminal READY result ที่ผูก attempt หรือจน B ยืนยัน exact E reap.
B เริ่มอ่านหลังจุดใดจุดหนึ่งนี้และใช้เพื่อ terminal drain/EOF เท่านั้น.
หาก E อ่าน frame ไปบางส่วนแล้วสูญหาย B ทิ้ง suffix ภายใต้ byte cap
และบันทึก EOF แยก. ห้ามประกอบ frame ขึ้นใหม่หรือยอมรับ READY
แทน E. หาก EOF ไม่มาให้ HOLD. B ตรวจ retained H pidfd และ deadline
ก่อนยอมรับ readiness ที่ E รายงานตามปกติ.

## 3. Failure disposition

| สถานะ | ผู้รับผิดชอบก่อน D | ผลที่ตรวจรับได้ |
|---|---|---|
| E loss ที่ B สังเกตก่อน H create | B รอ/consume E และปิด endpoints ที่ยังไม่ได้ใช้ | exact E แยก, H create calls = 0 |
| H bound และ E สูญหาย | B ยุติ admission, freeze UNKNOWN, ปิด gate และใช้ original H pidfd ตาม stop budget | exact E/H consume แยก; READY/stream EOF แยก |
| H create result คลุมเครือหรือ binding สูญหาย | B consume slot และหยุด admission. ถ้ามี binding ของ E ที่ยืนยันได้ยังจัดการ E แยก | STOP_UNCONFIRMED/HOLD. ไม่มี trusted target สำหรับ H; ห้าม retry, numeric signal, reacquire หรืออ้างว่าไม่มี H |
| B ถึง D โดยยังไม่ยืนยัน exact reap/EOF | B บันทึก known custody, ผล syscall ที่ทราบ และหลักฐานที่ยังขาด | STOP_UNCONFIRMED/HOLD. ผู้มีสิทธิ์และวิธี cleanup หลัง D ยัง UNBOUND |
| B สูญหาย หรือ kernel stall | profile นี้ไม่มี owner สำรองที่ผ่าน review | residual HOLD; ไม่มี test fault injection จนกว่าจะมี containment แยก |

ใช้ timeline เดิม `D−3s` admission close, `D−1s` exact-wait cutoff,
`D−500ms` stream EOF cutoff และ D terminal. เมื่อต้องจัดการ E/H พร้อมกัน
ต้องใช้เวลาร่วมและบันทึกต่อ child. ห้ามนำ TERM/KILL wait budget ของ H
ไปเริ่มใหม่สำหรับ E. Source package ต้องแสดง timing ของทุก phase
รวมตอน B ยังไม่ทราบว่า create สำเร็จหรือไม่. Deadline จำกัดช่วง
admission/evidence และไม่เพิ่มอำนาจ cleanup หลัง D.

**Feasibility decision.** FD ownership และ READY arbitration ออกแบบต่อ
เป็น model/source review ได้สำหรับ E loss ที่ B และ handles ยัง intact.
กรณี create คลุมเครือและ exact reap ค้างหลัง D ยังไม่มี failure disposition
ที่อนุญาตให้รัน fixture. การให้ B ออก, รอไม่จำกัด หรือขยาย deadline
ไม่มีอยู่ใน profile ที่เสนอ. การเปิด H ต้องรอข้อยุติที่รีวิวผ่าน
[SPEC §14](SPEC.md#14-change-control), รวม executable pin, FD-map proof
และผู้รับผิดชอบหลัง D ที่ตรวจสอบได้. หากไม่มี profile ที่รักษาเงื่อนไขได้
ให้คง HOLD และเดินงาน offline อื่น.

รอบนี้เป็น feasibility review จาก source และ design. ไม่มี source change,
runtime activation หรือ fault run. ทั้ง 7 กรณีของ proposal ยัง NOT RUN.
L1 UNPROVEN/HOLD · B4 OPEN · L1F/LH และ OA07/OA12 NOT RUN ·
J0 PAUSED · OC18 NOT RUN · R1 NOT AUTHORIZED / R2 HOLD.
