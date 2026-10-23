# SPEC §24 Phase A — two-blob input decision

Date: 23 October 2026.
Status: **PROPOSAL — no selection, manifest expansion or guest execution approval**.
Prior decision: [one-blob packet](S22-PHASE-A-INPUT-DECISION-TH.md).
Plan: [S22-SHAREDHOST-20261023-01](S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md).

## 1. Reason for a new decision

PR #91 remains draft/HOLD at `183edf61ab78c71102948c7d88d7e3a949df037a`, with input `d3144cc48437011830533ba0d4606b8d4644be3a` and its one-blob manifest unchanged.
The operator-supplied independent review confirmed that its dedicated Python 3.14 CI correctly failed on a real unclosed SQLite warning despite 234 tests reporting OK. Python 3.12 passed 234/7/10 plus warning scans.
The warning appeared during a Codex test; this is a finalization observation, not allocation attribution. No exact historical object-to-allocation identity is established.

A separate tracker proved another test-side cleanup defect at original `tests/test_bridge.py:212`, in `test_existing_database_migrates`.
PR #92 repaired it without changing transaction/schema fixture/assertions or runtime. Its independent review approved head `0a2b24e41c5d9be3514680b941b6ee904886bbb4`; exact-head Tests run `39965040649` passed isolated migration and full 234-test suites with completed-output warning scans on Python 3.12/3.14.
The operator then instructed, verbatim:

> merge ได้

This message refers to PR #92 in the preceding conversation. No exact approval timestamp is available; none is invented. It approved that merge only, not a new candidate input or guest execution.
PR #92 merged at `93e056665fc8195697556178ea5ed42910f0773a`.
Its passing CI does not validate the unchanged pinned input of #91 or establish guest readiness.

## 2. Concrete proposed input

| Item | Immutable identity |
| --- | --- |
| Proposed two-blob commit | `02d7e8bb1e1902ca33a574ab904a6e5b0f441785` |
| Sole immediate parent | `d3144cc48437011830533ba0d4606b8d4644be3a` |
| Original ancestor | `71dcae67cbfa6f0b953ab8d81198d073d202ed2a` |
| Proposed tree | `e0a905fb5ec02b91c1a8e8c58351c316e94eadbd` |
| Focused test blob, reviewed in #89 | `c9fae04df337699a679cbf994401c875428cc234` |
| Migration test blob, reviewed in #92 | `c4bbedabea9054ef981bafd5f9f947e7071f85ea` |

Compared with the original input, the 104-file tree changes exactly two blobs:
- `tests/test_context_binding_unresolved.py`: +3/-3, already selected in the one-blob preparation.
- `tests/test_bridge.py`: +2/-1, the additional reviewed repair.

The other 102 blobs and all tracked modes stay unchanged. No runtime, assertion, dependency, stamp, schema, workflow or newer documentation is imported from main.
The branch exists only to make the source reviewable; its name is not an immutable pin. Fetch by full SHA after the required decision/review.
This proposed input has not been installed or executed in the guest. No fresh suite, dedicated CI or readiness result at this proposed input is claimed.

## 3. Operator choices after review

- **ก — recommended:** select this exact two-blob input for preparation of the revised #91 delta: artifact PIN, manifest candidate_commit and the two test entries relative to the original input, dedicated-CI input and coupled plan/README/checkpoints. Relative to #91's current one-blob manifest, only one additional blob entry changes. Preserve prior proposal/approval/evidence as dated history. Keep the matrix, assertions, warning patterns, fail-closed scanner, budgets and B gates unchanged.
- **ข — defer:** leave #91 and all existing guest evidence HOLD without an input change or warning waiver.

Neither proposal creation, external review nor packet merge selects an option. No operator selection or timestamp is invented.
Choice ก authorizes revised source/manifest preparation only; it does not authorize merging #91, guest input replacement or execution, readiness acceptance or B.

## 4. Required sequence

1. Review this exact input and decision packet; require packet exact-head CI and a separate operator merge order. Packet-head CI is not dedicated validation of the proposed candidate.
2. Obtain the explicit input selection. If ก, prepare the coupled #91 delta against current main, retain its failed CI history, and run dedicated full-suite/focused/artifact checks on the new input for both Python 3.12/3.14 with completed-output warning scans.
3. Require independent review of the new #91 head and successful exact-head CI; merge only on operator order. Missing observations, warnings or failures keep HOLD. No retry/suppression or scanner narrowing is authorized to obtain success.
4. Before guest use, obtain explicit scope bound to the exact reviewed candidate/artifact. Preserve the old checkout/logs, use new private paths, revalidate resource/time/continuity gates and collect fresh full/focused/artifact results plus dependency identity. Inspect output through process exit; test exit zero alone is insufficient.
5. Build the private 0600 readiness receipt only from measured evidence. Missing resource observations cannot be replaced by test success.

No current #91 source, manifest, candidate or guest checkout changes in this packet. Phase A remains incomplete; B, PR #80 and historical disposition remain HOLD.
No connector, credential, production/Dev change, release or deployment is authorized.

<a id="s24-two-blob-selection"></a>

## Operator selection checkpoint — 23 October 2026

The operator explicitly approved PR #93 merge and option ก in one complete message, verbatim:

> Merge ได้ และเลือก ก

No exact approval timestamp is available; none is invented. The merge completed at `55f42de1c7c83f637b3979058386b5239911083a`. Option ก selects preparation of this revised #91 source/manifest delta only; it does not authorize merging #91, revised guest execution, readiness acceptance, B, release or deployment.
This later checkpoint was not part of reviewed packet head `b973806`; the earlier proposal remains unchanged.
The revised [plan checkpoint](S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md#s24-two-blob-preparation) and [artifact](../acceptance/s24/README.md) prepare the exact selected input `02d7e8bb1e1902ca33a574ab904a6e5b0f441785`. Dedicated CI at the revised #91 head and independent review remain required. No guest checkout or evidence has been changed; Phase A incomplete, B and PR #80 HOLD.
