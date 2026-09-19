# อัปเกรดเป็น v0.4.0

## จาก v0.3.2 เป็น v0.4.0

1. หยุด `tunnel.sh run` เดิม แต่เก็บ `bridge-config.json` และ `state/`
2. แตกแพ็กเกจ v0.4.0 ไปยังโฟลเดอร์ใหม่ ห้ามลบแพ็กเกจเดิมก่อนตรวจเสร็จ
3. คัดลอก `bridge-config.json` และ `state/` จาก v0.3.2 มายัง v0.4.0
4. รัน `bash install.sh`; installer จะเพิ่ม `codex` block โดยรักษาค่า Hermes เดิม
5. แก้ `codex.allowed_workspaces` ให้เป็น path repository จริงใน WSL2
6. รัน `./bridge.sh doctor` และ `./bridge.sh codex-doctor`
7. รัน test suite แล้วเริ่ม tunnel ใหม่
8. เปิดแชทใหม่และตรวจ discovery ทั้ง 16 tools

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
