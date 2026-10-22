# Context binding — nonclosed ack/recovery gap decision packet

วันที่: 22 ตุลาคม 2026.
สถานะ: **PROPOSAL — รอ operator ตัดสินใจ**. เอกสารนี้เป็นข้อเสนอเท่านั้น ไม่ใช่การอนุมัติแก้ [SPEC](SPEC.md), ไม่ใช่ authorization ให้ implement runtime/tests, migrate schema, release, deploy หรือแตะ instance ที่กำลังรัน.
ฐานอ้างอิง: `origin/main` ที่ `02868ab5eba3e7784b7725e83fdb2c526603d86a` (merge ของ PR #76). Production = signed v1.2.8 deployed; Dev = pin `e7add7e` เดิม — เอกสารนี้ไม่เปลี่ยนทั้งสองฝั่ง.
ขอบเขต: ช่องว่าง acknowledgement/recovery หลัง acceptance ของ SPEC §21.2 สำหรับ binding error ที่ **ไม่ใช่** closed (DB busy, missing row, ฯลฯ). [SPEC §21.1–21.4](SPEC.md#21-context-lifecycle--closed-binding-outcome-approved-design-implementation-not-started) ทั้งหมดคงข้อความ normative เดิม; ข้อกำหนดที่ว่า "post-acceptance binding failures other than closed-rejection … MUST keep the existing error behavior" (SPEC §21.2, บรรทัด 465) ยังมีผลเต็มรูปแบบ และ error ที่มีอยู่ทุกตัวต้องคงเดิม.

## 1. Trace ของ flow ปัจจุบัน (อ้างบรรทัดจริง ณ `02868ab`)

| ขั้น | อ้างอิง | พฤติกรรม |
| --- | --- | --- |
| Precheck ก่อน backend call ใด ๆ | `bridge.py:124-129` → `contexts.py:124-125,88-96` | invalid/unknown/closed raise `ContextError`/`ContextClosedError` ก่อนเรียก backend (zero backend calls) |
| Backend ACK ปกติ (Hermes) | `bridge.py:130` → `core.py:314-318` | `POST /v1/runs` สำเร็จ, persist `run_id` ลง `runs.sqlite3` ก่อน audit (`core.py:319-321`) |
| Backend ACK ปกติ (Codex) | `bridge.py:195` → `codex_core.py:269-287` | persist job row ภายใน bounded transaction, `pending_local_approval` สำหรับ workspace-write; read-only `_start` ล้มเหลว → `_mark_start_failed` (`codex_core.py:282-284,401`) |
| Bind attempt | `bridge.py:134-142` (Hermes), `bridge.py:196-207` (Codex) → `contexts.py:127-133,148-154` | catch เฉพาะ `ContextClosedError` → `context_binding="closed_rejected"` + `_CLOSED_BINDING_NOTE` (`bridge.py:22`); สำเร็จ → `"bound"` |
| Uncertain acceptance | `core.py:210-211` | transport error/timeout → `BridgeError("Hermes transport failed or timed out; acceptance may be uncertain.")` — ไม่มี ACK, ไม่มี `run_id` คืน |
| Bind exception อื่น (ไม่ closed) | `bridge.py:134-142,196-207` | `sqlite3.OperationalError` ฯลฯ ไม่ถูก catch → propagate ออกนอก tool function; MCP คืน error ทั้งรายการ แม้ backend รับงานแล้ว |

## 2. แยกกลุ่ม outcome ให้ชัดเจน

- **ACK ปกติจาก backend**: submit คืนผลสำเร็จ (มี `run_id`/`job_id` จริง); ownership row persist แล้ว (`core.py:317-318`; `codex_core.py:269-277`).
- **ไม่มี ACK**: precheck raise, transport error/timeout (`core.py:210-211`), partial start (Codex `_start` fail หลัง persist job row), หรือ `UPDATE runs SET run_id` raise หลัง POST สำเร็จ (`core.py:317-318`) — ห้ามสร้าง acknowledgement ปลอม.
- **known-no-write**: exception เกิดก่อน `execute` หรือ `_classify_missing_or_closed` raise ใน transaction ที่ยังเปิด (`contexts.py:70-86`) — commit ไม่เกิดแน่นอน.
- **uncertain registry outcome**: caller เห็น exception ระหว่าง `commit()`/cleanup (`contexts.py:34-42`) หรือหลัง commit; exception อย่างเดียวไม่บอกว่า bind เขียนแล้วหรือยัง ต้องอาศัยหลักฐาน transaction และ row state. โดยเฉพาะ exception หลัง commit อาจเกิดทั้งที่ binding persist แล้ว.
- `context_id` ที่ echo กลับคือ **เจตนาของ request** ไม่ใช่หลักฐานว่า bind สำเร็จ; binding outcome แยกจาก job status; task status/result เป็น authority ของสถานะ backend ตาม SPEC §21.2.
- ห้ามสรุป "unbound" เพียงเพราะเกิด exception; ต้องจำแนก known-no-write กับ uncertain commit ก่อนเสมอ.

## 3. ช่องว่างที่เปิดอยู่ (the gap)

หลัง backend ACK สำเร็จ ถ้า bind raise exception ที่ไม่ใช่ `ContextClosedError`: tool คืน error ทั้งรายการ ผู้เรียกจึงไม่เห็น `run_id`/`job_id` และ output เต็มของ backend ทั้งที่ ownership persist แล้ว และ task อาจกำลังทำงาน. Recovery จำกัดที่ API เดิม: `hermes_recent_tasks` (`bridge.py:160-162`, `core.py:424-427` — 30 แถวล่าสุด), `codex_recent_tasks` (`bridge.py:225-228`, `codex_core.py:657`), `bridge_context_status`/`bridge_context_recent` (`bridge.py:69-76`). ข้อจำกัด: ถ้า caller ไม่มี ID ค้างอยู่และหลุด window 30 แถว การ recovery อาจไม่สมบูรณ์; ไม่มี bind tool แยก และ Codex ไม่มี `request_id` ฝั่ง caller ให้ replay — ห้าม invent ทั้งสองอย่าง.

## 4. ทางเลือก (ตัดสินใจโดย operator; ชื่อที่เสนอเป็น DRAFT ไม่ผ่านการอนุมัติ)

| ทางเลือก | เนื้อหา | ผลต่อ contract |
| --- | --- | --- |
| **ก (คำแนะนำ — แคบที่สุด)** | คง error เดิมทั้งหมดตาม SPEC §21.2 + เพิ่มเอกสาร manual recovery ที่อธิบายขั้นตอนใช้ API เดิม (section 3) ให้ operator ใช้เมื่อเจอกรณีนี้ | ไม่เปลี่ยน code/schema/tools; ลดความสับสนด้วยเอกสารปฏิบัติการ แต่ **ไม่ปิดช่อง ACK ถูกซ่อน** |
| ข | เพิ่ม outcome แบบ additive หลัง ACK สำเร็จเท่านั้น: `context_binding` ค่าใหม่ (ชื่อ DRAFT เช่น `binding_unresolved` หรือ `bind_error`) โดยคง output ของ backend ทั้งหมดรวม `pending_local_approval` | เปลี่ยน response contract → ต้องมี SPEC §14 amendment แยกก่อน; ต้องจำแนก known-no-write กับ uncertain commit |
| ค (ยัง DEFERRED) | auto retry/rebind/replay/cancel หรือ reconcile ด้วย backend call ใหม่จาก wrapper; durable intents | ขัดขอบเขต deferred ของ SPEC §21.1 — ไม่เสนอให้พิจารณาใน scope นี้ |

ขอบเขตทุกทางเลือก: ไม่เพิ่มการเปิดเผย exception string/path/SQL ใน result หรือ audit log; privacy rules ของ SPEC §19 คงเดิม. **เฉพาะทางเลือก ข** ต้องคง backend ACK เต็มรูปแบบพร้อม identifier ทุกตัวรวม `pending_local_approval`; ทางเลือก ก ยังคืน error และยังมีช่อง ACK ถูกซ่อนตาม section 3. ทุกทางเลือกห้าม retry/rebind/replay/cancel อัตโนมัติ; ห้ามเรียก backend เพิ่มเพื่อ reconcile จาก wrapper; กฎ replay แบบ same-key guarded ของ Hermes คงเดิม (`replayed_locally`, window 23 ชั่วโมง, capabilities check — `core.py:298-313`) และห้ามอ้าง exactly-once.

## Checkpoint (22 ตุลาคม 2026): operator เลือกทางเลือก ข

External review ของ packet นี้เป็น **APPROVE — merge-ready as draft** ที่ head `2730f224516eb32b2717e1293cec986e2a185941` (base `02868ab5eba3e7784b7725e83fdb2c526603d86a`). หลังจากนั้น operator เลือกทางเลือก ข ในแชตเมื่อ 22 ตุลาคม 2026 โดยมีข้อความ (verbatim):

> เห็นด้วยกับการเลือก **ข**

ไม่มีเวลา (hh:mm:ss) ในข้อความ จึงไม่สร้าง timestamp เพิ่มเติม (แนวทางเดียวกับ checkpoint ของ PR #68, #69 และ #73). การเลือกนี้เป็นการตัดสิน **ทิศทางเท่านั้น**: ไม่ใช่การอนุมัติชื่อ field (`binding_unresolved` ยังเป็นชื่อ DRAFT ตามตารางด้านบน), ข้อความ note, ข้อความ normative ฉบับสมบูรณ์, implementation, release หรือ deployment. ผลตามมาคือ SPEC §22 amendment แบบ PROPOSED ถูกเปิดเป็น stacked draft PR ที่ตัด branch ใหม่จาก head `2730f224…` และตั้ง base ชี้ที่ branch ที่ review แล้วของ PR #77 (แก้ [SPEC](SPEC.md#22-context-binding-unresolved-proposed) พร้อม checkpoint ในเอกสารนี้, ROADMAP และ RELEASE-STATUS; ประวัติข้อความเดิมคงเดิม). การ implement ยังต้องผ่าน section 14 review และ merge ของทั้ง PR #77 และ amendment PR ก่อนเสมอ; production v1.2.8 และ Dev pin `e7add7e` ไม่เปลี่ยน.

## 5. ขอบเขตที่ยัง DEFERRED (ไม่อยู่ใน packet นี้)

submit admission; crash ระหว่าง submit–bind; ACK loss; uncertain backend replay; durable intents; P2 prune (apply/delete); Local Hands; MCP Events — ทั้งหมดคงสถานะ deferred เดิมตาม SPEC §21.1 และ [ROADMAP](ROADMAP.md).

## 6. Acceptance matrix ที่เสนอ (PROPOSAL เท่านั้น — ยังไม่ implement, ยังไม่เขียน test)

- ใช้ barrier/Event แบบ deterministic ก่อน writer transaction (ห้าม hold lock รอ close commit ใน process เดียว; ห้ามใช้ sleep กำหนดลำดับ).
- Injected binding error แยกสองตำแหน่ง: pre-write (ก่อน `execute`) กับ after-commit (หลัง commit แล้วจึง raise) — แต่ละตำแหน่งต้องอ้าง row state จริง ไม่ใช่ outcome assertion เดียว.
- Fatal process/`KeyboardInterrupt` ต้องไม่ถูก swallow; closed outcome (`closed_rejected`/`bound`/ไม่มี field) คงเดิมทุกกรณีเดิม; no-context/precheck/partial-start exception คง error เดิม.
- นโยบาย catch: ระบุ exception class ใดบ้างเป็น **decision ของ operator** — ห้ามใช้ catch-all โดยไม่วิเคราะห์ (catch กว้างจะกลืน DB error และปิดโอกาส fail-closed).

## 7. Phase gates ที่เสนอ

1. Operator เลือกทางเลือก (ก/ข/อื่น) จาก packet นี้ →
2. SPEC §14 amendment แยก (reviewed/merged ก่อนเสมอ — เฉพาะถ้าเลือก ข) →
3. implementation PR ขนาดเล็ก →
4. scoped Dev acceptance →
5. release และ deployment เป็น gate แยกตาม [RELEASE-RUNBOOK-TH.md](RELEASE-RUNBOOK-TH.md).

หากเลือก ก งานถัดไปเป็นเอกสาร manual recovery เท่านั้น; ขั้น runtime/Dev/release/deployment ไม่จำเป็นสำหรับการแก้เอกสารนั้น. หากเลือก ข ให้ผ่านขั้น 2–5 ตามลำดับและขอบเขตที่อนุมัติ; การ merge PR ของ packet นี้ไม่ใช่การเลือกทางเลือกหรืออนุมัติ implementation.
