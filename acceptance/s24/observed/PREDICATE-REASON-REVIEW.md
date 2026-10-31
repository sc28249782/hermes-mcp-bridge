# E16 — parser predicate reasons, source review only

Date: 31 October 2026. Input: E15 independent approval of actual E14 result at
`41f0eadb`. Status: **NEW SOURCE/SCHEMA CANDIDATE; NO THIRD LIVE ATTEMPT**.
Continue #112 draft. The E12 failure remains UNKNOWN; the actual E14 digest
milestone and parser HOLD in [its record](ARTIFACT-ATTEMPT-E14.json) remain intact.

## 1. Source and protocol delta

This changes the CURRENT artifact diagnostic producer/gate and dependent pins.
It is not an unchanged-E13-source claim: earlier reviewed bytes/results are
historical snapshots in Git. E11 baseline source/13 controls, public historical
attempt records and all operational observer/PowerShell runtime/pins stay intact.
New source requires independent review. No source-acceptance or action approval
is implied by this candidate.

Normal diagnostic schema changes **1 → 2**, adding exactly one key:
`predicate_reason`, either null or one of the nineteen literal enums below.
`PredicateHold` is a Hold subtype with EMPTY exception args and only the checked
enum stored; no input value/member/index/name/path/content is copied into it.
The frame emits the reason ONLY for this subtype, PREDICATE_REJECTED and stage
ARCHIVE_PARSE. It does not retain a last-passed reason in mutable progress state;
ordinary Hold, parser/IO errors and errors outside parse keep reason null.
The separate fixed diagnostic-unavailable fallback is unchanged (its own schema
1/class); it still cannot pass the normal gate.

Each archive predicate retains its original condition/bound and evaluation order.
Combined predicates are split in their original left-to-right short-circuit order
only to distinguish the reason. True predicates return as before; false ones
still immediately stop in Hold. No new tolerated name, type, sparse entry, size,
link, archive format or byte/member limit. Hash-before-parser, no extraction/link
resolution, response cleanup, 120 s/512 MiB budgets, no retry/fallback and existing
byte/hash milestones remain unchanged. Success inspection JSON is unchanged.

## 2. Closed reason vocabulary

| Reason(s) | Original failed predicate, no associated input data |
| --- | --- |
| NAME_LENGTH_OR_TYPE | name is a string, length 1–4096 before normalization |
| ABSOLUTE_PATH / BACKSLASH | normalized name is not absolute / contains no backslash |
| PATH_COMPONENT / NAME_CONTROL | no empty/dot/dot-dot component / no control character |
| NAME_DUPLICATE / COUNT_MEMBERS | normalized unique-name admission / member count below cap |
| HEADER_SIZE_RANGE / SIZE_LOGICAL | single header size in bounds / cumulative declared size in bounds |
| LINK_LENGTH / SPARSE | link metadata length <=4096 / no sparse mapping |
| TYPE_REJECTED / ROOT_NOT_DIRECTORY | regular/directory/symbolic/hard link only / root entry must be directory |
| COUNT_SELECTED / SIZE_SELECTED | selected entries <32 / selected regular size <=32 MiB |
| SELECTED_STREAM_MISSING | selected regular entry yields a content stream |
| SIZE_SELECTED_READ / SELECTED_READ_SIZE | bounded selected stream read / read size equals declared size |
| EMPTY_ARCHIVE | at least one admitted member |

Only an actual failed predicate constructs its reason. A label proves which
source condition rejected that NEW invocation; it does not establish a dangerous
archive, provider intent, member identity, parser bug or a safe relaxation.
parsed_members still means names admitted to the set before later checks. No
member index/rejected value/type byte/path/hash of a member is added to the
failure frame. Do not retroactively assign a reason to E14 from a fixture label.

## 3. Gate, tests and live boundary

The schema-2 gate requires the exact augmented key set. Non-null reason must be
an exact string enum AND ARCHIVE_PARSE/PREDICATE_REJECTED; unknown/list/private
values, old normal schema 1 and a reason on other stage/error are rejected.
Success COMPLETE/NONE therefore requires null reason. All original framing,
warning/duplicate-key checks, false flags, byte/hash bounds and cross-frame
success binding remain; valid HOLD still exits 2. Diagnostic lines remain <=2,048
bytes, no raw stderr or caught exception text is printed. Old live records remain
historical evidence, not input to this new gate.

Existing diagnostic 25 and gate 10 controls retain their assertions and counts;
only explicit schema/key-set/duplicate-key fixtures are updated for schema 2.
The original 69 and E11 13 are untouched. A NEW eleven-test suite exercises ALL
nineteen reason values and null/rejection/privacy semantics. Names/duplicate/root,
member/logical/link/type/selected/empty cases use actual synthetic tar streams.
Header-range/sparse/missing/short/oversized selected-stream cases explicitly inject
TarInfo/reader faults AFTER a real hash pass; these are not claimed as naturally
observed provider archive behavior. Gate accepts the resulting failure frames as
telemetry but keeps exit 2. Tests also enforce empty exception args, sentinel
absence, no stale reason on non-predicate failure, schema/enum/stage consistency
and unchanged success receipt versus E11. Limits are reduced only in test fixtures.
No test downloads provider bytes or invokes the live CLI/resource limits/alarms.

The E14 job stays hard-disabled at job level. Its dependent producer/gate pins
are recomputed from NEW bytes only to keep the proposal coherent; that neither
reactivates its spent selector nor grants a third attempt. No new activation
subject/job/argv/network request is introduced. A future separately reviewed and
approved finite action must bind these exact new sources and its own unused
selector. The actual 388,975,696-byte / bb415d82 digest milestone remains valid,
but full inspection/catalog/selected hashes and guest setup stay incomplete.
J0 NOT READY; R1 NOT AUTHORIZED; R2 HOLD; #80/#96 and all remaining integration/
private/kernel/lifecycle/stop bindings remain unchanged. No merge/provisioning.

## 4. Author-computed source SHA256

| Source | SHA256 |
| --- | --- |
| prepare_join_artifact_diagnostic.py | `f9d1c3ed88eaf6da3988e6b93dc43b90c37566d03ce59f890e6b500fd4435988` |
| gate_artifact_diagnostic.py | `ad9c2e0e1c8c550c14b4449eb46dffd88d89f63bccfa0573e6e4c40178f4d915` |
| test_artifact_diagnostic.py | `a1c7be6d42fad60100042977d5775f31010c102013769d7df602a660498c2a58` |
| test_artifact_gate.py | `9bf756768b7afbadfe41b5763be8cb951944248b40170eafe3302c6326ef65dc` |
| test_artifact_predicate_reason.py | `314b08dd7924ae8c8ce251655711e80367d71ecdb984ac6c1fd8584b778a2ee1` |
