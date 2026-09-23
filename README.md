# Hermes MCP Bridge

Securely connect ChatGPT to a local Hermes Agent and Codex CLI running in WSL2, through an OpenAI Secure MCP Tunnel.

The bridge is a controlled local execution boundary, not a general remote shell. The current signed, GitHub-verified production release is **v1.2.1** with 26 MCP tools. The in-development **v1.2.2 candidate** adds a local-only version/provenance surface and raises its discovery contract to 27 tools; it is not a production release until its live-acceptance and signed-release gates pass.

## Safety model

- Hermes uses its authenticated local Runs API and its own approval policy.
- An advertised Hermes approval-response endpoint does not by itself prove that the API profile can create an interactive approval session; v1.1.0 SSE approval integration is deferred pending an upstream contract.
- Codex can use only explicitly allowlisted workspaces.
- Codex permits only `read-only` and `workspace-write`; `danger-full-access` is rejected.
- Every write job requires interactive approval in the local WSL2 terminal.
- Approved Codex work is supervised by a durable local worker, which persists its terminal outcome independently of the tunnel process.
- Workspace policies can restrict sandbox modes, runtime, prompt size, concurrency, approval lifetime, and configured pre-flight prompt patterns.
- Audit logs are redacted, local-only, rotating JSONL files. Secrets, prompts, and outputs are not written to them.
- A persistent Codex watchdog enforces each workspace runtime limit even when no client polls job status.

## Start here

```bash
bash install.sh
./bridge.sh doctor
./bridge.sh codex-doctor
./bridge.sh diagnostics
./bridge.sh version
```

`./bridge.sh version` is local-only: it does not contact Hermes, Codex, the tunnel, GitHub, or another network service. It reports the installed bridge version, release/provenance fields, config-schema version, and MCP discovery contract. The MCP equivalent is the read-only `bridge_version` tool.

Run `bash tunnel.sh init tunnel_YOUR_ID --force` when changing the bridge directory or version; it updates the `hermes-wsl` profile and starts the tunnel. Later starts use `bash tunnel.sh run`.

## Documentation

- [Project origin](docs/PROJECT-ORIGIN.md) and [project history](docs/PROJECT-HISTORY.md)
- [Thai installation guide](docs/README-TH.md)
- [Codex / WSL2 policy](docs/CODEX-WSL2-TH.md)
- [Operations guide](docs/OPERATIONS-TH.md)
- [Upgrade guide](docs/UPGRADE-TH.md)
- [Technical architecture](docs/HERMES-MCP-BRIDGE-TECHNICAL-ARCHITECTURE-TH.md)
- [Testing](docs/TESTING.md), [release status](docs/RELEASE-STATUS-TH.md), and [changelog](docs/CHANGELOG.md)
- [v1.x acceptance checklist](docs/V1-ACCEPTANCE-TH.md), [compatibility matrix](docs/COMPATIBILITY-MATRIX-TH.md), and [release runbook](docs/RELEASE-RUNBOOK-TH.md)
- [Security](docs/SECURITY.md) and [contributing](docs/CONTRIBUTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Local Hands architecture and security](docs/LOCAL-HANDS-ARCHITECTURE-TH.md)
- [Local Hands implementation and acceptance plan](docs/LOCAL-HANDS-IMPLEMENTATION-PLAN-TH.md)
- [Local Hands v1.2.0 read-only setup](docs/LOCAL-HANDS-V1.2-SETUP-TH.md) and [WSL2/DrvFS live acceptance](docs/LOCAL-HANDS-V1.2-LIVE-ACCEPTANCE-TH.md)
- [ADR-0001: Local Hands foundation contracts](docs/adr/0001-local-hands-foundation.md)
- [Third-party notices and design attribution](THIRD_PARTY_NOTICES.md)

## License

Licensed under [Apache License 2.0](LICENSE).

The Local Hands design was inspired in part by [Endeavor Hands](https://github.com/halochamp/Endeavor_Hands) (MIT). No Endeavor Hands source code or assets are incorporated in the current runtime; see [Third-Party Notices](THIRD_PARTY_NOTICES.md).
