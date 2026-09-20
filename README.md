# Hermes MCP Bridge

Securely connect ChatGPT to a local Hermes Agent and Codex CLI running in WSL2, through an OpenAI Secure MCP Tunnel.

The bridge provides a controlled local execution boundary rather than a general remote shell. v0.7.0 exposes 18 MCP tools: 10 Hermes tools, 6 Codex tools, and two read-only operations tools.

## Safety model

- Hermes uses its authenticated local Runs API and its own approval policy.
- Codex can use only explicitly allowlisted workspaces.
- Codex permits only `read-only` and `workspace-write`; `danger-full-access` is rejected.
- Every write job requires interactive approval in the local WSL2 terminal.
- Workspace policies can restrict sandbox modes, runtime, prompt size, concurrency, approval lifetime, and configured pre-flight prompt patterns.
- An optional per-workspace allowlist governs Codex model and reasoning-effort overrides; omitting both keeps the local Codex CLI defaults.
- Audit logs are redacted, local-only, rotating JSONL files. Secrets, prompts, and outputs are not written to them.

## Start here

```bash
bash install.sh
./bridge.sh doctor
./bridge.sh codex-doctor
./bridge.sh diagnostics
```

Run `bash tunnel.sh init tunnel_YOUR_ID --force` when changing the bridge directory or version; it updates the `hermes-wsl` profile and starts the tunnel. Later starts use `bash tunnel.sh run`.

## Documentation

- [Project origin](docs/PROJECT-ORIGIN.md) and [project history](docs/PROJECT-HISTORY.md)
- [Thai installation guide](docs/README-TH.md)
- [Codex / WSL2 policy](docs/CODEX-WSL2-TH.md)
- [Operations guide](docs/OPERATIONS-TH.md)
- [Upgrade guide](docs/UPGRADE-TH.md)
- [Technical architecture](docs/HERMES-MCP-BRIDGE-TECHNICAL-ARCHITECTURE-TH.md)
- [Testing](docs/TESTING.md), [release status](docs/RELEASE-STATUS-TH.md), and [changelog](docs/CHANGELOG.md)
- [Security](docs/SECURITY.md) and [contributing](docs/CONTRIBUTING.md)
- [Roadmap](docs/ROADMAP.md)

## License

Licensed under [Apache License 2.0](LICENSE).
