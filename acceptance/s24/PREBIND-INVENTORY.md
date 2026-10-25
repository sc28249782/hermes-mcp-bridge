# Private metadata preparation inventory — source for review

Status: **OFFLINE SOURCE / NO GUEST SCOPE / R2 HOLD**.
Parent: [binding work package](../../docs/S24-METADATA-BINDING-WORK-PACKAGE-TH.md#s24-metadata-binding-work-package).

## What this helper does

`prebind_inventory.py` uses the Python standard library only. It reads exact
nominated preparation files and fixed guest system metadata. It can write one new
`binding-inventory.json` evidence file. It does not launch a program, open a network
connection, bind a listener, call an API, import the candidate/fixture or modify an
input. Input inspection is read-only; evidence creation is an explicit write.

The helper checks the pinned client/peer/manifest bytes and saved version string.
It checks the exact inactive JSON-formatted profile as YAML-compatible data.
The venv argv, selected loopback health port and attempt directory are explicit
private nominations. Extra channels, active commands, literal credentials, alternate
control-plane URLs, bool-for-int changes, duplicate keys and nonfinite values fail.
Tunnel-ID syntax follows the pinned client's plain/namespaced shape; syntax is not
entitlement, authentication or Platform association.

The helper checks key metadata with stat and never opens the designated runtime-key
file for reading. Symlinks, hardlinks, FIFO, unsafe mode and an interpreter alias to
that file fail before a key-content open. It does not validate the credential.
Do not send a key, profile, private report, process inventory or account ID to chat.

The helper compares the resolved interpreter bytes to the saved local inspection
identity while preserving its nominated venv argv. Distribution identity comes
from the saved dependency JSON, not a fresh interpreter or installed-package scan.
It does not spawn the nominated interpreter or client/peer, or import the SDK. Saved observations remain
saved observations; the helper cannot authenticate them.

Root/attempt directories must be same-owner 0700. Descriptor-relative traversal
rejects symlink components for nominated private paths. Read inputs are bounded,
regular, single-link files; descriptor/path identities are compared across reads.
The explicitly permitted venv interpreter symlink is resolved separately and
checked against saved identity. This is not protection against trusted same-user
replacement after inspection, malicious saved evidence or a compromised host.
Fixed procfs/sysfs reads have leaf no-follow checks, not a general ancestor-isolation
claim. No machine-attestation or original-runtime observation is produced.

Guest data includes Linux/x86_64 and VMware checks, MemAvailable, filesystem free
bytes, the nominated port's TCP-table snapshot and this process's cgroup text.
It enumerates no other account's argv and performs no cgroup write, migration or
delegation test. These observations do not prove process-cohort enforcement,
port reservation, global quiescence, cgroup headroom or writer cessation.
Disk/growth/log-series, Windows memory and original continuity remain separate gaps.

Every normal report fixes `key_contents_read`, `scope_granted`, `host_observed`,
`original_runtime_continuity_observed`, `authenticated`,
`complete_writer_coverage`, `containment_or_delegation_proved`,
`r1_complete` and `r2_authorized` to false. Forged true flags are rejected by the
record writer. Direct Python callers are trusted test/library callers; arbitrary
code can fabricate data. These flags/hashes are not authenticated evidence or tokens.

## Failure, timing and private evidence

The collection checks a 30-second elapsed limit between operations and after
sampling. This is post-hoc rejection, not interruption of blocked I/O.
The evidence writer is also synchronous. Independently reviewed foreground
control/timeout/stop targeting and a valid finite scope are required before a run.
The helper does not generate an approval, create/reset a window marker or extend
an existing deadline. Do not treat its internal elapsed counter as scope timing.

The output is O_EXCL/O_NOFOLLOW 0600, with file and parent-directory fsync.
The collector rejects an existing output before inspecting input files.
No output overwrite, stale removal or automatic retry is provided.
An error can leave no report or a partial report, including on failed fsync.
Keep partial files; no success receipt is invented. Any rerun needs disposition
under a valid scope, not deletion or reuse of the old evidence path.

Only a constant HOLD is printed for ordinary CLI failures. Successful stdout
contains a status/hash and false scope flags, not private paths or raw observations.
The private JSON contains actual nominations, file metadata and guest values.
Its hash covers exact bytes including the final newline; it is correlation only.

## Combined inventory scope proposed for later review

This is a proposed action list, not an executable scope or permission request.
No guest/host command is to be run from this document now.

| Part | Proposed exact action class | Excluded action |
| --- | --- | --- |
| Transfer | After exact-source review, obtain this one helper from the reviewed immutable revision into a new nominated private source path and verify its reviewed SHA-256 | Floating main, overlay, package install or modification of prepared input/evidence |
| Local authority | Operator inspects the new tunnel's organization/workspace and key principal's Read + Use grants in the local UI; retain private observations and limits | Creating/replacing keys, account/role changes, plugin connection or discovery |
| Windows | Read the already reviewed local CIM memory value before/during/after; separately nominate exact host/control identity privately | Changing VM/host policy or calling a cloud/remote machine |
| Guest | Under a proposed new R1 scope of at most 900 seconds, invoke the exact reviewed helper once with nominated root, attempt name, venv argv and health port | Client/peer/doctor, API request, original-runtime call, credential read/export or state mutation |
| Evidence | Create the single new private inventory file; return stdout summary and operator observations | Uploading the private report or claiming all binding fields are complete |
| Original continuity | First review/bind exact observation source, transport, projected fields and bounds as part of this work package | Calling an unidentified original endpoint/tool or treating absence of a probe as healthy continuity |

The future invocation shape is deliberately non-runnable:

`<REVIEWED_PYTHON_ARGV> -I -S -B <REVIEWED_HELPER_FILE> --root <PRIVATE_ROOT> --attempt-name <PRIVATE_ATTEMPT_NAME> --python-argv <BOUND_VENV_ARGV> --health-port <BOUND_PORT>`

The helper-only invocation disables site initialization with \`-S\`; it does not\nchange the metadata peer's separately bound venv argv.\nPrivate values and independent control/stop methods must be complete before asking
for that guest scope. The script hash/version, output path, all read paths,
Windows/UI methods and the full allowed duration belong in the actual request.
This helper does not fill host/control authority, actual credential validity,
original continuity or complete process/observer/supervision/stop/writer bindings.
An authenticated GET, loader, controller or setup needs separate reviewed source
and exact scope. R2 remains gated by the full work package, not this helper.

## Offline controls

Twenty-two controls use synthetic private files, injected guest metadata and unit
clocks. They test positive strict inspection without secret open/spawn/socket,
exclusive durable evidence, input drift, active/extra-channel/literal-key/bool and
JSON failures, tunnel/port nomination, unsafe key/path types, saved interpreter
alias/drift, saved dependency drift, missing/low/occupied observations, expiry,
directory/file identity changes, forged scope flags, partial writes and private
CLI errors. Fake executable bytes are unit data and are never executed.
Tests do not inspect the operator's guest, account, credential or saved report.

Dedicated Linux CI adds this suite under the unchanged post-exit warning scanner.
All earlier candidate/fixture/contracts/observer/supervisor sources and checks
remain unchanged. No unit/CI result is guest readiness, R1 completion, R2 route
proof, complete cessation, Phase B acceptance or a scoped §22 PASS.
