# E10 — J0 capability and provider-source checkpoint

Date: 30 October 2026. Based on approved-as-design E9 at `0b5927c3`.
Status: **PARTIAL J0 EVIDENCE FOR REVIEW — NOT READY FOR SETUP**.
Continue [the join plan](WINDOWS-LINUX-JOIN-PLAN.md) on the same draft #112.
This checkpoint does not supply executable guest setup or provisioning authority.

## 1. Provider-source candidate and attribution

[J0-PROVIDER-SOURCE.json](J0-PROVIDER-SOURCE.json) records the exact Microsoft WSL
manifest commit/path, Git blob identity, size and author-computed SHA256 of the
retrieved manifest bytes. The contents API response was fetched at the exact
commit; its bytes reproduce the Git tree's blob SHA-1 and size. This verifies the
retrieved metadata identity, not a downloaded rootfs or a provider signature.

The selected entry is specifically `Ubuntu-24.04`, amd64, not the moving default
`Ubuntu` entry. It names `ubuntu-24.04.5-wsl-amd64.wsl` on releases.ubuntu.com and
reports SHA256 `bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e`.
That is **provider-reported archive SHA256**, not an author-computed archive hash.
No archive was downloaded, opened, imported or executed. Its archive format,
contents, interpreter/sshd, package manifest, license/signature verification and
suitability for the proposed explicit import method remain unverified. A `.wsl`
filename alone does not establish those properties. Do not install it directly
or use this JSON as a setup/approval token. Later artifact preparation must bind
actual bytes/content before import, including any exact guest-only package steps.

Immutable metadata source:
[Microsoft WSL manifest at the recorded commit](https://github.com/microsoft/WSL/blob/341f1ddf76f089ff6351590b03f92bad30041725/distributions/DistributionInfo.json).
This metadata lookup is separate from the existing CI controls and from any
operator environment; its retrieval date is not a guest execution timestamp.

## 2. Exact CI-only read scope

`Test-WindowsCarrierCapabilities.ps1` retains E8's GitHub-hosted Windows guard,
optional-feature and sshd service-state queries. It adds image label/version and
Windows version, plus size, SHA256 and file-version snapshots at four locations:

| Role | Exact candidate location |
| --- | --- |
| Native SSH client | `%WINDIR%/System32/OpenSSH/ssh.exe` |
| Inbox WSL client | `%WINDIR%/System32/wsl.exe` |
| Inbox kernel candidate | `%WINDIR%/System32/lxss/tools/kernel` |
| MSI kernel candidate | `%ProgramFiles%/WSL/tools/kernel` |

The existing workflow step runs this checked-in script in a fresh pwsh child.
The script invokes none of these files. It reads only these fixed candidates,
rejects directories/reparse-point files and sizes outside 1 byte–256 MiB, and hashes
at most four files. No recursion, user-profile/Store scan, registry or distro
listing, WSL/native child invocation, download, install, import, boot, feature or
service mutation is included. Missing/inaccessible files remain
ABSENT_OR_UNREADABLE; a rejected file is not a selected alternate. No error
message/path or credential is emitted. The receipt prints symbolic roles.

These are read-only snapshots, not executable admission checks: no retained
handle/TOCTOU guarantee, configured-client/kernel selection or future runner
identity is claimed. Other installation locations remain unexamined. File
presence/hash/version and Enabled features cannot prove WSL2 boot, nested
virtualization, guest procfs/pidfd, locality, coexistence or a working SSH route.
Existing distro activity stays UNKNOWN_NOT_QUERIED. The script explicitly emits
`j0_ready=false`, `wsl_invoked=false`, `guest_started=false` and false scope flags.
The existing five-minute Windows job bound is unchanged; a timeout is not a
readiness pass or operational cessation proof.

## 3. Remaining J0 bindings and next review boundary

| Join-plan §2 binding | Disposition after this checkpoint |
| --- | --- |
| Windows image/client/kernel/boot support | CI file/image snapshots only; configured kernel and boot/virtualization support UNBOUND/NOT_TESTED |
| Existing distributions/activity | UNKNOWN; no reuse or implicit default operation |
| Rootfs provenance/content/archive hash | Metadata source pinned; archive bytes/content and prepared artifact UNBOUND |
| Python/sshd/client identity and interpreter matrix | Candidate host-client snapshot only; guest binaries and joined matrix UNBOUND |
| New distro/path/destinations/account/keys | UNBOUND; no names or private operator values inserted |
| Loopback endpoint/reachability | UNBOUND; no bind or network probe |
| Setup/launch/read/write/stop commands and owner | UNBOUND; no setup implementation in this delta |
| Resources/cleanup/evidence ownership | UNBOUND; no lifecycle/stop guarantee from CI teardown |

J0 is still NOT READY. Review these bounded capability methods and provider-source
candidate first. Then prepare exact artifact/setup source and hashes for review;
only after that separate review may guest provisioning be considered. Do not
silently fill missing fields with floating downloads, default-distro commands,
WSL updates, feature enablement, reboot, global settings or an operator VM.
A missing prerequisite remains ENVIRONMENT_UNAVAILABLE/HOLD, not a waiver or a
completed row. The actual Windows SSH/collect/CIM join, outer supervision/stop,
all eighteen row dispositions and A6/A7 remain open. No runtime/pins, timers,
sampler actor or existing control obligations change. R1 NOT AUTHORIZED; R2 HOLD.
