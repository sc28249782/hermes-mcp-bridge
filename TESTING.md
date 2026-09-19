# Validation plan — v0.4.0 (2026-09-19)

Target contract reviewed: Hermes v0.21.1, commit 8d79c2ff.

Installer repair: added pip presence detection and ensurepip bootstrap for an existing pip-less venv in the non-uv path. v0.2.0 adds a safe YAML dependency for model metadata.

- Core tests cover authenticated discovery, run lifecycle, follow-up sessions, pagination, key redaction, persistence, duplicate suppression, durable recovery, unsafe replay rejection, run/session ownership, approvals, cached output, stop, loopback/redirect guards, model override fingerprinting, follow-up model policy, model discovery and SQLite migration.
- MCP stdio integration covers initialization, discovery of 16 tools, model discovery, model-aware submission, usage tools, polling, output retrieval and foreign run rejection.
- Codex tests cover allowlist enforcement, symlink escape rejection, write approval staging, immediate read-only start, forbidden sandbox modes, denial of pending jobs และ fixed-argv subprocess/result capture.
- Tunnel tests cover secure key loading/mode and generated systemd unit without embedded key.
- Shell syntax checks are required for install.sh, bridge.sh and tunnel.sh.

The test server mocks the Hermes HTTP contract; no live model or user workstation was contacted. No live OpenAI tunnel registration or end-to-end ChatGPT test has been performed. install.sh and tunnel.sh require user-side validation; shell syntax checking does not prove runtime integration.

Live acceptance completed on 2026-09-14: all 10 tools were invoked through the Secure MCP Tunnel; cancel was verified on a running `sleep 60` task and reached `cancelled`. See `LIVE-ACCEPTANCE-TH.md`.
