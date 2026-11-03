# Protected transfer offline primitives — source candidate

Date: 3 November 2026. Input #112 `336d185718085d922dcab4097229494efe773aa3`.
Operator-supplied round-27 review accepted the transfer design; “ทำขั้นถัดไป”
requests this offline source/control candidate. Exact timestamp NOT_PROVIDED.
**SYNTHETIC OFFLINE PROFILE ONLY. No source/action readiness for a real transfer.**

## Implemented and deliberately unimplemented boundaries

transfer_offline.py implements bounded canonical lock/descriptor/context validation,
a fixed three-role binary envelope, a one-use in-memory quarantine/HOLD latch,
and complete retained-REGULAR payload/index/manifest verification over real
synthetic tar bytes. No filesystem member extraction, path lookup, subprocess,
network, key/credential, age, OIDC, secret or native Windows/WSL operation exists.

The API uses explicitly named fixture ciphertext/plaintext/EOF methods. Ciphertext
bytes are opaque fixture data: only size/digest is checked. No bool or caller field
can assert authenticated provenance or age EOF. The sole success state is
OFFLINE_VERIFIED_NOT_AUTHORIZED; crypto/provenance/import/scope/J0/R1/R2 flags
remain false. No plaintext or import token is returned. The in-memory state is
not an ACL/security boundary against a caller in the same Python process; clearing
buffers is not secure erasure. Native disk quarantine/atomic publication/TOCTOU/
custody/provenance verification remain unimplemented and blocked.

## Closed fixture schema and limits

Lock/descriptor/envelope/manifest kinds have distinct j0-offline-fixture-* names;
they do not accept production prepared-artifact or encrypted-transfer classes.
Exact key sets, canonical ASCII JSON, duplicate/float/nonfinite/depth/type/schema/
context/generation/expiry and false-action checks are enforced. Workflow identity
is the compiled synthetic fixture/builder.yml; fixture_now is supplied fixture
evidence, not a trusted production clock/approval source.

Envelope: J0XFER1 plus NUL; four-byte big-endian header length; canonical bounded
header; exact ordered rootfs_tar/private_index/manifest role streams and hashes.
No trailing bytes, role substitution, second admission or recovered success after
HOLD. Fixture caps: 8 MiB total, 16 KiB header/record, 1 MiB index+manifest,
128 entries, depth 16. These intentional test-profile bounds do NOT implement or
claim feasibility of the design's 5 GiB/200000-entry transfer.

Prepared tar profile is canonical uncompressed ASCII USTAR with explicit directory
parents, fixed root ownership/time/modes, regular/directory/leaf-symlink entries
only. Device/hardlink/FIFO/sparse/extension/unsupported output rejects; literal
backslash remains a character. Guest-root metadata links are graph-checked with
cycle/escape/depth limits and no parent-link entries or host resolution. Runtime-
unresolved links, broader PAX/Unicode/reserved overlays, package/stdlib/library/
loader closure and Windows importer compatibility are NOT IMPLEMENTED here.
The compiled synthetic executable names python/sshd are fixture predicates, not
real guest binary/version/dependency proof.

Every retained REGULAR is read only as its admitted regular TarInfo and hashed;
the complete ordered index must equal actual metadata/hashes, with complete
manifest counts/byte totals. Rebuilding canonical USTAR detects trailing/unbound
encoding changes. No seven-selected-file shortcut or delegation to native complete
status. This narrower fixture profile cannot become the real rootfs admission policy
without a separate reviewed schema/source decision.

## Controls and validation provenance

test_transfer_offline.py has 26 controls with real synthetic tar, descriptor/
envelope bytes, chopped input and deliberate digest/index/manifest/graph faults.
They cover all retained payloads (including a changed non-selected file with outer
hashes rebound), only-seven index rejection, false authority/context/schema mutations,
strict parser bounds, bad ciphertext/HOLD latch, prefix/trailing/role/EOF faults,
unsupported types reaching their stimulus without link/device reads, required
fixture-file rejection, literal/guest-root links, no host open/extraction and AST
import/action audit. No original test/assertion/selector is changed.

The workspace exec-server was unavailable at task start and a minimal exec check
failed. **Local tests NOT RUN.** Dedicated CI runs only these synthetic controls
on 3.12/3.14 with exact 26/OK/no-skips/post-exit warning gates and prints actual
source SHA256 values. Real CI hashes/results will be recorded after inspection;
no hash or pass is invented in this initial candidate.

## Remaining source/action gates

The [transfer design](J0-PROTECTED-TRANSFER-DESIGN.md) remains the contract for the
full implementation. Tool/binary pins, attestation/issuer/predicate/source-context
proof, custody/recipient and permissions, real envelope/manifest schemas, private
native quarantine/TOCTOU, complete production artifact/graph/binary closure and
external Windows owner/stop/timing/retention bindings remain UNBOUND/unimplemented.
Environment scaffolding/key generation need their own reviewed finite proposals
and action approvals. No source acceptance of the whole transfer or R1 package
follows from this offline fixture candidate.

FIVE consumed archive invocations / FOUR digest matches; E12 UNKNOWN.
All eighteen rows OPEN; #112 draft; J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD.
No real transfer, key/secret/custody generation, build/import, invocation six,
merge, new E counter or release/deployment. Original source/receipts and all
disabled live jobs remain unchanged; workflow adds one synthetic-only test step.
