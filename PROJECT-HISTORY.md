# Project history

For the project purpose, deployment context, and core design decisions, see [Project origin](PROJECT-ORIGIN.md).

## Evolution

| Release | Milestone | Outcome |
|---|---|---|
| v0.1.0 | Hermes Runs API bridge | Established the authenticated stdio MCP bridge, request ownership, idempotency handling, status/result retrieval, and cancellation lifecycle. |
| v0.1.1 | Operational hardening | Strengthened installation and tunnel operation practices before adding new execution capabilities. |
| v0.2.0 | Model-aware execution | Added safe per-task model/provider/options selection, model catalog tools, and persistent request fingerprinting. |
| v0.2.1 | Tunnel profile recovery | Added the `--force` path for replacing an existing tunnel profile safely. |
| v0.3.0 | Usage observability | Added usage summary/export for bridge-owned Hermes runs without estimating provider pricing or exporting prompts, outputs, or secrets. |
| v0.3.1 | Upgrade documentation | Added a direct upgrade path from v0.2.0. |
| v0.3.2 | Hermes live acceptance | Validated all 10 Hermes MCP tools through the Secure MCP Tunnel on the local WSL2 environment. |
| v0.4.0 | Permission-gated Codex / WSL2 | Preserved the 10 Hermes tools and added 6 Codex tools, workspace allowlisting, symlink-escape protection, sandbox restrictions, local write approval, job persistence, timeout, cancellation, and paginated results. Automated validation passed; Codex still requires live WSL2 acceptance. |

## Current baseline

v0.4.0 defines a 16-tool interface:

- 10 Hermes tools for health, model information/catalog, task lifecycle, recent tasks, and usage.
- 6 Codex tools for health, submit, status, result, cancel, and recent jobs.

The current release evidence is separated intentionally:

- [Changelog](CHANGELOG.md) records shipped changes.
- [Release status](RELEASE-STATUS-TH.md) records automated validation and remaining live acceptance.
- [Live acceptance](LIVE-ACCEPTANCE-TH.md) records evidence from the WSL2 environment.
- [Roadmap](ROADMAP.md) records future milestones.

## Repository as source of record

This repository is the maintained source of record for implementation, issues, pull requests, tags, releases, tests, and project documentation. Historical conversations informed early decisions but are not required to understand, install, operate, or contribute to the project.
