# Phase B source increment 2: offline identity/discovery contract

Status: **SOURCE FOR REVIEW — offline only; actual connector invocation remains HOLD**.
Design: [Phase B adapter/control plan](../../docs/S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md).
Prior source: [offline parent contract](PARENT-CONTRACT.md), reviewed at PR #97 head `143bcc33317dc2118b1a30ea2eb9728847c27561` and merged at `ab8fff7588296155eeb239c0847761ec083c88b3`.
The separate Phase A acceptance record [PR #96](https://github.com/sc28249782/hermes-mcp-bridge/pull/96) remains an unmerged draft when this increment is prepared. This source neither merges that branch nor changes its record.

## Invocation capability assessment

The author inspected available parent tool metadata without calling either existing connector. This session exposes the original Production and Dev bridge namespaces. No separately bound fixture connector or supported parent-to-new-connector invocation interface has been established here.
This observation is not raw protocol discovery, a health probe, proof of global unavailability or proof that a future supported interface cannot exist. No route/profile/key/connector was created, refreshed, retargeted or activated. Existing tool metadata is not permission to use an original connector as the test route.
The supported invocation path, actual independent authentication, identity/discovery capture method and finite client/cohort lifecycle remain HOLD. A local SDK call cannot satisfy that gate. The JSON-RPC-shaped data below is an offline validation contract, not a newly invented operational endpoint.

## Fixed source and schema manifest

Candidate remains `02d7e8bb1e1902ca33a574ab904a6e5b0f441785`. Behavioral fixture input remains PR #91 head `e7be0cc4e84b820eb8c7ac541325672d0f892fb2`. Candidate source, the 104-blob manifest, fixture, matrix and increment 1 are unchanged.
`discovery_manifest.json` records all 27 tool names and their inputSchema/outputSchema/annotations from an actual offline SDK stdio session against that pinned fixture. The new file is a separate discovery-schema baseline; it does not replace `candidate_manifest.json` or become a new candidate input.
The manifest's exact UTF-8 bytes include a final newline. SHA-256 is `ef081b19445fa9132f54f434254c04fbf4532b716ad1f994bbc1415261702ab9`. `identity_contract.py` checks that fixed digest and both source pins before producing request data. The read is capped at 65,537 bytes and a manifest symlink is rejected. This is integrity checking, not authentication or proof of independently observed source content.
No timestamp, state path, username, endpoint or credential is in the schema baseline. Transitive SDK/schema-generator changes may cause CI to fail; investigate such failures rather than accepting regenerated output automatically.

## Identity distinctions

The immutable candidate inherits version `1.2.8/v1.2.8`, build provenance `release`, embedded build input `887436f359683f0215f1993d7cb0c9035ec93571`, embedded schema 1 and reported default count 27. That inherited stamp does not mean the revised candidate is signed, released or deployed.
The fixture refuses operator configuration, so the reported config schema is `unknown`. The validator models two explicit source shapes:

| Source shape | Required report | Limit |
| --- | --- | --- |
| Pinned git checkout | source_kind git-worktree; source_revision exact candidate; revision_source git | A report is not independent verification of 104 file contents |
| No-.git tree | source_kind release-archive; source_revision inherited embedded input; revision_source embedded-build-input | The inherited revision does not identify the revised test tree or confer release status |

Fallback/unknown Git revision is not accepted for the git-checkout shape. Every version field must match, including numeric types; Boolean true does not substitute for schema 1. Independent management/source verification remains a separate B obligation. Version's count alone never completes discovery.

## Offline data state machine

`OfflineIdentityContract.request()` returns data bytes only. It first produces tools/call for bridge_version with empty arguments, then tools/list with exact cursor linkage. It never invokes an SDK, connector, backend or worker. The module has no CLI, credentials, network or process-control code.
`accept()` validates a supplied JSON-RPC-shaped reply against the pending integer id and protocol version. Duplicate keys, nonfinite/overflow numbers, error replies, unsolicited/duplicate replies, a second outstanding request and mismatched ids fail closed. It reuses increment 1's single UTF-8 newline frame limit of 65,536 bytes. At most eight discovery pages and 1 MiB combined request/reply data are accepted.
All 27 names must appear exactly once across the pages. Unknown/duplicate/missing tools, cursor cycles, malformed/bounded cursor violations and schema/annotation drift fail. Object key order and tool order do not change identity; array order and JSON value types remain significant. Tool title/description/presentation metadata are preserved as supplied, but are deliberately outside schema equality. This is a schema contract, not a claim that arbitrary presentation text is trusted.
Version content/metadata and full decoded tool entries are copied without rewriting. Results are always labeled `offline-identity-discovery-contract`. A successful hash/summary is not an approval token, live route proof or receipt, and does not enable the separate matrix runner. Request/accept failures latch the instance HOLD. There is no retry, timeout enforcement, transport, persistence or automatic stop action in this synchronous data validator.
The test envelopes are synthesized around SDK-decoded results or fabricated unit data. Their hash is not a raw-wire hash. Actual protocol capture/provenance and observation freshness require a separately reviewed collector and actual route approval.

## Validation and remaining gates

The new inventory has 13 offline checks. One uses actual SDK stdio for bridge_version and tools/list against a new synthetic fixture child, then closes/reaps that child. It submits no Hermes/Codex task and runs no matrix stimulus. The other checks cover both source shapes, exact field types, count-versus-discovery, pagination, schema/annotation drift, duplicate tools/cursors/ids, malformed frames, limits and manifest tampering. They do not simulate authenticated parent route success.
Dedicated CI retains selected-candidate 234/7, artifact 10 and parent-contract 16 checks on Python 3.12/3.14, then adds these 13 checks under the unchanged completed-output warning gate. Development full-suite failures documented in the original artifact remain history; no assertion is relaxed or warning suppressed.
Actual invocation/identity-discovery adapter, collectors/provenance, independent supervisor, exact PID/start identity, duplicate-launch prevention, private bounded trace/receipt persistence and operational stopped-writer proof remain outstanding. This is not a complete B implementation.
No new guest action or window, installation/authentication, connector setup/refresh or activation is authorized or performed. Original Production/Dev are untouched. Scoped section 22 and PR #80 remain HOLD; release/signing/publication/deployment remain separate.
