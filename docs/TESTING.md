# Validation plan — v0.7.0 (2026-09-20)

Target contract reviewed: Hermes v0.21.1, commit 8d79c2ff.

Installer coverage includes pip presence detection and ensurepip bootstrap for an existing pip-less venv in the non-uv path.

- Core tests cover authenticated discovery, run lifecycle, follow-up sessions, pagination, key redaction, persistence, duplicate suppression, durable recovery, unsafe replay rejection, run/session ownership, approvals, cached output, stop, loopback/redirect guards, model override fingerprinting, follow-up model policy, model discovery and SQLite migration.
- MCP stdio integration covers initialization, discovery of 18 tools, diagnostics, model discovery, model-aware submission, usage tools, polling, output retrieval and foreign run rejection.
- Codex tests cover audit redaction/rotation, recovery visibility after a bridge restart, workspace allowlist enforcement, symlink escape rejection, write approval staging, immediate read-only start, forbidden sandbox modes, denial of pending jobs, fixed-argv subprocess/result capture, and model/reasoning policy forwarding.
- Tunnel tests cover secure key loading/mode and generated systemd unit without embedded key.
- Shell syntax checks are required for install.sh, bridge.sh and tunnel.sh.

The test server mocks the Hermes HTTP contract; it does not replace workstation/tunnel validation. Shell syntax checking does not prove runtime integration.

Live acceptance is recorded in `LIVE-ACCEPTANCE-TH.md`: the Hermes 10-tool path was validated in v0.3.2; Codex workspace controls were validated in v0.4–v0.6; v0.7.0 validated default execution and `gpt-5.6-sol` + `high` through the Secure MCP Tunnel.
