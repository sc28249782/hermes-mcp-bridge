# Hermes Local Hands — สถาปัตยกรรมและขอบเขตความปลอดภัย

สถานะ: เอกสารออกแบบสำหรับ roadmap หลัง `v1.0.1`  
เป้าหมายรุ่นแรก: `v1.2.0` แบบ read-only (`health/list/read`)  
เอกสารที่เกี่ยวข้อง: `ROADMAP.md`, `LOCAL-HANDS-IMPLEMENTATION-PLAN-TH.md`, `HERMES-MCP-BRIDGE-TECHNICAL-ARCHITECTURE-TH.md`, `CODEX-WSL2-TH.md`

## 1. เป้าหมาย

Local Hands ทำให้ ChatGPT เรียก primitive ที่ควบคุมได้บน WSL2 และในระยะถัดไปบน Windows host โดยตรง เช่น อ่าน/แก้ไฟล์ รัน build/test ตรวจ process และควบคุม GUI ภายใต้นโยบายของเครื่องผู้ใช้

ข้อกำหนดสำคัญที่สุดคือ Local Hands ต้องเป็นอิสระจาก quota และ runtime ของ Hermes/Codex:

```text
ChatGPT Web
    │
Secure MCP Tunnel
    │
hermes-mcp-bridge
    ├── Hermes backend       (อาจ unavailable/quota exhausted)
    ├── Codex backend        (อาจ unavailable/usage limited)
    └── Local Hands backend  (ยังทำงานได้โดยไม่เรียกสอง backend ข้างบน)
            ├── WSL2 adapter
            ├── Windows adapter      [v1.4.0]
            └── Computer-use helper  [v1.5.0]
```

คำว่า “อิสระ” หมายถึงเส้นทาง `hands_*` ไม่เรียก Hermes Runs API, model provider หรือ Codex CLI ไม่ได้หมายความว่าจะใช้งานได้เมื่อ ChatGPT, Secure MCP Tunnel, bridge process หรือ WSL2 หยุดทำงาน

### 1.1 ที่มาของแนวคิดและการให้เครดิต

แนวคิด “ChatGPT เป็นสมอง ส่วน local MCP server เป็นมือ” และบทเรียนเรื่อง tool surface, deletion refusal, working-copy redirect, computer post-action verification และข้อจำกัดของ consent friction ได้แรงบันดาลใจจาก [halochamp/Endeavor_Hands](https://github.com/halochamp/Endeavor_Hands) ซึ่งเผยแพร่ภายใต้ MIT License, Copyright (c) 2026 Poomwat Jarussri

Local Hands เป็นงานออกแบบใหม่สำหรับ Windows/WSL2 ภายใต้ trust model ของ `hermes-mcp-bridge`; ณ ขั้นเอกสารนี้ไม่มีการคัดลอก source code หรือ asset จาก Endeavor Hands หากอนาคตมีการนำโค้ดมาดัดแปลง ต้องคง copyright/MIT notice ของ upstream ไว้ใน source/distribution ตามเงื่อนไข MIT และบันทึกใน `THIRD_PARTY_NOTICES.md` ส่วนโค้ดของโครงการที่เขียนขึ้นใหม่ยังอยู่ภายใต้ Apache-2.0

## 2. หลักการออกแบบ

1. **Sibling backends** — Hermes, Codex และ Hands มี lifecycle/health แยกกัน ไม่มี backend ใดเป็นทางผ่านบังคับของอีก backend
2. **Deterministic executor** — Hands รับคำสั่งที่มีโครงสร้าง ตรวจ policy แล้วลงมือ ไม่วางแผน ไม่ตัดสินใจแทน agent และไม่ delegate กลับไปหา agent
3. **Fail closed** — config ผิด, path กำกวม, approval หมดอายุ, helper version ไม่ตรง หรือไม่สามารถพิสูจน์ containment ได้ ต้องปฏิเสธ
4. **Least privilege** — upgrade แล้ว Hands ปิดเป็นค่าเริ่มต้น ไม่มี workspace เขียนได้ ไม่มี executable หรือ Windows action ที่อนุญาตโดยอัตโนมัติ
5. **Structured operations** — เริ่ม execution ใน v1.3.0 โดยรับ executable และ argv แยกช่อง ใช้ `shell=False`; ไม่รับ shell command string แบบ unrestricted
6. **Local human approval** — การอนุมัติทำใน local TTY/companion UI เท่านั้น MCP ไม่มี tool สำหรับ approve
7. **Content minimization** — audit บันทึก metadata ที่ redacted ไม่บันทึกเนื้อหาไฟล์ prompt/output screenshot/clipboard หรือ secret
8. **Bounded everything** — จำกัดขนาดไฟล์ output runtime จำนวน process concurrency และ TTL ของ pending action
9. **No generic deletion baseline** — file API ไม่มี delete primitive และ execution profile ต้องพิสูจน์ kernel-enforced no-delete/no-unapproved-truncate policy; local approval ไม่สามารถเปิด generic deletion ได้ ส่วน exact approved write/patch ใช้ได้เฉพาะ target ที่ผูก digest

## 3. Trust boundaries และ threat model

### 3.1 สิ่งที่ถือว่าไม่น่าเชื่อถือ

- prompt และ tool arguments จาก MCP client
- เนื้อหา repository, README, log, terminal output, web page, screenshot, OCR และ accessibility tree
- symlink, bind mount, Windows reparse point และ path ที่เปลี่ยนได้ระหว่างตรวจและเปิด
- executable/script ใน workspace
- process ID ที่อาจถูก reuse

### 3.2 ภัยคุกคามหลัก

| ภัยคุกคาม | การควบคุมหลัก |
|---|---|
| Path traversal / symlink escape | canonical allowlist, descriptor-based open เมื่อทำได้, no-follow policy, ตรวจซ้ำก่อน mutation |
| Prompt injection จากไฟล์/หน้าจอ | ถือ content เป็น data, ไม่เปลี่ยน policy/approval ตามข้อความที่อ่านพบ |
| Shell injection | argv array, `shell=False`, executable allowlist, environment allowlist |
| Secret exfiltration | protected paths, baseline protected filenames, output limits, redaction, network tools ปิดโดย default; exec output ยังถือว่า content-bearing |
| Delete/truncate/rename bypass | ไม่มี delete tool, exact operation schema, kernel-enforced execution policy, dedicated no-clobber move เท่านั้นหากเพิ่มในอนาคต |
| Approval replay | action digest, exact parameters, TTL, one-time use, local confirmation |
| PID reuse / process escape | process-group ownership, start-time identity, bounded children, cancellation verification |
| TOCTOU | canonicalize และตรวจที่จุดใช้งาน, atomic replace, reject path type changes |
| Windows boundary bypass | policy แยกจาก WSL, helper authentication, fixed helper path, deny UNC/reparse by default |
| GUI ทำรายการอ่อนไหว | protected-field refusal, app/window allowlist, stale-frame rejection, emergency stop |

`deny_prompt_patterns` หรือ command keyword blacklist ไม่ใช่ security boundary เพราะเปลี่ยนถ้อยคำเพื่อหลบได้ การบังคับใช้ต้องอยู่ที่ path, filename, executable, argv schema, OS primitive และ approval policy

## 4. Component model

เสนอให้แยกโมดูลโดยไม่บังคับว่าชื่อไฟล์จริงต้องตรงทุกตัว:

```text
bridge.py
├── Hermes adapter
├── CodexRunner
└── HandsRuntime
    ├── policy       canonical config and authorization
    ├── paths        containment and WSL/Windows translation
    ├── actions      pending action, digest, TTL, approval state
    ├── processes    spawn, poll, output paging, timeout, cancel
    ├── audit        shared redacted AuditLogger interface
    ├── wsl          file and fixed-argv execution adapter
    ├── windows      Windows helper adapter [v1.4.0]
    └── computer     capture/UI Automation adapter [v1.5.0]
```

Hands database ควรแยก table namespace หรือไฟล์ state จาก Hermes runs และ Codex jobs เพื่อให้ migration/cleanup ไม่กระทบกัน แต่ใช้ directory permission และ atomic migration discipline เดียวกัน

การสร้าง bridge ต้องไม่ fail เพียงเพราะ Hermes health check ไม่ผ่านหรือไม่พบ Codex binary Backend health ตรวจแบบ lazy และรายงานแยกกัน ข้อผิดพลาด config เชิงโครงสร้างยังคง fail closed; backend ที่ปิดอย่างถูกต้องต้องไม่ทำให้ backend อื่นหยุด

## 5. MCP tool contract ที่เสนอ

### 5.1 v1.2.0 read-only WSL2 core

| Tool | ลักษณะ | หน้าที่ |
|---|---|---|
| `hands_health` | read-only/local | รายงาน version, enabled state, adapter readiness และ policy summary ที่ไม่เผย path อ่อนไหว |
| `hands_list` | read-only | list directory แบบจำกัดจำนวน/ชนิดข้อมูลภายใน workspace |
| `hands_read` | read-only | อ่าน text ช่วงที่ระบุโดยมี byte/line limit; binary ปฏิเสธโดย default |
| `hands_write` | mutation, v1.3.0 | สร้างหรือแทนไฟล์แบบ atomic ภายใต้ write policy และ approval |
| `hands_patch` | mutation, v1.3.0 | apply exact patch พร้อม base digest เพื่อป้องกันเขียนทับไฟล์ที่เปลี่ยนแล้ว |
| `hands_exec` | execution, v1.3.0 | รัน executable ที่อนุญาตด้วย argv/cwd/env ที่ตรวจแล้ว |
| `hands_process` | process, v1.3.0 | `status`, `output`, `cancel`, `recent` เฉพาะ process ที่ Hands เป็นผู้สร้าง |

`v1.2.0` register เพียง `hands_health`, `hands_list`, `hands_read` เพื่อเก็บ feedback จาก read-only vertical slice ก่อนลงทุนกับ action store. ไม่สร้าง `hands_python` หรือ `hands_git`; เมื่อถึง v1.3.0 Python/Git ใช้ผ่าน `hands_exec` และ executable policy ได้

ข้อกำหนดสำคัญของ `hands_exec` ใน v1.3.0:

- request แยก `executable`, `args[]`, `workspace`, `cwd`, optional environment keys และ execution mode
- resolve executable เป็น path จริงและเทียบกับ allowlist; ห้ามอาศัย PATH ที่ควบคุมจาก workspace โดยไม่ตรวจ
- `shell=False`, ไม่มี `bash -c`, `sh -c`, `eval` หรือ PowerShell command string ใน baseline
- executable ที่ตีความ script/โค้ด เช่น Python, Node, Bash ต้องมี policy เฉพาะ ไม่ถือว่าปลอดภัยเพราะ binary อยู่ใน allowlist
- จำกัด runtime/output/concurrency และ process tree
- network-capable executable ปิดโดย default และแยก capability จาก local build/test
- executable profile ไม่ใช่ตรารับรองว่า safe: Git hooks/config, CMake build rules, test discovery, interpreter, response file และ config-file indirection อาจรันโค้ดหรืออ่าน secret ได้
- environment ของ Git profile ต้องเริ่มจาก minimal environment และปิด global/system config injection อย่างน้อยด้วย `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_SYSTEM=/dev/null`, ปิด hooks/pager/external diff ตาม action schema; executable อื่นต้องมี hardening เฉพาะตัว
- profile ที่ไม่ต้อง approval ต้องคืนเฉพาะ metadata และใช้ exact constrained argv; `git diff` เป็น content-bearing จึงไม่อยู่ในกลุ่มนี้
- stdout/stderr คือ trusted-workspace-content ที่จะไหลกลับเข้า ChatGPT และอาจมี secret การกรองตามชื่อไฟล์หรือ output redaction ไม่สามารถรับประกันการป้องกันได้

#### Kernel enforcement สำหรับ execution

`shell=False` ป้องกัน shell injection แต่ไม่ได้ป้องกัน binary, build rule, interpreter หรือ child process จากการเรียก `unlink`, `rename` หรือ `truncate` โดยตรง เพื่ออ้างว่า generic deletion และ unapproved truncation ถูกปิดจริง v1.3.0 ต้องมี kernel-enforced filesystem policy เช่น Landlock หรือกลไกเทียบเท่าที่ผ่าน acceptance ไม่ใช่ command deny-list Exact `hands_write`/`hands_patch` ที่ผ่าน digest-bound approval เป็น operation แยกและแตะได้เฉพาะ target ที่อนุมัติ

[Landlock](https://docs.kernel.org/userspace-api/landlock.html) เริ่มมีใน Linux 5.13 ไม่ใช่ 5.10 และยังขึ้นกับ kernel build/boot configuration และ ABI ที่รองรับ Runtime ต้อง probe syscall/ABI จริง ห้ามอนุมานจากเลข kernel หรือคำว่า WSL2 เพียงอย่างเดียว Profile ที่ต้อง enforce no-delete/no-truncate unavailable เมื่อกลไกไม่รองรับสิทธิ์ที่ต้องใช้; ห้าม downgrade เงียบไปเป็น keyword filter

ข้อกำหนดขั้นต่ำของ execution sandbox:

- allow เฉพาะ hierarchy ที่ profile ต้องอ่าน/เขียน และ deny ambient filesystem access ที่ไม่ประกาศ
- deny remove file/directory, rename/link escape และ truncate ตาม ABI ที่รองรับ
- restrictions สืบทอดไป child processes
- capability health รายงาน enforcement mechanism/ABI แบบไม่เผย path อ่อนไหว
- integration test ต้องพิสูจน์ direct syscall deletion, interpreter deletion, child-process deletion และ destination overwrite ล้มเหลว

### 5.2 v1.4.0 Windows host

เพิ่ม `hands_windows` เป็น tool เดียวที่ใช้ action schema เช่น `process_list`, `service_status`, `eventlog_query` และ action mutation ที่เปิดเป็นรายรายการ ไม่รับ PowerShell script อิสระเป็นค่าเริ่มต้น WSL policy ไม่ส่งต่อไป Windows โดยอัตโนมัติ

### 5.3 v1.5.0 computer use

เพิ่ม `hands_computer(action=...)` tool เดียว ภาพที่ observe ต้องมี `observation_id`, timestamp, window identity, dimensions และ TTL ทุก click/type ต้องอ้าง observation ล่าสุดและยืนยัน foreground window ก่อนลงมือ

## 6. Policy model

ตัวอย่างนี้เป็น draft contract สำหรับ implementation review ไม่ใช่ config ที่ v1.0.1 รองรับ:

```json
{
  "schema_version": 1,
  "hands": {
    "enabled": false,
    "approval_ttl_seconds": 300,
    "max_read_bytes": 1048576,
    "max_output_bytes": 1048576,
    "max_runtime_seconds": 900,
    "max_concurrency": 2,
    "protected_paths": [
      "~/.ssh",
      "~/.gnupg",
      "~/.aws",
      "~/.config/openai",
      "/mnt/c/Users/*/.ssh"
    ],
    "additional_protected_filename_patterns": [],
    "workspaces": [
      {
        "name": "openhdk",
        "path": "/mnt/e/Projects/OpenHDK",
        "capabilities": ["list", "read"]
      }
    ]
  }
}
```

[ADR-0001](adr/0001-local-hands-foundation.md) ตัดสินใจใช้ additive `hands` block ใน schema version 1 เพื่อให้ config เดิมยังใช้ได้และ Hands disabled เมื่อไม่มี block การเพิ่มนี้ยังต้องมี unknown-key warning, invalid-known-key failure, deterministic upgrade/rollback และห้าม installer เขียน workspace/executable จากการเดา

### 6.1 Protected filenames ภายใน workspace

Protected path อย่างเดียวไม่พอ เพราะ secret มักอยู่ภายใน repository เอง Baseline ต้องมี filename patterns ที่ผู้ใช้เพิ่มได้แต่ลดหรือ override ไม่ได้ และเทียบทุก path component/ชื่อไฟล์แบบ case-insensitive บน DrvFS อย่างน้อย:

```text
.env
.env.*
*.pem
*.key
*.p12
*.pfx
id_rsa*
id_ed25519*
credentials*.json
secrets*.json
.netrc
.npmrc
.pypirc
```

`hands_read`, `hands_write` และ `hands_patch` ต้อง deny ก่อนเปิดไฟล์เมื่อ match baseline หรือ additional patterns ส่วน `hands_list` คืน metadata ตาม policy แต่ไม่อ่าน content Pattern protection ลดความเสี่ยงกรณีทั่วไปเท่านั้น ไม่ตรวจเนื้อหาและไม่สามารถป้องกัน command ที่อ่าน secret แล้วพิมพ์ทาง stdout/stderr จึงต้องสื่อสาร execution risk และใช้ approval/executable profile แยกต่างหาก

### 6.2 Risk/approval matrix

| Operation | ค่าเริ่มต้น | Approval |
|---|---|---|
| health/list/read ภายใน read root | อนุญาตเมื่อเปิด workspace | ไม่ต้องอนุมัติรายครั้ง |
| metadata-only exact profile เช่น constrained `git status`, metadata-only log, `ctest -N` | ตาม policy ใน v1.3.0 | policy กำหนดได้ |
| `git diff`, build/test, interpreter หรือ workspace code | ปิดจนมี v1.3.0 policy | ต้องอนุมัติ local |
| create/replace/patch file | ปิดจนเปิด write capability | ต้องอนุมัติ local |
| process cancel ที่ Hands เป็นเจ้าของ | อนุญาตตาม policy | แสดงผลกระทบ; mutation policy กำหนด |
| interpreter/script execution | ปิด | ต้อง policy เฉพาะและ approval |
| generic delete/unlink/rmdir/destructive rename/unapproved truncate | baseline deny | approval ไม่สามารถเปิด generic delete; exact write/patch target ใช้ flow แยก |
| chmod/chown, package install, service mutation | ปิด | explicit high-risk policy + local approval ใน milestone ที่รองรับ |
| credential path, secure desktop, payment | ปฏิเสธ | approval ไม่สามารถ override baseline deny |

Approval record ต้องผูก canonical digest ตาม [ADR-0001](adr/0001-local-hands-foundation.md) หากค่าใดเปลี่ยนต้องขอ approval ใหม่ Runtime execute persisted immutable payload ที่ถูก digest เท่านั้น ไม่รับ payload รอบสองจาก MCP client

### 6.3 Canonical action digest

[ADR-0001](adr/0001-local-hands-foundation.md) กำหนด digest เป็น SHA-256 ของ ASCII `hermes-local-hands-action-v1`, ตามด้วย NUL byte `0x00`, แล้วต่อด้วย UTF-8 JSON ที่สร้างด้วย `ensure_ascii=false`, `sort_keys=true`, separators `(',', ':')`, `allow_nan=false` Payload ต้องมี `schema`, action type, canonical workspace/path, executable+argv/environment profile, content/base digest, risk class และ expiry เป็น integer Unix seconds; ห้ามมี float, secret หรือ raw content Content-bearing action อ้าง sealed immutable blob ด้วย SHA-256 และตรวจ digest ซ้ำก่อน execute

## 7. Filesystem semantics

- ใช้ workspace ID ใน public contract แทนเปิดเผย/ยอมรับ arbitrary absolute path เมื่อทำได้
- เปิด workspace root เป็น trusted directory fd ตอนโหลดหรือ refresh policy และ resolve target แบบ relative ต่อ fd
- Linux file tools ต้องใช้ `openat2` กับ `RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS | RESOLVE_NO_MAGICLINKS` เมื่อ syscall/filesystem รองรับ หาก strict self-test ของ workspace ล้มเหลวให้ workspace นั้น unavailable และห้าม fallback ไป `realpath()+open`
- path ต้องอยู่ใต้ root ด้วย descriptor/path-component policy ไม่ใช้ string prefix
- protected-path deny มีลำดับสูงกว่า workspace allow
- write ใช้ temporary file ใน directory เดียวกัน, fsync ตาม policy, แล้ว atomic replace
- patch ต้องระบุ hash ของ base file; mismatch แล้วหยุด ไม่ merge เดาเอง
- จำกัด regular files เป็น baseline; device, socket, FIFO และ proc/sysfs ปฏิเสธ
- protected filename baseline ตรวจทุก file operation ก่อนเปิดและผู้ใช้ลดไม่ได้
- DrvFS `/mnt/<drive>` ใช้ descriptor containment เหมือนกัน แต่ protected names/path comparisons ใช้ conservative case-folding, ตรวจ mount type/options และ reject case-fold collision ที่กำกวม ห้ามสมมติว่า semantics เหมือน ext4
- Windows path translation เป็น convenience เท่านั้น หลังแปลงต้องผ่าน canonical policy เหมือน path ปกติ

### 7.1 Move และ working-copy redirect

Baseline ไม่มี generic move/delete หากอนาคตต้องย้ายไฟล์ ให้สร้าง dedicated operation ที่รับ source/destination แบบ canonical, จำกัดใน workspace, ใช้ no-clobber primitive เช่น `renameat2(..., RENAME_NOREPLACE)`, ปฏิเสธ destination ที่มีอยู่ และไม่เปิดผ่าน arbitrary executable argv

สำหรับไฟล์นอก writable workspace อาจเพิ่ม read-adjacent workflow ในอนาคตที่สร้าง working copy ชื่อ `name.edited.ext` ใน workspace ที่อนุญาต โดยไม่แก้ต้นฉบับ การสร้างสำเนาต้องมี provenance metadata, collision-safe naming และต้องไม่ตีความว่าเป็นสิทธิ์เขียนนอก workspace

## 8. Process lifecycle

Process ทุกตัวต้องมี ID ของ Hands ไม่คืน raw PID เป็น authority หลัก State ขั้นต่ำคือ `pending_approval`, `queued`, `running`, `completed`, `failed`, `cancelled`, `timed_out`, `expired`, `unknown_exit` Pending actions ต้องมี cap ต่อ workspace และ global; เมื่อเต็มให้ reject ก่อน persist พร้อม redacted audit

ใช้ process group ใหม่, fixed cwd, minimal environment, bounded output file และ watchdog ใน persistent bridge process แนวทาง cancel ใช้ graceful termination, bounded wait, forced termination และยืนยันการตายก่อนบันทึก terminal state เช่นเดียวกับบทเรียนจาก Codex runner

Output เก็บเป็น bounded JSONL ต่อ process ตาม [ADR-0001](adr/0001-local-hands-foundation.md) พร้อม truncation/rotation หลัง restart ห้ามสรุป process ที่ไม่เห็น exit code ว่า completed หากพิสูจน์ไม่ได้ให้ `unknown_exit` และไม่ attach ไปยัง PID ที่อาจถูก reuse

## 9. Audit and privacy

ตัวอย่าง field ที่บันทึกได้:

```json
{
  "component": "hands",
  "action": "exec",
  "action_id": "hands_...",
  "status": "completed",
  "workspace_id": "openhdk",
  "executable_id": "cmake",
  "risk": "execute",
  "duration_ms": 2814,
  "exit_code": 0
}
```

ห้ามบันทึก argv ที่อาจมี secret แบบดิบ เนื้อหาไฟล์ patch/script stdout/stderr screenshot/OCR clipboard prompt หรือ environment value หากจำเป็นต่อ forensic ให้เก็บเฉพาะ allowlisted metadata/digest และอธิบาย retention ชัดเจน

## 10. Windows helper boundary

Windows helper ควรเป็น process แยกที่มี protocol version, nonce/request ID, message size limit และ local authentication key ที่สร้าง/เก็บด้วย permission เหมาะสม ไม่ listen บน public interface ไม่รับ arbitrary executable path และตรวจ policy ซ้ำฝั่ง Windows สำหรับ action ที่มีผลต่อ Windows

ห้ามถือว่า `powershell.exe -Command` ปลอดภัยเพียงเพราะเริ่มจาก WSL2 สำหรับ baseline ให้ใช้ action RPC ที่มี schema หากอนาคตเปิด script execution ต้องเป็น capability แยก ใช้ signed/hashed script หรือ exact content approval และมี output/runtime limit

## 11. Computer-use safety และ hard gate

ห้ามเริ่ม implementation จนกว่า v1.4.0 Windows Host จะผ่าน live acceptance และมี security review ที่บันทึกผลแล้ว รุ่นแรกของ computer use เป็น observe-only จากนั้นจึงเปิด click เฉพาะ disposable test application ส่วน typing ต้องผ่าน review/acceptance แยกอีกครั้ง

- observe ก่อน action และ action อ้าง `observation_id` พร้อม action/observation budget
- ตรวจ window/process identity และ geometry ใหม่ก่อน click/type
- หลัง action ต้องเก็บ post-action observation แบบ bounded แล้วตรวจ app/window identity, screen-change signal และ expected-state predicate; หากยืนยันไม่ได้ให้คืน `verification_inconclusive` ไม่เดาว่าสำเร็จ
- ไม่อ่านหรือกรอก protected field โดยใช้ accessibility secure-field flag เป็นหลักและใช้ normalized/case-folded marker เป็น defense-in-depth ได้แก่ `password`, `passcode`, `pin`, `otp`, `mfa`, `2fa`, `verification code`, `security code`, `รหัสผ่าน`, `รหัส`, `พิน`, `โอทีพี`
- ไม่ควบคุม UAC/secure desktop
- ไม่ทำ payment, signing, credential export หรือ security-setting changes
- ข้อความบนหน้าจอไม่มีสิทธิเปลี่ยน policy หรืออนุมัติ action
- มี local emergency stop ที่ตัด queue และ block action ใหม่จนผู้ใช้ reset
- เก็บ screenshot ชั่วคราวเท่าที่จำเป็นและไม่ลง audit

## 12. Capability and health contract

`bridge_status` ควรคืนสถานะแยก backend โดยไม่ทำให้ backend หนึ่งล้มแล้วทั้ง call ล้ม ตัวอย่างเชิงแนวคิด:

```json
{
  "hermes": {"available": false, "reason": "quota_exhausted"},
  "codex": {"available": false, "reason": "usage_limit"},
  "local_hands": {"available": true, "reason": "available", "adapter": "wsl2"}
}
```

เหตุผล `quota_exhausted`/`usage_limit` ต้องมาจากผลที่ backend รายงานได้อย่างเชื่อถือ ห้ามเดาจากข้อความทั่วไป หากจำแนกไม่ได้ใช้ `unreachable` หรือ `error` พร้อมรายละเอียดที่ redacted

Diagnostics ต้องมี classifier แยกจาก adapter ที่ map exception/exit/signal/stderr pattern เป็น structured `{error_code, layer, retryable, safe_hint}` โดยไม่ dump raw stderr อัตโนมัติ Raw output อ่านได้เฉพาะผ่าน bounded result paging ตาม policy และไม่เข้า audit log

## 13. รูปแบบจาก Endeavor Hands ที่จงใจไม่รับมา

- ไม่ใช้ sandbox แบบ `(allow default)` แล้วไล่ deny path เพราะ path ที่ตกหล่นยังเข้าถึงได้ Local Hands คง workspace/capability allowlist และอาจเสริมด้วย Landlock ที่ probe ได้จริง
- ไม่ใช้ nonce ที่โมเดล relay เป็น approval boundary; หากมี friction token ในอนาคตต้องประกาศว่า non-security และห้ามแทน local TTY/companion approval ที่ผูก digest
- ไม่เปิดอ่านทั่วเครื่องแล้วพึ่ง protected-path deny-list
- ไม่เพิ่ม PDF/OCR/media/parser เข้า `hands_read` โดยปริยาย ทุก capability ต้องมี policy, dependency, limits, threat model และ acceptance ของตัวเอง
- ไม่ทำ dynamic MCP-to-MCP bridge หรือ trusted delegation bypass ในรุ่นแรก และไม่ให้ exact path/cwd matching เพียงอย่างเดียวสร้าง trust root
- ไม่ยอมรับช่องทางที่ shell/interpreter เขียนข้าม edit gate เป็น accepted gap; execution ต้องใช้ operation profile, approval และ kernel enforcement ตาม capability

## 14. ข้อจำกัดที่ต้องสื่อสารกับผู้ใช้

Local Hands เป็น fallback เมื่อ Hermes/Codex ใช้ไม่ได้ แต่ ChatGPT ยังคงเป็น brain ดังนั้นยังขึ้นกับ quota/session ของ ChatGPT และความพร้อมของ tunnel/bridge มันไม่ใช่ offline agent, unrestricted shell หรือ remote desktop และไม่รับประกันว่า task ที่ต้อง reasoning ระยะยาวจะสำเร็จเท่า Codex/Hermes ผู้ใช้ควรแบ่งงานเป็นขั้นสั้น ตรวจผล และอนุมัติเฉพาะ action ที่เข้าใจผลกระทบ
