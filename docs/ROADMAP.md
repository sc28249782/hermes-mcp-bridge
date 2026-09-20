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

## v1.0.0 — Production baseline

- [ ] Compatibility matrix for Hermes, Codex CLI, Python, WSL2, and tunnel-client
- [ ] Repeatable end-to-end acceptance for all tools
- [ ] Security review and verified upgrade/migration paths
- [ ] Reproducible release process and incident/runbook documentation

## Non-goals

- Public inbound service, unrestricted remote shell, or unrestricted filesystem/network access
- Transmitting Hermes/OpenAI credentials through MCP
- Allowing an agent to approve its own Codex write job
