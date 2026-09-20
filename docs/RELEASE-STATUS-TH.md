# Release status — v0.5.0

## ผ่านแล้วใน build environment

- Python syntax compilation
- Hermes regression tests 16 รายการ
- Codex policy/process/audit/recovery tests 10 รายการ
- MCP stdio discovery/integration 1 รายการ: พบ 17 tools
- tunnel script tests 2 รายการ
- รวม 29 tests ผ่านทั้งหมด

## Live acceptance ที่ผ่านบน WSL2

- `./bridge.sh doctor` และ `./bridge.sh codex-doctor`
- restart Secure MCP Tunnel และ discovery Hermes 10 + Codex 6 tools
- Codex CLI `0.155.1` กับ workspace allowlist `/mnt/e/Projects/OpenHDK-validation`

## ยังต้องทำสำหรับ v0.5.0

- ตรวจ `bridge_diagnostics` ผ่าน Secure MCP Tunnel
- ตรวจ audit log หลัง read-only, workspace-write approval และ cancel
- ทดสอบ recovery marker หลัง restart bridge ระหว่าง job ที่ไม่มีผลกระทบต่อไฟล์
