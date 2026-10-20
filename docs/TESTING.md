# Validation record — v1.2.5 released (2026-10-19)

## v1.2.6 release candidate — unreleased privacy hardening (SPEC §19)

Current checkpoint (20 October 2026): the operator approved the v1.2.6 scope. External review of PR #48/#49 accepted the scoped Dev records and restoration. PR #49 code head `f570d03` passed WSL 184/184 and focused privacy 19/19; its boundary/approval results and limitations are in [PRIVACY-BOUNDARY-ACCEPTANCE-TH.md](PRIVACY-BOUNDARY-ACCEPTANCE-TH.md). The dated checkpoints below retain the preparation-stage evidence and pending status as written at that time. The 1.2.6/v1.2.6 release candidate uses reviewed build input `e3e698a7a220bf14a8bb4d1260bf2ded7e666b56`. Exact candidate WSL/archive/CLI-MCP/discovery checks must have a receipt in the release-preparation PR before merge; see [V1.2.6-RELEASE-PREP-TH.md](V1.2.6-RELEASE-PREP-TH.md). Prior counts in this paragraph apply to `f570d03`; the new receipt must identify its own tested head. No production acceptance is claimed. See [PRIVACY-RELEASE-DECISION-TH.md](PRIVACY-RELEASE-DECISION-TH.md).

Dev transport fixture checkpoint (19 October 2026, ~21:11 +07): parent called the actual Dev connector at `db009682`; filtered status metadata was 416 bytes, explicit result pagination matched all 29 characters, unknown-run ownership was denied, and an identical retry returned the existing run. The parent registry exposed 27 tools; no raw wire discovery or live 28/33 proof is claimed. This used in-process fake Hermes transport, not actual Hermes HTTP/native approval/model execution. Codex bounds and mode repair remain WSL filesystem-test evidence. Restoration was verified through the Dev connector at `e7add7e`: schema 1, original state mode 0700, zero Hermes/Codex registrations, running watchdog, Hands disabled and empty Hermes/Codex recent lists. OpenCode job count was not rechecked because its recent tool was absent from the parent registry. Acceptance-record review remains pending: [PRIVACY-DEV-ACCEPTANCE-TH.md](PRIVACY-DEV-ACCEPTANCE-TH.md).

WSL preparation checkpoint (19 October 2026): isolated candidate `db009682` passed 183/183 full-suite tests in its own venv, 18/18 privacy regressions and shellcheck. Local SDK stdio fixture discovery was 27; status metadata was 415 bytes with filtered approval/error. This supplements the earlier host limitation below; it is not live Dev transport evidence. Operator handoff: [PRIVACY-DEV-ACCEPTANCE-TH.md](PRIVACY-DEV-ACCEPTANCE-TH.md).

- `tests/test_privacy_hardening.py`: 18 process-free synthetic regressions cover metadata allowlists, numeric/size limits, exact local approval, legacy key exclusion, timeout/error behavior, existing-directory enforcement and failures, bounded snapshot reads, Unicode/newlines/invalid UTF-8, sparse/oversize logs, append/truncate races and read-budget assertions.
- `tests/test_mcp.py::test_privacy_metadata_is_bounded_on_real_stdio` checks the actual SDK stdio boundary with fake Hermes data. It verifies no raw approval/error fixture reaches metadata and discovery remains at the canonical default.
- Focused local suite: 40/40 pass with the project venv and `-W error::ResourceWarning` (`test_privacy_hardening`, `test_bridge`, `test_mcp`). No real model/provider call is made.
- Four pre-existing Codex process/identity tests fail in this execution environment on both baseline and candidate: unreaped-zombie detection, detached-approver result, model override forwarding, and fixed-argv result capture. The baseline comparison also failed to obtain a start-ticks identity. These are not counted as passing local full-suite evidence. Exact-head Linux CI must pass the full suite and shell checks; its result is recorded on the candidate PR.
- External review supplied by the operator on 19 October 2026 approved `c14cd8c` ([PR #47](https://github.com/sc28249782/hermes-mcp-bridge/pull/47)). The reviewer reported 183/183 tests on a clean worktree, independent metadata/directory/Unicode/read-limit probes, and exact-head CI `39260476787` passing. This supplements, and does not replace, the local-environment limitation recorded above.
- This is fixture acceptance, not production or Dev rollout acceptance. Signed v1.2.5 evidence below remains historical and unchanged.

## v1.2.4 candidate gates (historical pre-tag record; v1.2.4 released 2026-10-18)

> สถานะอัปเดต (18 ตุลาคม 2026): v1.2.4 เผยแพร่แล้วผ่าน signed tag พร้อม release assets ที่ตรวจแล้ว (ดู [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)) ข้อความ "not published, not installed" และรายการ "Pending: live Secure MCP Tunnel acceptance" ด้านล่างคงไว้เป็นหลักฐานก่อน tag ตามเดิม; live tunnel acceptance เกิดขึ้นจริงในวันเดียวกันเป็น bounded PASS บน Dev route (ดู [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md))

- Offline suite: all tests pass with the project-interpreter recipe below (`env -u PYTHONPATH`, `-W error::ResourceWarning`), including the 13 stdio-guard tests and the new packaging tests; `bash -n install.sh bridge.sh tunnel.sh` and `shellcheck -S warning install.sh bridge.sh tunnel.sh` pass.
- Local archive candidate verification (Phase B minus tag/publish): ZIP structure test, exclusion check (no `.venv/`, `state/`, `.env`, `bridge-config.json*`, `.git/`, `__pycache__/`), re-extraction, `./bridge.sh version` from the extracted tree, and the extracted-tree stdio fixture probe (pre-init `server/discover` → `-32601` with the same id, no params echo, no log flood; `initialize` → `tools/list` = 27 tools; EOF → exit code 0). No real Hermes/Codex/OpenCode/provider call is made.
- The optional 28-tool discovery is proven inside the suite by `tests/mock_opencode_server.py` with `tests/test_opencode.py`; the default and canonical count remains 27.
- `tests/test_packaging.py` (new): derives `bridge.py`'s real root-module import surface and proves `opencode_core.py`, `stdio_guard.py`, and the three stdio fixture servers are present and git-tracked. `install.sh` runs from the extracted `git archive` and copies nothing, so an untracked module would silently break the release archive.
- Pending: live Secure MCP Tunnel acceptance. Until it passes, the candidate is implemented and tested, not accepted and not released.

## v1.2.3 release record (2026-10-04)

Target contract reviewed: Hermes v0.21.1, commit 8d79c2ff.

## MCP tool contract (canonical count)

The normative bridge contract is defined in [SPEC.md](SPEC.md). The canonical discovery contract is **27 tools** (unchanged since v1.2.2: v1.2.1's 26 plus local-only `bridge_version`); it becomes 28 tools when only `opencode` health is enabled. The section 18 execution opt-in (v1.2.5 released) adds five more tools for 33; this does not change the released v1.2.4 contract. Other documents should refer here instead of maintaining an independent count. `bridge_version` and `./bridge.sh version` must agree on shared identity fields and must not contact Hermes, Codex, Tunnel, GitHub, or another network endpoint.

## Current context and Hands coverage

- `tests/test_hands.py` covers disabled stable results, additive schema validation, dependency direction, workspace secret-name protection, protected-name case folding, traversal, symlink escape, binary/oversize/hard-link rejection, case-colliding entries, strict-resolver failure, and audit content/path non-leakage.
- `tests/test_mcp.py` verifies discovery of 27 tools, the three read-only Hands tools, and explicit context creation/binding against a disposable fixture. `tests/test_hands_fallback_mcp.py` proves health/list/read continue to work when the Hermes transport is unreachable and the configured Codex binary is absent.
- The Hands path suite includes a deterministic generative invariant: only explicit safe fixture paths may return content; generated traversal, absolute, separator, protected-name, and missing-path candidates must be denied.
- Automated tests are necessary but do not satisfy the remaining WSL2/ext4/DrvFS and Hermes-off/Codex-unavailable live-acceptance gates for v1.2.0.

Installer coverage includes pip presence detection and ensurepip bootstrap for an existing pip-less venv in the non-uv path.

- Core tests cover authenticated discovery, run lifecycle, follow-up sessions, pagination, key redaction, persistence, duplicate suppression, durable recovery, unsafe replay rejection, run/session ownership, approvals, cached output, stop, loopback/redirect guards, model override fingerprinting, follow-up model policy, model discovery and SQLite migration.
- MCP stdio integration covers initialization and the canonical 27-tool discovery contract, diagnostics, local-only heartbeat, model discovery, model-aware submission, usage tools, polling, output retrieval and foreign run rejection.
- Codex tests cover audit redaction/rotation, recovery visibility after a bridge restart, `unknown_exit`, atomic concurrency reservation, start failure, cancellation/timeout races, watchdog enforcement, workspace allowlist enforcement, symlink escape rejection, write approval staging, fixed-argv subprocess/result capture, and model/reasoning policy forwarding.
- Tunnel tests cover secure key loading/mode and generated systemd unit without embedded key.
- CI runs shellcheck and `bash -n` for install.sh, bridge.sh and tunnel.sh.

The test server mocks the Hermes HTTP contract; it does not replace workstation/tunnel validation. Shell syntax checking does not prove runtime integration.

Live acceptance is recorded in `LIVE-ACCEPTANCE-TH.md`: v1.0.0 RC2 validated 19-tool discovery, Hermes idempotent read-only execution, Codex `gpt-5.6-sol` + `low`, local workspace-write approval, and cancellation through the Secure MCP Tunnel. v1.0.1 then passed its WSL2 deployment health check and a no-write/no-network Codex read-only acceptance with no configuration warnings.

## OpenCode health foundation (disabled by default)

- The `opencode` configuration section is optional, additive, and disabled by default (`enabled` defaults to `false`). Strict validation covers the type of `enabled`, an absolute control-character-free `binary` path up to 4096 characters, `version_timeout_seconds` in 1-120, and `max_output_bytes` in 1024-1048576. Enabling without an explicit `binary` is a configuration error. Unknown keys warn and are ignored. See `tests/test_opencode.py`.
- Default discovery stays at the canonical **27 tools**. When `opencode.enabled` is `true`, registration adds exactly one read-only tool, `opencode_health`, and discovery becomes 28 tools. The registration tests and the `tests/mock_opencode_server.py` stdio fixture prove both counts.
- `tests/test_opencode.py` uses fake executables and runs offline. It covers: disabled fail-closed behavior with no process spawn; enabled validation that requires a regular executable file (missing path, directory, and non-executable file are rejected at startup); one valid probe that asserts fixed argv (`binary --version`), symlink acceptance, and version reporting; malformed version rejection (invalid UTF-8, control characters, empty output, output without digits); nonzero exit rejection without output leakage; timeout enforcement with process-group termination; per-stream memory caps for oversized stdout and stderr; descendant cleanup when a child holds the pipes and ignores `SIGTERM` (the group receives `SIGTERM`, then `SIGKILL`); and the leader-reap ordering regression set (`TestOpenCodeCleanupOrdering`), which records real `killpg`/`wait` calls and proves every `killpg` happens before the single leader reap on the success, nonzero-exit, timeout, and pipe-descendant paths, that exit observation is nonreaping `waitid` with `WNOWAIT` and bounded by the probe deadline, that `EINTR` is retried without reaping, and that unknown leader ownership sends no signal.
- Fake executables do not prove real OpenCode CLI behavior beyond the version probe. Live acceptance recorded 2026-10-18 covers `--version` ONLY: the fixed pipeline against the real binary returned `ok: true` with `opencode v2.0.32` under an in-memory configuration (no settings change). In that historical health-only acceptance, task submission, sessions, JSON event output, cancellation, and permissions were unverified and unimplemented. The separate execution record below (v1.2.5 released) covers later work.

## v1.2.2 provenance and durable-worker gates

- `tests/test_version.py` covers worktree enrichment, embedded build-input provenance, archive/malformed-config fail-safe output, CLI parity, and the version action bypassing configured Hands/Hermes backends.
- MCP stdio and Hands fallback suites require 27-tool discovery, including `bridge_version`.
- Codex regression covers the detached worker retaining a real exit record after the local approver instance exits.
- WSL2 live acceptance passed CLI/MCP identity parity, unavailable-upstream behavior, and no secret/path leakage; the durable-worker acceptance separately passed exact marker bytes, terminal exit code, and JSONL result retrieval.

## Dev MCP Events probe fixture (originally planned for v1.2.4 — now deferred, no assigned release)

- `tests/test_events_probe.py` covers protocol discovery, empty-allowlist denial, exact/wildcard label-boundary matching, HTTPS/port rejection, callback challenge and one redacted delivery, idempotent unsubscribe, invalid allowlist forms, and Standard Webhooks signing inputs.
- This fixture test suite does not prove Secure MCP Tunnel, Work-chat subscription, callback ownership, persistence, expiry/refresh, retry, or Hermes terminal delivery. Those require the recorded Dev live probe before any runtime Events implementation.

## v1.2.3 implementation and acceptance contract

The v1.2.3 maintenance scope is limited to the worker-supervision invariant in SPEC.md: a worker that is unavailable MUST NOT cause `unknown_exit` while its Codex child is still alive.

Automated regression coverage includes worker-only loss, child liveness, delayed child exit, cancellation, restart recovery, PID-reuse start-time rejection, and a real unreaped-zombie liveness probe on Linux `/proc`. Automated CI passed on the current PR head.

WSL2 live acceptance passed on commit `7755f1219a54dd4c8cef6d6d17482e8c8c983478`: worker-zombie/child-alive retained `running` with the redacted supervision hint; a later child exit without a terminal record became `unknown_exit`; and cancel after worker loss became `cancelled`. The project interpreter completed 75 tests without `ResourceWarning`. Independent review passed.

Release verification passed for signed tag `v1.2.3` at `c610660637dbdcfa0b8ddb7bbf01ed22ae66055d`. The published archive SHA-256 is `c231f8563543dbfa9eafa240c5e8e15f44434103940352066e65b58162cb5458`. A fresh GitHub download passed both `sha256sum -c SHA256SUMS` and `unzip -t`.

## Legacy stdio discovery guard (released v1.2.4)

- `tests/test_stdio_guard.py` (13 tests): in-memory boundary pump (int/string id reply shape, no params echo, notification pass-through, non-matching requests, metadata preservation, parse-error forwarding, forward failure logged once, EOF) + guarded `stdio_server` lifecycle + real-stdio subprocess probes (pre-init probe, legacy initialize/initialized/tools-list = 27 tools, repeated probes, unchanged `-32602` validation, clean EOF shutdown rc=0).
- Run: `PROJECT_PYTHON=/absolute/path/to/bridge/.venv/bin/python` followed by `env -u PYTHONPATH "$PROJECT_PYTHON" -W error::ResourceWarning -m unittest discover -s tests`

## OpenCode task execution (v1.2.5; SPEC.md section 18)

- Verified 19 October 2026 at code head `e7add7e594fb2cc0029dd53b628c85f9a7c1a87c`: **164/164 tests pass** in WSL with `env -u PYTHONPATH .venv/bin/python -W error::ResourceWarning -m unittest discover -s tests`. Shellcheck and Bash syntax checks pass. [CI at the same code head](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/39212518227) passes. This is implementation/test evidence, not a release claim.
- Historical checkpoints: the initial `ee62fe8` WSL/CI run passed 162 tests, and `85e3bc` passed 163 after the cleanup-confirmation regression. The final config-load regression proves `opencode.execution` produces no false unknown-key warning while genuine unknown keys still warn.
- Coverage: 34 tests in `tests/test_opencode_tasks.py` and one actual SDK stdio lifecycle test in `tests/test_opencode_execution_mcp.py`, in addition to the existing 129 tests (164 total). Contract per SPEC section 18: disabled fail-closed; `opencode.execution` validation (parent enabled + binary, nonempty canonical workspaces/models, control characters, ranges); fixed argv with no `--auto`/`--server`/`--continue`/caller flags and no `OPENCODE_CONFIG*` env injection; prompt over stdin, shell disabled; session minted and stored before spawn (`ses_` shape); idempotency by `request_id` + fingerprint with conflict rejection; global and per-session concurrency 1 with busy rejection; deterministic fixture CLI paths for error-with-exit-0 (must fail), no completion evidence (must fail), streaming events, permission-request detection (`permission_required`), output caps, cancellation race, worker restart, and descendant cleanup under the WNOWAIT invariant (all `killpg` while the leader is unreaped; single reap after the final signal); redaction of `status`/`recent`/audit; 0600/0700 file modes; and 33-tool discovery through the real stdio fixture.
- Baseline parity passed on WSL and CI: 27 default / 28 health / 33 execution. The hosted editing environment passes the execution fixture checks, but its full run has four existing Codex `/proc` failures and one existing zombie-observation error. The four Codex failures reproduce on a clean `f58a36d` checkout; these baseline tests were not changed or skipped to obtain the WSL/CI pass.
- Release preparation (local): `version_info.py` stamped `v1.2.5` (build provenance `release`, reviewed build input `a666d626da1fe716ce4b259d49eedfc3f97acc7d` — `main` with PR #40 merged). A local candidate ZIP built from the release-prep head per RELEASE-RUNBOOK-TH.md Phase B minus tag/publish passed `unzip -t`, the exclusion check (no `.venv/`, `state/`, `.env`, `bridge-config.json*`, `.git/`, `__pycache__/`, single root `hermes-mcp-bridge-v1.2.5/`), and re-extraction: `bridge.py version` from the extracted tree reports version `1.2.5`, source kind `release-archive`, embedded build input `a666d626`, discovery 27; the extracted tree passes the full 164-test suite with `-W error::ResourceWarning`, including the real stdio fixture proofs of 27 default / 28 health / 33 execution tools. No real model call is made. No archive checksum is committed to the source tree.
- Real CLI v2.0.32 through the actual task controller: submission, same-request replay, same-session remembered-context reply and cancellation with observed CLI exit pass. Native absolute-path read/edit and same-session second edit pass with exact fixture-byte checks. Authenticated Dev Work-chat acceptance passed on 19 October 2026 at `e7add7e`: real-model submission, resumed context, request replay/recent and independent byte verification of native file creation; cancellation remains scoped to the earlier controller run and permission-required remains fixture-only; the scoped records are in [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md); do not infer either from the fixture tests.
- See [OPENCODE-TH.md](OPENCODE-TH.md) for the operator-facing contract. This surface ships in signed v1.2.5; historical candidate records above retain their original evidence scope.


## v1.2.5 — released (19 October 2026)

- Signed annotated tag `v1.2.5`: object `11420f1ae968244195701b296db2f8ce419b793a`, peeled commit `6fbcd7ef278d5e45a95b7328c719c5b01cbcf522`; EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`. Local and fresh-fetch remote `git verify-tag` pass; GitHub reports the signature valid.
- [GitHub Release v1.2.5](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.5) publishes exactly `hermes-mcp-bridge-v1.2.5.zip` and external `SHA256SUMS`. ZIP SHA-256: `1f1c8a583cf7f51a88ec35ca3023c86342220f5baba37faed3f1724b04bf8d5f`.
- Built from the signed tag: 79 files under the single root `hermes-mcp-bridge-v1.2.5/`, no private config/state/venv/env/git/cache entries. Fresh-download `sha256sum -c SHA256SUMS`, `unzip -t` and byte comparison against the built assets pass.
- Extracted identity: version `1.2.5`, release identifier `v1.2.5`, source kind `release-archive`, embedded build input `a666d626da1fe716ce4b259d49eedfc3f97acc7d`, canonical default discovery 27. The signed tag identifies the final commit; the embedded revision identifies its reviewed build input.
- Scope: opt-in OpenCode execution from PR #40; release preparation from PR #41. Candidate WSL/archive suite 164/164 and discovery 27/28/33 pass; exact-head CI `39224170181` passes. Work-chat proof remains scoped to the recorded Dev candidate; cancellation remains controller evidence and permission-required remains fixture-only.
- Production remains v1.2.3; active Dev remains the tested git-worktree candidate. Publishing does not change profiles, runtimes or permission configuration. This post-tag documentation record does not modify the tag or assets.
- Deployment checkpoint (19 October 2026, ~18:44 +07): production was upgraded to released v1.2.5 later that day. Identity, health, discovery, and the execution API listing were verified read-only through the production plugin (`opencode_recent_tasks` returned an empty `jobs` list; no production model task was submitted during this checkpoint, and the checkpoint does not establish production acceptance). See [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md). The bullet above preserves the post-tag record as written at release time.

