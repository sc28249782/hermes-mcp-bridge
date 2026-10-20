# Context soft-cap / prune — P1 scope approved, implementation pending

วันที่: 20 ตุลาคม 2026.
สถานะ: **operator อนุมัติ P1 scope แล้วเมื่อ 20 ตุลาคม 2026 เวลา 15:57:29 +07**.
PR #57 ผ่าน external review ที่ `a38d319` และ merge แล้วที่ `6c85432`. Operator ตอบ “ยืนยัน” ต่อคำขอ merge และอนุมัติ P1 ตามค่าที่เสนอ.
Contract สำหรับ implementation review อยู่ใน [SPEC §20](SPEC.md#20-context-p1--approved-scope-future-implementation-no-assigned-release).
Source baseline: `e24fa3eec00fd9d1f5d0e38561fb2d044346bc72`.
ยังไม่มี implementation, config ใหม่, release หรือ deployment จากข้อเสนอนี้.

## เป้าหมายและความหมายของ context

จัดการจำนวน metadata rows ใน `contexts.sqlite3` โดยคง explicit continuation ตาม SPEC §8.
Context registry เก็บ label, timestamps และ backend references; ไม่เก็บ prompt/output หรือ ChatGPT conversation history.
Soft-cap นี้ไม่ใช่ model token limit.
Prune ไม่ลด token history ของ ChatGPT/Hermes/OpenCode และไม่ใช่วิธีแก้ Connection interrupted ที่ได้รับการพิสูจน์.

| ประเด็น | Scope ที่เสนอ |
| --- | --- |
| Registry row growth | Warning และ bounded preview ของ metadata rows |
| ChatGPT chat length / session handoff | อยู่นอก bridge registry scope; ไม่อ้างว่าสั่ง prune จาก bridge ได้ |
| Native backend session history | ไม่ compact, summarize, reset หรือลบ |
| Job artifacts / audit / provider credentials | ไม่แตะ DB/log/files ของ backend หรือ audit retention |
| OpenCode context integration | ไม่เพิ่ม binding ใน registry รอบนี้ |
| Observation counters / annotations | แยก proposal ไม่รวมในงานนี้ |
| Hands / MCP Events | คง capability gates เดิม |

## Baseline ที่ตรวจแล้ว

- `contexts.py` มี create/status/recent/close และ Hermes/Codex bindings.
- `recent(limit)` ใช้ SQL LIMIT 1–100 (default 30); จำกัด response ไม่ใช่จำนวน stored rows.
- `close` ตั้ง closed/updated timestamps แต่ไม่ลบ row.
- ยังไม่มี soft-cap, retention, preview หรือ prune command.
- `bridge_status` ปัจจุบันส่ง contexts เพียง explicit_only; proposal fields ด้านล่างยังไม่มี.
- Baseline tests ใน `tests/test_contexts.py` มี 2 tests และผ่านบน Python 3.12.14.
- Synthetic probe ใน temporary state ยืนยันว่า recent(limit=2) คืน 2 จาก 3 rows และ close ยังเก็บ row ที่เรียก status ได้.
- การตรวจใช้ public source และ synthetic state เท่านั้น; ไม่อ่าน production config/state หรือส่ง backend task.

Precheck กับ binding UPDATE ใน baseline อยู่คนละ transaction.
Synthetic interleaving หลัง precheck ทำให้เขียน binding ลง row ที่ close แล้วได้.
นี่เป็นหลักฐานเฉพาะ registry mutation ไม่ใช่หลักฐานว่า production มี incident หรือ backend task ถูกส่งหลัง close จริง.
ต้อง review lifecycle concurrency ก่อนเปิด destructive prune.
ไม่แนบ production identifiers หรือรายละเอียดจาก state จริง.

## P1 ที่แนะนำ — warning + read-only preview

Operator อนุมัติเฉพาะ P1 warning + read-only preview ตาม scope นี้. SPEC §20 ต้องผ่าน review ก่อนเริ่ม implementation.
ค่าด้านล่างได้รับอนุมัติเป็นค่าเริ่มต้นของ P1 scope; ยังไม่ใช่ค่าที่ใช้งานอยู่หรือผล capacity benchmark.

| รายการ | ค่าเริ่มต้นที่อนุมัติสำหรับ P1 |
| --- | --- |
| Soft-cap | 1,000 stored rows; warning เมื่อ count ≥ cap |
| Validation | Integer 1–100,000; ไม่รับ boolean |
| Counting | อ่านไม่เกิน cap+1 rows เพื่อรายงาน lower bound และบอกเมื่อ count ถูก cap |
| ผลเมื่อถึง cap | Create ยังสำเร็จ; ไม่ปฏิเสธงาน ไม่ auto-close และไม่ evict |
| Preview age | Closed อย่างน้อย 30 วัน; ใช้ closed timestamp กับ UTC cutoff ที่จับครั้งเดียวต่อ preview |
| Preview batch | Default 100, maximum 1,000; deterministic order ตาม closed timestamp แล้ว context_id |
| Apply/delete | ไม่มีใน P1 |

เสนอ count/warning แบบ scalar metadata ใน `bridge_status` และ warning code คงที่ใน create response.
Count ที่อ่านไม่ได้ต้องแสดง unavailable ด้วย constant error; ห้ามแทนเป็น 0 หรืออ้างว่า registry ปกติ.
ชื่อ fields/config และ error mapping ต้องกำหนดใน SPEC ก่อน implementation.
ไม่ส่ง label, backend references, workspace paths หรือ row IDs ใน warning.

Preview เป็น local CLI แยก ไม่เพิ่ม MCP tool.
ชื่อ command และ config keys ยังเป็น proposal; ไม่ใช่คำสั่งที่รันได้ใน signed v1.2.6.
Preview เปิดเฉพาะ registry เดิมแบบ read-only; ห้ามเรียก constructor ที่สร้าง schema/chmod หรือ initialize backend runners.
หากไม่มี DB หรือ schema ไม่ตรง ให้หยุดด้วย constant error ไม่สร้าง DB ให้เอง.
ต้องทดสอบ read-only behavior รวม WAL/sidecar handling; ห้ามถือว่า read-only connection รับรองว่าไม่มี filesystem effect ทุกแบบ.

Preview เริ่มด้วย candidate predicate แบบ conservative:

- closed timestamp ถูกต้องและเก่ากว่า cutoff.
- Hermes run/session references ทั้งสองเป็น NULL.
- Codex workspace/job references ทั้งสองเป็น NULL.
- Open rows, bound rows และค่า timestamp ที่ยืนยันไม่ได้ถูก skip.
- อายุ row ไม่ใช่หลักฐานว่า backend task จบแล้ว; ไม่ใช้ upstream 404 เป็น terminal evidence.
- ไม่เรียก upstream API, native executable หรือ model.
- Default report เป็น bounded aggregate counts; ไม่แสดง labels/paths/IDs หรือเขียน plan file.
- ไม่มี UPDATE/DELETE, VACUUM, job cancellation หรือการเปลี่ยน native session.

Predicate นี้ตั้งใจไม่เสนอ cleanup สำหรับ bound contexts ใน P1.
Preview อาจรายงานไม่มี candidates แม้จำนวน rows สูง.
Warning ไม่ใช่ hard disk quota และไม่รับรองขนาด DB หรือ latency รวม.

## P2 — apply ยัง deferred

P2 ต้องมี scope/SPEC review แยกก่อน implementation.
อย่างน้อยต้องออกแบบ:

1. Linearization ของ create/close/bind/observe และ external task submission ให้ตรง SPEC §8.
2. วิธีไม่ให้เกิด lost acknowledgement หาก backend รับ task แล้วแต่ context binding เปลี่ยน.
3. Atomic eligibility recheck และ bounded transaction; preview ไม่ใช่ authorization หรือ snapshot ถาวร.
4. Operator local approval ของชุด rows ที่ชัดเจน พร้อม race/stale-plan handling.
5. Read-only unknown/active-state handling สำหรับ bound references หากจะขยาย predicate ในอนาคต.
6. Private backup/recovery และ audit ที่มีเฉพาะ action/count/result; ไม่มี labels/refs/content.
7. ข้อกำหนดว่า prune ไม่ลบ job ownership/recovery stores, logs หรือ native session history.

ยังไม่เลือกใช้ auto-prune, scheduler, TTL eviction, hard-cap rejection หรือ MCP apply/approval tool.
ไม่ถือ digest approval ของ Local Hands เป็น authorization ของ registry โดยอัตโนมัติ.

## Acceptance ก่อน P1 merge

- SPEC-first ตาม §14 สำหรับ config/response/CLI semantics; companion amendment ใน §20 ต้องผ่าน review ก่อน implementation. บันทึก scoping เดิมยังแยกจาก normative contract.
- Test ต่ำกว่า/เท่ากับ/เกิน cap; create ยังสำเร็จ และ count/error output ไม่มี sensitive fields.
- ตรวจ actual scan/batch bounds และ deterministic ordering.
- Preview บน missing/invalid DB, read-only filesystem และ WAL cases; ไม่ initialize backend หรือสร้าง schema.
- Candidate filtering ครบ open/closed, cutoff boundary, malformed timestamp และ references ทั้งสี่ fields.
- ตรวจว่า registry/backend DB contents ไม่เปลี่ยน และไม่เรียก provider/task/process API.
- Discovery 27/28/33, explicit continuation, ownership และ close semantics เดิมยังผ่าน.
- Full suites/CI บน Python 3.12 และ 3.14; synthetic local preview acceptance ตามขอบเขต.
- ก่อน P2 ต้องมี deterministic close/bind/submission interleavings; P1 preview ไม่อ้างว่าซ่อม race นี้แล้ว.

## Operator decision ที่ได้รับ

Operator ยืนยันเมื่อ 20 ตุลาคม 2026 เวลา 15:57:29 +07 ให้ merge PR #57 และอนุมัติ P1 ตามค่าที่เสนอ.
ขอบเขตคือ warning 1,000 rows, preview closed อย่างน้อย 30 วัน, batch default 100 และสูงสุด 1,000, predicate แบบ unbound และไม่มี apply/delete.
การอนุมัติ scope ยังไม่อนุมัติให้ลบ rows, เปลี่ยน production config, release หรือ deploy.
SPEC §20 ระบุ contract สำหรับ review ก่อน implementation; P2, model-context compaction และ observation work ยังแยกติดตาม.
ข้อเสนอทบทวนค่า 30 วันหลังใช้จริงเป็นคำแนะนำ ไม่ใช่ gate หรือ schedule ใหม่.
