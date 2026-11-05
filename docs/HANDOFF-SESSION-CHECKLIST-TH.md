# Session handoff / recovery checklist — v1

## Current handoff checkpoint — 5 November 2026

Deliveries #113–#116 are merged. Development and heldout each recorded 200 arm-trials with tied shared-contract outcomes. See [offline closure and receipts](HANDOFF-OFFLINE-CLOSURE-TH.md).

[Draft #117](https://github.com/sc28249782/hermes-mcp-bridge/pull/117) tracks OpenCode observation. OC18 is NOT RUN. The [J0 pause record](S24-J0-PAUSE-DISPOSITION-TH.md) tracks closed PR #112 and evidence retained at `e7142cf7`. R1 NOT AUTHORIZED. R2 HOLD.

For the next session, refresh main and PR states, read the immutable receipts, and carry forward the consumed trial budgets and current approval boundaries. The checklist and initial checkpoint below retain their original context.

## Original manual checklist and initial checkpoint

ใช้กับ [design](HANDOFF-CHECKPOINT-DESIGN-TH.md) และ [experiment plan](HANDOFF-RECOVERY-EXPERIMENT-PLAN-TH.md).
วันที่ 2 พฤศจิกายน 2026; schema เป็น candidate ยังไม่มี command/tool สำหรับ runtime checkpoint
อย่ารันคำสั่งที่คาดเดาขึ้นจากเอกสารนี้ หรือถือว่า checklist สร้างสิทธิ์ใหม่

## ก่อนส่งต่อ

1. ระบุ owner/repo/branch/full SHA และ dirty-state จากหลักฐานจริง; แยก main กับ draft head
   บอก changed/uncommitted files ผ่าน private manifest ไม่อ้างว่า remote sync ถ้ายังไม่ตรวจ
2. บันทึกเป้าหมาย, allowed scope, acceptance profile, verified progress, pending work และ
   next permitted step ด้วย refs ไป dossier ที่ recipient เข้าถึงได้; lessons แยกจาก evidence
3. แนบ existing request/job/session/context IDs เท่าที่ระบบคืนมา ห้ามแต่ง ID เพื่อให้ครบ schema
   ถ้า ACK หายให้ submission_unknown; ถ้า Codex job_id หายห้าม submit ซ้ำ
4. จด native status พร้อมเวลา/source และ result/artifact/verifier references แบบแยกกัน
   ACK/worker success/exit 0 ไม่ใช่ completed goal; unknown_exit ต้องคง uncertainty
5. จด authority reference, scope/expiry ที่ยืนยันได้; ถ้าไม่ทราบให้ unknown/NOT_PROVIDED
   ไม่ส่ง key/token/raw prompt/output/private path ไป public PR หรือ context metadata
6. ระบุ external writes ที่อาจเกิดแล้วและสิ่งที่ยังไม่ทราบ ผ่าน evidence refs; อย่าเดาว่า timeout
   แปลว่าไม่มี side effect Preserve approval/HOLD boundaries และ attempt budgets เดิม

## ตอนรับกลับ

1. อ่าน repo/PR/roadmap/contracts ปัจจุบันและ handoff/dossier ไม่ใช้ chat summary เป็น authority
2. Validate metadata/schema/checksum/current generation/bindings ก่อน action ไม่ execute refs
3. ตรวจสิทธิ์ปัจจุบันใหม่ แล้วตรวจ backend call ว่าอาจ mutate/reconcile/cancel หรือไม่
4. Reconcile original IDs ผ่าน route ที่ได้รับอนุญาต; unknown ไม่เท่ากับ failed/completed
   ไม่สร้าง request ใหม่เพื่อหลบ idempotency/approval และไม่ bind/reopen closed context
5. ถ้าใช้ Hermes bridge ในขั้นที่ได้รับ scope ให้เริ่ม health; submit ACK ต้องตามด้วย status/result
   continue ใช้เฉพาะ returned owned session ตาม backend contract; checkpoint ไม่มี resume authority
6. ปิด goal เมื่อ terminal/result/artifact/verifier ตรง acceptance profile ปัจจุบันเท่านั้น
   หาก mismatch ให้ HOLD เฉพาะ dependent action พร้อม fixed reason/required evidence

## Checkpoint ของงานที่ส่งต่อเข้ามารอบนี้

- Repo: sc28249782/hermes-mcp-bridge; main `93e9601f74b3e0bc1d963d65635d82f7083eca8a`.
- งาน handoff: gap/design/schema/experiment plan ready for review; runtime NOT IMPLEMENTED;
  paired recovery experiments NOT RUN; gain/held-out transfer NOT MEASURED/NOT TESTED.
- S24 #112 head `84b1ec3e0149be847d4f9d57ff095e6c1c190991` เป็น draft แยก; actual attempt four
  record `99271208`: HOLD/BACKSLASH, consumed 4, recorded matching digests 3, E12 UNKNOWN.
- V2 literal-name เป็น design recommendation ยังไม่ selected/implemented; no fifth invocation.
- J0 พักระหว่างทำ handoff; R1 NOT AUTHORIZED / R2 HOLD; A6/A7 และ #80/#96 unchanged.
- ขั้นถัดไปของ handoff หลัง design review: small standalone offline validator/store/planner
  source candidate + H01–H10 meaningful controls; ยังไม่ hook bridge/MCP/runtime หรือ deploy.
- Refresh exact PR/SHA/state ก่อนเริ่มงานรอบใหม่; checklist นี้เป็น dated snapshot ไม่ใช่ live status.
