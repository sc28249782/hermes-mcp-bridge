# Project history

Hermes MCP Bridge เริ่มจากการออกแบบและทดสอบร่วมกันใน ChatGPT session นี้:

https://chatgpt.com/share/6aae9c83-db48-83ec-ba0c-4ab5e3b088a7

เป้าหมายเริ่มต้นคือเชื่อม ChatGPT กับ Hermes Agent ที่รันใน Ubuntu 24.04 บน WSL2 ผ่าน Secure MCP Tunnel โดยรักษา authentication, run ownership, idempotency และ local approval

ลำดับการพัฒนา:

- `v0.1.0`: Hermes Runs API bridge และ lifecycle พื้นฐาน
- `v0.2.x`: ปรับ installation, tunnel และคู่มือ upgrade
- `v0.3.x`: เพิ่ม model catalog/override และ usage summary/export รวม Hermes tools 10 ตัว
- `v0.3.2`: พิสูจน์ tools ทั้ง 10 ตัวผ่าน live acceptance
- `v0.4.0`: เพิ่ม permission-gated Codex CLI บน WSL2 อีก 6 tools รวมทั้งหมด 16 tools

Chat session ใช้เป็นบันทึกความเป็นมาและเหตุผลในการออกแบบ ส่วน source, issues, pull requests, tags และ releases ใน repository นี้เป็นหลักฐานโครงการที่ใช้พัฒนาต่อ
