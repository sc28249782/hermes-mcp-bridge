# Release status — v0.8.0

## ผ่านแล้วใน build environment

- Python syntax compilation
- Hermes regression tests 16 รายการ
- Codex policy/process/audit/recovery/model-policy/lifecycle tests 24 รายการ
- MCP stdio discovery/integration 1 รายการ: พบ 18 tools
- tunnel script tests 2 รายการ
- รวม 44 tests ผ่านทั้งหมด (`-W error::ResourceWarning`)

## Live acceptance ที่ผ่านบน WSL2

- `./bridge.sh doctor` และ `./bridge.sh codex-doctor`
- restart Secure MCP Tunnel และ discovery Hermes 10 + Codex 6 tools
- Codex CLI `0.155.1` กับ workspace allowlist `/mnt/e/Projects/OpenHDK-validation`

## v0.8.0 — partial live acceptance (2026-09-21)

- `bridge_diagnostics` และ `codex_health` ผ่าน Secure MCP Tunnel: Hermes authenticated, Codex CLI `0.155.1`, watchdog interval 15 วินาที และ watchdog กำลังทำงาน
- งาน read-only ที่เริ่ม `sleep 120` ถูกยกเลิกผ่าน MCP ขณะยังรันอยู่; `status`/`result` ปลายทางเป็น `cancelled` และ audit เป็น `submit → start → cancel`
- ไม่พบการแก้ไข workspace หรือ network access ระหว่าง test
- คงเหลือเฉพาะ full live scenarios ที่ต้องมี maintenance window: ลด runtime policy ชั่วคราวเพื่อพิสูจน์ watchdog timeout และ restart recovery เพื่อพิสูจน์ `unknown_exit`

## v0.8.0 — build verification

- lifecycle hardening, atomic concurrency reservation และ watchdog regression tests ผ่าน
- CI เพิ่ม shellcheck พร้อมคง `bash -n`
- cancellation live acceptance ผ่านแล้ว; ยังต้องทำ watchdog timeout และ `unknown_exit` recovery semantics ก่อนประกาศ v0.8.0 ว่าผ่าน full production acceptance

## v0.7.0 — build verification

- `codex_submit_task` รองรับ optional `model` และ `reasoning_effort` โดยไม่เพิ่ม MCP tool ใหม่ (discovery ยังคง 18 tools)
- policy test ยืนยันการปฏิเสธ model/effort นอก allowlist ก่อนเริ่มงาน และตรวจ argv ที่ส่ง override ที่อนุญาต

## Live acceptance ที่ผ่านสำหรับ v0.7.0 — 2026-09-20

- bridge `/home/somchaip/hermes-mcp-bridge-v0.7.0` ทำงานผ่าน Secure MCP Tunnel; Hermes authentication และ Codex health ผ่าน
- `codex_health` ยืนยัน policy model IDs `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` และ effort `low/medium/high`
- งาน default `read-only` ตอบ `V070_DEFAULT_OK`; งาน override `gpt-5.6-sol` + `high` ตอบ `V070_MODEL_POLICY_OK`; ทั้งคู่ exit code `0` และไม่ต้อง local write approval
- audit export เก็บ model/effort และ lifecycle แบบ redacted ตามนโยบาย
- display name `GPT-5.6 Sol` ถูกปฏิเสธ จึงยืนยันว่าค่า allowlist ต้องเป็น Codex model ID จริง ไม่ใช่ชื่อที่แสดงใน UI

## Live acceptance ที่ผ่านสำหรับ v0.5.0 — 2026-09-20

- `bridge_diagnostics` ผ่าน Secure MCP Tunnel: Hermes auth verified, Codex CLI `0.155.1`, state mode `700` และ audit enabled
- Codex `read-only` job ใน `/mnt/e/Projects/OpenHDK-validation` จบสำเร็จโดยไม่แก้ไขไฟล์ และทำให้ `audit.jsonl` ถูกสร้าง
- Codex `workspace-write` job ผ่าน local terminal approval: สร้าง/ตรวจ/ลบไฟล์ทดสอบชื่อเฉพาะไฟล์เดียวและยืนยันว่าไม่มีไฟล์คงเหลือ
- สถานะของ write job แสดง `recovered_after_restart: true` ตาม semantics ที่ประกาศไว้ เพราะ terminal approval process เป็นผู้เริ่ม job แล้ว tunnel process อ่านสถานะต่อจาก persisted state
- Codex read-only cancellation job ถูกยกเลิกขณะรัน; สถานะสุดท้าย `cancelled` และไม่มีการแก้ไขไฟล์

## Live acceptance ที่ผ่านสำหรับ v0.6.0 — 2026-09-20

- discovery 18 tools รวม `bridge_audit_recent`
- `codex_health` แสดง workspace policy ของ `/mnt/e/Projects/OpenHDK-validation`: modes, prompt/runtime limit, concurrency 1 และ approval TTL 3,600 วินาที
- read-only job จบสำเร็จ; `bridge_audit_recent` แสดง `submit → start → finish` โดยมี workspace/policy root/prompt length เท่านั้น ไม่มี prompt, output หรือ credential
- write job คืน `pending_local_approval` พร้อม `expires_at` และ policy root; cancel job ที่ยัง pending เปลี่ยนเป็น `denied` โดยไม่เริ่ม process
- probe workspace `/mnt/e` ถูกปฏิเสธด้วย `workspace is outside allowed_workspaces`
