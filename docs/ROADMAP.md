# Roadmap

## Completed

- [x] v0.4.1 — WSL2 live acceptance for the Hermes and Codex paths
- [x] v0.5.0 — redacted audit logging, diagnostics, rotation/retention, and recovery visibility
- [x] v0.6.0 — per-workspace policy, approval TTL, prompt guardrails, and audit export
- [x] v0.7.0 — per-task Codex model and reasoning-effort policy
- [x] v0.8.0 — Codex process-lifecycle, timeout, cancellation, and concurrency hardening
- [x] v0.9.0 — operational state, configuration schema, and local-only heartbeat
- [x] v1.0.0 — production baseline, compatibility matrix, acceptance checklist, and release integrity
- [x] v1.0.1 — configuration/runtime alignment and watchdog documentation maintenance

### v1.2.0 — Independent read-only WSL2 Hands

- [x] Add an optional `hands` backend that initializes independently of Hermes health and Codex availability.
- [x] Keep the additive `hands` configuration block in schema version 1; Hands is disabled when the block is absent or `enabled=false`.
- [x] Add a canonical read-only workspace allowlist, protected-path rules, non-removable protected-filename patterns, and bounded list/read responses.
- [x] Add only three native MCP tools: `hands_health`, `hands_list`, and `hands_read`; discover them even while disabled and return a stable `disabled` result. The planned v1.2.0 discovery count is 22 tools (existing 19 + Hands 3).
- [x] Use descriptor-relative `openat2` with `RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS | RESOLVE_NO_MAGICLINKS` whenever the kernel/filesystem supports it. A configured workspace whose strict resolver self-test fails is unavailable; do not silently fall back to check-then-open.
- [x] Define conservative DrvFS behavior in v1.2.0: descriptor-based containment, case-folded protected-name matching, filesystem/mount reporting, and rejection of ambiguous case-colliding entries.
- [x] Reuse redacted rotating audit infrastructure without recording file content, secrets, or complete user payloads.
- [x] Add property-based path tests plus adversarial traversal, symlink-swap, protected-name, DrvFS case, binary, special-file, and size-limit tests.
- [x] Extend `bridge_status` and diagnostics with independent `hermes`, `codex`, and `local_hands` availability, without contacting a model for the Hands result.
- [x] Prove the critical fallback scenario in automated and WSL2 live acceptance: Hermes unavailable + Codex unavailable + Local Hands health/list/read functional.
- [x] Keep Hands disabled by default during upgrade; the installer must not invent readable workspaces.

## Deferred track — Hermes approval-event integration

`v1.1.0` remains reserved for Hermes API approval-event integration and is not on the active delivery path.

- [x] SSE transport POC against the installed API-server: `GET /v1/runs/{run_id}/events` returned authenticated `text/event-stream` frames for normal run events.
- [x] A terminal run before and after setting `approvals.mode: manual` did not emit an approval event or an exact approval request ID.
- [x] The API-server profile was confirmed to use `approvals.unattended_mode`, not the interactive approval flow.
- [ ] Do not implement SSE approval delivery, an approval MCP tool, or automatic approval responses until Hermes provides a documented interactive API approval contract.
- [ ] Re-open only after upstream demonstrates an approval event, stable exact request ID, reconnect semantics, expiry semantics, and a response contract; then repeat fake-server and WSL2 approval/deny/reconnect/expiry acceptance.

## Active roadmap — Hermes Local Hands

Local Hands adds deterministic local-computer primitives that ChatGPT can call directly. It is a sibling backend to Hermes and Codex, not a wrapper around either one.

Critical availability requirement:

> Local Hands MUST remain operational when Hermes or Codex is disabled, unavailable, rate-limited, or quota-exhausted. Its execution path MUST NOT invoke a Hermes model or Codex CLI.

The design, trust boundaries, proposed configuration, and tool contracts are in [LOCAL-HANDS-ARCHITECTURE-TH.md](LOCAL-HANDS-ARCHITECTURE-TH.md). The delivery sequence and acceptance matrix are in [LOCAL-HANDS-IMPLEMENTATION-PLAN-TH.md](LOCAL-HANDS-IMPLEMENTATION-PLAN-TH.md).


## v1.2.1 — Explicit work-context continuity

- [x] Add a local metadata-only context registry with opaque `context_id`; it never stores or replays prompts, outputs, credentials, or ChatGPT conversation state.
- [x] Bind a returned Hermes `session_id` to an explicit context after task status/result; a later `hermes_submit_task(context_id=...)` continues only that bridge-owned session.
- [x] Bind Codex workspace/job metadata to an explicit context without pretending that independent Codex CLI jobs are a resumable chat session.
- [x] Require `context_id` on every continued task; do not create a global active context or infer the latest session across chats.
- [x] Provide create/status/recent/close context tools and metadata-only audit events.

## v1.2.2 — Bridge version and provenance

- [x] Add one canonical embedded version/provenance source that is included in both Git worktrees and release archives; do not rely on `.git` or `git describe` at runtime.
- [x] Add a local-only `./bridge.sh version` command that reports bridge version, release identifier, embedded commit/build provenance, source kind (`git-worktree` or `release-archive`), config schema version, and MCP discovery count without calling Hermes, Codex, Tunnel, GitHub, or any network endpoint.
- [x] Add one additive read-only MCP tool, `bridge_version`, whose result matches the CLI contract and identifies the bridge instance actually reached through Secure MCP Tunnel. The planned discovery count is 27 tools.
- [x] Define deterministic fail-safe behavior for absent, malformed, or development provenance: report explicit `unknown`/development fields without raising, guessing a release, or exposing filesystem paths, environment values, credentials, prompts, outputs, or audit content.
- [x] Keep update availability separate from local version reporting. Any optional GitHub release check must be an explicit future command with network behavior documented; `doctor`, `bridge_status`, and `bridge_version` remain local-only.
- [x] Add tests for release-archive metadata, Git worktree metadata, missing/malformed provenance, CLI/MCP equality, disabled upstreams, and the 27-tool discovery contract.
- [x] Update README, TESTING, UPGRADE, OPERATIONS, CHANGELOG, release status, and release runbook before tag; document that tests must use the project interpreter (`.venv/bin/python`) rather than a PATH-selected `python3`.
- [x] Run WSL2/Secure MCP Tunnel live acceptance: CLI and MCP version fields agree for the deployed candidate, remain available when Hermes/Codex are unavailable, expose no secret-bearing state, and restore the Dev config byte-for-byte after the temporary unavailable-upstream fixture.
- [ ] Release only through the existing Phase A/B/C process: documentation gate before signed tag, external `SHA256SUMS` asset verified after download, and post-tag release-record commit.

## v1.3.0 — Approval-bound mutation and execution

- [ ] Add `hands_write`, `hands_patch`, `hands_exec`, and `hands_process` after v1.2.0 read-only live acceptance and feedback.
- [ ] Implement canonical action digests exactly as [ADR-0001](adr/0001-local-hands-foundation.md) specifies: versioned deterministic JSON bytes plus SHA-256, immutable persisted payload/blob reference, TTL, one-time use, and revalidation at execution.
- [ ] Require local human approval for writes, patches, content-bearing execution, and all trusted-workspace-code execution; expose no MCP approval tool.
- [ ] Bound pending actions globally and per workspace; reject new actions at the cap and audit only redacted metadata.
- [ ] Keep execution fixed-argv with `shell=False`; do not accept unrestricted shell/PowerShell command strings.
- [ ] Make generic deletion, unlink, rmdir, unapproved truncation, and destructive rename a non-overridable baseline deny. Do not expose a generic delete tool; exact approved write/patch remains a separate digest-bound operation.
- [ ] Enforce no-delete/no-unapproved-truncate execution at kernel level with a runtime-probed mechanism such as Landlock; Landlock starts with Linux 5.13 but availability/configuration/ABI must be probed rather than inferred from the kernel version or WSL2 label. Required profiles are unavailable when enforcement is insufficient.
- [ ] If a move operation is added, make it a dedicated exact-source/destination no-clobber operation; never implement it as arbitrary `mv` argv.
- [ ] Treat Git, CMake, test runners, interpreters, hooks, build rules, response files, and config-file indirection as trusted-workspace-code execution, not as safe merely because the executable is allowlisted.
- [ ] Permit no-approval profiles only when output is metadata-only and argv is exact/constrained; `git diff` is content-bearing and is not read-safe.
- [ ] Persist process output as bounded JSONL per process and persist lifecycle state with ownership, timeout enforcement, cancellation, and safe restart recovery.
- [ ] State explicitly that executable output is workspace-controlled content sent to ChatGPT and may contain secrets; filename protection cannot make command output secret-safe.
- [ ] Add Windows-to-WSL and WSL-to-Windows path translation as an internal helper; translation must not weaken canonical containment checks.

## v1.4.0 — Windows Host Adapter

- [ ] Add `hands_windows` as an optional adapter invoked from WSL2 through a fixed executable path and fixed argv, with PowerShell script policy disabled by default.
- [ ] Support bounded, policy-scoped read operations for processes, services, event logs, networking, filesystem metadata, and clipboard metadata before enabling mutations.
- [ ] Add Windows path canonicalization that handles drive letters, UNC rejection by default, reparse points, case-insensitive comparisons, and WSL mount translation.
- [ ] Add separate allowlists for Windows commands, service names, process actions, and accessible roots; do not inherit WSL permissions implicitly.
- [ ] Require local approval for service/process mutation, clipboard content access, Windows writes, and script execution.
- [ ] Add Windows-specific audit fields without recording clipboard contents, script bodies, credentials, or command output.
- [ ] Validate with Windows 11 + WSL2 under both `virtioproxy` and documented compatible networking modes; Hands must not require mirrored networking.

## v1.5.0 — Windows Computer Use

- [ ] Hard gate: do not start computer-use implementation until v1.4.0 Windows Host passes live acceptance and a recorded security review.
- [ ] Ship an observe-only vertical slice first, then bounded click in a disposable test application; typing remains disabled until a separate review and acceptance gate passes.
- [ ] Add one compact `hands_computer` tool with staged actions such as `observe`, then `click`; later actions such as `type`, `key`, `scroll`, `drag`, `open`, and `wait` require their own policy/review.
- [ ] Implement a signed/versioned Windows helper using supported Windows capture and UI Automation APIs; keep it bound to the local machine and authenticate WSL2 requests.
- [ ] Enforce a window/application allowlist, foreground-window verification, coordinate bounds, stale-observation rejection, and per-action timeouts.
- [ ] Add bounded post-action observation with screen-change signal, app/window revalidation, expected-state predicate, and `verification_inconclusive` when success cannot be proved.
- [ ] Refuse password, PIN, MFA, credential-manager, secure-desktop, UAC, payment, and other protected-field interaction.
- [ ] Include normalized English/Thai defense-in-depth markers: `password`, `passcode`, `pin`, `otp`, `mfa`, `2fa`, `verification code`, `security code`, `รหัสผ่าน`, `รหัส`, `พิน`, and `โอทีพี`; accessibility secure-field metadata remains authoritative where available.
- [ ] Require approval for high-impact UI actions and never infer approval from visible page text or model output.
- [ ] Treat screenshots, OCR, accessibility trees, and application text as untrusted input and document prompt-injection handling.
- [ ] Provide an emergency stop and visible local activity indicator; cancellation must prevent queued follow-up UI actions.
- [ ] Run live acceptance first against disposable applications and fixtures, never a maintainer's real credential or payment workflow.

## v1.6.0 — Routing, fallback, and operational hardening

- [ ] Publish a capability contract that lets ChatGPT choose Hermes, Codex, or Local Hands without circular orchestration.
- [ ] Report normalized backend reasons such as `available`, `disabled`, `unreachable`, `usage_limit`, `quota_exhausted`, and `policy_blocked` without exposing secrets.
- [ ] Document direct routing: short deterministic work to Hands, coding work to Codex, and long agentic work to Hermes; Hands itself never delegates back to an agent.
- [ ] Add cross-backend correlation IDs for audit only; never share prompts, outputs, credentials, or approval authority across backends.
- [ ] Add load, restart, expiry, cancellation-race, disk-full, truncated-output, and audit-rotation tests for all Hands adapters.
- [ ] Complete threat-model review, upgrade/rollback instructions, compatibility matrix, operations runbook, and a signed release acceptance record.

## Release gates applying to every Local Hands version

- Documentation, version references, tool counts, configuration examples, tests, checksums, and release notes must be updated before tagging or publishing release assets.
- Attribution and `THIRD_PARTY_NOTICES.md` must be reviewed before release; any future Endeavor Hands source adaptation must preserve its copyright and MIT notice.
- New mutation capabilities ship disabled by default and require explicit local policy.
- No backend may approve its own action or obtain approval through MCP.
- No credential value, file content, prompt, command output, screenshot, or clipboard content may enter audit logs.
- Unit tests and fake adapters are necessary but do not replace WSL2/Windows live acceptance.
- Release archives and checksums must be generated from the signed release commit and verified after download.

## Non-goals

- A public inbound service, unrestricted remote shell, unrestricted filesystem/network access, or generic remote-desktop product
- Replacing ChatGPT reasoning with a local model; Local Hands still requires an active ChatGPT/MCP session for interactive use
- Making Hands available when the bridge, tunnel, ChatGPT session, WSL2, or required local helper is unavailable
- Transmitting Hermes, OpenAI, Windows, SSH, cloud, browser, or signing credentials through MCP
- Letting an agent approve its own action, weakening Codex approval rules, or reusing Hermes approval authority
- Parsing arbitrary shell/PowerShell text and attempting to infer safety from keywords alone
- A deny-list sandbox with allow-by-default semantics, model-relayed nonce as authorization, read-anywhere filesystem policy, or dynamic MCP-to-MCP trust bypass
- Treating fixed argv, an exact entrypoint/cwd, or model-managed delegation as sufficient authority to bypass the Local Hands policy engine
- Multi-user credential management, payment automation, secure-desktop control, or unattended credential entry
