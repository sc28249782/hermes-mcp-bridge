# Project origin

Hermes MCP Bridge was created to let ChatGPT work with a locally running Hermes Agent on a user-controlled Windows 11 and Ubuntu 24.04 WSL2 workstation. Hermes exposes an authenticated loopback Runs API; ChatGPT reaches the local stdio bridge through an OpenAI Secure MCP Tunnel, without a public inbound service.

The project later added Codex CLI for carefully scoped local development work. It deliberately avoids a general remote shell: Codex is limited to approved WSL2 workspaces and sandbox modes, while any file-writing job needs an explicit local human approval.

## Local Hands design inspiration

The post-v1.0.1 Local Hands roadmap was inspired in part by [halochamp/Endeavor_Hands](https://github.com/halochamp/Endeavor_Hands), especially its separation of ChatGPT reasoning from local-machine primitives and its documented experience with deletion refusal, working-copy redirects, computer post-action verification, and consent limitations.

Endeavor Hands is MIT-licensed, Copyright (c) 2026 Poomwat Jarussri. Local Hands is a new Windows/WSL2 design with a different allowlist, approval, audit, and backend-independence model. As of the design stage, no Endeavor Hands source code or assets have been incorporated. If source is adapted later, the upstream copyright and MIT permission notice must be preserved in the affected source/distribution and recorded in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Design decisions

| Decision | Rationale |
|---|---|
| stdio MCP bridge | A small, local tool boundary compatible with Secure MCP Tunnel. |
| Hermes Runs API | Reuses Hermes authentication, idempotency, run ownership, status, result, and cancellation semantics. |
| Separate Codex runner | Adds independent workspace, timeout, job-state, audit, and approval controls. |
| Local Hands as sibling backend | Keeps deterministic local primitives usable without invoking Hermes or Codex while preserving independent policy and health. |
| No `danger-full-access` | Retains a firm limit on host access. |
| Local redacted audit | Supports troubleshooting without publishing secrets, prompts, or outputs. |

For release-by-release evolution, see [Project history](PROJECT-HISTORY.md). For planned work, see [Roadmap](ROADMAP.md).
