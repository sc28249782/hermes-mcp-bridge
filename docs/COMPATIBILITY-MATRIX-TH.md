# Compatibility matrix — v1.2.2 candidate

This is a candidate matrix, not a production compatibility claim. It becomes a release record only after the v1.2.2 live-acceptance and signed-release gates pass.

| Component | Candidate baseline | วิธีตรวจ | หมายเหตุ |
| --- | --- | --- | --- |
| Python | 3.12 | `.venv/bin/python --version` | รัน regression ด้วย `-W error::ResourceWarning` และต้องใช้ project interpreter |
| Hermes API | loopback `127.0.0.1:8642` | `./bridge.sh doctor` | ต้องตอบ unauthenticated 401 และ authenticated 2xx |
| Hermes Runs | submit/status/stop + durable idempotency | `hermes_health` | run approval เป็น optional capability |
| Codex CLI | 0.155.1 | `./bridge.sh codex-doctor` | workspace-write ต้องผ่าน local approval; durable worker ต้องบันทึก terminal record |
| WSL2 | Ubuntu 24.04 | `uname -a` | ทดสอบผ่าน Secure MCP Tunnel |
| tunnel-client | official profile `hermes-wsl` | `bash tunnel.sh status` | profile ต้องชี้ `bridge.sh` ของ instance เดียวกัน |
| ChatGPT MCP | 27 tools | discovery ในแชทใหม่ | 26 tools จาก v1.2.1 + read-only `bridge_version` |
| Version/provenance | local-only CLI/MCP parity | `./bridge.sh version` และ `bridge_version` | ต้องไม่เรียก Hermes, Codex, tunnel, GitHub หรือ network |

การเปลี่ยน component นอก matrix ไม่ได้แปลว่าไม่รองรับ แต่ต้องทำ acceptance checklist ซ้ำก่อนใช้งาน production.
