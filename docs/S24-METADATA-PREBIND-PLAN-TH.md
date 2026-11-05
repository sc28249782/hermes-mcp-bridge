# SPEC §24 — staged metadata prebinding plan

Date: 25 October 2026. Plan ID: `S24-PREBIND-20261025-01`.
Status: **PROPOSED / NOT EXECUTION-READY — no setup, account or client-start approval**.
Source baseline: PR #104 head `70eca6dc0895cc208cb3823e947f306c7f30bd26`.
Parent: [shared-host plan](S22-SHAREDHOST-SETUP-ACCEPTANCE-PLAN-TH.md),
[B design](S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md),
[peer limits](../acceptance/s24/INTEGRATION.md#proposed-manifest-only-prebinding-route).

## 1. Decision required before use

The operator-supplied seventh review approved the peer source at the baseline.
It did not approve this stage, provisioning or execution. This proposal requests
independent plan review: does a separately bounded, permanently inactive metadata
stage fit [§24](SPEC.md#24-shared-host-synthetic-acceptance-proposed) and the parent
plan? No exception is declared. If a normative change is required, its separate
§14 amendment must pass review/merge before use. A missing decision keeps HOLD.

The only proposed result is evidence about a new metadata-only route/namespace.
It cannot establish candidate discovery, task execution, fixture readiness, B PASS,
writer cessation or scoped §22 acceptance. Existing original-runtime controls and
PR #80 HOLD remain unchanged. Release/deployment are separate decisions.

## 2. Immutable source and proposed client

| Input | Pin / present evidence | Still required before use |
| --- | --- | --- |
| Peer source | `70eca6dc0895cc208cb3823e947f306c7f30bd26`, `acceptance/s24/route_prebind.py`; SHA-256 `f031f36c02f0eae7b1ce0c5e1baa8abaf996bb20e99d2c94e0a04a0f1d4bc1e3` | Compare actual guest bytes before/after; no overlay or active variant |
| Advertised manifest | Same source revision; SHA-256 `ef081b19445fa9132f54f434254c04fbf4532b716ad1f994bbc1415261702ab9` | Compare actual guest bytes; advertised 27 is not observed candidate discovery |
| Candidate / fixture | Candidate `02d7e8bb1e1902ca33a574ab904a6e5b0f441785`, fixture `e7be0cc4e84b820eb8c7ac541325672d0f892fb2` | Reference only; neither is loaded/started by this stage |
| Client proposal | Official `openai/tunnel-client` v0.0.18, source ref `274a5588414819f063d27100a4fb1096aae3830f` | Guest architecture, installed availability and compatibility unmeasured; no original client upgrade |
| Proposed Linux amd64 archive | `tunnel-client-v0.0.18-linux-amd64.zip`, asset ID `670307937`, 29,420,141 bytes; API-reported SHA-256 `3c82307316acd93c88a384b62af1d81d3f4cb0efa975f9c0bfaef922866a04c4` | No archive downloaded/extracted/executed here. Compare actual bytes, archive paths/modes and extracted binary hash under separately approved scope |
| Python/dependencies | Existing guest venv is a possible input, not a fresh observation | Bind interpreter argv path, real executable, version and dependency identity; preserve the venv path in argv rather than substituting its resolved base interpreter |

Release metadata/digests are source observations, not asset authentication or
runtime proof. If architecture is not amd64, stop and revise the selected asset.
Follow the official latest-release landing page for discovery; this attempt still
pins the reviewed asset above. A newer release is not an automatic substitution.

## 3. Private binding dossier

Keep the completed dossier/evidence 0600 under a fresh canonical 0700 root. Do not
publish usernames, paths, PIDs, endpoints, fingerprints, account IDs or credentials.
Digest the exact dossier bytes; the digest is correlation, not approval/authentication.

| Alias | Mandatory value / limit |
| --- | --- |
| HOST / GUEST / CONTROL | Exact trusted shared-host/guest and operator-console identities; no isolation claim; operator control independent of a bridge task |
| PROD / DEV | Read-only identity/health/continuity methods and inspection limits; never target them with metadata calls or stop/retarget them |
| ROOT / LOGS / PROFILE | New private paths, inode/owner/mode, no overlap with originals; one exact profile file and its digest |
| CLIENT / PYTHON / PEER | Exact argv and executable/file hashes, version/help/dependencies, source and interpreter paths; no shell wrapper, active target or PATH-selected binary |
| ROUTE / AUTH | Newly scoped tunnel ID, target Platform/workspace association, plugin identity and authentication method; operator provisions credentials locally only |
| PORTS / NETWORK | Exact unused guest loopback health listener and outbound HTTPS path; stdio peer needs no network listener; no host forwarding/firewall change |
| PROCESSES / STOP | Every client/peer/controller/observer/log writer, ownership/lifetime, PID/start/exe/argv and exact stop/confirmation method |
| OBSERVERS | Host/guest RAM, disk/growth/logs, original continuity, launch/exit/process coverage and private source/namespace evidence methods |

Every value is currently unfilled/unverified on the guest. That blocks execution.
Before a launch, approve the executable/argv/lifetime rule; bind the resulting exact
instance before accepting discovery evidence. An unexpected process/second peer,
unavailable observation or ambiguous stop target produces HOLD.

## 4. Separate future scopes

These scopes are proposals, not granted windows. Old Phase A windows are expired.
Merging this plan or asking to continue grants none of them.

| Scope | Maximum proposed work | Explicit exclusions / exit |
| --- | --- | --- |
| R0: read-only inventory, at most 10 min | Operator reads nominated guest architecture/interpreter/dependencies/resources and existing binary availability; public source/help review | No install, key/account change, profile creation, client/peer start, refresh or connector probe. Return private missing-field report |
| R1: inactive preparation, at most 15 min | Only after R0 review and separate exact approval: obtain the pinned archive if needed, validate/extract into new private paths, prepare the bound profile; operator provisions new route/auth through approved local UI | No client/peer start or discovery. No system package, SSH setting, original profile or original credential changes. Return completed dossier for review |
| R2: one metadata attempt, at most 120 s total | Only after compatibility decision, R1 evidence review, all bindings/observers/stop controls and separate finite approval: start exactly one new client/peer, create/connect the new plugin and inspect metadata | No fixture/backend/matrix calls or active handoff. No second launch, restart, extension, unattended refresh or retry. Return evidence/HOLD and stop confirmation |

Account/plugin operations that might discover or connect are R2, never R1. If an
account/UI operation cannot be staged without discovery, defer it until R2 scope.
No credential is entered through prompts, CLI literals, screenshots or public logs.
The later credential workflow must use its approved local/account path; no admin
key is supplied to the runtime. This plan creates or reuses no key now.

Resource floors/caps remain host available≥1,536 MiB, guest available≥768 MiB,
test RSS≤768 MiB, free workspace≥2 GiB, growth≤2 GiB and logs≤128 MiB. Observe
before/during/after; unreadable or exceeded limits mean HOLD, not service shutdown
to free resources. These are monitored thresholds, not kernel reservations.

The peer itself has one 30 s window, 128 input frames, 64 KiB/frame and 1 MiB output.
The R2 controller deadline starts before client launch, never resets on discovery,
and reserves at least 10 s TERM grace plus evidence time within 120 s. Peer expiry,
insufficient UI/invocation time or delayed requests means HOLD. No implicit rerun.
Source/file I/O is not interrupted by the peer's pipe deadline. Reviewed outer
supervision, complete stage process accounting and observer methods are still
unfilled prerequisites; the peer timer is not their replacement.

## 5. Profile shape for review only

This template is deliberately not runnable. All placeholders require reviewed
private values. Reject placeholder residue, whitespace/quoting ambiguity, extra
channels, URL backends, demo/Harpoon modes or an active fixture command.

```yaml
config_version: 1
control_plane:
  base_url: https://api.openai.com
  tunnel_id: "<NEW_BOUND_TUNNEL_ID>"
  api_key: "env:S24_PREBIND_RUNTIME_KEY"
health:
  listen_addr: "<BOUND_UNUSED_GUEST_LOOPBACK_ADDRESS>"
admin_ui:
  open_browser: false
log:
  level: info
  format: json
mcp:
  max_concurrent_requests: 1
  stdio_send_initialized_notification: true
  commands:
    - channel: main
      command: "<VENV_PYTHON_ABS> -I -B <PINNED_PEER_ABS> --metadata-only"
```

Bind a clean, reviewed environment allowlist. Inherited MCP_COMMAND, profile,
config, extra-channel, proxy or authentication overrides can change the target:
remove them from the child environment rather than modifying original settings.
Keep required interpreter/client variables explicit and credential values local.
Use the exact private profile-file path, not original profile lookup or --force.
The initialized-notification shim is proposed to avoid depending on an unknown
caller notification; source documents duplicate suppression. Its actual behavior
must be observed in the new route, not inferred from the option name.

Only after scope and installed-help validation, the proposed command shapes are
`CLIENT help quickstart`, `CLIENT doctor --profile-file PROFILE --explain`, then
in R2 only `CLIENT run --profile-file PROFILE`. These are aliases, not shell
variables/ready commands. Read-only source inspection finds stdio init/doctor
preflight checks and EOF-triggered shutdown requests, not an executed binary test.
If actual doctor/init behavior would launch a target or contact an unapproved
endpoint, stop/reclassify it before invocation. Health/doctor alone is not route proof.

## 6. One attempted route and stop sequence, after R2 approval

1. Recheck approval/dossier/source/binary/profile/env hashes, budgets and original
   continuity. Complete process/stop bindings and independent observer readiness.
   Do not start if any prerequisite is unknown. Stage the permitted UI before launch.
2. Start one client against only the new tunnel; record its exact instance and the
   one peer. Do not use nohup, a service manager, retry loop or original bridge job.
   Verify no other instance uses that stdio tunnel. Stop on any unexpected launch.
3. Through the approved ChatGPT plugin UI choose the new tunnel/authentication
   context. Record actual assigned plugin/namespace and advertised inactive identity,
   initialization/discovery observations and provenance. Platform policy, unavailable
   namespace or inability to finish within the peer window means HOLD.
4. Allow initialization, ping and tools/list only. Do not call even a denied submit
   or version tool as live stimulus. All-call denial/identity rejection are offline
   tests, not permission for live writes. No generic Python Work API or SDK substitute.
5. End discovery, finish/handoff controller dependencies and recheck exact test
   identities before TERM. KILL only after 10 s for the same matched test targets if
   explicitly in scope; otherwise HOLD for operator inspection. Confirm actual exits,
   channel inactivity, remaining processes/writers and original continuity. EOF or
   missing PID alone is not complete cessation proof. Preserve all evidence/files.

Client source requests shutdown after its stdio child exits; this does not prove
the installed client stopped or forbid an external supervisor from restarting it.
Observe one launch, and treat a restart/respawn/second client as HOLD. If actual
writer coverage or stop cannot be established, no completed-stage result is issued.
No workspace/profile/plugin/credential deletion or original-runtime action is included.

## 7. Evidence and later active handoff

The private record includes scope/dossier digest, all exact inputs and instances,
direct observations/times/limitations, namespace and metadata provenance, launch
counts, resources/continuity, expiry/failure/stop outcome and missing evidence.
Mark operator reports separately. Hashes and reported tool counts are not raw MCP
capture or authentication. Do not collect raw credential-bearing HTTP logging.

Independent review and operator acceptance can accept only this limited metadata
capability observation. R2 does not close Phase B/scoped §22, assert candidate 27,
acceptance 124/44/audit30, real backend behavior, original-run disposition or full
quiescence. PR #80 remains HOLD and #96 remains a separate unmerged record.

A later active source/profile requires fresh review/bindings and B approval;
namespace stability must be proved again. Switching a target, refreshing to a
spawn-capable executable or discovery that may start the fixture is activation.
No existing R2 permission, profile, receipt or metadata hash is an activation token.

## 8. Sources and present evidence limits

Checked 25 October 2026: [official tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels),
[custom MCP connection](https://developers.openai.com/api/docs/guides/custom-mcp-server),
[Work MCP surface](https://learn.chatgpt.com/docs/extend/mcp).
These establish a documented product path, not the operator's entitlement or route.
The official guide needs a running client for discovery; local Codex configuration
does not make this route available in a hosted Work chat. No latency is promised.

Pinned client sources: [configuration](https://github.com/openai/tunnel-client/blob/274a5588414819f063d27100a4fb1096aae3830f/docs/configuration.md),
[stdio lifecycle](https://github.com/openai/tunnel-client/blob/274a5588414819f063d27100a4fb1096aae3830f/pkg/mcpclient/stdio_command.go),
[preflight](https://github.com/openai/tunnel-client/blob/274a5588414819f063d27100a4fb1096aae3830f/cmd/client/stdio_preflight.go),
[release asset metadata](https://github.com/openai/tunnel-client/releases/tag/v0.0.18).
Source inspection supports profile-file/env precedence, one stdio instance per
tunnel, child start and EOF-triggered shutdown requests. No installed-client,
guest/network, asset-byte, credentials, workspace entitlement or live-route test
was performed. The source-approved peer 10/10 and prior CI are offline evidence.

All private bindings, guest measurements, asset/binary checks, operational observer
and supervision proofs, compatibility disposition and operator scope remain OPEN.
This plan is reviewable, not execution-ready. No provisioning, activation, original
service change, release or deployment was performed while authoring it.

## 9. R0/R1 preparation checkpoint — 25 October 2026

The [R0/R1 preparation record](S24-PREBIND-R0-R1-RECORD-TH.md#s24-prebind-r0-r1-preparation-record) retains operator-reported inventory, pinned file preparation, local version/help inspection, the expired first R1 window and the separately approved continuation. The private profile/key record remains pending bindings and independent review. This later checkpoint was not in reviewed PR #104 head `30b5a93`; prior proposal text remains historical. No R2 approval, client/peer service start, discovery or gate closure is recorded.

## 10. Binding method proposal — 25 October 2026

The [metadata binding work package](S24-METADATA-BINDING-WORK-PACKAGE-TH.md#s24-metadata-binding-work-package) maps each remaining private field to a proposed evidence method and HOLD condition. It distinguishes local doctor checks from authentication, retains complete cohort/control gaps and proposes one combined inventory followed by source/private review before R2. This is offline planning only; no new guest scope, helper execution, setup, API request or activation. All earlier text remains historical; PR #80 stays HOLD.
