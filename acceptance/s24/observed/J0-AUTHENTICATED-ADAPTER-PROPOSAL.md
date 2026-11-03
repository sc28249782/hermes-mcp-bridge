# J0 tool bootstrap and authenticated adapter — source proposal

Date: 3 November 2026 (Asia/Bangkok). Input draft #112
`e192a67d58b32177dc89561723031e025c864885`.
Operator-supplied round-30 review APPROVED unsigned preflight only. The subsequent
“ทำขั้นถัดไป” requests the proposed next source boundary; exact timestamp
NOT_PROVIDED. **PROPOSAL FOR REVIEW, NOT IMPLEMENTED, NOT ACTION-READY.**

## 1. Finite target and source findings

The [binding register](J0-TRANSFER-BINDING-PACKET.md) and
[unsigned preflight limitations](PROVENANCE-PREFLIGHT-SOURCE-REVIEW.md) remain
applicable. This packet selects a proposed adapter architecture and specifies
its future source interface, trust prerequisites and real signed controls.
It adds no adapter/downloader/crypto implementation or synthetic verifier tests.
T1/T2/P1/P2 remain acceptance-OPEN. C1-C3 custody remain a separate proposal.

[Source evidence commitments](AUTHENTICATED-ADAPTER-SOURCE-EVIDENCE.json) bind exact
inspected upstream text bytes, not executable identities or accepted trust anchors.
gh source revision is 63837fb778d6a39f02be0ce76ff89f2bc8d74bdc (v2.103.3);
age source is b74dce4cdbe35b5e5f66c06d9612b72f89028758 (v1.3.2).
Earlier release archive digests remain provider-reported discovery facts only.

Material findings from pinned gh verification/sigstore.go, tuf.go and verify.go:

- The default TUF fetcher sets maximum tries to three and uses a cache. Default
  remote trust initialization cannot silently satisfy our no-retry/fixed-context
  contract. Merely adding --bundle does not select the custom-root branch.
- A nonempty custom trusted-root file creates only custom verifiers and returns
  before default Public Good/GitHub TUF initialization. A local bundle selects
  local attestation loading. These are source observations, not a proved network-
  free execution; the future owner must additionally enforce network denial.
- The embedded TUF root is version 3 with expires=2025-04-11T14:36:57Z. That is
  historical bootstrap metadata, NOT a completed current trust-root validation.
  It is not the Sigstore trusted_root JSON accepted by the custom-root flag.
  An expired bootstrap root alone does not prove the whole updater/tool unusable:
  authenticated root rotation/current metadata have not been evaluated here.
- Custom-verifier selection uses the certificate authority organization and the
  supplied root. The GitHub OIDC issuer URI is a DIFFERENT identity dimension.
  Do not assume public-repository attestations use the GitHub private instance,
  or turn on no-public-good without an accepted actual trust-domain binding.
- The source can retain successfully verified attestations when other candidates
  fail. Our adapter must enforce its own exact-one accepted statement contract;
  exit zero or any-one-valid alone is not application admission.

These findings change no prior timer, policy, tool or source. No tool was run,
no root signature or release proof was verified, and no root/asset downloaded
except the bounded public upstream text used for this read-only source inspection.

## 2. Proposed bootstrap chain — no self-authentication

| Binding | Proposed prerequisite to its first use | Status |
|---|---|---|
| Initial verifier | Independently provisioned verifier/compiler provenance under an approved bootstrap authority; exact executable/dependency/platform hashes and authenticated delivery receipt | UNBOUND |
| gh executable | Verify exact release object with the independent bootstrap verifier and accepted release signer/workflow/source policy, then inspect selected executable and bind its actual SHA256 | UNBOUND; gh cannot authenticate its own installation |
| Sigstore trust set | Accepted trust-domain policy plus authenticated TUF/root rotation, timestamp/snapshot/targets and selected Sigstore trusted_root; exact bytes/hash, validity/freshness and rotation authority | UNBOUND; embedded root snapshot is not sufficient |
| age executable | Exact release archive and Sigsum proof, independently accepted age release public keys, Sigsum log/witness policy, authenticated sigsum-verify tool and receipt; actual selected executable hash | UNBOUND |
| Runtime native identities | Tool objects acquired into exclusive private staging; bounded archive parser selects only allowed executables; no installer/hooks/plugins/PATH fallback; owner/ACL/reparse and deny-write/delete handles | UNBOUND |

Bootstrap is a separately reviewable prerequisite stage, not a hidden network
step inside the receiver's <=90 s budget. Its source, input objects, trust anchors,
fetch inventory/no-retry/expiry/resource limits and independent evidence must be
reviewed before a finite bootstrap action is proposed. No acquisition budget or
permission is invented here. A checksum or manual acknowledgment without the
required independent authenticity evidence cannot close this chain.
No automatic package install, go install, latest lookup or trust-root refresh.
If a platform cannot supply the initial independent root of trust, stop with
BOOTSTRAP_UNBOUND and return to route/defer, not another self-verifying tool.

## 3. Proposed future source split and interfaces

These names are planned files, not existing source or executable argv:

| Planned source responsibility | Input and output boundary |
|---|---|
| tool_bootstrap_policy.py | Closed reviewed bootstrap lock + private acquisition/verification receipts; produces no execution authority from release API JSON; rejects missing independent trust chain |
| authenticated_provenance_owner.ps1 | Native owner starts first, retains immutable approved verifier/root/bundle/descriptor/ciphertext handles, captures bounded child output, enforces deadline/network/stop and feeds checked bytes privately |
| authenticated_provenance.py | Parses only owner-captured pinned verifier output; independently validates certificate/context/statement/subject/descriptor bindings; mints an internal one-use result only within that owned invocation |
| test_authenticated_provenance.py + Windows owner controls | Actual signed bundle verification with a pinned standard verifier plus native failure/identity/network/stop controls; synthetic parser tests reported separately |

The implementation review must provide exact source hashes for these files and
all dependencies; current names do not extend the baseline two-file transfer grant.
The existing unsigned preflight is neither imported as an authority nor given a
public promote/verified=true adapter. Its accepted bytes stay unchanged.

## 4. Verification transaction and trusted result

Proposed transaction: validate source/production lock and all prerequisite tool/
root identities -> retain owned immutable input handles -> hash exact descriptor
and ciphertext -> run ONE pinned gh verifier on the descriptor with an exact
local bundle, exact local custom trusted-root, SHA256, exact repo/issuer/certificate
identity/signer/source/ref/predicate policy and bounded JSON output -> confirm
owned process exit and revalidate all identities -> application policy check ->
mint internal result. Concrete native argv/path/source bindings remain UNBOUND.
No shell/OCI/registry/service lookup, HTTP client fallback, redirected/retried
network, user config/token inheritance or downloaded executable invocation.
The source must prove handle-to-path sharing supported by that exact native tool;
check-then-execute of a mutable numeric path is insufficient.

Require exactly one accepted verified statement. Its signed subject list must
bind EXACTLY the descriptor and ciphertext identities/digests, with fixed role
names, no duplicate/extra/ambiguous subjects and no stitching across statements.
gh verifies descriptor digest against the signed statement; the application must
also compare the ciphertext's actual digest to that SAME signed statement and
the authenticated descriptor. This proposed single-call design is NOT tested.
If the chosen attestor/verifier cannot supply this contract, report infeasibility
rather than silently changing subject semantics or adding retries.

All required certificate fields use authenticated verificationResult.signature.
certificate data; no equivalent value is read from statement.predicate. Enforce
repo/owner numeric IDs and URIs, OIDC issuer, exact SAN/buildSignerURI/revision,
source revision/ref, initiating buildConfigURI/revision, event/runner and exact
run/attempt URI. Source, workflow and signer digests remain separate. Do not infer
fork isolation from URI alone: approved event/source and workflow trust must hold.
All accepted timestamp/freshness/expiry, recipient/generation/lock and two-subject
rules must be bound in a closed production schema before source acceptance.

The internal result commits to exact source/tool/root/bundle/descriptor/ciphertext/
lock/policy hashes and authenticated repo/workflow/run/attempt/generation context.
It is minted and consumed inside the same owner-scoped transaction, never accepted
as caller-supplied JSON, a bool, replayable receipt or external constructor argument.
One successful use can permit only the separately approved next data-state step;
it cannot authorize secret release beyond its exact custody scope, decrypt/import,
J0/R1/R2 or any new action. Python type privacy alone is not a security boundary
against malicious code in that same process. Trusted source/owner and closed
call graph are required; process compromise lies outside that limited claim.

Failure latches HOLD. All paths require observed child exit/stop and handle cleanup;
driver EOF, client exit, missing PID or CI teardown do not prove cessation.
No raw JSON/bundle/certificate/predicate/stderr/paths escape into public telemetry.
Fixed bounded stage/reason labels only. Unknown execution consumes finite scope.
Existing transfer <=90 s inside owner <=240 s/job <=6 min remains unchanged;
bootstrap success cannot reset these clocks or establish feasibility.

## 5. Preregistered controls and finite exit

| Control family | Required evidence before dependent action |
|---|---|
| Bootstrap | Independent valid chain admits only exact expected object; substituted binary/proof/root/expired policy/hash-only/self-verification rejects before execution |
| Actual cryptography | A real standard-tool signed bundle passes signature+chain policy; changed payload/signature/cert/timestamp/root/expired or unsupported trust domain fails; counts separate from parser tests |
| Certificate context | Actual or independently signed controlled bundles reach every missing/wrong numeric ID, signer/source/workflow/ref/event/runner/run/attempt check; predicate backfill cannot pass |
| Subjects | Both exact subjects on one verified statement pass; one missing, swapped, duplicate, extra, different statements, rebinding descriptor/ciphertext/generation/recipient/expiry rejects |
| Native process and I/O | Owned executable/input substitution, reparse/ACL/locked sharing, blocked child, malformed/huge/trailing/duplicate output, valid prefix followed by failure and nonzero exit reach stimulus and HOLD |
| No network/retry/config | Default TUF/API/OCI and credential/config probes are denied; no retry or alternate domain; positive offline custom-root/local-bundle run proved on exact native binary |
| Result/ownership | No caller-forged token/JSON/bool, second consumption, stale generation, lost receipt or owner death opens the next stage; native stop remains independently confirmed |

No controls in this table have run. Tests must use pinned real cryptography
implementation, not hand-written signature acceptance or unsigned projections.
A self-generated local test CA is test-only and cannot become a production root.
Fixtures used for all context faults must reach the cryptographic/admission
boundary claimed; earlier rejection cannot masquerade as downstream coverage.

Exit of THIS packet: independent review of the source architecture, bootstrap
chain and registered controls, with explicit unresolved bindings. No fake pin or
additional synthetic-only matcher is needed to declare progress. Next implementation
starts only against accepted exact bootstrap inputs/trust policy and a reviewable
production schema. If those cannot be supplied, record infeasibility/route-defer.
Custody/environment proposal C1-C3 remains separate; no key-bearing job exists.

This is docs/data only, no source/workflow/pin/actual-record changes or new E counter.
No invocation six, tool install/execution, root update, key/secret/custody, signed
verification, transfer/build/import, merge or release/deployment. FIVE consumed /
FOUR digest matches; E12 UNKNOWN; all eighteen rows OPEN; #112 draft;
J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD; #80/#96/private A6/A7 unchanged.
SPEC section 14 applies before normative/security-boundary implementation merge.
