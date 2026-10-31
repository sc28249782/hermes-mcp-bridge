# J0 metadata catalog source candidate — A2/A3 prerequisite

## Scope and review request

Operator selected route **1** after the E18 design and milestone/closure review:
continue the existing CI route, implementing only the separately named metadata
catalog producer/gate/controls for exact-source review on draft #112. The reply
was `1`; an exact timestamp was not provided. This is source-work authorization,
not approval for a fourth archive request, provisioning, guest execution, merge,
R1/R2, release or deployment. No new E counter is introduced.

Normative input: [approved E18 design](METADATA-CATALOG-DESIGN.md).
Milestone target: **J0 prerequisite for A2 joined observation and A3 transport /
failure / stop**, primarily closure-ledger rows 3/5/9–14/17. This source package
provides no joined evidence and closes none of those rows. [Current ledger](R1-INTEGRATION.md#current-closure-ledger)
remains authoritative; A1–A7 package acceptance is incomplete.

## Exact new source bytes

| File | SHA256 |
| --- | --- |
| `catalog_join_artifact.py` | `cc170eef2afabce715d1b0cb47f39e6a35b330f22fdbbe09d5835cb4bbb8dfb5` |
| `gate_artifact_catalog.py` | `266ef06341db67c95c069846967733c3bbc0cb4910e9898e5a4966f194332182` |
| `test_artifact_catalog.py` | `04b58034f39d7b264eb5646de790c678eb75d86cab5c0f4217b4ee0fe6541b80` |

New producer/gate are standalone copies evolved from the strict lane. Neither
imports or executes the strict producer/gate. Strict producer/gates, their
existing controls, J0 provider receipt, observed runtime and PowerShell pins
remain unchanged. They retain TYPE_REJECTED for the same char/block fixtures.
The existing live diagnostic job stays literally disabled; both spent selectors
and all three actual-attempt records remain unchanged. No new live job or
activation selector is installed by this source candidate.

## Producer and gate contract

Fixed policy `ROOTFS_METADATA_CATALOG_V1`, distinct CLI
`--download-and-catalog-metadata`, class `j0-rootfs-metadata-catalog-only` schema 1.
Ordered classes: REGULAR / DIRECTORY / SYMLINK / HARDLINK / CHAR_DEVICE /
BLOCK_DEVICE. Existing isreg classification is retained, including contiguous
regular headers; sparse (including an empty extent list or GNU sparse type),
FIFO and unknown returned types remain HOLD. No member-name special cases.

Device admission requires zero size, empty linkname, strict non-boolean integer
major/minor in 0..2^32−1 and mode/uid/gid in 0..2^63−1. A selected-name device is
HOLD. Devices receive no extractfile call, content hash, node creation or selected
identity. Their header metadata contributes only to the policy-prefixed ordered
catalog digest. Names, raw type and major/minor are not public per-device fields.
Selected regular streams alone receive content hashes; selected directory/link
metadata stays disclosed without resolution or guest-binary admission.

Both frames have a six-key closed count map. Successful EOF requires total count
== normalized member count and cross-frame equality. On every failure diagnostic
count-complete is false, with partial total <= parsed_members. The new diagnostic
class/schema are distinct; its 21 predicate reasons comprise the old 19 plus
DEVICE_METADATA_REJECTED and SELECTED_DEVICE_COLLISION. Exceptions retain only a
fixed enum, never member/path/content. Unavailable diagnostics remain HOLD.

Gate keeps exactly two ASCII LF lines (65536 + 2048 bytes, total 67586), scans
warnings/finalizer/traceback before parsing and rejects duplicate keys, nonfinite
numbers, unknown keys/classes/schemas and inconsistent milestones/counts. A valid
HOLD remains exit 2. Success says metadata_catalog_complete=true but explicitly
archive_inspection_verified=false. Extraction/prepared-guest/import/setup/J0/
R1/R2/scope flags stay false; no receipt acts as an approval token.

Fixed provider URL/digest and receipt binding, hash-before-parser, no proxy /
redirect / retry / fallback, github-hosted Linux guard and all existing resource
budgets are retained: 1 GiB archive, 200000 members, 4 GiB logical, 32 MiB per
selected regular, 32 selected entries, 4096 name/link chars, 120 s alarm, 512 MiB
address space and no core dumps. TemporaryFile holds downloaded bytes only;
there is no extraction directory or persisted prepared rootfs.

## Offline controls and declared substitutions

`test_artifact_catalog.py`: **36 tests** = 25 new controls plus 11 applicable
unchanged E11 regressions rebound in a private test-module copy to the new
producer. The two excluded strict-only tests assert special-file rejection and
the original one-line main; equivalent new-lane policy/two-line-main controls are
explicitly included. Original tests are not edited or removed from their suite.

Real synthetic tar covers all six classes, independent policy-prefixed digest
calculation, major/minor hash sensitivity, device size/link/collision rejection,
strict rejection of identical devices, unsupported types, path/duplicate/root /
expansion / selected bounds, no device/link extractfile and no device values in
public frames. Header fault injection covers bool/invalid integer metadata and
empty/nonempty sparse extents that tar serialization cannot preserve faithfully.
Gate controls cover exact framing limits, privacy/authority/count/schema/digest
rejections, unavailable diagnostics and failure exit propagation.

The main-to-gate success/failure test uses real main/TemporaryFile/hash/parser /
encoding, but replaces network with synthetic bytes, replaces resource-limit /
signal calls, and substitutes the synthetic receipt/digest in both producer and
gate. This is not a provider archive receipt or execution/stop-budget proof.
Inherited HTTPError/redirect cleanup is verified with disposable response streams.
No test downloads provider bytes or performs any device/provisioning operation.

Local Python 3.12.14 with ResourceWarning-as-error: **36/36 OK**, no skips or warning
markers. CI adds only this offline suite to Linux 3.12/3.14, with exact count /
no-skips / post-exit warning gates; new exact-head CI is to be inspected separately.
Existing Linux/Windows/identity/carrier controls and strict artifact suites remain.

## Remaining decisions and closure

Actual history remains three consumed requests, **TWO** recorded full digest
matches (E14/E17), E12 UNKNOWN, no completed provider inspection/catalog receipt.
TYPE_REJECTED gives no actual subtype/path. Synthetic evidence changes none of
those facts. Kernel/boot/guest binaries/ports/setup/lifecycle remain unbound.

Next boundary is independent **exact-source** acceptance of this candidate. Only
then may the operator separately approve ONE new finite archive action with a
new unused selector and freshly recorded source/gate hashes. This package neither
requests nor activates that action. Provisioning/source acceptance and the joined
Windows SSH/guest collect/CIM route remain later work. **Draft/unmerged; J0 NOT
READY; R1 NOT AUTHORIZED; R2 HOLD; #80/#96 unchanged.**
