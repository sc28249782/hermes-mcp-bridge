# Handoff evaluation SPEC pinning policy proposal

Status: proposed for review on 5 November 2026. The proposal covers preparation CI
and historical evidence for the completed handoff evaluation. Implementation and
any change to SPEC follow the applicable [change control](SPEC.md#14-change-control).

## Evidence

The frozen evaluation protocol hashes the entire `docs/SPEC.md` file. The harness
opens that path in its checkout and checks the raw bytes before loading evaluation
roles. The preparation workflow checks out the PR head, so status-only changes to
SPEC can invalidate that check. The first mismatch on main came from the historical
status and evidence update in [PR #80](https://github.com/sc28249782/hermes-mcp-bridge/pull/80).

| Object | Recorded identity |
| --- | --- |
| Frozen SPEC source revision | `d7515c5fb4e33b41f81a8535fb06a0ea2cd72255` |
| Frozen SPEC SHA-256 | `d0f97851b7d1984cc6f2b249541f4b54bcd8f6f2e2f0c9f238d21055bcdccc65` |
| SPEC SHA-256 on main after #80 | `1218a8289d034c13d3e55d59a9103600061ba0e3f4dc31c801147dd28799c95b` |
| Frozen protocol SHA-256 | `af1b4b2c1db2bdd422c7954a5065a601c7e88f4097d08e05ade4a8c4a1e2c903` |

At the reviewed head of [PR #119](https://github.com/sc28249782/hermes-mcp-bridge/pull/119),
preparation stopped with exit 2 on Python 3.12 and 3.14. Both experiment jobs
were skipped. The [CI record](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41978839304)
and [offline closure](HANDOFF-OFFLINE-CLOSURE-TH.md) describe the two scopes.

## Proposed policy

The live SPEC serves the current repository contract. Historical evaluation uses
the exact SPEC bytes covered by its protocol and receipts. The manifest, pinned
harness, source digests and original receipts form one evidence chain. A future
experiment with different inputs requires its own protocol and receipts and a
separate execution decision.

For preparation CI, use an isolated temporary copy of the reviewed PR head and
place the verified frozen SPEC at the harness's expected path in that copy. This
lets the existing harness verify its complete allowlist and leaves any drift in
the other pinned inputs visible. Run current offline source checks from the
ordinary PR checkout and label results by their input scope.

The implementation proposal must specify a full commit ID and fixed Git path
controlled by reviewed repository source. Fetch the immutable object from this
repository with read-only access and check its size and SHA-256 before use. A
missing commit or blob, a mismatched hash, or drift in any other pinned path must
fail preparation. A missing object requires a separately reviewed recovery
decision. The preparation summary should report the PR head, frozen SPEC revision
and digest, current SPEC digest, and zero evaluation arms executed.

| Alternative | Consequence |
| --- | --- |
| Validate the complete historical tree | Gives historical reproducibility. A separate check is needed to detect other frozen-input drift on a PR head. |
| Validate the PR copy with the frozen SPEC at the expected path | Preserves full harness checks and makes drift in other pinned inputs visible. Requires a bounded, isolated copy and a clear summary of which SPEC was validated. |
| Change the protocol pin for a new experiment | Creates a different manifest identity. New receipts and execution scope are required. |

The recommended path for review is the isolated PR copy. Current SPEC header
maintenance should be reviewed on its own diff after the preparation policy is
settled. The existing development and heldout jobs remain disabled under their
consumed budgets.

## Acceptance criteria for a later implementation

- Preparation passes with the verified frozen SPEC and otherwise matching pinned
  inputs on Python 3.12 and 3.14. Existing offline and preparation controls report
  their actual results.
- Changes to current SPEC prose remain visible on the PR while preparation
  reports the independently verified frozen SPEC identity.
- A wrong frozen digest, missing source object, or mismatch in another pinned
  input fails closed. The preparation copy is bounded and isolated from the
  checked-out PR and repository worktree.
- The protocol, harness and both receipts compare byte-for-byte with the closure
  baseline. The two experiment jobs are skipped and zero evaluation arms run.

This packet records the decision for review. The current workflow and its
failure record provide the baseline for the later implementation review.
