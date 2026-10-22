# Hermes MCP Bridge

## v1.2.8 — released (22 October 2026)

Released v1.2.8 contains the reviewed SPEC §21 context-lifecycle delta only: conditional atomic registry mutations with a typed closed rejection, the one-row `observe_hermes` guard, and the §21.2 `context_binding` submit outcome. Signed annotated tag `v1.2.8` (object `bb2f076bb3fd665950551ca613abb6ce6fb8f809`, peeled commit `1ae159031a53e4e5359fd39e61b2748159149a52` see [release record](docs/V1.2.8-RELEASE-RECORD-TH.md)) passed cryptographic verification with fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`; the GitHub badge reports `verified: false` (reason `no_user`), recorded separately. [Release assets](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.8) passed maintainer-side fresh-download verification; the external independent audit is pending. Production still runs signed v1.2.7 (deployed 21 October 2026); release approval does not approve a v1.2.8 deployment. See the [preparation record](docs/V1.2.8-RELEASE-PREP-TH.md) and the [scope decision packet](docs/V1.2.8-RELEASE-DECISION-PROPOSAL-TH.md).

## v1.2.7 — released (20 October 2026)

Released v1.2.7 combines the reviewed Codex read-ahead fix and Context P1.
Signed tag `v1.2.7` (object `5a652cbf44c768cec70b3555686bbaaa93383d75`, peeled commit `625ea117aa693f577872638a6353b1408fb405aa`) passed local EDDSA verification with fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`; the GitHub badge reports `verified: true`, reason `valid`.
[Release assets](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.7) passed fresh-download verification, and the external fresh-input audit passed (operator-supplied report; scope limits in the [release record](docs/V1.2.7-RELEASE-RECORD-TH.md)).
Production was upgraded to signed v1.2.7 on 21 October 2026; see the [deployment record](docs/V1.2.7-DEPLOYMENT-TH.md). Historical checkpoint (20 October 2026): the deployment decision, including the not-deploy option, was pending and production remained v1.2.6.
See the [preparation record](docs/V1.2.7-RELEASE-PREP-TH.md) and [scope decision](docs/V1.2.7-RELEASE-DECISION-TH.md). P1 adds aggregate status/create warnings and a local preview; registry unavailability makes heartbeat `ok=false`, while a cap warning alone does not. No deletion or native history compaction is added.

## Codex result read-ahead fix (shipped in v1.2.7)

This fix disables binary read-ahead to enforce the existing snapshot byte budget in SPEC §19.3.
Regression tests cover truncation and appends on Python 3.12 and 3.14.
This fix ships in released v1.2.7 and reached production with the upgrade on 21 October 2026. Historical checkpoint (20 October 2026): it was not yet deployed on the production v1.2.6 baseline.
See [testing evidence](docs/TESTING.md#unreleased--codex-result-read-ahead-fix).

## v1.2.6 — released (20 October 2026)

Released v1.2.6 implements the reviewed privacy requirements in [SPEC section 19](docs/SPEC.md).
It filters Hermes metadata, enforces private directory modes and bounds Codex result reads.
The operator approved v1.2.6 as its target scope on 20 October 2026.
The release is stamped 1.2.6/v1.2.6 with reviewed build input `e3e698a7a220bf14a8bb4d1260bf2ded7e666b56`.
[Signed release assets](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.6) passed fresh-download verification. The operator separately approved deployment on 20 October 2026; production ran v1.2.6 at that dated checkpoint. Production subsequently moved to signed v1.2.7 on 21 October 2026.
Cryptographic tag verification passed; GitHub's badge reports `no_user`. See the [release record](docs/RELEASE-STATUS-TH.md).
See the [release-preparation record](docs/V1.2.6-RELEASE-PREP-TH.md) for verification gates.
See the [scope decision record](docs/PRIVACY-RELEASE-DECISION-TH.md).
The signed v1.2.5 release and its acceptance records remain unchanged.

Securely connect ChatGPT to a local Hermes Agent and Codex CLI running in WSL2, through an OpenAI Secure MCP Tunnel.

The bridge is a controlled local execution boundary. It does not expose a general remote shell.
The current signed release is **v1.2.8** (released 22 October 2026).
The production deployment is **signed v1.2.7** (operator upgraded on 2026-10-21); a v1.2.8 deployment requires a separate decision. Historical checkpoint (2026-10-20): production ran v1.2.6 and the v1.2.7 upgrade decision, including the not-deploy option, was pending.
The production upgrade checkpoint is recorded in [release status](docs/RELEASE-STATUS-TH.md).

Released v1.2.5 adds the separately gated OpenCode execution opt-in.
Discovery contains 27 MCP tools by default.
Enabling only the OpenCode health adapter adds one tool, for 28 tools.
Enabling OpenCode execution adds five more tools, for 33 tools.

The bridge reports version and provenance through local-only operations.
A durable worker supervises each approved Codex write job.
Status remains `running` when that worker is unavailable but its child is still alive.

Earlier release: **2026-10-18**, **v1.2.4** with a GPG-signed annotated tag on `2133056`. It adds the disabled-by-default OpenCode health adapter (PR #34; discovery stays at the canonical 27 tools unless an operator opts in) and the legacy stdio discovery guard (PR #35). Release assets plus an external SHA256SUMS are published at https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.4 (ZIP SHA-256 `e6deb0e6ab16d669836b0e361e2e875858e19597ef35dc7e4fc19010a6a5f3a9`, download re-verified). MCP Events is not included (deferred, BLOCKED). Production deployment remains v1.2.3; this release requires no rollout, service, or config change. At that dated checkpoint, installation and upgrade instructions used v1.2.6. The current released production baseline remains v1.2.7; v1.2.8 was released on 2026-10-22 and its deployment decision, including the not-deploy option, is separate.

Deployment note (dated): the "Production deployment remains v1.2.3" statement in the paragraph above describes 2026-10-18, the v1.2.4 release date. A later checkpoint records production v1.2.6 on 2026-10-20; see [release status](docs/RELEASE-STATUS-TH.md).

Released **2026-10-19** as **v1.2.5** with a signed annotated tag on `6fbcd7e`. [Release ZIP and external SHA256SUMS](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.5) were downloaded and verified (ZIP SHA-256 `1f1c8a583cf7f51a88ec35ca3023c86342220f5baba37faed3f1724b04bf8d5f`). See [release status](docs/RELEASE-STATUS-TH.md).

## OpenCode health (disabled by default)

The bridge includes a disabled-by-default OpenCode adapter (`opencode_core.py`). Discovery stays at the canonical 27 tools while it is disabled. Enabling it registers one additive read-only tool, `opencode_health` (28 tools).

- Configuration lives in `bridge-config.json` under `opencode`: `enabled` (default `false`), `binary` (absolute path to the OpenCode executable, required when enabled), `version_timeout_seconds` (1-120, default 10), and `max_output_bytes` (1024-1048576, default 65536). Unknown keys are warned and ignored.
- When disabled, the bridge fails closed: it never spawns a process and makes no network, model, or authentication call.
- The health check runs one bounded `--version` probe with a fixed argv list, `shell` disabled, a hard timeout, and a per-stream memory cap. The probe group always receives `SIGTERM` and then `SIGKILL`, including descendants that hold pipes or ignore `SIGTERM`. Every group signal is delivered while the leader is still unreaped (its zombie pins the PID/PGID), exit is observed with a nonreaping `waitid` bounded by the probe deadline, and the leader is reaped once by handle after the final `SIGKILL`; if leader ownership is unknown, no signal is sent.
- The configured executable is not a sandbox. It runs with the full user privileges of the bridge process and can read global configuration and credentials.
- Released v1.2.4 ships this adapter as a health-only foundation. Task execution exists only behind the separate `opencode.execution` opt-in (see the next section; released v1.2.5). Event subscription and native permission replies are not implemented. Never pass `--auto` to a bridge-run OpenCode process.

## OpenCode task execution (released v1.2.5)

A separately gated execution extension (SPEC.md section 18), released in v1.2.5, adds five tools — `opencode_submit_task`, `opencode_task_status`, `opencode_task_result`, `opencode_cancel_task`, `opencode_recent_tasks` — for a discovery count of 33 tools. It is disabled by default behind an explicit `opencode.execution` opt-in that requires the health adapter (`opencode.enabled` plus `opencode.binary`), nonempty canonical `allowed_workspaces` and `allowed_models`, and explicit limits (`max_prompt_chars` 1-131072 default 32000, `max_runtime_seconds` 1-14400 default 1800, `max_output_bytes` 65536-8388608 default 524288; independent of the health `max_output_bytes`).

The boundary is explicit: the configured executable runs with the full privileges of the bridge process and the bridge adds no sandbox; workspace selection is a current-working-directory allowlist, NOT filesystem or network isolation; the bridge injects no permission configuration and native OpenCode configuration, plugins, and saved permissions apply unchanged; `--auto` is never passed and the bridge never auto-approves a native permission request (an unresolved ask ends as `failed` at the bounded deadline or `permission_required` only on an explicit protocol event). `completed` means the native turn finished, not that the user's goal succeeded — inspect the untrusted output. Sessions are bridge-minted; resume is only for a bridge-owned session with the same canonical workspace and model, and `request_id` retries replay the original acknowledgement without a second model invocation. Details: [docs/OPENCODE-TH.md](docs/OPENCODE-TH.md). This opt-in is included in signed v1.2.5; enabling it remains an operator configuration choice.

## Legacy stdio discovery guard

On the legacy stdio serve path (`./bridge.sh serve`), an incoming `server/discover` request is answered at the stream boundary with a JSON-RPC `-32601` error carrying the original request id and no echoed parameters. The reply is an error, not a capability: discovery stays at the canonical 27 tools (28 with `opencode` enabled), repeated probes do not flood logs, and every other message is forwarded to the SDK unchanged. See SPEC.md section 17.

## Safety model

- Hermes uses its authenticated local Runs API and its own approval policy.
- An advertised Hermes approval-response endpoint does not by itself prove that the API profile can create an interactive approval session; v1.1.0 SSE approval integration is deferred pending an upstream contract.
- Codex can use only explicitly allowlisted workspaces.
- Codex permits only `read-only` and `workspace-write`; `danger-full-access` is rejected.
- Every Codex `workspace-write` job requires local terminal approval. The bridge adds no approval layer for OpenCode execution. Native OpenCode permission policy applies.
- Approved Codex work is supervised by a durable local worker, which persists its terminal outcome independently of the tunnel process.
- Codex workspace policies can restrict sandbox modes, runtime, prompt size, concurrency, approval lifetime, and configured pre-flight prompt patterns.
- Audit logs are redacted, local-only, rotating JSONL files. Secrets, prompts, and outputs are not written to them.
- A persistent Codex watchdog enforces each workspace runtime limit even when no client polls job status.

## Start here

Run each step in order from the repository root. Stop when a step reports an error and fix the cause before the next step.

1. Create the virtual environment and the initial configuration:

   ```bash
   bash install.sh
   ```

2. Verify the Hermes connection:

   ```bash
   ./bridge.sh doctor
   ```

3. Verify the Codex workspace policy:

   ```bash
   ./bridge.sh codex-doctor
   ```

4. Inspect state permissions and audit configuration (read-only):

   ```bash
   ./bridge.sh diagnostics
   ```

5. Verify the installed identity and discovery contract:

   ```bash
   ./bridge.sh version
   ```

`./bridge.sh version` is local-only: it does not contact Hermes, Codex, the tunnel, GitHub, or another network service. It reports the installed bridge version, release/provenance fields, config-schema version, and MCP discovery contract. The MCP equivalent is the read-only `bridge_version` tool.

Run `bash tunnel.sh init tunnel_YOUR_ID --force` when changing the bridge directory or version; it updates the `hermes-wsl` profile and starts the tunnel. Later starts use `bash tunnel.sh run`.

## Documentation

- [Project origin](docs/PROJECT-ORIGIN.md) and [project history](docs/PROJECT-HISTORY.md)
- [Thai installation guide](docs/README-TH.md)
- [Codex / WSL2 policy](docs/CODEX-WSL2-TH.md)
- [Operations guide](docs/OPERATIONS-TH.md)
- [Upgrade guide](docs/UPGRADE-TH.md)
- [Technical architecture](docs/HERMES-MCP-BRIDGE-TECHNICAL-ARCHITECTURE-TH.md)
- [Specification](docs/SPEC.md), [testing](docs/TESTING.md), [release status](docs/RELEASE-STATUS-TH.md), and [changelog](docs/CHANGELOG.md)
- [v1.x acceptance checklist](docs/V1-ACCEPTANCE-TH.md), [compatibility matrix](docs/COMPATIBILITY-MATRIX-TH.md), and [release runbook](docs/RELEASE-RUNBOOK-TH.md)
- [Security](docs/SECURITY.md) and [contributing](docs/CONTRIBUTING.md)
- [Roadmap](docs/ROADMAP.md)
- [STE-inspired writing style guide](docs/WRITING-STYLE.md)
- [Local Hands architecture and security](docs/LOCAL-HANDS-ARCHITECTURE-TH.md)
- [Local Hands implementation and acceptance plan](docs/LOCAL-HANDS-IMPLEMENTATION-PLAN-TH.md)
- [Local Hands v1.2.0 read-only setup](docs/LOCAL-HANDS-V1.2-SETUP-TH.md) and [WSL2/DrvFS live acceptance](docs/LOCAL-HANDS-V1.2-LIVE-ACCEPTANCE-TH.md)
- [ADR-0001: Local Hands foundation contracts](docs/adr/0001-local-hands-foundation.md)
- [Third-party notices and design attribution](THIRD_PARTY_NOTICES.md)

## License

Licensed under [Apache License 2.0](LICENSE).

The Local Hands design was inspired in part by [Endeavor Hands](https://github.com/halochamp/Endeavor_Hands) (MIT). No Endeavor Hands source code or assets are incorporated in the current runtime; see [Third-Party Notices](THIRD_PARTY_NOTICES.md).

