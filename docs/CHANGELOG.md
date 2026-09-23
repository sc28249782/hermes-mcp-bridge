# Changelog

## v1.2.2 — release candidate (tag pending)

- Added local-only `./bridge.sh version` and read-only MCP `bridge_version`; both identify the reached bridge without contacting Hermes, Codex, Tunnel, GitHub, or another network endpoint.
- Added canonical embedded identity fields and safe `unknown` values for malformed config or unstamped development provenance. Git revision is optional worktree enrichment; release archives do not require `.git`.
- Added the durable Codex worker repair: local write approval now hands ownership to a detached worker that stores the actual exit code and terminal record after the short-lived approval CLI exits.
- Dev acceptance passed for the durable worker: an isolated approved write produced the exact marker, `completed`, `exit_code: 0`, terminal actor `worker`, and retrievable JSONL output.
- Release remains pending review, CI, bridge-version live acceptance, signed tag, external asset verification, and the Phase C release record.

## v1.2.1 — released (22 September 2026)

- Added explicit metadata-only work contexts: opaque context IDs bind a bridge-owned Hermes session after observation or bind Codex workspace/job metadata without replaying prompts, outputs, credentials, or ChatGPT conversation state.
- Added four MCP context tools and raised the canonical discovery contract to 26 tools. Context continuation is explicit per call; no global active context or latest-session inference exists.
- Live acceptance passed: Hermes continuation across a new ChatGPT chat, Codex workspace/job metadata binding without prompt/output replay, closed-context denial, and redacted audit records.
- Published signed and GitHub-verified tag `v1.2.1` at `d86703d1e1d8f675b656588208b3f557f5b63598`.
- Published the GitHub release archive and external `SHA256SUMS`; the archive checksum `36c01197d7dfb89b7a64a22ad32b35475762915076520c84ced8affb542e9b51` was verified after downloading from GitHub.

## v1.2.0 — released (22 September 2026)

- Released the Local Hands read-only vertical slice after successful WSL2 ext4/DrvFS live acceptance, deny-matrix and audit-redaction checks, case-collision refusal, and Hermes-off/Codex-unavailable fallback.
- Published signed tag `v1.2.0` at `bd56bafd4fcefcfbdf26699ab281cc1a6798bfc9`; the GPG signature was verified with EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- Published the GitHub release archive and `SHA256SUMS`; the archive checksum `621db6718323fb0639c67a9eac677af23de31a4f0f6e4d09b413d05f82960d08` was verified again after downloading from GitHub.

## v1.0.1

- Aligned schema validation with the Codex runtime: `codex.approval_ttl_seconds` is now rejected below 60 seconds rather than failing later during runner startup.
- Documented that the timeout watchdog runs in the persistent MCP server process; standalone local CLI approval depends on that server remaining available or on later status polling.

## Unreleased

- Clarified the two-phase release process: final archive checksums are external GitHub Release assets verified after the signed tag; a follow-up release-record commit documents that outcome without mutating the release tag.

- Documented Secure MCP Tunnel recovery after a ChatGPT Plugin disconnect: use `tunnel.sh status` rather than direct `tunnel-client doctor` when the profile references `CONTROL_PLANE_API_KEY`, select **Tunnel** plus **No authentication** for the stdio bridge, and preserve a redacted escalation path for stale-link/`harpoon` transport errors. Confirmed a successful live reconnection after this recovery flow.

- Added an automated critical-fallback MCP acceptance: Local Hands health/list/read work with an unreachable Hermes transport and missing Codex binary, plus a deterministic generated-path invariant test.
- Added a WSL2/ext4/DrvFS live-acceptance runbook and recorded its successful fixture, deny-matrix, audit-redaction, and OFF/OFF/ON results for v1.2.0.

- Started the v1.2.0 Local Hands read-only implementation: opt-in additive `hands` schema, `hands_health`, `hands_list`, and `hands_read` bring MCP discovery to 22 tools when the branch is deployed.
- Added a fail-closed descriptor-relative `openat2` resolver with beneath/no-symlink/no-magic-link constraints; workspaces whose strict resolver probe fails are unavailable rather than using check-then-open fallback.
- Added case-folded baseline workspace secret-name protection, protected credential-path handling, bounded UTF-8 regular-file reads, hard-link/special-file denial, redacted Hands audit metadata, and a read-only setup guide.
- Added unit and MCP integration coverage for disabled discovery, policy/secret denial, strict-resolver failure, path traversal/symlink escape, size/binary limits, hard links, case collisions, and 22-tool discovery.


- Added Endeavor Hands design attribution and its MIT notice while recording that no upstream source or assets are currently incorporated.
- Made generic deletion and unapproved truncation a non-overridable Local Hands baseline deny; execution must runtime-probe kernel enforcement such as Landlock, which starts with Linux 5.13 and must not be inferred from WSL2 alone.
- Recorded rejected reference patterns: allow-by-default deny-list sandboxes, model-relayed nonce authorization, read-anywhere policy, broad multi-format tools, and nested MCP trust bypasses.
- Added no-clobber move/working-copy guidance, structured failure classification, post-action computer verification, and English/Thai protected-field markers.

- Hardened the Local Hands design after review: v1.2.0 is now a three-tool read-only vertical slice, while mutation/execution moves to v1.3.0 and later Windows/computer-use milestones shift to v1.4.0-v1.6.0.
- Added non-removable workspace-internal protected filename patterns, strict `openat2`/DrvFS policy, property-based path tests, pending-action caps, trusted-workspace-code classification, and a computer-use security gate.
- Added ADR-0001 defining additive schema-v1 configuration, stable disabled-tool discovery, canonical SHA-256 action serialization, bounded JSONL process output, and metadata-only initial no-approval profiles.

- Added the post-v1.0.1 Local Hands roadmap, architecture/security design, and implementation acceptance plan. Local Hands is specified as a native sibling backend that remains usable when Hermes or Codex is unavailable or quota-limited.
- Reserved the deferred `v1.1.0` line for Hermes approval-event integration; the active Local Hands delivery path begins at `v1.2.0`.

- Deferred the proposed v1.1.0 Hermes approval-event SSE integration after live POC confirmed SSE transport but did not observe an interactive API approval event or exact approval request ID under `approvals.mode: manual`.

## v1.0.0

- Released as signed, GitHub-verified tag `v1.0.0`, targeting commit `2b280b2d3a763f69afa417bc76bdca6b801553fc`.
- Established the production baseline: compatibility matrix, repeatable WSL2 acceptance, release-integrity runbook, and published SHA-256 verification material.
- RC2 live acceptance passed for local-only heartbeat, Hermes idempotent read-only execution, configured Codex read-only execution, local workspace-write approval, and cancellation.
- Hardened nested bridge configuration validation so audit limits and unknown workspace keys match runtime policy.

## v0.9.1

- Fixed Hermes approval capability detection: the canonical Hermes Runs flag is `run_approval_response`; the legacy `run_approval` alias remains accepted for compatibility.
- `hermes_health` now reports whether local approval resolution is advertised instead of implying it unconditionally.

## v0.9.0

- Added `bridge_status`, a local-only heartbeat that reports bridge state without calling Hermes or Codex upstream APIs.
- Hermes status now includes `age_seconds`, local `stale` and `approval_stale` labels; these never stop or deny upstream work.
- Added schema version 1 validation for `bridge-config.json`; unknown keys appear as doctor/diagnostic warnings and invalid known values fail early.
- Installer migrates legacy config by adding `schema_version` and default Hermes stale thresholds.

## v0.8.0 — 2026-09-20

- Hardened Codex lifecycle handling: failed starts become `failed`, unobserved exits after restart become `unknown_exit`, and concurrency reservation is atomic.
- Added a persistent timeout watchdog (`codex.watchdog_interval_seconds`, default 15 seconds) so runtime policy is enforced without status polling.
- Cancellation now waits for process exit, escalates from SIGTERM to SIGKILL after a bounded grace period, and never records a terminal result while the process remains alive.
- Added public `approval_preview` for the local CLI, lifecycle/race/watchdog regression tests, and shellcheck in CI.
- Automated suite: 44 tests passing locally with `ResourceWarning` treated as errors; shellcheck runs in GitHub Actions.

## v0.7.0 — 2026-09-20

- เพิ่ม optional `model` และ `reasoning_effort` ให้ `codex_submit_task` โดยส่ง override ให้ Codex CLI เฉพาะเมื่อผ่าน allowlist
- เพิ่ม `allowed_models` และ `allowed_reasoning_efforts` ระดับ Codex หรือแยกต่อ workspace; ค่าเริ่มต้นปิด override เพื่อคง local Codex defaults
- แสดง policy model/reasoning ที่บังคับใช้ใน `codex_health`; เก็บชื่อค่าที่ร้องขอใน job state, status/recent และ redacted audit (ไม่เก็บ prompt/output)
- หน้าจอ local approval แสดง model/reasoning ที่ร้องขอ และยังต้องอนุมัติงานเขียนเหมือนเดิม
- เพิ่ม tests สำหรับ allowlist, forwarding argv และ health export; MCP discovery ยังคง 18 tools
- ผ่าน WSL2/Secure MCP Tunnel live acceptance ทั้ง default และ `gpt-5.6-sol` + `high`; ยืนยันว่าต้องใช้ model ID ไม่ใช่ display name ใน allowlist
- ทบทวนคู่มือ installation, developer, architecture, operations, testing และ upgrade ให้ใช้ v0.7.0, 18 tools, model IDs ที่ผ่าน acceptance และ project-origin link ปัจจุบัน

## v0.6.0 — 2026-09-20

- เพิ่ม workspace policy แบบ backward-compatible: sandbox modes, prompt/runtime limit และ concurrency ต่อ workspace
- เพิ่ม approval TTL สำหรับ write job ที่รอ local approval; job หมดอายุเป็น `expired`
- เพิ่ม approval context ที่คืน expiry และ policy root โดยไม่เปิดเผย prompt ผ่าน MCP
- เพิ่ม optional literal `deny_prompt_patterns` เป็น pre-flight guard พร้อมเอกสารข้อจำกัดว่าไม่ใช่ sandbox
- เพิ่ม `bridge_audit_recent` และ `./bridge.sh audit-recent` เพื่ออ่าน redacted audit records
- เพิ่ม policy/expiry/audit export tests; MCP discovery เป็น 18 tools

## v0.5.0 — 2026-09-20

- เพิ่ม `bridge_diagnostics` แบบ read-only; ตรวจ Hermes/Codex health, state directory permissions และ audit configuration โดยไม่แสดง secret
- เพิ่ม audit log แบบ JSONL ที่ redacted, mode `600`, หมุนไฟล์และกำหนด retention ได้
- บันทึก lifecycle ของ Hermes/Codex โดยไม่เก็บ prompt หรือ output
- เพิ่ม recovery marker สำหรับ Codex job ที่ยังรันหลัง bridge/WSL restart และอธิบายข้อจำกัดของ exit code ที่ไม่ถูกสังเกตโดย bridge เดิม
- installer เพิ่ม audit configuration โดยไม่ทับค่า Hermes หรือ Codex เดิม
- เพิ่ม test สำหรับ redaction, rotation, restart recovery และ diagnostics; MCP discovery เป็น 17 tools

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
