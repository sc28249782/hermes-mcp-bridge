# ผล Live Acceptance — v1.2.2 released (23 กันยายน 2026)

## v1.2.2 — Bridge version/provenance (23 กันยายน 2026)

- ทำบน Dev working copy ที่ commit `5fcac967bc69e82e546a710702454464e52b86be` ผ่าน Secure MCP Tunnel ของ `Hermes Local Bridge - Dev`; Production ไม่ถูกเปลี่ยนแปลง.
- `./bridge.sh version` และ MCP `bridge_version` ให้ identity ตรงกันทุก field: version `1.2.2`, release identifier `v1.2.2-candidate`, source kind `git-worktree`, revision `5fcac967bc69e82e546a710702454464e52b86be`, schema `1`, และ discovery contract `27` tools.
- ตั้ง Dev config ชั่วคราวให้ Hermes ชี้ `http://127.0.0.1:1` และ Codex binary เป็น path ที่ไม่มีอยู่, restart เฉพาะ Dev tunnel, แล้ว MCP `bridge_version` ยังตอบผล identity เดิมได้. ระหว่างทดสอบไม่เรียก Hermes/Codex task หรือ tool อื่น.
- response ไม่มี filesystem path, credential, prompt, output หรือ audit content. หลังทดสอบ restore config จาก backup แล้ว `cmp` ผ่านแบบ byte-for-byte. ต้องเริ่ม Dev tunnel ด้วย config ปกติก่อนใช้งานต่อ; การยืนยัน restart ปกติบันทึกเป็น recovery check แยกต่างหาก.
- signed tag `v1.2.2` ชี้ commit `f8f1d93930882dc3e669dab0a05b4bd5c1834bef`; `git verify-tag --verbose` ผ่านด้วย GPG EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- [GitHub Release v1.2.2](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.2) แนบ ZIP และ external `SHA256SUMS`; SHA-256 ZIP คือ `e9582153c57458e3ca73a4c169f46653662377b004c9c2ee552824c4ffce5dc5`.
- ดาวน์โหลด asset กลับจาก GitHub แล้ว `sha256sum -c SHA256SUMS` และ `unzip -t` ผ่านครบ.

## v1.2.0 — Local Hands read-only released (22 กันยายน 2026)

- ทดสอบ deployment `/home/somchaip/hermes-mcp-bridge-v1.2.0-rc` ผ่าน Secure MCP Tunnel; discovery พบ 22 tools (base 19 + Hands 3) และ `bridge_diagnostics` ไม่มี `config_warnings`.
- รอบ ext4: `hands_health` เป็น available; list แสดงเฉพาะไฟล์/ไดเรกทอรีที่อนุญาต, ซ่อน `.env` และ symlink `escape`; read `allowed.txt` และ `nested/allowed.txt` ได้ fixture ที่คาดไว้.
- รอบ DrvFS ที่ `/mnt/e` (mount รายงาน `9p`/DrvFS): ได้ผล read/list/deny และ audit-redaction แบบเดียวกับ ext4. ไดเรกทอรี Windows ที่เปิด case-sensitive และมีทั้ง `A.txt`/`a.txt` ถูก `hands_list` ปฏิเสธแบบ fail-closed.
- deny matrix ปฏิเสธ `.env`, `binary.txt`, `escape`, traversal, absolute path และ normalized path; audit ไม่บันทึก secret, fixture content, file name หรือ absolute fixture path.
- ทดสอบ critical fallback โดย Hermes หยุดและตั้ง `codex.binary` เป็น `/definitely-missing-codex`: Hermes/Codex health ใช้ไม่ได้ตามคาด ขณะที่ Hands health/list/read ยังทำงานได้; ไม่ได้ submit task ไปยัง Hermes หรือ Codex.
- คืน config และบริการแล้ว `./bridge.sh doctor`, `./bridge.sh codex-doctor` และ diagnostics ผ่าน; cleanup เสร็จและ production Local Hands กลับสู่ `disabled` โดย workspaces ว่าง.

หลักฐาน provenance: live acceptance ทำบน checkout ที่สะอาด `9d00431975a61dc7fd67b521180f4e8669d84479`; `uname -r` = `6.18.33.2-microsoft-standard-WSL2`; WSL `2.7.14.0` (kernel package `6.18.33.2-2`, WSLg `1.0.73.2`); Windows `10.0.26300.9539`.

- released เป็น signed tag `v1.2.0` ที่ commit `bd56bafd4fcefcfbdf26699ab281cc1a6798bfc9`; GPG verify ผ่านด้วย EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- GitHub Release แนบ `hermes-mcp-bridge-v1.2.0.zip` และ `SHA256SUMS`; SHA-256 ของ ZIP คือ `621db6718323fb0639c67a9eac677af23de31a4f0f6e4d09b413d05f82960d08`.
- download asset กลับจาก GitHub แล้ว `sha256sum -c SHA256SUMS` และ `unzip -t` ผ่านครบ.

## v1.0.1 — maintenance release acceptance (21 กันยายน 2026)

- เชื่อมผ่าน `Hermes Local Bridge` จาก deployment `/home/somchaip/hermes-mcp-bridge-v1.0.1` ได้สำเร็จ
- `bridge_status` ยืนยัน state mode `0700`, audit เปิดใช้งาน, ไม่มี `config_warnings` และ Codex watchdog ทำงานทุก 15 วินาที
- `hermes_health` ยืนยัน authentication ที่ `127.0.0.1:8642`; `codex_health` ยืนยัน Codex CLI `0.155.1`, workspace policy และ approval TTL 3,600 วินาที
- Codex job แบบ `read-only` ที่ห้ามแก้ไขไฟล์และห้ามใช้เครือข่ายจบด้วย exit code `0` และตอบ `V101_READ_ONLY_ACCEPTANCE_OK`; audit บันทึก lifecycle แบบ redacted
- signed tag `v1.0.1` ถูก GitHub ยืนยัน signature แล้ว; release archive ผ่าน `sha256sum -c` ด้วย SHA-256 `a20a07aaeb0baeb885c85223dab9eba61c8a0ce1be20bb83d0e422faaa45c9d3`

## v1.0.0 — release deployment health check (21 กันยายน 2026)

- เชื่อมผ่าน `Hermes Local Bridge` จาก deployment ที่ checkout signed tag `v1.0.0` ได้สำเร็จ
- `bridge_status` ยืนยัน state mode `0700`, watchdog ทำงานทุก 15 วินาที, audit เปิดใช้งาน และไม่มี `config_warnings`
- `hermes_health` ยืนยัน authentication ที่ `127.0.0.1:8642`, capabilities `run_submission`, `run_status`, `run_stop`, `run_approval_response` และ durable idempotency 86,400 วินาที
- `codex_health` ยืนยัน Codex CLI `0.155.1`, workspace policy `/mnt/e/Projects/OpenHDK-validation`, model allowlist `gpt-5.6-sol`/`gpt-5.6-terra`/`gpt-5.6-luna` และ reasoning `low`/`medium`/`high`
- tag `v1.0.0` ถูก GitHub ยืนยัน signature แล้ว; SHA-256 ของ archive คือ `04421690f877807975810dfeffb29ec6412d8313103409cfd5713300e32de793`

## v1.1.0 approval-event SSE POC — deferred (21 กันยายน 2026)

- `GET /v1/runs/{run_id}/events` ผ่าน authentication ด้วย `HTTP 200 text/event-stream`; event ทุกตัวมี `run_id` ที่ตรงกับ run ที่ subscribe.
- POC read-only เห็น `message.delta`, `reasoning.available` และ `run.completed`; POC terminal `true` เห็น `tool.started`, `tool.completed`, `message.interim` และ `run.completed`.
- stream มี message/output/reasoning payload ด้วย จึงไม่เหมาะให้ relay ผ่าน MCP; bridge ต้องไม่ทำ general output streaming.
- หลังตั้ง `approvals.mode: manual` และ restart Hermes, terminal `true` ยังจบทันทีโดยไม่มี approval event หรือ `request_id`.
- ข้อสรุป: SSE transport ใช้ได้ แต่ approval-event contract สำหรับ API profile ยังพิสูจน์ไม่ได้; deferred integration ตาม `ROADMAP.md` และไม่เพิ่ม approval MCP tool.

## v1.0.0-rc.2 — full acceptance (21 กันยายน 2026)

- `bridge_status` ยืนยัน local-only heartbeat, schema ไม่มี warning, discovery มี 19 tools และ Hermes/Codex health ผ่าน
- Hermes read-only ตอบ `V100RC2_HERMES_OK`; ส่ง request ID เดิมซ้ำแล้ว replay locally โดยไม่สร้าง run ซ้ำ
- Codex read-only ที่ `gpt-5.6-sol` + `low` จบ exit code `0` และตอบ `V100RC2_CODEX_OK`
- Codex workspace-write ผ่าน local terminal approval: สร้าง/ตรวจ/ลบ `.hermes-mcp-bridge-v100rc2-acceptance.txt` แล้วตรวจว่าไม่มีไฟล์เหลือ
- write job ถูกรายงาน `unknown_exit` เนื่องจาก bridge restart/recovery ระหว่าง process; JSONL output และ audit ยืนยัน create/verify/delete/verify ครบ จึงไม่เดา exit code เป็น `completed`
- Codex read-only cancellation ระหว่าง `sleep 120` จบเป็น `cancelled`

watchdog timeout และ `unknown_exit` recovery ได้ผ่าน WSL2 live acceptance แล้วใน v0.8.0 บน policy/runtime เดียวกัน. Hermes upstream approval-event integration เป็นงาน v1.1.0 แยกต่างหาก.

## v0.9.0 — partial live acceptance (21 กันยายน 2026)

- `bridge_status` ผ่าน Secure MCP Tunnel โดยรายงาน `upstream_checked: false` สำหรับทั้ง Hermes และ Codex; schema migration ไม่มี `config_warnings` และ discovery พบ 19 tools.
- ตั้ง `hermes.stale_run_seconds` ชั่วคราวเป็น 1 วินาที แล้วส่ง Hermes task read-only ที่รอ 30 วินาที: ระหว่างรัน status มี `age_seconds: 10` และ `stale: true`.
- Bridge ไม่ส่ง stop; Hermes จบเองเป็น `completed` พร้อมยืนยันว่าไม่แตะไฟล์/เครือข่าย. Audit เก็บ submit แบบ redacted เท่านั้น.

`approval_stale` มี regression coverage แต่ยังไม่ได้สร้าง Hermes approval workflow จริงในการ acceptance เพื่อหลีกเลี่ยงผลกระทบจาก upstream approval; คืน threshold production ก่อนใช้งานต่อ.

ข้อสรุปเดิมจาก `run_approval: null` ถูกแก้ใน v0.9.1: Hermes ใช้ capability canonical ชื่อ `run_approval_response`. v1.0.0 ตรวจพบ capability แล้ว แต่ upstream approval-event SSE acceptance เป็นงาน v1.1.0.

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
