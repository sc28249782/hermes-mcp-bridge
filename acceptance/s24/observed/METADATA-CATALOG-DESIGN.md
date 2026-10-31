# E18 — separate rootfs metadata catalog policy, design for review

Date: 31 October 2026. Reviewed input: E17 record at `ed038d6e`.
Status: **DESIGN ONLY; NO POLICY IMPLEMENTATION / FOURTH REQUEST / PROVISIONING**.
Continue the same draft #112 and [J0 join plan](WINDOWS-LINUX-JOIN-PLAN.md).

## 1. Evidence boundary and count correction

| Actual invocation | Digest milestone | Inspection / diagnostic result |
| --- | --- | --- |
| E12, run 41170222586 | UNKNOWN; no computed digest emitted | constant HOLD, stage UNKNOWN |
| E14, run 41195199976 | 388,975,696 bytes, bb415d82… match | ARCHIVE_PARSE/PREDICATE_REJECTED; specific predicate UNKNOWN |
| E17, run 41200750250 | 388,975,696 bytes, bb415d82… match | ARCHIVE_PARSE/PREDICATE_REJECTED/TYPE_REJECTED |

Three live invocations were authorized and consumed. **Two** have recorded full-
archive digest equality (E14 and E17), not three. E12 stays UNKNOWN; do not infer
its download/hash result from later matching bytes. E17's parsed_members=5 counts
normalized unique names admitted before remaining checks; it does not establish
a sixth raw tar header/member, path or subtype. Preserve all three JSON records.
These corrections concern evidence claims, not retraction of the approved runs.

The only observed subtype fact is E17's actual false predicate:
`item.isreg() or item.isdir() or item.issym() or item.islnk()`.
A character/block device is a hypothesis, not an observed finding. No device
name, character/block/FIFO kind, corruption or maliciousness has been proved.
This design considers a catalog policy independently of that unknown subtype.

## 2. Chosen policy: explicitly named catalog lane

Propose fixed policy ID `ROOTFS_METADATA_CATALOG_V1`, implemented later in a
separately named producer and gate. Source/asset hashes and exact invocation are
UNBOUND until implementation/source review. Do not repurpose or silently change
the current strict producer/gate or convert their existing HOLD into a pass.
No config-controlled arbitrary whitelist or automatic fallback from strict mode.
The current TYPE_REJECTED predicate remains the current strict-mode contract.

The new lane would permit six disjoint logical entry classes FOR CATALOG ONLY:

| Logical class | Classification and allowed work |
| --- | --- |
| REGULAR | Existing isreg() classification; hash payload ONLY when the existing fixed selected() predicate matches, within its original cap |
| DIRECTORY | Existing isdir(); header metadata only; no path/directory creation |
| SYMLINK | Existing issym(); header/link metadata only; never resolve or follow |
| HARDLINK | Existing islnk(); header/link metadata only; never resolve or follow |
| CHAR_DEVICE | Exact tarfile.CHRTYPE after the original four classifications; validated header metadata only |
| BLOCK_DEVICE | Exact tarfile.BLKTYPE after the original four classifications; validated header metadata only |

Classification is ordered as listed, one class per returned logical TarInfo.
FIFO, socket/other/unknown returned member types remain HOLD. Sparse records
remain rejected BEFORE this classification. Parser-internal extension handling
is not permission to admit an unsupported returned logical member. Exact Python/
tarfile behavior must be tested on both supported versions during source review.
No special casing of named members, directories such as dev, archive version,
member index or the current failing count is permitted.

This is an explicit extension of CATALOG admission, not a claim that the original
whitelist had a defect. Later extraction/import/guest execution has a separate
admission policy and approval; this catalog policy grants none of those actions.

## 3. Device metadata and selected-file rules

Both new device classes require declared size ZERO, empty linkname and integer
(non-bool) devmajor/devminor in 0..2^32-1. These are bounded catalog fields, not
claims about target-kernel device-number support. Mode/UID/GID must be bounded
nonnegative integers compatible with the reviewed gate (<=2^63-1). Invalid
metadata ends HOLD; no repair, truncation, inferred default or node creation.
Device numbers enter the catalog hash only, never a diagnostic/public per-device
record. Do not open a device path, call mknod/mount, prepare ACL/ownership or apply
archive mode/UID/GID to host files. No device payload stream may be requested.

Call extractfile ONLY for an admitted REGULAR entry matching the existing fixed
selected() predicate. Device entries must never reach extractfile, content hashing,
selected binary identity or source loader, including names matching that predicate.
A selected-name/device collision ends HOLD with a fixed reason, not a silent skip
or a guest-binary claim. Existing selected dir/link records retain their disclosed
metadata-only status; they do not gain content hashes or link-resolution proof.

Headers of non-selected entries contribute only to the ordered catalog hash.
Tar streaming may read/decompress/skip bytes while advancing; metadata-only does
not mean no archive I/O. Zero-size device checks and the unchanged byte/logical/
member/wall/memory caps bound that work. No member is materialized on disk.

## 4. Receipt, diagnostics and independent gate

Use a NEW receipt class `j0-rootfs-metadata-catalog-only`, schema 1, with the fixed
policy ID. A complete run may set metadata_catalog_complete=true and record the
full archive SHA/byte count, declared logical bytes, member count and six-key
closed type_counts map. All count values are strict bounded integers, sum to the
same normalized member count, and each entry is counted exactly once.

The catalog digest must include a fixed policy-ID domain prefix followed by
canonical ordered header records. Commit the original name/type/size/mode/UID/GID/
link fields and device major/minor for device classes. Never print device names,
raw type bytes/numbers or per-device metadata; emit only aggregate class counts
and the digest. Public selected-entry metadata/hashes remain restricted to the
existing selector names and supported original classes. This is still a header
catalog plus selected regular contents, not a complete content-tree manifest.

Keep archive_inspection_verified=false (the current strict-lane meaning),
prepared_guest_artifact=false, extraction_authorized=false,
import_compatibility_tested=false, setup_ready=false, j0_ready=false,
guest_imported=false, guest_started=false and all R1/R2/scope flags false.
A new metadata_catalog_complete flag is not a release, signature, prepared image,
J0/source acceptance or credential/authorization token. Gate/UI labels must say
CATALOG ONLY, never substitute the old strict success class.

The NEW diagnostic class `j0-metadata-catalog-diagnostic-only`, schema 1, may reuse
the finite stages/errors/byte/hash/member milestones and E16 predicate vocabulary,
adding ONLY DEVICE_METADATA_REJECTED and SELECTED_DEVICE_COLLISION. These reason
labels carry no input values. This new diagnostic has a mandatory six-key
type_counts map and strict boolean type_counts_complete: false on every failure,
true only after successful catalog EOF. Update a class count only after the
entry passes type/header eligibility. On failure the sum is <= parsed_members,
not a claimed complete catalog; on success it equals parsed_members and exactly
matches the receipt map. No optional/raw extra keys. Do not silently add fields/
enums to historical strict schema 2. Missing/invalid/extra/unavailable
output and every failed predicate/deadline/EOF remain HOLD, without recovery.

Retain exactly-two-line bounded protocol: inspection/catalog or constant HOLD
first (<=65,536 bytes), bounded diagnostic second (<=2,048), total <=67,586.
A separately checked new gate validates exact schemas/key sets/policy ID, false
flags, counts, selected entries and cross-frame archive/hash/member consistency.
Scan warning/finalizer/traceback markers before acceptance; never cat raw stderr,
exception text, URL/redirect target, temporary path, content or credential. A
successful catalog receipt proves only this new policy's completed metadata work.

## 5. Preserved budgets, actors and required controls

The proposed future actor remains one disposable GitHub-hosted Linux Python
process: same pinned provider URL/digest/receipt, HTTPS verification, no proxy/
redirect/retry/fallback, one new private temporary archive, hash BEFORE parser,
no root/subprocess/SSH/WSL/guest/package action. Retain 1 GiB archive, 200,000
logical members, 4 GiB declared size, 32 MiB selected file, 32 selected entries,
4096-character name/link, 120 s and 512 MiB caps. No output cache or archive from
another run may be presented as this invocation's evidence. Original strict
sources/pins/controls and actual records stay unchanged by this design.

Implementation/source review must demonstrate:

- Unchanged strict regression results; the original TYPE_REJECTED still rejects
  both devices in strict mode with the original verdict.
- Actual synthetic char/block tar headers reach new catalog-only counts/hash,
  while extractfile is trapped/asserted NEVER called for them or any dir/link.
- Device payload size, linkname, negative/bool/oversized major/minor and selected
  collisions reject; failures emit only fixed enums/partial milestones.
- FIFO/unknown type, sparse, path/duplicate/root/size/count/link and all existing
  parser/download/identity/error privacy controls remain fail-closed.
- Same-name device-number changes alter catalog hash; policy ID domain separates
  the new catalog from strict output; counts agree without leaking header values.
- Gate rejects old strict success/failure classes as new catalog evidence,
  false-flag promotion, duplicate/unknown JSON, count/digest/frame mismatch and
  any attempt to turn a catalog receipt into extraction/import authorization.

Source controls are synthetic, not additional observations about the provider
archive. Limits may be reduced only in fixtures, never in live verdict claims.

## 6. Design exit and next boundary

Review this explicit new lane/type/device/receipt/selection contract first. Then
implement exact separate source/gate + controls, compute real hashes and obtain
source review. Only after that may the operator consider ONE new separately
scoped CI attempt with an unused selector. No source implementation, fourth
request, guest setup or extraction/import exists in E18. Current live job stays
hard-disabled; spent E12/E14/E17 selectors remain consumed.

If accepted later, catalog evidence could support guest artifact/setup source
preparation alongside still-open kernel/boot/ports/lifecycle/private bindings.
It cannot itself close them or any of the eighteen integration rows. Keep #112
draft/unmerged; J0 NOT READY; R1 NOT AUTHORIZED; R2 HOLD; #80/#96 unchanged.
