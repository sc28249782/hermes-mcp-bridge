# E9 — Windows/Linux joined-path design proposal

Date: 30 October 2026. Reviewed-input checkpoint: `7830c3a7` (E8).
Status: **DESIGN FOR REVIEW — NO PROVISIONING / SOURCE ACCEPTANCE / RUN AUTHORITY**.
Continue [the same R1 work package](R1-INTEGRATION.md) and its eighteen-row ledger.
This proposal assigns no invented hashes, installs nothing and changes no runtime.
Any normative conflict requires the existing §14 procedure before use.

## 1. Direction and current facts

The required direction is Windows entry/CIM → Windows OpenSSH **client** → Linux
guest **sshd** → guest wrapper/controller/worker/collect. Windows does not require
an SSH server for this direction. E8's absent Windows sshd.exe is therefore not a
missing production prerequisite and does not justify installing Windows SSHD.

E8 observed Windows client presence, WSL/VMP features Enabled and guest availability
NOT_TESTED. Neither features nor a client binary prove a bootable Linux guest,
kernel/pidfd/procfs support, localhost reachability or an accepted host key.
E4, E6 and E7 remain separate collect, real SSH and Windows-entry/CIM evidence.
Do not combine their clocks/receipts and call that a joined run.

Preferred test topology: a fresh, uniquely named WSL2 distribution on a disposable
GitHub-hosted Windows job, with a foreground guest sshd and exact Windows client.
This is a conditional environment proposal, not a claim WSL2 works on that image.
The WSL engine is host infrastructure, not an owned child; distribution
registration alone establishes no isolation or complete-writer boundary.

## 2. J0 — bind the environment before any import/start

| Required binding | Present disposition |
| --- | --- |
| Windows image, WSL binary/kernel versions, boot/virtualization support | UNVERIFIED beyond E8; review bounded CI-only capability methods first |
| Existing running distributions and original activity | UNKNOWN; no reuse/default selection; ambiguous coexistence means HOLD |
| Fixture rootfs source/provenance/content manifest/archive SHA | UNBOUND; no floating image/tag or placeholder allowed at execution |
| Python/sshd/client binaries, hashes/versions and supported interpreter matrix | UNBOUND for this joined environment; no inference from E6's Linux client |
| New distro name/install path, source destinations, account/keys/config | UNBOUND; all new and confined to the fixture; no operator values in public code |
| Guest loopback endpoint and Windows localhost reachability | NOMINATION ONLY until actual bind/one-attempt evidence; no alternate port on failure |
| Exact setup/launch/read/write/stop commands and outer owner | UNBOUND; required in source before setup, with no retry/respawn |
| Resource limits and cleanup/evidence ownership | Existing floors/caps retained; VM/WSL attribution and enforcement method need review |

Rootfs preparation must produce a reviewed immutable artifact and manifest from
pinned inputs before Windows imports it. Any package/build steps belong inside
that new fixture image, not the operator host or existing distributions. Exact
source/asset hashes must be computed, not nominated as if already verified.
J0 is not ready while any row is UNKNOWN/UNBOUND.

No automatic WSL install/update, kernel download, optional-feature enablement,
reboot, default distro/version change, global .wslconfig, firewall or portproxy
edit is included. A missing prerequisite ends at ENVIRONMENT_UNAVAILABLE/HOLD.
An alternative dedicated test lab requires its own reviewed source/control scope;
it is not a silent fallback to the operator's VM, original bridge or namespace.

## 3. J1 — one joined fixture lane, distinct from operational R1

| Actor | Proposed behavior and evidence boundary |
| --- | --- |
| Windows outer fixture owner | New CI driver; exact instance/deadline, inventory of owned actors, private records and explicit distro lifecycle authority; no claim a job timeout proves operational cessation |
| Windows entry/coordinator | Exact checked candidate sources and original ACL/config writer; E7 default-owner precondition confined to the new fixture driver; actual native Windows ssh.exe, no compiled transport replacement |
| Windows sampler child | Actual pinned CIM readings; query must start after sample-window frame for during; existing child/query budgets retained unless separately reviewed |
| Guest sshd/auth peer | Foreground server inside ONLY the new distro, new account/keys, strict known_hosts, no PAM/password/root login/forwarding/TTY/UserRC; exact forced command and argv, one connection per named case |
| Guest wrapper | Checked existing run/state-machine/pidfd/pre-drain/post logic; emit only false scope flags and pending-review or HOLD frames |
| Fixture controller/worker | Explicit fixture-only source binding; real ownership/admission/pipe/markers and unchanged observed collect body using declared synthetic inputs/readers, as in E4 |

The fixture controller is not the production `13d8c0ca…` controller. If the test
entry substitutes the controller source binding, it must be a separately named
test entry, exact-hash-bound fixture controller and an explicit reported
substitution. It may not alter identity/liveness checks, worker-marker boundaries,
window predicates, production files or timers, or be staged as an operational
guest entry. Reusing the original Target code does not turn a fixture controller
into production controller evidence. All inputs/receipts remain fixture-labeled.

The collect body requires a VMware product-name observation. A WSL guest must not
be described as VMware or as satisfying that operational predicate. J1 may use
the already disclosed synthetic input/system-reader lane; it must report that
substitution and keep all authentication/host/scope/coverage flags false. No
sysfs spoofing, original prepared input rewrite or relaxed production predicate.
Kernel PID/pidfd/identity and the Windows CIM query/carrier must be real.

J1 target evidence is the SAME invocation: real collect entered → actual Windows
CIM query begins/ends → post request → real wrapper confirms → collect leaving,
with a retained real worker identity and exact correlation/frame/log sequence.
A fabricated resource number, C# transport, Linux-only sample, before-query result
cache or receipts from different runs cannot satisfy this predicate.

## 4. Timing decision before changing the sampler actor

Current HostCoordinator starts a fresh PowerShell sample child for each phase.
It enforces a 3 s child budget and ≤1 s reported query, but those upper bounds do
not establish that cold startup plus query fits a natural collect invocation.
There is no joined Windows/collect latency result yet. Do not assert impossibility
or feasibility from E4/E7 durations or unrelated clocks.

The first unchanged-path case must record causal order and local elapsed budgets
once, without retry/resample. A natural fast-collect HOLD is honest failure of
the positive join target, not a completed joined PASS. Negative cases must reach
their declared stimulus, as in E4, or remain unproved.

If measured timing requires a warm sampler, propose an explicit actor-contract
delta before implementation: a single owned sampler may start before worker
launch, but each during query must be fresh and start only after the window frame.
No cached query counts. Bind its phase protocol, one-use/order/EOF handling,
process lifetime, source/hash/argv, deadline and stop confirmation. A lifetime
change from one short child per phase to a persistent child is not automatically
covered by the old approval. Preserve the absolute host/guest/controller/worker
budgets; do not widen a timer, add worker ACK wait, sleep/SIGSTOP or inflate an
inventory input beyond its reviewed fixture purpose to manufacture a PASS.

## 5. Joined failure matrix and source-review exit

| Required result | Acceptance evidence, never an automatic row closure |
| --- | --- |
| Positive J1 | One causally bracketed real collect + actual Windows CIM + native Windows SSH/guest wrapper exchange; exact sequence and honest fixture substitutions |
| Before-entry/after-leaving/worker exit | Reject through the same carrier; no successful post/after result after HOLD; actual negative stimulus required |
| Corrupt/duplicate/mismatched/oversize/flood/partial EOF | Bounded framing/queues/logs; no reconnect, second worker, resample or recovered success |
| Provider/output/log/start/deadline/owner loss | Source-reviewed fault injection reaches the intended boundary; no next stimulus; partial evidence preserved; unknown stop remains unknown |
| Host trust/source/ACL drift/existing evidence | Refuse before active work; no host-key acceptance, chmod/ACL repair, stale-claim removal or alternate path |
| End/stop | Exact owned identities, exits/reap/EOF and private writer inventory; distinguish fixture cleanup from operational coverage |

Every test reports source/input hashes, interpreter/image/method attribution,
actor counts, elapsed local budgets and frame sequence. A failed environment or
positive window stays failed evidence. Existing 69 controls, E3/E5/E7 Windows,
E6 carrier and E8 identity suites remain mandatory; test count is not acceptance.

Do not implement the full matrix as more independent substitute-path PRs.
Continue implementation and evidence on #112 only after the route/actor design
and exact setup source are independently reviewed. The ledger requires explicit
disposition for all eighteen rows against A1–A5; no obligation becomes optional
because a test environment is unavailable.

## 6. Stop authority and cleanup limits

Before creating a distribution, bind a unique name/path/creation receipt and
an owner outside guest/SSH failure paths. Address only that name on every command;
never invoke default-distro operations or global WSL shutdown. A named terminate
is limited to the new fixture distro. Destructive unregister is a separate cleanup
action requiring its exact creation binding, stopped-state evidence and preserved
receipt; no deletion of existing names/paths or evidence to get another attempt.

Native WSL processes, its host engine and CIM service are not automatically in a
test-owned process tree. Neither killing ssh.exe/PowerShell nor closing pipes
proves guest/provider or external-writer cessation. The independent supervisor,
owner-loss path and stop/confirmation mechanism are still UNBOUND, requiring
their own source and controls. Job teardown may contain a disposable CI failure
but cannot be reported as operational R1 stop proof. No generic Kill(tree),
service termination, existing-distro stop or original-runtime signal is proposed.

## 7. J2 and requested design disposition

J1 is fixture-based source evidence only. Operational R1 would require the actual
production controller/helper/source bindings, original guest/Windows observations
and A6/A7 private review plus a separate finite operator approval. It must exclude
fixture entry/controller/readers and invalid credential placeholders. J1 receipts,
SSH authentication and correlation digests are not R1/R2 approval tokens.

Review this proposal's direction, conditional WSL2 environment, declared fixture
controller/reader substitution, timing decision, failure matrix and unbound stop
authority before implementing setup. No CI guest/rootfs import/start, install,
sampler redesign, source-acceptance PASS or operator action occurs in E9.
R1 NOT AUTHORIZED; R2 HOLD; #80/#96/release/deployment remain unchanged.

References: [WSL commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)
distinguish targeted termination, global shutdown and destructive unregister;
[WSL networking](https://learn.microsoft.com/en-us/windows/wsl/networking) documents
the Windows-to-Linux localhost path, not its availability on this CI image.
