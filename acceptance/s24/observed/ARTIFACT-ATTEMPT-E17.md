# E17 — third finite CI attempt: actual TYPE_REJECTED, still HOLD

Date: 31 October 2026. Reviewed source parent: `5a864543` (E16).
Status: **ACTUAL FAILED INSPECTION; ACTION CONSUMED AND DISABLED AGAIN**.
Continue draft #112; no merge, provisioning or operational scope.

## 1. Approval and exact activation

Operator answered **“อนุมัติ”** to the explicit proposal: one third CI-only attempt,
reviewed source/hash and original 120 s/512 MiB limits, no retry/fallback,
provisioning or merge; preserve the result and disable the job again. Approval
date in conversation: 31 October 2026 Bangkok; no exact timestamp was provided.

Activation `0a2b07ae4363757750571632e6c7b55272ca044a` changed ONLY the false-guard
removal and the unused selector subject:
`ci: run approved predicate-reason artifact attempt once (E17)`.
The selector still required GITHUB_RUN_ATTEMPT=1. E12/E14 subjects were not reused.
Producer `f9d1c3ed…`, gate `ad9c2e0e…`, receipt `41e2e56f…`, argv, limits and parser
predicates remained the reviewed E16 bytes; source pin checks preceded network.

## 2. Actual run evidence

[Observed run 41200750250](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41200750250),
job `124535893803`, run attempt 1, configured Python 3.12. The live step ran
19:21:45–19:21:52 Bangkok time (12:21:45–12:21:52 UTC) on 31 October 2026.
The checked gate emitted a schema-2 j0-artifact-gate-hold frame and exited **2**;
job/workflow FAILURE, without recovery. The actual allowlisted frame and approval/
source/run facts are preserved in [ARTIFACT-ATTEMPT-E17.json](ARTIFACT-ATTEMPT-E17.json).

| Milestone / result | Actual value |
| --- | --- |
| received_bytes / hashed_bytes | 388,975,696 / 388,975,696 |
| download_complete / hash_complete / digest_matches | true / true / true |
| computed full archive SHA256 | `bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e` |
| stage / error / predicate_reason | ARCHIVE_PARSE / PREDICATE_REJECTED / TYPE_REJECTED |
| parsed_members | 5; normalized names admitted before remaining entry checks, not a raw tar-header index |
| archive_inspection_verified / archive_verified_receipt | false / false |
| complete catalog / selected hashes | NOT AVAILABLE |
| setup / J0 / guest / R1 / R2 / scope | all false |

This identifies the actual predicate rejected in THIS invocation:

```python
item.isreg() or item.isdir() or item.issym() or item.islnk()
```

The condition was false under the reviewed parser. No subtype byte/enum, member
name/path/content was emitted. Do NOT infer character/block device, FIFO, unknown
extension, exact entry identity, archive corruption/maliciousness or a safe policy
change from this label. Digest equality proves the same provider-pinned bytes;
it does not prove the parser policy is appropriate for all rootfs entry types,
complete inspection, import/extraction safety or prepared-image readiness.
The E14 record retains UNKNOWN specific predicate; the new observation is not
backfilled into older diagnostics. E12 remains separately UNKNOWN as before.

## 3. Stop boundary and next decision

The third authorized invocation is consumed. Result commit restores literal
job-level false and uses a non-activation subject. No fourth request, rerun/local
download, alternate archive, expanded limits or parser relaxation is performed.
The producer closes/removes only its own temporary archive; no rootfs is retained,
extracted, installed, imported or booted. Gate never cats raw process output;
only its checked allowlisted failure frame is emitted.

Next review topic is the inspection/admission policy for entry types, using the
new actual predicate evidence. Any proposed subtype diagnostic or metadata-only
inspection lane needs an explicit bounded contract and independent source review;
neither is implemented here. It must distinguish inspection metadata from later
extraction/import authority and must not convert a failed run into a pass. Any
further live request requires a new finite operator approval and unused selector.
Guest package/setup source remains incomplete until full inspection/selected
binary evidence and remaining kernel/boot/ports/lifecycle/private bindings exist.

Later green offline/regression workflows and skipped live jobs do not supersede
this failed actual inspection. J0 NOT READY; R1 NOT AUTHORIZED; R2 HOLD; all eighteen
row dispositions/private bindings/#80/#96/release/deployment remain unchanged.
