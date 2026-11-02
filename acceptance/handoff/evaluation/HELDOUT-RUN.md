# Heldout split — one approved run (2 November 2026)

## Authority and scope

Operator message, verbatim: “อนุมัติทำขั้นถัดไป”.
Exact approval timestamp: NOT_PROVIDED. In context this separately approves the
next heldout run after independent acceptance of the
[development results](DEVELOPMENT-RUN.md) at
`fb3e796cdfcdb0a377dde1db065db48bdeea1f60`. It is separate from source approval.

One heldout split only: 100 schedules x baseline/candidate = 200 arm-trials.
No development rerun, retry, tuning, merge or operational pilot.
No real backend/model/Dev/production calls. J0 parked; R1 NOT AUTHORIZED / R2 HOLD.
PR #112 is untouched; PR #114/#115 remain draft and unmerged.

## Execution and frozen inputs

- Activation: `6f7b81d7f7362c71f6d0e9f5a36bb81886b3fa5c`, subject
  `ci: run approved handoff heldout split once`.
- [Run 41437912825](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41437912825),
  attempt 1; heldout job `125252238491`: SUCCESS, harness exit 0.
- Protocol SHA256:
  `af1b4b2c1db2bdd422c7954a5065a601c7e88f4097d08e05ade4a8c4a1e2c903`.
- Harness SHA256:
  `ca211b2be3bcb414a08c7eb97c5d2d9d0ba1c5aa2d7892281d63568ea732c2b3`.
- Development receipt preflight SHA256:
  `d1a023c6a52aba5b9f6ea4f51f88e7777317a1004dca4d8457887ba83cfafaed`.
  The existing harness validates its manifest, all 200 development rows, traces,
  aggregate, runtime and passing threshold before heldout output/trials.
- All 17 protocol source pins, corpus/profiles/schedules, candidate and runtime
  binding remain unchanged. No new profile selection, seed or budget.
- Actual runtime matched: Linux x86_64; Python 3.12.15; SQLite 3.45.1;
  kernel 7.0.0-1017-azure; output-parent and temporary filesystem magic 61267.
- Warning markers: []. One heldout invocation, no workflow rerun/fallback.
  The development job was SKIPPED in the same activation run.

The new job uses the prior checked collector pattern, with heldout split names,
a pinned passing development receipt, exact activation subject/head and attempt-1
selector. The result-record commit restores its job-level false guard.
The original development job stays disabled throughout.

## Heldout outcomes — denominators separate from development

| Scope | Arm | Correct decisions | Verified recoveries / eligible | Verified task successes / eligible |
|---|---|---:|---:|---:|
| shared_contract | scripted baseline | 80/80 | 27/27 | 5/5 |
| shared_contract | candidate | 80/80 | 27/27 | 5/5 |
| checkpoint_specific (H07/H10) | scripted baseline | 20/20 | 20/20 | 0/0 |
| checkpoint_specific (H07/H10) | candidate | 20/20 | 2/2 | 0/0 |

Each H01–H10 case has 10 trials per arm. All 200 heldout rows meet their
preregistered contracts; `threshold_passed=true`.
Duplicate effects, unauthorized actions, incorrect successes, timeouts and
censored rows are zero in these fixtures. Correct HOLD is included in correct
decisions; it is not counted as a verified recovery.

Shared-contract outcomes tie again. No task-success/recovery outcome gain over
the scripted reference is demonstrated. H07/H10 have different arm contracts
and recovery eligibility, so their recovery totals cannot be treated as causal
gain/loss. All per-case timings remain in the receipt; no operational latency
improvement is established by this single serial synthetic run.

Development and heldout results retain their separate denominators and receipts.
The two approved invocations total 400 arm-trials, not 400 independent tasks.
This is the public synthetic factorial corpus described in the protocol;
“heldout” is a frozen split label, not a secret statistically independent sample.
The comparator is a scripted client-reference policy, not the old live bridge,
a model or a human. Model/human comparison remains NOT_TESTED; token comparison
NOT_APPLICABLE. Both advisory interfaces lack native dispatch: zero dispatch
metrics do not prove native exactly-once/approval/production reliability.

## Evidence and validation

[Exact heldout receipt](heldout-receipt.json), SHA256:
`9f7862f212397956c4fbd7f1140dddf3f021cc8aae3e04aad797d92ecd4fe07f`.
Rows SHA256:
`705562cdaba1a182f696da63c6f8824f6e22c16eec1e9ed9682ee38e303daa8e`.

The collector validated the receipt and emitted one header, 200 bounded synthetic
row frames and an end digest. The committed receipt was reconstructed from those
frames; its bytes match the original file SHA exactly. Independent receipt-only
validation checked canonical bytes, row/trace hashes, frozen schedule/profile
bindings, passing development prerequisite and recomputed oracle metrics and
aggregate. This validation did not execute any arm.

Original fsynced journal, receipt and action summary are retained in artifact
`handoff-heldout-once-41437912825`, ID `13137072145`, archive digest
`sha256:2bded99b95a577ef9260924fdfeffdbae77bc950b8b51e5912752d0f79397f36`.
The CI artifact expires 2 December 2026; this exact repository receipt persists.
No raw harness/child output was printed or uploaded.

At the activation head, preparation jobs `125252238905` (3.12) and
`125252238888` (3.14) each passed 26 inherited + 18 preparation controls, with no
skips/warning markers and zero corpus arms in those jobs. These controls are
distinct from the 200 heldout arm-trials.

## Disposition

Heldout budget consumed: one split, 200 arm-trials. Development and heldout
execution are complete for this frozen protocol. No additional run, tuning or
merge is authorized. Submit the actual heldout result and combined disposition
for independent review; any product/runtime integration needs its own scope.
Passing fixtures do not close S24 rows, establish candidate gain, authorize R1/R2
or complete a release/deployment milestone.
