# Context lifecycle (SPEC §21) — scoped synthetic Dev acceptance

วันที่: 21 ตุลาคม 2026.
สถานะ: **scoped synthetic Dev acceptance performed; mock-backend evidence; ยังไม่ released และยังไม่ deployed; ยังรอ external review**.
ฐาน: PR #70 merge `227f2ad1f43ff64c6c4866595c9ea705fd7977b3` (review head `07bfe824ab32f9aa223cf0ed9b15e41c7ac1ef47`).
เอกสารนี้ไม่อนุมัติ release, deployment หรือ production acceptance. ไม่มี release ที่ได้รับมอบหมาย.

## Scope และ fixture honesty

Fixture เรียก `server()` และ `Bridge` และ `ContextRegistry` ของ candidate จริงบน Dev tunnel จริง. Wrapper ทุกจุดที่ parent ตรวจคือ production code path. Hermes ACK เป็น synthetic ผ่าน mock transport; HTTP ไม่ออกนอกเครื่อง. Codex เป็น stub ที่คืน ACK เท่านั้น; Local Hands เป็น stub. State เป็นชั่วคราว; state reset เมื่อเริ่ม fixture process ใหม่; counters อยู่ใน memory.

Hook ทดสอบอยู่ใน fixture code เท่านั้น ไม่แตะ runtime:

- label `P1_LIFECYCLE_CLOSE_AT_BIND` — close commit หลัง backend ACK ก่อน bind จริง; เป็น interleave จาก test hook ไม่ใช่ natural network race.
- label `P1_LIFECYCLE_DB_BIND_ERROR` — DB error ที่ bind boundary; error กระจายออกโดยไม่ถูกแปลง.

Fixture ไม่เพิ่ม MCP tools. SDK `tools/list` = 27 tools. `bridge_version` รายงาน `1.2.7`/`v1.2.7`/`release`/`git-worktree`/`227f2ad`/`git` — stamp รับมาจาก release เดิม ไม่ใช่ release ใหม่. Root config schema เป็น `unknown` เพราะ fixture root ไม่มี `bridge-config.json`; บันทึกตามผลจริง. ไม่มี credentials หรือ keys ใน fixture. ไม่มี model/backend task จริง.

## การเตรียมและ activation

Preflight เก็บ backup state/config/profile แบบ 0600 ก่อนแก้อะไร. Preflight ตรวจงานที่ไม่ terminal ด้วย metadata เท่านั้น. Offline checks ผ่านก่อน activate: in-process smoke ครบ scenario, SDK stdio (`tools/list` = 27), focused lifecycle tests 21/21 บน Python 3.14.7.

หยุด Dev เดิมด้วย process stop ที่ตรวจ argv ก่อน. เริ่ม fixture ผ่าน profile Dev เดิมพร้อม ephemeral `--mcp.command` override. ไม่แก้ profile YAML. Health อยู่ที่ port `8081`. Production ไม่ถูกแตะตลอดช่วงทำงาน.

## ผลการตรวจ (แยกชั้นหลักฐาน)

| ชั้นหลักฐาน | ขอบเขต | ผล |
| --- | --- | --- |
| Durable (rows/audit ของ fixture state) | ตรวจซ้ำได้จาก DB | runs 4 แถว ครบ 4 request ID (`p1l-hermes-bound-01`, `p1l-hermes-close-bind-01`, `p1l-hermes-plain-01`, `p1l-hermes-db-error-01`); contexts 5 แถว: bound, closed + `hermes_run_id` NULL, codex bound, codex closed + `codex_job_id` NULL, open ไม่มี binding; audit 12 records (5 create, 3 close, 4 hermes submit) |
| Parent live observation | ผ่าน Dev connector จริง; raw response ไม่ถูก persist | identity ตรง `bridge_version`; counters ก่อน restore: hermes 4 / codex 4; response payload: `replayed_locally`, `pending_local_approval` ครบ, ข้อความ DB-error |
| Offline smoke | maintainer automation ในเครื่อง; ไม่ใช่ transport evidence | in-process scenarios ครบ; SDK stdio 27 tools; focused tests 21/21 |

Parent ตรวจ scenario เหล่านี้ผ่าน connector จริง:

- Hermes: bound, replay รู้จัก ID แล้วไม่ส่งซ้ำ, close, double-close, precheck closed/empty/invalid/unknown แบบ 0 backend calls, close-at-bind ได้ `closed_rejected` พร้อม note คงที่, ไม่ใส่ context ได้ response ไม่มี field, DB error กระจายออก.
- Codex: bound คง `pending_local_approval` payload, close-at-bind, ไม่ใส่ context, precheck 0 calls, DB error กระจายออก.

การข้ามชั้นหลักฐานเป็นสิ่งต้องหลีกเลี่ยง ตามข้อจำกัดถัดไป.

## ข้อจำกัดของหลักฐาน

- การที่ audit ไม่มี record ไม่พิสูจน์เองว่าแต่ละ invalid request ถูกกระทำ.
- Timestamp ในวินาทีเดียวกันไม่พิสูจน์ลำดับเหตุการณ์.
- Counter ฝั่ง codex (4) พึ่ง parent observation เท่านั้น; fake Codex ไม่เขียน audit. DB rows สนับสนุนเฉพาะ codex bound/closed row states.
- ข้อความ response รายละเอียด (`replayed_locally`, approval payload, ข้อความ DB-error) เป็น parent observation ก่อน restore; ไม่มีการ reconstruct ย้อนหลังเป็น raw proof.
- Fixture นี้เป็น mock-backend evidence; ไม่ใช่ real-backend acceptance.

## Recovery และ restoration checkpoint

Parent เจอ Connection Error และมีคำสั่งหยุดระหว่างรอ followup; งาน phase ผ่านไปก่อนหน้านั้นครบตาม counter. ผู้ควบคุมเก็บ snapshot ของ fixture state แบบ 0600 ก่อนหยุด fixture. จากนั้นหยุด fixture ด้วย process stop ที่ตรวจ argv และคืน Dev profile default command.

ผลการ restore ที่ตรวจแล้ว:

- Dev identity กลับ `1.2.4`/`v1.2.4`/`e7add7e`/config schema 1/discovery 27 — ตรวจด้วย offline CLI และ parent live.
- State/config/profile ตรง backup แบบ byte-identical.
- Production คง `1.2.7`/`release-archive`/`07ec0069` — process และ health ต่อเนื่อง ไม่ถูกแตะ.

Record นี้ไม่อ้างสาเหตุของ Connection Error. Record นี้ไม่ใช้ความเหลื่อม clock ของ WSL เป็นสาเหตุของอาการใด.

## สิ่งที่ checkpoint นี้ไม่ปิด

- Release และ deployment ของ candidate ยังเป็นขั้นแยก; ไม่มี release ที่ได้รับมอบหมาย.
- Real-backend acceptance และ production acceptance ไม่ถูกอ้าง.
- Uncertain replay ไม่ได้ถูกพิสูจน์ผ่าน transport; คงอยู่ใน core tests ระดับ local.
- Submit admission และ crash ระหว่าง submit→bind ยังเป็น gap ตาม SPEC §21.
- Post-acceptance non-closed binding failures (ack/recovery gap) ยังเปิด ตาม SPEC §21.
- P2 apply/delete ยัง deferred.
- Acceptance record PR รอ external review; ไม่มี PASS PR ก่อน operator ยืนยัน.
