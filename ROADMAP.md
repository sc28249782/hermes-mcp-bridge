# Roadmap

> แนวทางพัฒนา Hermes MCP Bridge หลัง v0.4.0  
> ไม่มีวันที่กำหนดตายตัว: แต่ละ milestone จะเริ่มเมื่อเงื่อนไข acceptance ของ milestone ก่อนหน้าผ่านแล้ว

## หลักการที่ไม่เปลี่ยน

- Bridge เป็น **local, user-controlled execution boundary** ไม่ใช่ remote shell ทั่วไป
- ไม่มี `danger-full-access`
- Codex เข้าถึงได้เฉพาะ workspace ที่ระบุไว้ล่วงหน้า
- งานที่แก้ไฟล์ต้องมี **local human approval** เสมอ
- ห้ามส่ง API key, prompt/output ที่ละเอียดอ่อน หรือ state runtime ขึ้น GitHub
- เพิ่มความสามารถต่อเมื่อมี test และเอกสารปฏิบัติการรองรับ

## Current — v0.4.0

- [x] Hermes MCP tools 10 ตัว: health, models, task lifecycle, recent tasks และ usage
- [x] Codex/WSL2 MCP tools 6 ตัว: health, submit, status, paginated result, cancel และ recent jobs
- [x] Workspace allowlist และ canonical-path/symlink-escape protection
- [x] จำกัด Codex sandbox เป็น `read-only` หรือ `workspace-write`
- [x] Local approval gate ผ่าน `codex-approve` / `codex-deny`
- [x] Automated validation 26 tests และ MCP discovery 16 tools
- [ ] Live acceptance บน WSL2 ของผู้ใช้

## v0.4.1 — Live acceptance and release hardening

เป้าหมาย: ยืนยันว่า v0.4.0 ใช้กับ WSL2, Hermes และ Secure MCP Tunnel จริงได้อย่างปลอดภัย

- [ ] รัน `./bridge.sh doctor` และ `./bridge.sh codex-doctor` บน WSL2
- [ ] ยืนยัน discovery ทั้ง 16 tools จาก ChatGPT ผ่าน Secure MCP Tunnel
- [ ] ทดสอบ Codex `read-only` หนึ่งงานใน allowed workspace
- [ ] ทดสอบ `workspace-write` แบบ reversible หนึ่งงาน พร้อม local approval
- [ ] ทดสอบ cancel งาน Codex ที่กำลังทำงาน
- [ ] บันทึกผลใน `LIVE-ACCEPTANCE-TH.md` พร้อมเวอร์ชัน Codex CLI, WSL2 และ tunnel-client
- [ ] แก้เฉพาะ defect ที่พบจาก acceptance และเผยแพร่ patch release

**Exit criteria:** ไม่มีการ bypass allowlist/approval, output และสถานะงานถูกอ่านได้จาก ChatGPT, และการยกเลิกทำงานตามที่คาด

## v0.5.0 — Operations and reliability

เป้าหมาย: ให้ใช้งาน bridge ระยะยาวและวิเคราะห์ปัญหาได้ โดยไม่ลดระดับสิทธิ์

- [ ] Structured local audit log สำหรับ submit, approve/deny, start, finish, timeout และ cancel
- [ ] Log rotation และ retention ที่ตั้งค่าได้ โดยไม่เก็บ secret
- [ ] Health/diagnostic report ที่ตรวจ Codex CLI, config permissions, tunnel profile และ workspace policy
- [ ] Recovery semantics ที่ชัดเจนหลัง WSL restart หรือ tunnel reconnect
- [ ] Job-state schema migration และ compatibility tests
- [ ] Systemd user-service hardening/documentation สำหรับการรัน tunnel
- [ ] เพิ่ม regression tests จากผล live acceptance

**Exit criteria:** ผู้ดูแลตรวจสอบ lifecycle ของงานย้อนหลังได้ และ restart/reconnect ไม่ทำให้สถานะหรือ approval สูญหายอย่างเงียบ ๆ

## v0.6.0 — Policy and workflow controls

เป้าหมาย: รองรับการใช้หลายโครงการโดยควบคุมความเสี่ยงเป็นราย workspace

- [ ] Policy ต่อ workspace: sandbox, timeout, prompt-size และ concurrency limits
- [ ] Approval TTL และการหมดอายุของ pending write jobs
- [ ] Approval context ที่แสดง workspace, requested task summary และผลกระทบที่คาดได้
- [ ] Optional command/category denylist สำหรับงานที่ไม่ควรผ่าน bridge
- [ ] Export audit record แบบ redacted สำหรับการตรวจสอบ
- [ ] Threat-model review และ security regression suite

**Exit criteria:** นโยบายและหลักฐานการอนุมัติชัดเจนพอสำหรับการใช้กับหลาย repository โดยยังคง human-in-the-loop

## Backlog — evaluate before commitment

รายการต่อไปนี้ยังไม่ใช่สัญญาว่าจะทำ ต้องออกแบบ threat model และทดสอบก่อน:

- Per-workspace Codex profiles และ reusable task templates
- Read-only repository inspection tools ที่มีผลสรุปเป็น structured data
- Metrics integration สำหรับ observability ภายใน เช่น Prometheus
- CI release automation: test, package integrity, SBOM และ signed artifacts
- Optional GitHub workflow integration โดยยังคงให้การแก้ไข local ต้องผ่าน approval
- Multi-user authorization model สำหรับเครื่องเดียวกัน

## Out of scope

- เปิด SSH shell หรือ arbitrary command execution ให้ ChatGPT
- Allowing unrestricted filesystem/network access
- เก็บหรือส่ง Hermes/OpenAI API keys ผ่าน MCP
- ให้ agent อนุมัติ write job ของตัวเอง
- ทำให้ Secure MCP Tunnel เป็น public inbound service

## How to contribute

ดู [CONTRIBUTING.md](CONTRIBUTING.md) และ [SECURITY.md](SECURITY.md) ก่อนเปิด issue หรือส่ง pull request. สำหรับการเปลี่ยน policy หรือ execution boundary ให้แนบ test และอธิบายผลกระทบด้านความปลอดภัยเสมอ.
