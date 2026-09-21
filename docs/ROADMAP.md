# Roadmap

## Completed

- [x] v0.4.1 — WSL2 live acceptance for the Hermes and Codex paths
- [x] v0.5.0 — redacted audit logging, diagnostics, rotation/retention, and recovery visibility

## v0.6.0 — Policy and workflow controls

- [x] Per-workspace sandbox, timeout, prompt-size, and concurrency policy
- [x] Approval TTL and expiry for pending write jobs
- [x] Approval context with workspace and policy root
- [x] Optional pre-flight prompt guardrails (documented as non-sandbox)
- [x] Redacted audit export and security constraints documentation

## v0.7.0 — Codex model policy

- [x] Per-task model and reasoning-effort request through the Codex bridge
- [x] Allowlist at Codex default or workspace scope; secure default disables overrides
- [x] Persist and audit requested execution preferences without recording prompts or outputs
- [x] Retain separate local approval for every workspace-write task

## v0.8.0 — Process-lifecycle hardening

- [x] Do not report an unobserved post-restart Codex exit as `completed`; expose `unknown_exit`
- [x] Make Codex cancellation race-safe: SIGTERM, bounded grace period, SIGKILL fallback, process-death verification, and atomic terminal-state transition
- [x] Prevent `_start()` failures from leaving permanent `queued` jobs; record a failed lifecycle/audit outcome
- [x] Make workspace concurrency reservation atomic
- [x] Add a Codex runtime watchdog that enforces `max_runtime_seconds` without requiring status polling
- [x] Correct type annotations, remove CLI-to-private-method coupling, and add regression tests for lifecycle races
- [x] Add shellcheck to CI while retaining `bash -n`

## v0.9.0 — Operational state and configuration hardening

- [x] Report Hermes run age and configurable stale status without claiming that an upstream run was stopped
- [x] Report waiting Hermes approvals past a configurable local threshold as `approval_stale`; do not auto-deny upstream work
- [x] Add versioned `bridge-config.json` schema validation and deterministic migration guidance; surface unknown keys as doctor warnings
- [x] Add a fast local-only `bridge_status` heartbeat tool that does not call Hermes or Codex upstream APIs
- [x] Add coverage for Hermes deny resolution and usage-limit validation

## v1.0.0 — Production baseline and release integrity

- [x] Compatibility matrix for Hermes, Codex CLI, Python, WSL2, and tunnel-client
- [x] Repeatable end-to-end acceptance checklist for all tools, including configured Codex model/effort policy
- [x] Security review and verified upgrade/migration paths
- [x] Incident/runbook and reproducible-release documentation
- [x] Publish SHA-256SUMS and a signed, GitHub-verified release tag; document verification of the release archive before extraction

## v1.1.0 — Hermes approval-event integration

- [ ] Run a protocol POC against the installed Hermes API-server: confirm the required run-event SSE subscription, approval event shape, reconnect behavior, and exact response contract
- [ ] Subscribe only to approval/status events for bridge-owned runs; do not add general output streaming through MCP
- [ ] Persist redacted approval state and exact request ID locally; expose safe waiting/delivery status through `hermes_task_status`
- [ ] Keep approval and denial in the local interactive CLI only; re-read the exact request ID immediately before `POST /v1/runs/{run_id}/approval` to prevent TOCTOU
- [ ] Fail closed on missing capability, event-delivery failure, stale event, or reconnect uncertainty; never auto-approve or expose a ChatGPT MCP approval tool
- [ ] Add fake-server SSE/approval contract tests and WSL2 live approval, deny, reconnect, and expiry acceptance

## Non-goals

- Public inbound service, unrestricted remote shell, or unrestricted filesystem/network access
- Transmitting Hermes/OpenAI credentials through MCP
- Allowing an agent to approve its own Codex write job
- Multi-user credential management, streaming transport, or provider-cost estimates
- Streaming Hermes output over MCP; v1.1.0 SSE is approval/status delivery only
