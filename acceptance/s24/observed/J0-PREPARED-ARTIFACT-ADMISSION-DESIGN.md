# J0 consumer-specific prepared-artifact admission — design B

Date: 2 November 2026 (Asia/Bangkok). Input draft #112
`f2ee6d555672ffcacd1e38f5aa40070138982235`.
**DESIGN CANDIDATE / EXECUTION BINDINGS UNBOUND / NOT SOURCE- OR ACTION-READY.**
Operator selected “ทำขั้นถัดไป B” after round-25 requirement-mapping APPROVE.
Exact approval timestamp: NOT_PROVIDED. B authorizes this design only.
No builder, import driver, package fetch, invocation six, guest or new E counter.
[Requirement decision](J0-INSPECTION-IMPORT-DECISION.md) and
[original join contract](WINDOWS-LINUX-JOIN-PLAN.md) remain applicable.

## 1. Concrete consumer and artifact choice

Propose **native Windows WSL2 tar import into one new disposable CI distribution**.
A separately reviewed unprivileged Linux builder would create a fixture-specific
rootfs tar and manifest; the Windows owner would verify the exact resulting bytes
before passing that tar to the exact pinned native WSL client.
Do not directly import the vendor .wsl input or treat its extension as an import
contract. Do not add another variant of the historical strict/catalog producers.

The builder writes archive bytes and private manifest records, never an extracted
vendor tree on the CI host. The native importer is the only proposed actor that
materializes the prepared filesystem, confined by its reviewed target binding to
the new distribution. Its handling of names/links/device omission and host writes
must be independently proved on the exact consumer; it is not assumed safe.

Microsoft documents tar import with explicit distribution/location and version,
and imported distributions initially use root. Per-distribution wsl.conf controls
boot/automount/interop; global .wslconfig affects WSL infrastructure. These facts
do not prove that the present CI image supports boot, containment or this artifact.
Disabling automount/interop is hardening, not a security sandbox against guest root.
Only disposable hosted CI with no operator/production workload is in this proposal.

Official sources checked 2 November 2026:
[custom distro import](https://learn.microsoft.com/windows/wsl/use-custom-distro),
[WSL commands](https://learn.microsoft.com/windows/wsl/reference),
[configuration](https://learn.microsoft.com/windows/wsl/wsl-config).
These pages do not authorize their example install/shutdown commands here.

## 2. Fixed evidence input and construction state machine

Input bytes must match archive SHA256
`bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e`.
The accepted [V2 receipt](LITERAL-CATALOG-ATTEMPT-FIVE-GATE.json) binds
49190 normalized members and ordered catalog SHA256
`89ad212e398c51452cfab1bef956a88ba6a4833376893f17caca23884988587c`.
It is evidence input, not a prepared artifact or execution capability.
Attempt-five bytes were ephemeral; no cache/artifact is claimed available now.
Any later reacquisition is a separately reviewed finite request, not authorized here.

Proposed builder states: input admission → complete metadata/graph preflight →
sealed input/package lock → regular-payload verification → deterministic tar
construction → independent output scan/manifest verification → atomic publish.
No consumer invocation or input execution is part of this builder.
Every failure latches HOLD; no publish, repair, alternate package/lane or retry.
No checkpoint success may be reused after an input/source/config drift.

The preflight recomputes the fixed input digest before parsing, reproduces V2
catalog identity and selected regular hashes, and applies the **additional consumer
policy below** to all effective metadata, including relevant extension fields.
V2 did not authenticate a full payload tree, PAX/xattr policy, dependency closure,
boot behavior or extraction semantics. Additional checks cannot be inferred from it.

## 3. Proposed consumer policy — explicit transformations

This is a new fixture-artifact policy for review, not a change to V2/strict.
Builder uses a metadata graph and bounded regular-payload streams/spools, not
Path/open/resolve on member names, extractall, host links/mknod/chown/mount or
application of archive ownership/modes to host files. Literal names remain literal.

| Input or condition | Proposed output/admission rule |
|---|---|
| REGULAR | Verify/read only through its admitted regular TarInfo; hash every retained payload, not only the seven catalog selections; preserve bytes except explicit owned overlays |
| DIRECTORY | Emit controlled directory headers before children; missing logical parents may be synthesized only by the declared graph rule; conflicting parent types HOLD |
| SYMLINK | Retain as a leaf header only after guest-root-relative graph validation; absolute targets refer to the proposed guest root, never host root; reject escape/cycle/depth >16 and any output entry whose parent is a symlink |
| HARDLINK | Resolve only in the validated archive graph to one admitted REGULAR payload and emit a regular copy; never use extractfile on a link or create a host hardlink; unresolved/cyclic/nonregular target HOLD |
| CHAR_DEVICE / BLOCK_DEVICE | Validate original metadata, then omit ALL such entries from the fixture output under a declared transformation; no named-device exception or mknod. Consumer/runtime device availability must pass compatibility proof; it is not presumed |
| Sparse/FIFO/socket/unknown types | HOLD; no extension of the whitelist |
| Names | Preserve literal backslash/case/Unicode; retain existing slash/control/absolute/duplicate checks. No slash replacement, escape decoding, Windows path interpretation or member-specific exception |
| Symlink targets under runtime mounts | Metadata-only guest-root targets may be marked runtime-unresolved under explicit proc/sys/dev namespaces; never followed by builder. Required executable/library paths must resolve to retained regular bytes, not runtime-unresolved nodes |
| Extensions/attributes | Source must close the exact recognized PAX/long-name/effective-field policy. Reject unknown/security xattr/ACL/capability/sparse metadata; never silently copy unreviewed extension fields |
| Mode/UID/GID/time | Explicit reproducible output policy: regular 0644 or 0755 by reviewed executable classification, directories 0755, no setuid/setgid; root-owned by default. Reserved sensitive/account/temp paths have separately enumerated modes/ownership; all timestamps fixed. No arbitrary inherited privilege bits |
| Collisions | Duplicate normalized paths, file/directory conflicts, overlay collisions or changed protected identity HOLD unless the exact reviewed overlay owns that replacement; no first/last-wins behavior |

Device omission and hardlink expansion are deliberate fixture-image changes,
not a vendor-equivalent rootfs claim or a promotion of catalog acceptance.
Original regular bytes/links/configs cannot be assumed functional after these
changes. Unsupported consumer behavior or loss of a required binary/dependency
ends infeasibility/HOLD, not an automatic new policy variant.

Output is a canonical tar with deterministic logical ordering and reviewed
extension encoding, reconstructed headers and complete per-output-payload hashes.
Independent output inspection must confirm the declared transformations, no
device/hardlink/sparse/unknown output entries, no parent-link writes and unchanged
critical payload hashes. Its receipt has a NEW fixed policy/class, exact schema
and source review; it cannot be accepted by old strict/V1/V2 gates.

## 4. Boot configuration, binaries and packages

The builder owns explicit fixture overlays, with source bytes/hash reviewed before
use. Proposed reserved configuration: no automatic boot command/systemd service,
no fstab processing/drive automount, no Windows interop/PATH injection, no inherited
OOBE/default-user/service startup, locked root/password accounts and one non-sudo
fixture user. New known-hosts/authorization/key material is created only under a
separate runtime setup scope and is never baked into the distributable artifact.
Exact config grammar/bytes and all reserved-path graph checks are source blockers.
No existing host/global .wslconfig, feature, firewall or portproxy edit is allowed.

| Binary prerequisite | Evidence now / required binding |
|---|---|
| Python | Vendor usr/bin/python3.12 hash a92f0f95… and unresolved python3 symlink exist in receipt. Full stdlib, loader/shared libraries, executable identity and supported runtime behavior remain UNBOUND; no host execution/ldd/version inference |
| Guest sshd | No usr/sbin/sshd selected entry was returned. Do not infer alternate-path absence/presence or run an installer. Its exact package/binary plus complete dependency/helper/data closure must be bound before build acceptance |
| Guest setup/probe helpers | Separately named, exact source/hash/argv and ownership; no claim existing baseline two-file transfer approval covers these writers/wrappers |
| Windows SSH/WSL/kernel | Exact configured-client/kernel identity, boot/virtualization/coexistence and native route proof remain UNBOUND. Historical candidate-path absence is not global absence or permission to update |

Any package overlay uses a **sealed finite lock**, not adaptive apt/pip/curl or
maintainer/postinstall scripts. Each exact object has authenticated metadata/
trust-anchor policy, version/architecture/URL/size/SHA256, dependency edges,
overlay paths and conflict handling. Do not execute input binaries, scripts,
triggers or package hooks on the builder. Required postinstall effects must be
explicit declarative fixture overlays or the package strategy is infeasible.
Metadata/signatures and package identities are presently UNBOUND; none are invented.
The catalog's provider_signature_verified=false remains unchanged.

## 5. Immutable artifact/manifest and transfer admission

Proposed fixed manifest class: j0-wsl2-prepared-fixture-manifest-v1, schema 1.
Source must provide a closed schema and independent verifier before execution.
Required bounded fields: input/archive/catalog/source/policy/config lock hashes;
all package object identities and graph; transformation totals and ordered input/
output catalog roots; complete private path/type/mode/ownership/content-hash index;
critical binary/loader/library/stdlib closure; output tar size/SHA256; reproducibility
parameters and exact manifest digest. No keys/credentials/raw file contents.

Public receipt is an allowlisted summary of digests/counts/fixed reasons only.
Private full path/package/index evidence is retained in an owned 0700 workspace,
not dumped in public logs. A cross-job protected carrier is UNBOUND: ordinary
artifact upload is not assumed confidential. No unredacted index or prepared tar
may leave that workspace until an explicit protected/approved transfer policy is
reviewed and bound. Size/count/depth bounds apply before parsing or publishing.

Proposed publication protocol on the supported Linux builder: retain trusted parent
dirfd; create one exclusive 0700 staging generation; create tar/index/manifest with
O_EXCL/O_NOFOLLOW and 0600; fsync, close and independently reopen/read back the
complete pair and its digests; fsync staging; publish using atomic no-replace
rename of the generation directory, then fsync the parent. Missing no-replace /
filesystem guarantees HOLD, with no overwrite or copy fallback. Existing names/
symlinks/modes reject, never chmod repair. Partial/orphan generations are not
admissible and are preserved under the bounded failure policy; source/controls
must prove crash/fsync and exact newly-owned cleanup behavior. This protocol
assumes the trusted current CI uid and does not defeat a malicious same-uid writer.

The Windows consumer verifies approved source/lock, actual artifact/manifest hashes,
private ACL/owner/reparse/size and new-destination bindings before import. Bind the
verified bytes to the bytes consumed: source must prove a retained deny-write/delete
handle strategy or another reviewed TOCTOU-safe method supported by that WSL client.
A check-then-import numeric path without that proof is HOLD. Artifact upload/download
hashes and provenance are verified end-to-end; CI artifact ID alone is not identity.

No prepared hash or completion flag is assigned today. A future artifact-created/
digest-verified receipt proves only those facts. Import-compatibility/guest/J0/R1/R2/
scope remain false until their own independently reviewed evidence exists.
Original strict archive_inspection_verified and every old receipt remain unchanged.

## 6. Actors, proposed budgets and lifecycle authority

These are proposed bounds for NEW preparation actors, not changes to any existing
catalog/observer/worker/sampler/controller budgets. Feasibility is NOT TESTED.

| Actor | Read/write and proposed bound |
|---|---|
| Linux unprivileged builder | Fixed rootfs input <=1 GiB plus <=64 prelocked package objects, total <=512 MiB; at most one approved request/object, no retries/discovery; full object list frozen before action |
| Builder process/job | Process <=300 s, address space <=1 GiB/no core; job <=10 min; HTTP operation <=15 s. Private temp workspace only; aggregate decoded logical bytes across rootfs and all packages <=4 GiB, output tar <=4 GiB, private manifest <=1 GiB, aggregate input/output counts each <=200000 entries, <=4096 name/link chars |
| Builder disk/ownership | Admission free space >=16 GiB and declared write cap <=12 GiB; no root, service/package install or input execution; explicit owned cleanup after preserving bounded evidence. Missing resource proof HOLD |
| Windows outer owner | Separate exact-hash driver outside guest/SSH; starts before any distribution creation; retained child identity/start-time, actor/writer ledger, absolute setup deadline <=240 s; job <=6 min |
| Import/bootstrap steps | Import <=90 s; first boot <=30 s; explicit bootstrap <=30 s; read-only verification <=20 s; stop/confirmation <=30 s; evidence flush <=10 s, all inside outer deadline; no respawn/retry |
| Joined controller/sampler | Existing source/timer/window/no-delay contract unchanged; no cached CIM, ACK wait, SIGSTOP/sleep/input inflation or warm sampler lifetime change under this design |

The proposed limits need exact enforcement source and positive feasibility evidence;
they are not claims this runner has enough resources or that a timeout stops WSL.
No global VM resource configuration is changed to make the route fit.

Only the new distro name/install root, creation receipt and targeted lifecycle
are in proposed scope; every native operation uses that bound identity explicitly.
No default distro/version selection, global shutdown, service/engine kill, existing
distro stop, automatic WSL/kernel install/update or reboot. WSL engine/CIM remain
host infrastructure, not owned subprocess descendants.
SSHD is foreground inside that distro, new fixture user/ephemeral keys only, strict
known-hosts, password/PAM/root login/forwarding/TTY/UserRC disabled and exact forced
command; no auto service. Bind listener/endpoint and one-connection case scope
without alternate port/reconnect on failure.

Outer cleanup distinguishes exact owned Windows child exit from distro cessation.
A targeted terminate request/CLI exit is not alone proof that every guest/provider/
external writer stopped. Reconcile named stopped state and the reviewed actor/
writer evidence; unknown stop latches HOLD and blocks restart/reuse/public success.
Unregister is a separately approved destructive cleanup step requiring matching
creation binding, confirmed stopped state and preserved evidence. Never delete
existing names/paths/evidence to regain an attempt. Artifact preservation and guest
cleanup have separate ownership; neither CI teardown nor pipe EOF is R1 stop proof.

## 7. Preregistered controls and finite source exit

| Control family | Evidence required before any dependent approval |
|---|---|
| No side effects before admission | Hash/lock/config/ACL/owner/source drift fails before network/build/import/guest action; fixed failures do not echo inputs |
| Real synthetic tar and graph | Literal/slash names, duplicate/parent-link/cycle/escape/runtime-link rules; hardlink-to-regular byte identity; generic device omission; all unsupported/PAX/limit/collision negatives reach their stimulus |
| Complete output identity | Independent full-payload/manifest verification, protected overlays, deterministic repeat build from identical synthetic inputs, atomic publish/readback and partial-write/fsync/preserve faults |
| Binary/package closure | Missing sshd/library/stdlib/helper/trust anchor, incompatible architecture, package collision, unresolved hooks and missing hashes HOLD; no host execution or dependency download fallback |
| Consumer compatibility | On separately approved disposable WSL fixture, prove exact importer name/link/config/mode behavior and host-write confinement, no unintended auto-start/drive/interop behavior, boot/pidfd/procfs/Python/foreground sshd and native Windows reachability |
| Ownership/stop/deadlines | Import/boot/start/blockage/owner-loss/failure tests preserve evidence and reach actual stop predicates; client exit, job teardown or missing PID cannot masquerade as complete cessation |
| Existing contracts | Old strict/V1/V2 tests/pins/results/false flags and all eighteen rows retained. Native Windows SSH, guest collect and fresh Windows CIM must later be proved in the SAME invocation |

Compatibility/import controls themselves require exact actors/bytes, private creation/
stop bindings, source review and separate finite action approval BEFORE running.
They are not a pretext to boot the real artifact while admission remains unknown.
Any confirmed incompatibility returns to explicit design disposition or A/C, not an
automatic parser/consumer-policy increment or sixth invocation.

Design exit requested: independent acceptance of this selected consumer,
transformations, trust/flag boundaries, proposed budgets/controls and HOLD conditions.
Then exact builder/verifier/manifest and owner source may be prepared offline.
**Source/action acceptance remains BLOCKED** while any required binding below is
UNBOUND; synthetic source controls alone cannot discharge these facts.

| Blocking execution binding | Current state |
|---|---|
| Immutable package object/trust/dependency lock, executable/library/stdlib closure | UNBOUND |
| Exact generated configs/overlays/user/source hashes and closed extension/output format | UNBOUND |
| Actual prepared artifact/full manifest hashes and protected retention/transfer | NOT BUILT |
| WSL/client/configured kernel/boot/coexistence and import TOCTOU method | UNBOUND / NOT TESTED |
| Distro/path/key/port/owner/stop authority and enforcement implementation | UNBOUND |
| Actual consumer compatibility and complete writer/cessation evidence | NOT TESTED |
| Operational A6/A7 and joined full package acceptance | OPEN |

Finite success is a closed reviewed design/source/input/owner plan with actual hashes
before action; finite failure is declared infeasibility/HOLD or explicit A/C selection.
No placeholder is a pass, no repeated catalog measurement is required to settle
this design, and there is no guarantee this CI route can satisfy J0.
FIVE consumed invocations / FOUR digest matches, E12 UNKNOWN; no sixth authorization.
All eighteen rows OPEN; #112 draft; J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD;
#80/#96/private bindings/release/deployment unchanged. Any normative/security-boundary
conflict requires SPEC §14 review before implementation is merged.
