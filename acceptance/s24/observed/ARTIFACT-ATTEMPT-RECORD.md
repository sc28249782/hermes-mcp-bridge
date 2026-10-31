# E12 — single CI artifact-inspection attempt

Date: 31 October 2026. Input: independently approved E11 at `c4d81d59`.
Operator instruction after review: run `--download-and-inspect` through CI, not
locally, to obtain actual archive evidence before guest package/setup source.
This instruction does not authorize guest provisioning, retries, merge or R1/R2.

## Execution boundary

The new `observed-artifact-once` job uses Python 3.12 on ubuntu-24.04 with a
four-minute job bound. The preparation process retains its reviewed 120-second,
512-MiB and byte/member/content limits. Before network access the step checks the
actual prepare_join_artifact.py and E10 JSON source hashes against E11. The
reviewed preparation source and pins are unchanged.

Exactly one live invocation is selected by commit subject
`ci: run reviewed E11 artifact inspection once (E12)` AND GITHUB_RUN_ATTEMPT=1.
This is a checkpoint selector, not an authorization token or an operational gate.
Other commits and reruns print NOT ATTEMPTED and skip the live step. There is no
Python matrix, automatic retry, alternate URL/archive, local fallback or setup
step. Future approved attempts would require a new explicit source/action scope.
Existing suites continue unchanged, including thirteen offline artifact controls.

The workflow retains complete stdout/stderr and scans post-exit warnings before
rejecting a failed exit. Success requires one bounded JSON line, exact computed
archive SHA and all review/readiness/guest/scope flags false. A successful
inspection is not a prepared image, import/boot test, signature verification,
full-tree manifest or completion of J0. A failed download/parser stays HOLD;
no archive evidence or guest package versions may be inferred from it.
Only the JSON receipt or constant HOLD plus gate metadata is printed; no archive
or private temporary path/key/account data is uploaded.

## Results

PENDING exact-head CI. No outcome is asserted by this source checkpoint.
E10/E11's no-live-download statements remain true of their historical deltas.
After this finite attempt, append the actual run/head/job, exit/warning facts and
receipt or failure. Do not overwrite historical false flags or reinterpret a
NOT ATTEMPTED job as an archive pass. Windows configured kernel, boot/coexistence,
setup/lifecycle/stop bindings and operational row dispositions remain open.
R1 NOT AUTHORIZED; R2 HOLD; #80/#96 unchanged; keep #112 draft and unmerged.
