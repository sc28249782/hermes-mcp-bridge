# Roadmap

> แนวทางพัฒนา Hermes MCP Bridge จากรากฐานเดิมจนถึง production baseline  
> จุดเริ่มต้น: [ChatGPT conversation](https://chatgpt.com/share/6aae9c83-db48-83ec-ba0c-4ab5e3b088a7)  
> ไม่มีวันที่กำหนดตายตัว: เริ่ม milestone ถัดไปเมื่อ acceptance ของ milestone ก่อนหน้าผ่านแล้ว

## หลักการที่ไม่เปลี่ยน

- Bridge เป็น **local, user-controlled execution boundary** ไม่ใช่ remote shell ทั่วไป
- ไม่มี `danger-full-access`
- Codex เข้าถึงได้เฉพาะ workspace ที่ระบุไว้ล่วงหน้า
- งานที่แก้ไฟล์ต้องมี **local human approval** เสมอ
- ห้ามส่ง API key, prompt/output ที่ละเอียดอ่อน หรือ state runtime ขึ้น GitHub
- เพิ่มความสามารถต่อเมื่อมี test, เอกสารปฏิบัติการ และ acceptance criteria รองรับ

## เส้นทางที่ทำมาแล้ว

| Release | เป้าหมายเดิม | สถานะ |
|---|---|---|
| v0.1.1 | Operational hardening | เสร็จและรวมในรุ่นถัดมา |
| v0.2.0 | เลือก model/provider/options ราย task | เสร็จ |
| v0.2.1 | Hotfix การแทน tunnel profile ด้วย `--force` | เสร็จ |
| v0.3.0 | Usage summary/export โดยไม่เดาราคา | เสร็จ |
| v0.3.2 | Live acceptance ของ Hermes tools 10 ตัว | เสร็จ |
| v0.4.0 | Safe Codex/WSL2 operations โดยไม่เปลี่ยน schema/พฤติกรรม Hermes เดิม | Automated validation เสร็จ; รอ live acceptance |

## Current — v0.4.0

- [x] Hermes MCP tools 10 ตัว: health, model information/catalog, task lifecycle, recent tasks และ usage
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

## v0.5.0 — Workspaces, audit and reliability

เป้าหมาย: ต่อจากแนวคิดเดิม “workspaces/audit” ให้ใช้งาน bridge ระยะยาวและวิเคราะห์ปัญหาได้ โดยไม่ลดระดับสิทธิ์

- [ ] Structured local audit log สำหรับ submit, approve/deny, start, finish, timeout และ cancel
- [ ] Log rotation และ retention ที่ตั้งค่าได้ โดยไม่เก็บ secret
- [ ] Health/diagnostic report ที่ตรวจ Codex CLI, config permissions, tunnel profile และ workspace policy
- [ ] Recovery semantics ที่ชัดเจนหลัง WSL restart หรือ tunnel reconnect
- [ ] Job-state schema migration และ compatibility tests
- [ ] Systemd user-service hardening/documentation สำหรับการรัน tunnel
- [ ] เพิ่ม regression tests จากผล live acceptance

**Exit criteria:** ผู้ดูแลตรวจสอบ lifecycle ของงานย้อนหลังได้ และ restart/reconnect ไม่ทำให้สถานะหรือ approval สูญหายอย่างเงียบ ๆ

## v0.6.0 — Policy and workflow controls

เป้าหมาย: รองรับหลาย repository โดยควบคุมความเสี่ยงเป็นราย workspace และรักษา human-in-the-loop

- [ ] Policy ต่อ workspace: sandbox, timeout, prompt-size และ concurrency limits
- [ ] Approval TTL และการหมดอายุของ pending write jobs
- [ ] Approval context ที่แสดง workspace, requested task summary และผลกระทบที่คาดได้
- [ ] Optional command/category denylist สำหรับงานที่ไม่ควรผ่าน bridge
- [ ] Export audit record แบบ redacted สำหรับการตรวจสอบ
- [ ] Threat-model review และ security regression suite

**Exit criteria:** นโยบายและหลักฐานการอนุมัติชัดเจนพอสำหรับการใช้กับหลาย repository โดยยังคง human-in-the-loop

## v1.0.0 — Production baseline

เป้าหมายตาม roadmap เดิม: ยืนยันความเข้ากันได้ ความปลอดภัย และ end-to-end operation ก่อนถือเป็น baseline สำหรับใช้งานจริง

- [ ] Compatibility matrix ที่ระบุ Hermes, Codex CLI, Python, WSL2 และ tunnel-client ที่รองรับ
- [ ] End-to-end acceptance บน WSL2 ครอบคลุม Hermes และ Codex ทั้ง 16 tools
- [ ] Security review ของ execution boundary, state persistence และ approval flow
- [ ] Upgrade/migration verification จาก v0.3.2 และ v0.4.x
- [ ] Reproducible release process: tests, package integrity และ release notes
- [ ] Incident/runbook documentation สำหรับ tunnel outage, stale job และ local approval failure

**Exit criteria:** มี compatibility/security/E2E evidence ที่ทำซ้ำได้, ไม่มี known critical security issue, และคู่มือ operational ครบถ้วน

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
