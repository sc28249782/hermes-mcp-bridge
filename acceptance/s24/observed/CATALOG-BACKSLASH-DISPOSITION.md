# J0 BACKSLASH HOLD — disposition and route decision for review

Status: **DESIGN / DECISION PROPOSAL ONLY; NOT IMPLEMENTED OR SELECTED**.
Reviewed input: actual record head `992712085e9e6d3a1570f547b7d5d48d4ce1ecff`.
Same draft #112; no new E counter. Operator's “ทำขั้นถัดไป” advances this
reviewable disposition/decision packet, not a fifth invocation or parser change.
Independent acceptance of the actual record and of this proposal is still needed.

## 1. What the actual HOLD establishes

[Attempt four](CATALOG-ATTEMPT-FOUR.md) / [exact JSON](CATALOG-ATTEMPT-FOUR.json):
run 41213711915, attempt 1, job 124573771376, FAILURE / gate exit 2. The producer
and checked gate preserve ARCHIVE_PARSE / PREDICATE_REJECTED / BACKSLASH,
388,975,696 received/hashed bytes and digest equality with the fixed provider pin.
Partial counts/parsed_members=11701 are not a completed catalog or EOF proof.

The source-level cause of this verdict is the failed predicate
`'\\' not in name` in V1's member_name(), after its leading `./` handling and
absolute-slash rejection. This is a correct rejection under the reviewed V1
policy, not proof of a parser defect. No specific name/path/content, numbered raw
header, intent, corruption, import suitability or security diagnosis is known.
No real member is reconstructed here. Synthetic examples below are not provider
observations. Do not reinterpret earlier E12/E14/E17 outcomes.

Accounting stays **FOUR consumed invocations / THREE recorded digest matches**
(E14/E17/fourth); E12 UNKNOWN. Catalog and diagnostic jobs are disabled. Neither a
new policy proposal nor design approval changes the failed result into a pass.

## 2. Choices against the A2/A3 target

J0 is the environment prerequisite for the disposable joined observer route;
its catalog is not itself an A2/A3 completion criterion or an R1 scope token.

| Option | Work and review needed | Limit / decision |
| --- | --- | --- |
| A — retain V1 and choose another artifact | New exact provider/source/digest binding, inspection policy and provisioning route review; no automatic URL/image substitution | Current archive remains V1 HOLD. Cost/boot/guest compatibility unproved; no alternate artifact is nominated here |
| B — explicit literal-name catalog V2 | Review the narrowly defined metadata-only name policy below; if selected later, separate producer/gate/offline controls and exact-source review | Recommended design option for the current fixed artifact. No promise it passes later predicates or completes J0 |
| C — defer the selected CI route | Operator explicitly records deferred A2/A3 route and remaining obligations; identifies another independently reviewed route only if needed | Does not waive joined evidence, close any row, authorize operator VM use or make this package release-ready |

Recommendation is **B for design review**, because the proposed change concerns
only non-materialized metadata names and keeps the existing artifact, selectors,
selected-file authority and resource bounds fixed. This is an engineering
recommendation, not a claim about actual provider member names or a selected
operator decision. A/C remain available; no runtime work begins in this packet.

## 3. Proposed fixed V2 contract — catalog-only literal names

If B is independently accepted and explicitly selected, use fixed policy
`ROOTFS_METADATA_CATALOG_V2_LITERAL_NAMES` in a separately named producer and
gate. Exact source paths, hashes and argv are **UNBOUND** until source review.
No config switch, silent V1 edit, auto-fallback, named-member exception, header-
index exception or archive-specific path special case. V1 and strict sources, tests, pinned workflow and actual records remain untouched.
V1 retains its 21 reasons; the strict diagnostic retains its own 19 reasons.

The only proposed admission delta is removal of the universal BACKSLASH name
rejection **in this new lane only**. A backslash is one literal character in the
catalog string; it is never a separator, escape sequence or instruction for a
host filesystem operation. This is a deliberately defined catalog alphabet,
not an extraction/path-safety, Windows compatibility or import policy.

Preserve the existing order and predicates otherwise:

1. Require a string of 1..4096 characters. Strip only existing leading `./`
   repetitions; retain existing root marker handling.
2. Reject a leading `/`. Remove existing trailing `/` characters. Split components
   only on `/`; reject empty, `.` or `..` components as before.
3. Reject ASCII control characters and DEL as before. No new Unicode, case,
   drive-prefix, backslash, escape, URL or filesystem normalization. Do not replace
   backslashes with slashes, interpret `\n`/`\xNN`, collapse components or resolve
   links. TarInfo strings are catalog input, not proof of original raw name bytes.
4. Duplicate detection uses the resulting exact string. Existing leading-`./` /
   trailing-`/` aliases still collide; slash and literal-backslash names remain
   different strings, never aliases on any host filesystem.
5. Root-not-directory, six-class/device eligibility, sparse/FIFO/unknown rejection,
   selected-name device collision, member/size/link/content caps and count-update
   rules remain the reviewed V1 contract.

Illustrative **synthetic** catalog decisions (quoted strings here are notation):

| Input name | Proposed result / unchanged boundary |
| --- | --- |
| `a\b` versus `a/b` | Two different catalog names; neither rewritten nor used as a filesystem path |
| `..\x` or `C:\x` | Literal metadata strings, not interpreted as parent traversal or a drive path; grants no path use |
| `../x`, `/x`, `a//b` | HOLD under unchanged slash-component/absolute-name rules |
| `./a\b` plus `a\b` | Duplicate after existing leading-`./` handling: HOLD |
| Backslash followed by letter `n` | Preserve two characters; an actual newline remains NAME_CONTROL/HOLD |
| Selected-looking name with an inserted backslash | Does not match the unchanged fixed selected() predicate; no selected content hash |

These examples expose the deliberate representation-policy difference. They are
not instructions to join/open/extract such names on Linux or Windows. No member
path is ever passed to Path/open/mkdir, subprocess, a device operation or an
extract-to-disk API. extractfile remains restricted to admitted REGULAR TarInfo
objects matching the unchanged fixed selector; it is not given a decoded name.
Selected symlink/hardlink metadata remains unresolved and not executable proof.

## 4. Hash, gate and evidence separation

V2 catalog digest uses its own fixed policy-ID prefix plus canonical ordered
header records, retaining literal strings through ensure_ascii JSON encoding.
This prevents V1/V2 digest identity from being interpreted as policy equivalence.
No raw non-selected name, device field, exception text or pathname is emitted;
non-selected names are committed only into the aggregate catalog digest.
Device metadata remains hash-only. Existing selected allowlist/shape remains
unchanged and admits no backslash-bearing selected name or device target.

Use distinct proposed evidence classes (schema 1):
`j0-rootfs-literal-metadata-catalog-only`,
`j0-literal-metadata-catalog-diagnostic-only`,
`j0-literal-metadata-catalog-gate-only` and
`j0-literal-metadata-catalog-gate-hold`.
Their separately checked gate accepts only the new policy/class combination;
old V1/strict classes and old/new-policy cross-combinations reject. Keep the
same exact key sets/count map/flag meanings and bounded two-frame protocol;
BACKSLASH may remain in the closed 21-reason vocabulary for schema stability,
but literal-backslash admission itself cannot emit that rejection. No input
value is added to diagnostics. Count-complete stays false on every failure;
successful EOF requires exact total/cross-frame consistency.

Keep archive_inspection_verified, extraction_authorized, prepared_guest_artifact,
import_compatibility_tested, provider_signature_verified, links_resolved,
setup_ready, j0_ready, guest/R1/R2/scope flags false in their existing applicable
frames. metadata_catalog_complete=true may mean only this V2 catalog completed;
it does not authenticate the artifact, import it or authorize any next action.
Malformed/missing/oversize/extra/duplicate/nonfinite output, warnings, broken
output and failure exit remain HOLD. Never cat or upload raw producer output.

## 5. Required offline evidence before any new source acceptance

- V1/strict exact hashes and unchanged regressions; identical synthetic backslash
  names still reject BACKSLASH in their original lanes.
- Real synthetic tar in V2 exercises literal/backslash/slash distinction,
  normalization duplicates, multiple backslashes, apparent drive/UNC strings and
  backslash-letter sequences without any rewrite, path lookup or content read
  for non-selected entries. Assert no non-selected names in public output.
- Existing slash traversal/absolute/empty-component/root/control/duplicate and
  all caps remain HOLD; no member-index or named-path bypass.
- Independent expected canonical digest proves policy domain separation and
  literal-name sensitivity. Fixed selector remains exact; backslash-bearing
  near-matches/device collisions cannot gain selected identity or file reads.
- All six type/device/sparse/unsupported checks and all V1 gate consistency,
  false-flag, privacy, failure framing, HTTP cleanup and resource-guard controls
  remain exercised. V1 and V2 gates reject one another's classes/policies.
- Supported Python 3.12/3.14 offline suites pass count/no-skips/post-exit warning
  gates; disclose all synthetic/header/network substitutions. No real archive
  request, import, provisioning, operational timing or stop proof is inferred.

Retain fixed URL/provider digest/receipt, no proxies/redirect/retry/fallback,
hash-before-parser, ordinary GitHub-hosted Linux actor, TemporaryFile-only bytes,
120 s / 512 MiB / no core, 1 GiB archive / 200000 members / 4 GiB logical /
32 MiB selected regular / 32 selected / 4096 name/link bounds. No new service,
actor, download route, package, guest, privilege or operator machine access.

## 6. Finite exit and next decisions

This packet ends at a reviewable HOLD disposition and choices A/B/C. It changes
no source, pin, workflow, criterion or action budget and requests no fifth run.
If B is selected after design acceptance: implement separate exact sources and
controls -> independent source acceptance -> separately reviewed disabled wrapper
and finite-action proposal -> separate operator approval for any live invocation.
No activation selector or source hash is invented here.

Do not automatically create another parser-policy increment on the next HOLD.
A future finite action, if ever approved, ends either with a completed catalog
receipt or a preserved HOLD and return to the route-or-defer decision. Successful
catalog still leaves kernel/boot/guest binaries/ports/setup/lifecycle and joined
A2/A3 evidence to bind/prove; it does not close all of J0 or the integration rows.
[Current delivery map](../../../docs/S24-DELIVERY-CLOSURE-TH.md) and
[eighteen-row ledger](R1-INTEGRATION.md#current-closure-ledger) remain binding.

**All eighteen rows OPEN; same draft/unmerged; J0 NOT READY; R1 NOT AUTHORIZED;
R2 HOLD; A6/A7 and #80/#96 unchanged. No source implementation, fifth attempt,
provisioning, merge, release or deployment is authorized by this packet.**
