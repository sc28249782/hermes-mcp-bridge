# Phase B source increment 1: offline parent contract

Status: **SOURCE FOR REVIEW — offline only; B implementation incomplete**.
Design: [adapter/control plan](../../docs/S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md).
Phase A operator acceptance is recorded in [PR #96](https://github.com/sc28249782/hermes-mcp-bridge/pull/96), a separate unmerged draft when this increment was prepared. That statement accepts preparation readiness only. This source does not depend on that draft's document changes and does not merge it.

## Scope and fixed inputs

`parent_contract.py` reuses the existing fixture matrix and stopped-state verifier without modifying either. The candidate remains `02d7e8bb1e1902ca33a574ab904a6e5b0f441785`; fixture behavioral input remains PR #91 head `e7be0cc4e84b820eb8c7ac541325672d0f892fb2`. No candidate, manifest, fixture hooks, assertions, stamp, runtime or dependency changes are included.
The new module has no CLI, live mode, connector API, credential reader, network client, process launcher or signal operation. Its injected async exchange accepts one bytes frame and returns one bytes frame. The tests supply fabricated observations and an in-process synthetic fixture; neither is a host/guest observer or route capability proof.
Successful results are always labeled `offline-ipc-contract`, including the nested matrix result. No output is an approval token, readiness receipt or live acceptance result.

## Frame and runner contract

Each frame is one UTF-8 JSON object followed by one newline. Envelope keys are exactly `seq`, `route`, `kind` and `payload`. The fixed namespace is `offline-fixture-contract`; it cannot select Production, Dev or a new operational connector. Sequence numbers start at 1 and must match the reply exactly. Only one request may be outstanding.
Tool payloads contain `name` and `arguments`; checkpoint payloads contain `stage`. Replies echo the envelope and carry the complete result or observation as payload. Duplicate JSON keys, nonfinite numbers, extra envelope keys, invalid UTF-8, multiple frames and bad sequence/namespace/kind are rejected.
The tool allowlist contains only the six matrix tools. Identity/discovery calls are deliberately absent from this source increment. Arguments are restricted to the current matrix case, fixture prompt/workspace/mode/request identity and contexts returned by this instance. The immutable matrix still checks full rows, backend counters, constant notes, nested ACK digests and the named known-ID replay. The contract adds no resubmission behavior.
Decoded result fields, including nested ACK, content, metadata and extra fields, are preserved. The runner does not strip errors or replace lost replies with synthetic success.

| Proposed contract bound | Value / failure behavior |
| --- | --- |
| Single encoded request/reply | At most 65,536 bytes including final newline |
| Combined request/reply trace | At most 8 MiB, within the existing 128 MiB evidence ceiling |
| Awaited reply | At most 5 seconds, further bounded by the remaining window |
| Observation age before dispatch and after reply | At most 2 seconds in the same test monotonic clock domain |
| Whole contract | At most 1,200 seconds; no deadline reset or second run |

These values are source-review proposals, not approved B activation values. The timeout uses cooperative asyncio cancellation. An uncooperative exchange or blocked event loop is not forcibly terminated by this library; an independent supervisor is still required. No kernel enforcement, cross-machine clock synchronization or process cessation is claimed.
On error, timeout, cancellation, concurrency, stale observation or uncertain acceptance, the instance latches HOLD and permits no further exchange. Partial trace bytes remain in memory. There is no retry, reconnect, persistence, receipt creation or automatic stop action. Any later trace persistence needs its own private-file/budget implementation and review.

## Checkpoint test-data validation

The module enforces the fixture's 44 ordered checkpoint stages. An observation must include the exact stage, a fresh increasing local monotonic time, fixed candidate/artifact/cohort/Production/Dev identity strings, all six numeric resource fields and the complete prebound writer list. A Boolean callback result is rejected.
Resource checks retain host available >=1,536 MiB, guest available >=768 MiB, observed RSS <=768 MiB, disk free >=2,048 MiB, workspace growth <=2,048 MiB and logs <=128 MiB. Boolean, negative, nonfinite, missing or nonnumeric measurements fail closed.
These checks validate supplied data only. Identity strings and expected/observed writer equality do not authenticate a collector, prove PID/start identity, discover detached writers, establish global quiescence or prove absence of interference. Host/guest sampling, source hashes, process inventories and continuity observations must come from separately reviewed collectors and private bindings. Fabricated internally consistent test data is not operational evidence.

## Offline validation

Run in a separate development checkout with the selected candidate and its dependencies:

```bash
python -W error::ResourceWarning -B acceptance/s24/test_parent_contract.py --candidate "$CANDIDATE" -v
```

Inspect completed combined output through interpreter shutdown with the unchanged warning markers, as in the dedicated CI workflow. The new 16-test inventory is separate from the historical 234/7/10 inventories. CI retains the pinned full suite, focused section 22 tests and ten artifact checks on Python 3.12/3.14, then runs these new controls under the same warning gate.
The successful full-matrix control uses real candidate code in process, patches native spawn/real HTTP to fail, closes its client and applies the existing read-only stopped-state comparison. It is not SDK stdio, a tunnel run or evidence about guest processes. The original ten artifact checks retain their separate SDK stdio coverage.

## Remaining B source and authority gates

This is the first source increment, not a complete B adapter/control implementation. The following are still absent: supported real parent-to-new-connector invocation proof; actual identity/discovery adapter; host/guest collectors and observation provenance; finite independent guest supervisor; exact executable/owner/PID/start-identity stop targeting; duplicate client/fixture launch prevention; durable bounded private trace/receipt persistence; and operational stopped-writer proof before verification.
Those components require further source review and offline validation. The current data contract may need a separately reviewed revision once the supported connector/observer interfaces are known. No live fallback is supplied.
No new guest execution, installation, authentication, profile/connector setup, refresh or activation is authorized or performed. Any action that could spawn a fixture requires the separate finite B approval first. The previous Phase A window is historical. The scoped section 22 gate and PR #80 remain HOLD; release/signing/publication/deployment remain separate.
