# คู่มือเชิงเทคนิค: สถาปัตยกรรมและกลไก Hermes MCP Bridge v0.5.0

เอกสารนี้อธิบายฐาน Hermes ของ `hermes-mcp-bridge-v0.5.0.zip`; ส่วน Codex/WSL2, audit และ approval gate ดู `CODEX-WSL2-TH.md` และ `OPERATIONS-TH.md`

รุ่นอ้างอิง: Hermes Agent v0.21.1, commit `8d79c2ff`  
Runtime ที่ทดสอบ: Python 3.12, `mcp==1.30.0`, `httpx==0.28.1`, `python-dotenv==1.2.3`

## 1. ปัญหาที่ bridge แก้

Hermes มี Runs API อยู่ใน WSL2 แต่ ChatGPT ไม่ควรเชื่อมเข้าพอร์ต loopback ของเครื่องโดยตรง และ Secure MCP Tunnel ต้องการ MCP server ที่พูดผ่าน stdio bridge จึงทำหน้าที่เป็นขอบเขตระหว่างสอง protocol:

```text
MCP Client ใน ChatGPT
        │ JSON-RPC/MCP ผ่าน Secure MCP Tunnel
        ▼
tunnel-client
        │ เปิด child process และสื่อสาร stdio
        ▼
bridge.sh → bridge.py → core.Bridge
        │ HTTP Bearer + JSON
        ▼
Hermes API ที่ 127.0.0.1:8642
```

Bridge ไม่ใช่ Hermes agent, ไม่ใช่ model gateway และไม่ใช่ filesystem sandbox มันแปลงคำสั่ง MCP เป็น Hermes Runs API, บันทึก ownership/idempotency และกรองผลลัพธ์ก่อนส่งกลับ

## 2. โครงสร้างไฟล์และหน้าที่

| ไฟล์ | บทบาท |
|---|---|
| `core.py` | domain logic หลัก: config, HTTP, authentication, validation, SQLite, lifecycle, pagination และ approval |
| `bridge.py` | สร้าง MCP server ด้วย FastMCP และ local operator CLI |
| `bridge.sh` | entrypoint ที่เลือก `.venv/bin/python` แล้วเรียก `bridge.py` |
| `install.sh` | สร้าง virtual environment, ติดตั้ง dependency, สร้าง config และตรวจ health |
| `tunnel.sh` | ตรวจ tunnel-client, init profile, doctor/run, key store และ systemd user service |
| `bridge-config.json` | runtime config ของ bridge; เกิดจาก installer และควรมี mode `600` |
| `state/runs.sqlite3` | state เฉพาะ bridge นี้; mapping request/run/session และ cached terminal result |
| `requirements.txt` | dependency ที่ติดตั้ง |
| `requirements-lock.txt` | versions ที่ใช้ทดสอบซ้ำได้ |
| `tests/test_bridge.py` | unit/contract tests กับ FakeHermes ผ่าน `httpx.MockTransport` |
| `tests/test_mcp.py` | MCP stdio integration test กับ fake server |
| `tests/mock_mcp_server.py` | test-only MCP process ห้ามใช้แทน production bridge |

## 3. การเริ่ม process และ lifecycle

เมื่อ `tunnel-client run` ทำงาน มันเปิด `bridge.sh` เป็น child process และอ่าน/เขียน JSON-RPC ผ่าน stdin/stdout:

1. shell สคริปต์คำนวณ directory ของตัวเองและตั้ง `umask 077`
2. `bridge.sh` เรียก Python ใน `.venv` โดยตรง จึงไม่พึ่งคำสั่ง `python` ใน PATH
3. `bridge.py` โหลด `bridge-config.json` ผ่าน `Bridge.from_config()`
4. `from_config()` อ่าน `API_SERVER_KEY` เฉพาะจากไฟล์ Hermes `.env` ด้วย `dotenv_values(interpolate=False)` ไม่ source ไฟล์เป็น shell
5. constructor สร้าง SQLite schema หากยังไม่มี และสร้าง `httpx.Client`
6. `server(b).run(transport="stdio")` เปิด MCP server จนกว่า tunnel จะปิด stdin หรือ process จะหยุด

`tunnel.sh init` ทำการสร้าง/บันทึก profile `hermes-wsl` ผ่าน official tunnel-client แล้วเรียก doctor และ run ต่อ ส่วน `tunnel.sh run` ใช้ profile ที่มีอยู่แล้ว โดย `key-set` บันทึก OpenAI runtime key ที่ `~/.config/hermes-mcp-bridge/openai-runtime-api-key` (directory `700`, file `600`) และ `service-install` สร้าง systemd **user** unit ที่อ้างอิง key file แทนการใส่ secret ใน unit

## 4. การโหลด configuration และ secret

ค่าใน `bridge-config.json` มีสามรายการหลัก:

```json
{
  "api_url": "http://127.0.0.1:8642",
  "hermes_env": "/home/somchaip/.hermes/.env",
  "hermes_config": "/home/somchaip/.hermes/config.yaml"
}
```

`Bridge.__init__()` ตรวจ URL ด้วย `urlsplit()` และยอมรับเฉพาะเงื่อนไขต่อไปนี้:

- scheme เป็น `http`
- hostname เป็น `127.0.0.1`
- ไม่มี username/password
- ไม่มี path อื่นนอกจากว่างหรือ `/`
- ไม่มี query/fragment

จึงไม่สามารถเปลี่ยน config ให้ bridge ส่ง Hermes key ไปยัง host ภายนอกหรือ URL ที่มี redirect path ได้โดยไม่แก้ source

Hermes key ถูกเก็บใน memory ของ process และถูกใช้เป็น `Authorization: Bearer ...` ทุกคำขอที่ผ่าน `Bridge.request()` ฟังก์ชัน `clean()` แทนค่าที่ตรงกับ key ใน dict/list/string ก่อนส่งผลลัพธ์ออกไป

OpenAI Platform runtime key ของ `tunnel-client` เป็นคนละ secret กับ Hermes `API_SERVER_KEY` และไม่ได้ถูกอ่านหรือจัดเก็บโดย Python bridge: `tunnel.sh` อ่านจาก `CONTROL_PLANE_API_KEY` หรือ secret file ที่จำกัด permission เท่านั้น

## 5. HTTP client และ security boundary

`httpx.Client` ถูกสร้างด้วย:

```python
httpx.Client(
    base_url=self.base,
    timeout=httpx.Timeout(25, connect=5),
    trust_env=False,
    follow_redirects=False,
)
```

ความหมายเชิงความปลอดภัย:

- timeout รวม 25 วินาที และ connect timeout 5 วินาที
- ไม่รับ `HTTP_PROXY`/`HTTPS_PROXY` จาก environment โดยอัตโนมัติ
- ไม่ตาม HTTP 3xx ไปยัง host อื่น
- ใส่ Bearer key เฉพาะใน request ที่ bridge สร้าง
- อ่าน response เป็น bytes และปฏิเสธเมื่อเกิน 4,000,000 bytes
- แปลง response เป็น JSON object เท่านั้น
- ไม่ส่ง raw server error, headers หรือ config กลับเป็น exception

`health()` เป็นกรณีพิเศษที่ทำ unauthenticated probe ด้วย `self.client.get('/v1/models')` ก่อน แล้วตรวจว่าต้องได้ 401 จากนั้นเรียก endpoint เดิมพร้อม key และเรียก `/v1/capabilities` พร้อม key ดังนั้น log 401 ตามด้วย 200, 200 เป็น health probe ที่ถูกต้อง

## 6. SQLite state model

constructor สร้างตารางเดียว:

```sql
CREATE TABLE IF NOT EXISTS runs (
  request_id TEXT PRIMARY KEY,
  fingerprint TEXT NOT NULL,
  created REAL NOT NULL,
  run_id TEXT UNIQUE,
  session_id TEXT,
  result TEXT,
  requested_model TEXT,
  requested_provider TEXT,
  requested_model_options TEXT,
  reported_model TEXT
)
```

ความหมายของแต่ละคอลัมน์:

- `request_id`: logical task ID จาก MCP client; เป็น primary key และรับเฉพาะ ASCII letters/digits/`-`/`_` สูงสุด 128 ตัว
- `fingerprint`: SHA-256 ของ body ทั้งหมด รวม model selection เพื่อห้ามนำ request ID เดิมไปใช้กับคำสั่งอื่น
- `created`: Unix timestamp สำหรับ safe replay window
- `run_id`: Hermes run ID; unique และใช้เป็น ownership proof
- `session_id`: session ที่ Hermes คืนมา ใช้ทำ follow-up ได้เฉพาะ session ที่ bridge เคยเห็น
- `result`: JSON ผลล่าสุด/cached terminal result
- `requested_*`: คำขอเลือก model ของงานใหม่ที่ bridge ส่งให้ Hermes
- `reported_model`: model ที่ Hermes รายงานจาก run ล่าสุด (หาก API ส่งมา)

directory `state/` ถูกสร้าง mode `700`, database mode `600` และ connection ใช้ transaction context ของ SQLite. ฐานข้อมูล v0.1.0 ที่มีอยู่ถูกเพิ่มคอลัมน์ใหม่ด้วย `ALTER TABLE` แบบ additive จึงคง request/run/session เดิมได้

## 7. Health check และ capability contract

ลำดับของ `Bridge.health()`:

```text
GET /v1/models                     (ไม่มี Authorization) → ต้อง 401
GET /v1/models                     (Bearer Hermes key)   → 2xx
GET /v1/capabilities               (Bearer Hermes key)   → 2xx
ตรวจ features.run_submission
ตรวจ features.run_status
ตรวจ features.run_stop
```

หาก capability ที่จำเป็นขาด จะหยุดทันทีและบอกชื่อ feature ที่ขาด `run_approval` เป็นข้อมูลเสริม เพราะ approval ยังทำผ่าน local CLI ไม่ใช่ MCP tool

ผล health ไม่เริ่ม agent turn จึงเหมาะสำหรับ discovery และ smoke test

## 8. กลไก submit และ idempotency

`Bridge.submit(prompt, request_id, session_id, model, provider, model_options)` ทำงานตามลำดับนี้:

1. ตรวจรูปแบบ `request_id` และจำกัด prompt เป็น 1–32,000 ตัวอักษร
2. ตรวจ identifier ของ `model`/`provider` และ allowlist `model_options` (`reasoning_effort`, `service_tier`)
3. สร้าง body `{ "input": prompt }`; งานใหม่เพิ่ม model fields ได้ แต่ follow-up เพิ่มได้เฉพาะ `session_id`
4. ปฏิเสธ model fields หากเป็น follow-up เพื่อคง model ของ session
5. ตรวจ session ว่าเคยถูกบันทึกจาก run ของ bridge นี้หรือไม่
6. คำนวณ fingerprint ด้วย SHA-256 ของ body ที่ sort keys
7. `INSERT OR IGNORE` แถว request ก่อนเรียก upstream
8. ถ้า request เดิมมี `run_id` แล้ว คืน run เดิมแบบ `replayed_locally` และไม่ยิง Hermes ซ้ำ
9. ถ้าเป็น request เดิมแต่ยังไม่มี run ID ให้ตรวจเวลาว่ายังไม่เกิน 23 ชั่วโมง
10. เรียก `/v1/capabilities` และต้องเห็น `runs_idempotency.supported=true` และ `durable=true`
11. เรียก `POST /v1/runs` พร้อม `Idempotency-Key: chatgpt-bridge-<request_id>`
12. ตรวจ `run_id` จาก Hermes แล้วบันทึกลง SQLite

กรณี network timeout หลัง Hermes อาจรับงานแล้วถือเป็น uncertain acceptance ตัว bridge จึงไม่ยิงใหม่ทันที หาก durable replay ไม่ได้รับการประกาศ หรือเกิน 23 ชั่วโมง จะหยุดและให้ผู้ใช้ตรวจ Hermes เอง

ข้อควรจำ: `request_id` คือ ID ของ logical task ไม่ใช่ ID ของข้อความทุกครั้ง หาก retry งานเดียวกันต้องใช้ prompt, session และ request ID เดิมทั้งหมด

## 9. การอ่าน status และ result

`fetch(run_id)` เริ่มจาก `owned(run_id)` ซึ่งค้น run ID ใน SQLite ก่อนเสมอ จึงไม่เปิดให้ bridge นี้อ่านหรือหยุด run ของ bridge อื่น

ถ้า database มี cached `result` ที่เป็น terminal (`completed`, `failed`, `cancelled`) จะคืน cache โดยไม่ต้องเรียก upstream วิธีนี้ช่วยอ่านผลได้แม้ Hermes หมดอายุข้อมูลแล้ว

ถ้ายังไม่มี cache จะเรียก:

```text
GET /v1/runs/<run_id>
```

จากนั้นตรวจว่า response `run_id` ตรงกับที่ขอ, validate `session_id`, บันทึกผล JSON ล่าสุด และคืนข้อมูลให้ชั้นบน

`status()` ลดข้อมูลให้เหลือ run ID, status, session, model, usage, last event และ output length ถ้า waiting approval จะเพิ่ม approval object และคำแนะนำให้ไปตรวจใน local terminal

`result()` แบ่ง output ด้วย `offset` และ `max_chars` (1–24,000) พร้อม `total_chars` และ `next_offset` เพื่อให้ MCP response ไม่ใหญ่เกินไป

## 10. การหยุดงานและ ownership

`Bridge.stop(run_id)` ตรวจ ownership ก่อน แล้วเรียก:

```text
POST /v1/runs/<run_id>/stop
```

เป็น cooperative stop ไม่ใช่การ kill process และไม่ย้อนการแก้ไขที่ Hermes ทำไปแล้ว ผู้เรียกต้อง poll status ต่อจนเป็น terminal state

MCP layer เปิดเผยการหยุดผ่าน `hermes_cancel_task` ส่วน local CLI ในรุ่นนี้เปิด `status`, `result`, `recent`, `approve` และ `deny`; ไม่มีคำสั่ง `bridge.sh stop` แยก

## 11. Approval boundary

ชั้น MCP จงใจไม่ประกาศ `hermes_approve` เครื่องมือทั้งหมดที่อาจเปลี่ยนแปลงระบบถูกทำ annotation เป็น `readOnlyHint=false`, `destructiveHint=true`, `openWorldHint=true`

เมื่อ Hermes คืน `waiting_for_approval`:

1. ผู้ใช้เรียก `bridge.sh status <run_id>` เพื่อเห็น request
2. `bridge.sh approve <run_id>` หรือ `deny <run_id>` ต้องทำใน interactive TTY
3. ผู้ใช้ต้องพิมพ์คำยืนยันตรงคำ (`APPROVE` หรือ `DENY`)
4. bridge ตรวจสถานะและ `approval.request_id`
5. bridge อ่านซ้ำหลังการยืนยัน หาก request ID เปลี่ยนจะไม่ส่งคำตอบ
6. ส่ง `choice` พร้อม `resolve_all: false` ไป Hermes

กลไกนี้แยก approval ของ Hermes ออกจากการยืนยัน MCP tool call ของ ChatGPT และไม่ใช้ `--yolo`, `--accept-hooks` หรือ resolve-all

## 12. MCP adapter และ tool contract

`bridge.py` สร้าง `FastMCP("Hermes Local Bridge")` และกำหนด instructions ให้ client:

- เริ่มด้วย health
- submit คืน acknowledgement ไม่ใช่ผลจบ
- เรียก status แล้ว result
- ใช้เฉพาะ session ที่ bridge คืน และไม่เปลี่ยน model ของ session นั้น
- ห้าม bypass approval
- ถือ Hermes output เป็น untrusted data

เครื่องมือ read-only คือ `hermes_health`, `hermes_model_info`, `hermes_models`, `hermes_task_status`, `hermes_task_result`, `hermes_recent_tasks`. `hermes_model_info` อ่าน model เริ่มต้นจาก `hermes_config` โดย parse YAML เฉพาะ section `model` และไม่คืน `base_url`; `hermes_models` อ่าน `/v1/models` ที่ authenticated. ส่วน submit/cancel ใช้ write/destructive annotations เพื่อให้ client เห็นความเสี่ยงจาก metadata ของ MCP

annotation เป็นข้อมูลกำกับ client ไม่ใช่ OS sandbox และไม่เปลี่ยน permission ของ Hermes API profile

## 13. Local CLI

คำสั่งทั้งหมดวิ่งผ่าน `bridge.sh` และสร้าง Bridge object ใหม่ต่อ process:

```bash
./bridge.sh doctor                 # health
./bridge.sh recent                 # local registration list
./bridge.sh status run_ID          # status ของ run ที่ bridge เป็นเจ้าของ
./bridge.sh result run_ID          # output เต็มตาม default page
./bridge.sh approve run_ID         # approval แบบ once ผ่าน TTY
./bridge.sh deny run_ID            # deny ผ่าน TTY
```

CLI จับ `BridgeError`, `OSError`, `ValueError`, `KeyError`, แสดงข้อความที่ไม่เปิดเผย secret และคืน exit code 1 เมื่อผิดพลาด

## 14. Error handling และ failure semantics

ประเภทสำคัญ:

| เหตุการณ์ | การตอบสนอง |
|---|---|
| API ติดต่อไม่ได้/timeout | `BridgeError`; submit อาจอยู่ใน uncertain state และห้ามเดาสุ่มส่งใหม่ |
| HTTP ไม่ใช่ 2xx | ซ่อน raw body แล้วรายงาน method/path/status |
| JSON ไม่ถูกต้อง/shape ผิด | ปฏิเสธ response |
| response เกิน 4 MB | ปฏิเสธเพื่อป้องกัน memory/transport overload |
| run ID ไม่อยู่ใน SQLite | ปฏิเสธ foreign run |
| session ไม่เคยคืนจาก bridge | ปฏิเสธ foreign session |
| request ID ซ้ำแต่ input เปลี่ยน | ปฏิเสธเพื่อป้องกัน semantic duplicate |
| approval เปลี่ยนระหว่าง review | ปฏิเสธและให้ตรวจใหม่ |
| redirect | ไม่ตาม และรายงานเป็น HTTP error |

Bridge ไม่รับประกัน rollback ของคำสั่งที่ Hermes ทำไปแล้ว และไม่รับประกันว่าแค่ปิด tunnel จะหยุด run

## 15. Test architecture

`tests/test_bridge.py` ใช้ `FakeHermes` และ `httpx.MockTransport` จึงไม่ติดต่อ network หรือ model จริง ทดสอบกรณีหลักดังนี้:

- authenticated discovery และ lifecycle
- follow-up session
- output pagination
- key redaction
- persistence หลัง restart bridge
- duplicate suppression
- lost acceptance กับ durable idempotency
- block replay เมื่อไม่ durable หรือเก่าเกิน window
- run/session ownership
- exact approval และ stale approval rejection
- cached terminal output
- cooperative stop
- loopback URL guard
- redirect rejection
- model catalog/info, per-run model override และ schema migration

`tests/test_mcp.py` เปิด fake MCP server ผ่าน stdio แล้วตรวจ initialize, discovery 18 tools, diagnostics, annotations, model discovery, model-aware submit, usage tools, health, status, result และ foreign run rejection ส่วน `tests/test_codex.py` ตรวจ workspace/model/reasoning allowlist, symlink escape, sandbox mode, write approval, audit และ recovery marker

ชุดนี้เป็น contract/integration test ของ adapter ไม่ใช่ live end-to-end test ของ OpenAI Tunnel และไม่ใช่ visual/runtime test ของ WordPress, Elementor หรือ Hermes model จริง

## 16. Threat model และข้อจำกัด

สิ่งที่ bridge ป้องกัน:

- การส่ง Hermes key ไป host ภายนอกผ่าน URL config
- HTTP redirect ที่พา key ไปปลายทางอื่น
- proxy environment ที่อาจดักคำขอ
- MCP client อ่าน/หยุด run ที่ bridge ไม่ได้สร้าง
- การส่งงานซ้ำจาก retry เดิม
- การอนุมัติ request ที่เปลี่ยนระหว่างผู้ใช้ตรวจ
- key ที่สะท้อนกลับใน output ตรง ๆ

สิ่งที่ bridge ไม่ได้ป้องกัน:

- Hermes profile มี OS/tool permission กว้างเกินไป
- prompt injection ที่อยู่ในข้อมูลซึ่ง Hermes อ่าน
- secret ชนิดอื่นที่ไม่เท่ากับ `API_SERVER_KEY`
- ผลข้างเคียงของคำสั่งที่ Hermes ทำเสร็จแล้ว
- การหลับ/ปิด WSL หรือ tunnel process
- การทดสอบว่า WordPress frontend/editor แสดงผลถูกต้อง
- การเก็บ OpenAI Platform runtime key ของ tunnel-client หากผู้ใช้เลือกวิธีจัดเก็บที่ไม่ปลอดภัย

## 17. แนวทางแก้ไขหรือต่อยอด

การเปลี่ยนแปลงที่ควรรักษา invariant เดิม:

1. เปลี่ยน API contract ต้องแก้ `core.py`, FakeHermes และ MCP integration test พร้อมกัน
2. เพิ่ม MCP tool ต้องกำหนด annotation, ownership และ output redaction ให้ชัดก่อนเปิดใช้งาน
3. เปลี่ยน state schema ต้องมี migration version และทดสอบ persistence หลัง restart
4. เปลี่ยน retry/idempotency ต้องทดสอบ lost acceptance และ duplicate suppression เสมอ
5. เพิ่ม background polling ต้องไม่ทำให้มีการ submit ซ้ำหรือแย่ง session
6. เพิ่ม auth provider ต้องรักษา loopback restriction และไม่ log credential
7. หากทำ systemd user service ต้องแยก environment ของ tunnel-client ออกจาก Hermes key และจำกัด file permissions

ก่อน release ควรตรวจ:

- `bash -n install.sh bridge.sh tunnel.sh`
- unit/contract tests ทั้งหมด
- MCP stdio integration test
- dependency lock และ hash ของ package
- `./bridge.sh doctor` บนเครื่องเป้าหมาย
- live tunnel discovery และ health
- approval/cancel ใน environment จริง

## 18. สรุป state machine

```text
ไม่มีแถว
   │ submit ใหม่
   ▼
registered (ยังไม่มี run_id)
   │ POST /v1/runs สำเร็จ
   ▼
accepted + run_id
   │ status/result
   ├── running ───────────────┐
   ├── waiting_for_approval ──┼─ local approve/deny
   └── completed/failed/       │
       cancelled ◄─────────────┘
```

จุดสำคัญคือแถว SQLite ถูกสร้างก่อน upstream submission เพื่อให้ timeout หลัง upstream รับงานแล้วสามารถใช้ idempotent replay ที่ปลอดภัยได้ และ terminal result ถูก cache เพื่อให้การอ่านผลยังทำได้หลังข้อมูล upstream หมดอายุ
