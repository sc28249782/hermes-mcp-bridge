# L3 containment/reaper — feasibility packet สำหรับรีวิวตาม SPEC §14

**REVIEW CANDIDATE · UNBOUND/HOLD · H launch HOLD · R1 NOT AUTHORIZED · R2 HOLD**

## ฐานหลักฐาน

- Draft PR #117 สาขา `design/opencode-handoff-observation-20261103` มี head ก่อนเพิ่ม packet ที่ `4cd8335107d005b2bf40ae0f8efa11e2144658a7` ตรงกับ checkpoint รอบ 38. GitHub Actions สำหรับ SHA นี้ผ่าน 14/14 workflows. งาน pre-live มีขั้น Strict source build and controls without H สำเร็จ. [PR #117](https://github.com/sc28249782/hermes-mcp-bridge/pull/117) · [Pre-live](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/42038290718) · [Tests](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/42038290869)
- รอบ 38 **APPROVE AS A SPEC §14 PROPOSAL** ตาม checkpoint. [Proposal](OPENCODE-HANDOFF-L3-CONTAINMENT-REAPER-PROPOSAL-TH.md) วาง boundary ของ C, B, E/H และ matrix ห้าแถว. [SPEC §14](SPEC.md#14-change-control) กำหนดให้แก้ specification ก่อน merge implementation ที่เปลี่ยน security boundary.
- [C lifecycle](../acceptance/handoff/opencode/l1_broker_lifecycle.c) และ [pre-live integration](../acceptance/handoff/opencode/test_l1_broker_integration.py) ใช้ lifecycle I/O, birth receipts และ pidfds จำลอง. Sealed image verification และ exec จาก FD เดิมใช้จริงกับ probe build ที่ test pin เอง. Runtime image pins, kernel membership, adoption และ post-D authority ยัง UNBOUND. [README](../acceptance/handoff/opencode/README-L1-C-LIFECYCLE.md) · [L1 FD/failure feasibility](OPENCODE-HANDOFF-L1-FD-FAILURE-FEASIBILITY-TH.md)

## 1. Birth และ membership

**กลไกสำหรับพิจารณา.** ให้ C เป็น parent ของ B และตั้ง child subreaper ก่อน create. C อยู่ข้างนอก attempt cgroup ตลอดช่วงงาน. C สร้าง cgroup v2 แบบ domain leaf ใหม่ต่อ attempt/generation และเก็บ directory FD เดิม. C สร้าง B โดยตรงในกลุ่มด้วย `clone3(CLONE_INTO_CGROUP | CLONE_PIDFD)` ตามความสามารถของ kernel/host เป้าหมาย. Trusted B stub อยู่ที่ admission gate จน C ตรวจ binding และ capability ครบ. E/H เกิดในกลุ่มเดียวกันผ่าน membership inheritance จาก B ภายใต้เส้นทาง create ที่ผ่านการรีวิว และ B รับ pidfd ตอน birth แยกตาม role. [clone3](https://man7.org/linux/man-pages/man2/clone.2.html) · [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)

**ข้อสมมติที่ต้องผูกกับ environment.** Fixture เป็น owned inert image และมี process graph C→B→{E,H} ภายใน PID namespace ที่ตกลงกัน. ต้องกำหนด trusted management boundary และกันการ migrate เข้า/ออก การสร้าง subgroup และการ create นอกเส้นทางที่รีวิว. ตรวจ credential, delegation, namespace, seccomp, FD allowlist และ image/argv/env pins รวมถึง FD ชั่วคราวใน child stub. E/H และ B ไม่มี group-control FD หรือสิทธิ์เปิด group-control path. ต้องยืนยัน C อยู่ภายนอกและกลุ่มใหม่ว่างก่อน B birth. Scope ของคำสั่ง stop ต้องรวมผลที่อาจหยุด B, E และ H พร้อมกัน.

**หลักฐานที่ต้องเก็บ.** บันทึก kernel/build และ config ที่ pin, attempt/generation, C identity, cgroup mount/object identity จาก FD เดิม, FD map และเหตุการณ์ create/receipt ของแต่ละ role. เปิด control file แบบ relative กับ retained directory FD ภายใน mount ที่ตรวจแล้ว และผูก kill/events FD กับกลุ่มเดียวกัน. ต้องมีหลักฐาน identity ต่อเนื่องจนปิด cleanup และ membership proof จาก birth และการปิดช่อง migration โดยใช้ข้อมูลเฉพาะ attempt. Snapshot ของสมาชิกใช้ประกอบหลักฐาน. ถ้าหลักฐาน boundary ขาดก่อน birth ให้ reject โดยไม่สร้าง B/E/H. ถ้าขาดหลัง B birth ให้ปิด admission และ HOLD โดยงด group stop เมื่อ target binding ตรวจไม่ได้. Capability และ evidence mapping ของ host จริงยัง **UNBOUND**.

## 2. Original pidfd, adoption และ waiter

| Phase | Custody และสิทธิ์ที่เสนอ | Evidence / disposition |
|---|---|---|
| B birth | C ถือ original B pidfd และเป็น waiter ของ B. | ผูก FD จาก create result กับ attempt/generation/B และบันทึก observe/consume ของ B แยกจาก E/H. |
| E/H birth และ B ยังเป็น parent | B ถือ original pidfd ต่อ role และเป็น waiter เดียวของ E/H. | สร้าง slot ก่อน create. Bind receipt กับ FD ที่ได้จาก birth โดยตรง. ห้าม reuse slot เมื่อ birth คลุมเครือ. C ยังไม่มีสิทธิ์ wait E/H. |
| Handoff แบบร่วมมือ | เมื่อปิด admission แล้ว B หยุดเส้นทาง wait ต่อ role ก่อนส่ง descriptor ของ pidfd เดิมให้ C ผ่าน private Unix socket ที่ผูกกับ attempt. `SCM_RIGHTS` เป็นกลไก candidate. | ส่ง role/generation/attempt และ sequence ต่อ role พร้อม FD. C รับและตรวจ peer, message binding, FD count, truncation, replay และการรับแบบ close-on-exec ก่อน ACK. B ปิดสำเนาของตนหลัง ACK. ช่วงส่งมี reference ซ้อนชั่วคราวที่ต้องผ่าน §14 review และไม่มี standby pidfd. C ยังรอ adoption แม้รับ FD แล้ว. |
| B loss / adoption | C ใช้ FD ที่ผูกได้ต่อเมื่อพิสูจน์ว่าเป็น parent ผู้มีสิทธิ์ wait ของ child นั้น และมี waiter เดียว. | ตรวจว่า C เป็น subreaper ที่ใกล้สุดใน topology ที่ pin, ไม่มีผู้ consume แข่งหรือ auto-reap และ B exit ได้รับหลักฐานแยก. ใช้ผล `waitid(P_PIDFD, …, WEXITED \| WNOWAIT \| WNOHANG)` ที่มี matching status จาก child เป็นหลักฐานสิทธิ์สำหรับเส้นทาง exact reap แล้ว consume ด้วย original handle เดิมและเทียบผลทั้งสองครั้ง. `ECHILD` หรือผลว่างให้คง exact reap UNPROVEN. |
| B consume แล้ว หรือ custody ขาด | ใช้ receipt ที่ B commit ไว้เมื่อ observe/consume ตรงกัน. C ไม่ consume ซ้ำ. | ถ้า B ตายหลัง consume แต่ก่อน receipt หรือระหว่าง birth/send/ACK ให้ระบุ phase และหลักฐานที่ขาด. รับ queued FD ได้เฉพาะเมื่อ provenance, transfer state และสิทธิ์ wait ยืนยันครบ. เมื่อ binding ขาดให้คง exact reap UNPROVEN แม้ group ว่าง. |

Reference ที่ส่งด้วย `SCM_RIGHTS` อ้างถึง open file description เดิมและมีเลข FD ฝั่งรับต่างกันได้. Handoff, ACK-loss policy, FD cleanup และ adoption evidence ของ kernel จริงยัง **UNBOUND**. หากหลักฐาน consume ขัดกันให้หยุด path นั้นและ HOLD. [Unix sockets](https://man7.org/linux/man-pages/man7/unix.7.html) · [Subreaper](https://man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html) · [waitid](https://man7.org/linux/man-pages/man2/waitpid.2.html)

## 3. D และ cleanup window ที่เสนอ

- เก็บ timeline L1 เดิม `D−3s` ปิด admission, `D−1s` cutoff สำหรับ exact wait, `D−500ms` cutoff สำหรับ stream EOF และ D เป็น terminal. ที่ D ให้ freeze L1 HOLD เมื่อหลักฐานยังขาด. Ledger L3 แยก timestamp และ verdict ของตน.
- Owner ที่เสนอคือ **C ของ attempt/generation เดิม**. เมื่อ trigger ก่อน D เช่น birth คลุมเครือหรือ B loss ให้ปิด admission ทันที. การ stop ก่อน D ต้องอยู่ใน grant ที่ระบุ trigger และช่วงเวลาไว้แยก. Post-D window เริ่มที่ D แบบ absolute บน clock เดียวกับ L1 และสิ้นสุดที่ `T_cleanup = D + Δ`. ต้อง pin ค่า Δ, clock semantics, wall-clock budget ราย phase และผู้รับรายงานเมื่อ C สูญหายก่อนเสนอรัน. ค่าและผู้รับรายงานยัง **UNBOUND**.
- เสนอให้ใช้ budget ร่วมทั้ง attempt. Group stop ได้สูงสุดหนึ่งครั้งรวมก่อนและหลัง D ภายใต้ grant ที่ครอบคลุมช่วงนั้น และเมื่อ identity/membership ยังยืนยันได้. ใช้ deadline-aware readiness ภายในเวลาร่วม และกำหนด observation/consume อย่างมากหนึ่งคู่ต่อ role ที่ยังค้างและมีสิทธิ์ wait. หาก observe ว่างหรือ consume คลุมเครือให้ HOLD. ต้องระบุจำนวน read/notification operations สูงสุดและ cutoff ก่อนออกแบบ probe. ห้าม reset เวลาเมื่อเปลี่ยน role หรือ phase.
- `cgroup.kill` ใช้ SIGKILL กับกลุ่มและ descendants. บันทึกผล write, `cgroup.events populated=0` จากกลุ่มเดิม, B exact reap, E/H exact reap และ READY/stream EOF เป็นคนละหลักฐาน. ปิดทุก birth path ก่อนรับ population evidence เป็นผลสุดท้าย. Group ว่างยังปล่อย exact reap หรือ EOF เป็น UNPROVEN ได้. [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- Cutoff ของ policy จำกัดการเริ่ม action และการรับผล แต่ syscall ที่ค้างใน kernel อาจเกินเวลาได้. ต้องเสนอ independent deadline observer นอกกลุ่มและนอก C สำหรับบันทึก `STOP_UNCONFIRMED/HOLD` เมื่อ C หายหรือเกิน cutoff โดยไม่มีสิทธิ์ signal หรือ reap. หาก syscall ค้างและกลับมาหลัง cutoff ให้เก็บเป็น late evidence แยกจาก verdict และงด action ถัดไป. หากพิสูจน์ขอบเขตและ disposition ของ stall รวมถึงการค้างของ kill write ไม่ได้ ให้ reject การรัน. Observer, residual custody และการตอบสนองต่อ C loss ยัง **UNBOUND**.
- ข้อกำหนดทุกกรณีห้าม numeric signal, host scan, process-group kill และ pidfd reacquire. HOLD เมื่อขาด authority, group identity, membership, ownership, adoption หรือหลักฐานภายใน cutoff.

## 4. Acceptance matrix และเกณฑ์ตัดสิน

| แถวตาม proposal | หลักฐานที่ต้องเก็บในการรันที่ได้รับอนุญาตภายหลัง | Negative control และเกณฑ์ reject/HOLD | สถานะ |
|---|---|---|---|
| 1. Group mismatch, escape หรือ C capability ขาด | Record ก่อน birth ว่า C อยู่นอกกลุ่มและมี capability ครบ, original handle ผูกกับ leaf ว่าง, B/E/H เกิดภายในและ membership policy ปิดทาง migrate. | สลับ FD ไปยังกลุ่ม decoy, ตัด capability หรือเปิดเส้นทาง migrate. Reject ก่อน B/E/H birth เมื่อ preflight พบปัญหา. ถ้าพบ loss หลัง birth ให้ HOLD และงด stop ที่ scope ตรวจไม่ได้. Decoy ต้องไม่มี action. | **NOT RUN** |
| 2. H birth คลุมเครือ | ปิด admission, บันทึก birth ที่ unknown, scoped stop receipt และ population ของ original group. บันทึก H reap แยกตามหลักฐานที่มี. | ตัด H receipt หลัง create และวาง inert decoy นอกกลุ่ม. Reject หากแตะ decoy, retry birth, อ้างว่า H ไม่เกิด หรืออ้าง exact reap จาก population. ถ้าไม่มี identity ให้ H exact reap UNPROVEN. | **NOT RUN** |
| 3. B ยังเป็น parent / B สูญหาย | บันทึก waiter ก่อนและหลัง adoption, original FD provenance ต่อ role, matching observe/consume และ B receipt แยก. | ทดลองขอ wait ขณะ B ยังเป็น parent, ทำ B loss ก่อนส่ง FD/ก่อน ACK และหลัง consume ก่อน receipt. แทรก stale generation หรือ FD ผิด role. HOLD ต่อ role เมื่อไม่มี binding/receipt. Reject หาก C consume ก่อน adoption, consume ซ้ำ หรือประกาศ exact reap เมื่อ custody ขาด. | **NOT RUN** |
| 4. ถึง D โดย EOF หรือ consume ขาด | Ledger ณ D, grant ที่ pin กับ attempt, trigger/time/budget log และผล L3 แยกจาก L1. | หน่วง EOF และ consume แยกกันจนผ่าน cutoff และใช้ grant ขาดหรือหมดอายุ. L1 ต้อง freeze HOLD และกรณี grant ขาดต้องไม่มี post-D action. Reject หาก late success เปลี่ยน L1 verdict. | **NOT RUN** |
| 5. C loss, kernel stall หรือหมด window | Observer บันทึก cutoff, phase/operation ที่ค้าง, known/unknown custody และ residual disposition โดยแยกผล late completion. | จำลอง C หาย, kill/write หรือ wait ค้าง และผลกลับหลัง cutoff. ต้องได้ STOP_UNCONFIRMED/HOLD. Reject หากเพิ่ม budget, สั่ง cleanup ใหม่หลัง cutoff หรือรายงาน closure โดยไม่มีหลักฐาน. | **NOT RUN** |

## 5. จุดตัดสินก่อนเสนอขอรัน

1. รอบ 38 รับรอง proposal สำหรับพิจารณาตาม §14. รอบนี้ขอรีวิว **docs-only feasibility** และข้อผูกมัดรายแถว. Reviewer ระบุ accept for design review หรือ HOLD พร้อม gap ที่ต้องปิด.
2. การเลือก profile และร่าง/อนุมัติ SPEC amendment เป็นการตัดสินใจแยก. ต้องกำหนด actor, authority, boundary และ failure semantics ที่ review ได้ก่อน merge implementation.
3. ก่อนเสนอขอรันแยก ให้ pin candidate/environment/image และ FD map, scope ของ inert fixture, grant และผลของ kill ต่อ B/E/H, เวลาจริงและ operation caps, ผู้รับผิดชอบเมื่อ C สูญหาย, evidence schema และ abort/disposition รายแถว. ทุกช่องที่ยังพิสูจน์ไม่ได้อยู่ที่ UNBOUND/HOLD.

**H launch HOLD · B4 OPEN · L1 UNPROVEN/HOLD · L1F01–L1F12 และ LH01–LH08 NOT RUN · OA07/OA12 NOT RUN · J0 PAUSED (#112 @ e7142cf7) · OC18 NOT RUN · R1 NOT AUTHORIZED · R2 HOLD.**
