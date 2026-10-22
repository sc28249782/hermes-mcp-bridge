# Hermes MCP Bridge — released v1.2.8 (ยังไม่ deploy) / production signed v1.2.7

## v1.2.8 — released (22 October 2026)

Scope ได้รับอนุมัติแล้ว. อัปเดตสถานะ (22 ตุลาคม 2026): v1.2.8 เผยแพร่แล้วผ่าน signed tag `v1.2.8` (object `bb2f076bb3fd665950551ca613abb6ce6fb8f809`, peeled commit `1ae159031a53e4e5359fd39e61b2748159149a52`) และ [GitHub Release](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.8) พร้อม ZIP/SHA256SUMS ที่ตรวจหลังดาวน์โหลดฝั่ง maintainer และ external fresh-input audit ผ่าน (APPROVE ที่ PR #74 head `cddcdb5`). รวม SPEC §21 context-lifecycle delta. ยังไม่ deployed; production คง signed v1.2.7. ดู [release record](V1.2.8-RELEASE-RECORD-TH.md), [preparation record](V1.2.8-RELEASE-PREP-TH.md) และ [scope decision](V1.2.8-RELEASE-DECISION-PROPOSAL-TH.md).

## v1.2.7 — released (20 October 2026); deployed 21 October 2026

Scope ได้รับอนุมัติแล้ว. Source stamp เป็น `1.2.7/v1.2.7`, reviewed build input `07ec0069b952f08a49adbd0ec778c204f85ee282`. รวม Codex read-ahead fix และ Context P1 warning/status/local preview. เผยแพร่แล้วผ่าน signed tag `v1.2.7` และอัปเกรด production เมื่อ 21 ตุลาคม 2026 (ข้อความ "ยังไม่ signed/released/deployed; production คง v1.2.6" ด้านล่างเดิมเป็นบันทึกช่วง preparation ณ 20 ตุลาคม 2026). ดู [preparation record](V1.2.7-RELEASE-PREP-TH.md), [scope decision](V1.2.7-RELEASE-DECISION-TH.md) และ [release record](V1.2.7-RELEASE-RECORD-TH.md).

## Signed v1.2.6 และ historical checkpoints

ข้อความ candidate v1.2.6 ด้านล่างเป็นบันทึกก่อน publication ของรุ่นนั้น; ไม่ใช่ stamp ปัจจุบันของ candidate v1.2.7.

Release checkpoint (20 ตุลาคม 2026): v1.2.6 เผยแพร่แล้วพร้อม ZIP/SHA256SUMS ที่ตรวจหลังดาวน์โหลด. GPG signature ผ่าน; GitHub badge เป็น `no_user`. Production เป็น v1.2.5 ตอนตรวจหลัง publication. Operator อนุมัติ deployment แยกเมื่อ 13:52:34 +07 และอัปเกรดเป็น v1.2.6 แล้วในวันเดียวกัน. ดู [deployment record](V1.2.6-DEPLOYMENT-TH.md) สำหรับ acceptance และข้อจำกัด. ดู [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md). Checkpoint เกี่ยวกับ candidate ด้านล่างเป็นบันทึกก่อน publication.

Candidate checkpoint (20 ตุลาคม 2026): source นี้ stamp `1.2.6/v1.2.6` สำหรับ privacy hardening ตาม SPEC §19. ยังไม่ released หรือ deployed. Release ที่เผยแพร่ล่าสุดและ production checkpoint ยังคง v1.2.5. ดู [release-preparation record](V1.2.6-RELEASE-PREP-TH.md) สำหรับ candidate verification และ gates ก่อน tag.

[![Tests](https://github.com/sc28249782/hermes-mcp-bridge/actions/workflows/tests.yml/badge.svg)](https://github.com/sc28249782/hermes-mcp-bridge/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../LICENSE)

Repository: https://github.com/sc28249782/hermes-mcp-bridge  
Specification: [SPEC.md](SPEC.md)  
Release status: [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)  
Operations: [OPERATIONS-TH.md](OPERATIONS-TH.md)  
จุดเริ่มต้นของโครงการ: [Project origin](PROJECT-ORIGIN.md)

จัดทำสำหรับ Hermes Agent v0.21.1, commit `8d79c2ff` ที่ผู้ใช้ยืนยัน
วันที่ปรับปรุง: 20 ตุลาคม 2026 — v1.2.6 released; signed tag และ release assets ผ่านการตรวจแล้ว

หมายเหตุ (18 ตุลาคม 2026): released v1.2.4 เผยแพร่แล้วผ่าน signed tag (ZIP ตรวจแล้วจากการดาวน์โหลดจริง; ดู [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)) โดยเพิ่ม OpenCode health adapter แบบ disabled by default และ legacy stdio discovery guard ขณะนั้นคู่มือแนะนำติดตั้ง released v1.2.4 การอัปเกรด deployment ที่ผลิตจริงเป็นดุลยพินิจของ operator (ยังรัน v1.2.3 เดิมได้)

หมายเหตุ (19 ตุลาคม 2026): เผยแพร่ **v1.2.5** แล้ว พร้อม signed tag และ ZIP/SHA256SUMS ที่ตรวจหลังดาวน์โหลด คู่มือปัจจุบันใช้ v1.2.5; ดู [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md) สำหรับ checksum และ provenance; production deployment อัปเกรดเป็น v1.2.5 แล้วเมื่อ 19 ตุลาคม 2026 (ตรวจ identity/health/discovery แบบ read-only ผ่าน production plugin; ขอบเขตหลักฐานอยู่ใน RELEASE-STATUS-TH.md)

ตัวกลางนี้ทำให้ ChatGPT ส่งงานให้ Hermes ที่รันอยู่บนเครื่องคุณ แล้วตรวจสถานะ อ่านผล และขอหยุดงานได้
ใช้ Runs API เดียวกับที่ `hermes peer run/status/stop` เรียก แต่เรียก HTTP โดยตรง
งานใหม่เริ่ม session ใหม่ ไม่ใช้ canonical “Bot Chat” ร่วมกับ peer อื่น
งานต่อเนื่องสามารถใช้ `context_id` แบบ explicit เพื่อผูก Hermes session หรือ Codex workspace metadata ได้; ไม่มี global active context และไม่มีการ replay prompt/output

เส้นทาง: ChatGPT → Secure MCP Tunnel → bridge.sh (stdio MCP) → Hermes API `127.0.0.1:8642`

## ตรวจ identity ของ deployment

```bash
./bridge.sh version
```

คำสั่งนี้ไม่เรียก Hermes, Codex, tunnel หรือ network. สำหรับ release ที่ลงนามแล้ว `release_identifier` ต้องตรง tag ที่ติดตั้ง; candidate อาจรายงาน revision เป็น `unknown` อย่างปลอดภัย.

## สถานะก่อนติดตั้ง

- ผู้ใช้ทดสอบ `/v1/models` แล้ว: ไม่มี key ได้ 401; key ถูกต้องได้ 200
- มีเมนู Developer mode และ Connection → Tunnel
- ยังต้องสร้าง tunnel ใน OpenAI Platform, ติดตั้ง tunnel-client และเชื่อม Plugin
- v1.2.1 ผ่าน regression 63/63 โดยใช้ project `.venv/bin/python` พร้อม `-W error::ResourceWarning`, shellcheck และ Bash syntax; Live Acceptance ผ่าน Hermes context ข้าม ChatGPT chat, Codex metadata-only binding, closed-context denial และ audit redaction
- v1.2.3 ผ่าน 75 regression tests, WSL2 worker-supervision acceptance และ independent review
- v1.2.4 ผ่าน 129 regression tests รวม stdio-guard และ packaging tests, live tunnel acceptance แบบ bounded PASS บน Dev route และการตรวจ release assets หลังดาวน์โหลด (ดู [TESTING.md](TESTING.md) และ [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)) ผลข้างต้นเป็นหลักฐาน v1.2.4; สำหรับติดตั้งปัจจุบันใช้ release v1.2.6 ในหัวข้อถัดไป

อัปเกรดจาก bridge รุ่นก่อนใช้ [UPGRADE-TH.md](UPGRADE-TH.md) ก่อนเริ่ม tunnel รุ่นใหม่ โดยเฉพาะหากต้องการเก็บ session/state เดิม

## 1. ติดตั้งตัวกลางใน WSL2

ดาวน์โหลดทั้ง `hermes-mcp-bridge-v1.2.6.zip` และ `SHA256SUMS` จาก [GitHub Release v1.2.6](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.6) แล้ววางทั้งสองไฟล์ไว้ในโฟลเดอร์บ้านของผู้ใช้ใน WSL เช่น:

```text
~
```

`SHA256SUMS` เป็น external release asset จึงต้องอยู่ข้าง ZIP ก่อนตรวจสอบ หากดาวน์โหลดผ่าน Windows สามารถเปิดโฟลเดอร์บ้าน WSL ใน File Explorer ด้วย `explorer.exe ~` แล้วแตกไฟล์ใน WSL:

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
   unzip hermes-mcp-bridge-v1.2.6.zip
   ```
4. เข้า directory ที่แตกได้:

   ```bash
   cd ~/hermes-mcp-bridge-v1.2.6
   ```
5. ติดตั้ง:

   ```bash
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

1. เข้า directory ของ deployment นั้น:

   ```bash
   cd ~/hermes-mcp-bridge-v1.2.6
   ```
2. ซ่อม pip ใน venv เดิม:

   ```bash
   .venv/bin/python -m ensurepip --upgrade
   ```
3. ติดตั้งซ้ำ:

   ```bash
   bash install.sh
   ```

หากไม่มี `ensurepip` ด้วย และใช้ Ubuntu/Python 3.12:

1. ติดตั้งแพ็กเกจ venv ของระบบ:

   ```bash
   sudo apt install python3.12-venv
   ```
2. อัปเกรด venv เดิม:

   ```bash
   python3 -m venv --upgrade .venv
   ```
3. ติดตั้งซ้ำ:

   ```bash
   bash install.sh
   ```

ตัวติดตั้งฉบับแก้ไขตรวจและ bootstrap pip ก่อนใช้ pip install แล้ว ส่วนเส้นทาง `uv pip install` ไม่ต้องมี pip อยู่ใน venv
ไม่ต้องลบโฟลเดอร์โครงการหรือสร้าง alias `python`

ตัวอย่าง config ที่จะสร้าง:

```json
{
  "api_url": "http://127.0.0.1:8642",
  "hermes_env": "/home/<user>/.hermes/.env",
  "hermes_config": "/home/<user>/.hermes/config.yaml",
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
แตกแพ็กเกจแล้ววาง executable `tunnel-client` ใน `~/.local/bin/`
รักษาไฟล์ประกอบตามคำแนะนำใน release นั้นถ้ามี ตรวจ checksum กับ `SHA256SUMS` ของ release เดียวกัน

1. สร้าง directory สำหรับ executable:

   ```bash
   mkdir -p ~/.local/bin
   ```

2. ตรวจว่าได้วาง executable ที่ดาวน์โหลดและตรวจ checksum แล้วไว้ที่ `~/.local/bin/tunnel-client` ก่อนกำหนด permission:

   ```bash
   chmod 700 ~/.local/bin/tunnel-client
   ```

3. เพิ่ม directory นี้ใน PATH ของ shell ปัจจุบัน:

   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

4. ตรวจว่า client แสดง quickstart ได้ หากคำสั่งล้มเหลวให้หยุดและตรวจไฟล์/architecture/PATH ก่อน init:

   ```bash
   tunnel-client help quickstart
   ```

ไฟล์ tunnel-client ไม่ได้รวมอยู่ใน ZIP นี้ ขั้นตอน init/doctor/run ด้านล่างอิงคำสั่งในเอกสาร OpenAI ที่ตรวจวันที่จัดทำ
หาก CLI ที่ดาวน์โหลดเปลี่ยนรูปแบบ ให้ดู `tunnel-client help quickstart` และส่ง error มาตรวจ ไม่ต้องเดาชื่อ flag

## 4. ตั้งค่าและรัน Tunnel

หัวข้อนี้ใช้ production profile `hermes-wsl` ซึ่ง `tunnel.sh` กำหนดไว้ตายตัว
ก่อนเริ่ม `init` หรือ `run` ให้ operator ยืนยันว่าไม่มี tunnel instance ของ profile นี้ทำงานอยู่
หาก profile เดิมเป็นของงานอื่น ให้หยุดขั้นตอนนี้
สำหรับ Dev profile `hermes-wsl-dev` และ health port 8081 ให้ใช้ [OPENCODE-TH.md](OPENCODE-TH.md).

คง Hermes gateway ให้รันอยู่ เปิด terminal อีกหน้าหนึ่ง แล้วทำตามลำดับ:

1. เข้า directory ของ bridge ที่จะเชื่อมต่อ:

   ```bash
   cd ~/hermes-mcp-bridge-v1.2.6
   ```

2. บันทึก OpenAI Platform runtime key ซึ่งเป็นคนละตัวกับ Hermes `API_SERVER_KEY`:

   ```bash
   bash tunnel.sh key-set
   ```

3. ตรวจ key file:

   ```bash
   bash tunnel.sh key-status
   ```

   ต้องรายงานว่า key file มีอยู่และ mode เป็น `600`
   หากรายงาน `Runtime key is not saved` หรือ mode ไม่ตรง ให้หยุดและแก้ก่อนเริ่ม tunnel
   Exit code 0 เพียงอย่างเดียวไม่ยืนยันว่ามี key และขั้นนี้ไม่ตรวจ authentication
   สคริปต์เก็บ key ที่ `~/.config/hermes-mcp-bridge/openai-runtime-api-key`
   สคริปต์ไม่ใส่ key ลง command history หรือ systemd unit file

4. แทน `tunnel_YOUR_ID` ด้วย tunnel ID จริงจาก Platform แล้วเลือกคำสั่งเพียงกรณีเดียว:

   หากยังไม่มี profile `hermes-wsl` ให้สร้าง profile:

   ```bash
   bash tunnel.sh init tunnel_YOUR_ID
   ```

   หากมี profile เดิม ให้ตรวจ tunnel ID และ command target ใน profile ก่อน
   ใช้คำสั่งต่อไปนี้เฉพาะเมื่อ operator ยืนยันให้แทน profile ของ instance นี้:

   ```bash
   bash tunnel.sh init tunnel_YOUR_ID --force
   ```

   อย่าพิมพ์ `[--force]` เป็น argument
   เมื่อสำเร็จ `init` จะสร้าง profile ตรวจ `doctor` และเริ่ม tunnel แบบ foreground
   หาก doctor ล้มเหลว ให้หยุดและแก้ตามข้อความ ไม่ต้องส่งงานใหม่ผ่าน Plugin
   เมื่อเชื่อมต่อแล้ว ให้เปิด terminal นี้ค้างไว้และไปเพิ่ม Plugin ในหัวข้อ 5

หากต้องตรวจ profile ที่สร้างแล้ว ให้เปิด terminal อีกหน้าหนึ่งโดยคง tunnel เดิมไว้
เข้า directory ของ instance เดิม:

```bash
cd ~/hermes-mcp-bridge-v1.2.6
```

ตรวจ doctor ผ่าน wrapper:

```bash
bash tunnel.sh status
```

คำสั่งนี้ตรวจ doctor และไม่เริ่ม tunnel เพิ่ม
ผลต้องผ่านก่อนใช้งานต่อ หากไม่ผ่าน ให้ตรวจ error ของ instance นี้
`tunnel.sh` โหลด key file เข้า environment ให้ doctor และ run
การเรียก `tunnel-client doctor --profile hermes-wsl` โดยตรงไม่โหลด key file นี้
ห้ามพิมพ์ key ลง command line, chat หรือ log

Tunnel เรียก `bridge.sh` ผ่าน stdio
ไม่ต้องเปิด bridge เป็น HTTP server หรือรัน `bridge.sh serve` แยก
`hermes mcp serve` ไม่ใช่ Runs bridge นี้

สำหรับการเริ่มครั้งถัดไป ใช้ terminal ใน directory ของ instance นี้
รันเมื่อ tunnel เดิมหยุดแล้วเท่านั้น:

```bash
bash tunnel.sh run
```

หากต้องการใช้ systemd user service ให้กด `Ctrl+C` ใน terminal ของ foreground tunnel นี้ก่อน
ยืนยันว่า foreground process ออกแล้วก่อนเริ่ม service
จาก directory เดิม:

1. สร้างและเปิดใช้ unit โดยต้องมี key file แล้ว:

   ```bash
   bash tunnel.sh service-install
   ```

2. เริ่ม service:

   ```bash
   bash tunnel.sh service-start
   ```

3. ตรวจว่า service เป็น `active (running)`:

   ```bash
   bash tunnel.sh service-status
   ```

หาก service ไม่ active ให้ตรวจ `bash tunnel.sh service-logs` และแก้ error ก่อนส่งงาน
หยุด service ด้วย `bash tunnel.sh service-stop`
การหยุด tunnel ไม่ได้หยุด Hermes run ที่เริ่มแล้ว
การเชื่อมออกนี้ไม่ต้องเปลี่ยน WSL networking mode หรือ forward พอร์ต 8642 ที่เราเตอร์

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

ตรวจจำนวนเครื่องมือตาม canonical discovery contract ใน [TESTING.md](TESTING.md). ตารางต่อไปนี้เป็นคำอธิบายเครื่องมือพื้นฐาน ไม่ใช่รายการ discovery ทั้งหมด:

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

ตารางนี้ไม่ใช่รายการครบทุก tool: ยังมี work contexts 4 ตัว, Local Hands read-only 3 ตัว (`hands_health`, `hands_list`, `hands_read`) และ `bridge_version` รวมเป็น canonical 27 tools ตาม [TESTING.md](TESTING.md) นอกจากนี้ยังมี `opencode_health` เป็น tool ที่ 28 เฉพาะเมื่อ operator เปิดใช้ section `opencode` ด้วยตนเอง (ปิดเป็นค่าเริ่มต้น, ตรวจสุขภาพอย่างเดียว, ไม่เรียกโมเดล; ดู [README.md](../README.md) และ [SPEC.md](SPEC.md) section 16)

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

1. ตรวจรายละเอียด request:

   ```bash
   ./bridge.sh status run_แทนด้วยIDจริง
   ```

2. อนุมัติเฉพาะ request นั้น:

   ```bash
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

## OpenCode task execution (released v1.2.5)

ส่วน execution (SPEC.md section 18) รวมใน `main` แล้วผ่าน PR #40 และเผยแพร่ใน
v1.2.5 เพิ่ม 5 tools
(`opencode_submit_task`, `opencode_task_status`, `opencode_task_result`,
`opencode_cancel_task`, `opencode_recent_tasks`) เป็น 33 tools ปิด default —
เปิดได้ด้วย `opencode.execution.enabled=true` ซึ่งต้องมี `opencode.enabled` +
`opencode.binary`, `allowed_workspaces` (absolute canonical path) และ
`allowed_models` (เช่น `opencode-go/glm-5.3-flash`) ไม่ว่าง พร้อมขอบเขต
`max_prompt_chars` / `max_runtime_seconds` / `max_output_bytes` แยกจากของ health

ขอบเขตสำคัญ: executable รันด้วยสิทธิ์เต็มของ bridge process, **ไม่มี sandbox**,
workspace เป็น cwd allowlist ไม่ใช่ filesystem/network isolation, bridge ไม่ inject
permission configuration และ native policy ของ OpenCode ทำงานตามปกติ, ห้าม `--auto`,
bridge ไม่เคยอนุมัติ permission แทน (unresolved ask จบเป็น failed ตาม deadline หรือ
permission_required เมื่อเห็น protocol event ชัด). `completed` แปลว่า native turn จบ
ไม่ได้แปลว่าเป้าหมายสำเร็จ — ตรวจ output (untrusted) เอง. session เป็นของ bridge;
resume ได้เฉพาะ session เดิม workspace/model เดิม; retry ด้วย `request_id` เดิมได้
acknowledgement เดิมโดยไม่เรียก model ซ้ำ. รายละเอียด: [OPENCODE-TH.md](OPENCODE-TH.md)
