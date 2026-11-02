# Development split — one approved run (2 November 2026)

## Authority and scope

Operator message, verbatim: “ทำขั้นถัดไป และอนุมัติ development run แยกจากผลรีวิว source”.
Exact approval timestamp: NOT_PROVIDED. This is action approval separate from the
source review at `41c5d55b373dfc9ff4be33b81a6f216534c72ab2`.

One development split only: 100 schedules x baseline/candidate = 200 arm-trials.
No retry, tuning, heldout, merge, real backend/model call or operational pilot.
J0 parked; R1 NOT AUTHORIZED / R2 HOLD. #112 remains untouched.

## Execution and immutable inputs

- Activation: `b8d5c58597b6dd6532586b7a27e3d1a7218329a0`, subject
  `ci: run approved handoff development split once`.
- [CI run 41436015130](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41436015130),
  attempt 1; development job `125245843034`: SUCCESS, harness exit 0.
- Protocol SHA256: `af1b4b2c1db2bdd422c7954a5065a601c7e88f4097d08e05ade4a8c4a1e2c903`.
- Harness SHA256: `ca211b2be3bcb414a08c7eb97c5d2d9d0ba1c5aa2d7892281d63568ea732c2b3`.
- All 17 protocol source pins, profiles, schedules, candidate and runtime binding
  stayed unchanged. Activation changes only the workflow wrapper.
- Actual runtime matched: Linux x86_64, Python 3.12.15, kernel
  7.0.0-1017-azure, SQLite 3.45.1, output-parent and temporary fs magic 61267.
- Exactly one harness development invocation; no workflow rerun or alternate
  runner requested. Warning markers: [].

The selector requires exact checked-out event head, activation subject and attempt 1.
The result-record commit disables the development job at job level. Its ordinary
preparation jobs do not execute corpus arms.

## Results and denominators

| Scope | Arm | Correct decisions | Verified recoveries / eligible | Verified task successes / eligible |
|---|---|---:|---:|---:|
| shared_contract | scripted baseline | 80/80 | 26/26 | 4/4 |
| shared_contract | candidate | 80/80 | 26/26 | 4/4 |
| checkpoint_specific (H07/H10) | scripted baseline | 20/20 | 20/20 | 0/0 |
| checkpoint_specific (H07/H10) | candidate | 20/20 | 2/2 | 0/0 |

All 200 rows satisfy their preregistered contracts; `threshold_passed=true`.
Each case has 10 trials per arm. Duplicate effects, unauthorized actions,
incorrect successes, timeouts and censored rows are all zero in these fixtures.
Correct HOLD is included in correct decisions; it is not a verified recovery.

Shared-contract outcomes tie: this run demonstrates no task-success or recovery
gain of candidate over the scripted reference. H07/H10 recovery eligibility
differs by arm, so those numbers must not be presented as causal gain or loss.
Per-case timings and all rows are retained in the receipt; timing samples from
one serial synthetic run do not establish operational latency improvement.

The baseline is the reviewed scripted client-reference policy, not the old live
bridge or a human. This public synthetic corpus is not a secret independent
heldout dataset. Native dispatch is absent from both advisory interfaces, so zero
dispatch metrics cannot establish native backend exactly-once reliability.
Model and human comparisons remain NOT_TESTED; token comparison NOT_APPLICABLE.

## Evidence and validation

[Exact receipt](development-receipt.json), SHA256
`d1a023c6a52aba5b9f6ea4f51f88e7777317a1004dca4d8457887ba83cfafaed`.
Rows SHA256:
`31cff748a318e18d427ba14fe61655cea2fb5a5c0f9c3965862c94098ac91f43`.

The checked collector emitted a header, 200 bounded synthetic row frames and an
end digest. This repository receipt was reconstructed from those frames and its
bytes match the original receipt SHA exactly. Receipt-only validation reran
`validate_records` and `oracle.aggregate`, checked canonical bytes, all trace
hashes and rows digest; it did not execute any arm.

Original receipt, fsynced records.jsonl and action summary are also retained in
CI artifact `handoff-development-once-41436015130`, artifact ID `13136432685`,
archive digest `sha256:faec27721b06651ef95c120e882c758f0bbb13bbc5e81dc2107c7d71aa1c200e`.
CI artifact expires 2 December 2026; the exact repository receipt is durable.
Raw harness/child output was not printed or uploaded.

At the activation head, preparation jobs `125245842519` (3.12) and
`125245843559` (3.14) each passed 26 inherited controls + 18 preparation
controls, with no skips/warning markers and zero corpus arms in those jobs.
These controls are separate from the 200 development arm-trials.

## Disposition

Development budget consumed: one split, 200 arm-trials. Additional development
retry/tuning and heldout execution are not authorized by this message.
Review these actual results independently before any heldout action proposal.
No release/deployment or S24 closure follows from this result.
PR #114/#115 remain draft and unmerged.
