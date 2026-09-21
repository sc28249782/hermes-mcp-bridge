# Validation plan — v1.0.0 (2026-09-21)

Target contract reviewed: Hermes v0.21.1, commit 8d79c2ff.

Installer coverage includes pip presence detection and ensurepip bootstrap for an existing pip-less venv in the non-uv path.

- Core tests cover authenticated discovery, run lifecycle, follow-up sessions, pagination, key redaction, persistence, duplicate suppression, durable recovery, unsafe replay rejection, run/session ownership, approvals, cached output, stop, loopback/redirect guards, model override fingerprinting, follow-up model policy, model discovery and SQLite migration.
- MCP stdio integration covers initialization, discovery of 19 tools, diagnostics, local-only heartbeat, model discovery, model-aware submission, usage tools, polling, output retrieval and foreign run rejection.
- Codex tests cover audit redaction/rotation, recovery visibility after a bridge restart, `unknown_exit`, atomic concurrency reservation, start failure, cancellation/timeout races, watchdog enforcement, workspace allowlist enforcement, symlink escape rejection, write approval staging, fixed-argv subprocess/result capture, and model/reasoning policy forwarding.
- Tunnel tests cover secure key loading/mode and generated systemd unit without embedded key.
- CI runs shellcheck and `bash -n` for install.sh, bridge.sh and tunnel.sh.

The test server mocks the Hermes HTTP contract; it does not replace workstation/tunnel validation. Shell syntax checking does not prove runtime integration.

Live acceptance is recorded in `LIVE-ACCEPTANCE-TH.md`: v1.0.0 RC2 validated 19-tool discovery, Hermes idempotent read-only execution, Codex `gpt-5.6-sol` + `low`, local workspace-write approval, and cancellation through the Secure MCP Tunnel. The final v1.0.0 deployment health check also passed with no configuration warnings.
