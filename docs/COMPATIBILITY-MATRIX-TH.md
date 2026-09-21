# Compatibility matrix — v1.0.0 baseline

| Component | Baseline ที่ยืนยัน | วิธีตรวจ | หมายเหตุ |
| --- | --- | --- | --- |
| Python | 3.12 | `python3 --version` | รัน regression ด้วย `-W error::ResourceWarning` |
| Hermes API | loopback `127.0.0.1:8642` | `./bridge.sh doctor` | ต้องตอบ unauthenticated 401 และ authenticated 2xx |
| Hermes Runs | submit/status/stop + durable idempotency | `hermes_health` | run approval เป็น optional capability |
| Codex CLI | 0.155.1 | `./bridge.sh codex-doctor` | ต้องใช้ workspace policy ที่จำกัดไว้ |
| WSL2 | Ubuntu 24.04 | `uname -a` | ทดสอบผ่าน Secure MCP Tunnel |
| tunnel-client | official profile `hermes-wsl` | `bash tunnel.sh status` | profile ต้องชี้ `bridge.sh` ของ release เดียวกัน |
| ChatGPT MCP | 19 tools | discovery ในแชทใหม่ | Hermes 10 + Codex 6 + operations 3 |

การเปลี่ยน component นอก matrix ไม่ใช่การรับรองว่าไม่รองรับ แต่ต้องทำ acceptance checklist ซ้ำก่อนใช้งาน production.
