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

รายละเอียด threat model และข้อจำกัดดู `HERMES-MCP-BRIDGE-TECHNICAL-ARCHITECTURE-TH.md` และ `CODEX-WSL2-TH.md`
