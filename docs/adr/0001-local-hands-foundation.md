# ADR-0001: Local Hands foundation contracts

- Status: Accepted for implementation planning
- Date: 2026-09-21
- Applies to: Local Hands v1.2.0+

## Context

Local Hands must remain available when Hermes or Codex is unavailable while preserving the bridge's fail-closed security model. The initial design left several contract choices open. These choices must be stable before implementation so config migration, tool discovery, approval integrity, and process recovery do not drift between pull requests.

## Decisions

### 1. Configuration remains schema version 1

Add `hands` as an optional additive block to the existing schema version 1. A config without the block is valid and means Hands is disabled. Unknown Hands keys produce warnings consistently with the existing validator; invalid known values fail startup validation. The installer must not invent workspace roots or grant read/write/execute capabilities.

Rationale: the addition is backward-compatible and does not reinterpret existing keys. A future incompatible change must introduce a new schema version explicitly.

### 2. Stable tool discovery

All Hands tools delivered by the installed release are registered even when `hands.enabled=false`. Calls return a stable structured `disabled` result. Tool count therefore depends on the release, not private configuration.

For v1.2.0 the delivered tools are only `hands_health`, `hands_list`, and `hands_read`. Mutation/process tools are introduced in v1.3.0.

### 3. Canonical approval digest

The immutable persisted action record is the sole execution source after approval. The client cannot submit a replacement payload at execution time. Content-bearing actions reference a sealed content blob in the action store by SHA-256; execution rechecks that blob digest before use.

Canonical bytes are:

```text
ASCII("hermes-local-hands-action-v1") || 0x00 ||
UTF-8(json.dumps(payload,
                 ensure_ascii=False,
                 sort_keys=True,
                 separators=(",", ":"),
                 allow_nan=False))
```

The action digest is lowercase hexadecimal SHA-256 of those bytes.

Rules:

- Payload includes `schema="hands-action-v1"`, action type, canonical workspace ID/path reference, operation-specific normalized parameters, content/base digest where applicable, risk class, and expiry as integer Unix seconds.
- Payload contains no raw file content, secret, output, or floating-point value. Any sealed content blob is stored separately, is immutable, and is addressed only by the digest included in the payload.
- Paths are canonicalized and authorized before serialization.
- Strings retain their Unicode code points after operation-specific normalization; implementations must not apply additional implicit Unicode normalization while hashing.
- Golden vectors cover key order, whitespace, Unicode, integer boundaries, rejected float/NaN, field omission versus null, and prefix separation.
- Any policy-relevant change creates a new action/digest and requires new approval.

### 4. Process output uses bounded JSONL files

Each Hands-owned process writes structured output records to its own permission-restricted JSONL file, following the proven Codex-log operational pattern. Runtime limits bound bytes, records, line size, and retention. Truncation is explicit in status/result metadata. Logs are never audit records and are not copied into audit storage.

Process output is trusted-workspace-content, not trusted or secret-safe content. It may contain credentials printed by build scripts or tools and will flow to the MCP caller when result pages are requested. Filename protection and audit redaction do not prevent this channel.

### 5. Initial no-approval execution profiles are metadata-only

Execution begins in v1.3.0. A profile can avoid per-run approval only when its argv is exact/constrained and its output is metadata-only. Initial candidates are constrained `git status`, metadata-only `git log`, and `ctest -N`; each still requires adversarial profile tests.

`git diff`, build/test execution, interpreters, scripts, hooks, response files, and config-file indirection are content-bearing or trusted-workspace-code and require approval. Git profiles use a minimal environment and disable global/system config, hooks, pager, external diff, and other action-specific escape paths.

### 6. Deletion is a non-overridable baseline deny

Local Hands exposes no generic delete tool. Local approval cannot authorize generic delete, unlink, rmdir, destination-clobbering rename, unapproved truncate, or an execution profile that cannot prove these actions are blocked. Exact `hands_write`/`hands_patch` is a separate digest-bound action that may replace only its approved target.

`shell=False` and argv validation do not constrain filesystem syscalls made by a binary or child process. Execution profiles claiming no-delete/no-unapproved-truncate therefore require a runtime-probed kernel mechanism such as Landlock or an equivalent accepted control. Landlock was introduced in Linux 5.13 and also depends on build, boot, and ABI support; availability must not be inferred from the WSL2 label or kernel version alone. If the required rights cannot be enforced, the profile is unavailable without a keyword-filter fallback.

A future move operation must be a dedicated canonical source/destination action using a no-clobber primitive and must not expose arbitrary `mv` arguments.

## Required security contracts recorded with this ADR

- Baseline protected filename patterns inside workspaces are non-removable; users may only add patterns.
- File access uses strict descriptor-relative resolution. A workspace that fails its `openat2`/filesystem self-test is unavailable rather than silently downgraded to check-then-open.
- Pending actions have explicit global and per-workspace caps.
- DrvFS is handled conservatively with case-folded protected-name matching, descriptor containment, mount reporting, and ambiguous case-collision rejection.
- Computer use cannot start until the Windows Host phase passes live acceptance and a recorded security review.
- Model-relayed nonces, allow-by-default deny-list sandboxes, read-anywhere policies, and dynamic MCP trust bypasses are not authorization mechanisms for Local Hands.

## Consequences

- v1.2.0 is intentionally small and read-only, enabling earlier operational feedback.
- The release adds three tools even when Hands remains disabled by default.
- v1.3.0 carries the action-store/process complexity and needs a separate acceptance record.
- Strict filesystem handling may mark some workspaces unavailable; this is preferable to an insecure fallback.
- Users must be warned that approved execution can expose workspace content through stdout/stderr.

## Deferred decisions

- Final non-removable protected path/name set after fixture testing
- Hard-link and bind-mount support scope
- CLI-only approval versus a future Windows companion UI
- Windows helper transport, authentication, signing, and distribution
