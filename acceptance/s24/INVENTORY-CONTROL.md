# Private inventory controller — offline source for review

Status: **DRAFT / NO GUEST OR HOST EXECUTION SCOPE / R1 INCOMPLETE / R2 HOLD**.
Parent: [metadata binding work package](../../docs/S24-METADATA-BINDING-WORK-PACKAGE-TH.md#s24-metadata-binding-work-package).
Inventory: [unchanged reviewed helper](PREBIND-INVENTORY.md).

## Source and authority boundary

`inventory_control.py` controls one newly spawned direct inventory worker. It uses
only the standard library. It does not import OwnedChild, parent_contract, the
fixture, candidate or SDK. It compiles the exact hash-checked helper bytes in
memory. The fixed helper SHA-256 is
`db0e56b5f91b3214b864d8fd5a7fd2743f52e3fc1e94e9573e516cc36d904847`.
The controller does not download or invoke a client, peer, doctor or credential
loader. It makes no socket or API call. It never executes the nominated venv
interpreter. It launches its own Python with `-I -S -B` and a minimal fixed
PATH/LANG environment. Private nominations travel in that owned child's argv;
they must not enter public logs or the repository.

Source approval, finite acquisition approval, merge, R2, Phase B, release and
deployment are separate decisions. A caller's scope timestamp is data, not an
approval or a reset of an old window. All ten scope/authentication/host/continuity/
containment/writer/descendant/R1/R2 flags remain false. Hashes are correlation only.

## Ordered control and stop method

1. Check finite caller timing (age 0–840 seconds), port/type constraints, pinned
   helper bytes and same-owner 0700 root/attempt directories. Reject any existing
   inventory, claim, trace or receipt, including a dangling symlink. Do not delete
   stale evidence or create a replacement attempt automatically.
2. Create/fsync the exclusive 0600 claim and its directory before spawning once.
   Create/fsync an exclusive 0600 bounded trace. Any creation/write/fsync failure
   preserves partial evidence and prevents automatic retry. A claim is not a
   global lock or a defense against trusted same-user replacement.
3. Start one worker. The worker arms Linux parent-death TERM and its own 40-second
   real-time timer before announcing readiness. It loads only the pinned helper
   before the G barrier. Readiness must be one bounded strict JSON frame with
   exact integer PID/parent fields and no duplicate keys. Startup/adoption must
   finish within 10 seconds from controller start; the ready read is at most
   5 seconds. Worker stdin EOF, wrong G or no G within 5 seconds rejects collection.
4. Check coherent procfs, direct-parent relation, same UID, exact argv, resolved
   executable and start ticks on the new unreaped Popen child. Open and retain its
   pidfd, check liveness and compare identity again. A mismatch sends no G and
   grants no signal authority. There is no numeric-PID/group fallback, adoption
   of an old process, retry or respawn.
5. Record G intent and the actual one-byte write separately. Neither proves G
   consumption. After G the worker checks age below 900 seconds, collects through
   the unchanged helper, compares directory identities and exclusively records
   inventory. The tuple/list normalization is only JSON representation handling.
6. Drain bounded stdout/stderr into the private fsynced trace. Initiate TERM at
   elapsed 48 seconds if still running. Allow 10 seconds of grace. KILL is
   default-off; `--allow-kill` requires its own explicit future scope nomination.
   If opted in, send KILL through the same validated retained pidfd only. Continue
   draining for at most 0.5 seconds after grace; never assume that wait/reap alone
   means the pipes are closed. Before each signal recheck the original identity.
7. On startup/evidence/protocol failure, close stdin, drain failed evidence without
   claiming complete capture, and attempt only validated pidfd stop. If identity
   is stale or adoption failed, wait for worker EOF/timer/parent-death behavior;
   never signal an unvalidated target. Unconfirmed stop retains Popen, pipes and
   pidfd. The CLI waits under the already armed absolute 60-second controller
   timer, without sending additional signals or inventing a receipt.
8. Only after confirmed direct-child reap and both pipe EOFs, close owned handles.
   Completion also requires exit 0, empty stderr, no expiry HOLD, one strict result
   frame, exact inventory hash/mode/nominations/directory identities and all nine
   helper flags false. Recheck current named directory paths as well as retained
   descriptors. Verify the final caller age/deadline before receipt creation.

The controller CLI arms the 60-second timer before preparation. Direct Python
library calls are trusted test interfaces; they do not arm that timer. SIGALRM or
controller death can leave partial files and no receipt. Uninterruptible kernel
I/O can defer signal delivery; these timers are not a hard kernel-I/O guarantee.
A same-user or compromised host can replace files or forge evidence. Leader reap
and pipe EOF are not proof of complete descendant or external-writer cessation.

## Exact read/write classes for a future finite scope

The future source transfer must nominate both immutable controller/helper files,
reviewed SHA-256 values and new private source destinations. No floating branch,
package installation, overlay or rewrite of prepared input is part of this method.

Before G, reads cover source metadata/bytes, nominated directory metadata,
existence of the four evidence names, `/proc/self/stat`, the new direct child's
`stat`, owner, `exe` and `cmdline`, and the controller interpreter's resolved path.
After G, the worker uses exactly the helper's documented nominated input reads,
stat-only runtime-key metadata and fixed guest procfs/sysfs observations. No other
account's process inventory or credential content is read.

Only these new files in the same nominated attempt may be written:

| Name | Writer | Condition |
| --- | --- | --- |
| `inventory-control-claim.json` | Controller | Exclusive durable single-use claim before spawn |
| `inventory-control-trace.jsonl` | Controller | Exclusive bounded private byte/identity trace |
| `binding-inventory.json` | Worker through unchanged helper | Exclusive inventory after G |
| `inventory-control-receipt.json` | Controller | Exclusive record after confirmed direct-child reap and pipe EOF |

`CONTROL_COMPLETE_PENDING_REVIEW` means only verified inventory/control evidence.
A `HOLD` receipt may describe a confirmed stopped failure with incomplete trace or
inventory. It never claims full capture or readiness. Unknown stop, timer death,
deadline/directory verification failure or failed receipt write/fsync yields no
confirmed final receipt; a partial receipt file may exist. Preserve every file.
No successful stdout summary is returned on receipt-write failure.

Private stdout contains only status, receipt digest and false flags. The trace,
claim, inventory and receipt stay private. Do not upload actual paths/accounts/
PIDs/tunnel IDs/endpoints, raw exceptions, profiles or operator evidence.

Exact private nominations, independent Windows memory/control observations,
local authority/Read+Use evidence and original continuity methods are still open.
A new finite operator approval must bind the complete action list, read/write
paths, source hashes, invocation, clocks, stop policy and independent console.
This document does not request or grant that approval. No VM run is authorized.

## Audit and offline validation

The handoff snapshot matched its stated `fbd046162123a6106685b8046aa0ef03f7426a000ec22d018903a5ca3ee2cf1e`
after restoring its single final newline. It was untested WIP, not reviewed source.
Audit changes reject duplicate/type-confused startup frames, fix tuple/list
binding, check evidence before spawn, drain pipes after KILL, retain unconfirmed
handles, check current named directories, validate result nominations and enforce
private trace mode. Earlier reviewed sources and pins remain unchanged.

Thirty-three mandatory controls are split into:

- 16 protocol/storage/timer controls: source drift, strict startup/EOF/deadline,
  G barrier, representation binding, single-use claim, existing/partial evidence,
  expiry/type rejection, trace bounds/mode/fsync, directory replacement, private
  CLI errors and an independent controller alarm.
- Seven synthetic-completion controls with actual disposable pipes/reap but a
  fabricated report/worker and a deliberately fake adoption target. They prove
  receipt gating, wrong hash/partial output/scope/nomination/stderr rejection and
  pre-G trace-failure cleanup. They do not prove real adoption or collection.
- Ten fresh Linux child controls: actual identity/pidfd targeting, wrong/stale
  identity, unrelated-child survival, expiry TERM, default-off KILL with retained
  handles, opted-in KILL and drain, real-worker no-G and safe inventory failure,
  independent worker alarm and parent-death TERM. No operator files are used.

Development Python 3.12.14: the final 33-control run returned exit 1, with 25 passes,
one failure and seven errors. All eight unsuccessful controls stop at the known
procfs/PID-namespace mismatch (one reports adoption instead of expected worker
failure). No skips, predicate relaxation, numeric-PID fallback, sleeps or retries
were introduced. No ResourceWarning/finalizer warning appeared. A prior synthetic
trace-failure test double raised AssertionError instead of the intended Hold; the
test double was corrected, and all seven synthetic controls then passed. The
unchanged inventory suite passed 22/22 with ResourceWarning-as-error.

The dedicated Linux 3.12/3.14 workflow runs all 33 controls, including real adoption,
under the unchanged fail-closed warning scanner. CI is required before source
acceptance; local synthetic passes do not substitute for it. Existing suites and
candidate checkout pins remain intact. No unit/CI result supplies guest readiness,
R1 completion, R2 approval, Phase B acceptance or scoped §22 PASS.
