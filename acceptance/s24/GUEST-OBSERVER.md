# Phase B source increment 4: read-only guest resource observations

Status: **SOURCE FOR REVIEW — guest observations only; no full checkpoint PASS**.
Design: [Phase B control plan](../../docs/S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md).
Existing control limits: [owned-child component](OWNED-CHILD.md).

## Scope and provenance

`guest_observer.py` has no launcher, subprocess, signal, network, credential, CLI, approval or persistence interface. It reads kernel counters and metadata under two prebound private roots. It never reads workspace/log file contents and never rewrites permissions, state or process status.
The constructor requires coherent Linux procfs and private owned nonsymlink workspace/log roots; logs must be nested inside the workspace. Root device/inode and initial allocated workspace bytes are recorded. Each sample revalidates root identity/privacy and procfs. Unsupported or incomplete observations permanently hold the instance; there is no automatic retry.
Results use local-read-only-guest-observation. They always set host_observed=false, complete_writer_coverage=false and full_checkpoint_pass=false. No result is an approval, receipt, quiescence finding, authenticated route observation or permission to call another tool. A separate reviewed controller must decide whether to stop stimulus; this sampler cannot stop a process.

## Measurements and limits

| Field | Actual source and limitation |
| --- | --- |
| Guest MemAvailable | Bounded /proc/meminfo read with exact kB units, required fields and range checks; never a Windows-host RAM observation |
| Account RSS | Sum of resident pages for every recognized same-effective-uid process, with PID/start identity and uid checks around each read; membership must match at two enumerations |
| Guest disk available | fstatvfs f_bavail × fragment size for the bound workspace filesystem; not a reservation or quota guarantee |
| Workspace growth | Current allocated st_blocks ×512, including directories, minus the constructor baseline; raw signed delta is retained |
| Log bytes | Logical sizes of ordinary single-link files under the bound logs root, not allocated storage size |
| Metadata/membership digests | Hashes of sampled metadata only; not authentication or proof of source contents |

RSS includes shared pages in each process, so it is a conservative sampled account aggregate, not an isolated workload RSS. Reads occur at different instants. Matching membership does not prove absence of transient processes, external/detached writers or processes under another uid, and cannot prove a missed peak was absent. Disappearance, permission errors or PID/start/uid changes produce HOLD rather than silently omitting a process. Kernel MemAvailable does not establish cgroup headroom; target cgroup limits and quotas require separate binding before B.
Filesystem traversal uses directory descriptors, no-follow opens/stats, owner/device checks and bounded metadata. Symlinks, regular-file hard links, special files and cross-filesystem entries are rejected, not followed or excluded silently. A future tree containing venv symlinks or mounts needs a separately reviewed scope; this component does not approve exceptions.
Tree metadata is a sequential observation, not an atomic snapshot or a defense against a compromised trusted host. Device/inode and before/after checks do not establish continuous containment or writer cessation. No final acceptance snapshot is taken here.
Bounded reads are at most 65,536 bytes; process enumeration is capped at 4,096 entries, filesystem traversal at 10,000 entries and 16 levels. A completed sample taking more than one second is rejected. This is an elapsed-time rejection after reads, not a mechanism to interrupt blocked kernel/filesystem I/O; an independent supervisor remains required.
guest_limit_failures reports only observed guest-side breaches against existing thresholds: guest available >=768 MiB, account RSS <=768 MiB, disk available >=2 GiB, workspace growth <=2 GiB and logs <=128 MiB. Boolean/noninteger/invalid negative counters are rejected; negative raw workspace growth is retained as a measurement. An empty guest-only failure list does not complete a checkpoint or supply host RAM/writer coverage.

## Tests and development evidence

Twelve new checks cover kernel self identity/memory/RSS, parser units/duplicates/types, real private filesystem sizes/growth, symlinks/hardlinks/FIFOs, root replacement/privacy, membership churn/unreadable RSS, all guest threshold boundaries, stale sample rejection and tree/process observation limits. Synthetic proc/account injections are explicit unit data, never claimed as real account measurements. The positive platform control uses the actual CI process identity and kernel counters; it does not certify a whole live guest/account run.
Development Python 3.12.14: eleven unit checks passed; the positive kernel check failed with the confirmed procfs/PID-namespace mismatch (12 total, errors=1, exit 1). This is not a passing baseline. No fallback or platform skip is added. Dedicated Ubuntu CI on Python 3.12/3.14 must validate the full new inventory under the unchanged completed-output warning gate. No whole-account guest measurement, guest readiness, source deployment or full local suite rerun is claimed.
The separate reviewer-reported cold-start adoption rejection from PR #100 remains open reliability evidence. This observer does not diagnose or modify adoption, introduce delays/retries or relax identity checks.

## Remaining integration

Actual host RAM/continuity collectors, authenticated observation transport and freshness binding, parent invocation/handoff, outer supervision, full cohort/writer coverage, duplicate-launch control, RPC policy, durable receipts and stopped-writer proof remain required. The caller must serialize and attribute samples; this module starts no collector job or background monitor.
Candidate/fixture/manifests and #97/#98/#100 sources remain unchanged. No original Production/Dev or historical run is inspected or controlled. No VM/SSH/account action, guest window, setup/activation, gate closure, release or deployment is authorized. Scoped section 22 and PR #80 remain HOLD.
