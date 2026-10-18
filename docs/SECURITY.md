# Security policy

## Supported versions

เฉพาะ release ล่าสุดได้รับ security fixes

## Reporting a vulnerability

อย่าเปิดเผย API keys, credentials, local paths ที่อ่อนไหว หรือ exploit ที่ใช้งานได้จริงใน public issue กรุณาติดต่อผู้ดูแล repository ผ่านช่องทาง private security reporting ของ GitHub เมื่อเปิดใช้งาน

## Security boundaries

- Hermes API ต้อง bind ที่ `127.0.0.1` และใช้ bearer key
- Codex workspace จำกัดด้วย canonical allowlist
- ไม่รองรับ `danger-full-access`
- งาน `workspace-write` ต้องผ่าน local terminal approval
- agent ไม่มี MCP tool สำหรับอนุมัติตัวเอง
- ห้าม commit `bridge-config.json`, `.env`, `state/`, logs และ tunnel key
- Release production ต้องเผยแพร่ checksum และ signed tag ที่ตรวจสอบได้; private signing key อยู่กับ maintainer เท่านั้น

## OpenCode adapter (`opencode_health`)

`opencode_health` (รวมใน release candidate v1.2.4 แล้ว แต่ยังไม่เผยแพร่และยังไม่ติดตั้ง — release ล่าสุดที่เผยแพร่คือ v1.2.3) เป็น disabled by default: เมื่อไม่กำหนด section `opencode` หรือ `enabled` เป็น `false` ทุก health check fail closed โดยไม่ spawn process และไม่มีการเรียก network/model/auth. การเปิดใช้ต้องกำหนด `opencode.binary` เป็น absolute path (ไม่เกิน 4096 ตัวอักษร ไม่มี control characters ต้องเป็น regular executable file) พร้อม `version_timeout_seconds` (1-120) และ `max_output_bytes` (1024-1048576); ไม่มีการเปิดใช้อัตโนมัติ

ขอบเขตเป็น health เท่านั้น: ยังไม่มี task submission, sessions, events, cancellation หรือ permission integration. bridge ไม่เพิ่ม sandbox — executable ที่กำหนดรันด้วยสิทธิ์เต็มของ bridge process และอ่าน global configuration/credentials ได้ จึงเปิดใช้เฉพาะ binary ที่ตรวจแล้ว. runner ไม่ส่ง `--auto` และ `--standalone` เป็น exclusive in-process server ไม่ใช่ sandbox

Local Hands ยังเป็น roadmap ไม่ใช่ production capability ใน v1.0.1 ขอบเขตที่อนุมัติไว้สำหรับ implementation คือ workspace/capability allowlist, local digest-bound approval, protected paths/names, baseline no deletion และไม่มี model-relayed nonce เป็น authorization ห้ามนำ allow-by-default deny-list sandbox, read-anywhere policy, shell-bypass accepted gap หรือ dynamic MCP-to-MCP trust bypass มาใช้

Execution ที่อ้างว่า no-delete/no-unapproved-truncate ต้องมี kernel enforcement ที่ probe ได้จริง เช่น [Landlock](https://docs.kernel.org/userspace-api/landlock.html) หรือกลไกเทียบเท่า Landlock เริ่มใน Linux 5.13 และยังขึ้นกับ kernel configuration/boot/ABI จึงห้ามสรุปว่ารองรับเพียงเพราะเป็น WSL2 หรือดูเฉพาะเลข kernel หาก enforcement ที่ profile ต้องใช้ไม่มี ให้ปิด profile แบบ fail closed Exact `hands_write`/`hands_patch` ที่ผูก local approval และ digest เป็น operation แยกซึ่งแตะได้เฉพาะ target ที่อนุมัติ

รายละเอียด threat model และข้อจำกัดดู `HERMES-MCP-BRIDGE-TECHNICAL-ARCHITECTURE-TH.md`, `CODEX-WSL2-TH.md` และ `LOCAL-HANDS-ARCHITECTURE-TH.md`

`deny_prompt_patterns` ใน workspace policy เป็น guard ก่อนเริ่มงานเท่านั้น ผู้โจมตีอาจเปลี่ยนถ้อยคำเพื่อหลบ pattern ได้ จึงห้ามถือว่าเป็น command sandbox หรือ authorization boundary; allowlist, Codex sandbox และ local approval เป็น controls ที่บังคับใช้จริง.
