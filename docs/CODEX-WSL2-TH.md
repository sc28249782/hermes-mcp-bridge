# Codex/WSL2 แบบควบคุมสิทธิ์ — v1.0.0

v1.0.0 มี Hermes tools 10 ตัว, Codex tools 6 ตัว และ operations tools แบบ read-only 3 ตัว (`bridge_diagnostics`, `bridge_audit_recent`, `bridge_status`) รวม 19 tools โดย `codex_submit_task` เลือก model และ reasoning effort ได้ภายใต้นโยบายที่กำหนด

## ขอบเขตความปลอดภัย

- workspace ต้อง resolve แล้วอยู่ใต้ `codex.allowed_workspaces`
- ป้องกัน path traversal และ symlink escape ด้วย canonical path
- เรียก `codex` ด้วย argument array โดยตรง ไม่ผ่าน shell
- อนุญาตเฉพาะ `read-only` และ `workspace-write`; ไม่มี `danger-full-access`
- `workspace-write` จะไม่เริ่มจนกว่าผู้ใช้อนุมัติจาก terminal ใน WSL2
- ไม่มี MCP approval tool สำหรับ Codex จึงไม่สามารถให้ agent อนุมัติตัวเอง
- log และฐานข้อมูลงานอยู่ใน `state/` และตั้ง permission แบบ private
- จำกัด prompt 32,000 ตัวอักษรและ runtime เริ่มต้น 1,800 วินาที
- Codex sandbox ควบคุม filesystem/network ชั้นสุดท้าย; bridge ไม่เพิ่มสิทธิ์ network
- การเลือก model/reasoning effort เป็นเพียง execution preference ไม่ได้ขยาย sandbox, network หรือสิทธิ์เขียนไฟล์

## ตั้งค่า

ตั้งแต่ v0.9.0 `bridge-config.json` รองรับ `schema_version: 1`; `bash install.sh` จะเติมค่านี้ให้ config เก่าอย่าง deterministic. หาก doctor/diagnostics แสดง `config_warnings` ให้แก้ key ที่ไม่รู้จักก่อนใช้งานจริง.

ตรวจว่า Codex CLI ติดตั้งและ login ใน WSL2 แล้วด้วย `codex --version` จากนั้นเพิ่มใน `bridge-config.json` โดยรักษาค่า Hermes เดิมไว้:

```json
"schema_version": 1,
"codex": {
  "binary": "codex",
  "approval_ttl_seconds": 3600,
  "watchdog_interval_seconds": 15,
  "workspaces": [
    {
      "path": "/mnt/e/Projects/OpenHDK-validation",
      "modes": ["read-only", "workspace-write"],
      "max_prompt_chars": 32000,
      "max_runtime_seconds": 1800,
      "max_concurrency": 1,
      "deny_prompt_patterns": ["deploy production"],
      "allowed_models": ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"],
      "allowed_reasoning_efforts": ["low", "medium", "high"]
    }
  ]
},
"audit": {
  "enabled": true,
  "max_bytes": 1000000,
  "retention_files": 7
}
```

`allowed_workspaces` แบบเดิมยังใช้ได้เพื่อความเข้ากันได้ แต่ `workspaces` ช่วยกำหนด policy แยกต่อ repository ได้ละเอียดกว่า ค่า `approval_ttl_seconds` ใช้กับ write job ที่รอการอนุมัติ (60–86,400 วินาที); เมื่อหมดอายุ job จะเป็น `expired` และเริ่มใหม่ไม่ได้

`allowed_models` และ `allowed_reasoning_efforts` ใส่ได้ทั้งระดับ `codex` (เป็นค่าเริ่มต้น) หรือในแต่ละ workspace (override ค่าเริ่มต้น) หากเป็น array ว่างหรือไม่ระบุ จะ **ไม่อนุญาต override** และ Codex CLI จะใช้ค่า default local ของผู้ใช้แทน bridge ไม่ค้นหรือเดาชื่อโมเดลที่บัญชีใช้ได้เอง; ตรวจ allowlist ที่มีผลจริงด้วย `codex_health`

`watchdog_interval_seconds` (5–300, ค่าเริ่มต้น 15) เป็นช่วงที่ persistent bridge server ตรวจ job ที่กำลังรันและบังคับ `max_runtime_seconds` ของ workspace แม้ไม่มีใครเรียก `codex_task_status`. หาก server ไม่ทำงานหลัง local CLI approve, enforcement จะกลับมาเมื่อ server เริ่มใหม่หรือมีการ poll status. เมื่อ timeout/cancel bridge ส่ง SIGTERM, รอช่วงสั้น, ส่ง SIGKILL หากยังไม่จบ และจะไม่เขียนสถานะ terminal จนยืนยันว่า process ตาย. Job ที่ bridge restart แล้วพบว่า process จบแต่ไม่ทราบ exit code จะเป็น `unknown_exit` ไม่ใช่ `completed`.

ส่ง `model` และ/หรือ `reasoning_effort` ไปที่ `codex_submit_task` เฉพาะค่าที่อยู่ใน allowlist ของ workspace เท่านั้น ค่า reasoning ที่ bridge รู้จักคือ `low`, `medium`, `high`, `xhigh`, `max`, `ultra` แต่จะใช้ได้จริงก็ต่อเมื่อโมเดลและบัญชี Codex รองรับด้วย หากละพารามิเตอร์ใด Bridge จะไม่ส่ง override นั้นไปยัง Codex CLI

`deny_prompt_patterns` เป็น pre-flight guard แบบ literal case-insensitive สำหรับปฏิเสธ prompt ที่ตรง pattern ก่อนเริ่มงาน **ไม่ใช่ sandbox และไม่ใช่สิ่งทดแทน local approval** จึงห้ามใช้เป็นมาตรการความปลอดภัยเพียงชั้นเดียว

ตรวจ policy ด้วย `./bridge.sh codex-doctor` แล้ว restart `tunnel.sh run` และเปิดแชทใหม่

## Codex tools 6 ตัว

1. `codex_health`
2. `codex_submit_task`
3. `codex_task_status`
4. `codex_task_result`
5. `codex_cancel_task`
6. `codex_recent_tasks`

งานอ่านอย่างเดียวเริ่มได้ทันทีด้วย `mode=read-only` ส่วนงานแก้ไขจะคืน `pending_local_approval` และ job ID

```bash
./bridge.sh codex-approve codex_แทนด้วย_JOB_ID
```

คำสั่งจะแสดง job ID, workspace, mode และ prompt ให้ตรวจ ต้องพิมพ์ `APPROVE` ตรงตัวจึงเริ่มทำงาน หากต้องการปฏิเสธใช้ `./bridge.sh codex-deny codex_แทนด้วย_JOB_ID`

การกดยืนยัน tool call ใน ChatGPT ไม่ทดแทนการอนุมัติใน terminal นี้

ตัวอย่างงานอ่านที่ขอ model/effort ตาม allowlist:

```text
codex_submit_task(
  prompt="Inspect the current git status only. Do not modify files or use network.",
  workspace="/mnt/e/Projects/OpenHDK-validation",
  mode="read-only",
  model="gpt-5.6-sol",
  reasoning_effort="high"
)
```

สำหรับ `workspace-write` ชื่อ model/effort จะปรากฏในหน้าจอ `codex-approve` เพื่อให้ผู้ใช้ตรวจพร้อม prompt แต่ยังต้องพิมพ์ `APPROVE` เช่นเดิม

การทดสอบ live acceptance ของรุ่นนี้ผ่านด้วย `gpt-5.6-sol` และ `high`; ต้องใช้ model ID เช่นนี้ ไม่ใช่ชื่อที่แสดงใน UI เช่น `GPT-5.6 Sol`.

## Diagnostics, audit และ recovery

เรียก `bridge_diagnostics` หรือรันคำสั่ง local ต่อไปนี้เพื่อตรวจ Hermes, Codex, permission ของ state และสถานะ audit log:

```bash
./bridge.sh diagnostics
./bridge.sh audit-recent
```

Audit log อยู่ที่ `state/audit.jsonl` ด้วย mode `600` และเป็น JSON Lines แบบหมุนไฟล์ตาม `max_bytes` เก็บย้อนหลังตาม `retention_files` (1–30 ไฟล์) บันทึกเฉพาะ lifecycle เช่น submit/start/approve/deny/finish/cancel, job/run ID, workspace, sandbox mode, ชื่อ model/reasoning effort ที่ร้องขอ และจำนวนตัวอักษรของ prompt

Audit log **ไม่บันทึก prompt, output, Hermes API key หรือ OpenAI runtime key**

`bridge_audit_recent` ส่งออกเฉพาะ redacted audit events ล่าสุดจาก MCP (limit 1–500); ใช้สำหรับตรวจสอบ ไม่ใช่ช่องทางอ่าน prompt/output

หลัง bridge หรือ WSL2 restart, job ที่กำลังรันจะไม่ถูกส่งซ้ำโดยอัตโนมัติ `codex_task_status` จะรายงาน `recovered_after_restart: true` เมื่อกำลังอ่านสถานะจาก persisted state แทน process handle เดิม หาก process จบระหว่าง bridge ปิดอยู่ exit code อาจไม่ทราบ; ตรวจ JSONL result และผลกระทบใน workspace ก่อนเริ่มงานใหม่

## Acceptance test ที่แนะนำ

1. เรียก `codex_health` และตรวจ version/allowlist รวมถึง model/reasoning allowlist
2. ส่ง `read-only` ให้ตรวจ `git status` และยืนยันว่าไม่มีไฟล์เปลี่ยน
3. ทดลอง workspace นอก allowlist และ symlink escape ต้องถูกปฏิเสธ
4. ส่ง `workspace-write`; ก่อน local approval ต้องไม่มี process Codex เริ่มทำงาน
5. deny หนึ่งงานและ approve หนึ่งงานที่แก้ไฟล์ทดสอบแบบย้อนกลับได้
6. ตรวจ status/result/cancel/recent และยืนยันว่า job ต่าง bridge ถูกปฏิเสธ
7. ทดลอง model หรือ effort ที่อยู่นอก allowlist ต้องถูกปฏิเสธก่อนเริ่ม; ทดลองค่าที่อยู่ใน allowlist แล้วตรวจ status/recent/audit ว่าตรงกัน

อ้างอิง: https://developers.openai.com/codex/cli
