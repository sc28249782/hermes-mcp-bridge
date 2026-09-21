# Hermes Local Hands — สถาปัตยกรรมและขอบเขตความปลอดภัย

สถานะ: เอกสารออกแบบสำหรับ roadmap หลัง `v1.0.1`  
เป้าหมายรุ่นแรก: `v1.2.0`  
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
            ├── Windows adapter      [v1.3.0]
            └── Computer-use helper  [v1.4.0]
```

คำว่า “อิสระ” หมายถึงเส้นทาง `hands_*` ไม่เรียก Hermes Runs API, model provider หรือ Codex CLI ไม่ได้หมายความว่าจะใช้งานได้เมื่อ ChatGPT, Secure MCP Tunnel, bridge process หรือ WSL2 หยุดทำงาน

## 2. หลักการออกแบบ

1. **Sibling backends** — Hermes, Codex และ Hands มี lifecycle/health แยกกัน ไม่มี backend ใดเป็นทางผ่านบังคับของอีก backend
2. **Deterministic executor** — Hands รับคำสั่งที่มีโครงสร้าง ตรวจ policy แล้วลงมือ ไม่วางแผน ไม่ตัดสินใจแทน agent และไม่ delegate กลับไปหา agent
3. **Fail closed** — config ผิด, path กำกวม, approval หมดอายุ, helper version ไม่ตรง หรือไม่สามารถพิสูจน์ containment ได้ ต้องปฏิเสธ
4. **Least privilege** — upgrade แล้ว Hands ปิดเป็นค่าเริ่มต้น ไม่มี workspace เขียนได้ ไม่มี executable หรือ Windows action ที่อนุญาตโดยอัตโนมัติ
5. **Structured operations** — รับ executable และ argv แยกช่อง ใช้ `shell=False`; ไม่รับ shell command string แบบ unrestricted
6. **Local human approval** — การอนุมัติทำใน local TTY/companion UI เท่านั้น MCP ไม่มี tool สำหรับ approve
7. **Content minimization** — audit บันทึก metadata ที่ redacted ไม่บันทึกเนื้อหาไฟล์ prompt/output screenshot/clipboard หรือ secret
8. **Bounded everything** — จำกัดขนาดไฟล์ output runtime จำนวน process concurrency และ TTL ของ pending action

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
| Secret exfiltration | protected paths, output limits, redaction, network tools ปิดโดย default |
| Approval replay | action digest, exact parameters, TTL, one-time use, local confirmation |
| PID reuse / process escape | process-group ownership, start-time identity, bounded children, cancellation verification |
| TOCTOU | canonicalize และตรวจที่จุดใช้งาน, atomic replace, reject path type changes |
| Windows boundary bypass | policy แยกจาก WSL, helper authentication, fixed helper path, deny UNC/reparse by default |
| GUI ทำรายการอ่อนไหว | protected-field refusal, app/window allowlist, stale-frame rejection, emergency stop |

`deny_prompt_patterns` หรือ command keyword blacklist ไม่ใช่ security boundary เพราะเปลี่ยนถ้อยคำเพื่อหลบได้ การบังคับใช้ต้องอยู่ที่ path, executable, argv schema, OS primitive และ approval policy

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
    ├── windows      Windows helper adapter [v1.3.0]
    └── computer     capture/UI Automation adapter [v1.4.0]
```

Hands database ควรแยก table namespace หรือไฟล์ state จาก Hermes runs และ Codex jobs เพื่อให้ migration/cleanup ไม่กระทบกัน แต่ใช้ directory permission และ atomic migration discipline เดียวกัน

การสร้าง bridge ต้องไม่ fail เพียงเพราะ Hermes health check ไม่ผ่านหรือไม่พบ Codex binary Backend health ตรวจแบบ lazy และรายงานแยกกัน ข้อผิดพลาด config เชิงโครงสร้างยังคง fail closed; backend ที่ปิดอย่างถูกต้องต้องไม่ทำให้ backend อื่นหยุด

## 5. MCP tool contract ที่เสนอ

### 5.1 v1.2.0 WSL2 core

| Tool | ลักษณะ | หน้าที่ |
|---|---|---|
| `hands_health` | read-only/local | รายงาน version, enabled state, adapter readiness และ policy summary ที่ไม่เผย path อ่อนไหว |
| `hands_list` | read-only | list directory แบบจำกัดจำนวน/ชนิดข้อมูลภายใน workspace |
| `hands_read` | read-only | อ่าน text ช่วงที่ระบุโดยมี byte/line limit; binary ปฏิเสธโดย default |
| `hands_write` | mutation | สร้างหรือแทนไฟล์แบบ atomic ภายใต้ write policy และ approval |
| `hands_patch` | mutation | apply exact patch พร้อม base digest เพื่อป้องกันเขียนทับไฟล์ที่เปลี่ยนแล้ว |
| `hands_exec` | policy-dependent | รัน executable ที่อนุญาตด้วย argv/cwd/env ที่ตรวจแล้ว |
| `hands_process` | policy-dependent | `status`, `output`, `cancel`, `recent` เฉพาะ process ที่ Hands เป็นผู้สร้าง |

ไม่สร้าง `hands_python` หรือ `hands_git` ในรุ่นแรก เพราะ Python/Git ใช้ผ่าน `hands_exec` และ executable policy ได้ การลดจำนวน tool ช่วยลด ambiguity แต่ยังคง authorization ที่ executable/argv schema

ข้อกำหนดสำคัญของ `hands_exec`:

- request แยก `executable`, `args[]`, `workspace`, `cwd`, optional environment keys และ execution mode
- resolve executable เป็น path จริงและเทียบกับ allowlist; ห้ามอาศัย PATH ที่ควบคุมจาก workspaceโดยไม่ตรวจ
- `shell=False`, ไม่มี `bash -c`, `sh -c`, `eval` หรือ PowerShell command string ใน baseline
- executable ที่ตีความ script/โค้ด เช่น Python, Node, Bash ต้องมี policy เฉพาะ ไม่ถือว่าปลอดภัยเพราะ binary อยู่ใน allowlist
- จำกัด runtime/output/concurrency และ process tree
- network-capable executable ปิดโดย default และแยก capability จาก local build/test

### 5.2 v1.3.0 Windows host

เพิ่ม `hands_windows` เป็น tool เดียวที่ใช้ action schema เช่น `process_list`, `service_status`, `eventlog_query` และ action mutation ที่เปิดเป็นรายรายการ ไม่รับ PowerShell script อิสระเป็นค่าเริ่มต้น WSL policy ไม่ส่งต่อไป Windows โดยอัตโนมัติ

### 5.3 v1.4.0 computer use

เพิ่ม `hands_computer(action=...)` tool เดียว ภาพที่ observe ต้องมี `observation_id`, timestamp, window identity, dimensions และ TTL ทุก click/type ต้องอ้าง observation ล่าสุดและยืนยัน foreground window ก่อนลงมือ

## 6. Policy model

ตัวอย่างนี้เป็น draft contract สำหรับ implementation review ไม่ใช่ config ที่ v1.0.1 รองรับ:

```json
{
  "schema_version": 2,
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
    "workspaces": [
      {
        "name": "openhdk",
        "path": "/mnt/e/Projects/OpenHDK",
        "capabilities": ["list", "read", "write", "patch", "exec"],
        "executables": [
          {"path": "/usr/bin/git", "profiles": ["status", "diff"]},
          {"path": "/usr/bin/cmake", "profiles": ["build"]},
          {"path": "/usr/bin/ctest", "profiles": ["test"]}
        ]
      }
    ]
  }
}
```

ก่อน implement ต้องตัดสินใจว่า schema จะ bump เป็น version 2 หรือรองรับ additive `hands` block ใน version 1 การเปลี่ยนนี้ต้องมี deterministic migration, unknown-key warning และ rollback path ห้าม installer เขียน workspace/executable จากการเดา

### 6.1 Risk/approval matrix

| Operation | ค่าเริ่มต้น | Approval |
|---|---|---|
| health/list/read ภายใน read root | อนุญาตเมื่อเปิด workspace | ไม่ต้องอนุมัติรายครั้ง |
| git status/diff หรือ build/test profile ที่ประกาศ read-safe | ตาม policy | policy กำหนดได้ |
| create/replace/patch file | ปิดจนเปิด write capability | ต้องอนุมัติ local |
| process cancel ที่ Hands เป็นเจ้าของ | อนุญาตตาม policy | แสดงผลกระทบ; mutation policy กำหนด |
| interpreter/script execution | ปิด | ต้อง policy เฉพาะและ approval |
| delete, chmod/chown, package install, service mutation | ปิด | explicit high-risk policy + local approval |
| credential path, secure desktop, payment | ปฏิเสธ | approval ไม่สามารถ override baseline deny |

Approval record ต้องผูกกับ digest ของ tool, canonical workspace/path, executable+argv, content/base digest, risk class และ expiry หากค่าใดเปลี่ยนต้องขอ approval ใหม่

## 7. Filesystem semantics

- ใช้ workspace ID ใน public contract แทนเปิดเผย/ยอมรับ arbitrary absolute path เมื่อทำได้
- canonicalize root ตอนโหลด config และ canonicalize target ที่จุดใช้งาน
- path ต้องอยู่ใต้ root ด้วย path-component comparison ไม่ใช้ string prefix
- protected-path deny มีลำดับสูงกว่า workspace allow
- write ใช้ temporary file ใน directory เดียวกัน, fsync ตาม policy, แล้ว atomic replace
- patch ต้องระบุ hash ของ base file; mismatch แล้วหยุด ไม่ merge เดาเอง
- จำกัด regular files เป็น baseline; device, socket, FIFO และ proc/sysfs ปฏิเสธ
- Windows path translation เป็น convenience เท่านั้น หลังแปลงต้องผ่าน canonical policy เหมือน path ปกติ

## 8. Process lifecycle

Process ทุกตัวต้องมี ID ของ Hands ไม่คืน raw PID เป็น authority หลัก State ขั้นต่ำคือ `pending_approval`, `queued`, `running`, `completed`, `failed`, `cancelled`, `timed_out`, `expired`, `unknown_exit`

ใช้ process group ใหม่, fixed cwd, minimal environment, bounded output file และ watchdog ใน persistent bridge process แนวทาง cancel ใช้ graceful termination, bounded wait, forced termination และยืนยันการตายก่อนบันทึก terminal state เช่นเดียวกับบทเรียนจาก Codex runner

หลัง restart ห้ามสรุป process ที่ไม่เห็น exit code ว่า completed หากพิสูจน์ไม่ได้ให้ `unknown_exit` และไม่ attach ไปยัง PID ที่อาจถูก reuse

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

## 11. Computer-use safety

- observe ก่อน action และ action อ้าง `observation_id`
- ตรวจ window/process identity และ geometry ใหม่ก่อน click/type
- ไม่อ่านหรือกรอก password/PIN/MFA/token/recovery code
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

## 13. ข้อจำกัดที่ต้องสื่อสารกับผู้ใช้

Local Hands เป็น fallback เมื่อ Hermes/Codex ใช้ไม่ได้ แต่ ChatGPT ยังคงเป็น brain ดังนั้นยังขึ้นกับ quota/session ของ ChatGPT และความพร้อมของ tunnel/bridge มันไม่ใช่ offline agent, unrestricted shell หรือ remote desktop และไม่รับประกันว่า task ที่ต้อง reasoning ระยะยาวจะสำเร็จเท่า Codex/Hermes ผู้ใช้ควรแบ่งงานเป็นขั้นสั้น ตรวจผล และอนุมัติเฉพาะ action ที่เข้าใจผลกระทบ
