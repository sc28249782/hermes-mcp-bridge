# Project history

For the project purpose and architectural choices, see [Project origin](PROJECT-ORIGIN.md).

| Release | Milestone | Outcome |
|---|---|---|
| v0.1.0 | Hermes Runs API bridge | Established authenticated stdio MCP, request ownership, idempotency, status/result, and cancellation. |
| v0.1.1 | Operational hardening | Improved installation and tunnel operation practices. |
| v0.2.0–v0.2.1 | Model-aware execution and tunnel recovery | Added per-task model choices, model catalog, safe request fingerprints, and profile replacement with `--force`. |
| v0.3.0–v0.3.2 | Usage and live acceptance | Added sanitized usage data and validated all 10 Hermes tools through the local Secure MCP Tunnel. |
| v0.4.0–v0.4.1 | Permission-gated Codex / WSL2 | Added the 6 Codex tools and completed WSL2 live acceptance. |
| v0.5.0 | Operations and reliability | Added redacted rotating audit logs, diagnostics, and restart-recovery visibility. |

This repository is the source of record for implementation, tests, issues, releases, and project documentation.
