# SPEC §24 — Phase A shared-host readiness record

Date: 23 October 2026.
Status: **READY FOR INDEPENDENT REVIEW — not a Phase A acceptance verdict or Phase B authorization**.
Plan: [S22-SHAREDHOST-20261023-01](S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md).
Input decision: [two-blob packet](S22-PHASE-A-TWO-BLOB-INPUT-DECISION-TH.md).
Artifact: [source and limits](../acceptance/s24/README.md).

## 1. Scope and provenance

The operator approved revised guest Phase A with this complete message, verbatim:

> อนุมัติ guest Phase A ตาม scope นี้

No exact approval timestamp was supplied; none is invented. The scope fixed the inputs, new private guest paths, original 30-minute window, resource thresholds, serial tests, evidence capture and a private 0600 receipt. It did not authorize B, a connector, live acceptance, release or deployment.
Guest execution used the operator's console/session. Guest results, private-file creation and audit summaries below are operator-reported outputs of the supplied commands; the author did not log into the guest or read its private receipt/log inventory directly.
Production/Dev health and identity observations were obtained by the author through the existing connectors, without task submission. These are parent observations, not raw transport captures.

## 2. Exact inputs

| Input | Identity |
| --- | --- |
| Candidate | `02d7e8bb1e1902ca33a574ab904a6e5b0f441785` |
| Candidate tree | `e0a905fb5ec02b91c1a8e8c58351c316e94eadbd` |
| Reviewed artifact | PR #91 head `e7be0cc4e84b820eb8c7ac541325672d0f892fb2` |
| Artifact merge | `39384c68d35eddf86c76c9394accb9723cf5d244` |
| Guest interpreter | Python 3.14.4 |

The 104-file manifest matches the selected candidate. Relative to original `71dcae67...`, only the reviewed #89/#92 test cleanups differ; the other 102 blobs and modes remain unchanged. Runtime, assertions, dependencies, stamp, schema, synthetic matrix and warning patterns were not changed for guest execution.
The operator reported artifact SHA-256 checks OK, candidate content_verified true and pip check success. The final audit rechecked artifact hashes, all 104 candidate blobs, before/after source-verification records and unchanged dependency freeze bytes. Transitive dependency identity and evidence hashes stay in the private receipt.

## 3. Preserved earlier evidence

- Original input: full suite 234 OK, focused 7 OK/exit 0 with two finalizer warnings, artifact 10 OK. The warning trace and repair/review chain remain evidence; no retroactive clean-gate claim.
- Selected two-blob input, first guest measurement: 234/7/10 OK with warning gates; 38 resource samples, guest available minimum 985 MiB, sampled account RSS peak 204.82 MiB, host minimum recorded 2259 MiB, workspace growth maximum 64.25 MiB and elapsed 554 seconds. The operator reported host monitoring without a threshold breach, but no original Production/Dev observations before/during that round. Its private receipt remains PENDING.
- A fresh measurement was then made under the same original deadline after new connector baselines. The old receipt/logs were preserved. No window extension or warning suppression was used.

The failed #91 CI runs/HOLD reviews at earlier heads remain historical evidence. New results do not identify the exact historical SQLite connection object or relabel those failed runs.

## 4. Fresh guest measurement and resource audit

| Check | Operator-reported observed result |
| --- | --- |
| Full suite | 234 tests / 27.455 s / OK / exit 0 |
| Focused section 22 | 7 tests / 0.473 s / OK / exit 0 |
| Artifact checks | 10 tests / 1.535 s / OK / exit 0 |
| Completed-output warning gates | Passed; same ResourceWarning/finalizing-database markers |
| Resource samples | 65 |
| Guest MemAvailable minimum | 980 MiB; threshold at least 768 MiB |
| Account RSS maximum sampled | 213.82 MiB; threshold at most 768 MiB |
| Host available minimum recorded | 2111 MiB; threshold at least 1536 MiB |
| Elapsed from original window start to final resource observation | 1604 s; limit 1800 s |
| Additional non-collector processes in final vs initial guest snapshot | 0 |

The resource audit checked every saved sample against memory/RSS, disk free at least 2 GiB, workspace growth at most 2 GiB, evidence at most 128 MiB and the original deadline. The completion report also showed 195 seconds remaining before the subsequent post-test connector observations.
Account RSS includes all sampled processes of the guest account and is used as a conservative bound, not an exact test-process measurement. Sampling does not prove a transient peak was absent.
The operator answered `yes` when asked whether host RAM was watched during this fresh round and stayed above threshold. This is an operator statement, separate from the three recorded host readings.
Zero added processes in snapshots does not prove complete worker cessation or global quiescence.

## 5. Discrete Production/Dev observations

| Surface | Before and after identity |
| --- | --- |
| Production | v1.2.8, source revision `887436f359683f0215f1993d7cb0c9035ec93571`, discovery 27 |
| Dev | v1.2.4, source revision `e7add7e594fb2cc0029dd53b628c85f9a7c1a87c`, discovery 27 |

Both existing connectors returned health ok and authentication verified before and after the fresh measurement.
Author-observed timestamps were `2026-10-23T15:04:25.618Z` before and `2026-10-23T15:10:26.947Z` after. These are observation timestamps, not approval timestamps or clock-synchronization proof.
The identity values matched. These discrete observations do not establish continuous process/start-identity continuity or absence of interference between observations; no mid-run connector observation is claimed.

## 6. Private receipt and disposition

The operator reported completion of the audit and creation of a separate private readiness receipt with status `READY_FOR_INDEPENDENT_REVIEW`. The supplied creation command uses O_EXCL and mode 0600; it does not overwrite the earlier pending receipt. No independent guest filesystem stat or raw private-receipt read by the author is claimed.
The receipt contains selected input/artifact identities, dependency/evidence hashes, resource summary, operator host statement, parent connector observations and limitations. Actual paths, accounts, endpoint bindings, process inventories and private receipt hashes are not published here.

This record is ready for independent evidence review; it does not itself accept Phase A or close the scoped section 22 synthetic acceptance gate.
Phase B remains HOLD: no new route/connector/credentials, live fixture activation or stimulus was performed. Reviewed live adapter/control implementation, completed private B bindings and separate scoped approval remain required.
PR #80 remains a separate held historical record. No historical disposition, real-backend/native/production/full-quiescence/host-isolation/continuous-no-interference or exactly-once claim is made. Release/signing/publication/deployment remain separate.
