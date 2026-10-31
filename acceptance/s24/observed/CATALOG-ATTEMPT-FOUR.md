# Catalog attempt four — actual HOLD record

Status: **HOLD / no completed catalog receipt / no fifth invocation authorized**.
This is an actual result record on continuing draft #112, not a new E increment.

## Approval, activation and run

- Operator approval: **“อนุมัติ”**, verbatim; exact approval timestamp **NOT_PROVIDED**.
- Finite scope: ONE CI catalog producer invocation, no retry; record real result and restore guard. No provisioning, guest/inventory action, merge, R1/R2, release or deployment.
- Independently reviewed proposal: `9d17992831c256deb0eeba872be5948618f1a2ab`.
- Activation: `2ee4167d47f8c80172ad651fa78bfbed9625bd38`, subject `ci: run approved metadata catalog attempt four once`.
- Actual activation delta: only one false-guard line removed, no source/pin/predicate changes.
- [Run 41213711915](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41213711915), attempt 1, [job 124573771376](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41213711915/job/124573771376).
- Job started 2026-10-31T15:12:06Z, completed 15:12:20Z. Producer/gate step 15:12:10Z–15:12:17Z. These are CI timestamps, not an inferred approval timestamp.
- Job **FAILURE**; gate exit **2**. Gate validates that the captured producer exit is 2. No rerun/retry was requested.

## Gate-emitted facts only

The machine-readable [record](CATALOG-ATTEMPT-FOUR.json) contains the single allowlisted gate frame.

| Fact | Actual value |
| --- | --- |
| Evidence | j0-metadata-catalog-gate-hold / ROOTFS_METADATA_CATALOG_V1 |
| Download / hash / digest equality | true / true / true |
| Received / hashed | 388,975,696 / 388,975,696 bytes |
| Archive SHA256 | `bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e` |
| Stage / error / predicate | ARCHIVE_PARSE / PREDICATE_REJECTED / **BACKSLASH** |
| parsed_members | 11701 |
| Partial type_counts | REGULAR=9643, DIRECTORY=1166, SYMLINK=881, HARDLINK=3, CHAR_DEVICE=8, BLOCK_DEVICE=0 |
| type_counts_complete / metadata_catalog_complete | false / false |
| archive_inspection_verified / prepared/import/setup/J0/R1/R2/scope | all false |

Counts sum to 11701 but are **partial**; equality does not mean successful EOF or
a completed catalog. The BACKSLASH enum identifies only the failed predicate.
It does not disclose a member/path/content, identify a numbered raw header, or
prove an archive-security/import/portability diagnosis. No raw producer output
was printed/uploaded; no catalog hash or selected-entry receipt was emitted.
Do not backfill this reason or device counts into E12/E14/E17.

## Accounting, restoration and next boundary

Four authorized live invocations are consumed. **THREE** full digest matches are
now recorded: E14, E17 and this fourth invocation. E12 remains UNKNOWN. Earlier
records retain their original facts; prior two-match/three-invocation snapshots
are history at their own heads. No completed provider inspection/catalog receipt.

This record commit restores the new catalog job's literal job-level false guard
to the exact reviewed proposal workflow bytes; the old diagnostic guard remains
false. Its subject is not an activation subject. Inspect its exact-head CI:
catalog and diagnostic jobs must be **SKIPPED**, E12 must say **NOT ATTEMPTED**.
Regression success there cannot erase this actual failed attempt.

No fifth invocation, predicate relaxation, fallback route or archive correction
is authorized. Independent review/disposition of this HOLD precedes any new
design/source/action proposal. J0 remains the environment prerequisite for
A2/A3; kernel/boot/guest/ports/setup/lifecycle remain unbound and the joined
Windows/SSH/collect/CIM route is unproved. All eighteen row dispositions remain
OPEN; A6/A7 private bindings/source acceptance and #80/#96 unchanged.
**Draft/unmerged; J0 NOT READY; R1 NOT AUTHORIZED; R2 HOLD.**
