# Hermes MCP Bridge v1.0.1 — Hermes + Codex/WSL2 / ChatGPT

[![Tests](https://github.com/sc28249782/hermes-mcp-bridge/actions/workflows/tests.yml/badge.svg)](https://github.com/sc28249782/hermes-mcp-bridge/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../LICENSE)

Repository: https://github.com/sc28249782/hermes-mcp-bridge  
จุดเริ่มต้นของโครงการ: [Project origin](PROJECT-ORIGIN.md)

จัดทำสำหรับ Hermes Agent v0.21.1, commit `8d79c2ff` ที่ผู้ใช้ยืนยัน
วันที่ปรับปรุง: 21 กันยายน 2026 — signed tag `v1.0.1` ได้รับการยืนยันโดย GitHub และ release archive ตรวจ SHA-256 ผ่าน

ตัวกลางนี้ทำให้ ChatGPT ส่งงานให้ Hermes ที่รันอยู่บนเครื่องคุณ แล้วตรวจสถานะ อ่านผล และขอหยุดงานได้
ใช้ Runs API เดียวกับที่ `hermes peer run/status/stop` เรียก แต่เรียก HTTP โดยตรง
งานใหม่เริ่ม session ใหม่ ไม่ใช้ canonical “Bot Chat” ร่วมกับ peer อื่น
งานต่อเนื่องระบุ session_id ที่ตัวกลางเคยคืนให้ได้

เส้นทาง: ChatGPT → Secure MCP Tunnel → bridge.sh (stdio MCP) → Hermes API `127.0.0.1:8642`

## สถานะก่อนติดตั้ง

- ผู้ใช้ทดสอบ `/v1/models` แล้ว: ไม่มี key ได้ 401; key ถูกต้องได้ 200
- มีเมนู Developer mode และ Connection → Tunnel
- ยังต้องสร้าง tunnel ใน OpenAI Platform, ติดตั้ง tunnel-client และเชื่อม Plugin
- ผ่าน regression tests 48 รายการ; v1.0.0 full acceptance ผ่าน Secure MCP Tunnel สำหรับ Hermes, Codex, model policy, local write approval และ cancellation และ v1.0.1 read-only live acceptance ผ่านบน WSL2

อัปเกรดจาก bridge รุ่นก่อนใช้ [UPGRADE-TH.md](UPGRADE-TH.md) ก่อนเริ่ม tunnel รุ่นใหม่ โดยเฉพาะหากต้องการเก็บ session/state เดิม

## 1. ติดตั้งตัวกลางใน WSL2

ดาวน์โหลด ZIP แล้วแตกในโฟลเดอร์ Linux ของผู้ใช้ `somchaip` เช่น:

```text
/home/somchaip/hermes-mcp-bridge-v1.0.1/
```

ถ้าดาวน์โหลดผ่าน Windows สามารถเปิดโฟลเดอร์บ้าน WSL ใน File Explorer ด้วย `explorer.exe ~`
แล้วคัดลอก ZIP เข้าไป จากนั้นแตกไฟล์ใน WSL:

```bash
cd /home/somchaip
sha256sum -c SHA256SUMS
unzip hermes-mcp-bridge-v1.0.1.zip
cd /home/somchaip/hermes-mcp-bridge-v1.0.1
bash install.sh
```

รันด้วยผู้ใช้ปกติ ไม่ใช้ sudo ตัวติดตั้ง:

- สร้าง Python virtual environment `.venv` สำหรับ bridge โดยเฉพาะ
- ติดตั้ง MCP SDK, HTTP client และตัวอ่าน `.env`
- สร้าง `bridge-config.json` ระบุ URL และตำแหน่ง Hermes `.env`
- อ่านเฉพาะ `API_SERVER_KEY` จาก `.env`; ไม่แก้ Hermes config หรือ secret เดิม
- ตรวจ authentication และ capabilities โดยไม่ส่งงานให้โมเดล

ถ้าไม่มีทั้ง `uv` และ Python venv ให้ติดตั้งแพ็กเกจ `python3-venv` ตาม Ubuntu ที่ใช้ แล้วรันตัวติดตั้งอีกครั้ง
ต้องใช้ Python >= 3.10; แนะนำ Python 3.11/3.12

**Installer repair: `.venv/bin/python: No module named pip`**

หาก `.venv` มี Python แต่ยังไม่มี pip ให้ซ่อม environment เดิม:

```bash
cd /home/somchaip/hermes-mcp-bridge-v1.0.1
.venv/bin/python -m ensurepip --upgrade
bash install.sh
```

หากไม่มี `ensurepip` ด้วย และใช้ Ubuntu/Python 3.12:

```bash
sudo apt install python3.12-venv
python3 -m venv --upgrade .venv
bash install.sh
```

ตัวติดตั้งฉบับแก้ไขตรวจและ bootstrap pip ก่อนใช้ pip install แล้ว ส่วนเส้นทาง `uv pip install` ไม่ต้องมี pip อยู่ใน venv
ไม่ต้องลบโฟลเดอร์โครงการหรือสร้าง alias `python`

ตัวอย่าง config ที่จะสร้าง:

```json
{
  "api_url": "http://127.0.0.1:8642",
  "hermes_env": "/home/somchaip/.hermes/.env",
  "hermes_config": "/home/somchaip/.hermes/config.yaml",
  "codex": {
    "allowed_workspaces": []
  }
}
```

ตัวกลางรุ่นนี้รับเฉพาะ API URL แบบ `http://127.0.0.1:PORT` ไม่มี path เพื่อใช้กับ default profile ภายใน WSL เท่านั้น
อ่าน secret โดยไม่ทำ shell expansion หาก key ใช้ `${VARIABLE}` ให้กำหนดเป็นค่าจริงใน `.env` ก่อน
เมื่อเปลี่ยน key ให้เริ่ม tunnel/bridge ใหม่

ตรวจได้อีกครั้ง:

```bash
./bridge.sh doctor
```

ผลต้องมี `"ok": true` และ `"authentication": "verified"`
หาก `/v1/capabilities` ขาด `run_submission`, `run_status` หรือ `run_stop` ตัวตรวจจะหยุดพร้อมระบุชื่อที่ขาด

## 2. สร้าง Secure MCP Tunnel ในบัญชี OpenAI

เปิด [เอกสาร Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
แล้วกดลิงก์ **Platform tunnel settings** ในหัวข้อ Before you start

1. เลือก Platform organization ของบัญชีคุณ
2. สร้าง Tunnel ตั้งชื่อ เช่น `Hermes WSL`
3. เชื่อม/associate กับ ChatGPT workspace ที่คุณจะเพิ่ม Plugin
4. เก็บ `tunnel_id` ที่ระบบสร้างให้
5. เตรียม runtime API key ของ OpenAI Platform สำหรับ tunnel-client

สิทธิ์สร้าง Tunnel ต้องมี Tunnels Read + Manage และสิทธิ์รัน/เลือก Tunnel ต้องมี Read + Use
Developer mode เป็นอีกสิทธิ์หนึ่ง การเห็นเมนู Tunnel อย่างเดียวไม่ยืนยันว่า Platform ให้สิทธิ์ครบ
หากไม่มีสิทธิ์หรือไม่มีปุ่มสร้าง ให้ส่งเฉพาะข้อความผิดพลาด/ภาพหน้าจอที่ไม่แสดง key กลับมาวิเคราะห์

**API key สองชนิดต่างหน้าที่กัน**

| Key | ใช้ที่ใด |
|---|---|
| Hermes `API_SERVER_KEY` | bridge อ่านจาก Hermes `.env` เพื่อเรียก API ใน WSL |
| OpenAI Platform runtime API key | tunnel-client ใช้เชื่อมกับ OpenAI |

ไม่ต้องนำ Hermes key ไปกรอกใน ChatGPT Plugin และไม่ต้องส่ง key ทั้งสองชนิดในแชท
การมี ChatGPT subscription ไม่ได้ยืนยันค่าใช้จ่ายหรือสิทธิ์ Platform Tunnel; ตรวจในบัญชี Platform
Hermes ยังคงใช้ provider/model และการคิดค่าใช้จ่ายตามที่คุณตั้งไว้

## 3. ติดตั้ง official tunnel-client ภายใน WSL

ใช้ลิงก์ดาวน์โหลดใน Platform tunnel settings หรือ [OpenAI tunnel-client releases ล่าสุด](https://github.com/openai/tunnel-client/releases/latest)
ตรวจสถาปัตยกรรมด้วย `uname -m`:

- `x86_64`: เลือกแพ็กเกจ `tunnel-client-<version>-linux-amd64.zip`
- `aarch64`: เลือก `tunnel-client-<version>-linux-arm64.zip`

เลือก **tunnel-client** ปกติ ไม่ใช่ runtime, source, cloudflared หรือแพ็กเกจ Windows
แตกแพ็กเกจแล้ววาง executable `tunnel-client` ใน `/home/somchaip/.local/bin/`
รักษาไฟล์ประกอบตามคำแนะนำใน release นั้นถ้ามี ตรวจ checksum กับ `SHA256SUMS` ของ release เดียวกัน

```bash
mkdir -p /home/somchaip/.local/bin
chmod 700 /home/somchaip/.local/bin/tunnel-client
export PATH="$HOME/.local/bin:$PATH"
tunnel-client help quickstart
```

ไฟล์ tunnel-client ไม่ได้รวมอยู่ใน ZIP นี้ ขั้นตอน init/doctor/run ด้านล่างอิงคำสั่งในเอกสาร OpenAI ที่ตรวจวันที่จัดทำ
หาก CLI ที่ดาวน์โหลดเปลี่ยนรูปแบบ ให้ดู `tunnel-client help quickstart` และส่ง error มาตรวจ ไม่ต้องเดาชื่อ flag

## 4. ตั้งค่าและรัน Tunnel

คง Hermes gateway ให้รันอยู่ แล้วเปิด terminal อีกหน้าหนึ่ง:

```bash
cd /home/somchaip/hermes-mcp-bridge-v1.0.1
bash tunnel.sh init tunnel_แทนด้วยIDจริง [--force]
```

ก่อนเริ่ม Tunnel ให้บันทึก OpenAI Platform runtime key หนึ่งครั้ง:

```bash
bash tunnel.sh key-set
bash tunnel.sh key-status
```

สคริปต์เก็บ key ที่ `~/.config/hermes-mcp-bridge/openai-runtime-api-key` ด้วย mode `600` และอ่านค่านี้อัตโนมัติเมื่อเริ่มใหม่ ไม่ใส่ key ลง command history หรือ systemd unit file

ตรวจ profile และ key ผ่าน wrapper ของโครงการก่อนเริ่ม/หลังแก้ปัญหา:

```bash
bash tunnel.sh status
```

อย่าใช้ผล `tunnel-client doctor --profile hermes-wsl` ที่รันตรง ๆ ตัดสินว่า key file ใช้ไม่ได้: profile อ้าง `env:CONTROL_PLANE_API_KEY` ขณะที่ `tunnel.sh` เป็นผู้โหลด key file เข้า environment ให้ `doctor` และ `run` เอง. ถ้าต้องเรียก `tunnel-client` โดยตรง ต้อง export runtime key ใน shell นั้นก่อน และห้ามวาง key ลง chat, command history หรือ log.

สคริปต์จะสร้าง profile `hermes-wsl`, ตรวจ `doctor` และเริ่ม `run`
Tunnel จะเรียก `bridge.sh` ผ่าน stdio เอง ไม่ต้องเปิด bridge เป็น HTTP server และไม่ต้องรัน `bridge.sh serve` แยก
อย่าใช้ `hermes mcp serve` แทน เพราะชุดเครื่องมือ messaging ไม่ใช่ Runs bridge ที่เราสร้าง

หาก profile `hermes-wsl` มีอยู่ก่อนแล้วสำหรับงานอื่น ให้เลือกชื่อใหม่ใน `tunnel.sh` ก่อน init เพื่อไม่ทับการตั้งค่าเดิม
การเริ่มใหม่ในครั้งต่อไปใช้:

```bash
cd /home/somchaip/hermes-mcp-bridge-v1.0.1
bash tunnel.sh run
```

เปิด terminal ค้างไว้ในช่วงทดสอบ หากต้องการให้เริ่มแบบ background ใน WSL ที่เปิด systemd แล้ว:

```bash
bash tunnel.sh service-install
bash tunnel.sh service-start
bash tunnel.sh service-status
```

ดู log ด้วย `bash tunnel.sh service-logs` และหยุดด้วย `bash tunnel.sh service-stop` การหยุด Tunnel ไม่ได้หยุด Hermes run ที่เริ่มไปแล้ว
ไม่ต้องเปลี่ยน WSL networking mode หรือ forward พอร์ต 8642 ที่เราเตอร์สำหรับการเชื่อมออกนี้

## 5. เพิ่ม Plugin ใน ChatGPT

ตาม [Connect and test your plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt):

1. เปิด Developer mode
2. Plugins → ปุ่มบวก
3. Name: `Hermes Local Bridge`
4. Description: `ส่งงานให้ Hermes บน WSL2 ตรวจสถานะ อ่านผล และขอหยุดงาน`
5. Connection: **Tunnel**
6. เลือก Tunnel ที่สร้าง หรือใส่ `tunnel_id`
7. Authentication: **No authentication**
8. สร้างการเชื่อมต่อและตรวจรายชื่อเครื่องมือ

bridge นี้เป็น stdio MCP server และไม่ประกาศ OAuth metadata; runtime API key ใช้ระหว่าง `tunnel-client` กับ OpenAI control plane ไม่ใช่ OAuth ของ MCP server. ห้ามเปลี่ยนไปใช้ Server URL หรือวาง OpenAI-hosted tunnel URL ลงในช่อง Server URL เพื่อแก้ปัญหา connection; ให้เลือก **Tunnel** และระบุ tunnel ที่สร้างใน Platform เสมอ.

ควรค้นพบ 19 เครื่องมือ (Hermes 10 + Codex 6 + operations 3):

| เครื่องมือ | หน้าที่ |
|---|---|
| `hermes_health` | ตรวจ API/auth/capabilities โดยไม่เรียกโมเดล |
| `bridge_diagnostics` | ตรวจ Hermes/Codex, permission ของ state และ audit config โดยไม่แสดง secret |
| `bridge_status` | heartbeat แบบ local-only; ไม่เรียก Hermes API หรือ Codex CLI |
| `bridge_audit_recent` | อ่าน lifecycle audit ล่าสุดแบบ redacted |
| `hermes_model_info` | อ่าน default model metadata และนโยบาย model override โดยไม่เปิดเผย secret |
| `hermes_models` | แสดง model IDs ที่ Hermes API ประกาศ |
| `hermes_submit_task` | ส่งโจทย์; คืน run_id โดยไม่รอจบ |
| `hermes_task_status` | อ่านสถานะและ pending approval |
| `hermes_task_result` | อ่าน output/usage แบบแบ่งหน้า |
| `hermes_recent_tasks` | กู้รายการ request/run IDs ของ bridge หลัง reconnect |
| `hermes_usage_summary` | รวม token usage เฉพาะ run ของ bridge ตาม model โดยไม่ประมาณราคา |
| `hermes_usage_export` | ส่งออก JSON usage ต่อ run โดยไม่มี prompt, output หรือ secret |
| `hermes_cancel_task` | ขอหยุดเฉพาะ run ที่ bridge นี้สร้าง |
| `codex_health` | ตรวจ Codex CLI, sandbox modes, workspace และ model/reasoning allowlist |
| `codex_submit_task` | เริ่ม read-only หรือสร้าง write job ที่รอ local approval; เลือก model/reasoning ได้เมื่อ policy อนุญาต |
| `codex_task_status` | อ่านสถานะ job ของ Codex |
| `codex_task_result` | อ่าน JSONL output แบบแบ่งหน้า |
| `codex_cancel_task` | หยุดงานที่กำลังรันหรือปฏิเสธ write job ที่ยังรออนุมัติ |
| `codex_recent_tasks` | แสดง Codex jobs ล่าสุด 30 รายการ |

เปิดแชทใหม่แล้วเลือก Plugin นี้ ถ้าเครื่องมือไม่ปรากฏในแชทเดิม ให้แนบ Plugin หรือเปิดแชทใหม่ตาม UI
การเพิ่ม Plugin ในบัญชีไม่ได้ยืนยันว่าบทสนทนาเดิมเห็นเครื่องมือแล้ว

การตั้งค่า Codex/WSL2, model/reasoning policy และ local write approval ดู `CODEX-WSL2-TH.md`

## เลือก model ต่อ task

เรียก `hermes_model_info` และ `hermes_models` ก่อนเลือก model จากนั้นส่ง `model`, `provider` และ `model_options` พร้อม `hermes_submit_task` ได้เฉพาะงานใหม่ ตัวอย่าง `model_options` ที่รองรับในรุ่นนี้คือ `reasoning_effort` และ `service_tier`

Hermes bridge ไม่ทำ allowlist ของ provider/model/reasoning เพื่อรองรับ provider ที่ Hermes มีได้หลากหลาย; Hermes API/profile เป็นผู้ตรวจว่าค่าที่ส่งใช้ได้จริง. ต่างจาก Codex ที่กำหนด allowlist ต่อ workspace เพื่อควบคุมการเรียก Codex CLI.

งานต่อจาก `session_id` ต้องไม่ส่ง model fields เพื่อให้คง model ของ session เดิม และค่า model/provider/options ถูกนำไปรวมใน request fingerprint: retry ด้วย `request_id` เดิมแต่เลือก model ต่างกันจะถูกปฏิเสธ

รุ่นนี้ไม่เปิด MCP tool สำหรับเปลี่ยน `model.default` ถาวร ใช้ `hermes config set model.default ...` และ `hermes config set model.provider ...` ใน WSL เมื่อผู้ดูแลต้องการเปลี่ยน global default

## 6. ทดสอบจาก ChatGPT

เริ่มด้วย:

> ใช้ Hermes Local Bridge เรียก hermes_health แล้วรายงานว่าพร้อมหรือไม่

จากนั้นทดสอบ agent turn ที่ไม่ใช้เครื่องมือ:

> ให้ Hermes ตอบเพียง HERMES_BRIDGE_OK โดยไม่เรียกเครื่องมือ แล้วติดตามจนงานจบและอ่านผลกลับมา

การส่งคำสั่งว่าไม่ใช้เครื่องมือเป็นข้อกำหนดใน prompt ไม่ใช่ sandbox; สำหรับการพิสูจน์แบบไม่มี tool permission ต้องจำกัด toolset ฝั่ง Hermes แยก

เมื่อสำเร็จจึงทดสอบงานอ่านข้อมูลที่ระบุชัด เช่น:

> ให้ Hermes ตรวจเวอร์ชัน Python และ Git ใน WSL2 ห้ามติดตั้งหรือแก้ไขไฟล์ แล้วส่งผลกลับมา

bridge ใช้ permissions/toolsets ของ API profile เดิม ไม่ได้แยก filesystem หรือจำกัดโฟลเดอร์ให้อัตโนมัติ
อย่าตีความข้อความ “ทำงานเฉพาะโฟลเดอร์นี้” ว่าเป็น OS sandbox

## การอนุมัติคำสั่ง

bridge ไม่เปลี่ยน approval policy ของ Hermes และไม่ตั้ง `--yolo`, `--accept-hooks` หรือ `--oneshot`
ถ้านโยบาย Hermes อนุญาตคำสั่งอยู่แล้ว Hermes อาจดำเนินการได้โดยไม่ถาม
ถ้าสถานะเป็น `waiting_for_approval` ให้ดูรายละเอียดใน ChatGPT หรือใน WSL:

```bash
./bridge.sh status run_แทนด้วยIDจริง
./bridge.sh approve run_แทนด้วยIDจริง
```

helper แสดง approval จาก API ให้ตรวจ แล้วต้องพิมพ์ `APPROVE` ใน terminal ด้วยตนเอง
อนุญาตเฉพาะ request_id นั้นแบบครั้งเดียว ไม่มี session/always/resolve-all
helper ตรวจ request_id ซ้ำหลังตัดสินใจเพื่อไม่อนุมัติรายการที่เปลี่ยนระหว่างดู
หากต้องการปฏิเสธ:

```bash
./bridge.sh deny run_แทนด้วยIDจริง
```

ไม่มี MCP tool สำหรับอนุมัติแทนผู้ใช้ การยืนยัน tool call ฝั่ง ChatGPT กับ approval รายคำสั่งฝั่ง Hermes เป็นคนละชั้น

ข้อจำกัดของ API profile ที่ยืนยันใน v1.1.0 POC: แม้ `hermes_health` ประกาศ `run_approval_response` แต่ Hermes Runs API ที่ติดตั้งอาจเป็น unattended context และไม่สร้าง interactive approval event จาก `approvals.mode: manual`. คำสั่ง local `approve`/`deny` จะทำงานได้เฉพาะเมื่อ `hermes_task_status` คืน exact pending approval จริงเท่านั้น; ห้ามถือว่า endpoint ที่ประกาศอยู่เพียงอย่างเดียวเป็นหลักฐานว่า API approval ใช้งานได้. ดู `LIVE-ACCEPTANCE-TH.md` และ `ROADMAP.md`.

## การส่งซ้ำ ผลลัพธ์ และการหยุด

- แต่ละงานต้องมี `request_id` ใหม่ เช่น UUID; retry งานเดิมต้องใช้ request_id และ prompt/session_id เดิม
- bridge บันทึก fingerprint และ run_id ใน `state/runs.sqlite3` ก่อน/หลังส่งงาน
- ถ้าเคยได้ run_id แล้ว จะคืน ID เดิมโดยไม่ส่งใหม่
- ถ้า response หายจนไม่รู้ว่า Hermes รับงานแล้วหรือยัง จะ replay ด้วย Idempotency-Key เดิมเฉพาะเมื่อ API โฆษณา durable replay และยังอยู่ใน 23 ชั่วโมงนับจากการส่งครั้งแรก
- หากเกินเวลา/ไม่รองรับ durable replay จะหยุดให้ตรวจใน Hermes โดยไม่ส่งงานใหม่อัตโนมัติ
- เก็บผล terminal ที่เคยอ่านแล้วลง SQLite; งานที่เสร็จแต่ยังไม่เคยอ่านอาจหมดอายุฝั่ง Hermesได้ ต้องติดตามจนได้ผล
- ผลใหญ่แบ่งหน้า `offset`/`max_chars`; limit ต่อ HTTP response 4 MB
- ไม่มี background polling ใน bridge; ChatGPT หรือผู้ใช้ต้องเรียก status/result
- cancel เป็น cooperative stop ต้องดูสถานะจนเป็น cancelled/completed/failed; ไม่ย้อนผลการแก้ไขที่ทำไปแล้ว
- การหยุด Tunnel ตัดช่องทางสั่งงาน แต่ไม่ได้ยืนยันว่า run ที่เริ่มแล้วหยุด ต้อง cancel ก่อนหากต้องการหยุดงานด้วย
- bridge นี้สำหรับบัญชีผู้ใช้เดียว ทุกแชทที่เข้าถึง bridge เดียวกันเห็นรายการงานของ bridge เดียวกัน
- SQLite เก็บผลลัพธ์ที่อาจเป็นข้อมูลส่วนตัว ตั้งโฟลเดอร์ private และไม่ส่งไฟล์ state กลับมาโดยไม่ตรวจข้อมูล
- bridge ปิด outbound proxy inheritance และไม่ตาม HTTP redirects สำหรับ Hermes API; API key ถูกแทนที่ในผลลัพธ์ แต่ไม่ได้รับประกันตรวจจับ secret ชนิดอื่นทั้งหมด

## การแก้ปัญหา

| อาการ | ตรวจจุดใด |
|---|---|
| API 401 หลังติดตั้ง | bridge-config.json ชี้ `.env` ถูกไฟล์หรือไม่; restart bridge หลังเปลี่ยน key |
| API connection failed | Hermes gateway ต้องรันใน WSL เดียวกับ bridge; ตรวจ 8642 |
| พบคำเตือน config top-level | API_SERVER_* อยู่ใน `.env` ตามที่แก้ไปแล้ว ไม่ใช่ top-level YAML |
| Tunnel ไม่ปรากฏ | ตรวจ workspace association และ Tunnels Read + Use ใน Platform |
| Tunnel ถาม key ทุกครั้ง | รัน `bash tunnel.sh key-set`; ตรวจ `bash tunnel.sh key-status` ว่า mode เป็น 600 |
| `tunnel-client doctor` ตรง ๆ แจ้งว่า `CONTROL_PLANE_API_KEY` ไม่ได้ตั้ง | ไม่ได้พิสูจน์ว่า key file หาย: คำสั่งตรง ๆ ไม่โหลด key file ของ wrapper; ใช้ `bash tunnel.sh status` แทน |
| `Error fetching OAuth configuration` หรือ tunnel endpoint `does not implement OAuth` | ในหน้า Plugin ให้คง Connection เป็น **Tunnel** และเลือก **No authentication**; bridge stdio นี้ไม่มี OAuth discovery อย่าวาง hosted tunnel URL ใน Server URL |
| `Link not found` หรือ `Invalid MCP request metadata` หลัง disconnect/reconnect | ตรวจ `bash tunnel.sh status` ก่อน แล้วสร้าง developer-mode Plugin connection ใหม่โดยเลือก Tunnel เดิม; อย่า refresh หรือ reuse link ที่หาย และอย่าเปลี่ยน bridge เพื่อแก้ UI state |
| log มี `unsupported channel "harpoon"` | เก็บ log/redact key, ยืนยัน `bash tunnel.sh status` เป็น `RESULT ok`, ให้ `tunnel.sh run` ทำงานค้าง และสร้าง connection ด้วย Tunnel + No authentication ใหม่; หากยังเกิดซ้ำบน tunnel-client release ล่าสุด ให้ส่ง tunnel ID, เวอร์ชัน และ log ที่ redacted ให้ OpenAI Support—ไม่ต้องเพิ่ม OAuth หรือแก้ protocol ใน bridge |
| service command ใช้ไม่ได้ | ตรวจว่า WSL เปิด systemd และ `systemctl --user show-environment` ผ่าน |
| Discovery ล้มเหลว | tunnel-client ยังรันหรือไม่; bridge.sh รันได้และ doctor ผ่านหรือไม่ |
| รอ approval | ใช้ approve/deny ใน terminal ตามข้างบน |
| run 404 | อาจหมดอายุ/หายหลัง restart; ห้ามสรุปว่าไม่เคยรันแล้วส่งใหม่โดยไม่ตรวจ |
| syntax/flag error จาก tunnel-client | ใช้ help quickstart ของ binary ที่ติดตั้ง แล้วส่ง error โดยไม่แนบ key |

## ทดสอบซ้ำและไฟล์ประกอบ

```bash
.venv/bin/python -m unittest discover -s tests -v
```

v1.0.1 ผ่าน regression 48 tests โดยใช้ `-W error::ResourceWarning`; ครอบคลุม Hermes lifecycle/idempotency, Codex policy/process/watchdog/audit และ MCP stdio discovery 19 tools. ไม่มี test ใดใช้ model จริง
ไม่เชื่อม OpenAI หรือเครื่องผู้ใช้ในการทดสอบชุดนี้

`core.py` = Hermes HTTP/ownership/replay/SQLite; `codex_core.py` = Codex policy/job runner; `bridge.py` = MCP/CLI;
`install.sh` = ติดตั้ง; `bridge.sh` = launcher; `tunnel.sh` = configure/run tunnel;
`requirements.txt` = direct dependencies; `requirements-lock.txt` = dependency versions ที่ใช้ทดสอบ

หากจะถอน ให้หยุด Tunnel และลบ Plugin connection ก่อน แล้วค่อยเก็บ/ลบโฟลเดอร์ bridge ตามต้องการ
ตัวติดตั้งไม่ได้แก้ Hermes config จึงไม่มี peer หรือคำสั่งที่ต้องถอนจาก Hermes
ถ้าเลิกใช้ API ด้วย ให้ปิด `API_SERVER_ENABLED` ใน Hermes `.env` แล้ว restart gateway เมื่อไม่มีงานค้าง

## แหล่งอ้างอิงที่ตรวจ

- [Hermes peer implementation ที่ commit ของผู้ใช้](https://github.com/NousResearch/hermes-agent/blob/8d79c2ff/hermes_cli/subcommands/peer.py)
- [Hermes Runs API implementation](https://github.com/NousResearch/hermes-agent/blob/8d79c2ff/gateway/platforms/api_server_runs.py)
- [Hermes API docs ที่ commit เดียวกัน](https://github.com/NousResearch/hermes-agent/blob/8d79c2ff/website/docs/user-guide/features/api-server.md)
- [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
- [OpenAI Connect and test](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [Official tunnel-client releases](https://github.com/openai/tunnel-client/releases/latest)


## v1.2.1 — work contexts

Use `bridge_context_create` to create an explicit metadata-only context. Pass its `context_id` to later Hermes or Codex submissions. A Hermes context resumes only the bridge-owned `session_id` observed from task status/result; Codex contexts bind workspace/job metadata only and never replay prior prompts or outputs. There is no global active context, so a new ChatGPT chat must explicitly provide the intended `context_id`.
