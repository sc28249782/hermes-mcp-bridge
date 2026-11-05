# Handoff/checkpoint — สรุปปิดขอบเขต offline และเกณฑ์งานถัดไป

## Current selected next design — 3 November 2026

Delivery 4 merged through #116 at `d7515c5f`; earlier candidate statements below
are historical. The offline component/evaluation package remains closed with
tie/no demonstrated gain; its source/protocol/receipts and consumed budgets stay frozen.

Operator explicitly selected the separate
[OpenCode passive observation design](OPENCODE-HANDOFF-INTEGRATION-DESIGN-TH.md)
with [preregistered controls](OPENCODE-HANDOFF-CONTROLS-TH.md).
This selects one backend and a narrow design/source-analysis profile only.
No Dev/backend calls, implementation, new experiment, runtime tool/config change
or pilot approval. The six gates in section 5 remain required; safe SQLite
capture and current authority/context/goal-verifier contracts are source blockers.

J0 remains paused on draft #112 at the operator-approved
[pause record](https://github.com/sc28249782/hermes-mcp-bridge/blob/e7142cf71792475af9375140df39acd55944d8d1/acceptance/s24/observed/J0-ROUTE-PAUSE.md).
R1 NOT AUTHORIZED / R2 HOLD; no S24 obligation/authority or release/deployment
gate is changed. This new explicit selection supersedes only earlier statements
that no backend/design path had been selected, not their execution restrictions.


วันที่ 2 พฤศจิกายน 2026 (Asia/Bangkok). ตรวจจาก main
`7fcb3f39dfaa3fcf2535fafe5104f425cf72bc00`.
เอกสารนี้เป็น delivery 4 ตาม
[แผนทดลอง §5](HANDOFF-RECOVERY-EXPERIMENT-PLAN-TH.md#5-evidence-receipt-and-staged-exit):
เอกสาร delivery 4 merge ผ่าน [#116](https://github.com/sc28249782/hermes-mcp-bridge/pull/116) แล้ว

## 1. สิ่งที่ส่งมอบและสถานะ

| Delivery | ขอบเขตที่เสร็จ | หลักฐาน / สถานะ |
|---|---|---|
| 1 | design/schema/checklist/preregistration | [#113](https://github.com/sc28249782/hermes-mcp-bridge/pull/113) merged `53c37737f242e87d55cea1cf525977d0202a2b01` |
| 2 | standalone offline validator, private SQLite store, advisory planner, 26 source controls | [#114](https://github.com/sc28249782/hermes-mcp-bridge/pull/114) merged `d0b8ed91544f0ad0957ab892faa54854f1f282e7` |
| 3 | frozen harness/profiles/schedules, development และ heldout อย่างละครั้ง | [#115](https://github.com/sc28249782/hermes-mcp-bridge/pull/115) merged `7fcb3f39dfaa3fcf2535fafe5104f425cf72bc00`; ผลสอง split ผ่าน independent review ที่ operator ส่งในแชต |
| 4 | ปรับ design/checklist/ROADMAP และบันทึก disposition จากผลจริง | [#116](https://github.com/sc28249782/hermes-mcp-bridge/pull/116) merged |

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
| current docs สอดคล้องผลจริงและ merge state | COMPLETE — delivery 4 merged via #116 |
| actual backend Facts collector, current authority, capability/ownership | OPEN — ไม่มี production collector/admission ใน package |
| Dev pilot และ native status/result/side-effect proof | NOT RUN / NOT AUTHORIZED โดยงานรอบนี้ |
| public tool/config/runtime integration | NOT IMPLEMENTED; ไม่มี replay/submit/cancel/resume dispatcher |
| release/deployment | ไม่ได้ขอ version ใหม่หรือเริ่ม release |

Work package ปิดที่ระดับ **reviewed offline component + evaluation** หลัง #116 merge.
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

การเลือก backend, model, route และ live IDs สำหรับ runtime ใช้ scope แยกตามหลักฐานของงานนั้น
ไม่เพิ่ม Codex request-ID shim, ไม่แก้ native uncertainty/terminal rows และไม่ยืม scope จาก S24
การพักงาน offline ไม่ได้ unpark J0; operator ต้องเลือกว่าจะเตรียม pilot แยกหรือกลับ J0
ห้ามถือว่า “ทำขั้นถัดไป” รอบนี้ให้สิทธิ์ provision/activate เพิ่มจาก gates ที่มีอยู่

## 6. ตำแหน่งบน ROADMAP และ final release

Handoff deliveries 1–4 รวม main แล้วผ่าน #113–#116 ในขอบเขต offline component และ evaluation.
[S24 delivery/closure map](S24-DELIVERY-CLOSURE-TH.md) ยังคงเป็นแผน A → B → C:
A: pre-R1 source/private bindings → B: finite R1/R2 metadata acquisition →
C: Phase B acceptance, release decision/preparation/signing/publication และ deployment decision
โดย C6 deployment เป็นการอนุมัติแยกจาก release
ไม่ได้ปิดแถวใดหรือเปลี่ยน scope จากการ merge handoff

J0 PAUSED. #112 ปิดโดยเก็บหลักฐานที่ `e7142cf7` ตาม [บันทึกพัก](S24-J0-PAUSE-DISPOSITION-TH.md).
R1 NOT AUTHORIZED. R2 HOLD. §22 acceptance HOLD.
[Draft #117](https://github.com/sc28249782/hermes-mcp-bridge/pull/117) ติดตาม OpenCode observation แยกต่างหาก. OC18 NOT RUN.
Recorded release/deployment ล่าสุดคือ signed v1.2.8 (22 ตุลาคม 2026) ตาม
[release status](RELEASE-STATUS-TH.md); รอบนี้ไม่ได้ตรวจ production สด
Hands v1.3.0 ยัง deferred ตาม capability gate เดิม ไม่มี final-release date/version ใหม่
