# อัปเกรดเป็น v1.0.1

## จาก v1.0.0 เป็น v1.0.1

1. แตก package v1.0.1 ไปยังโฟลเดอร์ใหม่ แล้วคัดลอกเฉพาะ `bridge-config.json` และ `state/` ที่ตรวจแล้วจาก v1.0.0.
2. ถ้าตั้ง `codex.approval_ttl_seconds` ไว้น้อยกว่า 60 ให้ปรับเป็นอย่างน้อย 60 ก่อนรัน `bash install.sh`; v1.0.1 ปฏิเสธค่าที่ขัดกับ runtime ตั้งแต่ schema validation.
3. ตรวจ `./bridge.sh codex-doctor`, restart tunnel และตรวจ `bridge_status`. คง persistent tunnel/bridge server ไว้ระหว่าง Codex jobs ที่ต้องการ watchdog timeout enforcement.

## จาก v0.9.1 หรือ v1.0.0-rc.2 เป็น v1.0.0

1. ตรวจ archive ก่อนแตกด้วย `sha256sum -c SHA256SUMS`; สำหรับ v1.0.0 ค่า archive คือ `04421690f877807975810dfeffb29ec6412d8313103409cfd5713300e32de793`.
2. หยุด `tunnel.sh run` หรือ user service เดิม รอให้ job สำคัญเป็น terminal status แล้วแตก `hermes-mcp-bridge-v1.0.0.zip` ไปยังโฟลเดอร์ใหม่ ห้ามเขียนทับ deployment เดิม.
3. คัดลอกเฉพาะ `bridge-config.json` และ `state/` ที่ตรวจแล้วจาก deployment เดิม, แล้วรัน `bash install.sh`. ห้ามคัดลอก `.venv`, `.env` หรือ tunnel key.
4. รัน `./bridge.sh doctor`, `./bridge.sh codex-doctor` และ `./bridge.sh diagnostics`; ต้องไม่มี `config_warnings`.
5. ใช้ `bash tunnel.sh init tunnel_IDเดิม --force` เพื่อให้ profile ชี้ `bridge.sh` ใน v1.0.0, restart tunnel และเปิดแชทใหม่เพื่อตรวจ discovery 19 tools.
6. ตรวจ `bridge_status` และทำ read-only smoke test ก่อนอนุมัติ `workspace-write`. ดู acceptance ที่ยืนยันแล้วใน `V1-ACCEPTANCE-TH.md`.

หากใช้ Git clone แทน archive ให้ checkout signed tag `v1.0.0` และตรวจ `git verify-tag v1.0.0` ก่อนติดตั้ง.

## จาก v0.7.0 เป็น v0.8.0

1. หยุด `tunnel.sh run` เดิม แล้วแตกแพ็กเกจ v0.8.0 ไปยังโฟลเดอร์ใหม่
2. คัดลอก `bridge-config.json` และ `state/` จาก v0.7.0 มายังโฟลเดอร์ใหม่ แล้วรัน `bash install.sh`
3. Installer จะเพิ่ม `codex.watchdog_interval_seconds: 15` หากยังไม่มี; ตรวจด้วย `./bridge.sh codex-doctor`
4. รัน `.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -v` แล้วใช้ `bash tunnel.sh init tunnel_IDเดิม --force`
5. ทดสอบ read-only, cancellation และ timeout recovery ตาม `OPERATIONS-TH.md` ก่อนใช้งาน write job

## จาก v0.6.0 เป็น v0.7.0

1. หยุด `tunnel.sh run` เดิม แล้วแตกแพ็กเกจ v0.7.0 ไปยังโฟลเดอร์ใหม่
2. คัดลอก `bridge-config.json` และ `state/` จาก v0.6.0 มายังโฟลเดอร์ใหม่ แล้วรัน `bash install.sh`
3. กำหนด `allowed_models` และ `allowed_reasoning_efforts` ที่ระดับ `codex` หรือ workspace ที่ต้องการ หากไม่ต้องการให้เลือกค่า override ให้คง `[]` ไว้; deployment นี้ผ่านด้วย model IDs `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` และ effort `low`, `medium`, `high`
4. รัน `./bridge.sh codex-doctor` แล้วตรวจว่า policy ที่แสดงตรงกับที่ตั้งใจ
5. รัน `.venv/bin/python -m unittest discover -s tests -v` แล้วใช้ `bash tunnel.sh init tunnel_IDเดิม --force`
6. เปิดแชทใหม่ ตรวจ discovery 18 tools และทดสอบ read-only job ด้วย model/effort ที่อยู่ใน allowlist ก่อนใช้งาน write job

ค่า model/effort ที่ใส่ใน allowlist ต้องเป็นค่าที่บัญชี Codex CLI ของเครื่องใช้ได้จริง; bridge จะปฏิเสธค่าอื่นก่อนเริ่มงาน

## จาก v0.4.1 เป็น v0.5.0

1. หยุด `tunnel.sh run` เดิม แต่เก็บ `bridge-config.json` และ `state/`
2. แตกแพ็กเกจ v0.5.0 ไปยังโฟลเดอร์ใหม่ ห้ามลบแพ็กเกจเดิมก่อนตรวจเสร็จ
3. คัดลอก `bridge-config.json` และ `state/` จาก v0.4.1 มายัง v0.5.0
4. รัน `bash install.sh`; installer จะเพิ่ม `audit` block โดยรักษาค่า Hermes/Codex เดิม
5. รัน `./bridge.sh doctor`, `./bridge.sh codex-doctor` และ `./bridge.sh diagnostics`
6. รัน test suite แล้วใช้ `bash tunnel.sh init tunnel_IDเดิม --force` เพื่อให้ profile ชี้ bridge รุ่นใหม่
7. เปิดแชทใหม่และตรวจ discovery ทั้ง 17 tools รวม `bridge_diagnostics`

อย่าใส่ `/`, `/home`, `/mnt/e` หรือ root กว้าง ๆ ใน allowlist ให้ระบุ repository เป็นรายโฟลเดอร์

## ประวัติการอัปเกรด v0.2.0 → v0.3.1

รุ่นนี้รวม code v0.3.0 และแก้เอกสาร v0.3.1: เพิ่ม usage summary/export และทำให้ `tunnel.sh init ... --force` แทน profile เดิมได้ ทำใน WSL ด้วย user เดียวกับ Hermes และไม่ใช้ `sudo`

## 1. หยุดช่องทางเดิมอย่างปลอดภัย

รอให้ run สำคัญเป็น terminal (`completed`, `failed` หรือ `cancelled`) ก่อน แล้วกด `Ctrl+C` ใน terminal ที่รัน tunnel อยู่

```bash
cd /home/somchaip
```

การหยุด tunnel ไม่ได้หยุด Hermes run ที่เริ่มไปแล้ว ให้ใช้ `hermes_cancel_task` และ poll status หากต้องการยกเลิกงาน

## 2. แตกและติดตั้งรุ่นใหม่

```bash
cd /home/somchaip
unzip hermes-mcp-bridge-v0.3.1.zip
cd /home/somchaip/hermes-mcp-bridge-v0.3.1
bash install.sh
```

ตัวติดตั้งสร้าง `bridge-config.json` ใหม่ที่ชี้ Hermes `.env` และ `config.yaml`; ตรวจ local API ด้วย:

```bash
./bridge.sh doctor
```

## 3. ย้าย state (เลือกทำ)

หากไม่มี run กำลังทำงานและต้องการเก็บ mapping `request_id`/`run_id`/`session_id` รวมทั้ง usage เดิม ให้คัดลอก state ก่อนเปิด v0.3.1:

```bash
cp -a /home/somchaip/hermes-mcp-bridge-v0.2.0/state \
  /home/somchaip/hermes-mcp-bridge-v0.3.1/
```

ไม่ต้องย้าย `bridge-config.json` เพราะ installer สร้างค่าใหม่ให้แล้ว

ข้ามขั้นตอนนี้ได้หากไม่ต้องการอ่าน result เดิมหรือทำ follow-up กับ session เดิม; bridge จะเริ่ม state ใหม่และไม่สามารถอ้างสิทธิ์ run เก่าได้

## 4. อัปเดต tunnel ให้ชี้ bridge รุ่นใหม่

runtime key ที่เคยตั้งด้วย `key-set` อยู่ใน `~/.config/hermes-mcp-bridge/` และใช้ร่วมกันได้ ตรวจหรือบันทึกใหม่ได้โดยไม่แสดงค่า:

```bash
bash tunnel.sh key-status
# หากยังไม่มี key หรืออยากแทนค่า
bash tunnel.sh key-set
```

ให้รัน init ด้วย `tunnel_id` เดิมเพื่อให้ profile `hermes-wsl` เรียก `bridge.sh` จากโฟลเดอร์ v0.3.1:

```bash
bash tunnel.sh init tunnel_IDจริง --force
```

หลัง doctor ผ่าน ให้เปิดแชทใหม่: ต้องพบทั้งหมด 10 tools รวม `hermes_usage_summary` และ `hermes_usage_export`

## 5. รันต่อเนื่อง (ไม่บังคับ)

หาก WSL เปิด systemd user manager ได้:

```bash
bash tunnel.sh service-install
bash tunnel.sh service-start
bash tunnel.sh service-status
```

หากใช้ไม่ได้ ให้ใช้ `bash tunnel.sh run` ใน terminal ที่เปิดค้างไว้แทน

## Rollback

หยุด tunnel v0.3.1 แล้วรัน `tunnel-client init` จากโฟลเดอร์ v0.2.0 ด้วย `--profile hermes-wsl`, `--mcp-command "$PWD/bridge.sh"` และ `--force` ไฟล์ state ต้นฉบับยังอยู่เพราะขั้นตอนย้ายเป็นการ copy
