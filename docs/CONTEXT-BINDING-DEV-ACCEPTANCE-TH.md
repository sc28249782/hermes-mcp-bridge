# Context binding (SPEC §22) — scoped synthetic Dev acceptance

วันที่: 22 ตุลาคม 2026.
สถานะ: **scoped synthetic Dev acceptance performed; parent-observed evidence; ยังรอ external review; ยังไม่ released และยังไม่ deployed**.
ฐาน: PR #79 — review head `44f3bacc9ea76157d05ebcd2f110ce3b76b55f38` (external APPROVE), merge `71dcae67cbfa6f0b953ab8d81198d073d202ed2a` เป็น main. Candidate ที่ใช้คือ clean checkout ที่ merge commit นี้ ตรวจ byte-identical ด้วย `git status` ที่ว่างและ hash ของไฟล์ runtime.
เอกสารนี้ไม่อนุมาต release, deployment หรือ production acceptance. ไม่มี release ที่ได้รับมอบหมาย.

## Scope และ fixture honesty

Fixture เรียก `server()` และ `Bridge` และ `ContextRegistry` ของ candidate จริง แล้ว parent ใช้ Dev tunnel จริงเรียกผ่าน connector. Hermes ACK เป็น synthetic ผ่าน `httpx.MockTransport`; HTTP ไม่ออกนอกเครื่อง. Codex เป็น stub ที่คืน ACK เท่านั้น ไม่เรียก CLI จริง; Local Hands เป็น stub. State เป็น directory แยกของ fixture; hooks อยู่ใน fixture module นอก production code ทุกจุด. ไม่มี MCP tool เพิ่ม.

Hook เลือกด้วย label ของ `bridge_context_create` ตามตารางนี้ ทุก injection เป็น test-only interleave ไม่ใช่ natural race:

| Label | พฤติกรรม hook | ผลตาม contract |
| --- | --- | --- |
| `S22_NORMAL` | ไม่แทรก; bind จริง | `bound`, ไม่มี note |
| `S22_OP_PRE` | `OperationalError` ก่อน write | `binding_unresolved`, row ยัง unbound |
| `S22_OP_COMMIT` | commit ของ transaction จริงล้ม one-shot; connection ปิดโดยไม่ commit (rollback) | `binding_unresolved`, row ยัง unbound; SELECT precheck ไม่กระทบ |
| `S22_OP_POST` | bind จริง commit สำเร็จ แล้วค่อย raise | `binding_unresolved` แต่ row มี binding ค้างจริง; response ไม่ฟันธง persistence |
| `S22_CONTEXT_PRE` | `ContextError` ก่อน write | `binding_unresolved`, row ยัง unbound |
| `S22_CLOSED_AT_BIND` | hook ปิด context จริงหลัง backend ACK ก่อน bind | `closed_rejected` + note ค่าคงที่, row closed และ unbound |
| `S22_EXCLUDED` | `sqlite3.ProgrammingError` ข้อความค่าคงที่ | กระจายออกทั้ง request เป็น MCP error |

Fixture ไม่แตะ `version_info`: `bridge_version` รายงาน stamp รับมาจาก release เดิม (`1.2.8`/`v1.2.8`/`release`), `source_kind: git-worktree`, `source_revision` = `71dcae6…`, `revision_source: git` และ `config_schema_version: unknown` เพราะ fixture root ไม่มี `bridge-config.json` — บันทึกตามผลจริง ไม่แสดงเป็น release ใหม่. ไม่มี credentials ใน fixture. ไม่มี real backend/model task ถูกส่งเป็น acceptance stimulus; งาน orchestration ของ session นี้เป็น Hermes control jobs ปกติ ซึ่งแยกจาก acceptance stimuli.

## การเตรียมและ activation

Preflight: backup profile/config/state แบบ 0600 (dir 0700) ก่อนแก้อะไร; state tar เก็บหลัง writer หยุด (ไม่คัดลอก SQLite ขณะมี writer). Quiescence inventory ใช้ metadata เท่านั้น: codex jobs 0, opencode jobs 3 (completed ทั้งหมด), ไม่มี worker process — ผ่านก่อนหยุด. หยุด Dev เดิมด้วย stop ที่ตรวจ argv และ start identity ก่อน TERM แบบ graceful. เริ่ม fixture ผ่าน profile Dev เดิมด้วย ephemeral `--mcp.command` override; ไม่แก้ profile YAML; auth เดิม, tunnel id เดิม, health port `8081`. Production ไม่ถูกแตะตลอดช่วงทำงาน.

Offline gates ผ่านก่อน activate: focused `tests/test_context_binding_unresolved` = 7/7 OK บน Python 3.14.7 ด้วย `-W error::ResourceWarning`; in-process smoke ตรวจ hook ครบทั้ง 7 labels ทั้งสอง backend พร้อม row-state; SDK stdio smoke `tools/list` = 27 (เป็น LOCAL capture ไม่ใช่ raw tunnel wire list).

## ผลการตรวจ (แยกชั้นหลักฐาน)

| ชั้นหลักฐาน | ขอบเขต | ผล |
| --- | --- | --- |
| Durable (snapshot หลังหยุด fixture ก่อนคัดลอก) | ตรวจซ้ำได้จาก DB | contexts 14 แถว = 2 closed (เฉพาะ `CLOSED_AT_BIND`) / 12 open; bound พอดี 4 = NORMAL และ OP_POST ของแต่ละ backend; อีก 10 unbound; runs 8 แถว ครบทุก request ID รวม plain; audit 24 records = 14 create + 2 close + 8 hermes submit — ไม่มี codex record |
| Parent live observation (receipt เก็บแบบ private 0600; ติดป้าย parent observations ไม่ใช่ raw signed wire capture) | ผ่าน Dev connector จริง | counters สุดท้าย hermes POST 8 / codex submits 8; replay รู้จัก ID แล้ว `replayed_locally: true` และไม่มี POST ใหม่; closed precheck ทั้งสอง backend ได้ error เดิมโดยมี 0 call เพิ่ม; EXCLUDED ได้ MCP error `INVALID_ARGUMENT` พร้อมข้อความค่าคงที่; Codex `pending_local_approval` + approval payload ครบ (STUB ONLY — ไม่มี approve และไม่มี process spawn) |
| Offline automation | maintainer ในเครื่อง; ไม่ใช่ transport evidence | focused tests 7/7 บน 3.14.7; in-process smoke ครบ; SDK stdio 27 tools |

ขอบเขต live matrix ที่บันทึกตรงกับที่ทดสอบจริง: live EXCLUDED คือเฉพาะ `ProgrammingError`; excluded class อื่นเป็น unit-test evidence เท่านั้น. live `ContextError` คือเฉพาะกรณี PRE; failure ทั้งสองประเภทครบ 3 ระยะ (before/at commit/after commit) เป็น unit evidence ไม่ใช่ live claim. การเทียบ ACK ลึกทุกค่าเป็น unit test; parent live เห็น known fields/IDs/notes/pending payload เท่านั้น ไม่ใช่ raw wire deep comparison. ไม่มี claim uncertain replay และไม่มี heal claim สำหรับกรณี OP_POST bind ซ้ำ (hook ไม่ถูก exercise ซ้ำ). Precheck ที่ทดสอบ live คือ closed เท่านั้น จึงไม่อ้าง invalid/unknown precheck เป็น live.

## ข้อจำกัดของหลักฐาน

- Counter ฝั่ง codex (8) พึ่ง parent observation เท่านั้น; stub เก็บ counter ใน memory ไม่เขียน DB หรือ audit.
- รายละเอียด response เป็น parent observation ก่อน restore; ไม่มีการ reconstruct ย้อนหลังเป็น raw proof.
- Fixture นี้เป็น mock-backend evidence; ไม่ใช่ real-backend, native หรือ production acceptance.
- Timestamp ในวินาทีเดียวกันไม่พิสูจน์ลำดับเหตุการณ์.

## Production discipline และ restoration checkpoint

Production runtime และ process chain ไม่ถูก restart และ deployment ไม่ถูกแตะ (ตรวจต่อเนื่องด้วย process identity ฝั่ง parent และเครื่อง). Record นี้ไม่อ้างว่า production state ทั้งหมด byte-identical หรือไม่มีการเขียนใด: control jobs ของ session ลงทะเบียนและบันทึก audit ตามระบบ production ปกติ. Restore: หยุด fixture ด้วย stop ที่ตรวจ argv, เก็บ snapshot fixture 0600 ก่อน, แล้วเริ่ม Dev เดิมด้วย command/profile/pin เดิม (ไม่แก้ YAML). ผลที่ตรวจแล้ว: Dev identity กลับ `1.2.4`/`e7add7e`/config schema 1/discovery 27 (parent live และ offline CLI); source/config/profile/state ตรง backup แบบ byte-identical. Delta เชิงปฏิบัติที่บันทึกตรง: Dev ตัวใหม่รันเป็น background worker ของ agent แทน foreground terminal เดิม; ไม่มี systemd service ติดตั้ง. Raw log รายละเอียดเป็นข้อมูล private; ข้อมูลสาธารณะรวมเฉพาะค่า counter โดยไม่มี path/PID.

## สิ่งที่ checkpoint นี้ไม่ปิด

- Release และ deployment ของ candidate ยังเป็นขั้นแยก; ไม่มี release ที่ได้รับมอบหมาย.
- Real-backend acceptance, native acceptance และ production acceptance ไม่ถูกอ้าง; uncertain replay ไม่ได้ถูกพิสูจน์ผ่าน transport.
- Submit admission และ crash ระหว่าง submit→bind ยังเป็น gap; excluded class ที่ไม่ได้ทดสอบ live ยังคงเป็น unit evidence เท่านั้น.
- P2 apply/delete, Local Hands และ MCP Events ยัง deferred.
- Record นี้รอ external review; ไม่ประกาศผล PASS หรือ approval ก่อน operator ยืนยัน.
