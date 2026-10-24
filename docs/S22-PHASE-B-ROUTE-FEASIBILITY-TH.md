# SPEC §24 — Phase B route feasibility assessment

Date: 24 October 2026.
Status: **PRODUCT PATH DOCUMENTED; INSTANCE / ADAPTER PROOF HOLD**.
Base: main `b966a51585eb3d9bb706d461eae6f6c8d60ef0e9` (PR #98 merge).
Design: [Phase B adapter/control plan](S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md).
This assessment is documentation work only. It does not approve provisioning or activation.

## 1. Sources and evidence classes

Official documentation was searched and opened on the date above:
- [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).
- [Connect and test your plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt).
- [Model Context Protocol / hosted Work](https://learn.chatgpt.com/docs/extend/mcp).

These are current product documents, not evidence about the operator's account, guest binary, private route or resource availability. The conclusions below distinguish documented features, parent metadata observations and proposals.

The author inspected this session's tool metadata without invoking original bridge tools. Original Production/Dev namespaces were present; no bound fixture namespace was established. A read-only plugin-directory search did not identify a relevant fixture integration. That search is not exhaustive and does not prove that private/custom plugins or a future supported route are unavailable. No plugin was installed, connected, suggested, refreshed or changed. No browser, Platform organization/workspace settings, credential store or guest was inspected.

## 2. What the documents establish

| Documented feature | Consequence for this plan | Still unproved |
| --- | --- | --- |
| The tunnel client forwards MCP requests to a private stdio or HTTP server over an outbound connection | A guest-local stdio fixture is a documented product deployment shape | Guest client version/digest, exact configuration, cohort lifecycle and actual route |
| ChatGPT can add a custom MCP plugin using a tunnel identity | A distinct test plugin/tunnel can be proposed without retargeting original profiles | Account permissions/associations, independent authentication and available fixture namespace |
| Hosted Work uses installed plugin tools; local Codex MCP configuration is a different surface | Do not assume a local Codex entry creates a hosted Work tool binding | Exact parent invocation/response adapter in the intended Work session |
| Plugin testing records tool selection, arguments, results and errors; refresh can update discovery | A later approved route needs its own captured observations | Raw protocol frames, unchanged full ACK exposure and supported capture/provenance method |

The first two rows follow the tunnel guide; the hosted-Work row follows the MCP page; plugin-testing behavior follows the connect/test guide. No source establishes a generic Python API for invoking tools inside this Work conversation or obtaining its raw tools/list envelopes. No such endpoint is assumed here.
This is a positive documentation result for the general product path. It does not close the design's instance-specific invocation gate.

## 3. Proposed route and adapter boundary

Proposed path: parent Work session → separately identified custom MCP plugin → separate test tunnel → reviewed guest-local client/supervisor → pinned synthetic stdio fixture.
This preserves the original guest-local-client proposal. It is not a selection, credential request or claim that any component is already installed.

The parent dispatcher must bind exact available tool identities to the six reviewed matrix operations and separate bridge_version discovery/identity handling. It must preserve the actual returned fields, errors and identifiers. The source must establish how bounded request/reply data reaches the runner; an assumed callback is insufficient. Neither #97 nor #98 implements this connection.
No fixture call may fall back to an original namespace, a local SDK session, Responses API or another product and be called Work-chat evidence. A missing namespace or unsupported result shape keeps HOLD.
An API-based alternative would change the evidence surface and require a separate reviewed scope; this assessment makes no API call, model selection or API-cost commitment.

A namespace issued only during plugin creation cannot be claimed as an exact prebound identifier. If the product cannot provide the required binding while inactive, first review a staged-binding design against the existing preapproval gates; use section 14 if a normative change is needed. An arbitrary future namespace or placeholder is not an approved binding. This dependency is unresolved here.

A raw discovery collector still needs source review. Proposed direction: a fixture-specific, bounded stdio recorder under the approved guest supervisor, with exact request/reply correlation to the selected route and independently bound source/cohort. This is a proposal, not an implemented recorder or raw capture. Do not enable broad raw HTTP logging or infer raw tools/list from version count, tool metadata, decoded SDK data or a synthesized envelope.

## 4. Static workload and timing limits

The unchanged fixture matrix has 124 tool calls on its successful path:
2 initial status/row calls + 18 cases × 6 calls + 4 replay calls + 2 precheck/plain groups × 5 calls.
It also has 44 ordered observation callbacks. Identity/discovery, collector/control activity and stop/verification add work outside those totals.
This is a source count, not an observed route run, request-rate measurement or completion-time guarantee.

The tunnel guide documents a service request deadline of 120 seconds; that protection is not a latency guarantee. It does not override #97's proposed 5-second cooperative timeout, 2-second observation freshness or the approved plan's at-most-20-minute B window.
Local CI timings do not prove those values feasible through the actual Work route. Any adjustment to source-only proposed values needs explicit source review; the plan's budgets/gates cannot be silently extended. No automatic reconnect, retry, second launch or deadline reset is approved.
Continuous independent collectors, parent-loss behavior and a finite supervisor must be implemented before operational timing can be relied on. Manually reporting a successful callback is not a substitute.

## 5. Reviewable work and later operational gates

| Stage | Concrete review item | Authority boundary |
| --- | --- | --- |
| Offline source preparation | Parent dispatch/data bridge, collectors, exact-identity supervisor/stop control, duplicate-launch prevention, bounded recorder/evidence and stopped-writer proof | Each exact delta needs offline validation and review; no original-runtime control or guest deployment |
| Inactive setup proposal | Reviewed client distribution/version/digest, new private paths/profile, dependency/storage plan and completed private resource map | Separate operator scope before installation, account/credential or profile changes; no client or fixture start |
| First activation proposal | Exact whole harness revision/digest, private namespace/tunnel bindings, controller, budgets, observation/capture method and finite stop policy | Separate B approval before any possible spawn |
| Actual route proof within that window | Observe new route identity/discovery/full result shape, one cohort and observer/control health before matrix stimulus | Missing proof ends at HOLD; no surrogate evidence or original-route fallback |
| Matrix and closure | Preserve exact case order, ACK/row/call evidence, stopped-state comparison and original-runtime observations | Completed attempt, independent review and explicit operator acceptance before scoped section 22 closure |

Custom-plugin creation, installation/connection, discovery, refresh or reconnect may start or queue work for a fixture. Do not classify them as harmless inactive probes. Treat an operation that may lead to spawn as activation unless its inactive behavior is independently established; it stays behind the separate B approval. The documented generic setup tutorial does not override this project's stricter ordering.
The reviewed launcher must cover all actual client/fixture/observer/log writers and stop only exact owned identities. The old unresolved run, historical state and original Production/Dev stop/switch gates remain unchanged.

The operator has explicitly accepted Phase A readiness; [PR #96](https://github.com/sc28249782/hermes-mcp-bridge/pull/96) records that statement and remains an unmerged draft at this base. That acceptance covers preparation only. This assessment does not rewrite the historical pending wording in the original design or merge #96.

## 6. Disposition and next source work

Record the product-level path as documented and retain HOLD for the actual invocation/adapter, authenticated observers, lifecycle and capture proof. The next useful source work is the finite collector/supervisor/recorder and parent handoff design with executable offline controls, not another claim that a data validator proves a route.
Before presenting an executable setup approval request, complete the exact reviewable source, client identity and private bindings. This assessment is not yet such a setup packet; it deliberately supplies no activation command or invented namespace/credential binding.
No VM/host/SSH change, installation, credential creation, account action, route setup/refresh, fixture activation, backend/model task or guest measurement occurred. Candidate `02d7e8bb1e1902ca33a574ab904a6e5b0f441785`, behavioral fixture `e7be0cc4e84b820eb8c7ac541325672d0f892fb2` and the #97/#98 sources remain unchanged.
Scoped section 22 and PR #80 remain HOLD. Release/signing/publication/deployment remain separate decisions. Review or merge of this assessment grants no operational authority.
