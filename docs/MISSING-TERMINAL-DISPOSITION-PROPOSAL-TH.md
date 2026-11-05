# Missing terminal record — operational disposition decision packet

Current checkpoint (22 ตุลาคม 2026): operator เลือก ข เพื่อออกแบบเท่านั้น; amendment ยังรอ review. Proposal status ด้านล่างคงไว้เป็นประวัติก่อนเลือก; ดูข้อความอนุมัติคำเดิมและขอบเขตท้ายเอกสาร.

วันที่: 22 ตุลาคม 2026.
สถานะ: **PROPOSAL — รอ operator เลือกแนวทาง**. เอกสารนี้ไม่แก้ contract หรืออนุมัติ disposition ของ run ใด.
ฐาน: main `71dcae67cbfa6f0b953ab8d81198d073d202ed2a` (PR #79 merge).
ขอบเขต: docs-only. ไม่มีการ probe 404 ซ้ำ, ค้น receipt ซ้ำ, restart, เปิด fixture, แก้ registry, cancel, replay หรือ resubmit ในงานนี้.

## 1. ปัญหาและหลักฐานที่มีอยู่

[PR #80](https://github.com/sc28249782/hermes-mcp-bridge/pull/80) ยังเป็น draft และ acceptance HOLD.
[บันทึกวินิจฉัย ณ head `3a566bb`](https://github.com/sc28249782/hermes-mcp-bridge/blob/3a566bb39f425aece9ababd5e9d7429cade44fa9/docs/CONTEXT-BINDING-DEV-ACCEPTANCE-TH.md) ยังรอ external review; packet นี้ใช้หลักฐานที่บันทึกไว้ ไม่อ้างว่าตรวจเครื่องใหม่.

| กลุ่ม | จำนวน | หลักฐาน / ข้อจำกัด |
| --- | --- | --- |
| Current API terminal | 8 | completed 5 / cancelled 2 / failed 1 |
| Prior positive terminal observation | 16 | Bridge เคยได้รับ terminal จาก authenticated GET ที่ run ID ตรงกัน; ต่อมา API ตอบ 404 |
| Unresolved | 1 | cached running, ปัจจุบัน 404; ไม่พบ terminal metadata หรือ exact-run terminal receipt จากแหล่งที่ตรวจ |

`Bridge.fetch` ของ Dev baseline เก็บ terminal observation และคืนผลนั้นโดยไม่ถาม API ซ้ำ.
การวินิจฉัย source ของ Hermes ที่ติดตั้งแยก completed/failed/cancelled ออกจากเส้นทาง steering requeue.
จึงไม่เหมารวม 17 responses ที่เป็น 404 ว่าเป็นงาน active หรือไม่มี terminal evidence ทั้งหมด.
แต่หลักฐานนี้ไม่ทำให้รายการ unresolved กลายเป็น terminal.

Authority ปัจจุบันไม่มี record ที่จับคู่กับ run ที่ค้าง. สาเหตุและเวลาที่ข้อมูลหายยัง **UNKNOWN**.
Process start time, sequence ที่เริ่มจาก 1, session ที่ยังอยู่, อายุ run, context ที่ closed และการไม่พบ process ไม่ใช่ terminal proof ด้วยตัวเอง.
คำว่า “record สูญหายถาวร” ใน packet นี้เป็นกรณีออกแบบ; ไม่ใช่ข้อพิสูจน์ว่าทุกสำเนาของ record นี้สูญหายแล้ว.

## 2. Contract ปัจจุบันยังมีผล

- [SPEC §11](SPEC.md#11-persistence-and-migration) ห้าม restart ส่งงานซ้ำเงียบ ๆ เปลี่ยน completed result หรือเปลี่ยน unverified outcome เป็น completed.
- [SPEC §12](SPEC.md#12-error-and-unavailable-behavior) ห้ามใช้ transport failure เป็นเหตุ resubmit, cancel หรืออนุมาน success.
- [SPEC §14](SPEC.md#14-change-control) กำหนดให้แก้ specification ก่อน merge implementation ที่เปลี่ยน status/terminal-state, recovery/persistence หรือ security semantics.
- [Quiescence gate ที่ใช้เป็นแบบ](V1.2.8-DEPLOYMENT-DECISION-TH.md) บล็อกเมื่อยังมี unknown job หรือ 404 โดยยังไม่ทราบผล. Packet นี้ไม่เพิ่มข้อยกเว้นให้ gate นั้น.
- `unknown_exit` ของ Codex เป็น terminal lifecycle ที่ backend นิยามไว้แล้ว. ห้ามนำชื่อนี้ไปติดให้ Hermes run ที่ record หายโดยไม่มี contract และหลักฐานรองรับ.

## 3. ตัวเลือกที่ต้องตัดสิน

| ตัวเลือก | สิ่งที่อนุมัติเมื่อเลือก | สิ่งที่ยังไม่อนุมัติ |
| --- | --- | --- |
| **ก — คง HOLD** | คง gate และหลักฐานเดิม; พัก acceptance จนมีหลักฐานใหม่ที่ผูกกับ run นี้ได้ | ไม่เปลี่ยน disposition, ไม่เปิด fixture, ไม่ retry polling เดิมโดยไม่มีหลักฐานใหม่ |
| **ข — ออกแบบ operational disposition แยก** | จัดทำ SPEC §14 / operations amendment PR สำหรับกรณี record หาย โดยคง task outcome เป็น unknown | ไม่ยืนยัน terminal, ไม่ adjudicate run นี้, ไม่ปลด gate, ไม่แก้ runtime หรือเริ่ม acceptance |

คำแนะนำ: **ข หากต้องการออกแบบเส้นทางดำเนินงานต่อเมื่อ terminal record กู้ไม่ได้**.
ก เป็นทางเลือกที่แคบที่สุดและคง contract ปัจจุบัน.
ข เป็นการอนุมัติให้ทำข้อเสนอ contract ถัดไปเท่านั้น; ไม่รับประกันว่าหลักฐานของ run นี้จะผ่านเกณฑ์ที่ออกแบบ.
ไม่มีการเลือก ก หรือ ข แฝงจากการ merge packet นี้ และไม่มีข้อความอนุมัติหรือ timestamp ที่แต่งขึ้น.

## 4. ขอบเขตการออกแบบถ้าเลือก ข — DRAFT, ยังไม่มีผล

Operational disposition ที่เสนอจะตอบเฉพาะว่าอนุญาต maintenance ที่ระบุได้หรือไม่.
มันไม่ใช่ backend terminal status และไม่ตอบว่างานสำเร็จ ล้มเหลว หรือไม่มีผลข้างเคียง.
ชื่อ disposition, รูปแบบ receipt และเกณฑ์ต่อไปนี้ยังต้องผ่าน review.

Evidence floor ที่ amendment ต้องกำหนดให้ตรวจได้:

1. ผูก run/request กับ backend instance, ownership และขอบเขตงานที่จะหยุดหรือสลับอย่างแน่นอน; ห้ามเลือกจาก recency หรือชื่อ process บางส่วน.
2. มีหลักฐานเชิงบวกว่า run เดิมไม่สามารถถูก dispatch/recover/replay ต่อได้ภายใต้ authority ที่เกี่ยวข้อง. 404 หรือ authority record ที่หายอย่างเดียวไม่พอ.
3. ครอบคลุม worker/child หรือ external work ที่อาจยังเขียน state พร้อมหลักฐาน ownership และ cessation ที่ตรวจได้. PID absence อย่างเดียวไม่พอ และไม่ให้หยุด process ใดจาก packet นี้.
4. เก็บ original rows, cached observations และ snapshots ไว้แบบ private โดยไม่ rewrite terminal status, purge, merge state หรือเติมผลลัพธ์ย้อนหลัง.
5. แยก receipt ของ operational decision ออกจาก backend registry. บันทึก exact scope, evidence references, ข้อที่ยัง unknown และคำตัดสินของ operator; ไม่เก็บ prompts, outputs หรือ secrets ใน public docs/audit.
6. การอนุมัติใน local terminal หาก amendment กำหนด ต้องผูกกับ exact run และ maintenance scope; ห้ามอนุมานจาก approval ของ release หรือจากการ merge เอกสาร.
7. หากหลักฐานขาด หรือพบ active writer/unknown execution ที่ไม่ครอบคลุม ให้คง HOLD. ห้ามใช้การรับความเสี่ยงแบบกว้างแทน evidence floor.

Receipt ที่แยกออกมาเป็นเพียงแนวทางออกแบบ. Packet นี้ไม่เพิ่มไฟล์ disposition ในเครื่อง ไม่เพิ่ม schema/tool/CLI และไม่อ้างว่า backend ปัจจุบันสร้างหลักฐานข้อ 2–3 ได้.
หากออกแบบแล้วพิสูจน์ cessation ไม่ได้ ทางเลือก ข ต้องจบที่ HOLD เช่นเดิม.

## 5. Review questions ของ amendment ถัดไป

- Authority ใดมีสิทธิ์ยืนยันว่า execution เดิมจบและไม่มีการ dispatch ต่อ? หลักฐานใดผูกกับ run เดิมได้แม้ authority record หาย?
- จะตรวจ descendants/external work ครบอย่างไรโดยไม่ใช้ substring kill หรืออ่าน payload?
- Receipt ถูกแก้ ปลอม หรือใช้ซ้ำต่าง maintenance scope ได้อย่างไร และจะปฏิเสธอย่างไร?
- การเปลี่ยน gate เป็นเพียง manual operations procedure หรือมี runtime/persistence change ที่ต้อง review เพิ่ม? ห้ามตัดสินว่า compatible ล่วงหน้า.
- จะทดสอบ missing evidence, mismatched identity, active child, stale/reused approval และ incomplete inventory ให้คง HOLD อย่างไร?

## 6. Gates และสถานะที่คงไว้

1. Review packet และ operator เลือก ก หรือ ข อย่างชัดเจน.
2. ถ้าเลือก ข ให้จัดทำ amendment แยก; review และ merge ก่อนใช้ semantics ใหม่.
3. ประเมินหลักฐานของ exact run ภายใต้ contract ที่ผ่านแล้ว และรับ local decision ที่ contract กำหนด. ถ้าไม่ครบให้หยุดที่ HOLD.
4. หลังอนุญาต maintenance ตาม contract ใหม่แล้ว จึงทำ full preflight ใหม่ทุก backend ก่อนพิจารณา acceptance รอบใหม่. ห้ามตัด control job กลางงาน.
5. บันทึกรอบใหม่แยกจากรอบแรก. หลักฐานภายหลังหรือ disposition ใหม่ไม่ทำให้ preflight ที่ตกหล่นของรอบแรกผ่านย้อนหลัง.

PR #80 ยังคง HOLD จนผ่าน gate ที่เกี่ยวข้องและมีรอบ acceptance ที่ถูกต้อง.
Production คง signed v1.2.8; Dev baseline คง `e7add7e` ตาม checkpoint ที่มีอยู่. Packet นี้ไม่ตรวจหรือเปลี่ยน runtime ทั้งสอง.
Release/deployment, P2 apply/delete, Hands, MCP Events และงาน systemd ยังคงเป็นขอบเขตแยกที่ไม่ได้รับอนุมัติจาก packet นี้.


## Design-scope checkpoint — 22 ตุลาคม 2026

Operator เลือกแนวทาง ข ด้วยข้อความจากแชต (verbatim):

> เห็นด้วย เลือก **ข**

ข้อความไม่มีเวลาอนุมัติที่แน่นอน จึงไม่สร้าง timestamp เพิ่มเติม. การเลือกนี้อนุมัติเฉพาะการจัดทำ SPEC/operations amendment; ไม่อนุมัติ final wording, evidence disposition ของ run ใด, local maintenance, การปลด HOLD, implementation หรือ acceptance repeat.
[ร่าง SPEC §23](SPEC.md#23-missing-terminal-operational-disposition-proposed) และ [manual procedure](OPERATIONS-TH.md#missing-terminal-manual-disposition-proposed) ยังรอ §14 review/merge. Checkpoint นี้ไม่ได้อยู่ใน tree ของ packet ก่อนหน้า `d14b34f`; ข้อความประวัติเดิมคงไว้.
