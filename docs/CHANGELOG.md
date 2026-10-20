# Changelog

## v1.2.7 — release candidate, tag pending (20 October 2026)

- Prepare the two unreleased scopes below with stamp `1.2.7/v1.2.7`, provenance `release`, and reviewed build input `07ec0069b952f08a49adbd0ec778c204f85ee282` (PR #63 merge). This input is not the final signed-tag commit.
- Keep schema version 1, discovery 27/28/33 and backend permissions unchanged. Source/extracted verification and candidate ZIP receipt belong to the [preparation PR](V1.2.7-RELEASE-PREP-TH.md). No signed tag, publication or deployment is performed.
- Production and the current signed release remain v1.2.6. Historical decision/release checkpoints below retain their original scope and time.

Scope decision checkpoint (20 October 2026, 18:47:56 +07): the operator approved [v1.2.7 target scope](V1.2.7-RELEASE-DECISION-TH.md), combining the two unreleased sections below. Release preparation, final-target signing/publication and deployment remain separate. No stamp, signed release or deployment is created by this checkpoint.

## Unreleased — Context P1 registry warning and preview

- Add optional `contexts.soft_cap` (default 1,000; range 1–100,000). Observe at most cap+1 logical rows through a read-only SQLite connection. Reaching the cap is a warning; it does not reject create or submission.
- Add the six-field `registry` aggregate to `bridge_status.contexts` and successful context creates. Report unavailable counts as null. Keep a successful create acknowledged when observation fails. Status root `ok` becomes false for registry unavailability, but remains true for a cap warning alone.
- Add local `context-prune-preview` before backend imports/configuration. Use an existing absolute state directory, closed/unbound predicates, fixed JSON errors and bounded result materialization. Retain SQLite locking and WAL checks. SQLite may use sidecar files; read-only SQL is not a filesystem-wide no-write guarantee.
- Keep existing status/recent semantics, schema version, discovery counts and signed v1.2.6 unchanged. No deletion, native compaction, release or deployment is included. P2 lifecycle/apply work remains deferred.

## Unreleased — Codex result read-ahead fix

- Open Codex result logs with `buffering=0`. Buffered readers could fetch appended bytes beyond the captured length and could serve prefetched data after truncation. Enforce the existing SPEC §19.3 byte budget at the raw read boundary.
- Add a deterministic append-before-read regression that observes the raw descriptor offset. Keep the existing truncate/error, decoding and pagination tests.
- Run CI on Python 3.12 and 3.14. The public candidate passed WSL 185/185 on both 3.12.3 and 3.14.7.
- Keep the 8,388,608-byte snapshot cap, 65,536-byte read limit, tool/schema contracts and stamp unchanged. This patch is not in signed v1.2.6 or production. Target scope v1.2.7 is approved and preparation is recorded above; signing/publication and deployment remain pending.

## v1.2.6 — released privacy contract and runtime hardening (20 October 2026)

- Amend SPEC §4/§10 through §19: explicit bounded result/file content can include a full short result and potentially sensitive data. Private operational storage is separate from content-free audit logging. This corrects an overbroad privacy promise and requires security-contract review; it does not add secret scanning, encryption, sandboxing or backend permissions.
- Filter Hermes task status/result metadata. Replace raw upstream error text with a constant message and approval payloads with `{"required": true}`. Keep exact approval preview and revalidation in the local terminal. Limit metadata to 8,192 serialized bytes; keep upstream decoded JSON at 4,000,000 bytes and HTTP connect/inactivity timeouts at 5/25 seconds (not a total deadline).
- Enforce `0700` on existing Hermes/Codex state directories and the Codex log directory. Fail initialization when modes cannot be secured.
- Read Codex result snapshots in 65,536-byte chunks up to 8,388,608 bytes per call. Preserve character pagination, UTF-8 replacement and universal newlines without loading the whole log. Oversize snapshots require local inspection; the read limit does not cap worker log capture or introduce cleanup.
- Keep tool registrations, binaries, config schema, signed releases and production deployment unchanged. Contract/implementation review and scoped Dev fixture acceptance/restoration passed through PR #47–#49. The operator approved the v1.2.6 scope on 20 October 2026. The candidate is stamped `1.2.6/v1.2.6` with reviewed build input `e3e698a7a220bf14a8bb4d1260bf2ded7e666b56`. Exact-head/archive verification is recorded through the [release-preparation record](V1.2.6-RELEASE-PREP-TH.md); signing/publication passed and the deployment decision remains pending. The approval and evidence limits are documented in [PRIVACY-RELEASE-DECISION-TH.md](PRIVACY-RELEASE-DECISION-TH.md); scope approval does not establish a release.

Release record: signed annotated tag `v1.2.6` on `cee144e14e53d971d986de346aab58c51bca97f0`; signer `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86` passed cryptographic verification. GitHub badge reports `no_user`, not verified. ZIP SHA-256 `acf6c38ca371acd73d31099c5448d6ef9c3588020e74d0c0bfe3769736b1664e`; ZIP and external SHA256SUMS passed fresh-download checksum/structure and byte-identical signed-tag rebuild checks. Production identity still reports v1.2.5 after publication; no deployment was performed. See [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md). This is a post-tag record, outside the signed archive.

## v1.2.5 — released (19 October 2026)

- Add the separate, disabled-by-default `opencode.execution` opt-in. Require the health adapter, existing canonical workspaces and allowed models.
- Add `opencode_submit_task`, `opencode_task_status`, `opencode_task_result`, `opencode_cancel_task` and `opencode_recent_tasks`. Discovery is 33 only when execution is enabled. The 27-tool default and 28-tool health-only contract remain unchanged.
- Store bridge-owned jobs and sessions with request idempotency and atomic admission. A detached worker bounds runtime and I/O. It signals its CLI group before reaping the leader. Unconfirmed cleanup remains `unknown_exit` and blocks new work.
- Keep native OpenCode configuration and permissions. The bridge adds no sandbox and never passes `--auto`. Workspace selection limits cwd, not filesystem or network access. A completed native turn does not prove goal success.
- Validate the final code on WSL with 164 passing tests, Shellcheck and exact-code-head CI. Regressions cover unconfirmed cleanup and execution config recognition. Real CLI v2.0.32 submission, context/session reuse, replay, cancellation and absolute-path file edits pass. See [TESTING.md](TESTING.md) and [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md).
- Authenticated Dev Work-chat acceptance passed on 19 October 2026: real-model submit/result, resumed context, request replay/recent and independently byte-verified native file creation. Native permission-required coverage remains fixture-only. This extension ships in v1.2.5; the adapter shipped in v1.2.4 remains health-only.
- Stamp `version_info.py` as `v1.2.5` with build provenance `release` and the reviewed build-input revision `a666d626da1fe716ce4b259d49eedfc3f97acc7d` (`main` with PR #40 merged). Release preparation passed before tagging; the published release record is below. No rollout is performed.

Release record: signed tag `v1.2.5` on `6fbcd7ef278d5e45a95b7328c719c5b01cbcf522`; ZIP SHA-256 `1f1c8a583cf7f51a88ec35ca3023c86342220f5baba37faed3f1724b04bf8d5f`. ZIP and external SHA256SUMS are published and fresh-download verified. See [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md). Production remains v1.2.3.

Deployment checkpoint (19 October 2026, ~18:44 +07): the production deployment was upgraded to v1.2.5 later that day. The "Production remains v1.2.3" sentence above preserves the post-tag release record as written; the upgrade checkpoint with its evidence boundary is in [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md).

## v1.2.4 — released (18 October 2026; signed tag, published)

- Scope note (18 October 2026): the capability-gated MCP Events track originally planned for v1.2.4 is deferred to an unversioned BLOCKED track with no assigned release and is not part of this maintenance release (OpenCode health adapter disabled by default and legacy stdio discovery guard only).

Release record: released on 18 October 2026 via GPG-signed annotated tag `v1.2.4` on main `213305638c135041c42a3f242d6c5665c49c3fdf` (build input `0884482d8cf74d696b6c52a785282f65f2bd40fa`); the final ZIP built from the signed tag is published at https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.4 (ZIP SHA-256 `e6deb0e6ab16d669836b0e361e2e875858e19597ef35dc7e4fc19010a6a5f3a9`, external SHA256SUMS asset, fresh download re-verified). Production runtime remains the released v1.2.3. Live Secure MCP Tunnel acceptance over the real Dev plugin route was recorded on 18 October 2026 as a bounded pass (identity/status/tool visibility confirmed; the tunnel-side guard `-32601` observation stays unproven from the dispatcher log — see LIVE-ACCEPTANCE-TH.md).

- Legacy stdio: guard `server/discover` ตอบ `-32601` ที่ boundary (same id, ไม่ echo params) และปิด context อย่างถูกต้อง (cancel forwarder, wake stdout writer ป้องกัน hang) — รวมใน released v1.2.4

- Add a disabled-by-default OpenCode adapter (`opencode_core.py`) with one additive read-only tool, `opencode_health`, registered only when the new `opencode` configuration section sets `enabled: true`. Discovery stays at 27 tools by default and becomes 28 tools when enabled.
- The health check performs one bounded `--version` probe with a fixed argv list, `shell` disabled, a 1-120 second timeout (default 10), a per-stream memory cap (1024-1048576 bytes, default 65536), and process-group cleanup with `SIGTERM` escalation to `SIGKILL`. When disabled, the bridge fails closed and never spawns a process.
- The adapter is a foundation only: task submission, sessions, JSON event output, cancellation, and permission handling are not implemented, and no such tool is registered in this release.
- Fix (review): the version probe no longer reaps the probe leader before the final group signal. Exit is observed with nonreaping `os.waitid` (`WEXITED|WNOHANG|WNOWAIT`, Linux) bounded by the same overall deadline as the drain; `SIGTERM`, the grace wait, and `SIGKILL` all happen while the unreaped leader pins the PGID; the single reap follows the final `SIGKILL` by handle; unknown leader ownership sends no signal. Regression tests record the real signal/wait ordering on the success, nonzero-exit, timeout, and pipe-descendant paths.
- Config validation now rejects every ASCII control character (0x00-0x1F and 0x7F) in `opencode.binary`, not only NUL/CR/LF. Removed the unused 300-character version cap; the version regex already bounds the string to 200 characters.
- Live acceptance recorded for `--version` ONLY against the real OpenCode CLI (WSL2, in-memory configuration, no settings change): `ok: true`, version `opencode v2.0.32`. Task submission, sessions, JSON event output, cancellation, and permissions remain unverified.
- SPEC.md: add section 16 as the normative contract for the OpenCode health adapter (review amendment, PR #34). It marks the surface as a v1.2.4 release-candidate surface, disabled by default, and maps each requirement to the existing offline tests and the v2.0.32 `--version` live acceptance only. Section 14 records the amendment as a separate PR-introduced change with no v1.2.4 Events claim.
- Release preparation (local): `version_info.py` is stamped `v1.2.4` with build provenance `release` and reviewed build-input revision `0884482d8cf74d696b6c52a785282f65f2bd40fa`; `tests/test_packaging.py` proves the release archive ships `opencode_core.py`, `stdio_guard.py`, and the stdio fixture servers (`install.sh` runs from the extracted `git archive`; it does not copy files).

## MCP Events Dev capability probe (4 October 2026) — blocked at the subscription gate

- Dev trace confirmed successful `server/discover`, `tools/list`, and `events/list`; the plugin page displayed `bridge.probe.ready`.
- Two additional Dev discovery sequences succeeded, but no `events/subscribe` reached the fixture in the supplied trace. The chat reply is not a protocol error or proof about all Work chats.
- Stop the runtime track at the subscription gate. Do not retry identical prompts or send callbacks. Reopen only when client/workspace event eligibility is verified and `events/subscribe` is observed. Explicit user-directed status polling remains available.

## v1.2.3 — released (4 October 2026)

- Preserve `running` when a durable worker is unavailable but its Codex child remains alive; expose only a redacted supervision-loss hint.
- Persist worker/child process start times to reject reused PIDs during recovery and keep cancellation targeted at the original process group.
- Treat Linux/WSL2 `/proc` state `Z` as not alive so an unreaped crashed worker cannot leave a dead job stuck in `running`.
- Keep `terminal` and `approval` fields stable across running-state early returns.
- Add regression coverage for worker-only loss, delayed child exit, fail-closed `unknown_exit`, PID-reuse detection, and an actual unreaped zombie process. Automated CI and WSL2 live acceptance passed; the 75-test WSL2 run has no `ResourceWarning`.
- Published signed tag `v1.2.3` at `c610660637dbdcfa0b8ddb7bbf01ed22ae66055d`. The GPG signature was verified with EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- Published the GitHub release archive and external `SHA256SUMS`; the archive checksum `c231f8563543dbfa9eafa240c5e8e15f44434103940352066e65b58162cb5458` was verified after a fresh download from GitHub.

## v1.2.2 — released (23 September 2026)

- Added local-only `./bridge.sh version` and read-only MCP `bridge_version`; both identify the reached bridge without contacting Hermes, Codex, Tunnel, GitHub, or another network endpoint.
- Added canonical embedded identity fields and safe `unknown` values for malformed config or unstamped development provenance. Git revision is optional worktree enrichment; release archives do not require `.git`.
- Added the durable Codex worker repair: local write approval now hands ownership to a detached worker that stores the actual exit code and terminal record after the short-lived approval CLI exits.
- Dev acceptance passed for the durable worker: an isolated approved write produced the exact marker, `completed`, `exit_code: 0`, terminal actor `worker`, and retrievable JSONL output.
- CI and Dev bridge-version live acceptance passed: CLI/MCP identity parity held through the Secure MCP Tunnel; `bridge_version` remained available with an unreachable Hermes endpoint and absent Codex binary, then the Dev config was restored byte-for-byte.
- Published signed tag `v1.2.2` at `f8f1d93930882dc3e669dab0a05b4bd5c1834bef`; its GPG signature was verified with EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- Published the GitHub release archive and external `SHA256SUMS`; the archive checksum `e9582153c57458e3ca73a4c169f46653662377b004c9c2ee552824c4ffce5dc5` was verified after downloading from GitHub.

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

## Historical development notes (already shipped)

> Historical note (18 October 2026): every item below this point shipped in v1.2.0 or a later release recorded above; kept here as history.

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

