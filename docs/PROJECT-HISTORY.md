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
| v0.6.0 | Policy and workflow controls | Added per-workspace execution policy, approval expiry/context, redacted audit export, and pre-flight prompt guardrails. |
| v0.7.0 | Codex model policy | Added allowlisted per-task Codex model and reasoning-effort overrides, with state/audit visibility and unchanged write approval. |
| v0.8.0 | Process-lifecycle hardening | Added watchdog-enforced runtime limits, atomic concurrency reservation, safer cancellation, and explicit unknown recovered exits. |
| v0.9.0–v0.9.1 | Operational state and Hermes capability hardening | Added local heartbeat, stale labels, versioned configuration validation, and canonical `run_approval_response` capability detection. |
| v1.0.0 | Production baseline | Completed compatibility/release documentation and full WSL2 acceptance; published archive checksum and signed, GitHub-verified release tag. |
| v1.0.1 | Maintenance validation | Aligned approval-TTL schema validation with runtime policy; published a signed, checksum-verified archive and completed WSL2 read-only acceptance. |
| v1.2.0 | Local Hands read-only | Added the opt-in read-only Local Hands backend (`hands_health`/`hands_list`/`hands_read`, 22-tool discovery), strict `openat2` workspace containment, and ext4/DrvFS live acceptance. |
| v1.2.1 | Explicit work contexts | Added metadata-only work contexts (four context tools, 26-tool discovery) with Hermes session and Codex metadata binding. |
| v1.2.2 | Bridge version and provenance | Added local-only CLI/MCP version identity with embedded provenance and the durable detached Codex worker repair. |
| v1.2.3 | Worker-supervision maintenance | Kept a job `running` while its Codex child outlives a lost worker; introduced SPEC.md as the normative contract. |
| v1.2.4 | Maintenance release | Added the disabled-by-default OpenCode health adapter (27-tool default, 28 on opt-in) and the legacy stdio discovery guard; MCP Events remained deferred (BLOCKED). |

This repository is the source of record for implementation, tests, issues, releases, and project documentation.
