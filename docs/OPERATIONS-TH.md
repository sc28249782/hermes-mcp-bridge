# คู่มือปฏิบัติการ — v0.5.0

## ตรวจสุขภาพ

```bash
./bridge.sh doctor
./bridge.sh codex-doctor
./bridge.sh diagnostics
```

`diagnostics` เป็น read-only: ใช้ตรวจ API/auth ของ Hermes, Codex CLI, state directory mode และ audit log configuration เท่านั้น ไม่เริ่ม model turn หรือ Codex job

## Audit log

ไฟล์หลักคือ `state/audit.jsonl`; ไฟล์เก่าจะเป็น `audit.jsonl.1`, `.2` ตาม retention ที่กำหนดใน `bridge-config.json`

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
3. ถ้าได้ `recovered_after_restart: true` ให้ตรวจ `codex_task_result` และ workspace ก่อนดำเนินการต่อ
4. ถ้างานเป็น `workspace-write` ที่ค้าง `pending_local_approval` ให้ตรวจรายละเอียดแล้ว approve/deny ผ่าน terminal เท่านั้น
5. การ restart tunnel ไม่ได้หยุด Hermes หรือ Codex job ที่เริ่มไปแล้ว; ใช้ cancel tool หากต้องการหยุด
