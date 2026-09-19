# Project origin

## Why this project exists

Hermes MCP Bridge was created to let a user work with a locally running **Hermes Agent** from ChatGPT while keeping execution under the user’s control.

The original environment is a Windows 11 workstation with Ubuntu 24.04 on WSL2. Hermes runs locally and exposes an authenticated Runs API only on loopback. ChatGPT reaches the bridge through an OpenAI Secure MCP Tunnel; it does not receive direct network access to the WSL2 host.

The project later expanded to include a carefully constrained Codex CLI path for local development work in explicitly approved WSL2 workspaces.

## The problem it solves

Local agents are useful for inspecting projects, running tests, and making changes, but a direct “chat-to-shell” connection creates unacceptable risk. The bridge provides a narrow MCP interface instead of a general remote shell:

- ChatGPT can submit and inspect declared jobs.
- Hermes owns its own run lifecycle and approval policy.
- Codex is restricted to declared workspaces and approved sandbox modes.
- A local person must approve every Codex job that may modify files.
- Secrets, runtime state, and local machine paths are not published as project artifacts.

## Design decisions

| Decision | Rationale |
|---|---|
| stdio MCP bridge | Keeps the tool boundary local and compatible with Secure MCP Tunnel. |
| Hermes Runs API over HTTP | Reuses Hermes run lifecycle, authentication, idempotency, and ownership semantics. |
| Secure MCP Tunnel | Avoids exposing the local API or WSL2 services to the public internet. |
| Separate Codex job layer | Lets Codex have independent workspace, sandbox, timeout, result, and approval controls. |
| Local approval for write jobs | Prevents an MCP client or agent from authorizing its own filesystem changes. |
| No `danger-full-access` | Preserves a hard boundary against unrestricted host access. |

## Scope

The project is intended for a user-controlled WSL2 workstation, not for multi-tenant remote command execution. Its public repository contains source, tests, release notes, documentation, and reproducible configuration examples only.

For release-by-release evolution, see [Project history](PROJECT-HISTORY.md). For planned work, see [Roadmap](ROADMAP.md).
