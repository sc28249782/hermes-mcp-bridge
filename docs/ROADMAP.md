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

## v1.2.0 — Independent WSL2 Hands Core

- [ ] Add an optional `hands` backend that initializes independently of Hermes health and Codex availability.
- [ ] Add schema-versioned Hands configuration with a canonical workspace allowlist, per-workspace read/write/execute capabilities, protected-path deny rules, size/runtime/output limits, and executable allowlists.
- [ ] Add native MCP tools: `hands_health`, `hands_list`, `hands_read`, `hands_write`, `hands_patch`, `hands_exec`, and `hands_process`.
- [ ] Keep command execution fixed-argv with `shell=False`; do not accept an unrestricted shell command string in v1.2.0.
- [ ] Reuse redacted rotating audit infrastructure without recording file content, command output, secrets, or complete user payloads.
- [ ] Require local human approval for writes, patches, and policy-classified execution; expose no MCP approval tool.
- [ ] Persist pending actions and background-process state with TTL, ownership, bounded output, timeout enforcement, cancellation, and safe restart recovery.
- [ ] Add Windows-to-WSL and WSL-to-Windows path translation as an internal helper; path translation must not weaken canonical containment checks.
- [ ] Extend `bridge_status` and diagnostics with independent `hermes`, `codex`, and `local_hands` availability, without contacting a model for the Hands result.
- [ ] Prove the critical fallback scenario in automated and WSL2 live acceptance: Hermes unavailable + Codex unavailable + Local Hands functional.
- [ ] Keep Hands disabled by default during upgrade; the installer must not invent writable workspaces or executable policy.

## v1.3.0 — Windows Host Adapter

- [ ] Add `hands_windows` as an optional adapter invoked from WSL2 through a fixed executable path and fixed argv, with PowerShell script policy disabled by default.
- [ ] Support bounded, policy-scoped read operations for processes, services, event logs, networking, filesystem metadata, and clipboard metadata before enabling mutations.
- [ ] Add Windows path canonicalization that handles drive letters, UNC rejection by default, reparse points, case-insensitive comparisons, and WSL mount translation.
- [ ] Add separate allowlists for Windows commands, service names, process actions, and accessible roots; do not inherit WSL permissions implicitly.
- [ ] Require local approval for service/process mutation, clipboard content access, Windows writes, and script execution.
- [ ] Add Windows-specific audit fields without recording clipboard contents, script bodies, credentials, or command output.
- [ ] Validate with Windows 11 + WSL2 under both `virtioproxy` and documented compatible networking modes; Hands must not require mirrored networking.

## v1.4.0 — Windows Computer Use

- [ ] Add one compact `hands_computer` tool with explicit actions such as `observe`, `click`, `double_click`, `type`, `key`, `scroll`, `drag`, `open`, and `wait`.
- [ ] Implement a signed/versioned Windows helper using supported Windows capture and UI Automation APIs; keep it bound to the local machine and authenticate WSL2 requests.
- [ ] Enforce a window/application allowlist, foreground-window verification, coordinate bounds, stale-observation rejection, and per-action timeouts.
- [ ] Refuse password, PIN, MFA, credential-manager, secure-desktop, UAC, payment, and other protected-field interaction.
- [ ] Require approval for high-impact UI actions and never infer approval from visible page text or model output.
- [ ] Treat screenshots, OCR, accessibility trees, and application text as untrusted input and document prompt-injection handling.
- [ ] Provide an emergency stop and visible local activity indicator; cancellation must prevent queued follow-up UI actions.
- [ ] Run live acceptance first against disposable applications and fixtures, never a maintainer's real credential or payment workflow.

## v1.5.0 — Routing, fallback, and operational hardening

- [ ] Publish a capability contract that lets ChatGPT choose Hermes, Codex, or Local Hands without circular orchestration.
- [ ] Report normalized backend reasons such as `available`, `disabled`, `unreachable`, `usage_limit`, `quota_exhausted`, and `policy_blocked` without exposing secrets.
- [ ] Document direct routing: short deterministic work to Hands, coding work to Codex, and long agentic work to Hermes; Hands itself never delegates back to an agent.
- [ ] Add cross-backend correlation IDs for audit only; never share prompts, outputs, credentials, or approval authority across backends.
- [ ] Add load, restart, expiry, cancellation-race, disk-full, truncated-output, and audit-rotation tests for all Hands adapters.
- [ ] Complete threat-model review, upgrade/rollback instructions, compatibility matrix, operations runbook, and a signed release acceptance record.

## Release gates applying to every Local Hands version

- Documentation, version references, tool counts, configuration examples, tests, checksums, and release notes must be updated before tagging or publishing release assets.
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
- Multi-user credential management, payment automation, secure-desktop control, or unattended credential entry
