# E14 — disabled CI wrapper proposal; no second attempt authorized

Date: 31 October 2026. Input: approved E13 at `474778ca`.
Status: **SOURCE/ACTION PROPOSAL FOR REVIEW; LIVE JOB DISABLED**.
The review explicitly requires separate scope approval before another attempt.
This delta prepares that reviewable scope; it does not activate it. Keep #112
in draft, unmerged. E12's failed [record](ARTIFACT-ATTEMPT-RECORD.md) stays UNKNOWN.

## 1. Exact sources and two-line gate

| Source | Author-computed SHA256 |
| --- | --- |
| prepare_join_artifact_diagnostic.py (unchanged E13) | `ed1f9b689b6fb38593ffd101a437f1d8985260de993fb45c6b6213fee8d4482d` |
| J0-PROVIDER-SOURCE.json (unchanged E10) | `41e2e56ff490475d899894e61c93b0e518439551f193031a8bef38b447805fbc` |
| gate_artifact_diagnostic.py | `ef7a8fc8923eacb565cfd559312aa372609204fe118d8e765e7a173ddc0987f2` |
| test_artifact_gate.py | `d4536d469761bbd23becbdb5a8e2d6965844f2e05285050a662ef3638bf70ffe` |

The new validator reads at most 67,587 bytes from the process log and rejects
anything over the 67,586-byte combined two-line ceiling. Require ASCII, exactly
two LF-terminated lines, no CR/extra line, first <=65,536 bytes and second <=2,048.
Reject ResourceWarning, any `Exception ignored` and Traceback markers before
parsing/accepting a receipt. Do not cat raw output or print caught exception text.
Unknown JSON fields, duplicate keys and non-finite numbers are refused. Invalid,
missing, unavailable, oversized or unknown-exit output yields constant gate HOLD,
exit 2, without echoing any untrusted text/path. The unavailable E13 fallback is
not a normal diagnostic frame and cannot become success.

Validate exact diagnostic key-set/schema/enums, strict boolean flags, bounded
integer byte/member milestones and null digest/match until hash completion.
All readiness/guest/scope flags remain false. On process exit 2, require exact
first-line constant HOLD and non-NONE diagnostic error; emit the allowlisted
frame with archive_inspection_verified=false, STILL exit 2. This makes valid
failure telemetry visible without recovering the failed job or accepting it.

On exit 0, additionally validate the complete E11 inspection key-set, provider
archive digest, original size/count/catalog limits and exact selected-entry
metadata shape (public selected archive names and regular-file hashes only).
Require COMPLETE/NONE, download/hash complete and matching digest, with identical
archive bytes/received/hashed counts and member counts across frames. Only then
emit inspection plus diagnostic and archive_inspection_verified=true, exit 0.
This field means archive-byte/inspection evidence only; prepared-image/import/
J0/setup/guest/R1/R2 flags remain false. No extraction, subprocess or network in
the gate; its log path is a wrapper argument, never serialized or accepted as
provider data. Raw invalid/unknown fields are never emitted.

## 2. Proposed finite action, not activation

`observed-diagnostic-proposal` is guarded at JOB LEVEL by literal `${{ false }}`.
It therefore executes NO checkout/setup/selector/source/producer/gate step in
this delta. The E12 selector is untouched and must also skip this head. Normal
CI adds only the new ten OFFLINE gate controls on Python 3.12/3.14; original
69 + 13 + 25 and Windows/identity/carrier controls remain unchanged.

If source and finite action scope are separately approved, the reviewable
activation delta is limited to removing the disabled-job guard and using unique
commit subject `ci: run approved diagnostic artifact attempt once (E14)`.
The inner selector then requires that exact subject AND GITHUB_RUN_ATTEMPT=1;
all later commits/reruns skip it. The subject is a checkpoint selector, never an
authorization token. Do not reuse E12, silently rerun, or treat source approval as
action approval. The actual activation SHA must be recorded after it exists;
none is invented here.

Proposed action: one Python 3.12 process on disposable ubuntu-24.04 CI, four-minute
job, unchanged E13 120 s/512 MiB and archive/content limits. Verify the three exact
source hashes above before any network request. Then execute once:

```sh
python -W error::ResourceWarning -I -S -B acceptance/s24/observed/prepare_join_artifact_diagnostic.py --download-and-inspect-diagnostic
```

Retain combined stdout/stderr only in a new runner-temp log and pass its actual
exit to the checked gate. No raw log upload/cat, key/account/host action, retry,
proxy/redirect/fallback, alternate archive/version, package setup, WSL, guest boot,
provisioning or destruction. A valid diagnostic HOLD, parser/hash failure, missing
output or unavailable environment stays failed and consumes that one attempt;
no next action follows automatically. Existing producer temp cleanup closes only
its own new file; CI job timeout is not operational stop/cessation proof.

## 3. Offline controls and exit boundary

Ten synthetic controls check producer-enum alignment, valid HOLD staying failure,
real parser/hash fixture success through the gate, framing/warning rejection,
duplicate/unknown-key/enum/schema refusal, strict false flags and milestone types,
unknown exit/unavailable rejection, cross-frame mismatch, extra/private fields
and constant CLI rejection without raw-input echo. Fixture success temporarily
binds the gate's expected digest to synthetic archive bytes; it does not contact
or validate the real provider. Main tests mock only its log input, never execute
the producer CLI. No second live attempt, archive evidence or setup completion
is claimed by these tests.

Review the wrapper/gate and this finite proposal before operator action approval.
A source APPROVE alone leaves the job disabled. Preserve E12 as failed evidence;
J0 NOT READY, R1 NOT AUTHORIZED, R2 HOLD and all outstanding integration/private/
kernel/lifecycle bindings remain. No merge, #80/#96, release or deployment change.
