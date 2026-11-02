# J0 inspection/import admission — evidence and next-route decision

Date: 2 November 2026 (Asia/Bangkok). Input draft #112
`c6c9597a0f024190dd7fc1bb653e67f94d3efb2f`.
**DECISION / REQUIREMENT-MAPPING CANDIDATE ONLY.**
Operator's “ทำขั้นถัดไป” prepares this packet; exact timestamp NOT_PROVIDED.
No new lane/source/receipt schema, invocation six, builder/import, guest or E counter.
Operator-supplied round-24 review accepts attempt-five V2 catalog evidence at
this input head; that review does not approve a new preparation action.

## 1. Keep the three actual lane outcomes distinct

| Actual lane / record | Proven result | What it does not prove |
|---|---|---|
| Strict diagnostic E17 — [record](ARTIFACT-ATTEMPT-E17.json) | ARCHIVE_PARSE / PREDICATE_REJECTED / TYPE_REJECTED; parsed_members=5; digest matches | Specific type/member/path UNKNOWN; no completed strict inspection or BACKSLASH observation |
| V1 catalog attempt four — [record](CATALOG-ATTEMPT-FOUR.json) | BACKSLASH; parsed_members=11701; incomplete counts; digest matches | Not a strict-lane BACKSLASH failure, parser defect, import/security diagnosis or completed EOF |
| V2 literal catalog attempt five — [gate](LITERAL-CATALOG-ATTEMPT-FIVE-GATE.json) | COMPLETE/NONE, 49190 normalized entries, complete six-class map, seven selected entries | No strict success, full content tree, safe extraction/import, prepared image or J0 authority |

Matching archive digest identifies the same fixed bytes across these recorded
runs, not equivalent policies or completion. V2's 49190 and eight CHAR_DEVICE
entries cannot be backfilled into E17 or identify E17's rejecting type/member.
No claim that both strict and catalog scanned the full same count is supported.
No historical actual record is edited or relabelled.

Current total: FIVE consumed invocations / FOUR recorded full digest matches;
E12 UNKNOWN. All producer jobs are disabled; no sixth action is approved.

## 2. Requirements traced to the reviewed J0 documents

This table separates required end-state evidence from one implementation's
success field; it does not waive any prerequisite.

| Source / existing criterion | Evidence now available | Still required before its dependent step |
|---|---|---|
| [Join plan §2](WINDOWS-LINUX-JOIN-PLAN.md#2-j0--bind-the-environment-before-any-importstart): pinned rootfs provenance/content/archive identity | Fixed source/receipt pins, real archive digest and accepted V2 header/selected-hash catalog | Reviewed artifact-preparation/admission contract and actual immutable artifact/manifest; metadata-only evidence is not that artifact |
| Same §2: reviewed immutable artifact and manifest before Windows import | No prepared artifact retained; attempt-five TemporaryFile was ephemeral | Exact resulting artifact bytes/hash, preparation provenance and manifest bound to the consumer before import; no placeholder success |
| [E11 §2–§3](ARTIFACT-PREPARATION-REVIEW.md#3-setup-source-dependencies-and-review-exit): contents precede package/build recipe; inspection receipt is not prepared image or extractor approval | Five selected regular content hashes and two unresolved links | Exact immutable package/build inputs if needed, preparation source/controls and independent review before execution; no floating install recipe |
| [Catalog design §§2,4,6](METADATA-CATALOG-DESIGN.md): explicit catalog-only policy; later extraction/import has separate policy/approval | Metadata milestone complete under reviewed V2; archive_inspection_verified/prepared/extraction/import flags false | Define and review the consumer-specific admission policy; do not promote catalog flags or silently reuse its name/type whitelist for filesystem writes |
| Join plan §2: Python/sshd/client identities and supported matrix | python3.12 file hash plus unresolved python3 link; no usr/sbin/sshd selected entry in the receipt | Guest binary/version/dependency/capability proof for the chosen route; no inference from filename/hash or missing selected entry to install/alternate-path authority |
| [Capability checkpoint §3](J0-CAPABILITY-SOURCE-REVIEW.md#3-remaining-j0-bindings-and-next-review-boundary): kernel/boot/coexistence | Named historical CI snapshots; two candidate kernel locations ABSENT_OR_UNREADABLE | Configured kernel/client identity, boot/virtualization support and coexistence; no global absence/presence claim, default-distro reuse or implicit WSL update |
| Join plan §§2,6: exact setup actors/resources/stop/lifecycle | No new setup/ownership source in this packet | New uniquely bound names/paths/account/keys/endpoint, exact source/hash/argv/budgets, outside owner and confirmed targeted stop; destructive unregister separately bound/approved |
| Join plan §§3–§5: same-invocation native Windows SSH/collect/CIM and failures | E4/E6/E7 remain separate component evidence | Actual joined source/control evidence and all mandatory eighteen-row dispositions, not a combined claim from separate receipts |

No global requirement to make the particular E11 strict program/success class
pass this same archive was found in the cited J0 end-state criteria. E11 specifies
that program's original strict contract; E18 explicitly permits catalog evidence
to support later artifact/setup source preparation while keeping strict flags false.
This is a documented interpretation **for review**, not permission to bypass
artifact inspection/preparation admission. The required real admission evidence
is still absent; J0 remains blocked.

If independent review establishes an additional mandatory strict-lane requirement,
it remains a blocker until explicitly resolved. Neither this interpretation nor
a green catalog authorizes a replacement receipt class or new security boundary.
Any normative conflict follows [SPEC §14](../../../docs/SPEC.md#14-change-control)
before implementation is merged. No specification is amended here.

## 3. Next-stage alternatives

These are choices for the next work package, not a revision of the accepted V2
catalog route choice or an action authorization.

| Choice | Work to prepare for review | Cost / boundary |
|---|---|---|
| A — another exactly bound artifact/route | Nominate provenance/digest, required guest binaries and import/admission policy anew | Existing V2 evidence does not transfer; no automatic URL/image substitution or invocation |
| B — consumer-specific prepared-artifact admission design using current fixed input | Define how this exact archive becomes an immutable artifact/manifest acceptable to the chosen Windows/WSL consumer; bind binary/package and environment prerequisites | Recommended **design-only next work**, not another generic strict clone, extractor, builder or direct import; feasibility and compatibility remain unproved |
| C — defer this CI route | Record deferred route and outstanding obligations; another dedicated lab requires its own reviewed scope | No optional-row conversion, operator-VM fallback or source-acceptance waiver |

Recommendation: **B for a single prepared-artifact admission design**, using the
accepted catalog as evidence input rather than downloading again to turn the old
strict flag true. No consumer implementation or package is selected by this packet.
A/C remain available; no automatic continuation if review rejects feasibility.

## 4. Finite design handoff and stop condition

If B is selected after independent review, the next design deliverable must settle
the following existing admission gaps together, before source/action approval:

1. Choose the consumer/preparation method explicitly. Treat all six returned types,
   literal names, slash aliases, links, device metadata, collisions and target
   filesystem semantics under that consumer's own reviewed policy. UNKNOWN means
   HOLD; no automatic extractall, mknod, path rewrite or link following.
2. Bind original input digest/catalog provenance, exact preparation transformations
   (or explicitly none), required guest binaries/packages and resulting immutable
   artifact/manifest identity. A raw download/catalog receipt is not a prepared image.
   No complete version, installed-package or library proof comes from the current
   selected hashes; no raw config/package-list contents are read by this packet.
3. Show kernel/boot/client/coexistence prerequisites and all setup/owner/stop/
   resource/cleanup bindings. Missing route capability cannot be repaired by more
   parser policy variants, packages on the operator host or a silent alternate lab.
4. Preregister preparation/compatibility and negative controls, evidence meaning
   and false-flag boundaries, then review exact source/hashes before any finite
   build/import/run proposal. Separate action approval is still required; no
   activation argv, invented output hash or sixth-attempt selector exists here.

Exit of this decision packet: independent verdict on the requirement mapping
and operator selection of B design scope, A or C. It does not need another live
archive request to settle that decision. Exit of a later B design is one closed
reviewable artifact-admission/setup plan **or explicit infeasibility/HOLD**.
Do not grow an automatic chain of new strict/catalog variants or repeatedly
re-measure the same complete catalog. A new request must have a defined remaining
evidence target and its own finite scope.

## 5. Preserved gates

All eighteen [ledger](R1-INTEGRATION.md#current-closure-ledger) obligations remain
OPEN; A2/A3 are not accepted merely because their environment prerequisite gained
metadata evidence. Private A6/A7 and #80/#96 unchanged.
J0 NOT READY; R1 NOT AUTHORIZED / R2 HOLD; #112 draft/unmerged.
No source/test/workflow/pin/actual-record edit; no archive read, import/preparation,
WSL invocation, guest setup, credential/model/backend action, merge or release.
