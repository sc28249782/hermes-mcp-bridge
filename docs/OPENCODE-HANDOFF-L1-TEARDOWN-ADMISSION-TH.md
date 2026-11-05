# L1 teardown admission — decision packet

วันที่ 5 พฤศจิกายน 2026 (Asia/Bangkok)

Input head `ca3869f2f0675f9f031150d1be7cbeb3d5c283af`.
Round 25 **APPROVE AS TEST MODEL** เป็นผลรีวิวที่ operator ส่งมา.
ข้อสังเกตเรื่องประกาศคลาสซ้ำตรวจจาก commit แล้วพบ `ScheduleControls`
หนึ่ง declaration ที่บรรทัด 92. ผล local 14/14 และ reviewer 14/14
เป็นหลักฐานของโมเดลตาม interpreter ที่แต่ละฝ่ายรายงาน.

อ้างอิง [L1 contract](OPENCODE-HANDOFF-L1-WAIT-CONTRACT-TH.md),
[admission schedule](OPENCODE-HANDOFF-L1-ADMISSION-SCHEDULE-TH.md)
และ [offline model](../acceptance/handoff/opencode/test_l1_admission_model.py).

## 1. Admission decision

**HOLD — ยังไม่อนุญาตให้ปิด pidfd ตัวสุดท้ายขณะ H ยังมีชีวิต.**

เส้นทางที่เสนอให้ H ออกเองเมื่อ gate EOF หรือเมื่อถึง expiry มีประโยชน์สำหรับ
fixture แต่ทั้งสองอาศัย H เดินต่อจนถึง exit. หาก H ค้าง หรือ E สูญหาย
หลัง close, แผนปัจจุบันยังไม่มีผู้ถือ capability ที่ผ่าน review สำหรับ
bounded stop และ exact reap. การรอแบบจำกัดจำนวนครั้งตรวจได้เพียง
สิ่งที่สังเกตภายใน deadline. การปิดรับผลเมื่อเลยเวลาให้ verdict HOLD
โดยไม่ยืนยันว่า H หยุดแล้ว.

| หลักฐาน | ขอบเขตที่รองรับ | สิ่งที่ต้องพิสูจน์เพิ่ม |
|---|---|---|
| 16 probes, confirmation, consume และ cutoff ใน model | จำนวน call และการตัดสินจาก scripted events | Wait จริงของ exact direct child, matching consume และ EOF ที่ตรวจแยก |
| Pre-close reject และ self-pidfd ที่ยังเปิด | จุดเรียก close ใน model ปฏิเสธเมื่อ injected readiness ไม่ครบ | Pinned H source, birth custody, timer, signal, READY และ FD ownership จริง |
| Gate EOF / pre-armed expiry ตาม design | เส้นทาง self-exit ที่ fixture เสนอ | Stop และ reap ภายใต้ fault ที่ self-exit หรือ E ใช้การไม่ได้ |
| B รอ exact E | Receipt ของ E | ผู้รับผิดชอบ H เมื่อ E สูญหาย พร้อมหลักฐาน wait ownership และ reap ของ H |

## 2. ขอบเขตก่อนพิจารณา live-close อีกครั้ง

1. **ระบุ fault envelope** ที่รับจริงก่อนตั้ง fixture. ระบุทั้งกรณี H
   ไม่อ่าน gate, expiry ไม่ถึง handler, E สูญหายก่อน/หลัง close
   และ kernel stall. กรณีที่จำเป็นต่อ safety แต่ยังคุมไม่ได้ให้คง HOLD.
2. **ระบุ stop และ reap แยกกัน** โดยระบุผู้ถือ capability, อายุ grant,
   ผู้มีสิทธิ์ wait และผู้ถือ stream ends ในแต่ละช่วง. ถ้าต้องใช้ containment
   แยก ให้เลือกและรีวิว profile นั้นผ่าน [SPEC §14](SPEC.md#14-change-control)
   ก่อนพิจารณา source integration และขออนุญาตรันแยก.
3. **รักษา budget เดิม** ใช้ `D=min(Ta+20s,T0+45s)` หรือ subset
   ที่เข้มกว่าเดิม, close ก่อน `D−3s`, H expiry `D−2s`.
   ยังคง observation/consume cutoff `D−1s`, EOF cutoff `D−500ms`
   และ closure ภายใน D. หาก containment ใช้เวลาเกินช่วงที่เหลือ
   ให้ reject ก่อน close. ไม่มี deadline ใหม่หลัง loss.
4. **กำหนด evidence ก่อน arm** โดยแยก source/READY/custody,
   liveness ณ loss, stop, exact wait/consume, EOF และ B exact-E.
   หาก liveness race ตัดสินไม่ได้ ให้บันทึก inconclusive. หาก cleanup
   proof ขาดหรือมาช้า ให้บันทึก STOP_UNCONFIRMED/HOLD. ผล candidate
   ที่ freeze เป็น UNKNOWN คงเดิม แม้ diagnostic cleanup สำเร็จ.
5. **รักษาขอบเขต capability** ห้าม numeric PID/PGID signal,
   pidfd reacquisition, backup pidfd, host scan, respawn และ watchdog
   แฝง. ห้ามทำลาย expiry route หลัง close เพื่อสร้าง negative stimulus.
   หาก profile ใหม่ต้องเปลี่ยนข้อจำกัด ให้เสนอเปลี่ยนแยกอย่างชัดเจน.

## 3. ทางเดินที่เสนอ

เดิน **retained-pidfd fixture design** ก่อนเพื่อแยกตรวจ source-bound READY,
timer readback, signal readiness และ pre-close negatives ด้วย H แบบ inert.
ออกแบบให้ original pidfd อยู่กับผู้รับผิดชอบตลอดช่วงที่ H ยัง live,
ใช้ stop/reap path เดิมที่ผ่าน review และปิด fd หลัง exact reap.
หลักฐานจากเส้นทางนี้จำกัดที่ readiness และ cleanup ก่อน handle loss.
ก่อนเสนอให้รัน ต้องมี exact source/FD map, inherited budget, fault
admission และ oracle ที่ระบุจุดปิด fd หลัง reap ให้ตรวจได้.

หากจะเดิน **L3** ให้เสนอ containment/reaper contract แยก โดยระบุ
failure-domain ownership, launch coverage, arbitration และเวลาที่เหลือ
สำหรับ cleanup. รอบนี้ยังไม่มี profile ที่เลือกหรือหลักฐานว่าผ่าน gate.

## 4. Evidence status

Docs-only decision. ไม่มีการเปิด H, ตั้ง timer, เรียก wait จริงหรือปิด
live-H pidfd ในรอบนี้. การรีวิวเอกสารนี้เป็นการรีวิว admission decision.
L1F01–L1F12 และ LH01–LH08 ยัง NOT RUN. L1 UNPROVEN/HOLD,
B4 OPEN, OA07/OA12 NOT RUN. Draft, J0 PAUSED, OC18 NOT RUN,
R1 NOT AUTHORIZED / R2 HOLD.
