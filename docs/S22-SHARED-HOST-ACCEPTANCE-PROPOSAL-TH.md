# SPEC §22 — shared-host synthetic acceptance proposal

Date: 23 October 2026.
Status: **PROPOSED — direction agreed; exact amendment and execution unapproved**.
Base: main `4c529bd85c760b62cd2d34bd5891b78ad1f568a6` (PR #85 merge).

## Problem and proposed change

The PR #84/#85 design requires a test management plane outside historical host authorities' control.
That requirement is stronger than functional fixture separation on an operator-controlled shared host.
This proposal explicitly changes that prerequisite for one separately approved synthetic §22 plan. It does not claim the original isolation requirement passed.
The proposed [SPEC §24](SPEC.md#24-shared-host-synthetic-acceptance-proposed) treats host management as trusted, requires explicit shared-authority disclosure, and retains fresh fixture inventory, integrity observations and interference/resource stop conditions.

## Directional agreement

The operator's opening assent to the preceding recommendation to draft this trust-model change was, verbatim:

> ใช่ครับ

The rest of that message describes private operating circumstances and is not reproduced here. The chat message has no exact approval timestamp; none is invented.
The assent is recorded only as agreement to prepare the proposal. It does not approve normative wording, an exception already in force, setup, a connector, credentials, activation, maintenance, release or deployment.

## Explicit tradeoff and preserved controls

- The proposal no longer requires proof that historical host authorities cannot reach the new test management plane. The host/administrator trust assumption and possible accidental interference must be disclosed.
- New guest fixture resources and their actual writers must be inventoried. Original production/Dev resources must not be stopped, switched, restored, copied, reset or retargeted.
- Integrity observations must cover the required identity, row-state and backend-call checks. Missing observations or unexplained changes produce HOLD. No observation claims continuous absence of host interference.
- No historical cessation, containment or safety conclusion is made. Section 23 disposition requirements are unchanged; the old stop/switch path and PR #80 remain HOLD.
- The test remains synthetic-only and needs a separate executable plan, local approval paths, independent evidence review and explicit operator acceptance. Release/deployment are separate.

## Verification and gates

This PR writes documentation only. It provides no runtime implementation, executed test, setup command or activation authority.
Existing SPEC text outside the added §14 checkpoint and appended §24 remains verbatim.
Earlier PR #84/#85 wording is retained as history with a later proposal checkpoint; no requirement is silently overridden.
The amendment must pass §14 review/merge first. A plan must then explicitly adopt the reviewed alternative and receive separate operator authorization before action.
No private local capability inventory, account/host identifiers, permissions dump, receipt contents/digests, SSH endpoint, host key, or credentials are published.
