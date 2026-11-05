# L3 containment/reaper — candidate pin pack รอบ 41

**DESIGN REVIEW ONLY · NOT RUN · H launch HOLD · R1 NOT AUTHORIZED · R2 HOLD**

ฐานคือ draft PR #117 ที่ `a95fb57b8ffbb7857d93612ddef6bb4b197f4503`.
Operator ให้ผลรอบ 40 **APPROVE AS EVIDENCE PLAN · DESIGN-REVIEW ONLY**.
เอกสารนี้เสนอค่าตัวเลขและแบบบันทึกสำหรับรีวิวต่อจาก
[Evidence Plan](OPENCODE-HANDOFF-L3-EVIDENCE-PLAN-TH.md) ตาม
[SPEC §14](SPEC.md#14-change-control). ค่าที่เสนอเป็นเพดานสำหรับ design review
ทุก binding ที่จำเป็นต่อการรันต้องได้รับการยืนยันแยกก่อนใช้.

## 1. Candidate host และผู้รับผิดชอบ

| Binding ที่ต้องลงใน manifest | ข้อเสนอและหลักฐานที่ต้องแนบ | สถานะ |
|---|---|---|
| Host / boot / kernel | เสนอ Linux VM แยกสำหรับ owned inert fixtures และ decoy. ระบุผู้รับผิดชอบ VM, VM ID, boot ID, kernel build/config, candidate commit, image digests, argv/env และ FD allowlist. | **UNBOUND** · ยังไม่มี VM ที่ระบุ instance |
| Boundary / permissions | แนบ cgroup v2 mount/object identity, PID/cgroup namespaces, delegation, credentials และ seccomp. แสดงสิทธิ์ clone/pidfd, event read และ kill write บน leaf ที่ผูกกับ retained FD. หลักฐานต้องครอบคลุมการปิด migration, subgroup creation และ birth path ตาม Evidence Plan §1. | **UNBOUND** · ต้องยืนยันบน VM/boot ที่ pin |
| Owner / observer / recipient | C instance เป็น cleanup owner. เสนอ observer แยก process อยู่นอก C และนอก attempt cgroup มีช่องบันทึกของตนเองที่เดินต่อเมื่อ C ค้าง. Observer ไม่มี signal/reap authority. ระบุ instance, channel, evidence sink และผู้รับผิดชอบ residual disposition ที่ตอบรับหน้าที่แล้ว. | **UNBOUND** · บทบาทระบุแล้ว ส่วน instance/channel/บุคคลยังไม่ยืนยัน |

เมื่อ manifest ขาด field หรือ pin ไม่ตรง ให้ reject ก่อน admission.
หลักฐานที่อ้างต่าง boot หรือ candidate ต้องประเมิน binding ใหม่.

## 2. ตัวเลขสำหรับรีวิว

เสนอใช้ clock เดียวกับ D และให้ post-D window เป็น `[D, D+2000 ms)`.
ค่า `Δ = 2000 ms` เป็นกรอบให้ reviewer ประเมินความเป็นไปได้.
ความพร้อมของ clock, scheduling และ kernel บน host เป้าหมายยัง **UNBOUND**.
L1 คง cutoff `D−3s / D−1s / D−500ms / D` และ verdict ณ D แยกจาก L3.

| ช่วงหลัง D | Wall-clock cap | Operation cap และเงื่อนไข |
|---|---:|---|
| ตรวจ grant และ boundary แล้วพิจารณา stop `[0,500)` ms | 500 ms | ตรวจ binding หนึ่งรอบ. Group kill-write ≤1 ครั้งรวม pre/post-D. จอง budget ก่อนเข้า syscall. เมื่อผลคลุมเครือให้คงสิทธิ์ที่ใช้ไปแล้วและ HOLD |
| เก็บ readiness, exact wait และ population `[500,1750)` ms | 1250 ms | readiness wait ≤1 ครั้งต่อ role ที่มีสิทธิ์ wait และ ≤1 ครั้งสำหรับ population รวม ≤4 ครั้งใน bucket นี้. Timeout ≤1 ครั้งต่อ slot และใช้เวลาที่เหลือร่วมกัน. Exact wait ≤1 observe และ ≤1 matching consume ต่อ role รวม B/E/H ≤6 calls. อ่าน `cgroup.events` ≤2 ครั้งรวมทั้ง attempt สำหรับ baseline และผลท้าย. อ่านผลท้ายหลังปิด birth paths และ resolve create ที่ค้าง |
| สรุปและบันทึก disposition `[1750,2000)` ms | 250 ms | snapshot disposition ≤1 ครั้งจากหลักฐานที่รับทันเวลา. ส่ง cutoff record ≤1 ครั้งต่อ attempt. Observer ใช้ deadline alarm ของตนเอง ≤1 ครั้ง. เมื่อหลักฐานไม่ครบให้ STOP_UNCONFIRMED/HOLD |

เวลาเป็น offset จาก D. ไม่มี polling/retry loop, timeout rollover หรือ budget reset.
ในร่างนี้ action ก่อน D ต้องมี grant แยกและแชร์ kill/write, event-read และ wait-pair cap
กับ post-D. Readiness wait ใช้ cap เดียวกันรวมทุกช่วง. Baseline read อยู่ก่อน admission
และ final read ใช้ slot ที่เหลือหนึ่งครั้ง. ค่า duration และ caps เป็นข้อเสนอสำหรับรีวิวและยังไม่เป็น operational defaults.
ถ้า syscall ข้าม bucket/cutoff ให้บันทึกตามเวลาเกิดจริงและงด action ที่เลยเวลาของ bucket.
ผลที่มาถึงตั้งแต่ cutoff ลง late ledger. Timestamp ของ observer ต้องแยก cutoff ที่ตั้งไว้
ออกจากเวลาที่ observer บันทึกได้จริง. การตรวจเวลาใน userspace อาจถูก preempt
ก่อนเข้า syscall. ต้องครอบคลุม dispatch race ใน failure envelope และ reject
หากยืนยันขอบเขตการเริ่ม action ตาม grant ไม่ได้.

## 3. Fault episodes และเกณฑ์ตัดสิน

| Episode | หลักฐานและผลที่ต้องเห็นก่อนยอมรับ design |
|---|---|
| Stall จำลองก่อน kill-write | ให้จุดทดสอบหยุดหลังจอง budget โดยยังไม่เข้า syscall แล้วปล่อยกลับทั้งก่อนและหลัง cutoff. กรณีปล่อยกลับหลัง cutoff ต้องมี observer HOLD และไม่มี write ใหม่. แยกเหตุการณ์นี้จาก syscall ค้างจริง |
| Kill-write เริ่มแล้วและผลไม่ทราบ | ทดสอบด้วย inert fixture ในแผนที่จะขออนุญาตแยก. Ledger แสดง budget จองแล้ว, เวลาเริ่ม และสถานะ outstanding ณ cutoff. Observer บันทึก HOLD ผ่านช่องแยก. เมื่อ write กลับมาช้า ให้ลง late ledger และงด retry หรือ action ใหม่ที่หมดเวลา |
| ขอบเขต kernel stall | ต้องมีหลักฐานสำหรับ kernel build และ failure envelope ที่ pin ว่า kill-write สิ้นสุดภายในขอบเขตที่เสนอ หรือมี disposition ที่พิสูจน์ขอบเขตได้สำหรับ syscall ที่ยังค้าง โดยระบุ authority, owner, cutoff และผลที่อาจเกิดเมื่อ syscall กลับมา พร้อมการอนุมัติแยก. ผล stall จำลองพิสูจน์ได้เฉพาะ observer/ledger. ถ้าพิสูจน์ขอบเขตหรือ residual disposition ไม่ได้ ให้ **REJECT RUN** |
| ACK หายหรือ B ตาย | C เก็บเฉพาะ FD ที่ตรวจ provenance ผ่าน. หลังส่ง B คง wait path ปิดแม้ ACK หาย และไม่มี resend. บันทึก received/validated/ACK-sent/ACK-observed แยก. C ต้องพิสูจน์ adoption และ single waiter ก่อน consume. Queue ที่ไม่ยืนยัน, stale sequence หรือ consume receipt ขาด ให้ exact reap UNPROVEN. Receipt ของ B ที่ยืนยันแล้วใช้ผลเดิม |
| C loss หรือ observer ส่งผลไม่ได้ | เมื่อ C หาย ให้ observer บันทึก outstanding custody และ HOLD โดยไม่มี signal/reap. ถ้าช่องบันทึกของ observer ขาด ให้ถือว่าขาดหลักฐาน cutoff และ reject แผนรันจนมี disposition ที่ตรวจสอบได้ |

## 4. Evidence schema และการออกจาก HOLD

| Record | Required fields |
|---|---|
| Manifest | schema version, attempt/generation, candidate SHA, host/boot/kernel, namespace/mount/leaf identity, image pins, FD map, actor IDs, clock/D/Δ, bucket caps, grant ID และ recipient |
| Event | attempt/generation, actor/role, event type, sequence, timestamp, handle provenance, budget slot, action/result, custody before/after และ reference ไปยัง event ที่เกี่ยวข้อง |
| Cutoff | observer ID, scheduled cutoff, recorded timestamp, evidence IDs ที่รับทัน, unknown birth, unproven reap, outstanding syscall/custody และ verdict. แยก write result, population, exact reap ต่อ role และ READY/stream EOF |
| Late event | ใช้ attempt/generation และ operation ID เดิม, completion timestamp, result และ reference ไปยัง cutoff record. เก็บแยกจาก L1 verdict |

ผูก manifest กับ review SHA และให้ reviewer ตรวจว่าแต่ละ field มีแหล่งหลักฐาน
รวมทั้งกรณี transport/adoption จริงและ kill-write stall. Candidate host, clock/budget
validation, observer/recipient และ kernel/transport evidence ยัง **UNBOUND**.
การเลือก profile, SPEC amendment และการอนุญาตรันเป็นการตัดสินใจแยก.
Acceptance matrix ของ Evidence Plan ทั้ง 5 แถวยัง **NOT RUN**.

**Draft · B4 OPEN · L1 UNPROVEN/HOLD · L1F01–L1F12 และ LH01–LH08 NOT RUN · OA07/OA12 NOT RUN · J0 PAUSED (#112 @ e7142cf7) · OC18 NOT RUN · H launch HOLD · R1 NOT AUTHORIZED · R2 HOLD**
