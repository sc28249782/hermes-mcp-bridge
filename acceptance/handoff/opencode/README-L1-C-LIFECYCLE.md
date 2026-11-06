# L1 C lifecycle — pre-live review guide

สถานะ **H launch HOLD / L1 UNPROVEN**. หลักฐานรอบ 36 อ้างอิง
[`877fb362`](https://github.com/sc28249782/hermes-mcp-bridge/commit/877fb362e2d92c31ce859772df6c73b60dc44acd)
และ [L1 pre-live CI](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/42031985077)
ที่ผ่าน 61/61 controls. ผล APPROVE รอบ 36 เป็นผลรีวิว pre-live integration.

## Executable pin

| ขอบเขต | สิ่งที่ตรวจได้ | หลักฐานที่ต้องมีสำหรับ runtime |
|---|---|---|
| C integration probe | Test คอมไพล์ static probe กับ C lifecycle แล้วคำนวณ SHA-256 ของ build นั้นเอง. `verified_image()` ตรวจ digest บน sealed image ก่อน exec จาก FD เดียวกัน. Digest ผิดถูกปฏิเสธก่อน exec. | Digest ของ E/H ต้องมาจาก artifact ที่ reviewer ตรวจแยกจาก invocation และระบุ build/link policy, role, argv/env และ FD allowlist. |
| Role binding | Probe ตรวจ attempt, generation, role และค่าของ pidfd จำลอง รวมถึงการปฏิเสธ fd ซ้ำข้าม role. | B ต้องบันทึก original pidfd จาก create ของตนต่อ slot. ค่า pidfd และ birth receipt จาก test ใช้ยืนยัน kernel identity ไม่ได้. |

เส้นทางทดสอบอยู่ใน [integration test](test_l1_broker_integration.py)
และ [C probe](l1_broker_integration_probe.c). คำสั่งจาก directory นี้
บน Linux ที่ system Python รองรับ memfd seals:

```sh
/usr/bin/python3 -W error::ResourceWarning test_l1_broker_integration.py -v
```

Probe รันเป็น process จริง ส่วน birth, stop, wait และ READY read เป็น
scripted I/O. ลำดับที่ยืนยันคือ stop H → reap E → drain READY → reap H.
เมื่อถึง D แล้ว stream EOF ยังขาด ผลอยู่ที่ HOLD แม้ READY EOF ยืนยันแล้ว.

## ผู้ถือ pidfd ตาม profile ที่เสนอ

| ช่วง | B | E | H |
|---|---|---|---|
| ก่อน create | จอง slot ตาม attempt/generation; ไม่มี handle ของ role ที่ยังไม่เกิด | ยังไม่เกิดหรือเป็น READY reader หลัง startup | ยังไม่เกิด |
| หลัง E/H birth ยืนยันแล้ว | ถือ original pidfd ของแต่ละ role และเป็นผู้มีสิทธิ์ stop/reap เพียงรายเดียวตามข้อเสนอ | ถือ READY read end และช่องส่งผล; ไม่มี pidfd ใน role body | ถือ gate read end และ READY/stream writers; ไม่มี pidfd ใน role body |
| E loss | เก็บ H pidfd เดิม; drain READY หลัง E ปิด reader แล้วส่งผลที่ตรวจรับได้ หรือหลัง B ยืนยัน exact E reap | หยุดอ่าน; ถ้าอ่านค้างให้ทิ้ง suffix | หยุดตาม gate หรือ retained-pidfd path ของ B |
| Exact reap ยืนยันภายใน cutoff | ปิด handle ของ role นั้นหลัง observe/consume ตรงกัน; บันทึก READY EOF และ stream EOF แยก | — | — |
| Birth คลุมเครือหรือถึง D แล้ว cleanup ไม่ครบ | เก็บหลักฐานที่ทราบและ handle ที่ยังอยู่; authority หลัง D ยัง UNBOUND | — | สถานะอาจยังไม่ยืนยัน |

ตารางระบุ FD ownership หลัง trusted child stub. การสืบทอด E pidfd หรือ
gate writer ชั่วคราวใน H stub ยังต้องมี exact FD-map review ก่อนรัน.
ดู [รายละเอียด feasibility](../../../docs/OPENCODE-HANDOFF-L1-FD-FAILURE-FEASIBILITY-TH.md).

## ทางเลือกตาม SPEC §14

| ทางเลือก | ผลต่อกรณี birth คลุมเครือและ cleanup หลัง D |
|---|---|
| คง pre-live และ HOLD | ใช้ source/mock evidence ต่อได้. ไม่มี trusted target ให้ stop เมื่อ birth คลุมเครือ และยังไม่มีเจ้าของ cleanup หลัง D. |
| เสนอ launch primitive แยก | ต้องพิสูจน์ว่า B ได้ handle ที่ผูกกับ child หรือได้หลักฐานว่าไม่มี child เกิด แม้เกิด fault ระหว่าง create. ต่อให้ปิด birth gap ได้ ยังต้องกำหนด disposition สำหรับ reap/EOF ที่ขาดเมื่อถึง D. |
| เสนอ containment/reaper profile แยก (L3) | ต้องระบุว่าใครหยุด ใคร exact reap และหลักฐานใดรับช่วง ownership ได้ในช่วง create gap และหลัง D. ต้องรีวิว capability, fault envelope และเวลาที่มีจริงก่อนเลือก. |

ข้อเสนอปัจจุบันคง **pre-live / HOLD** จนกว่าจะมี profile ที่รับผิดชอบทั้งสอง
กรณีและผ่าน [SPEC §14](../../../docs/SPEC.md#14-change-control). D เดิมเป็น
cutoff สำหรับ admission และ evidence. การเก็บ pidfd ที่ยังอยู่ไม่ใช่การให้
สิทธิ์ cleanup หลัง D. ดู [ข้อเสนอ E-loss](../../../docs/OPENCODE-HANDOFF-L1-E-LOSS-SPEC14-PROPOSAL-TH.md).

B4 OPEN · L1F/LH และ OA07/OA12 NOT RUN · J0 PAUSED · OC18 NOT RUN ·
R1 NOT AUTHORIZED / R2 HOLD.
