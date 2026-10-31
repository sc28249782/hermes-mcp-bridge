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

## Actual E12 outcome — HOLD, not archive verification

The pending statement above describes the initial source checkpoint. The actual
attempt at head `2bf5741a5fbd917795d006d7b90ddc23165c8378` ran in
[observed workflow 41170222586](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41170222586),
job `124446375046` (`observed-artifact-once`), run attempt 1, Python 3.12.15.
Its live step ran 11:51:15–11:51:17 Bangkok time on 31 October 2026
(04:51:15–04:51:17 UTC in the original log). The checked source
returned constant `HOLD: artifact preparation incomplete`, exit **2**. The wrapper
printed `artifact_live_exit=2`, `attempts=1`, `retry_permitted=false`, with empty
ResourceWarning/finalizer markers, then correctly rejected the exit (gate exit 1,
job failure). The separate runner reported Node.js 20 action deprecation; empty
preparation-process warning markers do not mean the entire Actions log had no
warnings. No retry or local download was executed.

[Machine-readable attempt facts](ARTIFACT-ATTEMPT-E12.json) deliberately contain
no computed archive hash. There is NO verification receipt, inspected catalog or
selected guest binary evidence. Constant HOLD does not identify the failure stage:
network success, completed download, hash match and parser progress are UNKNOWN.
Duration alone is not a diagnosis. Do not infer HTTP error, digest mismatch,
unsupported format or missing guest package from this output. E10/E11's historical
archive flags remain unchanged; this failed attempt does not turn them true.

The approved single attempt has been consumed. This documentation commit has a
different subject and must skip the live step, as must a rerun. Successful tests
at a later documentation head do not supersede this failed live result. Guest
package/build/setup source remains BLOCKED on actual artifact evidence, alongside
the existing Windows kernel/boot/coexistence and lifecycle bindings.

Next source-review topic: a privacy-safe finite diagnostic contract, if a future
attempt is authorized. It would need explicit stage/error enums and completed
byte/hash milestones without URLs from redirects, exception text, host/temp paths
or credentials, preserving all limits, no retries and constant HOLD. No such new
source, telemetry, network probe, alternate download or second attempt is executed
in E12. No provisioning, setup or R1/R2 authority follows this HOLD.
