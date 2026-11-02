# J0 literal catalog attempt five — actual completed CATALOG ONLY record

Date: 2 November 2026. Same draft #112.
Status: **V2 METADATA CATALOG COMPLETE — PENDING INDEPENDENT RESULT REVIEW**.
This record supplies no strict inspection, prepared image, import or J0/R1/R2 authority.
[Exact action record](LITERAL-CATALOG-ATTEMPT-FIVE.json) /
[exact gate-emitted JSON plus LF](LITERAL-CATALOG-ATTEMPT-FIVE-GATE.json).

## 1. Separate approval and one actual action

Operator quote, verbatim: “อนุมัติ invocation ที่ 5 แยกตาม proposal”.
Exact approval timestamp: NOT_PROVIDED. Scope is ONE fifth CI invocation under
the [reviewed disabled proposal](LITERAL-CATALOG-ATTEMPT-FIVE-PROPOSAL.md),
accepted at `71afeb04da7433158b7f84ee3de56b69ad4eaac4`.
Source review accepted `e1e438f0d0992dc1d30f01a6a8c95735041a293b`.
Neither approval grants provisioning, another invocation or #112 merge.

Activation `c5a8b6c27a121b45e7a34ed56a026eec2be236eb`, exact subject
`ci: run approved literal metadata catalog attempt five once`,
removed only the new literal job's one false-guard line.
[Run 41456279214](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41456279214),
attempt 1, job `125313650375`: **SUCCESS / checked gate exit 0**.
Job times from GitHub: 2026-11-02T13:49:17Z–13:49:34Z.
Producer exit 0 follows from the pinned gate's accepted success branch, which
rejects any other producer exit for this receipt. It is not inferred from duration.
No workflow/job rerun, retry, alternate source, resource widening or fallback.

## 2. Gate facts and normalized catalog counts

| Checked fact | Actual result |
|---|---|
| Policy | ROOTFS_METADATA_CATALOG_V2_LITERAL_NAMES |
| Download/hash/digest equality | true/true/true; received=hashed=388,975,696 B |
| Archive SHA256 | `bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e` |
| Stage/error/reason | COMPLETE / NONE / null |
| Normalized member entries | 49,190; complete six-class counts sum exactly to that value |
| Declared logical bytes | 1,190,874,239 |
| Ordered policy-prefixed catalog SHA256 | `89ad212e398c51452cfab1bef956a88ba6a4833376893f17caca23884988587c` |
| Selected entries | 7: five REGULAR content hashes and two unresolved symlink records |
| metadata_catalog_complete / type_counts_complete | true / true in their applicable gate/diagnostic fields |
| strict archive_inspection_verified / prepared_guest_artifact / import / setup / J0 / R1 / R2 / scope | all false |

| Class | Count |
|---|---:|
| REGULAR | 35,796 |
| DIRECTORY | 4,219 |
| SYMLINK | 9,164 |
| HARDLINK | 3 |
| CHAR_DEVICE | 8 |
| BLOCK_DEVICE | 0 |

These are source-defined normalized TarInfo catalog entries, not a count or
identity of raw extension headers. The ordered catalog commits header metadata
and selected regular-file hashes; it is not a full-content tree or extraction.
No device node was opened/created, no link resolved and no member materialized.
No non-selected member/name/device values are disclosed by this record.

The selected receipt includes `usr/bin/python3.12` with content SHA256
`a92f0f95e883390c7256b2e441484aac06b1002dbe1d924141a77c8d82f96223`;
the `usr/bin/python3` entry is an unresolved symlink. These are metadata/hash
facts, not executed interpreter/version/compatibility proof.
No `usr/sbin/sshd` entry is returned in the selected receipt. This does not
identify other possible binary paths or authorize installation/package setup.
Remaining guest binary/capability bindings still need separate source review.
No file contents, dpkg package list, provider signature or actual rejected V1
member were collected in public output.

## 3. Exact evidence and source integrity

[Gate JSON](LITERAL-CATALOG-ATTEMPT-FIVE-GATE.json) SHA256 including its trailing LF:
`6e42b0c795157c813ec2407833bbaffce4814d285abc1e6d9802920b51ef15fc`.
It reconstructs exactly the single checked JSON line emitted by the gate,
excluding CI timestamps. A receipt-only local audit confirmed canonical bytes,
all count/flag/schema/cross-frame rules through the pinned gate and equality
with the accepted object; no producer rerun or archive read occurred.

Pre-network pins remained:
producer `16d1953d2094281d39c328dd54bada15de6be3e1b3f84cbddf8b69acbf39fc90`,
gate `f7cf5136f8aaedecbe640fe960e0ae4f7c9fe5b7daf9f5992e410830ad53d4ba`,
provider receipt `41e2e56ff490475d899894e61c93b0e518439551f193031a8bef38b447805fbc`.
No source, policy, old test, runtime pin or historical actual record changes.
Raw producer output/archive was never printed/uploaded; the temporary archive
was not retained as a prepared/importable artifact. Only allowed gate facts
are committed. Old HOLD records are unchanged, not converted into successes.

## 4. Consumed budget, restored guard and remaining gates

Current total: **FIVE consumed invocations / FOUR recorded full digest matches**
(E14/E17/fourth/fifth); E12 remains UNKNOWN. No sixth action authorized.
The record commit restores the literal job's job-level false guard, returning
the complete workflow to proposal SHA256
`b0dab8abcf04144e088c342e5938552f7dcf764b625d770077ed36210b1b02e6`.
Its non-activation subject and the restored guard prevent automatic follow-on;
new-head CI must confirm literal/V1 catalog/diagnostic jobs SKIPPED and E12
NOT ATTEMPTED. Regression success is not independent acceptance of this result.

| Milestone | Current disposition |
|---|---|
| V2 catalog/selected-hash evidence | PRESENT, complete under its fixed catalog policy; independent result review pending |
| Strict inspection/signature/extraction/import compatibility | NOT ESTABLISHED / flags false; no authority inferred |
| Kernel/boot/virtualization/guest Python+sshd/setup/ports/lifecycle | Still unbound/unproved; no setup source or provisioning action supplied here |
| Same-invocation native Windows SSH/collect/CIM join and outer stop/deadline/writer coverage | Still OPEN |
| A6/A7 and complete R1 source/private acceptance | Still pending; no private values disclosed |

Next boundary is independent review of the actual catalog evidence, then one
reviewable remaining J0 setup/binary/environment work package if selected.
No source for setup or another action starts automatically from this record.
A/C remain possible future route decisions; this success does not retrospectively
waive them or approve the next stage. If a future separately approved action
HOLDs, return to route-or-defer with no automatic policy/retry increment.

All eighteen [ledger](R1-INTEGRATION.md#current-closure-ledger) rows stay OPEN.
Same draft/unmerged; J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD.
#80/#96/private A6/A7 unchanged; no release, deployment or operational gate closure.
