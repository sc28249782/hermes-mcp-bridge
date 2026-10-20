# Compatibility matrix — released v1.2.7 and signed v1.2.6 production baseline

Candidate v1.2.7 contains the reviewed Codex read-ahead fix and Context P1. The [preparation record](V1.2.7-RELEASE-PREP-TH.md) defines exact-head source/extracted verification and Python 3.12/3.14 CI. Stamp/build input are 1.2.7/v1.2.7/`07ec0069b952f08a49adbd0ec778c204f85ee282`; publication/deployment are pending. No component, permission, schema-version or discovery-count change is required. Python 3.14 CI evidence does not by itself change the production interpreter.

Status update (20 October 2026): v1.2.7 is released via signed tag `625ea117aa693f577872638a6353b1408fb405aa`; the sentence above preserves the pre-release state. Production remains v1.2.6; the deployment decision, including the not-deploy option, is pending. See the [release record](V1.2.7-RELEASE-RECORD-TH.md).

Released v1.2.6 adds SPEC §19 privacy hardening without changing component requirements, tool schemas or discovery counts. Signed-tag assets passed post-download verification; production was later upgraded to signed v1.2.6 as recorded in [the deployment checkpoint](V1.2.6-DEPLOYMENT-TH.md). Historical preparation gates are in [V1.2.6-RELEASE-PREP-TH.md](V1.2.6-RELEASE-PREP-TH.md).

The baseline below records released v1.2.5: the v1.2.4 component baseline plus the opt-in OpenCode execution extension. The WSL2 live-acceptance, independent-review, and signed-release gates passed before publication.

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
| OpenCode CLI (optional) | v2.0.32 (health and execution, separate opt-ins; released v1.2.5) | `opencode_health` + 5 execution tools | disabled by default; live acceptance: `--version` (18 ตุลาคม 2026) และ Dev Work-chat execution (19 ตุลาคม 2026); discovery 27 tools เมื่อปิด, 28 เมื่อเปิด health, 33 เมื่อเปิด execution |

การเปลี่ยน component นอก matrix ไม่ได้แปลว่าไม่รองรับ แต่ต้องทำ acceptance checklist ซ้ำก่อนใช้งาน production.

## OpenCode execution — released v1.2.5

ส่วน execution ใช้ OpenCode CLI v2.0.32 บน Linux/WSL2 ผ่าน `run --standalone --format json`
พร้อม stdin prompt และ session ที่ bridge เป็นเจ้าของ ใช้ detached worker และ Linux `waitid(WNOWAIT)`
จึงไม่มี Windows-native acceptance ฟีเจอร์นี้ไม่อยู่ใน signed v1.2.4 และไม่อ้าง HTTP v1/v2 API,
ACP, MCP Events หรือ native permission replies เป็น surface ที่รองรับ
ดู [OPENCODE-TH.md](OPENCODE-TH.md) และผลตรวจใน [TESTING.md](TESTING.md)
