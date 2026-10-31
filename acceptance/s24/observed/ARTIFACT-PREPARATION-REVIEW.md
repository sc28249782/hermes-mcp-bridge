# E11 — exact artifact-preparation source, before setup/provisioning

Date: 31 October 2026. Reviewed input E10: `2b3abd25`.
Status: **SOURCE CANDIDATE FOR REVIEW; LIVE DOWNLOAD NOT RUN; SETUP BLOCKED**.
Continue #112 draft and [J0](J0-CAPABILITY-SOURCE-REVIEW.md).

## 1. Exact source and proposed invocation

| Source | Author-computed SHA256 |
| --- | --- |
| prepare_join_artifact.py | `293f0f61077d5636bd728a779c803097887ae84bf7c4c261d42d04c0591be0a4` |
| test_join_artifact.py | `d116c70596dd77baf778259884ae0d99d219c894c45c3a86ba31ded0355f6fae` |

The proposed, **not yet executed**, command on disposable GitHub-hosted Linux is:

```sh
python -W error::ResourceWarning -I -S -B acceptance/s24/observed/prepare_join_artifact.py --download-and-inspect
```

This command is NOT added to CI in E11. Review its exact source before authorizing
that artifact-preparation action. Current CI runs only `test_join_artifact.py`
with the same Python flags on 3.12/3.14. These synthetic tests use in-memory
responses and archives; no archive from the provider is downloaded or opened.
The existing 69-control suite remains separate and unchanged; 13 artifact controls
are not thirteen new R1 integration passes.

The driver refuses other argv and non-GitHub-hosted Linux environments before
network access. No root privilege, subprocess, SSH, WSL, guest boot, package
installation, extraction or archive program execution is used. Its Python process
has a 120 s SIGALRM, 512 MiB address-space hard limit and disabled core dumps.
These are NEW preparation-process budgets, not observer timer extensions or
operational stop proof. No setup/import action occurs even on success.

## 2. Exact read/write/network contract

1. Read adjacent `J0-PROVIDER-SOURCE.json`; require its reviewed SHA256
   `41e2e56ff490475d899894e61c93b0e518439551f193031a8bef38b447805fbc`, selected
   URL and provider digest to match literal constants. No arbitrary URL/path/hash
   parameter or floating distribution selection.
2. One HTTPS request to the exact E10 URL, default certificate verification,
   identity encoding, 15 s socket timeout; disable proxies, redirects, retry and
   alternate endpoints. Require HTTP 200, unchanged URL and valid bounded
   Content-Length if supplied. Network error, redirect, partial/oversized response
   or digest mismatch ends HOLD. A missing Content-Length still has a byte cap.
3. Write at most 1 GiB into ONE new private `TemporaryFile` in the CI temp area.
   It is removed on close; no prepared rootfs directory is created. Operator preparation paths/accounts/keys/resources are not accessed; existing
   services/configuration are not modified. Python imports and TLS verification
   use the installed interpreter/libraries/trust store. The script prints no temporary path or exception detail.
4. Hash the same open stream and compare with the exact provider-reported SHA256
   BEFORE invoking the archive parser. Matching bytes establish digest equality,
   not a provider signature, accepted setup or a bootable/importable image.
5. Stream-parse supported tar compression without extracting to disk. Refuse
   absolute/traversal/backslash/control-character names, normalized duplicates,
   sparse/device/FIFO/unknown types, over 200,000 members or over 4 GiB declared
   logical size. Link targets are metadata only; never resolve/follow them.
   A recognized regular file/directory/link is not automatically safe for a later
   extractor. The process memory/wall caps also bound parser-internal processing;
   these checks are not a generic safe-extraction implementation.
6. Hash an archive-order catalog of normalized header fields (name, type, size,
   mode, UID/GID, link), plus content hashes only for selected REGULAR entries:
   os-release, python3/versioned python3 binaries, sshd, dpkg status and two WSL
   config files. Selected contents are capped at 32 MiB each, names/links at 4096
   characters and selected entries at 32. Missing entries remain missing; no
   symlink resolution or installed-package/version inference is made. The catalog
   is NOT a complete content-tree digest or a prepared-image manifest.
7. Emit one ASCII JSON receipt, at most 65,536 bytes, after closing the temporary
   archive. It records computed archive/header/selected hashes and explicit false
   readiness, import-compatibility, prepared-artifact, guest and scope flags.
   Unsupported format/limit/error yields constant HOLD and exit 2. No retry,
   extraction, package setup or downstream action follows success or failure.

The archive remains **NOT DOWNLOADED / NOT BYTE-VERIFIED / NOT INSPECTED** in E11.
The provider-reported digest in E10 is unchanged. Source/control hashes above are
computed from actual source bytes; no archive/kernel/guest hash is invented.

## 3. Setup-source dependencies and review exit

| Stage | Exact disposition |
| --- | --- |
| Provider retrieval/inspection source | Candidate above, with 13 offline controls; live execution not wired into CI |
| Artifact contents/format/guest binaries | UNKNOWN until a separately reviewed preparation attempt produces an actual receipt |
| Guest package/build recipe | BLOCKED pending actual contents and exact immutable package inputs; no apt update/install or postinstall execution supplied |
| Prepared image/manifest | UNBOUND; inspection receipt is not a prepared image, extractor approval or release artifact |
| Windows configured kernel/boot/coexistence | UNBOUND; E10's two candidate kernel paths were ABSENT_OR_UNREADABLE, not proof of global absence |
| New distro/name/path/account/key/port/setup argv | UNBOUND; no executable provisioning template with invented bindings |
| Independent owner/deadline/stop/unregister | UNBOUND; no WSL engine/service/global configuration changes or lifecycle authority |

The next concrete source-review decision is this preparation driver, its bounded
single request/temporary writes and receipt semantics. If accepted, a separate
finite disposable-CI preparation attempt can establish actual archive evidence.
Only then can exact image/package/setup source be completed and reviewed before
ANY provisioning. E11 completes the artifact-preparation source portion, not the
full artifact/setup work package. An unavailable URL/format/prerequisite remains
HOLD; it does not authorize an alternate version/download, WSL update, existing
guest or operator VM. Existing eighteen-row dispositions and A1–A5/A6–A7 remain
open. Runtime sources/pins, sampler actors and observer timers are unchanged.
No automatic source acceptance, merge, R1 scope or R2 authorization is claimed.
