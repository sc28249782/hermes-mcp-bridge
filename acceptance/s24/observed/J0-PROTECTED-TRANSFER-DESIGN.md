# J0 protected artifact transfer — separate design candidate

Date: 2 November 2026. Input #112
`a123471e68892766bc09ddec456d5361843f5534`.
**DESIGN ONLY / KEY, TOOL, CHANNEL AND EXECUTION BINDINGS UNBOUND.**
The operator-supplied round-26 review APPROVED admission design B and requested
a separate protected-transfer design. Exact request timestamp: NOT_PROVIDED.
This packet creates no source, receiver identity, CI secret, attestation, upload,
download, transfer invocation, WSL action or external owner driver.
[Admission design B](J0-PREPARED-ARTIFACT-ADMISSION-DESIGN.md) remains applicable.

## 1. Chosen separation: encrypted transport plus verified provenance

Propose one encrypted opaque bundle on the CI artifact service. Plaintext rootfs,
full index and manifest stay private to their approved builder/receiver workspaces.
Only ciphertext, a bounded public descriptor and signed provenance may cross the
public artifact channel. Never assume ordinary artifact upload is confidential.

Proposed encryption profile: the standard age v1 binary format with one native
X25519 recipient; no passphrase, SSH identity, plugins, recipient fallback or
custom cryptographic implementation. This is a classical-confidentiality choice,
not a post-quantum claim. Exact supported tool versions/source/binary hashes on
Linux/Windows are UNBOUND; unsupported profile ends HOLD, never auto-upgrade.

age supplies authenticated streaming ciphertext, not proof of our approved builder
or repository. Anybody knowing a public recipient can encrypt to it.
Therefore a separate pinned provenance verifier must authenticate the publisher,
approved source/workflow/context and both descriptor and ciphertext digests before
decrypting or admitting plaintext. A matching SHA, artifact name/ID or unsigned
run/job field alone is insufficient.

Primary references checked 2 November 2026:
[age format](https://c2sp.org/age@v1.1.0),
[upstream age manual](https://github.com/FiloSottile/age/blob/main/doc/age.1.ronn),
[GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations),
[verifier identity/predicate controls](https://cli.github.com/manual/gh_attestation_verify).
These describe mechanisms, not a pinned installed tool or proved CI route here.

## 2. Receiver-key custody and non-circular bootstrap

An independently approved custodian prepares ONE receiver identity per transfer
generation before the build/transfer action. Its public recipient and fingerprint
are bound in the reviewed immutable transfer lock; its private identity is delivered
only to the exact authorized Windows receiver through a separately reviewed,
access-controlled CI secret mechanism. Generation is a separate finite action,
not performed by this packet. No Linux builder or public artifact gets that secret.

The custody method/environment protection, allowed receiver source/ref, identity
fingerprint, creation/expiry, access audit and retirement authority are UNBOUND.
Neither the GitHub connection nor a secret name proves that mechanism exists.
Do not ask the assistant to print/paste a private identity into source/chat/logs.
Do not reuse an operator SSH/runtime/provider key or silently add a repository secret.
A substituted recipient would disclose plaintext to an attacker: missing independent
recipient-to-custodian binding blocks encryption and transfer before any upload.

The lock binds actual future values, not placeholders: repository identity, approved
builder/receiver source and policy hashes, one generation nonce, recipient fingerprint,
permitted workflow/ref, input/artifact policy and retention/scope budgets.
Actual workflow run/attempt/head values are bound from the trusted execution context
after activation, then checked against the signed provenance. They are not invented
before that run exists. A new receiver identity is not required to remain alive in
a long-running Windows job during the Linux build; approved custody bridges that gap.

Private identity is released only after source/context and required provenance
checks pass, to an owner-only no-reparse private file/handle with bounded lifetime.
No identity contents in argv, public environment dumps, telemetry or artifacts.
No untrusted action/PR code runs in a key-bearing job; forks and unreviewed refs HOLD.
Unavailable protected custody means ENVIRONMENT_UNAVAILABLE/HOLD, not weaker storage.

## 3. Fixed bundle, descriptor and publisher contract

Plaintext envelope is NOT an extraction archive: proposed fixed magic J0XFER1,
bounded length-prefixed canonical JSON header (<=16 KiB), then exactly three
role-bound byte streams: rootfs tar, private index and manifest.
Roles and ordering are fixed; header has exact keys/strict integer lengths/digests/
generation/lock binding, rejects duplicates/nonfinite/extra/trailing data.
Rootfs <=4 GiB; index+manifest together <=1 GiB; total <=5 GiB plus header.
No member-supplied filename controls envelope writes. No compression/archive nesting.

Builder hashes **EVERY retained REGULAR payload**, and independent output verification
checks the complete output index/manifest. The seven selected entries in the old
V2 catalog are input evidence only; they are not an alternative to full output hashing.
The encryption child receives only this verified generation through bounded private
pipes/handles. Standard implementation generates its own fresh encryption randomness;
do not hand-roll/reuse nonces/file keys or deterministically encrypt the bundle.

Public descriptor (proposed fixed class j0-encrypted-fixture-transfer-v1, schema 1)
contains only allowlisted policy/source/lock/recipient fingerprints, generation,
trusted run context, bounded byte counts, ciphertext SHA256 and private-part digest
commitments, expiry and false scope/readiness flags. No raw paths/package index/
device metadata/file contents, secret identity or arbitrary publisher text.
Provenance must bind EXACT descriptor bytes AND ciphertext bytes.

Proposed provenance route is GitHub artifact attestation with a pinned verifier
and trusted issuer/root/predicate policy, checking repository identity, exact
approved signer workflow/source revision and actual run/attempt context.
Descriptor strings cannot substitute for signed claims. Exact claim availability,
source-to-checkout binding, verification command/API/schema/trust-root pins and
same-run/generation matching are source blockers. If required identity cannot be
authenticated, HOLD before private identity access/decryption; no fallback to hash-only.

This route needs separately approved job-scoped OIDC/attestation permissions.
Exact permission set depends on the pinned attestor version; no workflow permission
is changed here. No blanket repository/admin token or pull_request_target secret
execution. Upload is a new opaque ciphertext basename only; no raw tar/index,
private stdout/stderr, existing workspace glob or hidden extra file is included.

## 4. Windows receiver admission before any WSL consumer

Proposed flow: verify source/lock/context → fetch bounded descriptor/provenance →
download exact ciphertext once → verify signed provenance and ciphertext digest →
load authorized receiver identity → decrypt to quarantined role files →
verify final authenticated EOF/process exit/all lengths and part digests →
independent full output-policy/manifest verification → seal generation.
Unknown/missing/expired/corrupt input latches HOLD with fixed enums only.

age may stream a plaintext prefix before the entire file has been authenticated.
That prefix is NEVER importable: three new quarantined role files remain private,
unpublished and ineligible until final authenticated completion and every verifier
passes. No full plaintext-envelope duplicate or member-name extraction is created.
The age child has no WSL/import capability and no alternate recipient/plugin/agent/
interactive prompt path; source must enforce bounded noninteractive behavior.

After decryption, rehash the actual tar/index/manifest and validate policy/source/
input/transform/critical-binary/closure bindings, every retained regular payload,
and the entire graph/output admission contract. Signed provenance and decryption
do not replace these checks or independent artifact-result acceptance.
A confidential malicious/wrong artifact still HOLDs. Transfer-ready is data state,
not guest/import/J0/R1/R2 authority.

The receiver and optional separately authorized importer must remain on the SAME
Windows job/workspace. No plaintext handoff to another job or ordinary artifact
upload. Before import, retain the reviewed deny-write/delete handle or equivalent
TOCTOU-safe mechanism on the exact verified bytes; reparse/path substitution or
unsupported importer sharing behavior HOLDs. This method is still UNBOUND.
If import is outside the approved finite scope, end at protected receipt and cleanup;
no indefinite wait, auto-import or authority inferred from a transfer success.

## 5. Budgets, retention, ownership and loss behavior

All limits below are proposals for NEW transfer substeps; previous observer/
controller/sampler/catalog timers are unchanged. No feasibility result is claimed.

| Stage | Proposed bound / containment |
|---|---|
| Linux encryption | <=180 s, <=256 MiB address space, no core; ciphertext <=6 GiB; existing builder job <=10 min remains the absolute cap |
| Builder disk | Existing >=16 GiB admission / <=12 GiB write cap retained. After preserving input/spool hashes, explicitly clean only newly-owned input/spools before encryption; verified plaintext parts <=5 GiB + ciphertext <=6 GiB fit that cap. If preservation prevents this, HOLD, no cap increase |
| Provenance publication | <=60 s inside the same builder-job deadline; scoped publisher only; no raw plaintext subject/path/content published |
| Windows receiver | <=90 s transfer subdeadline WITHIN the existing outside-owner absolute <=240 s and job <=6 min, not another clock/reset. Includes source/provenance/crypto/output verification; missing positive timing evidence is a blocker |
| Receiver disk/memory | >=16 GiB free, <=12 GiB owned workspace cap; ciphertext <=6 GiB plus decrypted parts <=5 GiB, no envelope duplicate. Crypto child <=256 MiB; bounded verifier <=1 GiB, streaming index records <=16 KiB and <=200000 |
| Retrieval | One exact descriptor/provenance/ciphertext object set per approved generation; each network operation <=15 s within the 90 s deadline; no redirect/retry/alternate run/object fallback |
| Validity/retention | Proposed acceptance expiry <=30 min after trusted publication; identity custody <=24 h; request ciphertext service retention <=1 day. Actual support/audit must be bound; expiry does not renew an action |

These upper bounds may yield false HOLD. They do not assert large bundles fit
the existing job/window, and cannot be widened silently for success.
Use local monotonic deadlines; ambiguous cross-host expiry/context is HOLD, not
a cross-clock timing proof. A failure consumes the finite transfer scope; uncertain
execution is treated as consumed. No new generation/key/object or re-download retry
is automatic. No durable exactly-once/rollback-resistance claim from a local marker.

The outside Windows owner starts before receiver activity and owns exact native
child handles/start identities, private generation ACLs, consumption state and
cleanup ledger. Process output is captured/bounded and reduced to fixed errors;
never cat crypto/verifier stderr or include raw exception/temp/identity paths.
Failure/owner loss before seal blocks WSL startup; import/guest stop remains the
separate admission-design obligation if that later scope ever starts.
Client exit, job teardown or file deletion is not guest/provider cessation proof.

Only source-verified newly-owned plaintext/key files may be cleaned after evidence
preservation, with no permission repair or existing-path deletion. Record key
retirement/request and observed cleanup honestly; do not claim secure erasure from
unlink, CI teardown, service expiry or secret removal. Custodian/service backup/
administrator and malicious-same-uid residual access stay outside the confidentiality
claim. No plaintext failure evidence may be uploaded to bypass its private boundary;
if safe preservation is unavailable, report HOLD/evidence-unavailable.

## 6. Preregistered controls and source/action exit

| Control family | Required source evidence |
|---|---|
| Custody/context admission | Missing/foreign/expired key binding, fork/ref/source drift, wrong generation/run/attempt/recipient and unapproved permissions reject before encryption/upload or secret release |
| Producer confidentiality | Private marker names/index/device fields cannot appear in public descriptor/log/upload inventory; only opaque ciphertext/provenance/descriptor leave the workspace |
| Crypto framing | Pinned standard tool; bit flip/truncation/reorder/wrong key/multi-recipient or unsupported profile/partial prefix/EOF failures never seal or launch WSL; error text never echoes secret/input data |
| Provenance vs encryption | Validly encrypted but unsigned/wrong-signer/wrong-predicate/wrong-source or replayed bundle rejects. A bare SHA or artifact ID is insufficient |
| Complete artifact verification | Tampered index/tar/content/closure/transform/overlay or only-seven-file validation fails after decrypt; every retained regular payload and manifest binding checked |
| Filesystem/publication/TOCTOU | Reparse/symlink/ACL/owner/existing destination/partial write/fsync/disk-full/source drift and verified-path replacement reach stimulus and HOLD; no existing file repaired |
| Ownership/deadlines/cleanup | Native blocked child, owner loss, expiry, lost receipt and unconfirmed stop preserve honest state; no retry or background key/guest use; driver EOF is not cessation |
| Actual route | After exact source/custody/permissions/storage/attestation/tool binding and separate finite approval, real Linux-to-Windows ciphertext/provenance/private-seal evidence on the same run; synthetic fixtures cannot claim that route tested |

Design acceptance enables source preparation only. Builder/receiver/verifier/
custody integration/external-owner sources and exact hashes do NOT exist here.
Action blockers remain: actual approved recipient/custody access, pinned tools/
attestor/verifier/trust policy and permissions, authenticated claim/context mapping,
closed descriptor/envelope schema, real timing/disk/capability, private ACL and
TOCTOU method, exact owned cleanup/retention and separately approved finite scope.
No key value/hash, prepared artifact or activation selector is invented.

FIVE archive invocations / FOUR digest matches; E12 UNKNOWN. This proposal neither
fetches that archive nor approves invocation six, transfer, build/import or secrets
provisioning. All eighteen rows OPEN; #112 draft; J0 NOT READY;
R1 NOT AUTHORIZED / R2 HOLD; #80/#96/A6/A7 and previous records unchanged.
Any security/approval-boundary change must follow SPEC §14 before implementation merge.
