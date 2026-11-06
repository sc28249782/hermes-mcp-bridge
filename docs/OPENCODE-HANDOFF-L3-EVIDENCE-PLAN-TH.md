# L3 containment/reaper — แผนเก็บหลักฐานรอบ 40

**DESIGN REVIEW ONLY · UNBOUND/HOLD · H launch HOLD · R1 NOT AUTHORIZED · R2 HOLD**

ฐานรีวิวคือ draft PR #117 ที่ `668639d68c82cc21581cb6ea351c02ccbf4819b2`.
Operator รายงานรอบ 39 ว่า **APPROVE AS FEASIBILITY REVIEW CANDIDATE**.
เอกสารนี้แปลง [feasibility packet](OPENCODE-HANDOFF-L3-FEASIBILITY-PACKET-TH.md)
เป็นข้อกำหนดสำหรับหลักฐานที่จะใช้ตัดสินในรอบถัดไป โดยอ้างอิง
[matrix เดิม](OPENCODE-HANDOFF-L3-CONTAINMENT-REAPER-PROPOSAL-TH.md)
และ [SPEC §14](SPEC.md#14-change-control).

## 1. ชุดหลักฐานก่อน admission

| Record | หลักฐานที่ต้องมี | ผลเมื่อขาด |
|---|---|---|
| Environment pin | ระบุ host/VM และ boot identity, kernel build/config, cgroup v2 mount, PID/cgroup namespaces, delegation, credentials และ seccomp ของ C/B/E/H. ผูกกับ candidate source, image digests, argv/env และ FD allowlist ที่ reviewer ตรวจได้. | **UNBOUND** ก่อนเสนอรัน |
| Attempt boundary | ผูก attempt/generation กับ cgroup domain leaf ใหม่ที่ว่าง ผ่าน retained directory FD และ mount/object identity. ตรวจ type และการไม่มี descendants. เปิด `cgroup.events` สำหรับอ่านและเตรียม `cgroup.kill` สำหรับเขียนแบบ relative จาก FD เดียวกันภายใต้ mount ที่ตรวจแล้ว. บันทึก provenance ของ FD แต่ละตัว. | Reject ก่อนสร้าง B/E/H ถ้า binding หรือ capability ไม่ครบ |
| Birth และ membership | C ตั้ง subreaper ก่อน create และอยู่ภายนอก leaf. บันทึก direct birth ของ B จาก `clone3(CLONE_INTO_CGROUP \| CLONE_PIDFD)` ที่ผูกกับ directory FD เดิม. B อยู่ที่ gate จนตรวจ binding. บันทึก E/H จาก create path ที่ review แล้วและ membership inheritance. แสดงว่า trusted management boundary ปิดทาง migrate เข้า/ออกและสร้าง subgroup ตลอด attempt รวมช่วง child stub และ cleanup. | ก่อน birth ให้ reject. หลัง birth ให้ปิด admission และ HOLD. งด group stop เมื่อ identity หรือ membership scope ขาด |
| Isolation control | ใช้ decoy เฉพาะ fixture ที่ได้รับอนุญาตเพื่อแยก mismatch จาก target จริง. เก็บว่ามี action ใดไปยัง decoy และตรวจว่า C, B และ E/H ถือเฉพาะ capabilities ที่กำหนด. | Reject เมื่อ decoy ถูกแตะ หรือ B/E/H มี group-control capability |

ให้ตรวจความว่างและความเป็น leaf ก่อน birth พร้อมหลักฐานว่า boundary ถูกคุมต่อเนื่อง.
เมื่อเก็บ population ตอนจบ ต้องปิดทุก birth path และระบุผลของ create ที่อยู่ระหว่างดำเนินการ.
ถ้ายังแยกไม่ได้ว่า create จบหรืออาจมีงานเกิดภายหลัง ให้ population เป็น observation
ตามเวลาที่อ่าน และคง HOLD. Evidence ของ host, kernel และ FD binding จริงยัง **UNBOUND**.

## 2. ตาราง custody และ waiter ที่ต้องตรวจต่อ role

C ถือ original B pidfd และเป็น waiter ของ B ตั้งแต่ B birth.
B ถือ original E/H pidfd และเป็น waiter ของ E/H ขณะยังเป็น parent.
การถือ FD และสิทธิ์ wait บันทึกแยกกัน.

| เหตุการณ์ | หลักฐานขั้นต่ำ | การตัดสิน |
|---|---|---|
| Birth หรือ receipt คลุมเครือ | บันทึก slot ที่จองก่อน create, attempt/generation/role และผล create ที่ทราบ. | Freeze slot. ถ้า original FD provenance ขาด ให้ exact reap ของ role นั้น UNPROVEN |
| เตรียมส่ง | B ปิด admission และหยุด wait path ของ role นั้นก่อนส่ง. ระบุสถานะก่อนส่งว่า consume ค้าง, consume สำเร็จพร้อม receipt หรือยังไม่ consume. | ห้ามส่งต่อสิทธิ์ consume เมื่อสถานะเดิมขัดกันหรือ consume ค้าง |
| ส่ง / รับ / ACK | ส่ง pidfd เดิมด้วย `SCM_RIGHTS` ผ่าน private Unix socket. C ตรวจ peer, attempt/generation/role/sequence, FD count, truncation, replay และ close-on-exec. ACK ต้องผูกกับ sequence เดียวกัน. B ปิด reference ฝั่งส่งหลัง ACK. | ปิด FD ที่รับผิดหรือเกินจำนวน. Reference ซ้อนจำกัดอยู่ในช่วงส่ง. C เก็บ FD ที่ตรวจผ่าน แต่รอ adoption ก่อนใช้ wait |
| B ตายก่อน send หรือหลัง send ก่อน ACK | เก็บ phase สุดท้ายที่ยืนยันได้และสถานะ receipt/FD ฝั่ง C. ถ้า FD อยู่ในคิว ให้ตรวจ provenance และเงื่อนไขเดียวกับการรับตามปกติ. | ไม่มี FD ที่ตรวจรับได้ หรือพิสูจน์ว่า B หยุด wait path ไม่ได้ ให้ exact reap UNPROVEN. การไม่มี ACK เพียงอย่างเดียวไม่ได้ยืนยันว่า C รับหรือไม่ได้รับ FD |
| B ตายหลัง consume ก่อน commit receipt | เก็บ phase ที่ทราบ, B exit evidence และหลักฐาน consume ที่มี. | คง exact reap UNPROVEN เมื่อ matching receipt ขาด. ห้าม consume ซ้ำเพื่อเติมหลักฐาน |
| Adoption และ exact reap | ยืนยัน B exit แยก, topology ของ nearest subreaper, การปิด auto-reap และการไม่มี concurrent waiter. หลัง adoption ใช้ original FD ที่ตรวจรับได้ทำ `waitid(P_PIDFD, …, WEXITED \| WNOWAIT \| WNOHANG)` และ matching consume ผ่าน FD เดิม. | ผลว่าง, `ECHILD`, mismatch หรือ consume ไม่ยืนยันภายใน cutoff ให้ UNPROVEN/HOLD. B receipt ที่ยืนยันแล้วให้ใช้ผลเดิม |

สำหรับแต่ละ event ให้บันทึก attempt/generation, role, phase/sequence, actor,
handle provenance token, monotonic timestamp, action/result และสถานะ custody ก่อน/หลัง.
เลข FD ใช้อ้างถึง slot ภายใน actor. Review ต้อง trace จาก birth FD ถึง matching wait
และตรวจได้ว่าเมื่อ receipt ขาด ผู้ตัดสินยังแยกได้ว่า evidence รายการใดสูญหาย.
Transport, ACK-loss policy และ adoption บน kernel จริงยัง **UNBOUND**.

## 3. Grant, cutoff และ residual ownership

| ช่องที่จะ pin ก่อนเสนอขอรัน | ข้อกำหนดที่ต้อง review |
|---|---|
| Owner / scope / trigger | C instance ของ attempt/generation เดิม, bound leaf identity, trigger ที่อนุญาตก่อน D และหลัง D, authority ของแต่ละช่วง และการยอมรับผลที่ stop อาจหยุด B/E/H พร้อมกัน |
| Clock / window | ใช้ clock domain เดียวกับ D. คง L1 admission ที่ D−3s, exact wait cutoff ที่ D−1s และ stream cutoff ที่ D−500ms. Freeze L1 verdict ที่ D. Post-D เริ่มที่ D และเริ่ม action ได้เมื่อเวลายังน้อยกว่า absolute cutoff `D+Δ`. ผลที่ถึงหรือเลย cutoff ลง late ledger แยก |
| Operation budget | Group stop สูงสุดหนึ่งครั้งรวม pre/post-D. จอง budget ก่อนเริ่ม write และห้าม retry เมื่อผล write คลุมเครือ. จำกัด observe/consume หนึ่งคู่ต่อ role ที่มีสิทธิ์ wait พร้อม pin read/notification caps และ wall-clock budget ของแต่ละ phase ภายใต้ cutoff ร่วม. ห้าม reset budget |
| Observer / recipient | Observer นอก C และนอก cgroup เฝ้า deadline และบันทึก C loss/stall พร้อมแจ้งผู้รับรายงานที่ระบุใน grant. Observer ไม่มีสิทธิ์ signal หรือ reap. ระบุช่องส่งหลักฐานที่ยังทำงานเมื่อ C ค้างและผู้รับผิดชอบ residual disposition |
| Evidence / closure | บันทึก stop write, population, B/E/H exact reap ต่อ role และ READY/stream EOF แยกกัน. บันทึกเวลาเริ่ม/จบ syscall และ disposition ณ cutoff. ถ้าหลักฐานยังขาดให้ `STOP_UNCONFIRMED/HOLD` พร้อมรายการ outstanding custody และ action ที่อาจยังค้าง |

ค่าจริงของ Δ, phase budgets, read/notification caps, observer และผู้รับรายงานยัง
**UNBOUND**. Reviewer ต้องเห็นว่า observer ตัดสินได้ภายในขอบเขตที่กำหนดแม้ kill-write
ค้าง และมี disposition ที่ตรวจได้สำหรับ syscall ซึ่งอาจกลับมาหลัง cutoff.
ถ้ายังพิสูจน์ไม่ได้ให้ reject การรัน. ผล late completion ไม่เปลี่ยน L1 verdict.
ห้าม numeric signal, host scan, process-group kill และ pidfd reacquire.

## 4. เกณฑ์ตรวจแผนตาม matrix เดิม

| แถว | ชุดหลักฐานและ negative control ที่ต้อง trace | สถานะ |
|---|---|---|
| 1. Boundary mismatch / escape / capability | Environment และ boundary records → สลับ decoy FD, เปิด migration path หรือตัด capability → reject ก่อน birth หรือ HOLD หลัง birth ตามจุดที่พบ. Decoy ไม่มี action | **NOT RUN** |
| 2. H birth คลุมเครือ | Birth slot + original group stop/population records → ตัด receipt หลัง create → ไม่มี retry หรือ claim H exact reap เมื่อ identity ขาด | **NOT RUN** |
| 3. B ยังเป็น parent / B loss | Custody ledger → พยายามให้ C wait ก่อน adoption, ตัด B ตามช่วงใน §2, ส่ง stale/wrong-role FD → ไม่มี consume ก่อน adoption หรือ consume ซ้ำ | **NOT RUN** |
| 4. ถึง D โดย EOF หรือ consume ขาด | L1 verdict ณ D + L3 grant/ledger → หน่วง EOF และ consume แยกกัน และใช้ grant ที่ขาดหรือหมดอายุ → L1 freeze HOLD และไม่มี action หลัง D เมื่อ grant ไม่ครอบคลุม | **NOT RUN** |
| 5. C loss / stall / window หมด | Observer + residual custody record → จำลอง C หาย, kill-write ค้าง, หรือ late completion → STOP_UNCONFIRMED/HOLD ภายใน cutoff ของ policy และไม่มี action ใหม่หลัง cutoff | **NOT RUN** |

รอบนี้ขอให้ reviewer ตรวจว่าแต่ละแถวมี evidence owner, pass/reject criteria และวิธี
แยกสถานะ UNPROVEN ครบหรือไม่. การเลือก profile, SPEC amendment และการอนุญาตรัน
เป็นการตัดสินใจแยกตาม [SPEC §14](SPEC.md#14-change-control).

**Draft · B4 OPEN · L1 UNPROVEN/HOLD · L1F01–L1F12 และ LH01–LH08 NOT RUN · OA07/OA12 NOT RUN · J0 PAUSED (#112 @ e7142cf7) · OC18 NOT RUN · H launch HOLD · R1 NOT AUTHORIZED · R2 HOLD**
