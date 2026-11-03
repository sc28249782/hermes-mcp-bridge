# OpenCode source contract — SQLite snapshot and retained identity

Date: 3 November 2026. Input #117 `7fb2088f`, operator-supplied APPROVE AS DESIGN.
The following “ทำขั้นถัดไป” requests source contracts, not implementation or Dev
execution. **CONTRACT CANDIDATE; NO CAPTURE HELPER/VFS IS IMPLEMENTED OR TESTED.**

## 1. Selected method and explicit effect boundary

Select a Linux-only native **read-only VFS shim around SQLite's standard unix VFS**,
with an owned retained-FD handoff and one short SQLite read transaction. Do not
implement a new SQLite locking protocol, parse a copied live DB in memory,
use immutable/nolock, or delegate source access to Python's default VFS.
The shim's purpose is to deny filesystem writes/secondary opens at the VFS
boundary while retaining SQLite's supported read locking and snapshot semantics.

A normal read transaction takes SHARED locks and can briefly defer a writer's
commit. This is NOT a zero-interference observation. The existing “no worker delay”
rule remains a ban on deliberately stopping/prolonging work to create an
observation window; this contract additionally exposes ordinary lock contention
for independent review. Any interpretation requiring literally zero writer
blocking is incompatible with this selected method: HOLD/choose another reviewed
method, no implicit waiver. No lock is held waiting for a sample or worker state.
The future finite read authority must expressly cover shared-file read locking;
absent that permission, HOLD before any transaction. Ordinary reads may also update
filesystem access times: denial of VFS writes is not a zero-metadata-effect claim.
No-source-write controls cover bytes/rows/schema/journals/audit/permissions/entries;
read-access timestamp effects must be disclosed in the read scope. No action is approved here.

Proposed lock residence <=1 s within the existing helper <=20 s / owner <=45 s,
not a widened budget. busy timeout is zero, no busy handler/retry/poll loop; lock
conflict aborts the one capture. Exact source, native stop and real concurrent
writer controls must prove this behavior or report stop-unconfirmed. No positive
feasibility or hard real-time guarantee is claimed for an uninterruptible I/O fault.

## 2. Proposed source and capability handoff

Planned source names, not existing artifacts:
- oc_snapshot_owner.py: approved authority/dossier resolver, trusted-dirfd opens,
  owned native child launch/deadline/stop, private response admission.
- oc_snapshot_vfs.c: fixed read-only VFS + fixed prepared SELECTs + private bounded
  result, linked to an exact reviewed SQLite/compiler/libc/runtime set.
- opencode_facts.py: current admission/context/model/binary checks, independent
  verifier invocation and trusted Facts construction per the [Facts contract](OPENCODE-HANDOFF-FACTS-CONTRACT.md).

No package installation/compiler/source download or dependency pin is invented.
Actual helper/compiler/SQLite artifacts/source versions/options/hashes remain
UNBOUND until the source package supplies them. No runtime import/constructor
of OpenCodeTasks/ContextRegistry, no native status/result/recent/reconcile call.

The trusted owner opens the exact reviewed private directory chain using dirfds,
O_NOFOLLOW and owner/mode/type checks. Source DB is O_RDONLY, regular, single-link,
0600 and same approved uid; directories 0700, outside allowed workspaces. Reject
symlink, group/world access, changed/missing identity; never chmod/repair.
DB size <=64 MiB, no NFS/DrvFS/WAL/unreviewed filesystem. Physical access to the
shared DB requires explicit authority even when only one row is returned.

Pass only explicitly owned O_RDONLY DB and trusted-directory descriptors to the
one child, plus a private capability request over a fixed pipe; close other fds.
The request names a pre-admitted role and exact target IDs, not arbitrary paths,
SQL, VFS names, pragmas, extensions or callbacks. Source pins and descriptor
identity checks occur before launch and again on checked result admission.
Only owner-created handles are inherited; root descriptors give no action authority.

A dedicated helper connection uses the explicitly selected shim and PRIVATECACHE.
The shim must open/reopen the admitted inode through its retained descriptor,
using only an exact process-local fd alias supported by the inspected unix VFS.
xFullPathname must not turn that alias into an attacker-replaceable source path.
No direct-path fallback. If exact native FD/lock/alias identity cannot be proved,
the platform is unsupported. This is a source/proof obligation, not an assertion
that SQLite's default unix VFS already guarantees it.

## 3. Closed VFS and SQL surface

| Surface | Required implementation behavior |
|---|---|
| Main DB xOpen | Exactly one admitted role/inode per transaction, READONLY/MAIN_DB only; reject CREATE/READWRITE/DELETEONCLOSE, unknown flags, alternate names/URIs or additional DBs |
| Sidecars | Owner probes exact -journal/-wal/-shm names with no-follow metadata only; ANY existing sidecar rejects, including empty/cold files. VFS must not hide existing journals as absent |
| xAccess | Map only admitted main/known sidecar probes to trusted retained directory; any unknown lookup or sidecar presence/error fails closed |
| xWrite/xTruncate/xDelete/xSync | Deny mutation; no delegation of data/size/deletion/sync requests to source filesystem |
| Shared memory/mmap | Deny xShm* access/WAL and source mmap; xFetch returns no mapped region; use bounded reads |
| xLock/xUnlock/xCheckReservedLock | Delegate standard unix locking with admitted descriptor identity; SHARED/NONE only, never request RESERVED/PENDING/EXCLUSIVE; reject busy, no custom/no-lock/exclusive VFS |
| xFileControl | Closed reviewed safe-query whitelist only; unknown/changing/locking-strategy operations reject or return the required NOTFOUND behavior, never blindly delegate |
| Extensions/dynamic load | Disabled; no ATTACH, VACUUM, writable_schema, triggers/views/virtual tables/user functions, user SQL, custom collations or filesystem functions |
| SQLite runtime options | Source must bind defensive/trusted-schema/authorizer/resource/progress settings and prove support; no option is presumed present from a version string |
| Output | Fixed private metadata record <=64 KiB, no raw prompt/output/config/exception text, no public stdout/stderr dump |

Require rollback-journal format, both header read/write versions 1, and the exact
reviewed native jobs or contexts schema. These prechecks do not replace a SQLite
transaction. SQLite never gets a source writable handle or a second file target.
If it requests journal recovery, WAL/SHM or unsupported VFS work, abort, no repair.
Race cases must exercise real accesses; a precheck-only rejection is insufficient
to claim that a downstream attempted write/open would have been denied.

Acquire one normal read transaction, validate the exact schema without running
user schema features, execute fixed bound-parameter queries, finalize statements,
commit/close the READ transaction and release locks within budget. A transaction
pins row coherence, not all filesystem objects or both databases simultaneously.
Context queries are separately bounded as described in the Facts contract.
No source DB bytes are copied/backed up/serialized or exported. SQLite may still
read prompt-containing pages internally; that physical shared-state access is
part of the admission, never a claim of single-row byte isolation.

The job query selects exactly the admitted job's identity/workspace/model/binary,
status/exit and transition fields, protected original fingerprint for comparison,
and bounded output references/caps. It does NOT select prompt text or arbitrary
rows. Fingerprint value stays private and is never recomputed from prompts.
Schema allowlist includes exact expected indices; no schema migration/DDL.
Close must be confirmed even after a failed open with partially initialized VFS.

## 4. TOCTOU, result files and as-of semantics

Retain owner directory/file identities and recheck directory-entry-to-inode
bindings before/after the read transaction and before publishing its advisory
receipt. A rename/unlink/entry replacement causes HOLD; the handle is not rebound
to another numeric path. Trusted cooperating native writers may update DB content
under normal SQLite locks. A hostile same-uid writer bypassing SQLite locking or
rewriting trusted directories is outside this limited model, not defeated by
before/after stat/hash checks.

Native result references are never opened from raw checkpoint/log_path strings.
Resolve the dossier-bound object beneath the retained trusted logs directory,
compare its binding to the selected native row and approved owner, then open
O_RDONLY/O_NOFOLLOW, require regular/single-link/0600/approved uid and cap <=8 MiB.
Read full exact bytes through the retained handle; verify size/identity and full
evidence digest, recheck binding before publication. Mutation/truncation/drift
or missing immutable evidence guarantees HOLD; no accepted prefix/UTF-8 replacement.
No all-writer quiescence claim from a stable fstat/hash pair.

The DB row snapshot, context observations and result-file capture have separate
as-of provenance/sequence; no global atomic snapshot or clock-sync claim.
The [Facts contract](OPENCODE-HANDOFF-FACTS-CONTRACT.md) admits only the supported
completed-job/evidence profile and rejects incompatible component observations.

## 5. Required source evidence and exit

Refines OC03/04/07/08/09/15, without marking any control passed:
- Real standard-unix writer commits before/after the read snapshot show a coherent
  row; conflicting writer, bounded contention, no-lock strategy and timeout fail.
- Journal/WAL/SHM/recovery and every mutation/extra-open attempt reach the actual
  shim and are denied; source files/audit/rows/permissions remain unchanged.
- Path/FD alias replacement, inode reuse, closed descriptor, unsupported VFS and
  partial-open cleanup cannot yield an admitted row.
- Query authorizer and exact native-schema tests prove no prompt projection,
  arbitrary row/SQL/function/extension access or raw output leakage.
- Owned deadline/kill/reap proves helper stop and lock release, or honestly reports
  unconfirmed stop. No claim that the owner stops native OpenCode processes.

Implementation must include exact shim/dependency sources/build/runtime pins and
real filesystem/SQLite controls, not mocked read results alone. If the retained-FD
shim or contention contract cannot be implemented on the bound platform, report
infeasibility; do not fall back to default Python SQLite, live copy or another
method without review. This contract acceptance would select source work only,
not close OC18, six pilot gates or authorize Dev access.

Primary mechanism references checked read-only 3 November 2026:
[SQLite VFS](https://www.sqlite.org/vfs.html),
[I/O methods](https://www.sqlite.org/c3ref/io_methods.html),
[rollback locking](https://www.sqlite.org/lockingv3.html),
[open flags](https://www.sqlite.org/c3ref/c_open_autoproxy.html),
[WAL read-only caveats](https://www.sqlite.org/wal.html).
These justify the proposed interface, not an implemented/proved shim.
J0 remains PAUSED; no Dev/backend/pilot/source execution, no #112 change.
