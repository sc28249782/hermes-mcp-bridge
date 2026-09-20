# Project origin

Hermes MCP Bridge was created to let ChatGPT work with a locally running Hermes Agent on a user-controlled Windows 11 and Ubuntu 24.04 WSL2 workstation. Hermes exposes an authenticated loopback Runs API; ChatGPT reaches the local stdio bridge through an OpenAI Secure MCP Tunnel, without a public inbound service.

The project later added Codex CLI for carefully scoped local development work. It deliberately avoids a general remote shell: Codex is limited to approved WSL2 workspaces and sandbox modes, while any file-writing job needs an explicit local human approval.

## Design decisions

| Decision | Rationale |
|---|---|
| stdio MCP bridge | A small, local tool boundary compatible with Secure MCP Tunnel. |
| Hermes Runs API | Reuses Hermes authentication, idempotency, run ownership, status, result, and cancellation semantics. |
| Separate Codex runner | Adds independent workspace, timeout, job-state, audit, and approval controls. |
| No `danger-full-access` | Retains a firm limit on host access. |
| Local redacted audit | Supports troubleshooting without publishing secrets, prompts, or outputs. |

For release-by-release evolution, see [Project history](PROJECT-HISTORY.md). For planned work, see [Roadmap](ROADMAP.md).
