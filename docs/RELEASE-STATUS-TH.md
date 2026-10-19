# Release status

## v1.2.5 — released (19 October 2026)

- Signed annotated tag `v1.2.5`: object `11420f1ae968244195701b296db2f8ce419b793a`, peeled commit `6fbcd7ef278d5e45a95b7328c719c5b01cbcf522`; EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`. Local and fresh-fetch remote `git verify-tag` pass; GitHub reports the signature valid.
- [GitHub Release v1.2.5](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.5) publishes exactly `hermes-mcp-bridge-v1.2.5.zip` and external `SHA256SUMS`. ZIP SHA-256: `1f1c8a583cf7f51a88ec35ca3023c86342220f5baba37faed3f1724b04bf8d5f`.
- Built from the signed tag: 79 files under the single root `hermes-mcp-bridge-v1.2.5/`, no private config/state/venv/env/git/cache entries. Fresh-download `sha256sum -c SHA256SUMS`, `unzip -t` and byte comparison against the built assets pass.
- Extracted identity: version `1.2.5`, release identifier `v1.2.5`, source kind `release-archive`, embedded build input `a666d626da1fe716ce4b259d49eedfc3f97acc7d`, canonical default discovery 27. The signed tag identifies the final commit; the embedded revision identifies its reviewed build input.
- Scope: opt-in OpenCode execution from PR #40; release preparation from PR #41. Candidate WSL/archive suite 164/164 and discovery 27/28/33 pass; exact-head CI `39224170181` passes. Work-chat proof remains scoped to the recorded Dev candidate; cancellation remains controller evidence and permission-required remains fixture-only.
- Production remains v1.2.3; active Dev remains the tested git-worktree candidate. Publishing does not change profiles, runtimes or permission configuration. This post-tag documentation record does not modify the tag or assets.

### Deployment checkpoint (19 October 2026, ~18:44 +07)

The production deployment was upgraded to released v1.2.5 later that day. The bullet above preserves the post-tag record as written at release time, before this upgrade. Full live-record note: [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md).

- Identity: `bridge_version` — version `1.2.5`, release identifier `v1.2.5`, source kind `release-archive`, build provenance `release`, embedded build input `a666d626da1fe716ce4b259d49eedfc3f97acc7d`.
- State: `bridge_status` — state path `~/hermes-mcp-bridge-v1.2.5/state`, mode `0700`, no config warnings, watchdog running.
- Health: `hermes_health` authenticated (durable idempotency 86,400 seconds); `codex_health` `0.160.0` ok; `opencode_health` `v2.0.32` ok.
- Registry: parent tool registry exposes 33 tools (parent-side count, not a raw wire `tools/list` capture); `opencode_recent_tasks` ok with an empty `jobs` list; Local Hands disabled.
- Scope: identity, health, discovery, and the execution API listing only. No production model task was submitted during this checkpoint; production acceptance is not established by it.

### Fresh artifact re-verification (19 October 2026)

Maintainer-side automation re-verified the full v1.2.5 artifact chain from fresh inputs: a fresh remote tag fetch in a temporary bare repository, a fresh re-download of both release assets, checksum and ZIP-structure checks, and a byte-identical `git archive` rebuild from the signed tag. All checks pass. Full record: [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md). These are automation checks, not an external review; independent external reviewer approval of that record remains pending ([ROADMAP.md](ROADMAP.md)).

## v1.2.5 — historical pre-tag candidate (19 ตุลาคม 2026)

- Scope คือ PR #40 (OpenCode task execution opt-in ตาม `docs/SPEC.md` section 18) ที่ merge ที่ `main` commit `a666d626da1fe716ce4b259d49eedfc3f97acc7d` แล้ว (code head สุดท้าย `e7add7e`) candidate ยังไม่มี signed tag, ไม่เผยแพร่, และไม่ติดตั้งลง runtime การผลิต — production ยังเป็น released v1.2.3
- สถานะ: implemented + tested — 164/164 offline tests ผ่านด้วย project venv และ `-W error::ResourceWarning`, shellcheck และ `bash -n` ผ่าน, CI ผ่านที่ code head `e7add7e`; live acceptance: authenticated Dev Work-chat ผ่าน 19 ตุลาคม 2026 (real-model submit/result, resume, replay/recent, byte-verified native file creation; ส่วน native permission replies และ event subscriptions ยังไม่รองรับ — permission-required ครอบคลุมเฉพาะ fixture; ดู [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md)) ยังไม่ `released` และยังไม่ติด tag — release gates ที่เหลือ: tag/sign/publish และ asset verification ตาม RELEASE-RUNBOOK-TH.md
- `version_info.py` stamp: `RELEASE_IDENTIFIER` = `v1.2.5`, `BUILD_PROVENANCE` = `release`, `EMBEDDED_SOURCE_REVISION` = `a666d626da1fe716ce4b259d49eedfc3f97acc7d` (reviewed build input = `main` หลัง merge PR #40; signed tag ในอนาคตคือ authority ของ final commit), `MCP_DISCOVERY_COUNT` = 27 (canonical default; 28 เมื่อเปิด health adapter, 33 เมื่อเปิด execution opt-in ตาม [TESTING.md](TESTING.md))
- v1.3.0 ยังสงวนไว้สำหรับ Local Hands deferred track ตาม [ROADMAP.md](ROADMAP.md); MCP Events (section 15) ยัง BLOCKED ที่ subscription gate เหมือนเดิมและไม่อยู่ใน candidate นี้

## v1.2.4 — released (18 ตุลาคม 2026)

- เผยแพร่ผ่าน annotated tag `v1.2.4` ที่เซ็น GPG (EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`) บน main commit `213305638c135041c42a3f242d6c5665c49c3fdf` (tag object `191ec44e979739659d042ff7306446a2db0639fc`); `git verify-tag` ผ่านทั้ง local และจาก remote object ที่ fetch สด
- ทรัพยากร release: https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.4 มีเฉพาะ `hermes-mcp-bridge-v1.2.4.zip` (SHA-256 `e6deb0e6ab16d669836b0e361e2e875858e19597ef35dc7e4fc19010a6a5f3a9`; 65 ไฟล์ใต้ root `hermes-mcp-bridge-v1.2.4/`; สร้างจาก signed tag) และ SHA256SUMS ภายนอก (ไม่ถูก commit ลง source tree)
- ตรวจซ้ำจากการดาวน์โหลดจริงจาก GitHub: `sha256sum -c SHA256SUMS` ผ่าน, `cmp` กับไฟล์ build เท่ากันทุก byte, re-extract แล้ว `bridge.py version` รายงาน version `1.2.4` / release identifier `v1.2.4` / build_provenance `release` / source_kind `release-archive` / source_revision `0884482d8cf74d696b6c52a785282f65f2bd40fa` (embedded build input) / discovery 27
- production runtime ยังเป็น released v1.2.3; ทั้งหมดนี้ไม่ต้องมี rollout, service, config หรือการเปลี่ยน runtime
- บันทึก historical ระหว่าง candidate อยู่ด้านล่างครบถ้วน ไม่มีการรื้อ

## v1.2.4 — release candidate (historical; event ตามหลักฐานเดิม — 2026-10-18)

- Scope คือ PR #34 (OpenCode health adapter, disabled by default) และ PR #35 (legacy stdio discovery guard) ทั้งสอง merge แล้วที่ `main` commit `0884482d8cf74d696b6c52a785282f65f2bd40fa` candidate ยังไม่มี signed tag, ไม่เผยแพร่, และไม่ติดตั้งลง runtime การผลิต — production ยังเป็น released v1.2.3
- สถานะ: implemented + tested + live smoke บน Dev route จริงแล้ว (18 ตุลาคม 2026) offline regression suite ผ่านครบด้วย project venv และ `-W error::ResourceWarning`; `bash -n` และ shellcheck ผ่าน ผล live acceptance เป็น bounded PASS — identity/status/tool visibility ของ candidate ยืนยันผ่าน plugin Dev จริง แต่ `server/discover` → `-32601` บน tunnel สังเกตไม่ได้เพราะ dispatcher log ไม่บันทึก method/outcome code (ตารางผ่าน/ไม่สังเกตได้/ค้าง อยู่ใน [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md)) ยังไม่ `released` และยังไม่ติด tag — release gates ที่เหลือ: รีวิว acceptance record นี้, archive สุดท้ายจาก signed tag และ tag/sign/publish ตาม RELEASE-RUNBOOK-TH
- `version_info.py` stamp: `RELEASE_IDENTIFIER` เป็น `v1.2.4`, `BUILD_PROVENANCE` เป็น `release`, `EMBEDDED_SOURCE_REVISION` เป็น `0884482d8cf74d696b6c52a785282f65f2bd40fa` (reviewed build input ตามแบบ v1.2.3; signed tag ในอนาคตคือ authority ของ final commit)
- Local archive candidate สร้างจาก candidate commit ตาม RELEASE-RUNBOOK-TH Phase B ยกเว้นขั้น tag/publish: ตรวจ ZIP structure, ตรวจว่าไม่มี `.venv/`, `state/`, `.env`, `bridge-config.json*` หรือ `.git/` ใน archive, re-extract แล้วรัน `./bridge.sh version` และ stdio fixture probe จาก tree ที่แตกแล้ว; checksum ไม่ถูก commit ลง source tree (ห้าม self-reference) และยังไม่มีการอัปโหลด
- MCP Events (SPEC.md section 15) ยัง BLOCKED ที่ subscription gate เหมือนเดิม และไม่อยู่ใน candidate นี้ — งานนี้ถูกเลื่อนออกจาก v1.2.4 เป็นงานไม่ผูกเวอร์ชัน (deferred, no assigned release) ไม่มี event channel หรือ capability ใหม่

## v1.2.3 — released (4 ตุลาคม 2026)

- Scope is limited to the `SPEC.md` worker-supervision invariant. The change adds no MCP tools and does not expand permissions.
- The branch records worker/child liveness, rejects reused PIDs and Linux/WSL2 zombies, preserves stable running-response fields, and keeps cancellation targeted at the original process group.
- Automated CI passed on the current PR head. WSL2 acceptance passed the worker-zombie/child-alive, child-gone fail-closed, and cancel-after-worker-loss cases. The 75-test WSL2 regression run completed without `ResourceWarning`.
- Independent review passed after the WSL2 evidence and documentation record were complete. `version_info.py` is stamped with release identifier `v1.2.3`, build provenance `release`, and reviewed build-input revision `60de77fa8945a67eb578828e710f1cacc63680e5`.
- signed tag `v1.2.3` points to `c610660637dbdcfa0b8ddb7bbf01ed22ae66055d`; `git verify-tag --verbose` passed with EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- [GitHub Release v1.2.3](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.3) publishes the ZIP and external `SHA256SUMS`. The verified archive checksum is `c231f8563543dbfa9eafa240c5e8e15f44434103940352066e65b58162cb5458`.
- Phase B post-download verification passed: `sha256sum -c SHA256SUMS` and `unzip -t` completed without errors. The asset checksum is not committed to the source tree.

## v1.2.2 — released (23 กันยายน 2026)

- เพิ่ม `./bridge.sh version` และ MCP `bridge_version` แบบ local-only; discovery contract ยืนยันตาม canonical count ใน `TESTING.md`.
- เพิ่ม embedded identity/provenance และ fail-safe `unknown` fields สำหรับ config/provenance ที่ไม่สมบูรณ์ โดยไม่เปิดเผย path, prompt, output หรือ secret.
- แก้ Codex workspace-write lifecycle ด้วย detached durable worker: acceptance Dev ยืนยัน `completed`, `exit_code: 0`, `transition_actor: worker`, JSONL output retrieval และ exact marker bytes.
- CI ผ่าน และ Dev live acceptance ผ่าน: CLI/MCP identity parity, `bridge_version` ผ่าน Secure MCP Tunnel แม้ตั้ง Hermes/Codex ให้ unavailable, ไม่มี secret/path leak, และ restore config กลับ byte-for-byte ด้วย `cmp`.
- independent review ผ่านแล้ว และ Phase A stamp กำหนด `release_identifier` เป็น `v1.2.2`, `build_provenance` เป็น `release`, พร้อม reviewed build-input revision `079f1fc2386de62cfa52a5bbe38645e4efdbdd2e`; signed tag เป็น authority ของ final commit แยกจาก embedded build input.
- signed tag `v1.2.2` ชี้ commit `f8f1d93930882dc3e669dab0a05b4bd5c1834bef`; `git verify-tag --verbose` ผ่านด้วย GPG EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- [GitHub Release v1.2.2](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.2) เผยแพร่ ZIP และ external `SHA256SUMS`; SHA-256 ของ archive คือ `e9582153c57458e3ca73a4c169f46653662377b004c9c2ee552824c4ffce5dc5`.
- Phase B re-verification หลังดาวน์โหลดผ่านทั้ง `sha256sum -c SHA256SUMS` และ `unzip -t`; release asset ไม่ถูก commit กลับเข้า repository.
## v1.2.1 — released (22 กันยายน 2026)

- เพิ่ม explicit work contexts แบบ metadata-only: 4 MCP tools, discovery contract 26 tools, Hermes resume จาก bridge-owned session เท่านั้น และ Codex bind เฉพาะ workspace/job metadata โดยไม่ replay prompt/output.
- Live acceptance ผ่าน: Hermes continuation ข้าม ChatGPT chat ด้วย `context_id` เดียว, Codex workspace/job binding, closed-context denial และ audit redaction.
- regression 63/63 ผ่านเมื่อใช้ project `.venv/bin/python` พร้อม `-W error::ResourceWarning`; shellcheck และ Bash syntax ผ่าน.
- release commit คือ `d86703d1e1d8f675b656588208b3f557f5b63598`, signed tag `v1.2.1` ถูก GitHub ตรวจเป็น Verified.
- [GitHub Release v1.2.1](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.1) เผยแพร่ ZIP และ external `SHA256SUMS`; SHA-256 ของ archive ที่ตรวจหลังดาวน์โหลดกลับผ่านคือ `36c01197d7dfb89b7a64a22ad32b35475762915076520c84ced8affb542e9b51`.

## v1.2.0 — released (22 กันยายน 2026)

- WSL2 live acceptance ผ่านทั้ง ext4 และ DrvFS: discovery 22 tools, strict resolver, secret/path/binary/symlink denial, audit redaction และ case-collision fail-closed.
- Critical fallback OFF/OFF/ON ผ่าน: เมื่อ Hermes ใช้ไม่ได้และ Codex binary หาย Local Hands health/list/read ยังคงใช้ได้; ไม่มี Hermes/Codex task ถูกส่งระหว่างทดสอบ.
- คืน production state แล้ว Local Hands เป็น `disabled`, workspaces ว่าง และ diagnostics ไม่มี `config_warnings`.

release commit คือ `bd56bafd4fcefcfbdf26699ab281cc1a6798bfc9`, จาก signed tag `v1.2.0` (GPG EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`). GitHub Release เผยแพร่ ZIP และ `SHA256SUMS`; SHA-256 ที่ตรวจหลังดาวน์โหลดกลับผ่านคือ `621db6718323fb0639c67a9eac677af23de31a4f0f6e4d09b413d05f82960d08`.

## v1.0.1 — released (21 กันยายน 2026)

- schema ของ `codex.approval_ttl_seconds` ตรงกับ runtime ที่ 60–86,400 วินาที พร้อม regression test ที่ขอบเขต 59/60
- เอกสารระบุข้อจำกัด watchdog: enforcement อัตโนมัติอยู่ใน persistent MCP server ไม่ใช่ process ของ local approval CLI
- regression suite 48/48, shellcheck และ WSL2 read-only live acceptance ผ่าน
- signed tag `v1.0.1` ถูก GitHub ตรวจเป็น `Verified` และ release archive ผ่าน `sha256sum -c`: `a20a07aaeb0baeb885c85223dab9eba61c8a0ce1be20bb83d0e422faaa45c9d3  hermes-mcp-bridge-v1.0.1.zip`

## v1.0.0 — released (21 กันยายน 2026)

- security review และ regression 48 tests ผ่าน; แก้ schema validation ให้สอดคล้อง audit/runtime policy
- RC2 WSL2 full acceptance ผ่านสำหรับ Hermes/Codex, idempotency, write approval, cancellation และ audit/recovery semantics
- `SHA256SUMS` เผยแพร่แล้ว: `04421690f877807975810dfeffb29ec6412d8313103409cfd5713300e32de793  hermes-mcp-bridge-v1.0.0.zip`
- signed tag `v1.0.0` ถูก GitHub ตรวจเป็น `Verified` และชี้ไปที่ commit `2b280b2d3a763f69afa417bc76bdca6b801553fc`

## v0.9.0 — build verification

- Python compilation, shell syntax และ regression suite 48 tests ผ่าน (`-W error::ResourceWarning`)
- MCP stdio discovery ยืนยัน 19 tools รวม `bridge_status`
- `bridge_status` ไม่เรียก Hermes HTTP หรือ Codex CLI upstream
- Config schema version 1 ปฏิเสธ known type ที่ผิดและรายงาน unknown key เป็น warning
- heartbeat และ `stale` label ผ่าน live acceptance บน WSL2; `approval_stale` มี regression coverage แต่ยังไม่ได้สร้าง upstream approval workflow จริง
- v0.9.1 แก้การอ่าน capability เป็น `run_approval_response`; v1.0.0 ตรวจพบ capability แล้ว แต่ upstream approval-event live acceptance ถูกเลื่อนไป v1.1.0 ตาม roadmap

## ผ่านแล้วใน build environment

- Python syntax compilation
- Hermes regression tests 16 รายการ
- Codex policy/process/audit/recovery/model-policy/lifecycle tests 24 รายการ
- MCP stdio discovery/integration 1 รายการ: พบ 18 tools
- tunnel script tests 2 รายการ
- รวม 44 tests ผ่านทั้งหมด (`-W error::ResourceWarning`)

## Live acceptance ที่ผ่านบน WSL2

- `./bridge.sh doctor` และ `./bridge.sh codex-doctor`
- restart Secure MCP Tunnel และ discovery Hermes 10 + Codex 6 tools
- Codex CLI `0.155.1` กับ workspace allowlist `/mnt/e/Projects/OpenHDK-validation`

## v0.8.0 — full live acceptance (2026-09-21)

- `bridge_diagnostics` และ `codex_health` ผ่าน Secure MCP Tunnel: Hermes authenticated, Codex CLI `0.155.1`, watchdog interval 15 วินาที และ watchdog กำลังทำงาน
- งาน read-only ที่เริ่ม `sleep 120` ถูกยกเลิกผ่าน MCP ขณะยังรันอยู่; `status`/`result` ปลายทางเป็น `cancelled` และ audit เป็น `submit → start → cancel`
- ไม่พบการแก้ไข workspace หรือ network access ระหว่าง test
- ตั้ง runtime policy ชั่วคราว 5 วินาทีแล้วปล่อยงาน `sleep 120` โดยไม่ poll: watchdog ยุติงานเป็น `timed_out` และ audit บันทึก `cancel(timed_out)`
- restart tunnel ระหว่างงาน `sleep 30` แล้ว reconnect หลังงานจบ: job ปลายทางเป็น `unknown_exit`, result รายงาน `recovered_after_restart: true`, audit เป็น `finish(unknown_exit)` พร้อม `exit_code: null`
- คืน runtime policy production เป็น 1,800 วินาทีแล้ว

## v0.8.0 — build verification

- lifecycle hardening, atomic concurrency reservation และ watchdog regression tests ผ่าน
- CI เพิ่ม shellcheck พร้อมคง `bash -n`
- full production acceptance บน WSL2 ผ่าน: cancellation, watchdog timeout และ `unknown_exit` recovery semantics

## v0.7.0 — build verification

- `codex_submit_task` รองรับ optional `model` และ `reasoning_effort` โดยไม่เพิ่ม MCP tool ใหม่ (discovery ยังคง 18 tools)
- policy test ยืนยันการปฏิเสธ model/effort นอก allowlist ก่อนเริ่มงาน และตรวจ argv ที่ส่ง override ที่อนุญาต

## Live acceptance ที่ผ่านสำหรับ v0.7.0 — 2026-09-20

- bridge `/home/somchaip/hermes-mcp-bridge-v0.7.0` ทำงานผ่าน Secure MCP Tunnel; Hermes authentication และ Codex health ผ่าน
- `codex_health` ยืนยัน policy model IDs `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` และ effort `low/medium/high`
- งาน default `read-only` ตอบ `V070_DEFAULT_OK`; งาน override `gpt-5.6-sol` + `high` ตอบ `V070_MODEL_POLICY_OK`; ทั้งคู่ exit code `0` และไม่ต้อง local write approval
- audit export เก็บ model/effort และ lifecycle แบบ redacted ตามนโยบาย
- display name `GPT-5.6 Sol` ถูกปฏิเสธ จึงยืนยันว่าค่า allowlist ต้องเป็น Codex model ID จริง ไม่ใช่ชื่อที่แสดงใน UI

## Live acceptance ที่ผ่านสำหรับ v0.5.0 — 2026-09-20

- `bridge_diagnostics` ผ่าน Secure MCP Tunnel: Hermes auth verified, Codex CLI `0.155.1`, state mode `700` และ audit enabled
- Codex `read-only` job ใน `/mnt/e/Projects/OpenHDK-validation` จบสำเร็จโดยไม่แก้ไขไฟล์ และทำให้ `audit.jsonl` ถูกสร้าง
- Codex `workspace-write` job ผ่าน local terminal approval: สร้าง/ตรวจ/ลบไฟล์ทดสอบชื่อเฉพาะไฟล์เดียวและยืนยันว่าไม่มีไฟล์คงเหลือ
- สถานะของ write job แสดง `recovered_after_restart: true` ตาม semantics ที่ประกาศไว้ เพราะ terminal approval process เป็นผู้เริ่ม job แล้ว tunnel process อ่านสถานะต่อจาก persisted state
- Codex read-only cancellation job ถูกยกเลิกขณะรัน; สถานะสุดท้าย `cancelled` และไม่มีการแก้ไขไฟล์

## Live acceptance ที่ผ่านสำหรับ v0.6.0 — 2026-09-20

- discovery 18 tools รวม `bridge_audit_recent`
- `codex_health` แสดง workspace policy ของ `/mnt/e/Projects/OpenHDK-validation`: modes, prompt/runtime limit, concurrency 1 และ approval TTL 3,600 วินาที
- read-only job จบสำเร็จ; `bridge_audit_recent` แสดง `submit → start → finish` โดยมี workspace/policy root/prompt length เท่านั้น ไม่มี prompt, output หรือ credential
- write job คืน `pending_local_approval` พร้อม `expires_at` และ policy root; cancel job ที่ยัง pending เปลี่ยนเป็น `denied` โดยไม่เริ่ม process
- probe workspace `/mnt/e` ถูกปฏิเสธด้วย `workspace is outside allowed_workspaces`
