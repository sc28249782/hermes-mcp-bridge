# Hermes Local Hands — แผนพัฒนาและเกณฑ์ยอมรับ

สถานะ: implementation handoff สำหรับ roadmap `v1.2.0`–`v1.5.0`  
เอกสารออกแบบหลัก: `LOCAL-HANDS-ARCHITECTURE-TH.md`

## 1. ลำดับการพัฒนา

### Stage 0 — Contract และ test harness

1. บันทึก ADR ว่า Hands เป็น sibling backend และห้ามเรียก Hermes/Codex
2. กำหนด schema migration, workspace ID, action ID, process state และ normalized error codes
3. สร้าง fake filesystem/process/Windows adapters เพื่อทดสอบ policy โดยไม่แตะเครื่องจริง
4. เพิ่ม dependency-direction test หรือ static assertion เพื่อป้องกัน Hands import/call Hermes client และ Codex runner
5. กำหนด golden redaction tests ก่อนสร้าง mutation tools

Exit criteria:

- config เก่าที่ยังไม่มี `hands` โหลดได้เหมือนเดิมและ Hands เป็น disabled
- invalid Hands config fail closed พร้อมข้อความที่ไม่เผย secret
- test พิสูจน์ว่า Hands core ไม่มี dependency ต่อ Hermes/Codex execution objects

### Stage 1 — Read-only WSL2 vertical slice

Implement `hands_health`, `hands_list`, `hands_read`, canonical workspace resolution, protected paths, byte limits และ audit metadata

Exit criteria:

- อ่านได้เฉพาะ regular text file ใน read-enabled workspace
- traversal, symlink escape, protected path, binary/oversize และ special file ถูกปฏิเสธ
- Hermes ปิด + Codex binary ไม่มี: health/list/read ยังผ่าน
- audit ไม่มี content/path secret และไฟล์ permission/rotation ถูกต้อง

### Stage 2 — Approval-bound mutations

Implement pending action store, local CLI preview/approve/deny, TTL, one-time digest, `hands_write` และ `hands_patch`

Exit criteria:

- MCP สร้าง pending action ได้แต่ approve ไม่ได้
- local preview แสดง canonical target, risk, size/digest และผลกระทบโดยไม่พิมพ์ secret/content เกินจำเป็น
- เปลี่ยน target/content/base digest หลัง approval ไม่ได้
- expired/denied/replayed approval ไม่เขียนไฟล์
- atomic write/patch ไม่ทิ้ง partial target เมื่อเกิด failure

### Stage 3 — Bounded execution/process control

Implement executable profiles, fixed argv, minimal environment, process state, paginated output, watchdog และ cancellation

Exit criteria:

- `shell=False` ถูกยืนยันด้วย unit test และ code review
- executable/path/argv/cwd/env นอก policy ถูกปฏิเสธก่อน spawn
- runtime/output/concurrency limit บังคับใช้แม้ client ไม่ poll
- cancel race, timeout, bridge restart และ PID reuse ไม่รายงาน completed ผิด
- network-capable/interpreter execution ปิดเมื่อไม่มี explicit policy

### Stage 4 — Windows host adapter

1. นิยาม versioned action protocol และ authentication
2. เริ่ม read-only process/service/event-log actions
3. เพิ่ม Windows canonical path/reparse-point tests
4. เพิ่ม mutation ทีละ action พร้อม local approval
5. ทดสอบ helper install/upgrade/rollback/signature/version mismatch

### Stage 5 — Computer use

1. observe-only capture/accessibility tree
2. observation identity/TTL/foreground verification
3. allowlisted click/key/scroll ใน disposable app
4. typing พร้อม protected-field refusal
5. emergency stop, visible indicator, queue cancellation และ prompt-injection tests

### Stage 6 — Routing and release hardening

เพิ่ม independent backend status, fallback documentation, operations/runbook, compatibility matrix, upgrade/rollback, signed release checklist และ live acceptance record

## 2. Proposed code changes for v1.2.0

ชื่อไฟล์ต่อไปนี้เป็นข้อเสนอและปรับได้ระหว่าง implementation แต่ separation ต้องคงอยู่:

| Area | Proposed responsibility |
|---|---|
| `hands_core.py` | HandsRuntime, domain errors, tool-facing operations |
| `hands_policy.py` | schema-derived immutable policy, canonical authorization |
| `hands_paths.py` | containment, protected paths, translation helpers |
| `hands_actions.py` | pending action, digest, approval TTL, one-time transition |
| `hands_process.py` | spawn/watchdog/status/output/cancel/recovery |
| `config_schema.py` | additive or migrated `hands` validation |
| `bridge.py` | MCP tools and local operator CLI only; no policy logic |
| `audit.py` | shared logger interface and Hands-safe metadata validation |
| `tests/test_hands_*.py` | focused policy/path/action/process tests |
| `tests/test_mcp.py` | discovery, annotations, result/error contract, fallback acceptance |

อย่าคัดลอก CodexRunner แล้วเปลี่ยนชื่อทั้งก้อน ควร reuse เฉพาะ primitive ที่มี contract เหมือนกันจริง เช่น audit writer หรือ atomic state helper และแยก approval/action state เพราะ Hands มี file mutation กับ executable profiles ที่ Codex ไม่มี

## 3. Configuration work

Checklist:

- [ ] ตัดสินใจ schema v2 หรือ additive v1 และบันทึก ADR
- [ ] unknown keys เป็น warnings; invalid known keys เป็น errors
- [ ] `hands.enabled` default `false`
- [ ] canonical workspace name/path ไม่ซ้ำ
- [ ] capability enum ไม่มีค่าที่ runtime ไม่บังคับใช้
- [ ] protected paths มี baseline deny ที่ผู้ใช้ลดไม่ได้สำหรับ credential classes สำคัญ
- [ ] limits มี min/max ที่สอดคล้อง runtime
- [ ] executable ใช้ absolute canonical path และ profile schema
- [ ] config/doctor output ไม่เผย protected path pattern หรือ secret โดยไม่จำเป็น
- [ ] installer upgrade ไม่ทับ config เดิมและไม่สร้างสิทธิ write/exec
- [ ] rollback ไป v1.0.1 อธิบายผลของ schema/state ใหม่ชัดเจน

## 4. MCP contract checklist

ทุก tool ต้องมี:

- input validation แบบ strict; reject unknown fields ถ้า framework รองรับ
- bounded strings/lists/response size
- tool annotation ที่ตรงกับผลกระทบ แต่ไม่ถือ annotation เป็น authorization
- normalized error code เช่น `disabled`, `policy_denied`, `approval_required`, `expired`, `conflict`, `not_found`, `limit_exceeded`, `unavailable`
- opaque ID ที่ validate รูปแบบและผูก ownership กับ bridge instance/state
- ไม่มี raw exception, environment, local secret หรือ unrestricted absolute path ใน error

Mutation flow:

```text
MCP request
  → validate + canonicalize + authorize
  → create immutable pending action + digest + expiry
  → return approval_required/action_id/summary
  → user previews in local terminal
  → local exact confirmation
  → re-resolve + compare digest + execute once
  → terminal state + redacted audit
```

## 5. Automated test matrix

### 5.1 Independence and fallback

| Hermes | Codex | Hands | Expected |
|---|---|---|---|
| ON | ON | ON | ทั้งสาม backend รายงาน/ทำงานแยกกัน |
| OFF | ON | ON | Hands ผ่าน; Hermes failure ไม่กระทบ |
| ON | OFF | ON | Hands ผ่าน; Codex failure ไม่กระทบ |
| OFF | OFF | ON | `hands_health/list/read/allowed exec` ผ่าน — critical gate |
| ON | ON | OFF | v1.0.1 behavior เดิม; Hands tools ตอบ disabled ตาม contract |

ต้องทดสอบทั้ง disabled โดย config, binary หาย, connection refused, timeout และ backend-specific quota/usage-limit response ที่ mock ตาม contract จริง

### 5.2 Path and file tests

- `..`, absolute path, mixed separators, Unicode normalization และ prefix collision
- symlink ใน root ชี้ออกนอก root; symlink swap ระหว่าง check/use
- hard link policy, bind mount/documented limitation, special files, `/proc`, `/sys`, device/FIFO/socket
- protected path ที่อยู่ใต้ workspace โดยบังเอิญต้องยังถูก deny
- file โตเกิน limit, binary/NUL, invalid encoding, short read, concurrent replacement
- patch base digest mismatch, duplicate patch, atomic replace failure, disk full
- Windows drive-letter case, reserved names, ADS, UNC, reparse/junction และ `/mnt/<drive>` translation ใน v1.3.0

### 5.3 Execution/process tests

- executable symlink/path substitution และ PATH poisoning
- argv metacharactersไม่กลายเป็น shell syntax
- interpreter profile bypass, response file (`@file`) และ config-file indirection ตาม executable
- cwd escape, environment injection, inherited proxy/credential variables
- output flood, long line, invalid UTF-8, timeout, concurrency exhaustion
- child/grandchild process, SIGTERM ignored, SIGKILL fallback, cancel/exit race
- bridge restart ก่อน/หลัง spawn, orphan, stale PID/PID reuse, unknown exit

Executable แต่ละตัวต้องมี adversarial tests ตาม semantics ของมัน ไม่ควรอนุญาต generic executable เพียงเพราะ fixed argv ป้องกัน shell injection เพราะ executable เองอาจมี flag สำหรับรันคำสั่งหรือโหลด config/script

### 5.4 Approval tests

- no TTY, wrong confirmation, expiry, deny, double approve, replay after restart
- digest mismatch จาก path/content/argv/policy change
- action ownership mismatch และ malformed ID
- MCP ไม่มี approval tool และไม่สามารถเปลี่ยน pending action
- audit บันทึก approve/deny/expire โดยไม่บันทึก content

### 5.5 Windows/GUI tests

- helper authentication/version mismatch/replay/message oversize
- helper path replacement/signature mismatch และ public bind refusal
- window เปลี่ยนก่อน click, geometry/DPI เปลี่ยน, stale screenshot, foreground mismatch
- password/MFA/UAC/payment fields ถูกปฏิเสธ
- prompt injection บนหน้าจอไม่เปลี่ยน policy
- emergency stop ระหว่าง queue และหลัง helper reconnect

## 6. Live acceptance gates

### v1.2.0 WSL2

ใช้ dedicated disposable workspace และ fixture เท่านั้น:

1. อัปเกรดจาก signed `v1.0.1`; ยืนยัน 19 tools เดิมไม่ regression ก่อนเปิด Hands
2. เปิด Hands read-only; discovery และ health ต้องตรง documented tool count
3. list/read fixture, ทดสอบ traversal/symlink/protected denial
4. สร้าง write/patch pending action, approve/deny/expire ผ่าน local TTY
5. รัน executable profile ที่ไม่มี network, poll output, timeout และ cancel
6. หยุด Hermes API และทำให้ Codex unavailable แล้วทำข้อ 2–5 ซ้ำในส่วนที่ policy อนุญาต
7. restart bridge ระหว่าง pending/running state และยืนยัน recovery semantics
8. ตรวจ audit/config/state permissions และค้นหา secret/content leakage

### v1.3.0 Windows

ใช้ Windows 11 + WSL2 และ disposable fixture/service/application:

1. helper install, authenticate, version check, stop/restart/upgrade/rollback
2. read-only process/service/event-log actions
3. path/reparse/UNC denial tests
4. approved mutation ที่ย้อนกลับได้หนึ่งรายการ
5. Hermes/Codex unavailable ขณะเรียก Windows Hands
6. ทดสอบกับ `virtioproxy`; networking mode อื่นเป็น compatibility record แยก ไม่ใช่เหตุให้บังคับเปลี่ยน

### v1.4.0 Computer Use

ใช้ test application ที่ไม่มีข้อมูลจริง:

1. observe → click/type/key/scroll โดยอ้าง observation ID
2. stale/window-change/DPI/coordinate denial
3. protected-field refusal และ emergency stop
4. cancellation ตัด queued actions
5. screenshot retention/audit inspection

## 7. Documentation and release checklist

ก่อน tag ทุกครั้งต้องทำตามลำดับ:

1. freeze tool/config contract
2. update README, ROADMAP, architecture, security, operations, install/upgrade, testing, compatibility, release status และ changelog
3. search ทั้ง repo หา version/tool-count/config examples เก่า
4. run automated suite, shellcheck และ static/dependency checks
5. run live acceptance และบันทึก environment/limitations
6. security review protected paths, approval, redaction และ release diff
7. tag signed commit, build archive/checksums จาก commit เดียวกัน
8. ดาวน์โหลด release assets จาก GitHub แล้วตรวจ filename, contents, SHA-256 และ signature จริง

เอกสารต้องเสร็จก่อน tag/release ไม่ใช่อัปเดตย้อนหลังหลังเผยแพร่

## 8. Definition of done สำหรับ v1.2.0

`v1.2.0` พร้อม release เมื่อครบทุกข้อ:

- Hands native tools ทำงานโดยไม่ invoke/import execution path ของ Hermes/Codex
- critical OFF/OFF/ON fallback ผ่านทั้ง automated test และ WSL2 live acceptance
- workspace/protected path/executable policy fail closed และมี adversarial coverage
- write/patch/execute ตาม risk ต้องผ่าน local immutable approval ไม่มี MCP approve
- process timeout/cancel/restart semantics ไม่รายงานผลเกินหลักฐาน
- audit ไม่มี prompt/output/content/secret และผ่าน rotation/permission tests
- upgrade default ปิด Hands และไม่เพิ่ม privilege
- เอกสาร/tool count/version/config/release assets ตรงกันทั้งหมด

## 9. ประเด็นที่ต้องตัดสินใจก่อนเริ่ม code

1. schema version 2 หรือ additive version 1
2. Hands tools จะถูก discover เมื่อ disabled แล้วตอบ `disabled` หรือ register เฉพาะเมื่อ enabled — แนะนำ discover เสมอเพื่อ contract/tool count คงที่
3. read-only executable profiles ใดปลอดภัยพอไม่ต้อง approve; เริ่ม conservative และ require approval หากไม่แน่ใจ
4. baseline protected paths ที่ผู้ใช้เพิ่มได้แต่ลดไม่ได้
5. รองรับ bind mounts/hard links ระดับใดใน v1.2.0
6. เก็บ output เป็นไฟล์หรือ SQLite; ต้องมี truncation/rotation/recovery ชัดเจน
7. local approval ใช้ CLI เดิมก่อน หรือเพิ่ม companion UI ในรุ่น Windows
8. Windows helper transport/auth/signing/distribution model

คำตอบของข้อเหล่านี้ควรถูกบันทึกเป็น ADR ก่อน merge implementation PR แรก
