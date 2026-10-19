# OpenCode task execution (UNRELEASED — SPEC.md section 18; no assigned release)

เอกสารนี้อธิบายส่วน execution ของ OpenCode adapter ซึ่งเป็น **งานที่ยังไม่เผยแพร่ (unreleased)**
บน branch `opencode-investigate` เท่านั้น ยังไม่มี release, tag, หรือ version note ใด ๆ
อ้างสิทธิ์ส่วนนี้ เว้นแต่จะปิด change-control gate ของ `docs/SPEC.md` section 14 ก่อน
สิ่งที่เผยแพร่แล้วใน v1.2.4 (18 ตุลาคม 2026) คือ **health-only adapter** (`opencode_health`
tool เดียว) เท่านั้น

## สถานะ tool count (provisional)

- Baseline canonical: **27 tools** (default)
- เปิด `opencode` health adapter: **28 tools** (released v1.2.4)
- เปิด `opencode.execution` (เอกสารนี้): เพิ่ม 5 tools → **33 tools**
  - ตัวเลข 27/28/33 เป็นค่าตาม contract; ยังไม่ยืนยันผ่าน test suite ขั้นสุดท้าย
    จนกว่าการตรวจสอบจะเสร็จ อย่าอ้างว่า "ผ่านแล้ว"

## Schema `opencode.execution` (opt-in เดี่ยวชัดเจน)

```json
{
  "opencode": {
    "enabled": true,
    "binary": "/absolute/path/to/opencode",
    "execution": {
      "enabled": true,
      "allowed_workspaces": ["/absolute/canonical/workspace/path"],
      "allowed_models": ["opencode-go/glm-5.3-flash"],
      "max_prompt_chars": 32000,
      "max_runtime_seconds": 1800,
      "max_output_bytes": 524288
    }
  }
}
```

- `execution.enabled` default `false`; ปิด = fail closed, ไม่ register tool, ไม่ spawn
- เปิดได้เมื่อ `opencode.enabled=true` + `opencode.binary` ถูกต้องตามกติกา health adapter
- `allowed_workspaces` ต้องเป็น list ที่ไม่ว่าง ของ absolute path ไม่มี control characters
  (0x00-0x1F, 0x7F); canonicalize ครั้งเดียวตอนโหลด
- `allowed_models` ต้องเป็น list ที่ไม่ว่าง รูปแบบ `provider/model` (เช่น
  `opencode-go/glm-5.3-flash`)
- ขอบเขตจำกัด: `max_prompt_chars` 1-131072 (default 32000), `max_runtime_seconds`
  30-14400 (default 1800), `max_output_bytes` 65536-8388608 (default 524288) —
  **เป็นค่าลงท้ายแยกจาก** `opencode.max_output_bytes` ของ health adapter ห้าม reuse กัน

## ขอบเขตความปลอดภัย (อ่านก่อนเปิดใช้ — ไม่มี sandbox)

- CLI ที่กำหนดรันด้วย **สิทธิ์เต็มของ bridge process** bridge ไม่เพิ่ม sandbox ใด ๆ
- การเลือก workspace เป็น **cwd allowlist เท่านั้น** ไม่ใช่ filesystem isolation
  และไม่ใช่ network isolation; process ที่รันอ่านไฟล์อื่นและออกเน็ตได้ตามสิทธิ์ OS
- bridge **ไม่ inject permission configuration** ไม่ตั้ง `OPENCODE_CONFIG`,
  `OPENCODE_CONFIG_CONTENT`, `OPENCODE_CONFIG_DIR` และไม่ใช้ flag ที่เปลี่ยนพฤติกรรม
  permission — config, plugins และ saved permissions ของ OpenCode ฝั่ง operator ทำงาน
  ตามปกติ (native policy)
- **ห้าม `--auto`** — native permission ที่ยังตอบไม่ได้ (unresolved ask) จบด้วย
  bounded deadline เป็น `failed` หรือจบเป็น `permission_required` เมื่อเห็น protocol
  event ชัดเจน bridge **ไม่เคยอนุมัติแทน**
- เปิดใช้ = ยอมรับ trust decision แบบเดียวกับการปล่อยให้ model ทำงานในเครื่อง

## 5 tools และ lifecycle

1. `opencode_submit_task(prompt, workspace, request_id, session_id=None, model=None)` —
   ส่งงาน ได้รับ `{job_id, status, session_id, model}`; เมื่อระบุ `session_id` ต้องเป็น
   session ที่ bridge เป็นเจ้าของ และ resume ได้เฉพาะ **workspace และ model เดิม**
2. `opencode_task_status(job_id)` — สถานะแบบ redacted (ไม่มี prompt/output/credentials)
3. `opencode_task_result(job_id, offset=0, max_chars=12000)` — อ่านผลลัพธ์แบบ paginated
   **เนื้อหาเป็น model output ที่ต้องตรวจเอง (untrusted)**
4. `opencode_cancel_task(job_id)` — ขอยกเลิก; worker ยืนยัน cleanup ก่อนถึง `cancelled`
5. `opencode_recent_tasks()` — รายการล่าสุด 30 รายการแบบ redacted

สถานะ: `pending → running → completed | failed | cancelled | permission_required |
unknown_exit` สถานะ terminal เปลี่ยนไม่ได้ มี idempotency ด้วย `request_id`: ส่งซ้ำ
เดิม = ได้ acknowledgement เดิม; ส่ง `request_id` เดิมพร้อม input ต่าง = ปฏิเสธ ไม่เรียก
model ซ้ำ. Concurrency 1 ทั้งระบบและต่อ session; งานใหม่เมื่อ slot ว่างเท่านั้น
(ไม่มี queue ไม่จำกัด)

- `completed` = native turn จบจริง (มี completion event + exit 0) **ไม่ได้แปลว่า
  เป้าหมายงานสำเร็จ** — ต้องอ่าน output ตรวจเอง; การปฏิเสธแบบ text ล้วนก็อาจ `completed`
- `permission_required` เกิดเฉพาะเมื่อเห็น native permission event จาก output เท่านั้น
  กรณีไม่ชัดเจนจะจบเป็น `failed` (timeout) ไม่เดา
- `unknown_exit` เมื่อ worker เสียการควบคุม process — ไม่มีการสรุป success/cancel แทน
- stderr/stdout มี cap ตาม `max_output_bytes`; state/log เก็บ 0600, ไดเรกทอรี 0700,
  output อยู่นอก workspace ทั้งหมด; audit ไม่มี prompt/output/credentials

## ข้อควรระวังสำหรับ operator

- ทดสอบเสมอใน workspace ที่แยกจาก production เพราะไม่มี filesystem/network isolation
- อย่าวาง secrets ใน workspace ที่ allowlist; native policy ของ OpenCode ฝั่ง operator
  คือชั้นป้องกันจริง ไม่ใช่ bridge
- `deny_prompt_patterns` ของ Codex ไม่มีผลกับ OpenCode; ตัวจำกัดจริงคือ allowlist ของ
  workspace/model, native permissions และ caps ข้างต้น
