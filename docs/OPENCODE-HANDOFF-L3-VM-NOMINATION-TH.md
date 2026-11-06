# L3 — Candidate VM nomination และขอบเขต preflight รอบ 42

**OPERATOR DECISION PENDING · DESIGN REVIEW ONLY · H launch HOLD · R1 NOT AUTHORIZED · R2 HOLD**

ฐานรีวิวคือ draft PR #117 ที่ `e54ee8ecfb9b18b7e1d07f235a2f3a7e008f971d`.
รอบ 41 ได้ **APPROVE AS PIN PACK · DESIGN-REVIEW ONLY**. CI ณ head นั้นผ่าน
14/14 หลังรัน Tests ซ้ำบน SHA เดิม. [Tests run](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/42046955950)
บันทึกทั้ง attempt 1 ที่แตกไฟล์ ShellCheck ไม่สำเร็จก่อนเริ่มทดสอบ และ attempt 2 ที่ผ่าน.

## 1. ข้อมูลที่ operator ต้องระบุ

| ช่อง | ค่าที่ต้องส่งให้ reviewer | สถานะ |
|---|---|---|
| Candidate VM | ชื่ออ้างอิงหรือ VM ID ของ Linux VM แยกสำหรับ owned inert fixtures, ผู้ดูแล และยืนยันว่า VM อยู่ในขอบเขตทดสอบของ operator | UNBOUND |
| Preflight collector | ผู้เก็บข้อมูลและวิธีเข้าถึง VM ภายใต้บัญชีที่ระบุ. ส่งชื่ออ้างอิงบัญชีได้โดยไม่ส่ง credential | UNBOUND |
| Evidence recipient | ผู้รับหลักฐานและผู้ตัดสิน residual disposition เมื่อ C หรือ observer ขาดหาย. ถ้าคนละรายให้ระบุทั้งสองราย | UNBOUND |
| ขอบเขตที่อนุมัติ | ระบุแยกว่าจะอนุญาตเฉพาะ read-only preflight ตาม §2 สำหรับ VM ใด ภายใต้บัญชีใด หรือคง HOLD | PENDING |

การ nominate VM และการอนุญาตให้เก็บข้อมูลเป็นคนละรายการ. การตอบรับสองรายการนี้
ครอบคลุมเพียง preflight ที่ระบุ. การเลือก L3 profile, SPEC amendment,
การติดตั้งหรือรัน probe และการอนุญาตทดสอบยังเป็นการตัดสินใจแยก.

## 2. Read-only preflight ที่เสนอให้อนุมัติ

| เก็บจาก VM/boot ที่ nominate | ส่งกลับใน record | ข้อจำกัดของหลักฐาน |
|---|---|---|
| Kernel และ boot metadata | VM alias, boot identity token, kernel release/build, architecture และ config ที่อ่านได้ พร้อม provenance | ถ้า config อ่านไม่ได้ให้บันทึก unavailable. ห้ามยกระดับสิทธิ์เพื่อเติมข้อมูล |
| Mount และ namespace ของ collector | cgroup v2 mount แบบสรุปพร้อม flags, PID/cgroup namespace identity ของ collector, cgroup ของ collector และ timestamp | ผลของ collector ใช้แทน namespace หรือ retained FD ของ C/B/E/H ไม่ได้ |
| ข้อมูลสิทธิ์ที่มองเห็น | สรุป UID/GID, capabilities, seccomp และ metadata ของ delegation ที่ operator ระบุ ถ้ามองเห็นจากบัญชีที่อนุมัติ | การอ่าน metadata ใช้ยืนยัน effective permission สำหรับ clone, migration หรือ kill-write ไม่ได้ |
| ที่มาของหลักฐาน | review SHA, เวลาเก็บ, ชื่อ collector, วิธีอ่านต่อ field และค่า `OBSERVED`, `UNAVAILABLE` หรือ `NOT_APPLICABLE` พร้อมเหตุผล | ปกปิด credentials, env dump และรายละเอียด host ที่อยู่นอก scope. เก็บ identity token ให้เทียบซ้ำได้ใน boot เดิม |

ขอบเขตคืออ่าน metadata ของ VM ที่ระบุด้วยสิทธิ์เดิม. ห้ามสร้าง/แก้ cgroup,
เปิด kill control เพื่อเขียน, ทดสอบ clone/pidfd/adoption, เรียก signal,
รัน fixture, ติดตั้งแพ็กเกจ หรือเปลี่ยนค่า VM. เมื่อ VM/boot identity ไม่ตรง
หรือข้อมูลต้องใช้สิทธิ์เพิ่ม ให้หยุดและรายงานช่องที่ขาด.

## 3. สิ่งที่ยังต้องตัดสินก่อนขอรัน

| Gate | เกณฑ์ตัดสินหลัง preflight |
|---|---|
| Environment binding | Reviewer ตรวจ record ที่ผูกกับ candidate VM/boot และแยกค่าที่อ่านได้จาก runtime binding ที่ยัง UNBOUND. หาก boot เปลี่ยน ให้ยืนยัน binding ใหม่ก่อนใช้หลักฐาน |
| Runtime boundary และ custody | ต้องมีหลักฐานแยกสำหรับ leaf/retained FD, authority จริงของ actor, migration closure, original pidfd transport และ adoption ตาม [Evidence Plan](OPENCODE-HANDOFF-L3-EVIDENCE-PLAN-TH.md). Metadata preflight ปิด gate เหล่านี้ไม่ได้ |
| Timing และ residual disposition | ต้องยืนยัน observer, recipient, clock และ operation caps. ค่า `Δ = 2000 ms` จาก [Pin Pack](OPENCODE-HANDOFF-L3-PIN-PACK-TH.md) ยังเป็นข้อเสนอ. ถ้าขอบเขต dispatch race หรือ kill-write stall และผลค้างพิสูจน์ไม่ได้ ให้ REJECT RUN |
| Authorization | ส่งผล preflight ให้ operator พิจารณาตาม [SPEC §14](SPEC.md#14-change-control) ก่อนขออนุมัติขั้นถัดไป. CI และผล design review ไม่ใช่หลักฐาน acceptance |

Candidate VM และผู้รับผิดชอบยัง **UNBOUND**. รอบนี้จัดทำเอกสารสำหรับตัดสินใจ.
ทั้ง 5 แถว **NOT RUN**. **Draft · B4 OPEN · L1 UNPROVEN/HOLD · J0 PAUSED · H launch HOLD · R1 NOT AUTHORIZED · R2 HOLD**
