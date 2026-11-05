# SPEC §24 — R0/R1 metadata prebinding preparation record

Date: 25 October 2026. Plan ID: `S24-PREBIND-20261025-01`.
Status: **INACTIVE_PREPARATION_RECORDED_PENDING_BINDINGS — R2 HOLD**.
This record requests independent evidence review. It does not declare R1 complete.

<a id="s24-prebind-r0-r1-preparation-record"></a>

## Scope and approval

The [staged plan](S24-METADATA-PREBIND-PLAN-TH.md) was merged through PR #104:
reviewed head `30b5a9319d8041491b21672cc5f94bbe1dd7e27c`,
merge `b100161d14b6a4212e52ecc2a3e4ce394da5ffd0`.
The operator supplied the eighth external review for the plan. Merge did not grant execution.

The operator then supplied these separate statements:

> ยืนยัน **“อนุมัติ R0 แบบ read-only ตามแผน #104”**

> อนุมัติ R1 ตามแผน #104

After the first R1 window expired, the operator authorized only the remaining work:

> อนุมัติ R1 รอบใหม่ ≤15 นาที เฉพาะงานที่เหลือนี้ได้

The operator separately confirmed the private key destination:

> ยืนยันให้บันทึก key ที่พาธนี้ได้

No exact approval timestamp was supplied or invented. The destination remains private.
The new R1 window did not reset the expired window or authorize R2, discovery,
client/peer service start, fixture execution, an original-runtime change or a release.

## Evidence attribution

All guest commands, file results, measurements and Platform provisioning below are
**operator-reported**. The author supplied command batches but did not log into the
guest or independently inspect its private files, credential, dossier or Platform
authorization. The returned dossier hash is correlation, not authentication.
Source/API review and author-side diagnostics are identified separately.

## R0 inventory

The operator reported VMware guest identity, x86_64, Python 3.14.4 and available
venv/ensurepip modules. The nominated existing candidate venv reported
`is_venv=true`. Its four direct dependencies matched the pinned lock:
mcp 1.30.0, httpx 0.28.1, python-dotenv 1.2.3 and PyYAML 6.0.3.
No tunnel-client was found on PATH; that is not a full-disk absence claim.

Guest MemAvailable was 1,137 MiB; available home-filesystem space was 7,646 MiB.
The Windows reading was 2,601 MiB. The operator confirmed that the whole R0 round
was below 600 seconds and that observed host RAM did not fall below 1,536 MiB.
The initial command's 8-second duration measured only that command, not the whole
round. Host observation is an operator statement, not a continuous recorded series.
R0 supported proceeding to separately approved R1; it did not prove route readiness.

## First R1 window and retained failures

The operator reported a 29,420,141-byte v0.0.18 Linux-amd64 archive with SHA-256
`3c82307316acd93c88a384b62af1d81d3f4cb0efa975f9c0bfaef922866a04c4`.
Its seven entries passed the supplied directory/path/type/size checks.
Extraction and subsequent reads reported the tunnel-client binary SHA-256
`55c48566e682473a602eea4951978d27acc0f2c8de2340b684a8b114feba7a83`.
These hashes do not authenticate the downloaded binary or prove its behavior.

Guest peer/manifest bytes matched the plan's source/file hashes.
The client was executed for `--version` and `--help` inspection only.
No `run`, peer start or discovery was reported.
Version stdout was exactly `0.0.18+274a5588414819f063d27100a4fb1096aae3830f (git sha: 274a5588414819f063d27100a4fb1096aae3830f)`; stderr was empty.
The first comparison incorrectly rejected the build-metadata suffix.
The correction checked the full saved string against the pinned ref without
rerunning version. This was a supplied-check defect, not a binary-version mismatch.

The operator reported help/Python binding completion at 490.25 seconds and 31
installed distributions. The private record retained the venv argv path separately
from the resolved executable. No source/manifest substitution was made.

The operator reported creating a new tunnel and new runtime credential
through Platform UI. Their scope, permissions and association were not independently
verified. Later, key saving stopped before prompting: the first R1 window had reached
2,762.5 seconds. No key destination existed then. This window remains expired and
incomplete. No time marker was changed to make it pass.

## Separately approved R1 continuation

The new window first stopped at the private tunnel-binding stage before any prompt.
The operator reported dependencies recorded, no profile or key file, and no selected
health-port entry in the guest TCP tables. An author-side disposable pseudo-terminal
reproduced `UnsupportedOperation: File or stream is not seekable` for text-mode
`r+`; separate read/write opens succeeded. The guest script had suppressed its
specific exception, so that exact guest exception was not directly captured.

The corrected continuation used local hidden terminal entry. It retained the same
new-window marker and existing evidence. It rechecked client/peer/manifest hashes,
used exclusive file creation and parsed the profile locally without invoking the client.
The operator returned `INACTIVE_PREPARATION_RECORDED_PENDING_BINDINGS` at
221.35 seconds: profile created, key mode 0600, client/peer service not started.
The dossier SHA-256 was
`d06bb3e2eaab64354089c193c1dc4fb61e45a0a9a9dbbd6ebe10e0114bcc262f`.
The profile contains an environment-variable reference, not the credential.

The final Windows reading was 2,412 MiB. In answer to the explicit question about
this new R1 round, the operator confirmed monitoring without an observed value
below 1,536 MiB. This is not a recorded continuous minimum. No final public numeric
guest RAM/disk/growth/log series or original-runtime continuity probe was supplied.

## Remaining bindings and next gate

The private record itself retains these gaps:

- Exact host/control and Platform/workspace association.
- Route authorization and credential validity; no authenticated request tested them.
- Reviewed clean launch environment and credential-loading method.
- Original Production/Dev continuity methods and observations.
- Complete client/peer/controller/observer process accounting, finite supervision,
  exact stop/confirmation methods and writer coverage.
- Plugin identity, which remains deferred to separately approved R2.
- Complete resource observations, including disk/growth/log bounds.

The author has not read the private profile/dossier. A local parse is not an
independent config review, client doctor result, port reservation or live-route proof.
The inactive profile targets only the reviewed metadata peer; candidate/fixture
references in the plan do not grant permission to load them.

**R1 remains pending bindings and independent evidence review. No R2 approval or
activation token is created.** Do not start a client/peer, connect/refresh a plugin,
extend a window or automatically retry from this record.
First resolve the remaining bindings and review their proposed methods offline.
Any further guest work needs a valid explicit scope; expired windows stay expired.
R2 still needs all prerequisites and its separate finite operator approval.

Phase B/scoped §22 and PR #80 remain HOLD. PR #96 remains a separate unmerged draft.
No guest readiness, completed metadata attempt, complete cessation, historical-run
disposition, release or deployment is accepted here. Earlier records remain unchanged.
