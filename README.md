# Hermes MCP Bridge

> Securely connect ChatGPT to a local Hermes Agent and Codex CLI running in WSL2.

[![Tests](https://github.com/sc28249782/hermes-mcp-bridge/actions/workflows/tests.yml/badge.svg)](https://github.com/sc28249782/hermes-mcp-bridge/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**Hermes MCP Bridge** is a local, stdio-based MCP bridge for controlled work on a user's own WSL2 machine. It exposes Hermes task operations and a permission-gated Codex execution layer through an OpenAI Secure MCP Tunnel.

Project origin: [ChatGPT conversation](https://chatgpt.com/share/6aae9c83-db48-83ec-ba0c-4ab5e3b088a7)

## What it provides

| Area | Capabilities |
|---|---|
| Hermes | Health checks, model catalog, task submit/status/result/cancel, recent tasks, usage summary and export |
| Codex / WSL2 | Health, submit, status, paginated result, cancel, and recent jobs |
| Security | Workspace allowlist, symlink-escape protection, explicit local approval for write jobs, fixed argv invocation, timeout and prompt-size limits |

The v0.4.0 design exposes **16 MCP tools**: 10 Hermes tools and 6 Codex tools.

## Security model

Codex jobs are deliberately restricted:

- Allowed sandboxes: `read-only` and `workspace-write` only.
- `danger-full-access` is rejected.
- Every workspace must be explicitly listed in `codex.allowed_workspaces`.
- A `workspace-write` job remains pending until a person approves it locally with `codex-approve`.
- An MCP client cannot approve its own job.
- Codex is started without a shell, using fixed argument handling.

Never commit `bridge-config.json`, `state/`, logs, virtual environments, runtime API keys, or Hermes secrets.

## Architecture

```text
ChatGPT
  → OpenAI Secure MCP Tunnel
  → bridge.sh (stdio MCP)
  → Hermes API on 127.0.0.1:8642
  → Codex CLI / approved WSL2 workspaces
```

## Quick start

> Run these commands as your normal WSL2 user; do not use `sudo`.

```bash
unzip hermes-mcp-bridge-v0.4.0.zip
cd hermes-mcp-bridge-v0.4.0
bash install.sh

./bridge.sh doctor
./bridge.sh codex-doctor
```

Then configure the allowed project roots in `bridge-config.json`:

```json
{
  "api_url": "http://127.0.0.1:8642",
  "hermes_env": "/home/USER/.hermes/.env",
  "hermes_config": "/home/USER/.hermes/config.yaml",
  "codex": {
    "allowed_workspaces": [
      "/home/USER/projects/example"
    ]
  }
}
```

Start the Secure MCP Tunnel after completing its one-time configuration:

```bash
bash tunnel.sh run
```

See the Thai documentation for the full setup and live acceptance procedure:

- [Installation guide](README-TH.md)
- [Codex / WSL2 configuration](CODEX-WSL2-TH.md)
- [Upgrade guide](UPGRADE-TH.md)
- [Technical architecture](HERMES-MCP-BRIDGE-TECHNICAL-ARCHITECTURE-TH.md)
- [Live acceptance checklist](LIVE-ACCEPTANCE-TH.md)
- [Security policy](SECURITY.md)
- [Contributing guide](CONTRIBUTING.md)

## Status

The automated v0.4.0 validation covers Hermes regression, Codex permission/process behavior, MCP discovery, and tunnel security. Perform the live WSL2 acceptance checklist before treating Codex execution as production-ready.

## License

Licensed under [Apache License 2.0](LICENSE).
