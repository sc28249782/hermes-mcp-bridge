# SPEC §24 — single-use launch admission

Date: 24 October 2026.
Status: **SOURCE FOR REVIEW — offline component, no operational launch authority**.
Parent: [Phase B control design](../../docs/S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md).

`launch_admission.py` reserves one fixed `launch-claim.json` in an existing,
canonical, same-owner 0700 attempt directory. Exclusive creation arbitrates
competing processes. The 0600 file and its parent directory are fsynced before
the object can dispatch a callback. A partial write or failed sync leaves the
claim in place. No overwrite, deletion, stale-lock recovery or automatic retry
is provided. An existing claim blocks even if the identifier, digest or window
changes. A process crash does not authorize a new attempt.

The claim binds the caller-supplied attempt identifier, exact candidate/fixture
commits, private-binding SHA-256, argv and proposed window (at most 1,200 seconds).
These are data, not source verification, authenticated approval or an acceptance
receipt. Actual bindings and argv stay private. Public tests use fabricated
identifiers and disposable helper processes, never original Production/Dev.

`dispatch_once(callback)` consumes the object before any recheck or callback.
It rechecks the directory inode, claim inode/bytes/owner/mode/link count and local
monotonic deadline, then calls the injected callback with a copy of bound argv.
Callback errors propagate without retry; its return value is preserved. No
successful callback, return value or reserved claim establishes a running or
stopped fixture, approval, complete writer coverage or a completed B attempt.
Concurrent calls, copying, pickling and dispatch from a fork-inherited object
are rejected. No subprocess, signal, network, credential, CLI or state repair
is implemented in this module. It writes only the new local claim.

The future approved launcher must route every start through the same bound
attempt directory. Choosing another directory or removing a claim bypasses this
cooperative control and requires a new reviewed scope; it is not recovery.
The shared host, filesystem and same-user caller remain trusted. Metadata/byte
rechecks are discrete, not atomic containment against an active trusted writer.
Filesystem durability depends on the storage stack honoring fsync. The module
does not supply a global host lock, approval store, reconnect detector or cohort
supervisor. It cannot interrupt blocked I/O, a blocked callback or delayed spawn.
The clock check is admission-only; independent lease/window enforcement, process
ownership, cleanup and stopped-writer proof remain required. No callback is
automatically connected to `OwnedChild` or the fixture.

Offline controls: 13 tests cover exact argv, both sync barriers before dispatch,
cross-process arbitration, concurrent calls, crash persistence, partial/short
writes, sync failures, expiry, callback uncertainty, changed paths/files/modes/
links, bounds, copy/pickle and fork ownership. Run:

```bash
python -W error::ResourceWarning -B acceptance/s24/test_launch_admission.py -v
```

Dedicated CI adds these controls under the unchanged post-exit warning scanner.
They are not a VM measurement or route proof. Candidate `02d7e8bb`, behavioral
fixture `e7be0cc4`, manifests and earlier source increments remain unchanged.
The #100 intermittent adoption rejection remains open and is not diagnosed here.
Private bindings, supported parent invocation/handoff, host/continuity observers,
authenticated freshness, outer/cohort supervision, RPC policy, durable attempt
receipts and stopped-writer proof remain prerequisites to B. No guest setup,
activation, scoped §22 gate closure, release or deployment is authorized.
PR #80 remains HOLD; the Phase A acceptance record #96 remains a separate PR.
