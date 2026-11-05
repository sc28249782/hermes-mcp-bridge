# SPEC §24 — read-only Windows host memory sampler

Date: 24 October 2026.
Status: **SOURCE FOR REVIEW — not an authenticated collector or checkpoint PASS**.
Parent: [Phase B control design](../../docs/S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md).

`HostMemory.psm1` provides one synchronous sample on local Windows PowerShell 7.
It reads only `Win32_OperatingSystem.FreePhysicalMemory` and
`TotalVisibleMemorySize` through module-qualified `Get-CimInstance`. It specifies
no remote computer, CIM session, credentials or object method. No process,
service, profile, connector, VM, file or permission is changed. Importing the
module defines functions; it does not query the host. There is no CLI, loop,
retry, cache, network transport or persistence.

The caller supplies a 64-character lowercase SHA-256 binding digest and a
64-character lowercase hexadecimal challenge. These values are echoed for
later correlation, not authenticated or accepted as approval. The function
does not prove that the machine queried is the operator's bound Windows host.
The default evidence label describes the local read; injected unit readers are
fabricated test data regardless of that label. A separate conversion function
always labels its result `offline-host-memory-conversion`.

Counter types must be uint64/uint32/int64/int32, nonnegative, with positive total,
available <= total and exact byte conversion within signed 64-bit range. Strings,
booleans, floating values, missing data and overflow are rejected. The provider's
kilobyte counters are converted by 1,024 to bytes. Available memory below
1,536 MiB produces a host-only failure list. No memory-only result is a complete
checkpoint PASS. Every sample explicitly reports `full_checkpoint_pass=false`,
`host_identity_proved=false`, `authenticated=false`, `guest_observed=false`,
`original_runtime_continuity_observed=false` and `complete_writer_coverage=false`.

The source proposes a one-second completed-sample cap and CIM operation timeout.
The stopwatch includes query/normalization; UTC start/end values are local
observations. They do not synchronize Windows and guest monotonic clocks or
establish freshness at a remote receiver. A completed slow query is rejected;
neither the cap nor the provider timeout is an independent process watchdog or
guarantee that blocked I/O can be interrupted. A failed read returns no partial
sample and a constant HOLD error, without raw provider details. There is no
stateful HOLD latch here: the future controller must latch any missing/late/
failed observation and block stimulus, rather than calling again as recovery.
Continuous minimum memory, transient peak absence and original-runtime process
continuity cannot be inferred from these discrete readings.

Twelve dependency-free PowerShell controls include one actual local Windows CI
query, strict conversion/boundary/type/overflow cases, correlation rejection
before querying, zero/duplicate/malformed rows, a single sanitized provider
failure with no retry, privacy/scope/JSON shape, slow-query rejection and a
low-memory result. Test reader replacements are confined to that test process.
The CI-host query is not an observation of the operator's host or guest. Existing
Linux candidate and component checks remain under their original warning gates.
No local PowerShell or operator-host passing result is claimed without a run.

Private host identity/method binding, authenticated challenge/freshness handling,
original-runtime continuity collectors and supervisor integration remain open.
Candidate `02d7e8bb`, fixture `e7be0cc4`, manifests and prior source increments
are unchanged. No host/VM setup, guest window, B activation, scoped §22 closure,
historical disposition, release or deployment is authorized. PR #80 remains HOLD;
#96 remains a separate unmerged record. The #100 adoption observation stays open.

Official field/interface references (general API facts, not local capability proof):

- [Win32_OperatingSystem](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-operatingsystem)
- [Get-CimInstance](https://learn.microsoft.com/en-us/powershell/module/cimcmdlets/get-ciminstance?view=powershell-7.6)
