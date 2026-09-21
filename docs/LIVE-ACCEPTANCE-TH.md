# ผล Live Acceptance — v0.3.2

## v0.9.0 — partial live acceptance (21 กันยายน 2026)

- `bridge_status` ผ่าน Secure MCP Tunnel โดยรายงาน `upstream_checked: false` สำหรับทั้ง Hermes และ Codex; schema migration ไม่มี `config_warnings` และ discovery พบ 19 tools.
- ตั้ง `hermes.stale_run_seconds` ชั่วคราวเป็น 1 วินาที แล้วส่ง Hermes task read-only ที่รอ 30 วินาที: ระหว่างรัน status มี `age_seconds: 10` และ `stale: true`.
- Bridge ไม่ส่ง stop; Hermes จบเองเป็น `completed` พร้อมยืนยันว่าไม่แตะไฟล์/เครือข่าย. Audit เก็บ submit แบบ redacted เท่านั้น.

`approval_stale` มี regression coverage แต่ยังไม่ได้สร้าง Hermes approval workflow จริงในการ acceptance เพื่อหลีกเลี่ยงผลกระทบจาก upstream approval; คืน threshold production ก่อนใช้งานต่อ.

ตรวจ capability ต่อมาแล้วพบ `run_approval: null` จาก Hermes API profile ปัจจุบัน จึงไม่สามารถสร้าง `waiting_for_approval` เพื่อทดสอบ live ได้อย่างปลอดภัย ไม่ใช่ข้อขัดข้องของ bridge. การทดสอบนี้จะกลับมาทำเมื่อ Hermes profile ประกาศ run approval.

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

## v0.8.0 — full live acceptance (21 กันยายน 2026)

ผ่าน Secure MCP Tunnel ไปยัง bridge `/home/somchaip/hermes-mcp-bridge-v0.8.0`:

- `bridge_diagnostics` และ `codex_health` ยืนยัน Hermes authenticated, Codex CLI `0.155.1`, workspace allowlist, model/effort allowlist และ watchdog ทำงานอยู่ทุก 15 วินาที
- งาน `read-only` ที่ตั้งใจรอ 120 วินาทีเริ่มทำงานจริง (Codex เรียก `sleep 120`) แล้ว `codex_cancel_task` ยุติงานเป็น `cancelled`
- `codex_task_status` และ `codex_task_result` ยืนยันสถานะปลายทาง `cancelled`; audit แสดง `submit → start → cancel` แบบ redacted และไม่มีการแก้ไขไฟล์หรือเรียกเครือข่าย
- ลด `max_runtime_seconds` ชั่วคราวเหลือ 5 วินาทีแล้วส่งงานที่รอ 120 วินาทีโดยไม่ poll; watchdog ยุติงานเองเป็น `timed_out` และ audit บันทึก `cancel` outcome เดียวกัน
- คืน runtime policy เป็น 1,800 วินาที, restart tunnel ระหว่างงาน read-only `sleep 30`, แล้วเชื่อมต่อใหม่หลังงานจบ: status เป็น `unknown_exit`, result มี `recovered_after_restart: true` และ audit บันทึก `finish` outcome `unknown_exit` พร้อม `exit_code: null`

ทั้ง timeout watchdog และ restart recovery ผ่านแล้ว; คืน policy production เป็น `max_runtime_seconds: 1800` ก่อนจบ acceptance.
