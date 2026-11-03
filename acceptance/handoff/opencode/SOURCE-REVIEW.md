# OpenCode passive observation — offline source candidate

Date: 3 November 2026. Parent reviewed contract head:
`a8008dfc537114babbe68c966af4c1decbf1da3f` on draft PR #117.
Operator supplied **“ทำขั้นถัดไป”** after the contract review; exact approval
timestamp NOT_PROVIDED. This authorizes preparation of this source candidate and
owned offline controls, not Dev observation, merge, pilot, release or deployment.

This is a **fixture-scoped implementation**, not acceptance of the whole
integration. The trusted fixture launcher is the only admission issuer implemented.
Production authority/current Dev bindings and the external owner are not implemented.
Nothing imports or instantiates native OpenCodeTasks/ContextRegistry. No backend,
CLI/model/network/API/secret/config call, checkpoint append, new evaluation or J0
operation occurs during observation. J0 stays PAUSED; R1 NOT AUTHORIZED / R2 HOLD.

## Source and dependency identity

[source-hashes.json](source-hashes.json) records actual SHA256 and byte length for
every new source/header plus the dedicated workflow. It also pins the unchanged
checkpoint/store/schema/native baseline dependencies. It does not authenticate the
compiler, operating system, SQLite library or fixture launch authority.

Supported source profile: **64-bit Linux x86_64, native SQLite 3.45.1**, rollback
journal format only. Unsupported version/platform, WAL/SHM, any journal, schema
change or missing compiler/library produces failure/HOLD, not a fallback/skip.
`sqlite_abi.h` is an authored, limited public SQLite ABI declaration subset, not
an upstream amalgamation/header or a vendored SQLite build. It requires independent
source review. Tests compile using existing `cc` and the existing shared object:

```text
cc -std=c11 -Wall -Wextra -Werror -O2 oc_snapshot_vfs.c /lib/x86_64-linux-gnu/libsqlite3.so.0 -o <new-owned-helper>
```

No compiler/library package is installed by this package/workflow. Test compilation
uses the source file's directory for its two local headers. The same command adds
`-DOC_CONTROL_BUILD` for explicit denial/lock controls and additionally
`-DOC_CONTROL_AUTHORIZE` for the prohibited prompt-query control. These test-only
hooks are absent from the production-helper build. The production-helper name
identifies a build variant, **not a production deployment**.

Each run emits actual compiler/Python/Python-SQLite/native-SQLite/source-ID,
library SHA256, source SHA256 and all helper-build SHA256 values. These are
measurement facts, not tool authenticity proofs or stable cross-build digests.
The helper gates native SQLite 3.45.1, not Python's potentially different SQLite.

`baseline.py` loads only exact hash-checked, mode-checked existing checkpoint/store
source bytes using `exec(compile(...))`; no JSON or caller content is executable.
Its temporary checkpoint-module alias is confined to standalone single-thread
fixture import. The existing admitted Store is constructed/appended by the fixture
launcher **before observation**. Observation uses its existing `head()` method;
that store access is separate from native-state VFS capture and does not establish
an independent external rollback anchor. No new public runtime/MCP entry exists.
The directory has no `__init__.py`: namespace imports support the explicit source
runner while legacy unittest discovery retains its unchanged 26-test scope.

## Capture mechanism and observed implementation corrections

`oc_snapshot_vfs.c` delegates byte reads and POSIX locking to SQLite's standard
`unix` VFS. It preserves a retained descriptor alias and uses one fixed read
transaction per capture, fixed schema/query/authorizer, zero busy timeout, no
retry/sleep, no data mutation/secondary DB/recovery/extensions/SHM/mmap capability.
Native SHARED locks can block writer commits; read atime effects are not denied.
The exact schema constants are normalized CREATE TABLE statements from the pinned
baseline native sources, without importing their constructors.

**Narrow native-open bridge:** direct `/proc/self/fd/N` use first failed with
ELOOP/errno 40 because the native unix VFS opens O_NOFOLLOW. This candidate uses
unix VFS's named `open` syscall hook in its dedicated single-connection process:
only the exact retained-fd alias and readonly flag set can duplicate the already
admitted descriptor. Every other open fails; there is no saved native-open or
mutable-path fallback. Standard unix VFS still owns all reads/locks/unlocks.
This source detail is a review obligation, not presumed covered by design approval.
All descriptors for the inode remain held until SQLite unlock/close completes.

Initial compilation exposed misleading-indentation/unused-result warnings;
source was corrected while retaining `-Wall -Wextra -Werror`. No assertion, timer,
identity predicate or warning gate was waived. No remote failed CI is claimed for
these local compile/probe iterations.

Each native open/transaction/close has a **real 1-second SIGALRM** ending in
non-returning exit 72. No lock is held while awaiting the parent's next request.
`batch.py` starts one owned helper for context-before → job → context-after,
retains pidfd and source descriptors, accepts at most 64 KiB cumulative stdout,
and requires final exact framing, EOF, exit zero and reaping before done. Helper
absolute deadline ≤20 seconds, owner SIGALRM ≤45 seconds. Failure cleanup can
consume up to 2 additional seconds within the outer owner bound; this is not a
fresh observation budget. Signals target only the direct owned helper; pidfd
acquisition failure requires unreaped direct-child WNOWAIT proof before signalling.
No stored backend PID is signalled. STOP_UNCONFIRMED is never advisory done.
**Abrupt death of the external owner is not implemented/proved by this profile.**

## Admission, goal verification and boundary

`facts.py` accepts only a checkpoint/reference on its untrusted observation method.
The trusted fixture launcher supplies retained private roots/helper fd, independently
expected hashes, fresh nonce/epoch and pre-admitted Store. Its closed fixture-only
admission and dossier are not an operator-token format. Owner-only files, checksums
and Python object privacy alone do not authenticate a hostile caller. Host/same-uid/
same-process compromise is outside this standalone trust model; there is no general
production authority API or serialized caller Facts/Decision/verifier boolean path.

Authority, current head, private dossier, repository/workspace, exact job/request/
session/fingerprint/model/provider/current binary and log identities are checked.
Non-null pre-admitted context association is checked against the same existing
native context before/after job/evidence capture, without creating/rebinding context.
All active/failed/uncertain states HOLD. Today's binary is not historical invocation
proof; an original-binary-required profile HOLDs. Current model/provider mappings
are synthetic fixture bindings, not discovered Dev capabilities.

The only implemented goal profile is independently locked **exact full-artifact
size+SHA256**. Expected fixture bytes are fixed before observation, not fitted to
observed output or reassuring text. Full evidence is read and rechecked after helper
stop; no output-page/replacement-decode/prose oracle. The existing pure planner
receives internal Facts only after checks. Success is `OFFLINE_ADVISORY_DONE`,
with `authorizes_actions=false`, `dev_observed=false`,
`original_invocation_verified=false`. A pre-capture HOLD reports helper_stopped=null;
confirmed reap reports true; inability to confirm reports false/STOP_UNCONFIRMED.
No permission, checkpoint, receipt file or backend action is published by observation.

## Current OC disposition — evidence present is not row acceptance

Original [OC definitions](../../../docs/OPENCODE-HANDOFF-CONTROLS-TH.md) stay unchanged.
48 controls are source tests, not 48 pilot trials or a claim all OC rows are closed.
Every row remains pending independent disposition at its named scope:

| Row | Present evidence in this package | Still open / not claimed |
|---|---|---|
| OC01 | Invalid checkpoint prevents capture; pinned old validator reused | Complete malformed-checkpoint family belongs to unchanged 26 controls; no Dev |
| OC02 | Fixture expiry/nonce/epoch/revocation before/after capture | Production current-authority issuer/rollback anchor |
| OC03 | Missing physical/read-lock scope prevents capture | Real shared-state authority; physical pages are not isolated by SELECT |
| OC04 | Actual native-schema SQLite, unrelated running row and source bytes unchanged; no reconcile | Actual Dev/audit/identity-lost native worker integration |
| OC05 | AST/native-import/mutation-call audit, one fixed helper child | No exhaustive native-hook trap/OS syscall sandbox proof |
| OC06 | Actual row identity mismatches, unknown job actual query failure, private prompt absent | Production model/provider/original invocation provenance |
| OC07 | Actual mode/symlink/nlink/entry-swap/schema gates | Cross-user owner changes, non-Linux/reparse, exhaustive race schedule |
| OC08 | Real hot journal/WAL/exclusive writer; shared-lock contention/coherent snapshot; denial callbacks | Exhaustive corrupt/truncated DB corpus and all filesystem variants |
| OC09 | Changed full evidence, after-read mutation, symlink/hardlink rejection | Exhaustive append/truncate/replacement/invalid-text/over-cap interleavings |
| OC10 | Native status family retained or restricted HOLD; exit-zero alone rejected | Actual backend transitions not observed |
| OC11 | Missing/closed/null context; actual close between captures | Production pre-admitted association resolver |
| OC12 | Independently fixed exact artifact profile; changed evidence rejects | General/original Dev goal verifier |
| OC13 | Hash-bound helper/current binary/dossier; caller dict cannot enter observed method | Production source/model/provider trust closure; hostile same-process outside model |
| OC14 | Actual Store CAS/head change; authority revocation after real capture | Whole-store rollback without independent anchor remains BLOCKER |
| OC15 | Actual 1-second lock alarm; owner timer; bounded owned helper kill/reap; failure after success prefix | Abrupt external-owner death, all blocked-device/output schedules remain BLOCKER |
| OC16 | Public receipt sentinel absence, private fixture roots and owned cleanup | Full adversarial OS/audit/retention acceptance |
| OC17 | Joined one-child context/job/context + full evidence + existing planner, advisory only | Acceptance limited to fixture scope |
| OC18 | NOT RUN | All six gates + separate finite Dev approval required |

Six pre-pilot gates remain OPEN: (1) actual backend identity, (2) current real
authority/Facts, (3) accepted capture/side-effect contract including contention,
(4) external ownership/death/stop, (5) independent original-goal verifier, and
(6) finite operator action approval. This source package cannot authorize pilot.
New runtime/authority/privacy surfaces still require SPEC section-14 change control.

## Local validation and CI attribution

Author-local, Python 3.12.14, native helper SQLite 3.45.1, umask 022 and
ResourceWarning-as-error: **48/48 OK**, no skips; unchanged handoff **26/26 OK** and
preparation **18/18 OK**, without executing development/heldout arm trials.
The earlier incremental 41- and 45-control local passes are development snapshots,
not additional trials or replacements for the final suite.

The local broad baseline attempt was **NOT PASS**: discovery reported 98 tests,
4 failures/14 errors (missing httpx/mcp/anyio imports and four existing Codex
process assertions). The process-assertion root cause is not established here;
no claim that all failures are dependency-only or that baseline regression passed
locally. Tests/source were not relaxed or skipped. Exact-head GitHub CI results
must be reported independently in the PR body, with their actual job logs.

The dedicated workflow runs only newly owned offline fixtures, checks exact
48/OK/no-skips plus post-exit warning markers on Python 3.12/3.14, and emits measured
build hashes. It installs no compiler/library. Existing CI workflows, consumed
experiment guards, all baseline source/test/schema/config bytes remain unchanged.
GitHub CI is author-triggered on GitHub, not the operator host or actual Dev.
No source acceptance, live feasibility, measured recovery gain, release readiness
or S24 row closure follows merely from green CI or test count.
