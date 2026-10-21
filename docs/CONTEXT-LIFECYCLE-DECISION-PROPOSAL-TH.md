# Context lifecycle — decision packet + DRAFT SPEC amendment wording

วันที่: 21 ตุลาคม 2026.
สถานะ: **DECISION PACKET + DRAFT — ยังไม่มีผล**. ตารางคำแนะนำและถ้อยคำ normative ด้านล่างเป็นข้อเสนอรอ operator ตัดสินใจเท่านั้น. ไม่มีข้อความใดในเอกสารนี้มีผลบังคับจนกว่า operator จะอนุมัติ และ [SPEC](SPEC.md) amendment แยกได้ผ่าน review/merge ตาม [SPEC §14](SPEC.md#14-change-control).
เอกสารนี้ไม่เปลี่ยน SPEC.md, runtime, tests, config, schema หรือ production (คง signed v1.2.7 เดิม).
ฐานอ้างอิง: `origin/main` ที่ `37625609c2e00009b3916b39ef9b2b239a3eb79a` (merge ของ PR #67).
ตอบ [operator decisions ข้อ 1-5 ของ design §9](CONTEXT-P2-LIFECYCLE-DESIGN-TH.md#9-operator-decisions-ที่ยังค้าง); ข้อกำหนดเดิมอยู่ใน [SPEC §8](SPEC.md#8-work-contexts) และ [SPEC §20](SPEC.md#20-context-p1--v127-target-scope-approved-released).

## Operator approval checkpoint (21 October 2026)

Operator อนุมัติคำแนะนำ D1–D5 ตามตารางข้างล่างและสั่ง merge PR #68 เมื่อ 21 ตุลาคม 2026 โดยการอนุมัติเกิดก่อน merge commit `926a3622dc8d17fcede098f115de5a6cb028f809`; ข้อความ DRAFT ทั้งหมดในเอกสารนี้คงสถานะ historical เดิมไว้.
ถ้อยคำ normative ที่เสนออยู่ใน [SPEC §21](SPEC.md#21-context-lifecycle--closed-binding-outcome-approved-design-implementation-not-started) ของ PR amendment แยก. ข้อความนี้ยังรอ §14 review/merge และไม่ใช่ implementation; งาน runtime ต้องตามหลัง gate นั้นตามหัวข้อ 5 ข้างล่าง.
ยังไม่มี release ที่ได้รับมอบหมาย; P2 apply/delete ยัง deferred; P1 และ discovery 27 (default) / 28 (OpenCode health-only) / 33 (OpenCode execution) คงเดิม.

## 1. ขอบเขตและเงื่อนไข

- คำแนะนำทุกข้อยังไม่ได้รับการอนุมัติ; เอกสารนี้ไม่เลือกแทน operator.
- P2 apply/delete ยัง **DEFERRED**; งาน lifecycle นี้ไม่ให้ authorization ของ destructive prune. P1 warning/preview คงค่าเดิมทั้งหมด. ไม่มีเลข release ใหม่.
- ห้ามอ้างว่า implementation ปัจจุบันรองรับข้อความ DRAFT ใด; การอนุมัติทุกข้อที่เปลี่ยน semantics ต้องเริ่มด้วย SPEC amendment PR แยกก่อน runtime PR.

## 2. ตารางคำแนะนำ (5 ข้อ)

| # | ประเด็น (design §9) | คำแนะนำ | ทางเลือกอื่น | ผลต่อ contract |
| --- | --- | --- | --- | --- |
| D1 | Double-close | คงพฤติกรรมปัจจุบัน: การ close ซ้ำบน context ที่ close แล้วคืน constant error เดิม (`contexts.py` `_row`: "Context is closed; create a new context_id instead.") | Terminal response แบบ idempotent | การคงเดิม = ไม่เปลี่ยน contract, ไม่ต้องแก้ SPEC; ทางเลือกต้องผ่าน §14 |
| D2 | Error ของ bind-after-close | คง constant error เดิม; Approach A (conditional UPDATE) ต้องคืน error ข้อความเดิมเมื่อ rowcount เป็น 0 เพราะ close | เพิ่ม error เฉพาะกรณี | การคงเดิม = ไม่เปลี่ยน contract; ทางเลือกต้องผ่าน §14 |
| D3 | Audit event สำหรับ bind ที่ถูกปฏิเสธ | **Defer** — ยังไม่เพิ่ม event; ใช้ error เดิมเป็น observable เพียงพอสำหรับขั้นนี้ | เพิ่ม event ใหม่ หาก operator ต้องการ trace | หากอนุมัติภายหลัง: fields จำกัดเฉพาะ `context_id`, action และ result สถานะเชิงนับ; ห้าม run_id/job_id ใหม่, label, path, prompt; ต้องผ่าน review ตาม §10/§19 |
| D4 | ขอบเขต Approach A / Approach B | เสนอให้อนุมัติเฉพาะ **conditional registry mutation** (เมื่อ operator เห็นชอบ): bind/observe/close เป็น statement เดียวเงื่อนไข `closed IS NULL`; Approach B (durable intent) **deferred** เป็น SPEC/schema review แยก | เปิด Approach B ทันที | A ไม่เปลี่ยน schema/tool; แต่ A แก้เฉพาะการเขียน registry หลัง close — **ไม่** ปิดช่อง submit-after-close และ crash ระหว่าง submit→bind (ดู §4) |
| D5 | ACK เมื่อ backend ยอมรับแต่ bind ล้มเหลว | เพิ่ม additive binding-outcome field (ร่างใน §3.2) โดยคง run_id/job_id/request_id เดิมทั้งหมด; แทนที่ raise หลัง acceptance ด้วย success response พร้อมผล binding ชัดเจน | ไม่เพิ่ม field — ใช้ reconciliation ผ่าน existing APIs (§6) และคง raise เดิม | **เป็น contract change** แม้ signature/discovery ไม่เปลี่ยน: response semantics + error ที่ไม่ raise อีก ต้องมี SPEC amendment ผ่าน §14 ก่อน implementation; ห้ามอ้างว่าโค้ดปัจจุบันรองรับ |

ข้อความเตือนร่วม: successful backend acknowledgement ห้ามถูก mask เป็น submit failure และห้ามชวน resubmission; ผล binding ไม่ใช่สถานะ backend.

## 3. DRAFT normative wording — NOT EFFECTIVE

### 3.1 ส่วนคงเดิม (ถ้า operator เลือกคำแนะนำ D1-D4 — ไม่ต้องแก้ SPEC)

- การ close ซ้ำคืน constant error เดิม; ไม่มี idempotent terminal response.
- การ bind ต่อ context ที่ close แล้วคืน constant error เดิม; closed rows **never rebound**.
- `close` ไม่ cancel งาน backend; work ที่ backend ยอมรับก่อน close สามารถมีชีวิตอยู่ต่อหลัง close และยังเป็นของ bridge ตาม store เดิม.
- ไม่มี auto-resubmit/auto-replay/auto-rebind ทั้งหลัง close และหลัง restart ([SPEC §11](SPEC.md#11-persistence-and-migration), [§12](SPEC.md#12-error-and-unavailable-behavior) คงเดิม).
- `observe_hermes` คง pairing run→session ปัจจุบัน: อัปเดตเพียง row เดียวที่ค้นเจอ (`hermes_run_id=? AND closed IS NULL`) และห้าม UPDATE ทุก row ที่ match; พฤติกรรมกรณี run เดียวถูก bind หลาย context (one-to-many) ยังไม่ได้ตัดสิน — ต้องเป็น decision แยก ไม่ใช่การเปลี่ยนเงียบ ๆ.
- Same-input `request_id` replay: ปัจจุบัน `core.py` submit อนุญาตแบบมีเงื่อนไข — row เดิมที่มี `run_id` คืน `replayed_locally=true`; input ต่างกันถูกปฏิเสธ; กรณี uncertain ต้องอยู่ในหน้าต่าง 23 ชั่วโมงและ capabilities ต้องประกาศ durable idempotency มิฉะนั้นถูกปฏิเสธ. DRAFT นี้ไม่เปลี่ยนกติกา replay; ห้ามอ้าง exactly-once.

### 3.2 ส่วน amendment ของ D5 (ร่างเพื่อนำไปเปิด SPEC PR แยก — ยังไม่มีผล)

ร่างหัวข้อใหม่ที่จะเสนอต่อท้าย [SPEC §8](SPEC.md#8-work-contexts) (ชื่อหัวข้อและเลขกำหนดใน SPEC PR):

- เมื่อ `hermes_submit_task` หรือ `codex_submit_task` ถูกเรียกพร้อม `context_id` และ backend ยอมรับ submission แล้ว แต่การบันทึก binding ล้มเหลวเพราะ context ถูก close การเรียก tool ต้องคืน response สำเร็จตามรูปเดิมพร้อม field เพิ่ม `context_binding` ด้วยค่า `"closed_rejected"` พร้อม `context_binding_note` ค่าคงที่เพียงค่าเดียว: `"Context was closed before binding. The task remains owned by this bridge. Do not resubmit; retrieve it by its existing identifiers."`
- เมื่อ binding สำเร็จ ให้ `context_binding` มีค่า `"bound"`.
- Field นี้ปรากฏเฉพาะเมื่อ caller ส่ง `context_id`; field ทั้งหมดที่มีอยู่เดิม (`run_id`, `request_id`, `job_id`, `status`, `replayed`, `requested_*`, `next`, `context_id`) คงความหมายเดิม — ห้ามใช้ field ใหม่แทนหรือลบ field เดิม.
- ack semantics: response สำเร็จหมายความว่า backend **ยอมรับ submission** (Hermes: ได้ `run_id` กลับ; Codex: row `job_id` persist แล้ว) — ไม่ได้หมายถึง task จบ และไม่ได้หมายถึง binding มีผลเชิง registry; authority ของสถานะยังเป็น status/result เดิม.
- ห้าม mask: ถ้า submit ล้มเหลวก่อน acceptance (backend unavailable, timeout ก่อน response) พฤติกรรม error เดิมคงอยู่และห้ามแนบ `context_binding`.
- ห้าม invite resubmission: note คงที่ต้องแนะให้ดึงงานเดิมตาม identifier เท่านั้น; field ใหม่ห้ามถูกตีความเป็น failure ของ submission.
- ข้อจำกัดที่ต้องระบุใน amendment อย่างซื่อสัตย์:
  - ถ้า bridge crash ก่อนได้ response จาก backend caller อาจไม่มี backend id กลับมา; recovery ไม่รับประกันว่า status-by-id ทำได้เสมอ (Hermes: `request_id` ยังอยู่ใน `hermes_recent_tasks` โดย `run_id` อาจเป็น NULL; Codex: caller ไม่มี request id ของตัวเอง).
  - Codex timeout/partial start อาจทิ้ง durable job ที่ caller ไม่รู้จัก; การค้นทำได้เฉพาะผ่าน recency ของ `codex_recent_tasks`.
  - ไม่มี auto replay; ห้ามอ้าง exactly-once; ห้ามอนุมาน terminal จาก 404 หรืออายุ row.
- ข้อไม่ได้ตัดสิน (label ชัดใน amendment): **admission** — เมื่อไม่มี reservation (Approach B deferred) conditional UPDATE ป้องกันเฉพาะการเขียน registry หลัง close; submit ที่ precheck ผ่านก่อน UPDATE ของ close ยังถูก backend ยอมรับได้และจะได้รับผล `closed_rejected`. การปิดช่อง admission ต้องใช้ reservation และต้องเปิด SPEC/schema review แยก.
- ข้อจำกัดของ Approach B: durable intent เพียงอย่างเดียว **ไม่รับประกัน** recovery ฝั่ง remote หากไม่มี durable identifier + idempotency/outbox protocol ครบ; จึงห้ามอ้าง total correctness.
- ข้อความนี้ไม่ลดทอน [SPEC §8](SPEC.md#8-work-contexts): close ยังป้องกัน binding/continuation ผ่าน context นั้น; closed rows ไม่ถูก rebound และ continuation ผ่าน closed context ยังถูกปฏิเสธเดิม.

## 4. เงื่อนไขชุดทดสอบ synthetic (design constraint สำหรับ runtime PR ภายหลัง)

- ควบคุมจังหวะด้วย barrier/event **ก่อน** SQL transaction เริ่มเท่านั้น; ห้ามหยุด writer ค้างไว้ขณะถือ SQLite lock แล้วรอ close commit ใน process เดียวกัน (เสี่ยง deadlock).
- กรณีตาม design §7 คงเดิม โดยเพิ่ม assertion ของ D5 เมื่ออนุมัติ: bind หลัง close คืน error คงที่และไม่เขียน row; bind ก่อน close คง binding บน row ที่ close; mock backend นับ submission = 1 ในทุก interleaving ที่ backend ยอมรับ; `request_id` same-input ตามกติกา replay เดิม ไม่มี duplicate job.

## 5. Implementation gate phases (ทุกข้อที่ผ่านการอนุมัติ)

1. Operator ตัดสินใจ D1-D5 จากเอกสารนี้.
2. SPEC.md amendment PR แยก (เฉพาะข้อที่เปลี่ยน semantics เช่น D5) — review + merge ก่อนขั้นถัดไป.
3. Runtime PR เล็ก + ชุด deterministic tests (conditional UPDATE ของ bind/observe/close; binding outcome field).
4. Scoped Dev acceptance ตามขอบเขต.
5. Release/deploy เป็นขั้นตอนแยกตาม runbook.

P2 apply/delete ยัง deferred; งานชุดนี้ไม่อนุญาต destructive prune; P1 และเลข release คงเดิม.

## 6. Reconciliation ภายใต้ existing APIs หากปฏิเสธ D5 (ทางเลือก)

- Hermes: caller คง `request_id`; ใช้ `hermes_recent_tasks` (รายการ registration ไม่ใช่ live status; `run_id` อาจเป็น NULL เมื่อ crash ก่อน response) แล้ว `hermes_task_status`/`hermes_task_result` ตาม id เมื่อทราบ.
- Codex: caller ไม่มี request id ของตัวเอง; ค้นได้เฉพาะ recency ผ่าน `codex_recent_tasks`; durable job จาก timeout/partial start อาจไม่เป็นที่รู้จักของ caller — เป็นข้อจำกัดที่ยอมรับชัด.
- ไม่เสนอ bind tool ใหม่และไม่เสนอการ rebind อัตโนมัติ.

## 7. ขอบเขตที่เอกสารนี้ไม่แตะ

- ไม่แก้ SPEC.md, runtime, tests, config, schema, tool signatures, discovery counts หรือ production.
- ไม่เปลี่ยน P1, ไม่เปิด P2 apply/delete, ไม่แตะ Hands/MCP Events gates, ไม่ทำ release/deployment.
- Discovery labels อ้างตาม contract ปัจจุบัน: 27 tools default; 28 เมื่อเปิด OpenCode health (health-only); 33 เมื่อเปิด OpenCode execution.
