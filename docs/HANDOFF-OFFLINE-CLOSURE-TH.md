# Handoff/checkpoint — สรุปปิดขอบเขต offline และเกณฑ์งานถัดไป

วันที่ 2 พฤศจิกายน 2026 (Asia/Bangkok). ตรวจจาก main
`7fcb3f39dfaa3fcf2535fafe5104f425cf72bc00`.
เอกสารนี้เป็น delivery 4 ตาม
[แผนทดลอง §5](HANDOFF-RECOVERY-EXPERIMENT-PLAN-TH.md#5-evidence-receipt-and-staged-exit):
ปรับภาพรวมจากหลักฐานหลัง merge; ยังต้องรีวิว/สั่ง merge เอกสารรอบนี้แยก
ไม่เพิ่ม source, controls, trial, runtime adapter หรือเลข E

## 1. สิ่งที่ส่งมอบและสถานะ

| Delivery | ขอบเขตที่เสร็จ | หลักฐาน / สถานะ |
|---|---|---|
| 1 | design/schema/checklist/preregistration | [#113](https://github.com/sc28249782/hermes-mcp-bridge/pull/113) merged `53c37737f242e87d55cea1cf525977d0202a2b01` |
| 2 | standalone offline validator, private SQLite store, advisory planner, 26 source controls | [#114](https://github.com/sc28249782/hermes-mcp-bridge/pull/114) merged `d0b8ed91544f0ad0957ab892faa54854f1f282e7` |
| 3 | frozen harness/profiles/schedules, development และ heldout อย่างละครั้ง | [#115](https://github.com/sc28249782/hermes-mcp-bridge/pull/115) merged `7fcb3f39dfaa3fcf2535fafe5104f425cf72bc00`; ผลสอง split ผ่าน independent review ที่ operator ส่งในแชต |
| 4 | ปรับ design/checklist/ROADMAP และบันทึก disposition จากผลจริง | เอกสารรอบนี้: docs-only candidate รอรีวิว; ไม่ใช่ Dev pilot |

Operator สั่ง merge stack ด้วยข้อความ “อนุมัติตามเสนอ” หลังผล heldout ผ่านรีวิว
ไม่มี exact timestamp ในข้อความ จึงไม่สร้างเวลาเพิ่ม การอนุมัตินี้ไม่ใช่ scope ของ runtime pilot
Integration head `c54a2b047759ab9747ff6887e89acbcfb373776b` รวม ancestry ของ main
โดย tree เท่ากับ reviewed result head `721163a6` และ main หลัง merge ทุก byte:
`b88b5bf7da723546629f78bceb078e4a655564cf`

## 2. ผลที่วัดได้และข้อสรุป

| Split | Arm | Correct decisions | Shared-contract recovery / eligible | Shared-contract task success / eligible |
|---|---|---:|---:|---:|
| Development | scripted baseline | 100/100 | 26/26 | 4/4 |
| Development | candidate | 100/100 | 26/26 | 4/4 |
| Heldout | scripted baseline | 100/100 | 27/27 | 5/5 |
| Heldout | candidate | 100/100 | 27/27 | 5/5 |

ต่อ split มี shared-contract 80 trials/arm และ checkpoint-specific H07/H10 อีก 20/arm
H07/H10: baseline recovery 20/20 eligible กับ candidate 2/2 eligible ต่อ split;
contract/eligibility ต่างกัน จึงห้ามสรุปเป็น causal gain/loss
Correct HOLD รวมอยู่ใน correct decisions แต่ไม่ใช่ verified recovery
ทุก split มี duplicate effects/unauthorized actions/incorrect success/timeouts/censored เป็นศูนย์ใน fixtures

**ผลเป็น tie: ยังไม่พบ task-success/recovery outcome gain ของ candidate เหนือ scripted reference**
สิ่งที่ยืนยันได้คือ candidate ทำตาม contract ที่ตรึงไว้ใน synthetic corpus นี้
ไม่ใช่หลักฐานว่าเหนือกว่ามนุษย์/โมเดล/bridge เดิมหรือเพิ่มความน่าเชื่อถือ production
สอง invocations รวม 400 arm-trials ไม่ใช่ 400 independent tasks; แยก denominator ทั้งสอง split
Public heldout เป็น frozen split ไม่ใช่ secret independent sample
Timing เก็บครบใน receipts แต่ไม่ใช้อนุมาน operational latency improvement

- [Development report](../acceptance/handoff/evaluation/DEVELOPMENT-RUN.md) /
  [receipt](../acceptance/handoff/evaluation/development-receipt.json):
  SHA256 `d1a023c6a52aba5b9f6ea4f51f88e7777317a1004dca4d8457887ba83cfafaed`
- [Heldout report](../acceptance/handoff/evaluation/HELDOUT-RUN.md) /
  [receipt](../acceptance/handoff/evaluation/heldout-receipt.json):
  SHA256 `9f7862f212397956c4fbd7f1140dddf3f021cc8aae3e04aad797d92ecd4fe07f`
- Protocol SHA256:
  `af1b4b2c1db2bdd422c7954a5065a601c7e88f4097d08e05ade4a8c4a1e2c903`.
  Source pins ทั้ง 17, corpus, budgets, runtime binding และ receipts ไม่ถูกแก้ในเอกสารรอบนี้

Development/heldout budgets ใช้ครบแล้ว; jobs ทั้งสอง disabled
ไม่มี tuning, rerun หรือเพิ่ม controls เพื่อไล่หาผล gain ใน protocol เดิม
Model/human comparison = NOT_TESTED; tokens = NOT_APPLICABLE; live backend recovery = NOT_TESTED

## 3. หลักฐาน integration หลังเปลี่ยนฐาน

ที่ exact head `c54a2b047759ab9747ff6887e89acbcfb373776b` ก่อน merge #115:

| Workflow | ผลที่ตรวจจาก logs |
|---|---|
| [Tests 41439660744](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41439660744) | 234/234 ทั้ง Python 3.12/3.14 |
| [Offline source 41439660753](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41439660753) | 26 controls ต่อ interpreter; no skips/warnings |
| [Evaluation preparation 41439660752](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41439660752) | 26 inherited + 18 preparation controls ต่อ interpreter; no skips/warnings; 0 corpus arms ใน preparation jobs |
| Jobs development-once / heldout-once | SKIPPED ทั้งคู่ |

นี่เป็น CI ก่อน merge บน integration head ไม่ใช่การอ้างว่า rerun หลัง merge หรือบนเครื่อง operator
Source controls, preparation controls และ corpus arm-trials เป็นคนละ denominator
จำนวน test ไม่ใช่ release-readiness proof

## 4. เกณฑ์จบ offline และสิ่งที่ยังเปิด

| เกณฑ์ | Disposition |
|---|---|
| design/schema ผ่านรีวิวและ merge | COMPLETE — delivery 1 |
| offline source/control ผ่านรีวิวและ merge | COMPLETE — delivery 2 |
| frozen development/heldout พร้อม receipt และ independent result review | COMPLETE — delivery 3; tie ยอมรับได้ตามแผน |
| current docs สอดคล้องผลจริงและ merge state | PRESENT ใน delivery 4 candidate นี้; รอรีวิว/merge |
| actual backend Facts collector, current authority, capability/ownership | OPEN — ไม่มี production collector/admission ใน package |
| Dev pilot และ native status/result/side-effect proof | NOT RUN / NOT AUTHORIZED โดยงานรอบนี้ |
| public tool/config/runtime integration | NOT IMPLEMENTED; ไม่มี replay/submit/cancel/resume dispatcher |
| release/deployment | ไม่ได้ขอ version ใหม่หรือเริ่ม release |

ข้อเสนอ disposition: ปิด work package ที่ระดับ **reviewed offline component + evaluation**
เมื่อ delivery 4 ผ่านรีวิว/merge; ไม่เพิ่มการทดลองใหม่เพียงเพราะผลเสมอ
Component ยังไม่ถูก hook เข้า bridge และไม่พร้อมประกาศ runtime recovery feature
Facts ที่ถูกส่งให้ planner ต้องมี trusted current collector; checkpoint/Decision ไม่เป็น authority

## 5. Boundary ของงานถัดไป

ยังไม่เสนอรัน Dev pilot เพราะหลักฐานที่ต้อง bind ยังไม่ครบ
หาก operator เลือกไปทาง runtime integration งานเตรียมถัดไปต้องเป็น design/source review
ของ backend เดียวที่ระบุชัด พร้อมรายการต่อไปนี้ก่อนขอ action:

1. Exact backend/Dev identity, native contract/capability และ original job/session IDs ที่ยืนยันได้
2. Current authority/expiry, repo/workspace/evidence bindings และ trusted Facts provenance
3. Side effects ของแต่ละ status/result/reconcile call; ห้ามถือว่า status pure โดยปริยาย
4. Owned actors/argv/timers/budgets/output/privacy/stop authority และ cessation evidence
5. Independent goal verifier และ success/HOLD oracle ของ backend นั้น
6. Finite action proposal ที่รีวิว exact source และ operator อนุมัติแยกจาก source acceptance

ไม่มีการเลือก backend, model, route หรือ live IDs ในเอกสารนี้
ไม่เพิ่ม Codex request-ID shim, ไม่แก้ native uncertainty/terminal rows และไม่ยืม scope จาก S24
การพักงาน offline ไม่ได้ unpark J0; operator ต้องเลือกว่าจะเตรียม pilot แยกหรือกลับ J0
ห้ามถือว่า “ทำขั้นถัดไป” รอบนี้ให้สิทธิ์ provision/activate เพิ่มจาก gates ที่มีอยู่

## 6. ตำแหน่งบน ROADMAP และ final release

Handoff deliveries 1–3 รวม main แล้ว; delivery 4 เป็นเอกสารปิดชุดนี้
ไม่ใช่ S24 R1/R2 หรือ Local Hands execution milestone
[S24 delivery/closure map](S24-DELIVERY-CLOSURE-TH.md) ยังคงเป็นแผน A → B → C:
A: pre-R1 source/private bindings → B: finite R1/R2 metadata acquisition →
C: Phase B acceptance, release decision/preparation/signing/publication และ deployment decision
โดย C6 deployment เป็นการอนุมัติแยกจาก release
ไม่ได้ปิดแถวใดหรือเปลี่ยน scope จากการ merge handoff

J0 parked; #112 draft `84b1ec3e0149be847d4f9d57ff095e6c1c190991`;
R1 NOT AUTHORIZED / R2 HOLD; #80/#96 และ A6/A7 ไม่เปลี่ยน
Recorded release/deployment ล่าสุดคือ signed v1.2.8 (22 ตุลาคม 2026) ตาม
[release status](RELEASE-STATUS-TH.md); รอบนี้ไม่ได้ตรวจ production สด
Hands v1.3.0 ยัง deferred ตาม capability gate เดิม ไม่มี final-release date/version ใหม่
