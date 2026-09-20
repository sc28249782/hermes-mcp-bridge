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

- [ ] Do not report an unobserved post-restart Codex exit as `completed`; expose a distinct `unknown_exit` outcome or verified JSONL terminal evidence
- [ ] Make Codex cancellation race-safe: SIGTERM, bounded grace period, SIGKILL fallback, process-death verification, and atomic terminal-state transition
- [ ] Prevent `_start()` failures from leaving permanent `queued` jobs; record a failed lifecycle/audit outcome
- [ ] Make workspace concurrency reservation atomic
- [ ] Add a Codex runtime watchdog that enforces `max_runtime_seconds` without requiring status polling
- [ ] Correct type annotations, remove CLI-to-private-method coupling, and add regression tests for lifecycle races
- [ ] Add shellcheck to CI while retaining `bash -n`

## v0.9.0 — Operational state and configuration hardening

- [ ] Report Hermes run age and configurable stale status without claiming that an upstream run was stopped
- [ ] Report waiting Hermes approvals past a configurable local threshold as `approval_stale`; do not auto-deny upstream work
- [ ] Add versioned `bridge-config.json` schema validation and deterministic migration guidance; surface unknown keys as doctor warnings
- [ ] Add a fast local-only `bridge_status` heartbeat tool that does not call Hermes or Codex upstream APIs
- [ ] Add coverage for Hermes deny resolution and usage-limit validation

## v1.0.0 — Production baseline and release integrity

- [ ] Compatibility matrix for Hermes, Codex CLI, Python, WSL2, and tunnel-client
- [ ] Repeatable end-to-end acceptance for all tools, including configured Codex model/effort policy
- [ ] Security review and verified upgrade/migration paths
- [ ] Incident/runbook and reproducible-release documentation
- [ ] Publish SHA-256SUMS and a signed release tag; document verification of the release archive before extraction

## Non-goals

- Public inbound service, unrestricted remote shell, or unrestricted filesystem/network access
- Transmitting Hermes/OpenAI credentials through MCP
- Allowing an agent to approve its own Codex write job
- Multi-user credential management, streaming transport, or provider-cost estimates
