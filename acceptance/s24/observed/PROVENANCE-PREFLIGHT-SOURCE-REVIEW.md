# T1/T2/P1/P2 — source discovery and unsigned policy preflight

Date: 3 November 2026 (Asia/Bangkok). Input #112
`004eac4f56f866b93c713379a969d04729bb221a`.
Operator-supplied round-29 review APPROVED the binding inventory. The subsequent
request “ทำขั้นถัดไป” authorizes this source-preparation target; exact timestamp
NOT_PROVIDED. **PARTIAL SOURCE CANDIDATE; NO AUTHENTICATED VERIFIER OR TOOL EXECUTION.**

## 1. What this delta actually supplies

[Discovery snapshot](TOOL-SOURCE-DISCOVERY.json) records exact upstream release
objects/source revisions and provider-reported archive/proof digests observed by
read-only GitHub API on the date above. It is not an executable lock. Archive bytes,
binary SHA256, release authenticity/trust chain and installed capabilities have
NOT been verified. No release archive/proof was downloaded, installed or executed.
No key or attestation was created; no OIDC/permission/token/secret change occurred.

`provenance_preflight.py` supplies a bounded, pure, stdlib-only policy comparison
contract and 20 synthetic negative/positive controls. **It accepts only a distinct
UNSIGNED certificate projection, not raw gh output or a Sigstore bundle.** The
policy/descriptor/projection namespaces are j0-unsigned-preflight-* and
j0-unsigned-certificate-projection. Missing/duplicate/extra keys, floating/nonfinite
numbers, bool-as-int, oversized/deep JSON, wrong identities and altered object
bytes reject. All exception args are empty and reasons are fixed labels.

Exact equality of all fifteen certificate values, both object subjects and bound
descriptor context yields only MATCHED_UNAUTHENTICATED with provenance/tool/scope/
secret-release/J0/R1/R2 false. The result is an ordinary advisory dictionary,
**not the internal authenticated typed result required by the transfer design**.
A caller can fabricate an unsigned projection; this component cannot distinguish
it from authenticated claims and deliberately never claims to do so. A separate
trusted adapter must authenticate cryptography and checked bytes before its own
non-caller-mintable internal result can exist. That adapter is NOT IMPLEMENTED.
There is no verifier-success boolean input, production admission API or integration
with transfer_offline.py. Existing fixture and real-transfer boundaries are intact.

The tool-object helper compares small synthetic bytes to an expected digest/length
and returns DIGEST_EQUAL_UNAUTHENTICATED with tool/execution false. Its 8 MiB cap
does not admit the discovered real tool archives and is not a production downloader.
No network, subprocess, host open, storage, key/crypto/WSL operation or CLI exists
in the module. Fixture limits: JSON 64 KiB/depth 12; compared object 8 MiB.

## 2. Exact upstream evidence and claim feasibility

Inspected primary source revisions (inspection pins, not installed binary pins):

- [gh CLI v2.103.3 source](https://github.com/cli/cli/tree/63837fb778d6a39f02be0ce76ff89f2bc8d74bdc)
  and [release API](https://api.github.com/repos/cli/cli/releases/424663522).
- [age v1.3.2 source](https://github.com/FiloSottile/age/tree/b74dce4cdbe35b5e5f66c06d9612b72f89028758)
  and [release API](https://api.github.com/repos/FiloSottile/age/releases/379059621).
- [sigstore-go certificate fields](https://github.com/sigstore/sigstore-go/blob/22d3691c7b8e0c5530fae3c05577690bfef5cd00/pkg/fulcio/certificate/extensions.go),
  dependency v1.3.0 in the inspected gh go.mod.
- [Fulcio GitHub mapping](https://github.com/sigstore/fulcio/blob/3707d80bb25330bc7ffbd9702fb401cd643e36fa/pkg/identity/github/principal.go).
  This historical mapping source is cited by the inspected extensions source;
  it is NOT proof of the currently deployed issuer version or actual emitted cert.
- [Attestor v3 action source](https://github.com/actions/attest-build-provenance/blob/977bb373ede98d70efdf65b84cb5f73e068dcc2a/action.yml)
  delegates to predicate `864457a58d4733d7f1574bd8821fa24e02cf7538` and attest
  `daf44fb950173508f38bd2406030372c1d1162b1`. Complete transitive dependency,
  permissions, builder trust/isolation and runtime verification remain UNBOUND.

The inspected [gh command source](https://github.com/cli/cli/blob/63837fb778d6a39f02be0ce76ff89f2bc8d74bdc/pkg/cmd/attestation/verify/verify.go)
distinguishes certificate/timestamp-derived values from workflow-controllable
statement.predicate values. Its policy/extension code enforces some certificate
fields, not the entire application contract. An unsigned JSON copy of gh output
cannot replace a trusted pinned execution with independently bound inputs/output.
Offline bundle repo-name matching alone also cannot prove current name ownership.

| Required claim | Candidate authenticated location / preflight check | Feasibility disposition |
|---|---|---|
| Issuer | certificate.issuer exact GitHub OIDC URI | REPRESENTED in inspected source; actual issuer/root verification UNBOUND |
| Signer workflow | subjectAlternativeName + buildSignerURI exact, including ref | REPRESENTED; exact reusable/direct topology and live cert UNBOUND |
| Signer source | buildSignerDigest | REPRESENTED; independent of source/build-config SHA |
| Source repository + owner | sourceRepositoryURI + sourceRepositoryOwnerURI | REPRESENTED; exact comparison, no case/prefix normalization |
| Immutable repo + owner IDs | sourceRepositoryIdentifier + sourceRepositoryOwnerIdentifier | REPRESENTED; additional application check required, not supplied by name-only flag |
| Checkout source revision | sourceRepositoryDigest | REPRESENTED; reviewed checkout-to-source enforcement still UNBOUND |
| Source ref/event/runner | sourceRepositoryRef + buildTrigger + runnerEnvironment | REPRESENTED; current profile requires main/dispatch/github-hosted; no fork inference from name alone |
| Initiating workflow + revision | buildConfigURI + buildConfigDigest | REPRESENTED; workflow_sha is separate from source_sha and signer_sha |
| Run + attempt | runInvocationURI exact /actions/runs/N/attempts/M | REPRESENTED in historical issuer mapping; actual route presence/format must be verified or HOLD |
| Predicate type | authenticated statement predicateType | REPRESENTED; content of predicate is not an issuer-authenticated context substitute |
| Descriptor + ciphertext subjects | two exact SHA256 subjects plus authenticated descriptor commitment | PROPOSED contract; actual two-subject attestor and adapter matching NOT TESTED |
| Generation/lock/recipient/expiry | authenticated descriptor, independently approved production lock | UNBOUND; unsigned preflight only checks fixture generation/lock/run/attempt, not recipient/expiry |
| Trusted publication time | verified timestamps plus independently accepted freshness policy | UNBOUND; no supplied caller time accepted as proof |

REPRESENTED means the named source field exists, not actual-route feasibility or
an accepted cryptographic binding. Missing/unsupported claims must HOLD, never
backfill from caller fields, predicate strings, API metadata or process exit alone.
The fixture profile fixes both workflow refs to main and assumes same repository;
it does not model arbitrary cross-repository reusable workflows. No real workflow
is selected by these synthetic expected values.

## 3. Tool authenticity remains a separate unresolved chain

age's pinned SIGSUM.md describes Sigsum proof verification, not SHA-only trust.
The discovered Linux/Windows archives have corresponding proof objects, but
Sigsum verifier binary/source/authenticity, log/witness policy, independently
approved release keys and key rotation are UNBOUND; none were bootstrapped here.
Documentation examples are not executed. The age release includes compatibility
plugins: a future installation must isolate the allowed native executable and
prove no plugin/PATH/agent fallback; archive digest alone does not enforce this.

gh release archive metadata is likewise not executable publisher-authenticity
evidence. Its bootstrap trust root/authenticity policy and final executable hashes
remain UNBOUND. A verifier cannot authenticate its own installation from an
untrusted copy of its output. Exact dependency/root/freshness pinning, network
restrictions, native child ownership/deadlines/stop and safe bounded output
capture are requirements for a future adapter, not implemented by this preflight.

Therefore T1/T2/P1/P2 are **PRESENT PARTIAL / ACCEPTANCE OPEN**, and all real
execution bindings in the prior register remain UNBOUND. No cryptographic claims
are closed. C1-C3, P3, S1/N1/W1/O1/A1 are unchanged. The next gate is independent
review of this mapping/source, followed by a concrete tool-bootstrap/authenticated
adapter proposal with the missing trust-chain/route evidence; not another
automatically authorized download, invocation or custody action.

## 4. Controls, validation and unchanged boundaries

Twenty tests cover all fifteen missing/mismatched claims, repo ID/name reuse,
run/attempt replay, workflow/ref suffix/prefix attacks, unsigned predicate backfill,
caller success/auth booleans, both subjects, wrong predicate, changed real input
bytes, descriptor mutations with rebound outer digest, schema/parser bounds,
tool digest/length mismatches, and AST import/action audit. Independent synthetic
expected claims distinguish source/workflow/signer SHA values. No valid signature,
certificate chain, transparency log, age encryption or real tool test is claimed.

Author local: Python 3.12.14, ResourceWarning as error, isolated/no-site/no-bytecode,
20/20 OK exit 0. The environment became usable this turn; this does not alter
earlier NOT RUN records. CI adds one offline-only 20/OK/no-skips/warning step.
Exact local-computed source SHA256 values:

| File | SHA256 |
|---|---|
| provenance_preflight.py | `1e9d8000e2c9b8e5f006bcde75d375c61143d25906c5f0faef9b199509df97a5` |
| test_provenance_preflight.py | `ba46b2e32507da8381085d3894ceb7f48f192585b20309a9cce6f649b8c8901a` |
| TOOL-SOURCE-DISCOVERY.json | `69e46fc4ba7130ab4d6fa82f05d7e037d60e39fedfb3568cbe579553d4dbb261` |

Head-specific CI evidence is recorded separately in the PR.
No existing test/assertion/source/pin/selector/actual result is modified.

FIVE archive invocations consumed / FOUR digest matches; E12 UNKNOWN.
No invocation six, key/secret/custody, permission/tool install, signed-verifier
execution, transfer/build/import/guest, merge or release/deployment. All eighteen
rows OPEN; #112 draft; J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD; #80/#96/A6/A7
unchanged. SPEC section 14 remains applicable before security-boundary implementation merge.
