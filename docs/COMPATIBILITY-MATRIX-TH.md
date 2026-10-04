# Compatibility matrix — v1.2.3 release

This matrix records the released v1.2.3 compatibility baseline. The WSL2 live-acceptance, independent-review, and signed-release gates passed before publication.

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

การเปลี่ยน component นอก matrix ไม่ได้แปลว่าไม่รองรับ แต่ต้องทำ acceptance checklist ซ้ำก่อนใช้งาน production.
