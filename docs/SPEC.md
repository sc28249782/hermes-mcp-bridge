# Hermes MCP Bridge Specification

Status: normative contract for the released v1.2.2 baseline and explicitly marked future requirements  
Current released baseline: v1.2.2  
Draft amendment target: v1.2.3 worker-supervision maintenance  
Canonical companion: TESTING.md for the MCP discovery count

Requirements marked for v1.2.3 are target-state requirements and MUST NOT be represented as current v1.2.2 behavior before their implementation and acceptance gates pass.

## 1. Purpose and scope

This document defines the externally observable contract of Hermes MCP Bridge. It is the source of truth for implementation, tests, live acceptance, review, and release claims.

The bridge is a local, permission-gated MCP boundary between ChatGPT and locally running Hermes Agent, Codex CLI, and optional Local Hands. It is not a general remote shell, hosted service, model proxy, or replacement for the upstream approval systems.

The terms MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative.

## 2. Architectural boundaries

The bridge has three independent backend paths:

1. Hermes path: authenticated requests to the configured loopback Hermes Runs API.
2. Codex path: policy-checked subprocess jobs executed only in configured workspaces.
3. Local Hands path: bounded local read-only filesystem operations that do not invoke Hermes or Codex.

A backend being unavailable MUST NOT cause an unrelated backend to be advertised as available. Local Hands health/list/read MUST remain independently callable when Hermes is unavailable or Codex is unavailable, subject to its own configuration and strict resolver checks.

The bridge MUST NOT expose a general arbitrary-command or arbitrary-filesystem primitive.

## 3. Version, provenance, and discovery

The CLI command bridge.sh version and the read-only MCP bridge_version tool MUST be local-only. They MUST NOT contact Hermes, Codex, the tunnel, GitHub, or another network endpoint.

Both version surfaces MUST report the shared identity fields:

- version
- release identifier
- build provenance
- source kind
- source revision when safely known
- configuration schema version
- embedded configuration schema version
- MCP discovery count

Missing or malformed provenance MUST produce explicit safe unknown/development values. The bridge MUST NOT infer a release from a directory name or expose credentials, prompts, outputs, or filesystem paths.

The released discovery contract is recorded in TESTING.md, which is the canonical location for the count. Other documents MUST reference that record instead of maintaining an independent number. Any discovery-count change requires a specification amendment, tests, documentation update, and release review.

## 4. MCP contract

MCP initialization MUST succeed without requiring an upstream model turn. Tool discovery MUST be deterministic for a given configuration.

Every tool MUST have:

- a stable name;
- an input schema that rejects unknown or invalid required values;
- a bounded response;
- a documented unavailable/disabled result where its backend can be unavailable;
- no secret-bearing fields in normal status, diagnostics, or audit responses.

MCP responses MAY contain operational identifiers needed for follow-up calls, but MUST NOT include API keys, credentials, full prompts, full outputs, or unredacted audit payloads.

The exact generated tool schemas and discovery count are validated by tests/test_mcp.py and TESTING.md. A code change that changes a tool schema is a contract change even when the tool count is unchanged.

## 5. Hermes contract

Hermes requests MUST use the configured authenticated loopback API and its advertised capabilities. The bridge MUST preserve request ownership and durable idempotency semantics.

A retry MAY reuse the same request identity only when the local record and the upstream contract prove that replay is safe. The bridge MUST NOT submit a duplicate task merely because a response or tunnel connection was lost.

Hermes context continuation MUST be explicit. A context identifier refers only to bridge-owned metadata and the latest observed bridge-owned Hermes session for that context. The bridge MUST NOT replay prompts, outputs, credentials, or ChatGPT conversation history. No implicit global context is allowed.

Approval state MUST be reported from the observed upstream response. An advertised approval endpoint alone is not proof that an interactive approval session exists.

## 6. Codex contract

Codex execution is permitted only when:

- the workspace is explicitly allowlisted;
- the requested mode is read-only or workspace-write;
- the requested model and reasoning effort are allowed by the effective workspace policy;
- prompt and runtime limits pass validation;
- workspace-write has explicit local interactive approval.

The bridge MUST use fixed argv construction, shell=False, and no arbitrary shell command composition. danger-full-access and workspace escape MUST be rejected before process start.

Codex status MUST distinguish non-terminal execution from terminal outcome. The bridge MUST never report completed without an observed successful worker result and exit code.

## 7. Durable worker and recovery contract

An approved workspace-write job is owned by a detached durable worker. The worker remains the parent of the Codex child, records the child exit status, and writes the terminal transition to persistent state.

The terminal record MUST preserve, when available:

- last known state;
- transition time;
- transition actor;
- transition reason;
- exit code or signal;
- completion result, or an explicit reason that no result exists.

The following invariant is mandatory for v1.2.3:

> A worker MUST NOT transition a job to unknown_exit while its Codex child is still alive.

If the worker is unavailable but the child is still alive, status MUST remain running and MAY include a redacted supervision-loss hint. The bridge MUST NOT infer completion, failure, or an exit code. Cancellation and timeout handling MUST continue to target the original process group and MUST NOT create a replacement job.

When the child is no longer alive and no durable terminal record exists, the bridge MUST use unknown_exit. This is a fail-closed result: it means the outcome cannot be verified, not that the task succeeded or failed.

Liveness checks MUST be resistant to PID reuse and MUST NOT treat an unrelated process with a reused PID as the original worker or child.

## 8. Work contexts

Contexts are metadata-only records. They MAY store context identifier, label, timestamps, bridge-owned session/run references, workspace, and job metadata.

Contexts MUST NOT store prompts, outputs, credentials, or full ChatGPT conversation state.

Continuation MUST name the context explicitly. Closing a context MUST prevent further binding or continuation through that context. For Hermes, when multiple runs are observed in one context, the latest observed bridge-owned session is the resumable session; this is latest-session semantics, not a fork.

Codex context binding records workspace/job metadata only and MUST NOT claim that Codex jobs are resumable conversations.

## 9. Local Hands read-only contract

The v1.2.x Hands surface consists only of health, list, and read operations. It MUST be disabled by default unless explicitly configured.

A configured workspace MUST pass strict containment/resolver checks. The implementation MUST fail closed for traversal, absolute paths, symlink escape, protected secret names, binary or NUL content, special files, hard links, oversize reads, and ambiguous case-colliding entries.

Hands MUST NOT mutate files, execute commands, access the network, or call Hermes/Codex in this release line.

## 10. Security and privacy invariants

The bridge MUST:

- keep state and audit files private;
- redact credentials and sensitive payloads from audit output;
- avoid logging prompts, outputs, file contents, or complete user payloads;
- reject workspace paths outside explicit policy;
- avoid shell=True and unrestricted argv;
- preserve local approval for every workspace-write job;
- keep backend availability and permissions fail-closed.

Security behavior is part of the public contract. A security relaxation requires a specification amendment, threat-model review, regression tests, live acceptance, and an explicit release note.

## 11. Persistence and migration

SQLite state is bridge-local and MUST be created with private permissions. Schema migrations MUST be additive or explicitly versioned and MUST preserve existing terminal records.

A bridge restart MUST NOT silently resubmit a task, change a completed result, or convert an unverified outcome into completed. Recovery MUST be observable through status/result and redacted audit records.

## 12. Error and unavailable behavior

Validation errors MUST identify the invalid field or contract condition without echoing secrets or full prompts. Backend-unavailable results MUST be explicit and MUST NOT be confused with successful execution.

A temporary transport failure MUST NOT by itself cause task resubmission, cancellation, or success inference.

Disabled or unavailable optional backends MUST retain stable response shapes so that MCP clients can reason about capability state without guessing.

## 13. Testing and acceptance

Every normative requirement MUST have at least one automated regression test or a documented reason why it requires live acceptance. Requirements planned for a future release are tracked as unchecked items in ROADMAP.md and MUST NOT be claimed as current behavior until their implementation and acceptance evidence are complete.

The minimum release evidence is:

- project-interpreter regression tests with ResourceWarning treated as errors;
- shell syntax and shellcheck validation;
- MCP discovery/schema verification;
- backend-disabled and unavailable-backend tests;
- WSL2 live acceptance for changed lifecycle behavior;
- independent review before tagging;
- clean documentation gate before tag;
- signed tag, external SHA256SUMS, archive verification, and post-tag release record.

TESTING.md records the current test inventory and canonical discovery count. LIVE-ACCEPTANCE-TH.md records workstation/tunnel evidence. RELEASE-RUNBOOK-TH.md defines release sequencing.

## 14. Change control

A change is contract-compatible only when it preserves this specification, existing security invariants, and the documented response semantics.

The following require a specification update before implementation is merged:

- MCP tool or schema changes;
- status/terminal-state changes;
- approval or workspace-policy changes;
- context/session semantics changes;
- persistence or migration changes;
- security boundary changes;
- discovery-count changes.

v1.2.3 is limited to the durable-worker supervision invariant in section 7 and its tests, operational guidance, and acceptance evidence. Mutation/execution features for Local Hands belong to the separately reviewed v1.3.0 track.
