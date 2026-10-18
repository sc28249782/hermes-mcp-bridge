# Hermes MCP Bridge

Securely connect ChatGPT to a local Hermes Agent and Codex CLI running in WSL2, through an OpenAI Secure MCP Tunnel.

The bridge is a controlled local execution boundary, not a general remote shell. The current signed production release is **v1.2.3**. It has 27 MCP tools, local-only version/provenance reporting, and durable Codex worker supervision that preserves `running` while a worker is unavailable but its child remains alive.

Released **2026-10-18** as **v1.2.4** with an GPG-signed annotated tag on `2133056`. It adds the disabled-by-default OpenCode health adapter (PR #34; discovery stays at the canonical 27 tools unless an operator opts in) and the legacy stdio discovery guard (PR #35). Release assets plus an external SHA256SUMS are published at https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.4 (ZIP SHA-256 `e6deb0e6ab16d669836b0e361e2e875858e19597ef35dc7e4fc19010a6a5f3a9`, download re-verified). MCP Events is not included (deferred, BLOCKED). Production deployment remains v1.2.3; this release requires no rollout, service, or config change. The installation and upgrade instructions still default to the released v1.2.3.

## OpenCode health (disabled by default)

The bridge includes a disabled-by-default OpenCode adapter (`opencode_core.py`). Discovery stays at the canonical 27 tools while it is disabled. Enabling it registers one additive read-only tool, `opencode_health` (28 tools).

- Configuration lives in `bridge-config.json` under `opencode`: `enabled` (default `false`), `binary` (absolute path to the OpenCode executable, required when enabled), `version_timeout_seconds` (1-120, default 10), and `max_output_bytes` (1024-1048576, default 65536). Unknown keys are warned and ignored.
- When disabled, the bridge fails closed: it never spawns a process and makes no network, model, or authentication call.
- The health check runs one bounded `--version` probe with a fixed argv list, `shell` disabled, a hard timeout, and a per-stream memory cap. The probe group always receives `SIGTERM` and then `SIGKILL`, including descendants that hold pipes or ignore `SIGTERM`. Every group signal is delivered while the leader is still unreaped (its zombie pins the PID/PGID), exit is observed with a nonreaping `waitid` bounded by the probe deadline, and the leader is reaped once by handle after the final `SIGKILL`; if leader ownership is unknown, no signal is sent.
- The configured executable is not a sandbox. It runs with the full user privileges of the bridge process and can read global configuration and credentials.
- This is a foundation only. Task submission, sessions, JSON event output, cancellation, and permission handling are not implemented. No public submit tool exists until safe permissions are verified. Never pass `--auto` to a bridge-run OpenCode process.

## Legacy stdio discovery guard

On the legacy stdio serve path (`./bridge.sh serve`), an incoming `server/discover` request is answered at the stream boundary with a JSON-RPC `-32601` error carrying the original request id and no echoed parameters. The reply is an error, not a capability: discovery stays at the canonical 27 tools (28 with `opencode` enabled), repeated probes do not flood logs, and every other message is forwarded to the SDK unchanged. See SPEC.md section 17.

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
- [Specification](docs/SPEC.md), [testing](docs/TESTING.md), [release status](docs/RELEASE-STATUS-TH.md), and [changelog](docs/CHANGELOG.md)
- [v1.x acceptance checklist](docs/V1-ACCEPTANCE-TH.md), [compatibility matrix](docs/COMPATIBILITY-MATRIX-TH.md), and [release runbook](docs/RELEASE-RUNBOOK-TH.md)
- [Security](docs/SECURITY.md) and [contributing](docs/CONTRIBUTING.md)
- [Roadmap](docs/ROADMAP.md)
- [STE-inspired writing style guide](docs/WRITING-STYLE.md)
- [Local Hands architecture and security](docs/LOCAL-HANDS-ARCHITECTURE-TH.md)
- [Local Hands implementation and acceptance plan](docs/LOCAL-HANDS-IMPLEMENTATION-PLAN-TH.md)
- [Local Hands v1.2.0 read-only setup](docs/LOCAL-HANDS-V1.2-SETUP-TH.md) and [WSL2/DrvFS live acceptance](docs/LOCAL-HANDS-V1.2-LIVE-ACCEPTANCE-TH.md)
- [ADR-0001: Local Hands foundation contracts](docs/adr/0001-local-hands-foundation.md)
- [Third-party notices and design attribution](THIRD_PARTY_NOTICES.md)

## License

Licensed under [Apache License 2.0](LICENSE).

The Local Hands design was inspired in part by [Endeavor Hands](https://github.com/halochamp/Endeavor_Hands) (MIT). No Endeavor Hands source code or assets are incorporated in the current runtime; see [Third-Party Notices](THIRD_PARTY_NOTICES.md).
