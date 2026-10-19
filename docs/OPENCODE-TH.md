# OpenCode task execution (UNRELEASED — SPEC.md section 18; no assigned release)

เอกสารนี้อธิบายส่วน execution ของ OpenCode adapter ซึ่งเป็น **งานที่ยังไม่เผยแพร่ (unreleased)**
บน branch `opencode-investigate` เท่านั้น ยังไม่มี release, tag, หรือ version note ใด ๆ
อ้างสิทธิ์ส่วนนี้ เว้นแต่จะปิด change-control gate ของ `docs/SPEC.md` section 14 ก่อน
สิ่งที่เผยแพร่แล้วใน v1.2.4 (18 ตุลาคม 2026) คือ **health-only adapter** (`opencode_health`
tool เดียว) เท่านั้น

## Tool count

- Baseline canonical: **27 tools** (default)
- เปิด `opencode` health adapter: **28 tools** (released v1.2.4)
- เปิด `opencode.execution` (เอกสารนี้): เพิ่ม 5 tools → **33 tools**
  - พิสูจน์ discovery ผ่าน SDK stdio fixture ทั้งสามรูปแบบ; ผล suite เต็มและ live acceptance ดู [TESTING.md](TESTING.md)

## Configuration

Merge fragment นี้เข้า `bridge-config.json` เดิม ห้ามแทนที่ไฟล์ทั้งฉบับ
แทนค่า binary และ workspace ด้วย absolute path จริงที่ operator ตรวจแล้ว
workspace ต้องเป็น directory ที่มีอยู่ และ state/output ของ bridge ต้องอยู่นอก workspace ทุกแห่ง

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
  1-14400 (default 1800), `max_output_bytes` 65536-8388608 (default 524288) —
  **เป็นค่าลงท้ายแยกจาก** `opencode.max_output_bytes` ของ health adapter ห้าม reuse กัน

## ขอบเขตความปลอดภัย (อ่านก่อนเปิดใช้ — ไม่มี sandbox)

- CLI ที่กำหนดรันด้วย **สิทธิ์เต็มของ bridge process** bridge ไม่เพิ่ม sandbox ใด ๆ
- การเลือก workspace เป็น **cwd allowlist เท่านั้น** ไม่ใช่ filesystem isolation
  และไม่ใช่ network isolation; process ที่รันอ่านไฟล์อื่นและออกเน็ตได้ตามสิทธิ์ OS
- bridge **ไม่ inject permission configuration** ไม่เปลี่ยนหรือลบค่าของ operator ใน `OPENCODE_CONFIG`,
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

## ตัวอย่างการสั่งงาน

หลังติดตั้ง branch สำหรับ Dev และเปิด config ให้ restart เฉพาะ Dev instance
ตรวจว่า profile `hermes-wsl-dev` ชี้ `bridge.sh` ของ candidate ใหม่ และใช้ health port 8081
ห้ามเรียก `tunnel.sh init/run` เดิมเพื่อเปิด Dev เพราะสคริปต์ใน baseline กำหนด
profile `hermes-wsl` ของ production ไว้ตายตัว ให้ใช้ launcher ของ operator ที่ระบุ
`hermes-wsl-dev` ชัดเจนและใช้ authenticated environment เดิม
แล้ว refresh plugin discovery ให้พบ 33 tools ก่อนส่งงานจริง
release v1.2.4 เดิมไม่มี execution tools เหล่านี้

เรียก `opencode_submit_task`:

```json
{
  "prompt": "อธิบายโครงสร้างโปรเจกต์นี้ ห้ามแก้ไฟล์",
  "workspace": "/absolute/canonical/workspace/path",
  "request_id": "opencode-20261019-01",
  "model": "opencode-go/glm-5.3-flash"
}
```

คำขอใน prompt ไม่ใช่ permission policy หรือ sandbox
ใช้ `job_id` ที่ตอบกลับเรียก `opencode_task_status` แล้ว `opencode_task_result`
`offset` เป็นจำนวนตัวอักษร เริ่มจาก 0 และใช้ `next_offset` ของหน้าก่อน
`max_chars` อยู่ในช่วง 1-24000; `truncated` บอกว่ายังมี output ที่เก็บไว้ให้อ่านต่อ
ถ้างานยัง `running` ต้องติดตาม status และอ่าน output ที่เพิ่มภายหลังด้วย

งานถัดไปใช้ request ID ใหม่ พร้อม `session_id` จากงานที่ completed ล่าสุด
และ workspace เดิม ไม่ต้องระบุ model อีกเพราะ bridge ใช้ model เดิม
ห้ามสร้าง session ID เองหรือใช้ session ของ OpenCode ที่สร้างนอก bridge
เมื่อ retry งานเดิมให้ใช้ request ID และ input เดิมทุก field รวมถึงการละ `session_id`
ถ้าคำขอครั้งแรกไม่ได้ระบุ field นี้; job/session เดิมจะถูกคืนพร้อมสถานะปัจจุบัน

เรียก `opencode_cancel_task` ด้วย job ID เพื่อขอหยุด แล้วติดตาม status จน terminal
การยกเลิกไม่ undo ไฟล์หรือผลข้างเคียงที่เกิดแล้ว
ใช้ `opencode_recent_tasks` กู้ job/session IDs หลัง reconnect

Resume รองรับเฉพาะ session ที่งานล่าสุด completed
ถ้าเป็น failed/cancelled/permission_required ให้ตรวจผลก่อนเริ่ม session ใหม่
ถ้าเป็น `unknown_exit` ให้หยุดส่งงานและให้ operator ตรวจ process ที่เกี่ยวข้อง
bridge ไม่มี remote force-unblock และไม่ฆ่า PID ที่พิสูจน์ ownership ไม่ได้
อย่าลบฐานข้อมูลเพื่อหลบด่านนี้ขณะอาจยังมีงานทำงานอยู่

ข้อจำกัด output: JSONL แต่ละบรรทัดไม่เกิน 65536 bytes; stdout/stderr แต่ละ stream
ไม่เกิน execution cap ที่กำหนด แม้ตั้ง cap สูงกว่านี้ก็ไม่ขยายขนาดต่อบรรทัด
หลัง deadline อาจใช้เวลาสั้นเพิ่มเติมตาม cleanup grace และการ drain ที่มีขอบเขต
`bridge_version.mcp_discovery_count` ยังคงรายงาน canonical default 27
ให้ตรวจ `tools/list`/discovery จริงเพื่อยืนยัน 33 tools ของ configuration ที่เปิด execution

## ข้อควรระวังสำหรับ operator

- ทดสอบเสมอใน workspace ที่แยกจาก production เพราะไม่มี filesystem/network isolation
- อย่าวาง secrets ใน workspace ที่ allowlist; native policy ของ OpenCode ฝั่ง operator
  คือชั้นป้องกันจริง ไม่ใช่ bridge
- `deny_prompt_patterns` ของ Codex ไม่มีผลกับ OpenCode; ตัวจำกัดจริงคือ allowlist ของ
  workspace/model, native permissions และ caps ข้างต้น

## เปิด Dev candidate ที่เตรียมไว้ (operator checkpoint: 19 ตุลาคม 2026)

candidate สำหรับการทดสอบครั้งนี้อยู่ที่ `~/hermes-mcp-bridge-opencode-dev`
เป็น unreleased git worktree ไม่ใช่ release ZIP ใหม่ workspace ที่เปิดไว้มีเพียง
`~/hermes-opencode-dev-workspace` และ model `opencode-go/glm-5.3-flash`
ณ checkpoint เตรียม candidate ตรวจ stdio ได้ 33 tools แต่ route ยังชี้ candidate เดิม.
หลัง operator เปิด Dev และ refresh แล้ว Work-chat acceptance ผ่านเมื่อ 19 ตุลาคม 2026;
ดู [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md). ขั้นตอนด้านล่างเก็บไว้สำหรับเปิดใหม่.

1. หยุดเฉพาะ tunnel ของ Dev ใน terminal ที่ใช้เปิด Dev เดิม เก็บ authenticated environment เดิมไว้
2. เปิด editor ของ Dev profile ด้วยคำสั่งด้านล่าง จดค่า command เดิมไว้สำหรับ rollback
   เปลี่ยนเฉพาะ `mcp.commands[0].command` ให้ชี้ absolute path ของ
   `~/hermes-mcp-bridge-opencode-dev/bridge.sh` ห้ามเปลี่ยน production profile,
   `tunnel_id` หรือ key/reference เดิม อย่าใส่ `~` ในค่า command โดยไม่ขยายเป็น absolute path

```bash
EDITOR=nano tunnel-client profiles edit hermes-wsl-dev
```

3. เปิด Dev จาก environment ที่เคย authenticate สำเร็จ คำสั่งนี้ระบุ profile/port ชัดเจน

```bash
tunnel-client run --profile hermes-wsl-dev --health.listen-addr 127.0.0.1:8081
```

4. Refresh plugin discovery แล้วตรวจ 33 tools และ `bridge_version.source_revision`
   ให้ตรง code head ที่ติดตั้ง ก่อนส่ง benign task ใน workspace ทดสอบ
   ทดสอบต่อ session เดิมหนึ่งรอบและตรวจไฟล์จริงเมื่อขอให้แก้ไฟล์

ขั้นตอนนี้เป็น manual operator handoff; operator เป็นผู้เปิด Dev สำหรับ acceptance ครั้งนี้
ไม่ต้องสร้าง key ใหม่ และห้ามอ่าน key ออกจาก process environment
หาก authenticated environment เดิมไม่พร้อม ให้หยุดแทนการใช้ profile production ทดแทน
