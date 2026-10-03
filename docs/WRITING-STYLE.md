# Writing Style Guide

## Purpose

Use this guide for English technical documentation, command help, error messages,
release notes, acceptance procedures, and pull request descriptions.

This project uses a **Simplified Technical English (STE)-inspired** style.
The goal is clear, safe, and testable communication for readers who do not use
English as their first language.

This guide does not claim ASD-STE100 compliance. A compliance claim requires a
review against the current official ASD-STE100 standard, including its dictionary
and writing rules.

## Scope and precedence

This guide defines project-wide writing principles. Project safety and release
documents take precedence when they define more specific wording or procedures.

In particular, preserve the terms and constraints in:

- `docs/SECURITY.md`
- `docs/OPERATIONS-TH.md`
- `docs/RELEASE-RUNBOOK-TH.md`
- `docs/SPEC.md`
- `docs/CODEX-WSL2-TH.md`

Do not use this guide to weaken a safety control, approval requirement, or
release verification step.

## Core rules

- Write one action or one fact in each sentence.
- Use active voice. State the actor when it is important.
- Start an instruction with a direct verb: `Run`, `Check`, `Stop`,
  `Verify`, or `Do not`.
- State the target, condition, and expected result.
- Use numbered steps for a sequence. A reader must be able to run each step in
  order.
- Use the same term for the same object or state. Do not use synonyms for
  technical terms.
- Define an abbreviation at its first use in a document, unless it is defined
  in the project glossary or an API contract.
- Use code formatting for commands, paths, configuration keys, tool names,
  model IDs, and status values.
- State units and limits explicitly: `3,600 seconds`, not `one hour` when
  the exact configuration value matters.
- Use American English spelling unless an external contract requires another
  spelling.

Avoid vague words and phrases, including `normally`, `appropriately`,
`quickly`, `simply`, `etc.`, and `as needed`. Replace them with a
condition or an explicit action.

## Safety-critical instructions

A safety-critical instruction changes a workspace, starts or stops a process,
approves work, changes policy, handles credentials, or creates a release.

Each safety-critical instruction must state:

1. The action.
2. The exact target.
3. The required authorization or precondition.
4. The verification result.
5. The safe response when verification fails.

Example:

> Run `./bridge.sh codex-doctor`. Submit a Codex job only when the command
> returns `ok: true`. If it returns an error, do not start the job.

Do not describe a pre-flight deny pattern as a sandbox or as a substitute for
workspace allowlists, Codex sandboxing, or local terminal approval.

Do not include secrets, private keys, passphrases, prompts, job output, or
unredacted audit data in documentation examples.

## Approved project terms

Use these terms consistently:

| Use this term | Do not replace it with |
| --- | --- |
| `bridge` | gateway, service, layer |
| `workspace` | project folder, working directory |
| `local terminal approval` | automatic approval, remote approval |
| `workspace-write` | unrestricted write access |
| `read-only` | safe mode |
| `allowlist` | whitelist |
| `audit log` | activity history |
| `redacted` | hidden, removed |
| `terminal status` | final state, completed state |
| `unknown_exit` | successful recovery |
| `watchdog` | background checker |

Use the exact MCP tool name, command name, configuration key, and status value
defined by the implementation. Do not invent aliases in user instructions.

## Commands, results, and errors

Put one command in each code block. Explain why a command is required before
the command. State what a successful result contains after the command.

Use error messages that tell the user what happened and what safe action to
take.

| Avoid | Prefer |
| --- | --- |
| `Configuration is invalid.` | `The workspace policy has no allowed sandbox mode. Add \`read-only\` or \`workspace-write\`, then restart the bridge.` |
| `The job failed.` | `The job ended with \`unknown_exit\`. Do not assume that the workspace is unchanged. Inspect the workspace in read-only mode.` |

## Status and release wording

Do not report an operation as complete unless its required verification has
passed. Distinguish these states:

- `planned`: The work is accepted but not implemented.
- `implemented`: The code or document exists. This does not prove runtime
  behavior.
- `tested`: A stated test passed in its stated environment.
- `accepted`: The defined acceptance procedure passed.
- `released`: A signed tag and verified release artifact are available.

For a release procedure, state each verification step explicitly. For example:
verify the signed tag, verify that each archive is non-empty, run `unzip -t`,
and verify the published checksum.

## Review checklist

Before merge, check that the text:

- gives a direct action and an exact target;
- uses the project terms in this guide;
- identifies every approval, workspace, and network boundary;
- includes a verification step for a state-changing command;
- describes failure as fail-closed when the result is uncertain;
- does not expose secrets or unredacted operational data; and
- does not claim ASD-STE100 compliance without formal review.

## References

- ASD-STE100 Simplified Technical English, current official issue:
  <https://www.asd-ste100.org/>
- Project security, operational, specification, and release documents listed
  in [Scope and precedence](#scope-and-precedence).
