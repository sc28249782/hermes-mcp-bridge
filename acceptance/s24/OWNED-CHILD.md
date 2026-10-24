# Phase B source increment 3: offline direct-child control and byte recorder

Status: **SOURCE FOR REVIEW — offline control component; not a complete B supervisor**.
Design: [Phase B control plan](../../docs/S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md).
Route limits: [feasibility assessment](../../docs/S22-PHASE-B-ROUTE-FEASIBILITY-TH.md).

## Boundary

`owned_child.py` supplies no launcher, CLI, network client, credential access, MCP tool or Work adapter. The caller provides an already-created Popen child and its exact expected argv. The module requires direct-parent ownership without reaping, coherent Linux procfs, matching live argv/executable/owner and pidfd support before adoption. The caller must hand off exclusive pipe/reap/signal ownership until close; concurrent external reads/waits/signals are outside this contract. Text-mode pipes are rejected. Adoption or watchdog-thread startup failure sends no signal; the original owner retains cleanup responsibility.
The module records the executable, owner uid, PID/start ticks and argv privately. Start ticks, owner, executable and argv are rechecked before each signal; a missing/mismatched observation blocks the signal. Signals use the retained pidfd only; no stored numeric PID, substring match or process-group signal is used. This protects the adopted process instance from PID reuse. It does not establish source hashes, permission to launch, full writer coverage or descendant containment. The future launcher must enforce those separately.
Only the direct child is controlled. Every result explicitly states descendant_cessation_proved=false. Leader reap, PID absence or empty pipes never prove global quiescence or that detached writers stopped. No stopped-state acceptance follows from this component alone.

## Lifecycle and bounds

A watchdog thread drains stdout/stderr while the caller is idle and checks a monotonic absolute window and renewable liveness lease. Renewal cannot revive an expired lease or extend the original window. Parent-loss/observation-failure stop methods are control inputs; they do not detect those events or authenticate an observer. No background control-plane task is started.
The default offline window is 30 seconds, lease 5 seconds, and TERM grace 10 seconds. Window <=1,200 seconds, lease <=30 seconds and grace <=10 seconds are validated, excluding Boolean/nonfinite values. Shorter grace values exist for new disposable test children only; they do not authorize shortening the plan's ten-second B stop policy. Actual B bindings and values still need review and separate approval.
On expiry/stop/error the controller blocks new input and sends TERM through the owned pidfd. KILL is disabled by default. The explicit offline test option permits KILL only through the same retained pidfd after grace; the flag itself is not operational authority. No retry, respawn or second cohort is created.
Without KILL, a stubborn child remains unconfirmed and close raises; the retained owner/pidfd remains available for operator inspection. No successful stop report is produced. On confirmed leader exit the owner reaps, joins the watchdog, fsyncs/closes the trace and closes its pipe/pidfd handles.
The watchdog depends on its own process, scheduling and filesystem I/O. It cannot survive owner-process death, force a blocked filesystem call or prove independent outer-supervisor operation. That stronger supervisor and crash behavior remain B gates.

## Private byte evidence

The trace is created O_EXCL/O_NOFOLLOW at mode 0600 under a resolved private parent directory; existing files are not replaced. Records contain direction and base64 bytes. Identity metadata and raw content remain private and must not be published.
stdin_intent records requested bytes. stdin_written records only bytes successfully accepted by the pipe; this is not proof the child consumed them. stdout/stderr records contain bytes actually read from those pipes, preserving chunk order per direction. A real fixture test reconstructs initialize/tools-list/version replies from recorded stdout bytes without synthesizing response envelopes.
This is actual offline pipe evidence, not an authenticated Work/tunnel trace or an app-level capture. Correlation, route provenance, source identity and RPC/tool/argument policy remain external obligations. This byte controller deliberately does not decide which JSON-RPC operations are permitted.
Input/stdout frames are bounded at 65,536 bytes, buffered stdout queue at 1 MiB and encoded trace bytes at 8 MiB. Nonblocking input writes have a two-second bound further limited by lease/window. Both output pipes are drained concurrently. Overflow or write/read failures stop input and hold the component; partial evidence is retained, never relabeled complete. A failed trace can contain an incomplete final record.

## Validation and environment limits

Thirteen new tests use only newly created children. They cover actual byte reconstruction/private modes/reap, lease expiry without polling, renewal versus absolute deadline, TERM then opted-in KILL, an unrelated child remaining alive, no-KILL unconfirmed stop, bad argv/nonchild/procfs rejection, no-overwrite/private-parent rules, limits and actual pinned fixture initialize/discovery/version over observed pipes. The fixture test submits no backend/model task.
The initial development run failed positive adoption checks: this development container's PID namespace and mounted procfs disagree. This is an unsupported environment for the identity check, not a passing baseline. Source checks remain strict; no procfs fallback, assertion relaxation or environment skip is added. A targeted negative test proves incoherent procfs is rejected before opening a target pidfd or signaling. Dedicated Ubuntu CI is required for actual control validation on Python 3.12/3.14 with unchanged warning gates.
The unchanged candidate/fixture and #97/#98 source remain fixed; new tests are separate from 234/7/10 +16+13. Full local regression is not claimed. Source review/CI is not guest readiness or B acceptance.

## Remaining B work

Actual parent handoff/invocation and namespace binding, host/guest collectors and resource/continuity provenance, independent outer supervisor, full cohort/descendant writer coverage, duplicate-launch control, protocol policy/correlation, durable attempt receipts and stopped-writer proof are still required. Original Production/Dev and the historical unresolved run are untouched. No new guest window, setup/activation, gate closure, release or deployment is authorized. Scoped section 22 and PR #80 remain HOLD.
