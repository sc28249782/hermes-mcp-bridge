# Approved design §9 — implementation control coverage

Date: 30 October 2026. Status: incomplete acceptance controls; no VM scope.

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
