# J0 literal catalog attempt five — disabled finite-action proposal

Date: 2 November 2026. **REVIEW PROPOSAL ONLY / NO FIFTH INVOCATION AUTHORIZED**.
Input #112 `e1e438f0d0992dc1d30f01a6a8c95735041a293b`.
Operator-supplied round-22 review approved the exact V2 source at that head.
The subsequent “ทำขั้นถัดไป” prepares this disabled wrapper/proposal only;
exact approval timestamp NOT_PROVIDED. No new E counter or full R1 acceptance.

[Source packet](LITERAL-CATALOG-SOURCE-REVIEW.md),
[route/design](CATALOG-BACKSLASH-DISPOSITION.md) and
[bounded work package](J0-RESUMPTION-WORK-PACKAGE.md) retain their boundaries.

## 1. Current evidence and alternatives stay open

Actual accounting remains FOUR consumed invocations / THREE recorded digest
matches (E14/E17/fourth); E12 UNKNOWN. Attempt four is still
[HOLD/BACKSLASH](CATALOG-ATTEMPT-FOUR.md), not a V2 failure or parser defect.
No completed catalog/selected-entry receipt or actual rejected member/path is known.
Synthetic V2 controls do not diagnose the provider archive.

| Operator option | Scope / disposition |
|---|---|
| A — retain V1, nominate another artifact | Still available; requires its own exact provider/source/hash/policy/route review; no alternate is nominated, downloaded or substituted here |
| B — reviewed V2, one finite attempt | Source preparation was selected; this proposal requests review of a possible fifth invocation using that exact source, not approval to run |
| C — defer this CI route | Still available; A2/A3 and all other obligations stay OPEN; no operator-VM fallback or waiver |

Approving source B did not close A/C as future decisions or grant a new attempt.
Operator may choose not to activate this job. No automatic route switch occurs
on failure. A future HOLD returns to route-or-defer; no automatic sixth invocation,
new parser-policy increment, timer widening or fallback.

## 2. Exact disabled wrapper and bindings

New job: `observed-literal-catalog-proposal` in
[the observed workflow](../../../.github/workflows/s24_observed.yml).
Literal job-level `if: ${{ false }}` prevents **every step**, including checkout,
setup-python, selector, pin check and producer invocation, at this proposal head.
Existing V1 catalog and diagnostic jobs remain independently disabled; inherited
handoff experiment jobs retain their guards. All old workflow bytes remain intact.

| Binding | Exact proposed value |
|---|---|
| Disabled workflow SHA256 | `b0dab8abcf04144e088c342e5938552f7dcf764b625d770077ed36210b1b02e6` |
| V2 producer | `catalog_join_artifact_literal.py` / `16d1953d2094281d39c328dd54bada15de6be3e1b3f84cbddf8b69acbf39fc90` |
| V2 gate | `gate_artifact_catalog_literal.py` / `f7cf5136f8aaedecbe640fe960e0ae4f7c9fe5b7daf9f5992e410830ad53d4ba` |
| Provider receipt | `J0-PROVIDER-SOURCE.json` / `41e2e56ff490475d899894e61c93b0e518439551f193031a8bef38b447805fbc` |
| Fixed provider URL | `https://releases.ubuntu.com/24.04.5/ubuntu-24.04.5-wsl-amd64.wsl` |
| Archive digest | `bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e` |
| Policy | `ROOTFS_METADATA_CATALOG_V2_LITERAL_NAMES` |
| Runtime/actor | Fresh GitHub-hosted `ubuntu-24.04`, setup-python `3.12`, ordinary runner user; checkout credentials not persisted |
| New unused activation subject | `ci: run approved literal metadata catalog attempt five once` |
| Selector | Exact event-head checkout + matching checkout SHA + exact subject + `GITHUB_RUN_ATTEMPT == 1` |
| Activation SHA | NOT_CREATED; record actual full SHA after separately authorized activation |

All three source/receipt SHA checks precede the producer. The producer independently
binds receipt selection before network, then hashes the archive before parsing.
No current source/test/runtime/PowerShell pin, prior selector or actual record changes.

## 3. Finite action proposed for separate approval

Only after independent wrapper/proposal review and explicit operator action approval:
**ONE producer invocation on CI**, fifth total, to obtain either a V2 CATALOG ONLY
receipt/selected hashes or bounded HOLD telemetry from the same fixed archive.

Producer argv, from repository root (interface binding, not a run instruction):
`python -W error::ResourceWarning -I -S -B acceptance/s24/observed/catalog_join_artifact_literal.py --download-and-catalog-literal-metadata`.
Combined stdout/stderr goes to the new runner-temp `s24-literal-catalog-proposed.log`.
Capture its actual exit once, then invoke the pinned
`gate_artifact_catalog_literal.py` with that log and exit code.

Never cat, echo or upload raw producer output. Only checked gate data or constant
rejection reaches public CI logs. No archive, raw log, extracted tree or prepared
image is uploaded or persisted to the repo. Only allowed gate facts may be recorded;
non-selected names/device metadata stay hash-only. The private TemporaryFile is
ephemeral and is not an inspected/prepared guest artifact.

| Budget | Bound |
|---|---|
| Job | 4 minutes |
| Producer alarm / address space / core | 120 s / 512 MiB / disabled |
| HTTP operation timeout | 15 s; no proxy, redirects, retries or fallback |
| Archive / normalized members / logical bytes | 1 GiB / 200000 / 4 GiB |
| Selected regular / selected count / name-link lengths | 32 MiB each / 32 / 4096 characters each |

No URL/image/lane substitution, predicate change, package installation, credential
use, WSL, sshd, guest, child worker, mknod, mount, extraction directory, link
resolution, filesystem member materialization, permission/ACL application or
system configuration. This is not operator VM access or R1 inventory.
Job cancellation is CI infrastructure containment, not operational stop proof.
Missing prerequisites/timeout/uncertain stop cannot be reported as readiness.

## 4. Outcomes and consumed scope

| Result | Mandatory disposition |
|---|---|
| Producer exit 0 + gate accepts | Record V2 metadata_catalog_complete=true only; strict archive_inspection_verified/extraction/prepared-image/import/setup/J0/R1/R2/scope remain false |
| Producer exit 2 + valid diagnostic | Gate emits fixed-schema HOLD telemetry and returns 2; job FAILURE preserved; no retry/recovery |
| Pin/guard/output/gate/warning/timeout failure | HOLD, record only proven stage/error facts; no raw exception/path/member inference, no automatic repeat |

An actual producer invocation consumes the single authorization regardless of
outcome. If execution is uncertain, treat budget as consumed and HOLD for
independent disposition. A positively identified pre-invocation failure is not
permission to retry; it also returns for disposition. Do not rerun this workflow
or failed job. Selector rejects run attempts >1; it is a checkpoint guard, **not
durable exactly-once protection across separately generated workflow events**.
Observe the one activation run and do not dispatch another.

After action, record operator approval verbatim with timestamp or NOT_PROVIDED,
actual activation SHA, run/job/attempt IDs, producer/gate exit and real conclusion,
plus allowed gate facts. Preserve failures and prior E12/E14/E17/fourth records.
No reason/type/count is backfilled. Restore this job's false guard in the record
commit with a non-activation subject; inspect new-head SKIPPED. With that single
guard restored and no other workflow edit, workflow bytes return to the proposal
SHA above. A completed catalog still leaves kernel/boot/guest/setup/lifecycle
and the same-invocation Windows SSH/collect/CIM target unproved.

## 5. Validation and activation boundary

Local checks parsed YAML, checked both new Bash blocks, and executed **only** the
three-file SHA preflight against actual reviewed source/receipt bytes. No producer
or gate execution, download, archive inspection or new trial occurred. Removing
the new job reproduces the parent workflow byte-for-byte. Two additive document
notes preserve original bodies; source/control/record blobs stay unchanged.
New links/whitespace are checked; exact-head CI must separately confirm SKIPPED.
The unchanged 46 V2 controls retain their named-head source-review evidence;
green regression is not action approval.

After proposal review, a separately approved activation is a **one-line removal**
of only this new job's false guard, using the exact new subject above. No invented
activation hash, reused fourth/diagnostic selector or source/pin edit. Any later
action requires approval of this finite scope; “ทำขั้นถัดไป” here is not that approval.

All eighteen [ledger](R1-INTEGRATION.md#current-closure-ledger) rows stay OPEN.
J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD; private A6/A7 and #80/#96 unchanged.
Full provider catalog is not full J0/source acceptance and cannot authorize R1.
Same draft/unmerged #112; no release/deployment or operational gate closure.
