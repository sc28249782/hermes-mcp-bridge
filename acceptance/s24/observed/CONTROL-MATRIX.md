# Approved design §9 — implementation control coverage

## Current status — 31 October 2026

Use the [current 18-row closure ledger](R1-INTEGRATION.md#current-closure-ledger)
for consolidated E1–E18 evidence and pending dispositions, and the
[A/B/C milestone map](../../../docs/S24-DELIVERY-CLOSURE-TH.md#current-milestone-status)
for delivery/authorization/release boundaries. All eighteen obligations remain
acceptance-OPEN; actual identity/component CI evidence is now available where the
original dated table says ERROR/NOT RUN/outstanding. Those old statements are
historical, not a claim that later evidence is missing. They are retained below
without weakening any obligation or replacing operator evidence with CI.

#107–#111 are merged; #112 remains draft/incomplete. No row closure/optional move,
source acceptance or R1 authority follows from this documentation update.
New E increments and implementation are paused pending milestone/route review.
J0 NOT READY; R1 NOT AUTHORIZED; R2 HOLD; live artifact job remains disabled.

## Historical control/evidence snapshots

Date: 30 October 2026. Status: incomplete acceptance controls; no VM scope.

Current closure criteria and stage ownership are in the [S24 delivery overview](../../../docs/S24-DELIVERY-CLOSURE-TH.md). This matrix mixes dated evidence checkpoints and outstanding obligations: its original local ERROR/NOT RUN entries remain historical, with later CI evidence below. The merged suite is 40 tests after #109; draft #110 reports 43 only on its own head. No row is closed, reclassified or made optional by this link. The next source increment must address the consolidated R1 integration criteria, not a test-count target.

PR #107 merged as `be88eef8cbf8d9726773f8579c4eaccc32d43c3d`. Exact reviewed head `81f18c6376c3b3a816f759860874e5050bac2eaa` passed coherent-Linux 34/34 on Python 3.12/3.14 and Windows 14+9 controls in CI runs [observed](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41048443885), [Tests](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41048443886), [fixture](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/41048444032). Earlier local failures below remain historical; the mandatory adoption and Windows-runner evidence gaps are closed by CI, not by an operator run.

| # | Required group | Actual control / outstanding obligation |
| --- | --- | --- |
| 1 | G written but not consumed | Real worker stdin EOF/no-G returns readiness only thenHOLD; protocol rejects no-entry |
| 2 | Worker alive before collect | Window pre-check rejects bound-only state; live guest integration still blocked |
| 3 | Sample before entry/after leaving | Pure protocol rejection tests pass; real host sample integration outstanding |
| 4 | Exit/PIDreuse/identity drift | Synthetic pid/digest/liveness rejection tests pass; mandatory real adoption ERROR at procfs coherence; retained pidfd after real child exit and injected UID/argv revalidation controls added; actual UID transition/exec/PID reuse still outstanding |
| 5 | Exit during sample | Protocol false-liveness rejection passes; end-to-end fast-exit integration outstanding |
| 6 | Buffered leaving before post | State rejection after fed leaving passes; real wrapper drain rejects atomically buffered entered+leaving with no sample frame; controller/identity are fixtures; live post scheduling still outstanding |
| 7 | Full/short/closed marker pipe | Actual disposable subprocesses exit72, no success output; identity is fabricated only for marker fault isolation |
| 8 | Exception/finally boundary paths | Normal-return/exception events tested; actual helper fatal exits at entered/leaving tested; underlying body AST preserved |
| 9 | Malformed/duplicate/oversize/order | Strict parser/state/framing/budget/partial-EOF tests pass; real wrapper malformed/partial-EOF pipe controls pass with fixture admission; Windows transport integration outstanding |
| 10 | Correlation/worker mismatch | Pure protocol rejection tests pass; real Windows transport negative controls outstanding |
| 11 | Missing/slow/low/corrupt sample | Host checks implemented; offline Windows runner14checks and process runner9checks NOT RUN; actual sample/provider integration outstanding |
| 12 | SSH EOF/cancel/adoption timing | Code has bounded HOLD cleanup and no reconnect; parser EOF controls pass; real cancellation/stop/EOF matrix outstanding |
| 13 | Flood/blocked provider/output | Parser/log bounds and real alarms pass; host async I/O/process-start/provider blockage controls outstanding |
| 14 | Log write/fsync failure | Actual disposable private-log failure preserves bytes and rejects; wrapper/host end-to-end log failure injection outstanding |
| 15 | No feedback/no delay | Marker atomic pipe test needs no ACK; no production sleep/SIGSTOP; real wrapper fast-completion fixture produces only HOLD and reaps its direct child; real inventory fast-run integration outstanding |
| 16 | Baseline regression/flags | Original body AST preserved; pinned baselines and approved transfer sources unchanged; protocol flags false; full variant-regression suite outstanding |
| 17 | Real Linux processes/pipes | Real no-G/alarms/fatal pipes pass; real adoption mandatory ERROR; no coherent-Linux end-to-end result |
| 18 | Windows offline/live separation | Offline runner never calls Get-S24HostMemorySample/SSH/process launch; not run locally; no live Windows/CIM/operator evidence |

The failed real-adoption test is kept in the default suite. No skip, retry,
predicate relaxation or suppression turns the suite green. Rows marked partial
are explicit pending source-acceptance work, not covered by design approval or
the prior transfer writer's26controls. All runtime predicates and private bindings
must be reviewed independently of this matrix and its synthetic test results.

Follow-up control scope: `WrapperPipeControls` exercises the unchanged guest wrapper event loop, actual nonblocking observation pipe, subprocess EOF, private log and direct-child cleanup. It substitutes controller source loading, target admission and worker identity/liveness only inside the disposable test subprocess. It does not close real identity, successful post-check, host transport, provider, ACL or inventory-regression obligations. The CI runner now requires all 37 tests; no original test is removed or skipped.

Identity follow-up: `WorkerIdentityControls` requires actual `ReadOnlyWorker` admission against a live disposable direct child with coherent procfs and a retained pidfd. Exit is real; UID/argv drift is injected only into subsequent identity reads. No identity predicate is stubbed during admission. Real PID reuse, UID change, exec and full wrapper handling remain unproved. The mandatory suite count is now 40; original tests are unchanged.

Local host-handshake follow-up: `WrapperHostHandshakeControls` drives the actual guest wrapper loop with real host stdin/stdout, a subprocess observation pipe and a private log. It covers successful post-check through final receipt plus wrong-challenge and duplicate-post HOLD paths, requiring exact frame/log order, false scope flags and a reaped fixture child. Fixture source loading/identity admission and a test-only release pipe isolate orchestration; no real sample or inventory body runs. Rows 3/5/6/9/10 still require actual sampling, worker/transport and scheduling evidence as applicable; this is not Windows/SSH evidence. The mandatory suite count is now 43, retaining every earlier test.

## Consolidated integration ledger

Continue remaining A1–A5 work in [R1-INTEGRATION.md](R1-INTEGRATION.md), which supplies a disposition/evidence entry for all eighteen rows. Its E1–E3 controls add helper regression, an actual controller/worker/collect failure path and separate Windows CI ACL/CIM checks. Rows remain PARTIAL/OPEN pending exact-source review and the stated integration obligations; this checkpoint does not overwrite historical results or claim source acceptance.
