# SPEC 24 Phase A fixture artifact

Status: **revised input preparation for review; guest execution scope pending; Phase A incomplete; no Phase B approval**.
Prepared candidate: `d3144cc48437011830533ba0d4606b8d4644be3a`.
Original candidate: `71dcae67cbfa6f0b953ab8d81198d073d202ed2a` (preserve its checkout and evidence).
Plan: [S22-SHAREDHOST-20261023-01](../../docs/S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md).

## Authorization and scope

The operator approved A only with this chat message, verbatim:

> ยืนยัน **“อนุมัติ A only ตามแผน #87”**

The message has no exact approval timestamp; none is invented. A does not authorize a connector, route credential, live fixture, or acceptance stimulus over a tunnel.
This artifact was authored and checked in a separate development environment. No guest suite result or readiness PASS is claimed here. Guest workspace preparation is operator-reported; private machine/account/endpoint/package inventories are not reproduced.
Relative to the original candidate, only the two synthetic SQLite connections in one focused test now close explicitly, using the reviewed PR #89 fix. Runtime, assertions, other tests, stamp, dependencies, configuration and tool input signatures are unchanged. No operator configuration loader is called.

## Source and instrumentation

- `candidate_manifest.json` lists the exact 104 Git blob identities from the candidate tree. Verification rejects changed/missing files, symlink boundaries, unexpected root entries and a candidate operator config. This is content integrity, not authentication of a person.
- `s24_fixture.py` constructs the actual candidate `server()`, `Bridge`, and `ContextRegistry`. Hermes uses `httpx.MockTransport`; no socket request is made even when its log prints an HTTP URL. Codex/Hands are stubs with no subprocess/native task path. Other backend operations are rejected.
- Labels select deterministic, one-shot bind hooks. COMMIT failures occur in a real open write transaction and roll back when the connection closes. POST failures occur after a real successful commit. CLOSED actually closes the row after ACK and before binding.
- Extra fields inside fixture `bridge_status` backend dictionaries expose synthetic counters and hashes of deep-copied ACKs. They are **test-only instrumentation**, not new production metadata, tools, or schema. Discovery remains 27.
- Full nested ACK preservation is checked against the pre-wrapper digest. Existing rows are compared between cases. After the SDK child stops, snapshots must match the complete expected context rows, request-to-run mapping and ordered audit projection, not just totals.
- Input hashes are checked before/after the offline smoke. These discrete checks do not prove continuous absence of host interference.

## Fixed matrix and arithmetic

Run backends in order Hermes then Codex. Each uses NORMAL, OP_PRE, OP_COMMIT, OP_POST, CTX_PRE, CTX_COMMIT, CTX_POST, CLOSED, EXCLUDED.
Then replay the same Hermes OP_PRE request once, test each backend's closed precheck, and submit one no-context request per backend.
EXCLUDED is ProgrammingError only. Broader excluded/fatal/submit-raise/malformed-ACK coverage remains candidate unit evidence.

| Final value | Expected / derivation |
| --- | --- |
| Context rows | 18 = 9 per backend |
| Closed / open | 2 / 16; only CLOSED per backend closes |
| Bound | 7 = NORMAL + OP_POST + CTX_POST per backend (6) + Hermes OP_PRE heal (1) |
| Unbound | 11, including both closed rows |
| Hermes POSTs / durable registrations | 10 = 9 matrix + 1 plain; known-ID replay/precheck add none |
| Codex submits | 10 = 9 matrix + 1 plain; memory-only stub observation |
| Audit | 30 = 18 create + 2 close + 10 Hermes submit; no Codex audit record |

Numbers describe this driver's successful completion only, not any unexecuted guest/tunnel run. Timestamps are observations, not proof of order.

## Phase A usage after artifact review

After independent review/merge and explicit guest scope binding this revised input/artifact, use the new guest candidate's own virtual-environment interpreter. Do not edit the original checkout or apply a test overlay.
Use the guest candidate's own virtual-environment interpreter. `ARTIFACT` names this reviewed artifact checkout, separate from `CANDIDATE`. Neither may be a floating branch input.
Run content verification first:

```bash
"$CANDIDATE/.venv/bin/python" -B "$ARTIFACT/acceptance/s24/s24_fixture.py" verify --candidate "$CANDIDATE"
```

Run the ten artifact checks, which include local SDK stdio and negative controls:

```bash
"$CANDIDATE/.venv/bin/python" -W error::ResourceWarning -B "$ARTIFACT/acceptance/s24/test_fixture.py" --candidate "$CANDIDATE" -v
```

The full candidate suite and focused section 22 tests must also be measured in the guest under the approved plan. Record actual versions/counts/skips/exits and transitive dependency identity; the candidate lock pins only four direct dependencies.
`offline` can write a separate new private receipt and fresh state path. Its parent directories must be 0700; it never overwrites state or receipts. Preserve guest evidence and stop on a failed check.

## Phase B remains blocked

`serve` is a test-only stdio entry point, not permission to activate a route. A local SDK child used by the offline checks is not a tunnel fixture or live acceptance.
Before B: review/pin the whole artifact revision, complete private resource bindings, supply the separately reviewed live connector/controller adapter and actual budget/continuity observations, and obtain scoped provisioning/activation approval.
The callable matrix permits `parent-route-observations` only with a checkpoint callback. Presence of that callback is not approval or proof of monitoring: its implementation/results need review. No live adapter, SSH automation, credential reader, resource supervisor or host-control capability is supplied by this artifact.
Independent evidence review and explicit operator acceptance remain required. PR #80 stays HOLD; no historical cessation, host isolation, production/native/real-backend/full-quiescence or release claim is made.

## Historical development evidence and limits

Artifact checks cover real SDK stdio, negative ACK, in-run writer, post-run row, commit-gate, source-drift and controller-checkpoint controls. Development results are recorded in the PR after the final run; this is not guest or tunnel evidence.
The original-input 234-test candidate suite was run twice in that development environment (second run captured a complete log). Both runs failed: 4 failures, 1 error, 2 skips, exit 1. Four Codex process/zombie/worker cases failed; an OpenCode leader-observation case could not read its process stat; two POSIX permission cases explicitly skipped under root. Cause is not fully established here. No assertion, candidate source or skip condition was changed to make them pass.
Guest measurements of this revised input remain pending. CI separately runs the pinned candidate suite and this artifact on Python 3.12/3.14; it does not substitute for guest readiness or shared-host acceptance.

## Revised-input preparation checkpoint — 23 October 2026

After PR #90 merged at `686973b5240e30b8f9e5d274f75e918e0af5b76c`, the operator selected option ก with this complete message, verbatim:

> ก

This response selects option ก in the [input decision packet](../../docs/S22-PHASE-A-INPUT-DECISION-TH.md). No exact approval timestamp is available; none is invented. It authorizes preparation of this coupled source/manifest PR only, not its merge, revised guest execution, readiness PASS, B, release or deployment.
The proposed 104-file input has sole parent the original candidate and differs only in `tests/test_context_binding_unresolved.py` (+3/-3), blob `c9fae04df337699a679cbf994401c875428cc234`, identical to reviewed PR #89.
The runtime artifact differs only in PIN; its matrix, hooks, counters and ten artifact checks are unchanged. The manifest changes its commit and that one file entry. CI checks the revised full suite, focused tests and artifact, and rejects ResourceWarning/finalizing-database markers in combined output after process exit, in addition to checking the exit status.
Original guest evidence remains 234 full-suite OK, focused 7 OK with two finalizer warnings, artifact 10 OK; those warnings are not waived. Corrected-input guest results are pending. Preserve original-input development failures above as historical evidence; do not reuse them as revised-input measurements.
