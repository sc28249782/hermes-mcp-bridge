# Changelog

## v0.4.0 — 2026-09-19

- รักษา Hermes MCP tools เดิม 10 ตัวจาก v0.3.2
- เพิ่ม Codex/WSL2 MCP tools 6 ตัว รวม discovery 16 tools
- เพิ่ม workspace allowlist พร้อม canonical-path และ symlink-escape guard
- เพิ่มโหมด `read-only` และ `workspace-write`; ไม่เปิด `danger-full-access`
- เพิ่ม local approval gate สำหรับงานเขียน: `codex-approve` / `codex-deny`
- เพิ่ม Codex job persistence, status, paginated JSONL result, timeout, cancel และ recent list
- installer เพิ่ม config block โดยไม่ทับค่าของ v0.3.2
- เพิ่ม permission-policy tests และอัปเดต MCP integration test เป็น 16 tools

## v0.3.2 — 2026-09-14

- เพิ่ม live-acceptance record สำหรับ 10 MCP tools และปรับเอกสาร/tool counts ให้ตรงกับ release

## v0.3.1 — 2026-09-14

- แก้และเพิ่ม `UPGRADE-TH.md` สำหรับอัปเกรดจาก v0.2.0 โดยตรง

## v0.3.0 — 2026-09-14

- เพิ่ม `hermes_usage_summary` และ `hermes_usage_export` สำหรับ cached usage ของ bridge-owned runs
- ไม่คำนวณราคา เพราะราคา provider/model ไม่ได้เป็นข้อมูลที่ bridge เชื่อถือได้
- export ไม่มี prompt, output หรือ API key

## v0.2.1 — 2026-09-14

- `bash tunnel.sh init tunnel_ID --force` ส่ง `--force` ให้ `tunnel-client init` เพื่อแทน profile เดิมได้

## v0.2.0 — 2026-09-13

รวม operational hardening ที่วางไว้สำหรับ v0.1.1 และ model-aware execution

### Added

- `tunnel.sh key-set`, `key-status`, `key-clear` สำหรับ OpenAI Platform runtime key แบบไฟล์ mode 600
- `tunnel.sh service-install`, `service-start`, `service-stop`, `service-restart`, `service-status`, `service-logs`, `service-uninstall` สำหรับ systemd user service
- MCP tools แบบ read-only: `hermes_model_info`, `hermes_models`
- optional `model`, `provider`, `model_options` ใน `hermes_submit_task` สำหรับงานใหม่
- SQLite migration ที่บันทึก requested model/provider/options และ Hermes-reported model
- tests สำหรับ model override, old SQLite migration, tunnel key loading และ generated service unit

### Changed

- `request_id` fingerprint รวม model/provider/model options แล้ว
- follow-up ที่ระบุ `session_id` จะปฏิเสธ model override เพื่อไม่ให้ session เปลี่ยน model อย่างเงียบ ๆ
- installer เพิ่ม `hermes_config` ใน `bridge-config.json` ใหม่ เพื่ออ่าน model metadata แบบ safe YAML

### Security

- runtime key ไม่ถูกเขียนใน systemd unit และไม่พิมพ์ใน output
- model options ใช้ allowlist: `reasoning_effort`, `service_tier`
- global Hermes model configuration ยังต้องเปลี่ยนจาก local WSL terminal
