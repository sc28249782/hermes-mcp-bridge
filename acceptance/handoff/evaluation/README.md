# Paired recovery evaluation — preparation/source candidate (NOT RUN)

Separate stacked PR over reviewed-but-unmerged #114 at
`c953b6f44116ba0740540e3c78d0b6e2c910573b`. No #114 merge, candidate edit or S24
change. J0 parked; R1 NOT AUTHORIZED / R2 HOLD. This package prepares the
[preregistered protocol](../../../docs/HANDOFF-RECOVERY-EXPERIMENT-PLAN-TH.md).
It does not execute either dataset arm, publish a gain or authorize a runtime pilot.

## Frozen inputs and comparator definition

`protocol.json` pins all imported evaluator/world/reference/candidate code,
profiles/schedules, approved schema/example and the audited original backend
sources by SHA256. Baseline source revision is `93e9601`; candidate revision is
`c953b6f4`. Full revisions are in the protocol. Inputs use closed compiled paths,
no caller-selected source, model, seed, endpoint, profile or budget. Every pin is
checked before candidate/reference roles are loaded. Hashes are integrity/provenance
checks, not authentication against a malicious same-uid writer who can replace
both manifest and code. Exact reviewed Git head remains the source authority.

The original baseline has no cross-session recovery planner. `baseline.py` is an
**independently written scripted client-reference policy**, not a claim that the
old bridge implements this algorithm or that a human performed the arm. It reads
the complete same reviewed dossier/IDs/authority and current fixture observations;
no evidence is deliberately withheld. It does not import candidate/checkpoint
code or apply a checkpoint checksum/store contract that baseline never had.
Expected profiles are separately enumerated; none are generated from candidate
outputs. Review of comparator/profile fairness is part of this source request.

H07/H10 are labeled `checkpoint_specific`: baseline may correctly observe a job
without using a damaged checkpoint. Their per-arm contracts/denominators differ.
Do not fold that difference into a causal task-success/recovery gain. Remaining
cases are `shared_contract`. Both scopes retain independent per-case/per-split/
per-arm numerator/denominator summaries. Native dispatch is absent from BOTH
advisory interfaces; zero dispatch metrics here cannot establish native backend
exactly-once/approval/production reliability.

## Corpus and held-out boundary

200 explicit schedules = 10 cases x (10 development + 10 heldout), each with
baseline/candidate arms: **400 proposed arm-trials**, not 400 completed trials.
Each case's configurations differ by fault variant, native backend contract
profile and/or committed checkpoint generation. Heldout labels do not mean secret
or statistically independent tasks: this is a public synthetic factorial corpus.
Candidate is frozen before its construction; no candidate tuning is authorized
from either split. A tie/no gain is a valid result. Source/profile fixes require
new hashes/protocol review before another evaluation, not silent held-out tuning.

Variants include actual lost ACK/reconstructed observer, wrong session/input,
missing dossier/profile, both cancel/completion orders, worker exit/unknown status,
changed bindings, checkpoint corruption/replay, crash before/after commit,
artifact absence/drift/verifier rejection, missing/revoked/expired authority and
competing CAS writers. The world reuses the pinned #114 owned-worker/ledger/store
fixture components; it is not a native Hermes/Codex/OpenCode adapter. Simulated
collector unknown_exit/status/authority/binding observations are disclosed, not
claimed as operational observations. Corruption uses synthetic bytes only.

## Trial supervisor and evidence

`harness.py` defaults to **validate only**. Import/CI/unit controls never call
`run_trial`, `World.prepare` or either corpus arm. Validate mode reads only fixed
pinned repository files; it does not import candidate roles or start a process.

A future explicit run would execute one split only, creating each arm's separate
private temporary world. Fixture worker, store fault/race children and the pure
decision child are all owned direct children of the supervisor; the decision
child does not own the fixture worker. No SIGSTOP, stored PID/PGID signalling,
service, network/model/SSH/CIM/guest or production environment is used. Local
multiprocessing pipes are IPC only. This is not OS sandboxing against same-uid
malicious code. Candidate remains reviewed/pinned; no dynamic task-code execution.

The fixed operation deadline is 10 seconds including setup/decision, <=3 fixture
metadata observations, <=1 same-logical replay, 0 new request IDs/model calls,
64 KiB checkpoint/32 evidence records. The source allows no replay dispatch;
replay count is zero by interface construction. Actual before/after effect and
job-row counts come from the independently read fixture ledger; duplicate count
also detects an already-doubled before/after floor. Forbidden API calls have no
provided dispatcher; their zero is an architectural scope fact, not native audit.

Emergency cleanup of <=4 direct fixture children is separately bounded at <=10 s
per child (<=40 s total). Any overall >10 s, timeout or unconfirmed cleanup fails
the trial; cleanup time never turns an over-budget trial into success. This is an
explicit protocol clarification for review before any run, not a relaxation of
successful-trial eligibility. A timeout is censored/failed, never retried.

Each world's parent records a monotonic **fault-schedule release** at the start
of the controlled injection sequence. Recovery duration ends after decision,
independent proof read and cleanup, using that same supervisor clock. Full elapsed
trial duration is recorded separately. These include remaining fixture work and
are not real backend/host observation timing, model latency or cross-host clocks.

`oracle.py` imports no candidate. It checks expected decision/reason/native status,
original job ID, reached_fault, cleanup, authority non-promotion, independent
artifact/verifier proof, effect/request counters and budgets. Correct HOLD,
recovery-eligible decisions and verified-task-success have separate denominators.
All failed/noncensored timing values remain; None timings count as censored.
Per-case summaries include median/p95/range, observed/censored/timeout counts.
No confidence/generalization/production inference is computed from repeated
synthetic fixtures; model/human comparisons NOT_TESTED, tokens NOT_APPLICABLE.

Each arm result is appended/fsynced to a new 0600 journal before the next arm.
Partial/aborted journals remain evidence but cannot form a passing receipt. A
final bounded receipt binds manifest/config/trace/row digests; no raw prompt,
output, exception text, credential or private path is printed. Each split requires
exactly 200 unique (schedule,arm) rows; metrics are recomputed from locked profiles
rather than trusting report flags. Candidate and baseline correctness gates are
both required, so a flawed reference cannot masquerade as candidate gain.
Heldout requires a matching complete passing development receipt, independently
revalidated; it is not an operator approval token or proof against fabricated
same-uid observations. No automatic run/retry/heldout continuation exists.

## Runtime facts and activation boundary

`runtime_facts(directory)` reads typed Python/OS/machine/kernel/SQLite and statfs
magic for the explicit output parent and default temp filesystem. statfs uses a
bounded buffer and Linux x86_64 ABI; no mount paths, hostname or directory contents
are emitted. It is a read-only CI capability snapshot, not a production probe.
Actual evaluation requires a non-null exact runtime binding in the protocol and
must match it before output creation. Initial source CI collects facts only;
they must be bound/reviewed before any future run. Other interpreter versions may
run preparation controls but cannot silently replace the selected runtime.

Future explicit CLI interfaces, **NOT executed in this PR**:

- Default / `validate`: pinned-input checks only.
- `development --output-root <new private directory>`: exactly 200 arm-trials.
- `heldout --development-receipt <matching receipt> --output-root <new private directory>`:
  exactly 200 more, only after independent development-result disposition and
  explicit operator instruction. Receipt validation alone grants no permission.

## Preparation controls and current result

18 preparation controls cover corpus/pin/split/scope invariants, default no-role/
no-arm execution, source drift rejection before role import, independent baseline
imports, duplicate JSON, unsafe success/identity/effect/authority/budget/cleanup/
unreached-fault mutants, denominator separation, incomplete development refusal,
metadata-only runtime facts and no output-root creation in validate mode.
CI also retains all 26 #114 controls unchanged. These are structural/oracle/source
controls, **not a dataset smoke run or paired evaluation**. Both corpus arms,
measured gain, actual baseline task success and held-out transfer are NOT RUN /
NOT MEASURED. No checkpoint or original candidate source was modified.

Next boundary: independent harness/profile/schedule/comparator/runtime review,
then a finite development-run instruction; preserve failures and review results
before any heldout action. Keep both source PRs draft until operator disposition.
#112/#80/#96/private A6/A7, J0/R1/R2 and release/deployment stay unchanged.
