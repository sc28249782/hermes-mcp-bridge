# Release status — v1.0.1

## v1.2.0 — functional acceptance passed, tag pending (22 กันยายน 2026)

- WSL2 live acceptance ผ่านทั้ง ext4 และ DrvFS: discovery 22 tools, strict resolver, secret/path/binary/symlink denial, audit redaction และ case-collision fail-closed.
- Critical fallback OFF/OFF/ON ผ่าน: เมื่อ Hermes ใช้ไม่ได้และ Codex binary หาย Local Hands health/list/read ยังคงใช้ได้; ไม่มี Hermes/Codex task ถูกส่งระหว่างทดสอบ.
- คืน production state แล้ว Local Hands เป็น `disabled`, workspaces ว่าง และ diagnostics ไม่มี `config_warnings`.

ก่อน release ต้องบันทึก release commit SHA, kernel/WSL/Windows versions และทำ signed tag กับ checksum ของ release archive ตาม runbook.

## v1.0.1 — released (21 กันยายน 2026)

- schema ของ `codex.approval_ttl_seconds` ตรงกับ runtime ที่ 60–86,400 วินาที พร้อม regression test ที่ขอบเขต 59/60
- เอกสารระบุข้อจำกัด watchdog: enforcement อัตโนมัติอยู่ใน persistent MCP server ไม่ใช่ process ของ local approval CLI
- regression suite 48/48, shellcheck และ WSL2 read-only live acceptance ผ่าน
- signed tag `v1.0.1` ถูก GitHub ตรวจเป็น `Verified` และ release archive ผ่าน `sha256sum -c`: `a20a07aaeb0baeb885c85223dab9eba61c8a0ce1be20bb83d0e422faaa45c9d3  hermes-mcp-bridge-v1.0.1.zip`

## v1.0.0 — released (21 กันยายน 2026)

- security review และ regression 48 tests ผ่าน; แก้ schema validation ให้สอดคล้อง audit/runtime policy
- RC2 WSL2 full acceptance ผ่านสำหรับ Hermes/Codex, idempotency, write approval, cancellation และ audit/recovery semantics
- `SHA256SUMS` เผยแพร่แล้ว: `04421690f877807975810dfeffb29ec6412d8313103409cfd5713300e32de793  hermes-mcp-bridge-v1.0.0.zip`
- signed tag `v1.0.0` ถูก GitHub ตรวจเป็น `Verified` และชี้ไปที่ commit `2b280b2d3a763f69afa417bc76bdca6b801553fc`

## v0.9.0 — build verification

- Python compilation, shell syntax และ regression suite 48 tests ผ่าน (`-W error::ResourceWarning`)
- MCP stdio discovery ยืนยัน 19 tools รวม `bridge_status`
- `bridge_status` ไม่เรียก Hermes HTTP หรือ Codex CLI upstream
- Config schema version 1 ปฏิเสธ known type ที่ผิดและรายงาน unknown key เป็น warning
- heartbeat และ `stale` label ผ่าน live acceptance บน WSL2; `approval_stale` มี regression coverage แต่ยังไม่ได้สร้าง upstream approval workflow จริง
- v0.9.1 แก้การอ่าน capability เป็น `run_approval_response`; v1.0.0 ตรวจพบ capability แล้ว แต่ upstream approval-event live acceptance ถูกเลื่อนไป v1.1.0 ตาม roadmap

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

## v0.8.0 — full live acceptance (2026-09-21)

- `bridge_diagnostics` และ `codex_health` ผ่าน Secure MCP Tunnel: Hermes authenticated, Codex CLI `0.155.1`, watchdog interval 15 วินาที และ watchdog กำลังทำงาน
- งาน read-only ที่เริ่ม `sleep 120` ถูกยกเลิกผ่าน MCP ขณะยังรันอยู่; `status`/`result` ปลายทางเป็น `cancelled` และ audit เป็น `submit → start → cancel`
- ไม่พบการแก้ไข workspace หรือ network access ระหว่าง test
- ตั้ง runtime policy ชั่วคราว 5 วินาทีแล้วปล่อยงาน `sleep 120` โดยไม่ poll: watchdog ยุติงานเป็น `timed_out` และ audit บันทึก `cancel(timed_out)`
- restart tunnel ระหว่างงาน `sleep 30` แล้ว reconnect หลังงานจบ: job ปลายทางเป็น `unknown_exit`, result รายงาน `recovered_after_restart: true`, audit เป็น `finish(unknown_exit)` พร้อม `exit_code: null`
- คืน runtime policy production เป็น 1,800 วินาทีแล้ว

## v0.8.0 — build verification

- lifecycle hardening, atomic concurrency reservation และ watchdog regression tests ผ่าน
- CI เพิ่ม shellcheck พร้อมคง `bash -n`
- full production acceptance บน WSL2 ผ่าน: cancellation, watchdog timeout และ `unknown_exit` recovery semantics

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
