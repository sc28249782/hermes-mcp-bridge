# J0 protected transfer — tool, provenance and custody binding packet

Date: 3 November 2026 (Asia/Bangkok). Input draft #112
`2a78269352a22475a192cef72b157fceec8df30e`.
**BINDING INVENTORY / REVIEW CANDIDATE. REAL TRANSFER NOT SOURCE- OR ACTION-READY.**

The operator-supplied round-28 review approves the offline fixture source at that
head and reports reviewer-local 26/26 OK (umask 022, ResourceWarning as error).
This is reviewer-reported local evidence, separate from author GitHub CI; it does
not retroactively give the author a local run. Exact review timestamp NOT_PROVIDED.
The subsequent operator request “ทำขั้นถัดไป” authorizes preparing this packet,
not any key, secret, permission, tool installation or transfer action.

## 1. Authority and evidence boundary

Applicable contracts are the [protected-transfer design](J0-PROTECTED-TRANSFER-DESIGN.md),
[consumer admission design B](J0-PREPARED-ARTIFACT-ADMISSION-DESIGN.md) and
[offline fixture source scope](TRANSFER-OFFLINE-SOURCE-REVIEW.md).
This packet maps their requirements; it neither changes those policies nor selects
tool releases, invents hashes, asserts installed capabilities or defines a new
production schema. No external capability discovery or new upstream-version
verification is claimed. Candidate mechanisms below come from the accepted design.

PRESENT means inspectable component evidence, not acceptance of a production
binding. UNBOUND blocks the dependent action. A version string, unsigned descriptor,
repository access or CI success cannot fill a signed identity/custody requirement.
Private evidence uses a reviewed alias/commitment in public records, never key
material, private paths, private recipient values or unrestricted raw diagnostics.

| Existing evidence | Disposition / what it does not establish |
|---|---|
| Protected-transfer design at 336d1857 | Operator-supplied design APPROVE; execution bindings remain UNBOUND |
| Fixture source at 2a782693 | Operator-supplied exact-source APPROVE; synthetic profile only, not whole transfer/R1 acceptance |
| Reviewer-local 26/26 | Reviewer-reported reproduction; not an author-local or actual transfer run |
| Author CI 41571797010 | Synthetic 26/26 on 3.12/3.14 plus prior suites; no crypto/provenance authentication |
| V2 catalog attempt five | Input metadata evidence only; ephemeral archive is unavailable, not a retained prepared artifact |
| Native quarantine / signed verifier / custody / owner | No accepted implementation or actual-route receipt |

## 2. Required binding register

All real execution fields in this register remain **UNBOUND**. Proposed families
are not executable argv or permission grants. A subsequent exact-source packet
must supply actual values and their verification evidence, without placeholders.

| ID | Required exact binding and evidence | Gate blocked until accepted |
|---|---|---|
| T1 | Linux and Windows age source revision/release, distribution-object digest and authenticity chain, actual binary SHA256/platform, fixed native X25519-only profile, noninteractive argv and bounded output/stop behavior | Tool execution / encryption / decryption |
| T2 | Attestor and verifier source/action revision and dependency pins, actual binary identities, trusted roots/issuer/predicate versions, bounded offline/online verification behavior and network policy | Attestation publication or verification |
| P1 | Repository numeric identity plus canonical identity, approved builder/receiver workflow identity and source revision, event/ref/fork policy, reviewed checkout-to-source binding | Publish / secret release |
| P2 | Exact signed-claim mapping for both descriptor and ciphertext subject digests, signer workflow/revision, actual source commit, run and attempt; generation/lock binding through authenticated descriptor | Publisher admission / decrypt |
| P3 | Exact job-scoped OIDC/attestation/artifact permissions, token audiences and access boundaries for the pinned versions; accepted least-scope workflow source | Permission change / dispatch |
| C1 | Named custodian authority via private alias, independent one-generation receiver identity creation source, public-recipient/fingerprint verification, creation/expiry/retirement and audit procedure | Identity generation / lock sealing |
| C2 | Access-controlled custody environment, approved receiver source/ref and release controls, exact secret scope and permitted principal, no builder/fork/unreviewed-code access | Secret provisioning / private identity release |
| C3 | Native private identity file/handle owner/ACL/no-reparse guarantees, bounded lifetime, noninteractive child access, failure cleanup and residual-access disclosure | Key-bearing receiver execution |
| S1 | Closed production lock/descriptor/envelope/manifest schemas, canonicalization and cross-binding rules, exact limits and domain separation from fixture/strict/catalog evidence | Real object admission |
| N1 | Exact artifact service object inventory and retrieval method, redirect/retry behavior, byte caps, trusted expiry source, retention support and access audit | Upload / download |
| W1 | Native Windows quarantine, exclusive creation, retained-handle TOCTOU protection, publication semantics, workspace ACL/owner and no-repair policy | Plaintext creation / seal / consumer handoff |
| O1 | Outside-owner source, exact child ownership/stop authority and confirmation, deadline/disk accounting, safe cleanup and loss-of-owner behavior | Any real receiver process |
| A1 | Finite generation/action scope, approved input/source/context, one-attempt consumption rule, protected evidence retention and explicit operator approval | Activation |

No tool/version/hash/recipient/secret name or actual workflow run is filled in by
analogy to another lane. A required signed claim missing from the chosen mechanism
is an infeasibility/HOLD result; it cannot be replaced by an unsigned field.
Actual future run/attempt values are obtained from trusted execution context and
authenticated as required after activation, not fabricated before dispatch.
Lock commitments must be non-circular: bind reviewed source/policy/input before
activation; bind actual output hashes only after verified output exists.

## 3. Provenance acceptance matrix to implement and preregister

| Stimulus | Required result before private identity access |
|---|---|
| Correct encryption but no authenticated publisher | HOLD |
| Hash/artifact ID correct but unsigned context or signer mismatch | HOLD |
| Descriptor authenticated, ciphertext not bound (or converse) | HOLD |
| Source/workflow/ref/fork/run/attempt mismatch or unsupported signed claim | HOLD |
| Generation, lock, recipient, expiry or object digest mismatch | HOLD |
| Valid prior generation replay / lost receipt / uncertain execution | HOLD; consumed scope, no retry |
| Complete accepted signed bindings | May proceed only within separately approved scope; never grants import/J0/R1/R2 |

These are future source controls, NOT tests executed by this document. A verifier
must produce an internal typed verification result bound to the exact checked
bytes/context. An external caller dictionary or success boolean cannot manufacture
that result. Negative controls must reach the claimed verifier/custody boundary;
fixtures alone cannot claim real signed provenance or protected secret release.
A cryptographically valid bundle with wrong content still fails the independent
full artifact verifier after authenticated decryption.

## 4. Custody and execution stages with finite exits

| Stage | Reviewable exit required | Action status now |
|---|---|---|
| Binding-source preparation | Exact T/P/C schemas, sources, tool objects/authenticity and permission policy; preregistered negative controls; explicit feasibility/HOLD dispositions | Documentation preparation only |
| Environment/custody scaffolding proposal | Exact access controls and owned changes, private evidence channel, audit/retirement/rollback limits, finite scope | NOT PROPOSED / NOT AUTHORIZED |
| One custodian generation proposal | Accepted generation source/environment, independent public binding, exact lifetime and disposal authority | NOT PROPOSED / NOT AUTHORIZED |
| Locked build/encrypt/publish proposal | Accepted builder/package/binary closure, sealed actual input/tool/source/recipient lock, resource bounds, provenance and artifact output gates | NOT PROPOSED / NOT AUTHORIZED |
| Receiver/private-seal proposal | Accepted signed claim mapping, custody access, Windows owner/quarantine/stop source and exact object identities, feasibility evidence | NOT PROPOSED / NOT AUTHORIZED |
| Optional consumer/import proposal | Accepted prepared artifact/manifest and TOCTOU-safe native consumer bindings, actual kernel/boot prerequisites and separate finite approval | NOT PROPOSED / NOT AUTHORIZED |

Source acceptance is separate from every action approval. Environment scaffolding
does not authorize generation; generation does not authorize build/transfer;
private seal does not authorize import. First-build output hashes are outcomes,
not circular preconditions to building. A missing prerequisite ends HOLD or an
explicit route/defer decision, without automatic tool installation, secret creation,
new policy variant, permission broadening, alternate object or additional attempt.

The accepted budgets remain unchanged: Windows transfer <=90 s inside owner
<=240 s and job <=6 min; builder <=10 min and owned writes <=12 GiB. Identity
custody <=24 h, acceptance expiry <=30 min and requested ciphertext retention
<=1 day remain design limits whose enforceability is UNBOUND, not demonstrated
service guarantees. No timer reset, resource widening or feasibility pass here.

## 5. Closure target and next source boundary

This packet exits with independent review of the register and stage separation,
not a claim that those bindings are complete. The next bounded source target is
T1/T2/P1/P2: an exact tool-authenticity and signed-claim verification contract with
negative controls and a feasibility disposition for every required claim.
C1-C3 must have a separately reviewable custody proposal before any generation.
No key-bearing job or real transfer wrapper is prepared by this document.
If the chosen tools/claims/custody cannot satisfy the design, report the specific
UNBOUND/infeasible field and return to route-or-defer; do not grow fixture controls
to imply that a production prerequisite was met.

No existing source/test/workflow/pin/guard or actual-attempt record changes.
All eighteen ledger rows remain OPEN. FIVE archive invocations consumed / FOUR
digest matches; E12 UNKNOWN. No invocation six, key/secret/custody action,
crypto/provenance execution, transfer, build/import, merge or release/deployment.
#112 stays draft; J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD.
#80/#96 and private A6/A7 remain unchanged. SPEC section 14 applies before
implementation merge if a normative/security/approval boundary changes.
