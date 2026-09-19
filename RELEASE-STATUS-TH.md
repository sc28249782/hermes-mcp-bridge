# Release status — v0.4.0

## ผ่านแล้วใน build environment

- Python syntax compilation
- Hermes regression tests 16 รายการ
- Codex policy/process tests 7 รายการ
- MCP stdio discovery/integration 1 รายการ: พบ 16 tools
- tunnel script tests 2 รายการ
- รวม 26 tests ผ่านทั้งหมด และรันโดยยกระดับ `ResourceWarning` เป็น error

## ยังต้องทำบน WSL2 ของผู้ใช้ก่อนถือว่า live accepted

- `./bridge.sh doctor`
- `./bridge.sh codex-doctor`
- restart Secure MCP Tunnel
- ตรวจ discovery 16 tools จาก ChatGPT
- รัน Codex `read-only` จริงหนึ่งงาน
- รัน `workspace-write` แบบ reversible หลัง local approval หนึ่งงาน
- ทดสอบ cancel งาน Codex ที่กำลังรัน

ไฟล์ `LIVE-ACCEPTANCE-TH.md` เดิมเป็นหลักฐานของ Hermes tools 10 ตัวใน v0.3.2 ไม่ใช่หลักฐาน live acceptance ของ Codex tools ใหม่
