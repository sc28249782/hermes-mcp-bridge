# Compatibility matrix — v1.2.4 release

This matrix records the released v1.2.4 compatibility baseline (same components as v1.2.3; v1.2.4 adds only the optional OpenCode health adapter row below). The WSL2 live-acceptance, independent-review, and signed-release gates passed before publication.

| Component | Release baseline | วิธีตรวจ | หมายเหตุ |
| --- | --- | --- | --- |
| Python | 3.12 | `.venv/bin/python --version` | รัน regression ด้วย `-W error::ResourceWarning` และต้องใช้ project interpreter |
| Hermes API | loopback `127.0.0.1:8642` | `./bridge.sh doctor` | ต้องตอบ unauthenticated 401 และ authenticated 2xx |
| Hermes Runs | submit/status/stop + durable idempotency | `hermes_health` | run approval เป็น optional capability |
| Codex CLI | 0.155.1 | `./bridge.sh codex-doctor` | workspace-write ต้องผ่าน local approval; worker หายแต่ child ยังทำงานต้องคง `running` พร้อม `supervision_lost` |
| WSL2 | Ubuntu 24.04 | `uname -a` | ทดสอบผ่าน Secure MCP Tunnel |
| tunnel-client | official profile `hermes-wsl` | `bash tunnel.sh status` | profile ต้องชี้ `bridge.sh` ของ instance เดียวกัน |
| ChatGPT MCP | canonical count in `TESTING.md` | discovery ในแชทใหม่ | v1.2.1 baseline plus read-only `bridge_version` |
| Version/provenance | local-only CLI/MCP parity | `./bridge.sh version` และ `bridge_version` | ต้องไม่เรียก Hermes, Codex, tunnel, GitHub หรือ network |
| OpenCode CLI (optional) | v2.0.32 (health-only, opt-in) | `opencode_health` | disabled by default; live acceptance ครอบคลุมเฉพาะ `--version` (18 ตุลาคม 2026); discovery 27 tools เมื่อปิด, 28 เมื่อเปิด |

การเปลี่ยน component นอก matrix ไม่ได้แปลว่าไม่รองรับ แต่ต้องทำ acceptance checklist ซ้ำก่อนใช้งาน production.

## OpenCode execution — unreleased extension

ส่วน execution ใช้ OpenCode CLI v2.0.32 บน Linux/WSL2 ผ่าน `run --standalone --format json`
พร้อม stdin prompt และ session ที่ bridge เป็นเจ้าของ ใช้ detached worker และ Linux `waitid(WNOWAIT)`
จึงไม่มี Windows-native acceptance ฟีเจอร์นี้ไม่อยู่ใน signed v1.2.4 และไม่อ้าง HTTP v1/v2 API,
ACP, MCP Events หรือ native permission replies เป็น surface ที่รองรับ
ดู [OPENCODE-TH.md](OPENCODE-TH.md) และผลตรวจใน [TESTING.md](TESTING.md)
