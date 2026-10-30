# Observed inventory source — draft CI validation

Status: **SOURCE CANDIDATE / NO OPERATOR EXECUTION SCOPE / R1 INCOMPLETE / R2 HOLD**.

The original inventory controller/helper remain unchanged. These separately named
variants add an entry/leaving marker inside `collect`, a bounded observation pipe,
an irreversible HOLD state and a guest/Windows causal sampling protocol. Private
operational configuration and execution packets are deliberately absent.

The helper retains the original collect body as `_collect_body`; the test compares
its AST with the immutable public baseline fixture. Entry/leaving write failure
is fatal exit 72. The worker never waits for a host ACK or sleeps to manufacture a
sampling window. Fast completion can produce HOLD without a retry.

The guest wrapper owns only its direct controller and observes the bound worker
through a read-only retained pidfd. Linux termination authority stays with validated
owned targets. Windows own-child stop, source/config/output ACL policy and exact
private invocation/transport bindings still require review before operator use.
Correlation data is not approval or authentication. All scope flags stay false.

This directory initially preserves the reviewed candidate's runtime and test
bytes. The new CI wrapper runs all 69 tests with no skip, predicate relaxation or
numeric-PID fallback. The CI step sets umask 022 before running this suite.
Source modes are checked fail-closed by the loaders (group/other-writable sources
are rejected). Full post-exit output is inspected for warnings even on failure.
Windows jobs parse the sources and run 14 offline plus 9 disposable-process checks;
they do not launch SSH, query CIM or access an operator preparation directory.

The author container's earlier suite had 33 passes / 1 procfs-coherence error. An
independent review reported 34/34 on coherent Linux. Neither result fills the
remaining real-integration rows of [CONTROL-MATRIX.md](CONTROL-MATRIX.md).
CI results must be read from the exact PR head; this document claims no new pass.

`HostMemory.psm1` and `baseline/prebind_inventory.py` are unchanged public fixtures,
not operator evidence. The two-file source transfer writer does not install this
new source set. New staging methods and complete private bindings still precede
any separately approved finite operator run. No merge, R2, release or deployment
is authorized by this draft source or a green CI result.

Three wrapper-loop negative controls use real subprocess pipes with fixture controller/identity admission: atomically buffered leaving, malformed JSON and partial-marker EOF. Each requires a single HOLD, no sample-window frame, no retry and a reaped direct child. They do not exercise the inventory body, real worker adoption, Windows transport or successful host sampling.

Three identity controls additionally require real coherent-procfs child admission and a retained pidfd. One verifies exit rejection without a numeric-PID identity read; two inject changed UID/argv reads while the admitted child remains alive. They do not perform an actual UID transition, exec or PID reuse, and do not exercise wrapper HOLD latching or Windows transport.

Three local host-handshake controls drive the unchanged wrapper through real stdin/stdout and observation pipes: successful post-check/final receipt, wrong challenge and duplicate post-check. Only the synthetic controller fixture waits on a test release pipe; no production worker is paused or modified. Controller loading and identity admission are fixtures. No memory sample, SSH or Windows host is involved, so these are local protocol integration evidence only.

The continuing [R1 integration work package](R1-INTEGRATION.md) maps all eighteen design groups to evidence and blocking obligations. It reuses 22 unchanged baseline helper controls against the observed helper, adds a real controller/worker/collect failure-path control, and separates ten Windows CI ACL/CIM checks from offline checks. These additions do not complete source acceptance or prove a host sample during actual inventory.

The joined E4 fixture adds real collect boundaries, real pidfd admission and a framed local Linux memory sample. Its coordinator and inventory inputs remain test fixtures; natural fast-collect HOLD is reported, not retried. Negative cases must actually reach sampling before testing worker exit or leaving-before-post. This is not the production Windows/SSH carrier.

E5 changes the production host PowerShell coordinator/support and their pins; earlier unchanged-source statements are historical. The checked HostCoordinator function is shared with a separate 16-case Windows process-fixture failure matrix. Bootstrap/config ACL admission and real SSH/CIM are outside that matrix; operational carrier/deadline/stop obligations remain open. See the E5 section in the integration ledger for exact runtime hashes and cleanup semantics.

E6 exercises the existing coordinator through real OpenSSH on a disposable Linux CI loopback server with fresh fixture account/keys. Peer/sample and config-writing remain fixtures; no operator SSH/VM/account action or complete Windows/CIM/collect join is claimed. See the ledger for actors, teardown and remaining gates.
