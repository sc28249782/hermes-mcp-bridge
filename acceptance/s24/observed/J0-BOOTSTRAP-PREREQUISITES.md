# J0 bootstrap prerequisites — concrete seed route and bounded disposition

Date: 3 November 2026 (Asia/Bangkok). Input draft #112
`ce97cfd485d1a374940e40a74fdb522def99e670`.
Operator-supplied round-31 review accepted the authenticated-adapter proposal.
The subsequent “ทำขั้นถัดไป” requests this prerequisite packet; exact timestamp
NOT_PROVIDED. **NO BOOTSTRAP ACTION OR AUTHENTICATED ADAPTER IMPLEMENTATION.**

## 1. Candidate root of trust — explicit platform assumption

The concrete candidate is a **GitHub-managed hosted Ubuntu runner image and its
independently preprovisioned gh executable**, used as the initial verifier for a
separately acquired, exact gh release object. Trust begins with the independently
accepted platform/image provisioning authority, not the target release checksum,
target binary or target binary's report about itself. This is a proposed trust
decision for review, NOT an accepted root or a claim that the present runner's
installed gh was inspected. No seed executable version/hash is known today.

Platform control plane, runner provisioning, reporting and accepted installed
seed integrity would be inside this limited trusted computing base. An attacker
controlling that platform/seed is outside this proposed verification claim.
Independent provisioning does not mean a different publisher; it means that the
seed's trusted acquisition and admission do not depend on the target it verifies.
If that trust assumption is not accepted, the route is unavailable. Do not pretend
that recursively verifying every verifier eliminates the need for an initial root.

Prerequisite policy: an independently approved platform/image/seed identity and
authenticated delivery evidence must exist BEFORE using the seed. A hosted label,
setup log, version string, file hash measured only by the same untrusted host,
GitHub connection or previous green CI alone cannot establish this acceptance.
No arbitrary preinstalled gh is executable under this packet.

## 2. Actual read-only evidence and failed binding check

The existing author-CI run 41589022058, job 125761168209, belongs to the reviewed
head ce97cfd4. Its setup log reports image ubuntu-24.04, version 20261025.353.1,
and points to runner-images ref ubuntu24/20261025.353. These are platform-reported
facts, NOT immutable image measurements or a receipt for installed executable bytes.
No new job or runner action was dispatched to obtain them.

Read-only GitHub API checks on that exact referenced ref returned:

- Contents lookup for images/ubuntu/Ubuntu2404-Readme.md with the exact ref:
  HTTP 404, “No commit found for the ref ubuntu24/20261025.353”.
- Matching refs for tags/ubuntu24/20261025.353: empty list.

Consequently that reference could not be bound to inspectable source in this
session. The cause, historical availability and any broader absence remain
UNKNOWN. No immutable manifest/seed digest, signing chain or installed binary
identity was recovered. Do not infer a specific gh version from another image,
promote main to that image's manifest, or treat this as proof of a compromised
image/tool. Tool URL-path rejection on an earlier encoded-ref request was not
used as evidence; the disposition uses the two subsequent API results above.

The runner-images README at the separately inspected source commit
4da2307112a0fad2fd2ecaca8ba7d08683b8c581 explains setup-log image/software identity,
weekly updates, and non-idempotent builds. It describes mechanisms, not proof of
this runner/image/seed. [Bounded evidence record](BOOTSTRAP-SEED-EVIDENCE.json)
keeps these distinctions and the upstream README commitment without raw logs.

## 3. Admission register — all dependent execution stays blocked

| Required binding | Concrete target / present evidence | Disposition |
|---|---|---|
| Root authority | GitHub-managed hosted-image provisioning trust, explicitly accepted by bootstrap authority | PROPOSED; acceptance UNBOUND |
| Image identity | Reported ubuntu-24.04 / 20261025.353.1, exact referenced manifest lookup unavailable | REPORTED ONLY; immutable/authenticated binding UNBOUND |
| Seed verifier | Preprovisioned gh in that accepted image; exact executable/dependencies/actual SHA256, owner and no-substitution proof | UNOBSERVED / UNBOUND; not executable |
| Independent delivery | Platform/seed authenticated provenance plus independently reviewed expected identity; not target-derived/self-report | UNBOUND |
| Target gh | Prior discovery v2.103.3 objects; seed verifies exact release signer/source/context before selecting/hash-binding executable | Provider metadata only; NOT ACQUIRED / NOT VERIFIED |
| Sigstore trust set | Prior proposal's authenticated rotation/current-root/freshness chain, exact custom trusted_root and domain | UNBOUND; embedded TUF root cannot substitute |
| age/Sigsum | Independently authenticated sigsum-verify, release keys/log/witness policy, exact archive/proof and selected native executable | UNBOUND; no key/claim/policy invented |
| Native owner | Reviewed image/seed/target/inputs handles, network denial/config isolation, finite process/stop/resource scope | UNIMPLEMENTED / UNBOUND |

BOOTSTRAP_SEED_UNAVAILABLE is the **packet's disposition**, not a new runtime enum,
an executed bootstrap failure, or a signed cryptographic verdict. It means this
chosen route cannot presently meet its prerequisites. T1/T2/P1/P2 remain OPEN.

## 4. Finite exit and next decision

This prerequisite investigation is complete at the documented failure to bind a
usable seed. Do NOT add more unsigned matchers, repeated image lookups, bootstrap
proposal layers or a permissive source implementation to call the gate passed.
No installed seed is authenticated and no bootstrap/action source is ready.

To resume this route, supply one independently reviewable authenticated seed
package: accepted root authority/trust boundary, exact platform or separately
provisioned seed identity, executable/dependency hashes, independent provenance/
delivery proof and retained-identity method. Review it against the table once.
Only then prepare exact bootstrap/adapter source and preregister actual signed
controls, followed by separate finite action approval. Existing image/manifest
unavailability cannot be repaired by silently using another image or runner ref.

If that package cannot be supplied, the next operator decision is **defer this
J0 route** or choose an explicitly different independent seed route with its own
bindings. This packet recommends deferring execution until such evidence exists.
It does not request secrets or authorize operator-host access. The seed/bootstrap
authority is distinct from receiver-key custodian C1-C3; no custody work is started.

The [accepted source proposal](J0-AUTHENTICATED-ADAPTER-PROPOSAL.md) remains the
adapter contract. This packet neither weakens it nor changes earlier facts.
No source/tests/workflow/pin/guard/actual-attempt record is changed. No tests are
added for this docs/data-only delta. No invocation six, tool install/execution,
root update, signature verification, permissions/key/secret/custody, transfer,
build/import/guest, merge or release/deployment. FIVE consumed / FOUR digest
matches; E12 UNKNOWN; all eighteen rows OPEN; #112 draft; J0 NOT READY;
R1 NOT AUTHORIZED / R2 HOLD; #80/#96/private A6/A7 unchanged.
SPEC section 14 remains applicable before normative/security-boundary implementation merge.
