# Observed inventory source — draft CI validation

Status: **SOURCE CANDIDATE / NO OPERATOR EXECUTION SCOPE / R1 INCOMPLETE / R2 HOLD**.

The original inventory controller/helper remain unchanged. These separately named
variants add an entry/leaving marker inside `collect`, a bounded observation pipe,
an irreversible HOLD state and a guest/Windows causal sampling protocol. Private
operational configuration and execution packets are deliberately absent.

The helper retains the original collect body as `_collect_body`; the test compares
its AST with the immutable public baseline fixture. Entry/leaving write failure
is fatal exit72. The worker never waits for a host ACK or sleeps to manufacture a
sampling window. Fast completion can produce HOLD without a retry.

The guest wrapper owns only its direct controller and observes the bound worker
through a read-only retained pidfd. Linux termination authority stays with validated
owned targets. Windows own-child stop, source/config/output ACL policy and exact
private invocation/transport bindings still require review before operator use.
Correlation data is not approval or authentication. All scope flags stay false.

This directory initially preserves the reviewed candidate's runtime and test
bytes. The new CI wrapper runs all34 tests with no skip, predicate relaxation or
numeric-PID fallback. Source-fixture creation declares umask022; source modes are
checked normally. Full post-exit output is inspected for warnings even on failure.
Windows jobs parse the sources and run14 offline plus9 disposable-process checks;
they do not launch SSH, query CIM or access an operator preparation directory.

The author container's earlier suite had33passes/1procfs-coherence error. An
independent review reported34/34 on coherent Linux. Neither result fills the
remaining real-integration rows of [CONTROL-MATRIX.md](CONTROL-MATRIX.md).
CI results must be read from the exact PR head; this document claims no new pass.

`HostMemory.psm1` and `baseline/prebind_inventory.py` are unchanged public fixtures,
not operator evidence. The two-file source transfer writer does not install this
new source set. New staging methods and complete private bindings still precede
any separately approved finite operator run. No merge, R2, release or deployment
is authorized by this draft source or a green CI result.
