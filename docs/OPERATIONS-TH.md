# คู่มือปฏิบัติการ — v1.0.1

## ตรวจสุขภาพ

```bash
./bridge.sh doctor
./bridge.sh codex-doctor
./bridge.sh diagnostics
```

`diagnostics` เป็น read-only: ใช้ตรวจ API/auth ของ Hermes, Codex CLI, state directory mode และ audit log configuration เท่านั้น ไม่เริ่ม model turn หรือ Codex job

## Audit log

ไฟล์หลักคือ `state/audit.jsonl`; ไฟล์เก่าจะเป็น `audit.jsonl.1`, `.2` ตาม retention ที่กำหนดใน `bridge-config.json`

## Heartbeat และ Hermes stale labels

ใช้ `bridge_status` เพื่อตรวจว่า bridge/state/audit พร้อมใช้งานโดยไม่ยิง request ไป Hermes หรือ Codex. ใน `hermes_task_status`, `age_seconds` คืออายุของ local registration; เมื่อเกิน `hermes.stale_run_seconds` จะมี `stale: true`. งานที่ `waiting_for_approval` และเกิน `hermes.approval_stale_seconds` จะมี `approval_stale: true`. ทั้งสองค่าเป็น local warning เท่านั้น—bridge จะไม่ stop หรือ deny Hermes run เอง.

```json
"audit": {
  "enabled": true,
  "max_bytes": 1000000,
  "retention_files": 7
}
```

ไม่ควรตั้ง `enabled: false` นอกการแก้ปัญหาแบบชั่วคราว เพราะจะทำให้ไม่มีหลักฐาน lifecycle ของงานใหม่ ห้าม commit `state/` หรือ audit log เข้าสู่ GitHub

## Recovery หลัง restart

1. อย่าส่ง job เดิมซ้ำโดยเดาจากสถานะก่อน restart
2. เรียก `codex_recent_tasks` แล้วใช้ `codex_task_status` กับ job ที่เกี่ยวข้อง
3. ถ้าได้ `recovered_after_restart: true` ให้ตรวจ `codex_task_result` และ workspace ก่อนดำเนินการต่อ; หาก status เป็น `unknown_exit` ห้ามถือว่างานสำเร็จจนกว่าจะตรวจผลกระทบเอง
4. ถ้างานเป็น `workspace-write` ที่ค้าง `pending_local_approval` ให้ตรวจรายละเอียดแล้ว approve/deny ผ่าน terminal เท่านั้น
5. การ restart tunnel ไม่ได้หยุด Hermes หรือ Codex job ที่เริ่มไปแล้ว; ใช้ cancel tool หากต้องการหยุด

## Workspace policy และ approval expiry

ตรวจ policy ที่มีผลจริงผ่าน `codex_health` หรือ `./bridge.sh codex-doctor` ก่อนส่งงาน แต่ละ workspace กำหนด sandbox mode, prompt/runtime limit และ concurrency ของตัวเองได้

งาน `workspace-write` จะมีเวลาอนุมัติตาม `codex.approval_ttl_seconds` (ค่าเริ่มต้น 3,600 วินาที) เมื่อหมดอายุสถานะเปลี่ยนเป็น `expired`; ให้สร้าง job ใหม่และตรวจ prompt อีกครั้ง ห้ามพยายามเปลี่ยน state database ด้วยตนเอง

Codex watchdog ตาม `codex.watchdog_interval_seconds` (ค่าเริ่มต้น 15 วินาที) เป็น background thread ของ persistent MCP server process เท่านั้น จึงบังคับ runtime limit ได้แม้ไม่มีการ poll เฉพาะขณะที่ tunnel/bridge server ยังทำงานอยู่. การสั่ง `codex-approve` จาก CLI เป็นเพียง local approval helper และไม่ทำให้ watchdog คงอยู่; หาก server หยุดหลังเริ่ม job จะไม่มี background timeout enforcement จนกว่าจะเปิด server ใหม่ หรือมีผู้เรียก `codex_task_status` เพื่อให้ status-poll path ตรวจงาน. ระหว่าง cancellation หาก process ยังไม่จบ status จะยังเป็น `running` พร้อม `cancellation_pending: true` หรือ `timeout_enforcement_pending: true`; อย่าส่งงานใหม่จนกว่าจะได้ terminal status.

ใช้ `bridge_audit_recent` หรือ `./bridge.sh audit-recent` เพื่ออ่าน event ที่ redacted ล่าสุด การตั้ง deny prompt patterns เป็นเพียง guard ก่อนเริ่มงาน; workspace allowlist, Codex sandbox และ local approval ยังคงเป็นชั้นควบคุมหลัก

## Codex model และ reasoning effort

ก่อนส่ง override ให้เรียก `codex_health` และใช้เฉพาะ model ID/effort ที่แสดงใน `workspace_policies` ของ workspace นั้น หากไม่ส่ง `model` หรือ `reasoning_effort` Codex CLI จะใช้ค่า default local. การเลือก override ไม่ข้าม sandbox หรือ local approval สำหรับ `workspace-write`.

หาก Codex CLI ตอบว่า model ไม่รองรับ ให้แก้ `allowed_models` เป็น model ID จริงที่บัญชีใช้งานได้—not display name—แล้ว restart tunnel และตรวจ `codex_health` ใหม่.
