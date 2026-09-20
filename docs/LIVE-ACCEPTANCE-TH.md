# ผล Live Acceptance — v0.3.2

วันที่ 14 กันยายน 2026 ทดสอบผ่าน Secure MCP Tunnel ไปยัง Hermes API `127.0.0.1:8642` ที่มี Bearer authentication โดยไม่เปิดพอร์ตสู่ public network

ผ่านครบ 10 tools: health, model info/catalog, recent tasks, usage summary/export, submit, status, result และ cancel

- `usage_export` ตรวจว่าไม่มี prompt, output หรือ API key
- smoke run ตอบ `HERMES_CANCEL_TEST_OK` ผ่าน submit/status/result
- cancel semantic: run `run_8980a67a66a94135a46f8b9d87dc4389` รัน `sleep 60` แบบไม่มี file/network operation แล้วเปลี่ยน `stopping` เป็น `cancelled`

ข้อจำกัด: model catalog ของ Hermes Runs API ประกาศ virtual model `hermes-agent` เพียงรายการเดียว แม้ config ปัจจุบันใช้ `deepseek/deepseek-v4-flash-0731` กับ provider `nous`

## v0.5.0 — 20 กันยายน 2026

ผ่าน Secure MCP Tunnel ไปยัง bridge `/home/somchaip/hermes-mcp-bridge-v0.5.0`:

- discovery 17 tools: Hermes 10, Codex 6 และ `bridge_diagnostics`
- `bridge_diagnostics`: Hermes authenticated, Codex CLI `0.155.1`, allowed workspace `/mnt/e/Projects/OpenHDK-validation`, state mode `700`, audit enabled
- Codex read-only: `git status --short` สำเร็จโดยไม่มีการแก้ไขไฟล์ และ `state/audit.jsonl` ถูกสร้าง
- Codex workspace-write: ผู้ใช้ตรวจ prompt และพิมพ์ `APPROVE` ใน WSL terminal; job สร้าง/ตรวจ/ลบ `.hermes-mcp-bridge-v050-acceptance.txt` สำเร็จและยืนยันว่าไฟล์หายไป
- Codex cancel: job read-only ที่รอ 60 วินาทีถูก cancel ขณะรันและจบด้วย `cancelled`

หมายเหตุ: write job แสดง `recovered_after_restart: true` เพราะ terminal helper เริ่ม process แล้ว tunnel-backed bridge process อ่านสถานะต่อจาก SQLite; bridge ไม่ส่ง job ซ้ำและไม่อ้าง exit code ที่ไม่ได้สังเกตเอง

## v0.6.0 — 20 กันยายน 2026

ผ่าน Secure MCP Tunnel ไปยัง bridge `/home/somchaip/hermes-mcp-bridge-v0.6.0`:

- discovery 18 tools รวม `bridge_audit_recent`
- `codex_health` รายงาน policy ต่อ workspace และ approval TTL 3,600 วินาที
- read-only acceptance จบสำเร็จ; audit export แสดง lifecycle `submit`, `start`, `finish` แบบ redacted
- workspace-write job ที่ยังไม่อนุมัติคืน expiry/policy context; `codex_cancel_task` เปลี่ยนเป็น `denied` โดยไม่เริ่มงาน
- policy probe ที่ workspace `/mnt/e` ถูกปฏิเสธก่อนเริ่มด้วย allowlist guard

## v0.7.0 — 20 กันยายน 2026

ผ่าน Secure MCP Tunnel ไปยัง bridge `/home/somchaip/hermes-mcp-bridge-v0.7.0`:

- `bridge_diagnostics` ยืนยัน Hermes authenticated, Codex CLI `0.155.1`, workspace policy และ audit state mode `700`
- `codex_health` แสดง allowlist ต่อ workspace: `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`; reasoning effort `low`, `medium`, `high`
- งาน `read-only` ที่ไม่ส่ง override จบด้วย `V070_DEFAULT_OK` และ exit code `0`
- งาน `read-only` ที่ร้องขอ `model: gpt-5.6-sol` และ `reasoning_effort: high` จบด้วย `V070_MODEL_POLICY_OK` และ exit code `0`
- `bridge_audit_recent` แสดง lifecycle `submit → start → finish` พร้อม model/effort ที่ร้องขอ โดยไม่มี prompt, output หรือ credential

ระหว่าง acceptance พบว่า display name `GPT-5.6 Sol` ใช้เป็น model ID ไม่ได้และถูก Codex CLI ปฏิเสธ; แก้เป็น `gpt-5.6-sol` แล้วผ่าน จึงต้องใช้ model ID จริงใน `allowed_models` เสมอ

## v0.8.0 — รอ live acceptance

Build verification ผ่าน 44 tests แล้ว แต่ต้องทดสอบบน WSL2 เพิ่มสำหรับ watchdog timeout, SIGTERM/SIGKILL cancellation และ `unknown_exit` หลัง recovery ก่อนปิด release นี้.
