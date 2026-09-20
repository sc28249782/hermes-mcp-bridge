# Release status — v0.6.0

## ผ่านแล้วใน build environment

- Python syntax compilation
- Hermes regression tests 16 รายการ
- Codex policy/process/audit/recovery tests 14 รายการ
- MCP stdio discovery/integration 1 รายการ: พบ 18 tools
- tunnel script tests 2 รายการ
- รวม 33 tests ผ่านทั้งหมด

## Live acceptance ที่ผ่านบน WSL2

- `./bridge.sh doctor` และ `./bridge.sh codex-doctor`
- restart Secure MCP Tunnel และ discovery Hermes 10 + Codex 6 tools
- Codex CLI `0.155.1` กับ workspace allowlist `/mnt/e/Projects/OpenHDK-validation`

## Live acceptance ที่ผ่านสำหรับ v0.5.0 — 2026-09-20

- `bridge_diagnostics` ผ่าน Secure MCP Tunnel: Hermes auth verified, Codex CLI `0.155.1`, state mode `700` และ audit enabled
- Codex `read-only` job ใน `/mnt/e/Projects/OpenHDK-validation` จบสำเร็จโดยไม่แก้ไขไฟล์ และทำให้ `audit.jsonl` ถูกสร้าง
- Codex `workspace-write` job ผ่าน local terminal approval: สร้าง/ตรวจ/ลบไฟล์ทดสอบชื่อเฉพาะไฟล์เดียวและยืนยันว่าไม่มีไฟล์คงเหลือ
- สถานะของ write job แสดง `recovered_after_restart: true` ตาม semantics ที่ประกาศไว้ เพราะ terminal approval process เป็นผู้เริ่ม job แล้ว tunnel process อ่านสถานะต่อจาก persisted state
- Codex read-only cancellation job ถูกยกเลิกขณะรัน; สถานะสุดท้าย `cancelled` และไม่มีการแก้ไขไฟล์

## ยังต้องทำสำหรับ v0.6.0

- ตรวจ `codex_health` ว่าแสดง workspace policy และ approval TTL ตาม config
- ส่ง write job แล้วตรวจ approval context/expiry และ `bridge_audit_recent`
- ทดสอบ policy อย่างน้อยหนึ่งข้อใน workspace ที่ตั้งใจให้ถูกปฏิเสธ โดยไม่ลด allowlist/sandbox/local approval
