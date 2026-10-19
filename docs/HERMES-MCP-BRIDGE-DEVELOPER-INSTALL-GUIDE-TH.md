# คู่มือพัฒนาและติดตั้ง Hermes MCP Bridge บน WSL2

เอกสารนี้อธิบาย bridge ที่เชื่อม ChatGPT ผ่าน Secure MCP Tunnel ไปยัง Hermes Agent ที่ทำงานอยู่ใน WSL2 โดยใช้ Hermes Runs API แบบ HTTP

รุ่นอ้างอิง: Hermes Agent v0.21.1, commit `8d79c2ff`  
Bridge: `hermes-mcp-bridge-v1.2.5` (signed and GitHub-verified)

สถานะ source ปัจจุบัน: released v1.2.5 (OpenCode execution opt-in); signed tag และ assets ผ่านการตรวจ ดู [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)

ปรับปรุงล่าสุด: 19 ตุลาคม 2026

## 1. ภาพรวมและขอบเขต

```text
ChatGPT
  │ MCP over Secure Tunnel
  ▼
tunnel-client
  │ stdio MCP
  ▼
bridge.sh → bridge.py/core.py
  │ HTTP + Bearer API_SERVER_KEY
  ▼
Hermes API 127.0.0.1:8642
  │
  ▼
Hermes Agent / configured tools / model
```

Bridge นี้ทำหน้าที่เป็น adapter และ state tracker:

- ตรวจ authentication และ capabilities ของ Hermes
- ส่งงานใหม่ผ่าน `POST /v1/runs`
- ติดตามสถานะและอ่านผลลัพธ์แบบแบ่งหน้า
- รองรับ `session_id` ที่ Hermes คืนกลับมาเพื่อทำงานต่อ
- ป้องกันการส่งงานซ้ำด้วย `request_id` และ Hermes `Idempotency-Key`
- เก็บ mapping และผลลัพธ์ terminal ใน SQLite ใต้ `state/`
- ยอมให้หยุดงานแบบ cooperative stop
- ไม่สร้าง filesystem sandbox เพิ่ม และไม่เปลี่ยน permission/tool policy ของ Hermes

เครื่องมือ MCP รวม 27 รายการ: Hermes 10 รายการ, Codex 6 รายการ, read-only operations 3 รายการ (`bridge_diagnostics`, `bridge_audit_recent`, `bridge_status`), work contexts 4 รายการ, Local Hands read-only 3 รายการ และ `bridge_version` 1 รายการ (เป็น 28 เมื่อเปิดใช้ OpenCode adapter แบบ opt-in และเป็น 33 เมื่อเปิด execution opt-in ตาม [OPENCODE-TH.md](OPENCODE-TH.md)) ตารางด้านล่างแสดงเฉพาะเครื่องมือ Hermes สัญญา discovery ฉบับเต็มอยู่ใน `TESTING.md` รายละเอียด policy และ approval ของ Codex อยู่ใน `CODEX-WSL2-TH.md`.

| Tool | หน้าที่ |
|---|---|
| `hermes_health` | ตรวจ API key, `/v1/models` และ capabilities โดยไม่เริ่ม agent turn |
| `hermes_model_info` | อ่านค่า model เริ่มต้นและนโยบาย override โดยไม่เปิดเผย secret |
| `hermes_models` | อ่านรายชื่อ model IDs ที่ Hermes API ประกาศ |
| `hermes_submit_task` | ส่ง prompt และคืน `run_id` |
| `hermes_task_status` | อ่านสถานะ, session และ approval ที่ค้าง |
| `hermes_task_result` | อ่าน output พร้อม `offset`/`max_chars` |
| `hermes_recent_tasks` | ดูรายการงานที่ bridge เคยลงทะเบียนไว้ 30 รายการ |
| `hermes_usage_summary` | สรุป token usage ที่ cache สำหรับ run ของ bridge |
| `hermes_usage_export` | ส่งออก usage per run โดยไม่มี prompt/output/secret |
| `hermes_cancel_task` | ขอหยุด run ที่ bridge เป็นผู้สร้าง |

การอนุมัติคำสั่งของ Hermes ยังต้องทำใน terminal WSL ด้วย `bridge.sh approve` หรือ `deny` ไม่มี MCP tool ที่อนุมัติแทนผู้ใช้

## 2. ความปลอดภัยของการเชื่อมต่อ

มี key สองชนิดและห้ามสลับกัน:

| Key | ตำแหน่ง/หน้าที่ |
|---|---|
| Hermes `API_SERVER_KEY` | อ่านจาก `/home/<user>/.hermes/.env` เพื่อเรียก Hermes API ใน WSL |
| OpenAI Platform runtime API key | ใช้โดย `tunnel-client` เพื่อเชื่อม Secure MCP Tunnel |

Bridge บังคับ API URL เป็น `http://127.0.0.1:PORT` เท่านั้น, ไม่ตาม redirect, ปิดการรับ proxy จาก environment และจำกัด HTTP response ต่อครั้งไม่เกิน 4,000,000 ไบต์

`state/runs.sqlite3` อาจเก็บ prompt และ output ที่มีข้อมูลส่วนตัว จึงตั้ง directory เป็น `700` และไฟล์เป็น `600` ห้ามนำโฟลเดอร์นี้เข้า Git หรือส่งต่อโดยไม่ตรวจข้อมูล

## 3. ข้อกำหนดก่อนติดตั้ง

- Windows 11 + WSL2 (Ubuntu ที่มี `python3`)
- Hermes Agent ติดตั้งและทำงานใน WSL เดียวกัน
- Hermes API Server เปิดที่ `127.0.0.1:8642` หรือ port ที่กำหนด
- Python 3.10 ขึ้นไป; ใช้ `python3` ได้ ไม่จำเป็นต้องมีคำสั่ง `python`
- `python3-venv`/`ensurepip` หรือ `uv`
- `unzip`, `curl`
- บัญชี OpenAI Platform ที่สร้างและใช้ Secure MCP Tunnel ได้
- official `tunnel-client` ใน `/home/<user>/.local/bin/`

หาก Hermes API ตั้งค่าและรันอยู่แล้ว ให้ข้ามไปตรวจ HTTP ในขั้น 4
ขั้น 1–3 เปลี่ยน configuration ของ Hermes จึงใช้เฉพาะเมื่อ operator อนุมัติให้ตั้งค่า API ของ instance นี้
หากคำสั่งใดล้มเหลว ให้หยุดและตรวจรูปแบบ config ของ Hermes รุ่นที่ติดตั้งก่อน

1. เปิด API Server:

   ```bash
   hermes config set API_SERVER_ENABLED true
   ```

2. จำกัด bind address เป็น loopback:

   ```bash
   hermes config set API_SERVER_HOST 127.0.0.1
   ```

3. กำหนดพอร์ตของ API Server:

   ```bash
   hermes config set API_SERVER_PORT 8642
   ```

4. เมื่อ Hermes API รันด้วย configuration นี้แล้ว ให้ตรวจ endpoint โดยไม่ส่ง key:

   ```bash
   curl --max-time 10 -sS -o /dev/null -w 'HTTP %{http_code}\n' \
     http://127.0.0.1:8642/v1/models
   ```

ถ้าไม่มี key จะได้ `401` ซึ่งเป็นพฤติกรรมที่ถูกต้อง ให้ตรวจด้วย key ที่ Hermes ใช้งานจริงโดยไม่แสดง key ในหน้าจอ

## 4. ติดตั้ง bridge

แตก ZIP ไปยัง path Linux ที่ไม่มีช่องว่าง เช่น:

1. เปลี่ยนไปที่ home directory:

   ```bash
   cd ~
   ```

2. ตรวจ checksum:

   ```bash
   sha256sum -c SHA256SUMS
   ```

   ผลต้องขึ้น `OK` ทุกบรรทัด หากไม่ผ่าน ให้ดาวน์โหลดไฟล์ใหม่ก่อนขั้นถัดไป
3. แตก ZIP:

   ```bash
   unzip hermes-mcp-bridge-v1.2.5.zip
   ```
4. เข้า directory ที่แตกได้:

   ```bash
   cd ~/hermes-mcp-bridge-v1.2.5
   ```
5. ติดตั้ง:

   ```bash
   bash install.sh
   ```

ให้รันด้วย user ปกติคนเดียวกับที่รัน Hermes และไม่ใช้ `sudo` ตัวติดตั้งจะ:

1. สร้าง `.venv` ด้วย `uv` หรือ `python3 -m venv`
2. ซ่อม `pip` ด้วย `ensurepip` หาก venv เดิมไม่มี pip
3. ติดตั้ง dependencies จาก `requirements.txt`
4. สร้าง `bridge-config.json` หากยังไม่มี
5. เรียก `./bridge.sh doctor`

ถ้าเจอ `.venv/bin/python: No module named pip`:

1. ซ่อม pip ใน venv เดิม:

   ```bash
   .venv/bin/python -m ensurepip --upgrade
   ```
2. ติดตั้งซ้ำ:

   ```bash
   bash install.sh
   ```

ถ้าไม่มี `ensurepip`:

1. อัปเดตรายการแพ็กเกจ หากคำสั่งล้มเหลว ให้แก้ error ก่อนติดตั้ง:

   ```bash
   sudo apt update
   ```

2. ติดตั้งแพ็กเกจ venv ของระบบ:

   ```bash
   sudo apt install -y python3.12-venv
   ```

3. อัปเกรด venv เดิม:

   ```bash
   python3 -m venv --upgrade .venv
   ```
4. ติดตั้งซ้ำ:

   ```bash
   bash install.sh
   ```

ไม่ต้องลบ `.venv` และไม่ต้องสร้าง alias `python`

ไฟล์ config ที่ตัวติดตั้งสร้าง:

```json
{
  "api_url": "http://127.0.0.1:8642",
  "hermes_env": "/home/<user>/.hermes/.env",
  "hermes_config": "/home/<user>/.hermes/config.yaml",
  "codex": { "allowed_workspaces": [] }
}
```

`core.py` อ่านเฉพาะ `API_SERVER_KEY` จาก `.env` ด้วย dotenv โดยไม่ source เป็น shell และไม่ export secret อื่น

## 5. ตรวจ local bridge

```bash
./bridge.sh doctor
```

ผลสำเร็จต้องมีลักษณะนี้:

```json
{
  "ok": true,
  "authentication": "verified",
  "api_url": "http://127.0.0.1:8642",
  "features": {
    "run_submission": true,
    "run_status": true,
    "run_stop": true,
    "run_approval_response": true
  }
}
```

ใน log อาจเห็นลำดับนี้เมื่อ `hermes_health` ทำงาน:

```text
GET /v1/models 401 Unauthorized
GET /v1/models 200 OK
GET /v1/capabilities 200 OK
```

401 แรกเป็นการตรวจว่าการเรียกโดยไม่มี key ถูกปฏิเสธ จากนั้น bridge เรียกซ้ำพร้อม key จึงได้ 200 ไม่ใช่ authentication failure

## 6. ตั้งค่า Secure MCP Tunnel

ใน OpenAI Platform ให้สร้าง Tunnel, associate กับ ChatGPT workspace และเก็บ `tunnel_id` จากนั้นติดตั้ง official `tunnel-client`:

1. เตรียมตำแหน่งติดตั้ง:

   ```bash
   mkdir -p ~/.local/bin
   ```

2. จำกัด permission ของ executable:

   ```bash
   chmod 700 ~/.local/bin/tunnel-client
   ```

3. เพิ่ม path ใน shell ปัจจุบัน:

   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

4. ตรวจว่า client ทำงานได้:

   ```bash
   tunnel-client help quickstart
   ```

ตรวจ architecture ด้วย `uname -m` และเลือกแพ็กเกจ Linux ที่ตรงกับ `x86_64` หรือ `aarch64` จาก release เดียวกัน

ก่อนเริ่มครั้งแรก ให้บันทึก OpenAI Platform runtime key (คนละตัวกับ Hermes `API_SERVER_KEY`) โดยไม่แสดงค่าในหน้าจอ:

1. เข้า directory ที่ติดตั้ง bridge:

   ```bash
   cd ~/hermes-mcp-bridge-v1.2.5
   ```

2. บันทึก key:

   ```bash
   bash tunnel.sh key-set
   ```

3. ตรวจว่า key file มีอยู่และ mode เป็น `600`; หากไม่ตรง ให้หยุดและแก้ก่อน init:

   ```bash
   bash tunnel.sh key-status
   ```

key ถูกเก็บใน `~/.config/hermes-mcp-bridge/openai-runtime-api-key` ด้วย mode `600`; environment variable `CONTROL_PLANE_API_KEY` ยังใช้แทนได้และมีลำดับสูงกว่า key file

ก่อนเริ่มครั้งแรก ให้ operator ยืนยันว่าไม่มี tunnel ของ profile `hermes-wsl` ทำงานอยู่
แทน `tunnel_YOUR_ID` ด้วย tunnel ID จริงจาก Platform
คำสั่งต่อไปนี้ต้องมี key จากขั้นก่อนหน้าจึงรันได้ แล้วสร้าง profile `hermes-wsl`, รัน `doctor` และเริ่ม `run` แบบ foreground หาก `doctor` ไม่ผ่าน ให้แก้ตามข้อความก่อนเชื่อม Plugin:

```bash
bash tunnel.sh init tunnel_YOUR_ID
```

ใช้ `--force` เฉพาะเมื่อตรวจเป้าหมายของ profile เดิมแล้วยืนยันว่าต้องการแทน เช่น เมื่อเปลี่ยน directory หรือเวอร์ชันของ bridge:

```bash
bash tunnel.sh init tunnel_YOUR_ID --force
```

เลือก init แบบไม่ใส่ `--force` หรือแบบ `--force` เพียงกรณีเดียว ไม่รันทั้งสองตามลำดับ
เมื่อ init เชื่อมต่อสำเร็จ terminal นั้นจะค้างรัน tunnel อยู่
ให้คง terminal เดิมไว้ แล้วเปิด terminal อีกหน้าหนึ่งใน directory ของ instance เดียวกันเพื่อตรวจ doctor:

```bash
cd ~/hermes-mcp-bridge-v1.2.5
```

ตรวจ profile ด้วย wrapper:

```bash
bash tunnel.sh status
```

คำสั่ง `tunnel-client doctor --profile hermes-wsl` ที่รันตรง ๆ จะไม่โหลด key file ของโครงการ และอาจรายงานว่า `CONTROL_PLANE_API_KEY` ไม่ได้ตั้งแม้ `key-status` จะผ่าน. `tunnel.sh status`/`run` โหลด key file อย่างปลอดภัยก่อนเรียก doctor; อย่าแก้ด้วยการพิมพ์ key ลง command line.

`tunnel.sh` เลือก production profile `hermes-wsl` ไว้ตายตัว อย่าแก้ `tunnel.sh` เพื่อเลือก profile อื่น; งาน Dev route แยกให้ทำตาม [OPENCODE-TH.md](OPENCODE-TH.md) (profile `hermes-wsl-dev`, health port 8081)

เริ่มครั้งถัดไป ให้รันจาก directory ที่ติดตั้ง bridge เมื่อ tunnel เดิมหยุดแล้วเท่านั้น:

```bash
bash tunnel.sh run
```

ไม่ต้องพิมพ์ key ซ้ำเมื่อใช้ `key-set` แล้ว ห้ามใส่ key ตรง ๆ ใน command history, source repository หรือ systemd unit

Terminal ที่รัน `tunnel.sh run` ต้องเปิดค้างไว้ตลอดเวลาที่ ChatGPT ใช้ plugin เชื่อมต่ออยู่ การปิด terminal จะตัด MCP connection แต่ไม่รับรองว่าจะหยุด Hermes run ที่เริ่มไปแล้ว หากต้องการหยุดงานให้เรียก MCP tool `hermes_cancel_task` แล้วตรวจ status

หาก WSL เปิด systemd user service ได้ ให้หยุด process foreground ที่รัน `tunnel.sh run`/`init` อยู่ก่อน (กด `Ctrl+C` ใน terminal นั้น) เพื่อไม่รัน tunnel สอง instance บน profile เดียว แล้วรัน tunnel แบบ background:

1. สร้างและเปิดใช้ systemd user unit (ต้องมี key แล้ว):

   ```bash
   bash tunnel.sh service-install
   ```

2. เริ่ม service:

   ```bash
   bash tunnel.sh service-start
   ```

3. ตรวจว่า service ทำงาน:

   ```bash
   bash tunnel.sh service-status
   ```

ดู log ด้วย `bash tunnel.sh service-logs`; หยุดด้วย `service-stop`; และลบ unit โดยเก็บ key ไว้ด้วย `service-uninstall`

## 7. เพิ่ม Plugin ใน ChatGPT

เปิด Developer mode แล้วไปที่ Plugins → `+` → Connection → Tunnel:

1. Name: `Hermes Local Bridge`
2. Description: `ส่งงานให้ Hermes บน WSL2 ตรวจสถานะ อ่านผล และขอหยุดงาน`
3. เลือก Tunnel ที่สร้าง หรือระบุ `tunnel_id`
4. Authentication: **No authentication**
5. สร้าง connection และตรวจว่าพบ MCP tools ตาม canonical contract ใน `TESTING.md` — 27 รายการ (Hermes 10 + Codex 6 + operations 3 + contexts 4 + Hands 3 + `bridge_version`); 28 รายการเมื่อเปิดใช้ OpenCode adapter แบบ opt-in และ 33 รายการเมื่อเปิด execution opt-in ตาม [OPENCODE-TH.md](OPENCODE-TH.md)

MCP target ของ profile นี้เป็น stdio และไม่มี OAuth discovery endpoint. OpenAI Platform runtime API key เป็น credential ของ `tunnel-client` เท่านั้น จึงไม่ใช่เหตุให้ต้องเลือก OAuth ในหน้า Plugin. ห้ามนำ hosted tunnel URL ไปวางใน Server URL; คง Connection เป็น **Tunnel** เสมอ.

ถ้า plugin ถูกเพิ่มแล้วแต่เครื่องมือไม่ปรากฏในแชทเดิม ให้เปิดแชทใหม่และเลือก plugin อีกครั้ง

## 8. ลำดับการทดสอบจาก ChatGPT

เริ่มจาก health:

> ใช้ Hermes Local Bridge เรียก `hermes_health` แล้วรายงานผล

ทดสอบ agent turn ที่ไม่ใช้ tool:

> ให้ Hermes ตอบเพียง `HERMES_BRIDGE_OK` โดยไม่เรียกเครื่องมือ แล้วติดตามจนงานจบและอ่านผลกลับมา

ทดสอบอ่านข้อมูลแบบไม่แก้ไข:

> ให้ Hermes ตรวจเวอร์ชัน Python และ Git ใน WSL2 ห้ามติดตั้งหรือแก้ไขไฟล์ แล้วส่งผลกลับมา

การส่งงานต้องใช้ `request_id` ใหม่ต่อ logical task หาก retry งานเดิมให้ใช้ `request_id`, prompt และ `session_id` เดิมทุกครั้ง ตัวกลางจะคืน `run_id` เดิมเมื่อพบงานที่ลงทะเบียนไว้แล้ว

ลำดับที่ถูกต้องคือ `hermes_submit_task` → `hermes_task_status` → `hermes_task_result` และงานต่อเนื่องใช้เฉพาะ `session_id` ที่ bridge คืนกลับมา

สำหรับงานใหม่ สามารถเรียก `hermes_model_info`/`hermes_models` ก่อน แล้วส่ง `model`, `provider` และ `model_options` (`reasoning_effort` หรือ `service_tier`) ใน `hermes_submit_task` ได้ งานต่อจาก `session_id` ต้องไม่ส่ง fields เหล่านี้ เพื่อให้ model ของ session เดิมคงที่

## 9. Approval และการหยุดงาน

ถ้า status เป็น `waiting_for_approval` ให้ตรวจรายละเอียดใน ChatGPT แล้วเปิด terminal:

```bash
./bridge.sh status run_ID
./bridge.sh approve run_ID
# หรือ
./bridge.sh deny run_ID
```

ต้องพิมพ์ `APPROVE` หรือ `DENY` ใน terminal เพื่อยืนยันเฉพาะ request เดียว ระบบจะไม่ใช้ `resolve_all` และไม่ bypass approval

การหยุดเป็น cooperative stop:

ใน ChatGPT ให้เรียก `hermes_cancel_task` ด้วย `run_id` แล้วเรียก `hermes_task_status` เพื่อตรวจจนเป็น `cancelled`, `completed` หรือ `failed` ปัจจุบัน local CLI ของ bridge ไม่มีคำสั่ง `stop` แยก

ผลจากคำสั่งที่ Hermes ทำไปแล้วจะไม่ถูกย้อนกลับ

## 10. แนวทางพัฒนาและทดสอบ bridge

ไฟล์สำคัญ:

| ไฟล์ | หน้าที่ |
|---|---|
| `core.py` | HTTP client, authentication, SQLite state, idempotency, pagination, ownership และ approval |
| `codex_core.py` | Codex policy, job runner และ durable worker |
| `opencode_core.py` | OpenCode health adapter (disabled by default) |
| `stdio_guard.py` | legacy stdio discovery guard |
| `bridge.py` | MCP stdio server และ local operator CLI |
| `bridge.sh` | เรียก Python ใน `.venv` |
| `install.sh` | สร้าง environment และติดตั้ง dependencies |
| `tunnel.sh` | init/doctor/run Tunnel, runtime-key store และ systemd user service |
| `requirements.txt` | dependency ranges |
| `requirements-lock.txt` | versions ที่ทดสอบแล้ว |
| `docs/TESTING.md` | test contract และข้อจำกัดของการทดสอบ |

หลักการพัฒนา:

- รักษา loopback-only policy ของ Hermes API
- ห้าม log key, prompt ที่มี secret หรือ raw response ที่อาจมี credential
- ทุก run ต้องมี ownership row ใน SQLite ก่อน status/result/stop
- ห้ามอนุมัติ run ที่ bridge ไม่ได้สร้าง
- retry หลัง response หายทำได้เมื่อ Hermes ประกาศ durable idempotency และยังอยู่ใน safe replay window
- เปลี่ยน schema/API ต้องเพิ่ม fake-server test และ MCP stdio integration test

ชุดทดสอบครอบคลุม Hermes lifecycle/recovery/model/usage เดิม, Codex workspace/model/reasoning allowlist, symlink, sandbox, write approval, audit/recovery และ MCP SDK stdio integration ที่ค้นพบ 27 tools

การทดสอบดังกล่าวเป็น contract test กับ Hermes จำลอง ไม่ใช่การรัน live model หรือการยืนยัน UI จริง

## 11. Troubleshooting

| อาการ | ตรวจสอบ |
|---|---|
| `401` ทุกคำขอ | ตรวจ path ใน `bridge-config.json`, `API_SERVER_KEY` ใน Hermes `.env`, และ restart bridge หลังเปลี่ยน key |
| `401` หนึ่งครั้ง ตามด้วย `200`, `200` | ปกติ เป็น health authentication probe |
| `Cannot reach Hermes API` | Hermes API server ยังไม่รัน, port ผิด หรืออยู่คนละ WSL |
| `No module named pip` | เรียก `ensurepip` หรือ install `python3.12-venv` ตามหัวข้อ 4 |
| Tunnel ถาม/หา key ไม่พบ | รัน `bash tunnel.sh key-set`; ตรวจด้วย `key-status` (ต้องเป็น mode 600) หรือ set `CONTROL_PLANE_API_KEY` เฉพาะ shell นั้น |
| direct `tunnel-client doctor` แจ้งว่า `CONTROL_PLANE_API_KEY` ไม่ได้ตั้ง | key file อาจยังปกติ; ใช้ `bash tunnel.sh status` ซึ่งโหลด key file ก่อนเรียก doctor |
| `Error fetching OAuth configuration` / `does not implement OAuth` | เลือก Connection: Tunnel และ Authentication: No authentication; bridge นี้ไม่มี OAuth discovery และไม่ควรใช้ hosted tunnel URL เป็น Server URL |
| `Link not found`, `Invalid MCP request metadata` หรือ `unsupported channel "harpoon"` | ยืนยัน `bash tunnel.sh status` เป็น `RESULT ok`, ให้ `bash tunnel.sh run` ทำงาน แล้วสร้าง developer-mode connection ใหม่ด้วย Tunnel + No authentication. ถ้า `harpoon` ซ้ำบน client รุ่นล่าสุด ให้ส่ง log ที่ redacted พร้อม tunnel ID/version ให้ OpenAI Support; ห้ามแก้ bridge เพื่อรับ channel ดังกล่าว |
| `service-install` ใช้ไม่ได้ | WSL session นี้ไม่มี systemd user manager; ใช้ `tunnel.sh run` ใน terminal แทน หรือเปิด systemd ใน WSL ตามนโยบายเครื่อง |
| Plugin discovery ล้มเหลว | ตรวจ `tunnel-client run`, `./bridge.sh doctor`, tunnel association และสิทธิ์ Tunnel Read/Use |
| ไม่พบ tools ในแชท | เปิดแชทใหม่และเลือก `Hermes Local Bridge` ใหม่ |
| output ยาว | เรียก `hermes_task_result` ต่อด้วย `offset` ที่คืนใน `next_offset` |
| approval ค้าง | ใช้ `./bridge.sh status`, ตรวจ request แล้ว approve/deny ใน terminal |
| ปิด tunnel แล้วงานไม่หยุด | tunnel เป็นเพียงช่องทางเชื่อมต่อ ต้องเรียก `hermes_cancel_task` และ poll status แยก |

## 12. Acceptance checklist

ก่อนใช้งานจริงควรผ่านทุกข้อ:

- Hermes API ตอบ `200` เมื่อใช้ key และปฏิเสธ request ที่ไม่มี key
- `./bridge.sh doctor` ได้ `ok: true`
- `tunnel-client doctor` ผ่านและ `tunnel.sh run` คง connection ได้
- ChatGPT ค้นพบเครื่องมือ MCP ครบตาม canonical contract (27 รายการ; 28 เมื่อเปิด OpenCode adapter; 33 เมื่อเปิด execution opt-in) รวม Hermes 10, Codex 6, `bridge_diagnostics`, `bridge_audit_recent`, `bridge_status`, contexts 4, Hands read-only 3 และ `bridge_version`
- health, response-only task และ read-only task ผ่าน
- `codex_health` แสดง workspace policy ที่ตั้งใจ; หากเปิด model override ให้ทดสอบ model ID/effort ที่อยู่ใน allowlist ก่อนใช้งานจริง
- retry ด้วย request เดิมไม่สร้าง run ซ้ำ
- result pagination อ่าน output ได้ครบ
- approval ถูกตรวจและตัดสินใน local terminal เท่านั้น
- cancel แล้ว status จบเป็น `cancelled`, `completed` หรือ `failed`
- backup/permission ของ `bridge-config.json` และ `state/` ถูกจำกัดเป็น user เดียว
- ไม่พบ key ใน shell history, log, Git หรือ output ที่ส่งกลับ ChatGPT
