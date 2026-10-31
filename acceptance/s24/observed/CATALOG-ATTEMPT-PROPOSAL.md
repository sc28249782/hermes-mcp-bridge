# J0 catalog attempt four — disabled wrapper and finite-action proposal

Status: **REVIEW PROPOSAL ONLY / NO FOURTH LIVE INVOCATION AUTHORIZED**.
Same draft #112. Source candidate at `74282917411c4feee9ed5da8694d9d15e207a4f0`
received independent exact-source APPROVE. Operator's subsequent “ทำขั้นถัดไป”
requests preparation of this reviewable disabled wrapper/proposal, not activation.
No precise timestamp is inferred. No new E counter is introduced.

Target remains the **J0 prerequisite for A2/A3**, not completion of those gates.
[Current eighteen-row ledger](R1-INTEGRATION.md#current-closure-ledger) stays OPEN.
[Catalog source packet](CATALOG-SOURCE-REVIEW.md) and [approved design](METADATA-CATALOG-DESIGN.md)
retain their source/evidence boundaries. Full R1 source acceptance is incomplete.

## Exact wrapper and reviewed source bindings

Wrapper is job `observed-catalog-proposal` in
[the observed workflow](../../../.github/workflows/s24_observed.yml).
It is structurally disabled at job scope with literal `if: ${{ false }}`; no step,
checkout, pin check or producer invocation from this job runs at this proposal.
Existing diagnostic job remains separately disabled; E12/E17 selectors and every
old job/step are unchanged. Only one new disabled job is added.

| Binding | Exact value |
| --- | --- |
| Workflow SHA256 at this proposal | `f2f0ab7735e43e4e7eb2fa6eacd39fe71cc4f65e75d4d872121e5360cc94a2a1` |
| Producer | `catalog_join_artifact.py` / `cc170eef2afabce715d1b0cb47f39e6a35b330f22fdbbe09d5835cb4bbb8dfb5` |
| Gate | `gate_artifact_catalog.py` / `266ef06341db67c95c069846967733c3bbc0cb4910e9898e5a4966f194332182` |
| Provider receipt | `J0-PROVIDER-SOURCE.json` / `41e2e56ff490475d899894e61c93b0e518439551f193031a8bef38b447805fbc` |
| Provider archive SHA256 | `bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e` |
| Fixed URL | `https://releases.ubuntu.com/24.04.5/ubuntu-24.04.5-wsl-amd64.wsl` |
| New unused activation subject | `ci: run approved metadata catalog attempt four once` |
| Attempt selector | Exact head checkout + exact subject + `GITHUB_RUN_ATTEMPT == 1` |
| Actor/runtime | Fresh GitHub-hosted `ubuntu-24.04`, setup-python `3.12`, ordinary runner user; checkout credentials not persisted |

Pin checks run before the producer. Producer independently verifies receipt
bytes/selection before network and archive digest before parser. Existing strict
sources/gates, catalog sources/gate/tests, runtime/PowerShell pins and all actual
attempt records are unchanged by this proposal.

## Proposed finite action — not yet approved

After independent wrapper review and a separate explicit operator approval:
**ONE additional producer invocation on CI**, the fourth live invocation in total,
using the pinned catalog lane above. Purpose: obtain either a validated catalog
receipt/selected regular hashes or a bounded diagnostic HOLD from the same fixed
provider archive. It is not an operator machine/VM run or inventory acquisition.

The wrapper invokes the producer exactly once with
`python -W error::ResourceWarning -I -S -B .../catalog_join_artifact.py --download-and-catalog-metadata`.
Combined stdout/stderr goes only to a new runner-temp log. It captures the real
exit status, then invokes the pinned gate with that log/status. Never cat/upload
raw output; only the gate's allowlisted data or constant rejection reaches CI log.
The runner-temp raw log and producer's private TemporaryFile are ephemeral;
no archive, rootfs or raw log is uploaded as an artifact or persisted to the repo.

Budgets: job 4 minutes; producer alarm 120 seconds, 512 MiB address space, no core;
HTTP timeout 15 seconds per operation; 1 GiB archive, 200000 normalized members,
4 GiB logical, 32 MiB per selected regular, <=32 selected, <=4096 name/link chars.
No proxy, redirect, retry, fallback, alternate URL/lane or changed parser predicate.
The 4-minute job cancellation is CI infrastructure containment, not proof of
operational actor cessation. This scope starts no WSL, sshd, guest or child worker.

Devices remain header metadata only; no extractfile/device read, mknod, mount,
permission/ACL application, link resolution, execution, extraction directory,
rootfs import, install, provisioning, system configuration or credential use.
Catalog output does not authenticate provider signatures or prepare a guest.

## Outcome, consumed budget and recording

| Observed result | Required disposition |
| --- | --- |
| Producer exit 0 and gate accepts | Record CATALOG ONLY, metadata_catalog_complete=true; archive_inspection_verified/prepared-image/extraction/import/setup/J0/R1/R2/scope remain false |
| Producer exit 2 and valid diagnostic | Gate emits bounded HOLD telemetry and exits 2; job FAILURE retained; no recovery or retry |
| Pin/guard/output/gate/warning/timeout failure | HOLD/failed action; preserve actual stage facts without inferring provider/member/path/root cause; no retry |

Any actual producer invocation consumes this single authorization, successful or
not. Approval will not authorize a fifth action. Automatic failed-job/rerun action
is forbidden for this live job; selector refuses run attempts >1. Exact-head and
subject are checkpoint guards, **not a durable exactly-once claim across separate
workflow runs/events**. Observe the activation run; do not dispatch another run.
If whether producer execution occurred is unknown, treat the budget as consumed
and HOLD pending independent disposition rather than rerun to find out.

After the single invocation, record approval verbatim/timestamp-or-NOT_PROVIDED,
activation full SHA, run/job IDs, real exit/conclusion and gate-emitted facts only.
Restore the job-level false guard in the record commit, whose subject differs
from activation; inspect that new head's job is SKIPPED. Do not change historical
E12/E14/E17 results or assign new reason/type/path retroactively.

## Proposal validation

Local validation parsed the workflow YAML, checked Bash syntax for both new run
blocks, and executed only the exact SHA preflight against the three actual
reviewed files. It did not invoke the producer. Removing the new disabled job
reconstructs the parent workflow bytes exactly; removing the two new document
notes reconstructs their parent bodies exactly. Both live proposal jobs retain
literal job-level false guards. Whitespace and new local links/fragments pass.
Unchanged catalog controls: 36/36 OK with ResourceWarning-as-error. Exact-head CI
must separately confirm this new job is SKIPPED; no live result is claimed here.

## Activation boundary for operator decision

This proposal does not activate anything. After wrapper review, operator may
approve only the finite action above. The later activation delta is **one line**:
remove this new job's false guard, with the exact subject shown in the table.
Record its actual full SHA after creation; no hypothetical activation hash here.
Reviewed producer/gate/provider hashes and all other workflow bytes stay fixed.
The later guard-restoration record is separate, preserving any real failure.

Current accounting remains three consumed invocations, TWO matching digests
(E14/E17), E12 UNKNOWN, no completed provider catalog/selected-hash receipt. No
fourth request occurred at this proposal. J0 kernel/boot/guest/ports/setup/lifecycle
bindings remain incomplete even if this future catalog succeeds. Same draft;
no merge, no R1/R2, no release/deployment. **J0 NOT READY; R1 NOT AUTHORIZED;
R2 HOLD; A6/A7 private bindings and #80/#96 unchanged.**
