# Roadmap

## Approved maintenance target — v1.2.7 (released)

[Scope decision](V1.2.7-RELEASE-DECISION-TH.md) records operator approval at 18:47:56 +07 on 20 October 2026 for the reviewed Codex read-ahead fix and Context P1. Preparation, final-target signing/publication and production deployment require their separate steps. [Release preparation](V1.2.7-RELEASE-PREP-TH.md) stamps candidate 1.2.7/v1.2.7 with reviewed input `07ec0069b952f08a49adbd0ec778c204f85ee282`. Production remains signed v1.2.6; no signed tag/publication/deployment is performed. Dedicated read-only mount evidence and the existing P2/Hands/Events boundaries remain as documented.

Status update (20 October 2026): v1.2.7 is released via signed tag `625ea117aa693f577872638a6353b1408fb405aa`; the external fresh-input audit passed. The sentences above preserve the pre-release roadmap state. The deployment decision, including the not-deploy option, is pending; see the [release record](V1.2.7-RELEASE-RECORD-TH.md).

Deployment checkpoint (21 October 2026): production was upgraded from signed v1.2.6 to signed v1.2.7 on 21 October 2026 after the [deployment receipt](V1.2.7-DEPLOYMENT-TH.md) review PR #66 merged at `420fd76`. The deployment used no rollback and changed no config/state beyond the version switch. The pre-deployment sentences above preserve their historical state.

## Completed

- [x] v0.4.1 — WSL2 live acceptance for the Hermes and Codex paths
- [x] v0.5.0 — redacted audit logging, diagnostics, rotation/retention, and recovery visibility
- [x] v0.6.0 — per-workspace policy, approval TTL, prompt guardrails, and audit export
- [x] v0.7.0 — per-task Codex model and reasoning-effort policy
- [x] v0.8.0 — Codex process-lifecycle, timeout, cancellation, and concurrency hardening
- [x] v0.9.0 — operational state, configuration schema, and local-only heartbeat
- [x] v1.0.0 — production baseline, compatibility matrix, acceptance checklist, and release integrity
- [x] v1.0.1 — configuration/runtime alignment and watchdog documentation maintenance

### v1.2.0 — Independent read-only WSL2 Hands

- [x] Add an optional `hands` backend that initializes independently of Hermes health and Codex availability.
- [x] Keep the additive `hands` configuration block in schema version 1; Hands is disabled when the block is absent or `enabled=false`.
- [x] Add a canonical read-only workspace allowlist, protected-path rules, non-removable protected-filename patterns, and bounded list/read responses.
- [x] Add only three native MCP tools: `hands_health`, `hands_list`, and `hands_read`; discover them even while disabled and return a stable `disabled` result. The planned v1.2.0 discovery count is 22 tools (existing 19 + Hands 3).
- [x] Use descriptor-relative `openat2` with `RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS | RESOLVE_NO_MAGICLINKS` whenever the kernel/filesystem supports it. A configured workspace whose strict resolver self-test fails is unavailable; do not silently fall back to check-then-open.
- [x] Define conservative DrvFS behavior in v1.2.0: descriptor-based containment, case-folded protected-name matching, filesystem/mount reporting, and rejection of ambiguous case-colliding entries.
- [x] Reuse redacted rotating audit infrastructure without recording file content, secrets, or complete user payloads.
- [x] Add property-based path tests plus adversarial traversal, symlink-swap, protected-name, DrvFS case, binary, special-file, and size-limit tests.
- [x] Extend `bridge_status` and diagnostics with independent `hermes`, `codex`, and `local_hands` availability, without contacting a model for the Hands result.
- [x] Prove the critical fallback scenario in automated and WSL2 live acceptance: Hermes unavailable + Codex unavailable + Local Hands health/list/read functional.
- [x] Keep Hands disabled by default during upgrade; the installer must not invent readable workspaces.

## Deferred track — Hermes approval-event integration

`v1.1.0` remains reserved for Hermes API approval-event integration and is not on the active delivery path.

- [x] SSE transport POC against the installed API-server: `GET /v1/runs/{run_id}/events` returned authenticated `text/event-stream` frames for normal run events.
- [x] A terminal run before and after setting `approvals.mode: manual` did not emit an approval event or an exact approval request ID.
- [x] The API-server profile was confirmed to use `approvals.unattended_mode`, not the interactive approval flow.
- [ ] Do not implement SSE approval delivery, an approval MCP tool, or automatic approval responses until Hermes provides a documented interactive API approval contract.
- [ ] Re-open only after upstream demonstrates an approval event, stable exact request ID, reconnect semantics, expiry semantics, and a response contract; then repeat fake-server and WSL2 approval/deny/reconnect/expiry acceptance.

## Active roadmap — Hermes Local Hands

Local Hands adds deterministic local-computer primitives that ChatGPT can call directly. It is a sibling backend to Hermes and Codex, not a wrapper around either one.

Critical availability requirement:

> Local Hands MUST remain operational when Hermes or Codex is disabled, unavailable, rate-limited, or quota-exhausted. Its execution path MUST NOT invoke a Hermes model or Codex CLI.

The design, trust boundaries, proposed configuration, and tool contracts are in [LOCAL-HANDS-ARCHITECTURE-TH.md](LOCAL-HANDS-ARCHITECTURE-TH.md). The delivery sequence and acceptance matrix are in [LOCAL-HANDS-IMPLEMENTATION-PLAN-TH.md](LOCAL-HANDS-IMPLEMENTATION-PLAN-TH.md).


## v1.2.1 — Explicit work-context continuity

- [x] Add a local metadata-only context registry with opaque `context_id`; it never stores or replays prompts, outputs, credentials, or ChatGPT conversation state.
- [x] Bind a returned Hermes `session_id` to an explicit context after task status/result; a later `hermes_submit_task(context_id=...)` continues only that bridge-owned session.
- [x] Bind Codex workspace/job metadata to an explicit context without pretending that independent Codex CLI jobs are a resumable chat session.
- [x] Require `context_id` on every continued task; do not create a global active context or infer the latest session across chats.
- [x] Provide create/status/recent/close context tools and metadata-only audit events.

## v1.2.2 — Bridge version and provenance

- [x] Add one canonical embedded version/provenance source that is included in both Git worktrees and release archives; do not rely on `.git` or `git describe` at runtime.
- [x] Add a local-only `./bridge.sh version` command that reports bridge version, release identifier, embedded commit/build provenance, source kind (`git-worktree` or `release-archive`), config schema version, and MCP discovery count without calling Hermes, Codex, Tunnel, GitHub, or any network endpoint.
- [x] Add one additive read-only MCP tool, `bridge_version`, whose result matches the CLI contract and identifies the bridge instance actually reached through Secure MCP Tunnel. The planned discovery count is recorded in TESTING.md.
- [x] Define deterministic fail-safe behavior for absent, malformed, or development provenance: report explicit `unknown`/development fields without raising, guessing a release, or exposing filesystem paths, environment values, credentials, prompts, outputs, or audit content.
- [x] Keep update availability separate from local version reporting. Any optional GitHub release check must be an explicit future command with network behavior documented; `doctor`, `bridge_status`, and `bridge_version` remain local-only.
- [x] Add tests for release-archive metadata, Git worktree metadata, missing/malformed provenance, CLI/MCP equality, disabled upstreams, and the canonical discovery contract recorded in TESTING.md.
- [x] Update README, TESTING, UPGRADE, OPERATIONS, CHANGELOG, release status, and release runbook before tag; document that tests must use the project interpreter (`.venv/bin/python`) rather than a PATH-selected `python3`.
- [x] Run WSL2/Secure MCP Tunnel live acceptance: CLI and MCP version fields agree for the deployed candidate, remain available when Hermes/Codex are unavailable, expose no secret-bearing state, and restore the Dev config byte-for-byte after the temporary unavailable-upstream fixture.
- [x] Release completed through the existing Phase A/B/C process: documentation gate before signed tag, external `SHA256SUMS` asset verified after download, and post-tag release-record commit.

## v1.2.3 — Specification and worker-supervision maintenance

- [x] Add SPEC.md as the normative contract for architecture boundaries, MCP/CLI behavior, security invariants, persistence, recovery, testing, and release change control.
- [x] Implement the worker-only-loss rule: keep a job running while its Codex child is alive, expose only a redacted supervision hint, and remain fail-closed when the child later exits without a durable exit record.
- [x] Add regression coverage for worker/child liveness, cancellation, restart recovery, PID reuse, and unreaped zombie processes.
- [x] Run WSL2 live acceptance: confirm worker-loss supervision, fail-closed recovery after child exit, cancellation through the original process group, and a 75-test clean `ResourceWarning` regression run.
- [x] Complete independent review before the v1.2.3 release gates.
- [x] Complete the Phase A, Phase B, and Phase C release gates for v1.2.3.

## v1.2.4 — Maintenance release (OpenCode health adapter, legacy stdio discovery guard)

Release record (18 October 2026): PR #34 and PR #35 are merged at `0884482d8cf74d696b6c52a785282f65f2bd40fa` and are the only code surfaces in released v1.2.4 — the OpenCode health adapter (disabled by default; 27 tools default, 28 on opt-in) and the legacy stdio discovery guard. The capability-gated MCP Events track is not part of this release: originally planned as the v1.2.4 release target, it is deferred to the unversioned BLOCKED section below with no assigned release. Live Secure MCP Tunnel acceptance was executed on 18 October 2026 through the real Dev plugin route with a bounded pass — candidate identity, status, and tool visibility confirmed; the exact tunnel-side `server/discover` → `-32601` observation is not obtainable from the dispatcher log (no method names or outcome codes recorded) and remains an accepted limitation of this release. Record: [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md). No Local Hands mutation is in scope.

- [x] Prepare the local v1.2.4 release candidate: documentation gate, `version_info.py` stamp (reviewed build input `0884482d8cf74d696b6c52a785282f65f2bd40fa`), packaging regression test, and a verified local archive built per RELEASE-RUNBOOK-TH.md Phase B without tag, publish, or upload.
- [x] Run live Secure MCP Tunnel acceptance for the candidate before tagging (18 October 2026, real Dev plugin route; bounded pass recorded in [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md) — tunnel-side guard observation stays unproven from the dispatcher log; the SPEC.md section 17 acceptance mapping is unchanged).
- [x] Complete the release gates: final archive built from the signed tag `v1.2.4` (tag object `191ec44e979739659d042ff7306446a2db0639fc`, peeled `2133056`), published 18 October 2026 with the ZIP (SHA-256 `e6deb0e6ab16d669836b0e361e2e875858e19597ef35dc7e4fc19010a6a5f3a9`) plus an external SHA256SUMS asset, and the published assets re-downloaded and re-verified.

## v1.2.5 — released OpenCode task execution (SPEC.md section 18)

Status: implemented on `main` (merged by PR #40 at merge commit `a666d626`; final code head `e7add7e`) and released as signed **v1.2.5** on 19 October 2026 after PR #41. ZIP and external SHA256SUMS were downloaded and verified; production was upgraded to v1.2.5 on 2026-10-19 (identity/health/discovery verified read-only through the production plugin; see [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)). An explicit `opencode.execution` opt-in adds five tools (`opencode_submit_task`, `opencode_task_status`, `opencode_task_result`, `opencode_cancel_task`, `opencode_recent_tasks`; discovery 27 → 28 → 33) with a durable detached worker, bridge-owned sessions, idempotent submission, and native permission boundaries: no `--auto`, no bridge permission injection, workspace selection is a cwd allowlist and NOT isolation, `completed` never implies goal success, and `permission_required` requires an explicit protocol event — native permission replies and event subscriptions remain unsupported, and permission-required coverage stays fixture-only. Verified: 164/164 offline tests and CI at the code head, plus authenticated Dev Work-chat live acceptance on 19 October 2026 (records in [TESTING.md](TESTING.md) and [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md)). Released v1.2.4 remains health-only shipped. Details: [OPENCODE-TH.md](OPENCODE-TH.md).

## Deferred — Capability-gated MCP Events task-completion notifications (BLOCKED)

> Deferral note (18 October 2026): this track was originally planned as the v1.2.4 release target ("Capability-gated MCP Events task-completion notifications"). It is now deferred with no assigned release and remains BLOCKED at the subscription gate. The historical documents [V1.2.4-MCP-EVENTS-PROBE-TH.md](V1.2.4-MCP-EVENTS-PROBE-TH.md) and [V1.2.4-MCP-EVENTS-PLAN-TH.md](V1.2.4-MCP-EVENTS-PLAN-TH.md) keep their original v1.2.4 filenames and titles as evidence; those filenames remain valid links.

- [x] Instrument the Dev fixture with redacted method/outcome tracing and an empty `tools/list` handler. A repeat Dev probe recorded successful `server/discover`, `tools/list`, and `events/list`; the plugin page showed `bridge.probe.ready`.
- [ ] **Runtime track blocked before fixture subscription handling (4 October 2026):** two further Dev discovery sequences succeeded, but no `events/subscribe` reached the fixture in the supplied trace. Stop identical prompt retries. Reopen only after verifying client/workspace event-triggered task eligibility and capturing the protocol request; do not infer universal lack of Events support from a chat reply.
- [ ] **Runtime delivery remains gated:** require documented subscription, verified callback, signed event receipt, and unsubscribe before implementing persistent subscriptions or Hermes terminal delivery. User-directed explicit `hermes_task_status` polling remains available.
- [ ] Add an opt-in, webhook-only MCP Events capability for a subscribed Work chat to receive a redacted terminal-status event for a bridge-owned Hermes run.
- [ ] Keep the MCP discovery contract at 27 tools; event subscription methods are protocol capabilities, not ordinary MCP tools.
- [ ] Require MCP Events protocol 2.0, persistent subscription state, authenticated ownership/filter checks, expiry/refresh, callback challenge verification, signed delivery, retry, and bounded deduplication.
- [ ] Keep events disabled by default; do not send an outbound callback unless the operator explicitly enables the feature and the user has subscribed in ChatGPT.
- [ ] Permit callbacks only to a locally configured allowlist of exact hosts or host suffixes; the default allowlist is empty. Keep HTTPS/private-address/redirect defenses as additional checks, not as the primary authorization rule.
- [ ] Accept subscriptions only through an authenticated MCP Events protocol call following the user's Work-chat confirmation; never expose a model-callable tool or prompt-derived callback URL path.
- [ ] Never disclose callback URLs, signing secrets, prompts, outputs, credentials, or detailed paths through events, audit, diagnostics, or tool results.
- [ ] Deliver an event only after the bridge persists a recoverable Hermes terminal record; failed delivery must not change the run state or lose the result.
- [ ] Prove capability compatibility on Dev Secure MCP Tunnel before implementation. Do not replace unsupported events with hidden polling while calling it push notification.
- [ ] Complete fake-callback security tests, restart/expiry/dedup/retry coverage, and WSL2 Work-chat live acceptance before release.
- [ ] Add a regression proof for explicit-context Hermes follow-ups: the follow-up request contains only the persisted session identifier and input, never a new model/provider override; document that `reported_model` is observation metadata, not a model-selection channel.

## OpenCode adapter — health foundation (disabled by default)

- [x] Add a disabled-by-default `opencode` configuration section: `enabled` (`false` by default), an explicit absolute `binary` path, `version_timeout_seconds` (1-120, default 10), and `max_output_bytes` (1024-1048576, default 65536), with strict validation and unknown-key warnings.
- [x] Register the read-only `opencode_health` tool only when the section is enabled, so the canonical discovery contract stays at 27 tools until an operator enables it; prove both counts in tests.
- [x] Implement one bounded `--version` health probe: fixed argv with `shell` disabled, hard timeout, per-stream memory cap, and process-group cleanup with `SIGTERM` escalation to `SIGKILL`, including descendants that hold pipes or ignore `SIGTERM`.
- [x] Keep the probe leader unreaped until after the final group signal (review fix): exit is observed with nonreaping `os.waitid` (`WEXITED|WNOHANG|WNOWAIT`, Linux) bounded by the same overall deadline as the drain; `SIGTERM`, the grace wait, and `SIGKILL` all happen while the unreaped leader pins the PGID; the single reap follows the final `SIGKILL` by handle; unknown leader ownership sends no signal. Regression tests record the real signal/wait ordering on the success, nonzero-exit, timeout, and pipe-descendant paths.
- [x] Fail closed when disabled: no process spawn and no network, model, or authentication call. Sanitized errors do not include output, paths, environment values, or credentials.
- [x] Cover the foundation with offline fake-executable tests in `tests/test_opencode.py` and the enabled stdio fixture `tests/mock_opencode_server.py`.
- [x] Verify the probe against the real OpenCode CLI (`v2.0.32`) in a WSL2 live acceptance for the `--version` surface only (in-memory configuration, no settings change): `ok: true` with version `opencode v2.0.32`. This proves the version probe only; it is not acceptance for any other surface.
- [x] Implement the submission capability behind the separately gated `opencode.execution` opt-in (v1.2.5 release; see the section above). Native permission replies and event subscriptions remain unsupported: `permission_required` requires an explicit protocol event, the bridge never auto-approves, and no coverage beyond the fixture probe is claimed. Working directory and private server mode are not a sandbox; never pass `--auto`.

## Outstanding work before Local Hands mutation development (checkpoint 19 October 2026)

This checkpoint records outstanding work and existing gates as of 19 October 2026. It does not add new requirements.

Existing hard gate (already normative; not introduced here):

- v1.3.0 remains paused until the bridge establishes reliable, user-subscribed Hermes terminal-status delivery, and MCP Events stays BLOCKED at the subscription gate. [SPEC.md](SPEC.md) section 14 ("Local Hands mutation/execution remains deferred while this gate is evaluated") and the deferred MCP Events section above already state this.
- Per that section's recorded rule: stop identical prompt retries; reopen only after verifying client/workspace event-triggered task eligibility and capturing the protocol request. This records the existing reopen rule; it does not categorically prohibit future diagnostics or code changes on that track.

Requirements that already bind mutation work (existing, per [SPEC.md](SPEC.md), [SECURITY.md](SECURITY.md), and the v1.3.0 section below):

- Spec-first: a SPEC amendment is required before implementation is merged for the change classes listed in SPEC.md section 14.
- Approval stays local and digest-bound (ADR-0001 action digests), with no MCP approval tool.
- Any execution profile that claims no-delete/no-unapproved-truncate requires kernel-level enforcement that is probed at runtime (for example Landlock), and such a profile fails closed when enforcement is unavailable. This requirement does not make kernel enforcement a prerequisite for exact approved write/patch operations or for design work.

Follow-up status (not blockers; scoped separately from the hard gate above):

- [x] v1.2.5 artifact-chain audit closed on 19 October 2026. Maintainer automation and the external Hermes Agent review supplied by the operator both passed fresh tag/signature, asset/checksum/ZIP, byte-identical rebuild, ancestry, and offline identity checks. Review target: `c3754c9` ([PR #45](https://github.com/sc28249782/hermes-mcp-bridge/pull/45)). Record: [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md).
- SPEC §4/§10 privacy follow-up is closed under §19.4 following the operator-supplied external APPROVE of PR #54 at `7b2886d` on 20 October 2026. The [v1.2.6 deployment record](V1.2.6-DEPLOYMENT-TH.md) records the reviewed scope and limits. The operator approved deployment on 20 October 2026 at 13:52:34 +07; production now reports v1.2.6 and passed the scoped checks recorded there. Signed v1.2.6 and its assets passed maintainer post-download verification on 20 October 2026; the independent signed-release fresh-input audit passed in the operator-supplied external review of PR #53 at `88fb58f` on 20 October 2026 (fresh tag/assets, byte-identical rebuild, offline identity and extracted suite 184/184). The operator approved the v1.2.6 target scope on 20 October 2026; released v1.2.6 uses the 1.2.6/v1.2.6 stamp and reviewed build input `e3e698a7a220bf14a8bb4d1260bf2ded7e666b56`. Historical preparation gates: [V1.2.6-RELEASE-PREP-TH.md](V1.2.6-RELEASE-PREP-TH.md). Contract/implementation review passed in PR #47. Scoped Dev transport acceptance, metadata-cap fault injection, approval-shape checks and restoration passed with external review in PR #48/#49; PR #49 code head `f570d03` passed WSL 184/184 tests. Approved v1.2.6 scope and remaining gates: [PRIVACY-RELEASE-DECISION-TH.md](PRIVACY-RELEASE-DECISION-TH.md). Production is unchanged by these PRs. Earlier evidence and its limits remain in [PRIVACY-DEV-ACCEPTANCE-TH.md](PRIVACY-DEV-ACCEPTANCE-TH.md) and [PRIVACY-BOUNDARY-ACCEPTANCE-TH.md](PRIVACY-BOUNDARY-ACCEPTANCE-TH.md).
- Production OpenCode benign-model acceptance passed on 20 October 2026 through the production connector: two completed jobs in one session, exact text, resume without the expected token in the second prompt, idempotent replay and pagination. See [OPENCODE-PRODUCTION-ACCEPTANCE-TH.md](OPENCODE-PRODUCTION-ACCEPTANCE-TH.md). This closes the benign-model follow-up only; it does not establish production write/cancel/native-permission acceptance. Earlier Dev and deployment checkpoints keep their original scope.

Scoped work and proposals awaiting decisions:

- Context P1 scope approved by the operator on 20 October 2026 at 15:57:29 +07 after PR #57 review/merge. [SPEC §20](SPEC.md#20-context-p1--v127-target-scope-approved-released) defines the warning and read-only-preview amendment for review before implementation. PR #58 merged the reviewed amendment at `64eb0a1` before implementation. PR #59 passed operator-supplied external APPROVE at `b7ff97a` and merged at `5685e11`, with [synthetic acceptance](CONTEXT-P1-ACCEPTANCE-TH.md). [Scoped live Dev aggregate acceptance and restoration](CONTEXT-P1-DEV-ACCEPTANCE-TH.md) passed at candidate `27030bb` on 20 October 2026; the operator supplied external APPROVE for PR #61 at `6d93808`, merged at `4513b30`. Dedicated read-only mount testing remains unperformed. P1 is unreleased/undeployed; P2 apply/delete remains deferred pending lifecycle/concurrency design. [Decision and scope](CONTEXT-RETENTION-SCOPE-TH.md). This concerns metadata rows, not ChatGPT/model token history. (21 October 2026 checkpoint note: P1 shipped in v1.2.7 and was deployed on 21 October 2026; see the [deployment checkpoint](#deployment-checkpoint-21-october-2026) above.)
- Context P2 lifecycle/concurrency design proposal (21 October 2026): [CONTEXT-P2-LIFECYCLE-DESIGN-TH.md](CONTEXT-P2-LIFECYCLE-DESIGN-TH.md) proposes close/bind/submit linearization, reconciliation after backend acceptance, and the deferred P2 apply/delete boundary. It is a proposal pending review — not an implementation authorization — and it does not change P1 values, tools, schema, or discovery counts.
- Context lifecycle decision packet (21 October 2026): [CONTEXT-LIFECYCLE-DECISION-PROPOSAL-TH.md](CONTEXT-LIFECYCLE-DECISION-PROPOSAL-TH.md) records recommendations with alternatives for the five open §9 decisions and DRAFT (not-effective) amendment wording, including the additive binding-outcome field proposal. It is pending operator decision and a separate SPEC §14 amendment PR; nothing in it is implemented, approved, or effective, P2 apply/delete remains deferred, and P1 values/discovery labels (27 default / 28 health-only / 33 execution) stay unchanged.
- Context lifecycle SPEC amendment (21 October 2026): the operator approved D1–D5 as recommended (recorded in the decision packet after the PR #68 merge at `926a362`). The approved contract is recorded as [SPEC §21](SPEC.md#21-context-lifecycle--closed-binding-outcome-approved-design-implementation-not-started) (conditional registry mutation with commit linearization, unchanged close/bind errors, and the additive `context_binding` closed-rejection submit outcome). The amendment is proposed for section 14 review in this PR; implementation is not started and requires that review to merge first. No release is assigned, P2 apply/delete remains deferred, and P1 values/schema1/discovery counts are unchanged.
- Context lifecycle implementation (21 October 2026): SPEC §21 is implemented in a runtime PR pending review — conditional atomic registry mutations, the typed `ContextClosedError`, the one-row `observe_hermes` guard, and the §21.2 closed-binding submit outcome, with the deterministic §21.3 test matrix in `tests/test_context_lifecycle.py`. Status: implemented, pending review; not released, not deployed, and no external acceptance is claimed. No release is assigned; P2 apply/delete remains deferred; discovery 27 (default) / 28 (OpenCode health-only) / 33 (OpenCode execution) and P1 values are unchanged. Implementation evidence is recorded in [TESTING.md](TESTING.md#unreleased--context-lifecycle-closed-binding-outcome-spec-21).
- Context lifecycle scoped Dev acceptance (21 October 2026): PR #70 merged at main `227f2ad1f43ff64c6c4866595c9ea705fd7977b3` (review head `07bfe82`) and the scoped synthetic Dev acceptance was performed. The acceptance used a test-only fixture that ran the production `server()` and `ContextRegistry` code paths over the real Dev tunnel with a mock-transport Hermes acknowledgement and a stub Codex backend; a parent connector verified identity, counters, and lifecycle responses before an argv-verified restore to the Dev baseline `1.2.4`/`e7add7e`. The acceptance is mock-backend evidence, not real-backend acceptance. Status: accepted on the synthetic fixture; not released, not deployed. No release is assigned; P2 apply/delete, the submit-admission and crash-between-submit-and-bind gaps, and the non-closed binding ack/recovery gap remain open. Evidence classes and limits are recorded in [TESTING.md](TESTING.md#scoped-synthetic-dev-acceptance-21-ตุลาคม-2026) and the [acceptance record](CONTEXT-LIFECYCLE-DEV-ACCEPTANCE-TH.md).
- Release readiness proposal v1.2.8 (21 October 2026): [V1.2.8-RELEASE-DECISION-PROPOSAL-TH.md](V1.2.8-RELEASE-DECISION-PROPOSAL-TH.md) proposes a narrow SPEC §21-only maintenance release (code delta = `contexts.py`, `bridge.py`, `tests/test_context_lifecycle.py` only, verified against the signed `v1.2.7` tag) with all deferrals preserved (P2 apply/delete, Hands v1.3.0, MCP Events) and schema 1 / discovery 27/28/33 unchanged. The packet is a **PROPOSAL pending operator scope decision**: the name `v1.2.8` is proposed only (checked unused, not assigned), no stamp, archive, tag, publication, or deployment is performed by the packet, the defer/not-deploy option with the v1.2.7 rollback baseline is recorded, and Phase A/B/C plus the separate deployment decision gate follow the [release runbook](RELEASE-RUNBOOK-TH.md).
- v1.2.8 scope approved; Phase A preparation (21 October 2026): the operator selected option ก — approve the v1.2.8 scope and start Phase A — in chat on 21 October 2026 (no exact timestamp is available in the message, so none is recorded). PR #72 merged at main `887436f359683f0215f1993d7cb0c9035ec93571` (reviewed head `4f09b44774f6075723f381675d5fee1e356289f2`, CI success). Phase A preparation stamps the candidate `1.2.8/v1.2.8` with that reviewed build input; status at that time was tag pending — not signed, published, or deployed, and production remains signed v1.2.7 (deployed 21 October 2026). Evidence is recorded in [V1.2.8-RELEASE-PREP-TH.md](V1.2.8-RELEASE-PREP-TH.md); signing/publication stay with the operator per the runbook.
- v1.2.8 released (22 October 2026): the operator merged PR #73 and signed/pushed annotated tag `v1.2.8` (object `bb2f076bb3fd665950551ca613abb6ce6fb8f809`, peeled commit `1ae159031a53e4e5359fd39e61b2748159149a52`); Phase B built release assets from the signed tag (ZIP SHA-256 `8f8ea06e6df6060062547f05a480552cce713b2effffa8826876bb0053899db8`, 438,643 bytes) and passed maintainer-side suite/identity/post-download verification; the external fresh-input audit passed (APPROVE at PR #74 head `cddcdb5`), production remains signed v1.2.7, and the deployment decision is separate. Evidence: [V1.2.8-RELEASE-RECORD-TH.md](V1.2.8-RELEASE-RECORD-TH.md).
- v1.2.8 deployment decision packet (22 October 2026, post PR #74): [V1.2.8-DEPLOYMENT-DECISION-TH.md](V1.2.8-DEPLOYMENT-DECISION-TH.md) proposes the two acceptable choices (deploy per the staged plan / not-deploy and keep signed v1.2.7) with target/baseline pins, read-only preflight findings, quiescence and control-plane handoff rules, scoped post-switch acceptance and rollback triggers. It is a proposal — no deployment approval or runtime change has occurred.
- v1.2.8 deployed (22 October 2026): the operator approved merge and option ก in chat («merge และ ก: deploy v1.2.8 ตามแผนและผ่านทุก gate», 22 October 2026, no exact timestamp recorded); PR #75 merged the packet at main `0d9174e9fcdffeb02c7b287c448153d29290cdb7`, and the deployment followed the staged plan the same day: full metadata-only quiescence inventory (no active/nonterminal job; the single persisted `unknown_exit` codex row is a terminal lifecycle by implementation with a durable finished record and its recorded worker/child PIDs verified absent — outcome stays unknown, DB unchanged), 16/16 quiescent state-copy hash match before start, exact-identity stop, no config/permission/schema change, and the scoped §21 isolated suite 21/21 on the deployed Python 3.12.3 (ResourceWarning-as-error). Parent live verification through the production connector confirmed identity/health/registry/Hermes auth (runs 263, watchdog interval 15, soft_cap 1,000/rows_lower_bound 4) with Hands disabled and Dev unchanged at 1.2.4 (`e7add7e…`); the connector inventory (33 tools) is not a raw wire `tools/list` capture. The pre-deployment sentences above preserve their historical state. See the [deployment record](V1.2.8-DEPLOYMENT-TH.md).
- Nonclosed binding ack/recovery decision packet (22 October 2026): [CONTEXT-BINDING-ACK-RECOVERY-PROPOSAL-TH.md](CONTEXT-BINDING-ACK-RECOVERY-PROPOSAL-TH.md) proposes alternatives for the nonclosed binding error gap left open by SPEC §21.2 — preserve the existing error with documented manual recovery (recommended, narrowest) versus an additive explicit nonclosed binding outcome after a successful backend acknowledgement only. It is a **PROPOSAL awaiting operator decisions**; no SPEC change, implementation, schema migration, or release/deploy is authorized by it, and the deferred gaps (submit admission, crash-between-submit-and-bind, uncertain replay, durable intents, P2 prune, Hands, Events) remain deferred.
- Unresolved binding outcome SPEC amendment (22 October 2026): after the packet above passed external APPROVE at head `2730f224516eb32b2717e1293cec986e2a185941`, the operator selected option ข (verbatim approval and no-timestamp disclosure in the [packet checkpoint](CONTEXT-BINDING-ACK-RECOVERY-PROPOSAL-TH.md)). [SPEC section 22](SPEC.md#22-context-binding-unresolved-proposed) is opened as a PROPOSED amendment in a stacked draft PR that depends on PR #77: a scoped `binding_unresolved` outcome after a successful backend acknowledgement, with an ordered catch policy and an explicit residual gap. It is **PROPOSED pending section 14 review and merge of both PRs**; deployed v1.2.8 behavior is unchanged; no implementation, release, or deployment is authorized.
- Unresolved binding outcome runtime implementation (22 October 2026): the SPEC §22 amendment passed section 14 review and merged via PR #78 at main `4ed8765` together with the PR #77 merge `e18d0d4`. The runtime implementation is pending review in a runtime PR: the ordered, closed catch policy wraps only the registry binding call (`closed_rejected` unchanged; `sqlite3.OperationalError` and `ContextError` become `binding_unresolved` with the exact note and the full backend acknowledgement preserved), with the deterministic §22.5 matrix in `tests/test_context_binding_unresolved.py`. Status: implemented, pending review; not released, not deployed; no acceptance is claimed and no release is assigned; the residual gap and deferred gaps stay unchanged. Evidence: [TESTING.md](TESTING.md#unreleased--unresolved-binding-outcome-after-acceptance-spec-22).

- Missing terminal record disposition proposal (22 October 2026): [MISSING-TERMINAL-DISPOSITION-PROPOSAL-TH.md](MISSING-TERMINAL-DISPOSITION-PROPOSAL-TH.md) records two operator choices: keep HOLD, or authorize a separate SPEC/operations design for a scoped operational disposition while the task outcome remains unknown. It uses the existing diagnosis in draft PR #80 (24 runs with terminal evidence / 1 unresolved); no new probe or runtime action is performed. The proposal does not adjudicate a run, change a gate, authorize acceptance, or approve implementation. PR #80 remains HOLD; the operator choice is pending.

- Missing terminal disposition amendment proposal (22 October 2026): the operator selected option ข (verbatim in the [packet checkpoint](MISSING-TERMINAL-DISPOSITION-PROPOSAL-TH.md)). [SPEC §23](SPEC.md#23-missing-terminal-operational-disposition-proposed) and the operations appendix propose a manual-only, one-scope disposition with positive authority/cessation evidence, private immutable dossier, live local approval, expiry and one-use control. Pending section 14 review/merge; no case is adjudicated, no gate is released, and PR #80 remains HOLD. No runtime action, implementation, or acceptance repeat is authorized.

ข้อความอนุมัติจาก operator (verbatim จากแชตวันที่ 21 ตุลาคม 2026):

> ก: อนุมัติ scope v1.2.8 และเริ่ม Phase A

ไม่มีเวลาที่แน่นอนในข้อความ จึงไม่สร้าง timestamp เพิ่มเติม. ข้อความนี้อนุมัติ scope และการเริ่ม Phase A; ไม่ใช่การอนุมัติ signing/publication หรือ deployment.

- Observation annotations and an observation counter remain separate proposals awaiting scoping.

Optional follow-ups, lower priority:

- Capture a raw wire `tools/list` on the production route in a future maintenance window; the 19 October 2026 production evidence for 33 tools is a parent-side registry count, not a wire capture.
- The recorded v1.2.4-era limitations (tunnel-side `server/discover` → `-32601` unobservable from the dispatcher log; permission-required coverage fixture-only) stay accepted as documented; revisit only when those surfaces change.

## Deferred — v1.3.0 Approval-bound mutation and execution

> v1.3.0 is intentionally paused until the bridge establishes reliable, user-subscribed Hermes terminal-status delivery — a capability requirement (the deferred, BLOCKED MCP Events track above has no assigned release), not a dependency on any numeric version. No Local Hands mutation or execution capability is in the v1.2.4 maintenance-release scope. The v1.2.5 release contains only the OpenCode execution opt-in (PR #40); v1.3.0 stays reserved for the Local Hands deferred track.

- [ ] Add `hands_write`, `hands_patch`, `hands_exec`, and `hands_process` after v1.2.0 read-only live acceptance and feedback.
- [ ] Implement canonical action digests exactly as [ADR-0001](adr/0001-local-hands-foundation.md) specifies: versioned deterministic JSON bytes plus SHA-256, immutable persisted payload/blob reference, TTL, one-time use, and revalidation at execution.
- [ ] Require local human approval for writes, patches, content-bearing execution, and all trusted-workspace-code execution; expose no MCP approval tool.
- [ ] Bound pending actions globally and per workspace; reject new actions at the cap and audit only redacted metadata.
- [ ] Keep execution fixed-argv with `shell=False`; do not accept unrestricted shell/PowerShell command strings.
- [ ] Make generic deletion, unlink, rmdir, unapproved truncation, and destructive rename a non-overridable baseline deny. Do not expose a generic delete tool; exact approved write/patch remains a separate digest-bound operation.
- [ ] Enforce no-delete/no-unapproved-truncate execution at kernel level with a runtime-probed mechanism such as Landlock; Landlock starts with Linux 5.13 but availability/configuration/ABI must be probed rather than inferred from the kernel version or WSL2 label. Required profiles are unavailable when enforcement is insufficient.
- [ ] If a move operation is added, make it a dedicated exact-source/destination no-clobber operation; never implement it as arbitrary `mv` argv.
- [ ] Treat Git, CMake, test runners, interpreters, hooks, build rules, response files, and config-file indirection as trusted-workspace-code execution, not as safe merely because the executable is allowlisted.
- [ ] Permit no-approval profiles only when output is metadata-only and argv is exact/constrained; `git diff` is content-bearing and is not read-safe.
- [ ] Persist process output as bounded JSONL per process and persist lifecycle state with ownership, timeout enforcement, cancellation, and safe restart recovery.
- [ ] State explicitly that executable output is workspace-controlled content sent to ChatGPT and may contain secrets; filename protection cannot make command output secret-safe.
- [ ] Add Windows-to-WSL and WSL-to-Windows path translation as an internal helper; translation must not weaken canonical containment checks.

## v1.4.0 — Windows Host Adapter

- [ ] Add `hands_windows` as an optional adapter invoked from WSL2 through a fixed executable path and fixed argv, with PowerShell script policy disabled by default.
- [ ] Support bounded, policy-scoped read operations for processes, services, event logs, networking, filesystem metadata, and clipboard metadata before enabling mutations.
- [ ] Add Windows path canonicalization that handles drive letters, UNC rejection by default, reparse points, case-insensitive comparisons, and WSL mount translation.
- [ ] Add separate allowlists for Windows commands, service names, process actions, and accessible roots; do not inherit WSL permissions implicitly.
- [ ] Require local approval for service/process mutation, clipboard content access, Windows writes, and script execution.
- [ ] Add Windows-specific audit fields without recording clipboard contents, script bodies, credentials, or command output.
- [ ] Validate with Windows 11 + WSL2 under both `virtioproxy` and documented compatible networking modes; Hands must not require mirrored networking.

## v1.5.0 — Windows Computer Use

- [ ] Hard gate: do not start computer-use implementation until v1.4.0 Windows Host passes live acceptance and a recorded security review.
- [ ] Ship an observe-only vertical slice first, then bounded click in a disposable test application; typing remains disabled until a separate review and acceptance gate passes.
- [ ] Add one compact `hands_computer` tool with staged actions such as `observe`, then `click`; later actions such as `type`, `key`, `scroll`, `drag`, `open`, and `wait` require their own policy/review.
- [ ] Implement a signed/versioned Windows helper using supported Windows capture and UI Automation APIs; keep it bound to the local machine and authenticate WSL2 requests.
- [ ] Enforce a window/application allowlist, foreground-window verification, coordinate bounds, stale-observation rejection, and per-action timeouts.
- [ ] Add bounded post-action observation with screen-change signal, app/window revalidation, expected-state predicate, and `verification_inconclusive` when success cannot be proved.
- [ ] Refuse password, PIN, MFA, credential-manager, secure-desktop, UAC, payment, and other protected-field interaction.
- [ ] Include normalized English/Thai defense-in-depth markers: `password`, `passcode`, `pin`, `otp`, `mfa`, `2fa`, `verification code`, `security code`, `รหัสผ่าน`, `รหัส`, `พิน`, and `โอทีพี`; accessibility secure-field metadata remains authoritative where available.
- [ ] Require approval for high-impact UI actions and never infer approval from visible page text or model output.
- [ ] Treat screenshots, OCR, accessibility trees, and application text as untrusted input and document prompt-injection handling.
- [ ] Provide an emergency stop and visible local activity indicator; cancellation must prevent queued follow-up UI actions.
- [ ] Run live acceptance first against disposable applications and fixtures, never a maintainer's real credential or payment workflow.

## v1.6.0 — Routing, fallback, and operational hardening

- [ ] Publish a capability contract that lets ChatGPT choose Hermes, Codex, or Local Hands without circular orchestration.
- [ ] Report normalized backend reasons such as `available`, `disabled`, `unreachable`, `usage_limit`, `quota_exhausted`, and `policy_blocked` without exposing secrets.
- [ ] Document direct routing: short deterministic work to Hands, coding work to Codex, and long agentic work to Hermes; Hands itself never delegates back to an agent.
- [ ] Add cross-backend correlation IDs for audit only; never share prompts, outputs, credentials, or approval authority across backends.
- [ ] Add load, restart, expiry, cancellation-race, disk-full, truncated-output, and audit-rotation tests for all Hands adapters.
- [ ] Complete threat-model review, upgrade/rollback instructions, compatibility matrix, operations runbook, and a signed release acceptance record.

## Release gates applying to every Local Hands version

- Documentation, version references, tool counts, configuration examples, tests, checksums, and release notes must be updated before tagging or publishing release assets.
- Attribution and `THIRD_PARTY_NOTICES.md` must be reviewed before release; any future Endeavor Hands source adaptation must preserve its copyright and MIT notice.
- New mutation capabilities ship disabled by default and require explicit local policy.
- No backend may approve its own action or obtain approval through MCP.
- No credential value, file content, prompt, command output, screenshot, or clipboard content may enter audit logs.
- Unit tests and fake adapters are necessary but do not replace WSL2/Windows live acceptance.
- Release archives and checksums must be generated from the signed release commit and verified after download.

## Non-goals

- A public inbound service, unrestricted remote shell, unrestricted filesystem/network access, or generic remote-desktop product
- Replacing ChatGPT reasoning with a local model; Local Hands still requires an active ChatGPT/MCP session for interactive use
- Making Hands available when the bridge, tunnel, ChatGPT session, WSL2, or required local helper is unavailable
- Transmitting Hermes, OpenAI, Windows, SSH, cloud, browser, or signing credentials through MCP
- Letting an agent approve its own action, weakening Codex approval rules, or reusing Hermes approval authority
- Parsing arbitrary shell/PowerShell text and attempting to infer safety from keywords alone
- A deny-list sandbox with allow-by-default semantics, model-relayed nonce as authorization, read-anywhere filesystem policy, or dynamic MCP-to-MCP trust bypass
- Treating fixed argv, an exact entrypoint/cwd, or model-managed delegation as sufficient authority to bypass the Local Hands policy engine
- Multi-user credential management, payment automation, secure-desktop control, or unattended credential entry


- Python 3.14 truncate-race: root cause reproduced as binary read-ahead. The unreleased candidate uses unbuffered Codex result reads to enforce the existing snapshot budget. A new regression also detects append read-ahead beyond the snapshot on 3.12.3 and 3.14.7; WSL candidate suites pass 185/185 on each. See [TESTING.md](TESTING.md#unreleased--codex-result-read-ahead-fix). Investigation/fix merged in PR #56 at `e24fa3e`; no release/deployment is assigned. Production stays on signed v1.2.6/Python 3.12.3.


- Missing terminal evidence assessment (22 October 2026, after PR #82 merge `3f1aab78`): the amendment review/merge prerequisite has passed. The [initial documentary assessment](MISSING-TERMINAL-EVIDENCE-ASSESSMENT-TH.md) maps the existing PR #80 diagnosis to section 23.2. Positive authority cessation and complete writer coverage are not established; the case and PR #80 remain HOLD. No fresh local probe, disposition, maintenance, or acceptance repeat is claimed or authorized. Earlier proposal checkpoints retain their historical wording.


- Separate §22 acceptance environment proposal (22 October 2026, after PR #83): [decision packet](S22-SEPARATE-ACCEPTANCE-DECISION-TH.md) offers defer versus feasibility design for a disposable, independently controlled test environment. No option is selected. Isolation, ownership coverage, route availability, and contract compatibility are unverified; no setup, connector change, acceptance repeat, gate exemption, disposition, release, or deployment is authorized. PR #80 remains draft and HOLD.


- Separate §22 feasibility design (22 October 2026): the operator selected ข (verbatim in the [packet checkpoint](S22-SEPARATE-ACCEPTANCE-DECISION-TH.md)). The [public design](S22-SEPARATE-ACCEPTANCE-FEASIBILITY-TH.md) defines the resource/authority evidence required for an unselected environment; no local infrastructure inventory is published. No boundary, independent route, setup or activation is claimed verified. PR #84 remains unmerged; this design is stacked on its reviewed head. No provisioning, acceptance repeat, historical disposition, release or deployment is authorized; PR #80 remains draft/HOLD.


- Shared-host synthetic §22 proposal (23 October 2026): after directional agreement to draft a revised trust model, [SPEC §24](SPEC.md#24-shared-host-synthetic-acceptance-proposed) proposes treating operator-controlled host management as trusted for a separately approved fixture-only plan. This explicitly changes the PR #84/#85 two-way-isolation prerequisite; it does not claim that prerequisite passed. [Proposal record](S22-SHARED-HOST-ACCEPTANCE-PROPOSAL-TH.md) retains interference/integrity/resource gates, separate setup/acceptance review and unchanged §23 case-disposition controls. Pending §14 review/merge; no execution authorized; PR #80 remains HOLD.


- Shared-host §22 setup/acceptance plan proposal (23 October 2026, after PR #86 merge `51a35d1a`): [S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md](S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md) proposes A-only guest/artifact preparation and separately approved B connector/activation. Exact private bindings, reviewed harness pins, budgets, integrity and continuity gates must pass before use. No setup, connector, SSH login or acceptance run is authorized or performed; PR #80 remains HOLD; release/deployment stay separate.


- SPEC §24 Phase A source artifact (23 October 2026): [acceptance/s24](../acceptance/s24/README.md) contains a pinned candidate manifest, synthetic-only server/driver and separate artifact checks. A-only approval is quoted in the artifact README. Expected successful matrix totals are defined before B: contexts 18 (2 closed / 16 open, 7 bound), Hermes registrations/POSTs 10, memory-only Codex submits 10, audit 30 = 18 create + 2 close + 10 submit. Development offline checks do not establish guest readiness or live acceptance. Guest measurements, independent artifact review/pin, private bindings and separate B approval remain outstanding; PR #80 remains HOLD.

- SPEC §24 Phase A input decision proposal (23 October 2026): [S22-PHASE-A-INPUT-DECISION-TH.md](S22-PHASE-A-INPUT-DECISION-TH.md) proposes a 104-file input derived from the original pin with only PR #89's SQLite test cleanup. Effective candidate/manifest remain unchanged; input choice, coupled manifest review and guest execution scope remain separate. Original guest warnings remain evidence; Phase A is incomplete, B and PR #80 remain HOLD.
