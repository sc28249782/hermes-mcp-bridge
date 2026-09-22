# Validation plan — v1.2.1 (2026-09-22)

Target contract reviewed: Hermes v0.21.1, commit 8d79c2ff.

## MCP tool contract (canonical count)

The canonical discovery contract for v1.2.1 is **26 tools**: existing 22 plus four explicit context tools (`bridge_context_create`, `bridge_context_status`, `bridge_context_recent`, `bridge_context_close`). Other documents should refer here instead of maintaining an independent count.

## Unreleased v1.2.1 context and Hands coverage

- `tests/test_hands.py` covers disabled stable results, additive schema validation, dependency direction, workspace secret-name protection, protected-name case folding, traversal, symlink escape, binary/oversize/hard-link rejection, case-colliding entries, strict-resolver failure, and audit content/path non-leakage.
- `tests/test_mcp.py` verifies discovery of 26 tools, the three read-only Hands tools, and explicit context creation/binding against a disposable fixture. `tests/test_hands_fallback_mcp.py` proves health/list/read continue to work when the Hermes transport is unreachable and the configured Codex binary is absent.
- The Hands path suite includes a deterministic generative invariant: only explicit safe fixture paths may return content; generated traversal, absolute, separator, protected-name, and missing-path candidates must be denied.
- Automated tests are necessary but do not satisfy the remaining WSL2/ext4/DrvFS and Hermes-off/Codex-unavailable live-acceptance gates for v1.2.0.

Installer coverage includes pip presence detection and ensurepip bootstrap for an existing pip-less venv in the non-uv path.

- Core tests cover authenticated discovery, run lifecycle, follow-up sessions, pagination, key redaction, persistence, duplicate suppression, durable recovery, unsafe replay rejection, run/session ownership, approvals, cached output, stop, loopback/redirect guards, model override fingerprinting, follow-up model policy, model discovery and SQLite migration.
- MCP stdio integration covers initialization and the canonical 26-tool discovery contract, diagnostics, local-only heartbeat, model discovery, model-aware submission, usage tools, polling, output retrieval and foreign run rejection.
- Codex tests cover audit redaction/rotation, recovery visibility after a bridge restart, `unknown_exit`, atomic concurrency reservation, start failure, cancellation/timeout races, watchdog enforcement, workspace allowlist enforcement, symlink escape rejection, write approval staging, fixed-argv subprocess/result capture, and model/reasoning policy forwarding.
- Tunnel tests cover secure key loading/mode and generated systemd unit without embedded key.
- CI runs shellcheck and `bash -n` for install.sh, bridge.sh and tunnel.sh.

The test server mocks the Hermes HTTP contract; it does not replace workstation/tunnel validation. Shell syntax checking does not prove runtime integration.

Live acceptance is recorded in `LIVE-ACCEPTANCE-TH.md`: v1.0.0 RC2 validated 19-tool discovery, Hermes idempotent read-only execution, Codex `gpt-5.6-sol` + `low`, local workspace-write approval, and cancellation through the Secure MCP Tunnel. v1.0.1 then passed its WSL2 deployment health check and a no-write/no-network Codex read-only acceptance with no configuration warnings.
