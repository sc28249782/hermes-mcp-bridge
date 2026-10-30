# Approved design §9 — implementation control coverage

Date: 30 October 2026. Status: incomplete acceptance controls; no VM scope.

| # | Required group | Actual control / outstanding obligation |
| --- | --- | --- |
| 1 | G written but not consumed | Real worker stdin EOF/no-G returns readiness only thenHOLD; protocol rejects no-entry |
| 2 | Worker alive before collect | Window pre-check rejects bound-only state; live guest integration still blocked |
| 3 | Sample before entry/after leaving | Pure protocol rejection tests pass; real host sample integration outstanding |
| 4 | Exit/PIDreuse/identity drift | Synthetic pid/digest/liveness rejection tests pass; mandatory real adoption ERROR at procfs coherence; real stale-handle/UID/argv matrix outstanding |
| 5 | Exit during sample | Protocol false-liveness rejection passes; end-to-end fast-exit integration outstanding |
| 6 | Buffered leaving before post | State rejection after fed leaving passes; real wrapper drain/post scheduling test outstanding |
| 7 | Full/short/closed marker pipe | Actual disposable subprocesses exit72, no success output; identity is fabricated only for marker fault isolation |
| 8 | Exception/finally boundary paths | Normal-return/exception events tested; actual helper fatal exits at entered/leaving tested; underlying body AST preserved |
| 9 | Malformed/duplicate/oversize/order | Strict parser/state/framing/budget/partial-EOF tests pass; transport integration outstanding |
| 10 | Correlation/worker mismatch | Pure protocol rejection tests pass; real Windows transport negative controls outstanding |
| 11 | Missing/slow/low/corrupt sample | Host checks implemented; offline Windows runner14checks and process runner9checks NOT RUN; actual sample/provider integration outstanding |
| 12 | SSH EOF/cancel/adoption timing | Code has bounded HOLD cleanup and no reconnect; parser EOF controls pass; real cancellation/stop/EOF matrix outstanding |
| 13 | Flood/blocked provider/output | Parser/log bounds and real alarms pass; host async I/O/process-start/provider blockage controls outstanding |
| 14 | Log write/fsync failure | Actual disposable private-log failure preserves bytes and rejects; wrapper/host end-to-end log failure injection outstanding |
| 15 | No feedback/no delay | Marker atomic pipe test needs no ACK; no production sleep/SIGSTOP; real fast-run integration outstanding |
| 16 | Baseline regression/flags | Original body AST preserved; pinned baselines and approved transfer sources unchanged; protocol flags false; full variant-regression suite outstanding |
| 17 | Real Linux processes/pipes | Real no-G/alarms/fatal pipes pass; real adoption mandatory ERROR; no coherent-Linux end-to-end result |
| 18 | Windows offline/live separation | Offline runner never calls Get-S24HostMemorySample/SSH/process launch; not run locally; no live Windows/CIM/operator evidence |

The failed real-adoption test is kept in the default suite. No skip, retry,
predicate relaxation or suppression turns the suite green. Rows marked partial
are explicit pending source-acceptance work, not covered by design approval or
the prior transfer writer's26controls. All runtime predicates and private bindings
must be reviewed independently of this matrix and its synthetic test results.
