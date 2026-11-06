# L3 containment/reaper profile — SPEC §14 proposal

สถานะ **PROPOSED / H LAUNCH HOLD**. ผลรีวิวรอบ 37 ที่
`6e8e73761ec6bf3a260f74cd252322d3c26ecba4` รับรอง README
ของ L1 C lifecycle. เอกสารนี้เสนอ profile แยกสำหรับ owned inert fixture
เพื่อพิจารณาตาม [SPEC §14](SPEC.md#14-change-control).
[ขอบเขต L1 C lifecycle](../acceptance/handoff/opencode/README-L1-C-LIFECYCLE.md)
และ [FD/failure feasibility](OPENCODE-HANDOFF-L1-FD-FAILURE-FEASIBILITY-TH.md)
ยังเป็นฐานของข้อเสนอ.

## 1. ขอบเขตและผู้ถือสิทธิ์

เสนอเพิ่ม **C เป็น containment supervisor** ที่เป็น parent ของ B
และ subreaper ที่อยู่นอก cgroup ของ attempt. C สร้าง cgroup v2 ใหม่
สำหรับ attempt เดียว และต้องพิสูจน์ว่า B เกิดภายใน cgroup นี้โดยตรง
ก่อนเริ่มงาน เช่น ด้วย `CLONE_INTO_CGROUP` ถ้า platform รองรับ.
E/H ที่ B สร้างต้องอยู่ในขอบเขตเดียวกันตั้งแต่เกิด. ต้องพิสูจน์ว่า
ไม่มีงานอื่นในกลุ่ม ไม่มีสิทธิ์ migrate ออกหรือเพิ่มสมาชิกจากภายนอก
และ C ยังถือ handle ของกลุ่มเดิม. ถ้าพิสูจน์ข้อใดไม่ได้ ให้ปฏิเสธก่อน launch.

| ช่วง | B | C |
|---|---|---|
| ก่อน birth | รับ attempt/generation และ D ที่กำหนดไว้ | ถือ original containment handle, original B pidfd และหลักฐานว่า subreaper พร้อมก่อนอนุญาต B สร้าง E/H |
| ทำงานปกติ | ถือ original E/H pidfd และทำ stop/reap ตาม L1 | เฝ้าขอบเขตและเก็บหลักฐาน; ไม่มีสิทธิ์ wait แทน B ขณะ B ยังเป็น parent |
| Birth คลุมเครือ, B loss หรือ cleanup ขาดที่ D | ยุติ admission; รายงาน known/unknown custody ถ้ายังทำได้ | ถ้าได้รับอำนาจ L3 ล่วงหน้าและตรวจ boundary ได้ ใช้ stop แบบจำกัดเฉพาะกลุ่ม; exact reap ทำได้เฉพาะ child ที่ C มีสิทธิ์ wait และผูก identity ได้ |
| สิ้นสุด | คงผล L1 ที่บันทึกไว้ | บันทึก L3 แยกตามหลักฐาน stop, membership, adoption, wait และ EOF |

L3 เพิ่ม actor และสิทธิ์ใหม่จาก profile B/E/H จึงต้อง review แยก.
ทางเลือกที่เสนอคือให้ C ใช้ `cgroup.kill` เฉพาะ cgroup ของ attempt
ซึ่งอาจหยุด B ด้วย. ต้องอนุมัติผลกระทบนี้ล่วงหน้าและปฏิเสธกรณี
group identity ไม่ตรงหรือ membership proof ขาด. ห้าม fallback เป็น
numeric signal, host scan, process-group kill หรือ pidfd reacquire.

## 2. การรับช่วงและข้อจำกัดของหลักฐาน

ก่อน launch ต้องมี record ที่ผูก attempt/generation, reviewed image
pins, C/B identity, cgroup handle และ FD map, D, เงื่อนไข trigger
และอำนาจ L3 ที่อนุมัติ. ต้องตรวจว่า E/H ไม่ถือ group-control capability.
C ต้องรักษาหลักฐาน lifecycle ของ B แยกจาก E/H.

- **Birth คลุมเครือ.** C อาจหยุดขอบเขตที่ตรวจรับได้แม้ไม่ทราบว่า H เกิดหรือไม่.
  ผลกลุ่มว่างให้หลักฐานระดับ containment เท่านั้น. เมื่อไม่มี original H pidfd
  หรือหลักฐาน birth ที่ผูก identity ได้ ให้ H exact reap เป็น **UNPROVEN**
  และห้ามแปลงเป็นผลว่า H ไม่เคยเกิด.
- **Reap.** การสิ้นสุด parentage ของ B และ adoption ตาม subreaper ต้องพิสูจน์
  แยก. สำหรับ E/H ที่ identity ยืนยันได้ ข้อเสนอต้องระบุวิธีส่งมอบ
  original pidfd โดยไม่สร้าง backup pidfd และพิสูจน์ว่า C เป็นผู้มีสิทธิ์ wait
  ก่อน matching observe/consume. วิธีส่งมอบยัง **UNBOUND**. B reap แล้ว
  ต้องใช้หลักฐานของ B; C ห้าม consume ซ้ำ.
- **Evidence.** การเขียน stop สำเร็จ, `cgroup.events populated=0`,
  B exact reap, E/H exact reap และ stream EOF เป็นหลักฐานคนละรายการ.
  หาก C สูญหาย, kernel stall, group identity ขาด หรือไม่ยืนยัน adoption
  ให้คง STOP_UNCONFIRMED/HOLD. ข้อเสนอนี้ยังไม่มี fallback สำหรับ C loss.

## 3. เวลาและผลที่ D

D ของ L1 คงเดิม. เมื่อถึง D และหลักฐานยังขาด ให้ freeze ผล L1 เป็น HOLD
และปิด admission. ข้อเสนอ L3 ต้องมี **cleanup window แยกที่อนุมัติก่อน launch**
ระบุจุดเริ่ม, absolute cutoff, จำนวน stop/wait ที่อนุญาต และผู้รับผิดชอบเมื่อ
หมดเวลา. ระยะและอำนาจนี้ยัง **UNBOUND**. ผล L3 ที่ได้หลัง D ห้ามย้อนแก้
L1 verdict. ถ้าพิสูจน์ไม่ได้ว่า window ที่เสนอมีขอบเขตและผู้รับผิดชอบ
ที่ตรวจได้ ให้คง H launch HOLD.

## 4. Acceptance matrix สำหรับ review

| Fault / control | หลักฐานที่ต้องได้ก่อนพิจารณารัน |
|---|---|
| Group mismatch, membership escape หรือ C capability ขาด | fail closed ก่อน B/E/H launch; ไม่แตะกลุ่มอื่น |
| H birth คลุมเครือภายในกลุ่ม | ตรวจ scoped stop และ population แยก; ไม่มี claim H exact reap โดยไม่มี identity |
| B ยังเป็น parent / B สูญหาย | ตรวจ waiter เดียว; C ต้องพิสูจน์ adoption และ original-handle transfer ก่อน exact E/H reap |
| ถึง D โดย stream EOF หรือ consume ขาด | freeze L1 HOLD; L3 ได้เฉพาะอำนาจและ window ที่อนุมัติล่วงหน้า |
| C loss, kernel stall หรือหมด L3 window | STOP_UNCONFIRMED/HOLD; เก็บหลักฐานที่มีและระบุ authority ที่ยังขาด |

ทุกแถว **NOT RUN**. ยังไม่ได้เลือก profile, อนุมัติ post-D authority,
แก้ SPEC หรือเชื่อม runtime. ขั้นถัดไปหลัง design review คือพิสูจน์
group birth/membership, วิธีส่งมอบ handle/adoption และ bounded
cleanup window ใน feasibility packet ก่อนขออนุมัติรันแยก.

อ้างอิง [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html),
[clone3](https://man7.org/linux/man-pages/man2/clone.2.html),
[subreaper](https://man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html)
และ [waitid](https://man7.org/linux/man-pages/man2/waitpid.2.html).

L1 UNPROVEN/HOLD · B4 OPEN · L1F/LH และ OA07/OA12 NOT RUN ·
J0 PAUSED · OC18 NOT RUN · R1 NOT AUTHORIZED / R2 HOLD.
