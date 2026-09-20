# Roadmap

## Completed

- [x] v0.4.1 — WSL2 live acceptance for the Hermes and Codex paths
- [x] v0.5.0 — redacted audit logging, diagnostics, rotation/retention, and recovery visibility

## v0.6.0 — Policy and workflow controls

- [ ] Per-workspace sandbox, timeout, prompt-size, and concurrency policy
- [ ] Approval TTL and expiry for pending write jobs
- [ ] Approval context with workspace, task summary, and expected impact
- [ ] Optional command/category denylist
- [ ] Redacted audit export and threat-model review

## v1.0.0 — Production baseline

- [ ] Compatibility matrix for Hermes, Codex CLI, Python, WSL2, and tunnel-client
- [ ] Repeatable end-to-end acceptance for all tools
- [ ] Security review and verified upgrade/migration paths
- [ ] Reproducible release process and incident/runbook documentation

## Non-goals

- Public inbound service, unrestricted remote shell, or unrestricted filesystem/network access
- Transmitting Hermes/OpenAI credentials through MCP
- Allowing an agent to approve its own Codex write job
