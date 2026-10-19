# Hermes MCP Bridge Specification

Status: normative contract for the released baselines (v1.2.3, extended by v1.2.4 sections 16-17) and explicitly marked unreleased/future requirements

Current released baseline: v1.2.4 (released 2026-10-18)  
Canonical companion: TESTING.md for the MCP discovery count

Release record: v1.2.4 released 2026-10-18 via a GPG-signed annotated tag on `213305638c135041c42a3f242d6c5665c49c3fdf` and published with a download-verified ZIP plus an external SHA256SUMS asset. The MCP Events amendment (section 15), originally the v1.2.4 target requirement, is deferred with no assigned release and remains blocked.

Section 15 requirements are deferred target-state requirements with no assigned release and MUST NOT be represented as current v1.2.3 behavior before their capability, implementation, and acceptance gates pass. Released v1.2.4 includes only the section 16 OpenCode health adapter and the section 17 legacy stdio discovery guard. Section 15 MCP Events is a future requirement and is not part of the release.

## 1. Purpose and scope

This document defines the externally observable contract of Hermes MCP Bridge. It is the source of truth for implementation, tests, live acceptance, review, and release claims.

The bridge is a local, permission-gated MCP boundary between ChatGPT and locally running Hermes Agent, Codex CLI, and optional Local Hands. It is not a general remote shell, hosted service, model proxy, or replacement for the upstream approval systems.

The terms MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative.

## 2. Architectural boundaries

The released bridge has three independent backend paths:

1. Hermes path: authenticated requests to the configured loopback Hermes Runs API.
2. Codex path: policy-checked subprocess jobs executed only in configured workspaces.
3. Local Hands path: bounded local read-only filesystem operations that do not invoke Hermes or Codex.

Section 18 adds a separately enabled, unreleased fourth path for native OpenCode CLI tasks. It does not run through the Hermes API or Codex sandbox.

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

v1.2.3 was limited to the durable-worker supervision invariant in section 7 and its tests, operational guidance, and acceptance evidence.

The MCP Events amendment (section 15) is capability-gated and deferred with no assigned release; it is no longer tied to the v1.2.4 release. Its first change is a Dev-only probe and specification amendment; no runtime event subscription or delivery may be claimed until the probe has passed. Local Hands mutation/execution remains deferred while this gate is evaluated.

Separately, PR #34 (merged 2026-10-18) and PR #35 (merged 2026-10-18) amend this specification by adding section 16 for the OpenCode health adapter and section 17 for the legacy stdio discovery guard: additive surfaces that are not part of the v1.2.3 baseline and carry no v1.2.4 Events claim. Both sections ship in v1.2.4, released 2026-10-18 via a GPG-signed tag on `2133056` and published with a download-verified archive; the bounded-pass live tunnel acceptance limitation (guard outcome unobserved on the tunnel) is preserved in [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md).

## 15. MCP Events capability gate (deferred — no assigned release; BLOCKED)

This section is a future requirement, originally planned as the v1.2.4 target requirement; it is now deferred with no assigned release and remains blocked at the subscription gate. The released v1.2.3 bridge has no MCP Events capability, subscription state, callback sender, or event delivery.

Before a runtime implementation is merged, a Dev Secure MCP Tunnel probe MUST demonstrate that authenticated MCP Events protocol 2.0 requests, signed HTTPS callback verification, one redacted event delivery, and unsubscribe work end-to-end in a ChatGPT Work chat. A failed or unsupported probe MUST stop the runtime Events track. Explicit user-directed polling through existing Hermes status/result tools remains permitted, but MUST NOT be described as push notification.

Any later Events configuration MUST be disabled by default. If Events are enabled and the locally configured callback-host allowlist is empty, every callback MUST be denied. The allowlist is an authorization boundary and MUST be operator configured; it MUST NOT be supplied by a model, prompt, subscription argument, or event payload.

A later callback validator MUST use canonical, label-boundary host matching. An exact entry matches only that host. A wildcard suffix entry such as `*.openai.com` matches only subdomain labels below `openai.com`; it MUST NOT match `openai.com` or `evil-openai.com`. HTTPS, public-address validation, redirect refusal, and TLS hostname verification are defense in depth and MUST NOT authorize a host that fails the allowlist.

A future subscription MUST be accepted only through an authenticated MCP Events protocol request after user confirmation in the Work chat. No ordinary MCP tool or CLI command may create a subscription or accept a model-derived callback URL. Callback URLs, signing secrets, prompts, outputs, credentials, detailed paths, and result content MUST NOT appear in events, audit output, diagnostics, or tool responses.

The detailed Dev acceptance procedure is in V1.2.4-MCP-EVENTS-PROBE-TH.md, which keeps its original v1.2.4 filename as a historical record; the filename remains a valid link.

## 16. OpenCode health adapter (v1.2.4; introduced by PR #34)

This section is introduced by PR #34 and is not part of the v1.2.3 baseline; it ships in v1.2.4, released 2026-10-18. The released v1.2.3 bridge has no OpenCode adapter, no `opencode` configuration section, and no `opencode_health` tool. No release or version note may present this section as current v1.2.3 released behavior. This amendment is the specification update required by sections 3, 4, and 14 for the conditional discovery-count change carried by PR #34.

The adapter is additive, disabled by default, and health-only. It is absent from the released v1.2.3 baseline; the published release record (released v1.2.4, 2026-10-18) covers it.

- The `opencode` configuration section MUST default to disabled (`enabled` false). While disabled, the bridge MUST NOT register `opencode_health`, MUST NOT spawn a process, and MUST return an explicit fail-closed disabled result for every health call. Default MCP discovery MUST remain the canonical 27 tools.
- Enabling MUST be an explicit operator configuration change that names an explicit `binary`. Configuration validation MUST reject: a non-boolean `enabled`; a non-integer or out-of-range `version_timeout_seconds` (1-120) or `max_output_bytes` (1024-1048576); a `binary` that is empty, longer than 4096 characters, not an absolute path, or contains any ASCII control character (0x00-0x1F and 0x7F); and a section that is enabled without a `binary`. Unknown keys in the section are warned and ignored, consistent with other optional sections.
- When enabled, the adapter MUST require the configured `binary` to be an absolute path to a regular file with executable permission before any spawn, and MUST re-verify this at probe time. Registration MUST then add exactly one read-only tool, `opencode_health`; discovery becomes 28 tools and MUST follow the change-control rules for discovery-count changes.
- The probe MUST be bounded and read-only: fixed argv `[configured binary, --version]`, shell disabled, standard input closed, and no network, model, authentication, or upstream API call made by the bridge as part of the probe. The configured executable runs with the full privileges of the bridge process user; the bridge adds no sandbox. The bounded probe bounds what the bridge does, not what the configured executable can do once started; the safety or permission of an arbitrary operator-configured executable is not guaranteed, and enabling remains a deliberate trust decision.
- Output handling MUST be bounded: stdout and stderr MUST be drained independently with a per-stream memory cap equal to `max_output_bytes`; exceeding either cap, the overall wall-clock deadline anchored at spawn, a nonzero or abnormal exit, or a malformed version string MUST produce a sanitized, explicit failure that does not include child stdout or stderr content or environment data. A successful version MUST be decodable UTF-8, non-empty after trimming, contain at least one digit, and stay within a bounded length and character set.
- On Linux/WSL2, the probe child MUST start a new session so the leader's PID is its process group ID. Every group signal MUST be sent only while the leader is still an unreaped child of the bridge process; the leader MUST be reaped exactly once, by handle, after the final group signal; no wait may gate a signal; and when leader ownership cannot be verified the bridge MUST NOT signal that process group at all.
- A successful health result MUST return a stable shape with exactly these fields: `ok`, `enabled`, `version`, `binary`, `version_timeout_seconds`, `max_output_bytes`, `probe`, `execution_scope`, and `runner_scope`, and MUST NOT include secret-bearing content, consistent with section 4.
- The adapter MUST NOT provide task submission, session management, event subscription, cancellation, approval, or permission handling. Such surfaces are outside this contract until separately amended.
- Acceptance mapping: the requirements above are proven by `tests/test_opencode.py` (disabled fail-closed, enabled validation including regular-executable checks, fixed argv and version reporting, symlink acceptance, malformed-version and nonzero-exit rejection, per-stream oversize caps, timeout termination, descendant cleanup, and the leader-reap ordering regression set `TestOpenCodeCleanupOrdering`), `tests/mock_opencode_server.py` with `tests/test_opencode.py` for enabled stdio discovery at 28 tools, and `tests/test_mcp.py` for the 27-tool default. The sole live acceptance surface is the real OpenCode CLI `--version`, recorded against v2.0.32 in WSL2. No other live surface is accepted, and this section claims no acceptance beyond it.


## 17. Legacy stdio discovery compatibility (v1.2.4; introduced by PR #35)

This section is a compatibility boundary for the legacy stdio transport only, introduced by PR #35. It is not part of the v1.2.3 baseline (the released v1.2.3 bridge predates the guard), so no release or version note may present it as current v1.2.3 behavior. It ships in v1.2.4, released 2026-10-18. It is deliberately narrow:

- The compatibility boundary applies ONLY to the legacy stdio serve path (`bridge.py serve` / `./bridge.sh serve` over `mcp.server.stdio.stdio_server()`). The tunnel-facing HTTP surfaces and the Dev `events_probe` fixture MUST show no change.
- The guard MUST sit only at the official SDK stdio stream boundary (the streams `stdio_server()` yields and the bridge hands to the low-level server), operating on typed SDK message objects. Site-packages edits and global monkeypatching of the SDK MUST NOT be used.
- An incoming JSON-RPC REQUEST whose top-level method is exactly `server/discover` MUST be answered at the boundary with a JSON-RPC error response carrying code `-32601` (METHOD_NOT_FOUND) with a constant message, the SAME request `id` (integer or string preserved), and no echoed request parameters. It MUST NOT reach the low-level server, MUST NOT produce the SDK's `-32602` union-validation warning, and its content MUST NOT appear in logs (a constant-text debug line without payload is permitted).
- The boundary MUST NOT claim any modern discovery protocol or capability: the reply is an error, initialize capabilities and the canonical discovery count (27 default; 28 only with the section 16 adapter explicitly enabled) MUST NOT change, and `server/discover` MUST NOT be answered with success, a tool list, or discovery capabilities.
- ONLY requests are intercepted. Notifications, including a notification-shaped `server/discover`, MUST be forwarded unchanged to the SDK so normal envelope validation applies; a supported request such as `tools/call` whose parameter values merely mention `server/discover` MUST NOT be intercepted (matching is on the top-level JSON-RPC request method only).
- Every other message - supported requests, unrelated unknown methods, responses, notifications, transport parse errors - MUST be forwarded unchanged as the same typed object with transport metadata preserved, so SDK validation outcomes (including `-32602` and its `Failed to validate request` warning) remain unchanged and uncovered. The guard MUST NOT add any broad logging filter or warning suppression.
- The forwarder MUST be cancellation-safe and bounded: when stdin reaches EOF or the session stops consuming, it must stop without leaving detached tasks or hanging the process, and it adds no extra process, network, or dependency surface. Repeated discovery probes in one process MUST NOT flood typical operator logs.
- Acceptance mapping: `tests/test_stdio_guard.py` proves the synthetic in-memory boundary cases (int/string id preservation, no-param reply shape, notification pass-through, argument-name non-matching, unknown-method unchanged behavior, repeated probes) and its real-stdio section proves the pre-initialize probe, the legacy initialize/initialized/tools-list sequence, unchanged malformed-request validation, and clean EOF shutdown.


## 18. OpenCode task execution (unreleased; no assigned release)

This section is an unreleased amendment. It is not part of the v1.2.3 baseline and carries no v1.2.4 claim; sections 16 and 17 keep their released history unchanged. This section is the specification update required by sections 3, 4, and 14 for the tool-count change it introduces. It overrides the section 16 rule that the adapter MUST NOT provide task submission, sessions, cancellation, or permission handling ONLY for the explicit execution opt-in defined here. The health-only default behavior of section 16 is unchanged. For this opt-in only, section 17 discovery-count references extend to 33 tools; the stdio guard and initialize capabilities remain unchanged.

### 18.1 Enabling and validation

- A new subsection `opencode.execution` MUST default to disabled (`enabled` false). While disabled, the bridge MUST NOT register any execution tool, MUST NOT spawn a worker or CLI process, and MUST return an explicit fail-closed disabled result for every execution call. Default MCP discovery MUST remain 27 tools, or 28 when the section 16 adapter is enabled.
- Enabling execution MUST require all of: `opencode.enabled` true with a valid `binary` under section 16 rules; a nonempty list `allowed_workspaces` whose entries are absolute directory paths with no ASCII control character (0x00-0x1F and 0x7F); a nonempty list `allowed_models` whose entries match the bounded pattern `provider/model` with printable non-control characters and a bounded length. Validation MUST reject empty lists, control characters, relative paths, non-boolean `enabled`, and out-of-range integers. Entries are canonicalized once at load; the canonical forms are the only accepted workspace and model values.
- The subsection MUST define, with explicit ranges: `max_prompt_chars` (default 32000, range 1-131072), `max_runtime_seconds` (default 1800, range 1-14400), and `max_output_bytes` (default 524288, range 65536-8388608). The execution `max_output_bytes` is independent of the section 16 health `max_output_bytes`; the bridge MUST NOT silently repurpose the health value for execution.

### 18.2 Tool surface

- When execution is enabled, the bridge MUST register exactly five tools and discovery becomes 33 tools under the change-control rules: `opencode_submit_task(prompt, workspace, request_id, session_id=None, model=None)`, `opencode_task_status(job_id)`, `opencode_task_result(job_id, offset=0, max_chars=12000)`, `opencode_cancel_task(job_id)`, and `opencode_recent_tasks()`. Tool annotations follow the existing read/write split: submit and cancel are write; the others are read.

- Acknowledgements contain `job_id`, `status`, `session_id`, and `model`; the job/session identifiers remain stable on replay, while status may advance.
- Status contains `job_id`, `status`, `session_id`, `model`, `created`, `started`, `finished`, `exit_code`, `transition_actor`, `transition_reason`, and `result_reason`. Timestamps are Unix seconds; unobserved timestamps and exit codes are null.
- Result contains the acknowledgement fields plus `offset`, `next_offset`, `content`, `truncated`, and `note`. Cancel contains the acknowledgement fields plus `note`. Recent contains `jobs` (at most 30 redacted entries with job/status/session/model/created/finished/transition_reason) and `redacted` true.

### 18.3 Execution boundary

- The bridge MUST NOT inject permission configuration. It MUST NOT override or strip operator-provided `OPENCODE_CONFIG`, `OPENCODE_CONFIG_CONTENT`, or `OPENCODE_CONFIG_DIR`, and MUST NOT pass flags that alter permission behavior. Rationale: config precedence for permission rules is not proven, so an injected policy MUST NOT be claimed as enforced. Native OpenCode configuration, plugins, and saved permissions apply unchanged.
- The configured executable runs with the full privileges of the bridge process. The bridge adds no sandbox. Workspace selection is a current-working-directory allowlist only; it is NOT filesystem isolation and NOT network isolation. All operator-facing documents (README, security, tool help, and operator examples) MUST state this unmistakably.
- The bridge MUST NOT use `--auto`, `--server`, `--continue`, or any caller-supplied flag, agent, environment variable, or file attachment. The CLI command line MUST be exactly `[binary, "run", "--standalone", "--format", "json", "--session", <session id>, "--model", <allowed model>]` with shell disabled. The prompt MUST be passed on standard input as UTF-8, never as an argv element, and stdin MUST be closed after the prompt.

### 18.4 Sessions and resume

- The bridge MUST mint each session identifier before spawn, store it in the state database first, and supply it with `--session`. A minted identifier MUST match `^ses_[A-Za-z0-9]{8,64}$`.
- Resume is permitted ONLY for a bridge-owned session with the same canonical workspace and the same allowed model as the owning job. The bridge MUST NOT permit arbitrary local session access or a model change on resume. A resumed prompt creates a new job row that references the prior session.

### 18.5 Durable worker and lifecycle

- A separate detached worker module owns each job. The worker remains the parent of the CLI process after the bridge disconnects and writes the terminal record to a private SQLite state database owned by the bridge. State files and output files MUST have mode 0600; private state directories MUST have mode 0700. Job outputs MUST be stored outside every allowed workspace.
- Job states are `pending`, `running`, and the terminal states `completed`, `failed`, `cancelled`, `permission_required`, and `unknown_exit`. A runtime deadline produces `failed` with a bounded timeout reason. An observed native permission request produces `permission_required`; the bridge MUST NEVER auto-approve. An unresolved ask that outlives the bounded deadline produces `failed` with the timeout reason, never success.
- Admission MUST be atomic. Concurrency is 1 globally and 1 per session. The bridge MUST NOT queue jobs without bound: when the global slot is busy, submission fails with an explicit busy result.
- Idempotency: a submission whose `request_id` matches a stored job with the same canonical input fingerprint (prompt, workspace, model, session) MUST return the original job and session identifiers with their current status. The same `request_id` with a different fingerprint MUST be rejected without a second model invocation.
- Cancellation is owned by the worker through a database cancel flag. Every `killpg` MUST be sent only by the direct parent of the CLI leader, only while the leader is still an unreaped child of that parent (the section 16 WNOWAIT invariant), and the leader MUST be reaped exactly once, by handle, after the final group signal. The controller MUST NOT signal a stored PID or PGID. A timeout is enforced by the worker independently of controller polling, including when the CLI never reads stdin. TERM/KILL/reap and post-cleanup pipe drain use separately bounded grace periods.
- If the worker crashes or its identity is uncertain, the job MUST become `unknown_exit`. The bridge MUST NOT invent a success or a cancel, MUST NOT signal a process it cannot prove it owns, and MUST reject new submissions conservatively while a job is `running` or `unknown_exit`. Cancellation reaches `cancelled` only after the worker confirms cleanup. Terminal states are immutable.

### 18.6 Output contract

- The CLI stdout MUST be JSON lines of bounded objects (at most 65536 bytes per line). Per-stream disk output MUST NOT exceed execution `max_output_bytes`. Every event MUST carry the job session identifier; a mismatch, malformed line, output overflow, truncation, or empty stream MUST fail the job. Process exit 0 alone is insufficient.
- A job MAY reach `completed` only when the bridge observed valid response evidence (a nonempty text response or a final step-finish event with a stop reason) AND the process exited 0. A text-only refusal or denial from the model MAY still be a `completed` native turn. Documents MUST state that callers inspect the output, and that the bridge cannot infer goal success or permission outcomes from it.
- Result pagination uses character offsets and a `max_chars` range of 1-24000. `next_offset` advances by returned characters; `truncated` describes currently stored output, not whether a running job can produce more. Result pagination returns untrusted content; the caller MUST treat it as model output. `status` and `recent` responses MUST be redacted: no prompt text, output content, credentials, or detailed paths. Audit records MUST NOT contain prompts, output, or credentials.

### 18.7 Acceptance mapping

- `tests/test_opencode.py` and the section 16 suite MUST pass unchanged; default discovery stays 27, and health-enabled discovery stays 28.
- A new execution test suite MUST prove: disabled fail-closed; section 18.1 validation; the fixed argv and stdin prompt; session minting and resume rules; idempotency and fingerprint conflict; admission concurrency and busy rejection; a deterministic fixture CLI for error-with-exit-0, streaming events, pause, descendant processes, cancellation race, output caps, worker restart, and bridge-owned sessions; `permission_required` detection; `unknown_exit`; redaction of status and recent; 0600 and 0700 file modes; and discovery 33 through the real stdio fixture.
- `tests/test_packaging.py` MUST include the new modules. No released surface may claim this section until its own change-control gate closes.
