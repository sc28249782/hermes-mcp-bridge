# คู่มืออัปเกรด Hermes MCP Bridge

## v1.2.6 — released; deployment ต้องได้รับอนุมัติแยก

Signed v1.2.6 และ ZIP/SHA256SUMS ผ่านการตรวจหลังดาวน์โหลดแล้วเมื่อ 20 ตุลาคม 2026. GPG verification ผ่าน; GitHub badge เป็น `no_user`.
Checkpoint: operator อนุมัติ deployment และ maintenance window เมื่อ 20 ตุลาคม 2026 เวลา 13:52:34 +07. Production อัปเกรดจาก v1.2.5 เป็น v1.2.6 แล้ว. ดู [deployment record](V1.2.6-DEPLOYMENT-TH.md). ขั้นตอนด้านล่างยังต้องได้รับอนุมัติสำหรับ rollout ครั้งใหม่.
ใช้ขั้นตอนอัปเกรด v1.2.6 ได้เมื่อ operator อนุมัติ deployment แยกแล้วเท่านั้น. ดู [release record](RELEASE-STATUS-TH.md) และ [decision record](PRIVACY-RELEASE-DECISION-TH.md).
เมื่อเสนอ rollout ต้องแจ้งว่า Hermes status/result จะไม่ส่ง raw error และ approval payload; approval details ยังตรวจใน local terminal.
Init จะ enforce state/Codex-log directories เป็น `0700`; ถ้าเปลี่ยน mode ไม่ได้ ต้องแก้ ownership/permissions ภายในเครื่องก่อนเริ่มใหม่.
Codex result ของ snapshot เกิน 8,388,608 bytes จะ fail พร้อมคำแนะนำให้ตรวจในเครื่อง; ไม่ตัด output แล้วรายงานเหมือนอ่านครบ.
Tool count และ binaries ไม่เปลี่ยน.
อย่าแก้ directory ของ deployment เดิมเพื่อเปิดรุ่นใหม่ระหว่างงานที่ยังรันอยู่.

release ที่เผยแพร่ล่าสุดคือ v1.2.6 (20 ตุลาคม 2026) — ดูขั้นตอนท้ายเอกสาร หัวข้อ "จาก X เป็น Y" ด้านล่างเป็นบันทึกประวัติรายรุ่นคงไว้ตามเดิม

v1.2.5 เผยแพร่แล้ว พร้อม signed tag และ ZIP/SHA256SUMS ที่ตรวจหลังดาวน์โหลด; OpenCode execution ปิดโดยค่าเริ่มต้น การอัปเกรดไม่สลับ production หรือตั้ง permission ให้อัตโนมัติ.

## จาก v1.2.5 เป็น v1.2.6

1. เริ่มได้เมื่อ operator อนุมัติ deployment และกำหนด maintenance window แล้ว. หากยังไม่อนุมัติ ให้ใช้ deployment เดิม.
2. ดาวน์โหลด `hermes-mcp-bridge-v1.2.6.zip` และ external `SHA256SUMS` จาก [release v1.2.6](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.6). ตรวจ `sha256sum -c SHA256SUMS`, `unzip -t` และ signed tag/fingerprint ตาม [RELEASE-RUNBOOK-TH.md](RELEASE-RUNBOOK-TH.md). ต้องผ่านทุกข้อก่อนแตกไฟล์; GitHub badge ไม่ใช่ตัวแทน cryptographic verification.
3. หยุดรับงานใหม่ รอ jobs ของ instance เดิมเป็น terminal และตรวจ process ของ `unknown_exit`. หยุด instance และยืนยันว่าไม่มี writer/watchdog/worker ใช้ state ก่อน backup/copy. Backup config/state แบบ private ตาม mode 0600/0700. เก็บไดเรกทอรีเดิมไว้ใช้ rollback.
4. แตก ZIP ใน directory ใหม่. คัดลอกเฉพาะ config/state ที่ตรวจแล้ว พร้อมรักษาสิทธิ์. ตรวจ relative key/config references ให้ยังชี้เป้าหมายที่ถูกต้อง. ไม่คัดลอก `.env` หรือ `.venv`; ใช้ installer สร้าง venv ใหม่. ห้ามคัดลอก state ขณะที่มี worker ทำงาน.
5. ตรวจ `./bridge.sh version` เป็น `1.2.6/v1.2.6`, source `release-archive`, embedded build input `e3e698a7a220bf14a8bb4d1260bf2ded7e666b56` และ default count 27. ตรวจ config, state/Codex-log mode 0700 และ backend health ตาม configuration เดิมก่อนเปลี่ยน tunnel ไป directory ใหม่. การอัปเกรดไม่เปิด OpenCode หรือ Hands ให้เอง.
6. ตรวจ identity, status, configured discovery 27/28/33 และ applicable privacy acceptance หลังสลับ instance. บันทึกเฉพาะผลที่ตรวจได้; identity/health ไม่ใช่ production model-task acceptance. หากตรวจไม่ผ่าน ห้ามเริ่มงานใหม่และคืน instance เดิม. หากมีงานเริ่มไปแล้ว ให้ตรวจ process/state ก่อน rollback; ห้ามเขียนทับ state ที่มี worker ทำงาน.

## จาก v1.2.3 หรือ v1.2.4 เป็น v1.2.5

ขั้นตอนนี้ใช้กับ signed release v1.2.5 ซึ่งตรวจ release assets แล้ว ดู [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md).

1. ดาวน์โหลด `hermes-mcp-bridge-v1.2.5.zip` กับ external `SHA256SUMS` จาก [GitHub Release v1.2.5](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.5) ตรวจ `sha256sum -c SHA256SUMS`, `unzip -t` และ signed tag ตาม [RELEASE-RUNBOOK-TH.md](RELEASE-RUNBOOK-TH.md).
2. รอ Hermes, Codex และ OpenCode jobs ของ instance ที่จะอัปเกรดเป็น terminal; ถ้ามี `unknown_exit` ให้ตรวจ process ก่อน หยุดเฉพาะ tunnel ของ instance นั้น แล้วแตก ZIP ไป directory ใหม่ ห้ามเขียนทับ deployment เดิมหรือคัดลอก state ที่ยังมี worker ทำงาน.
3. คัดลอกเฉพาะ config/state ที่ตรวจแล้วไป directory ใหม่ รักษา mode 0600/0700 ตรวจ relative references ใน `hermes_env`/`hermes_config` ให้ยังชี้ไฟล์เดิมที่ถูกต้อง ไม่คัดลอก key, `.env` หรือ `.venv` รัน `bash install.sh` เพื่อสร้าง venv ใหม่.
4. ตรวจ `./bridge.sh version` เป็น `1.2.5` / `v1.2.5` และใช้ `doctor`, `codex-doctor`, `diagnostics` ตรวจ config/auth เดิม การอัปเกรดไม่เปิด OpenCode อัตโนมัติ: default 27 tools, เปิด health เป็น 28, เปิด execution แยกเป็น 33 ตาม [OPENCODE-TH.md](OPENCODE-TH.md). Workspace เป็น cwd allowlist ไม่ใช่ filesystem/network sandbox และ native permissions ยังคงมีผล.
5. เปิด editor ของ profile ที่ต้องการ เปลี่ยนเฉพาะ command ให้ชี้ `bridge.sh` ใหม่ แล้ว restart จาก authenticated terminal เดิม สำหรับ Dev ใช้ `EDITOR=nano tunnel-client profiles edit hermes-wsl-dev` และ `tunnel-client run --profile hermes-wsl-dev --health.listen-addr 127.0.0.1:8081`; ห้ามใช้ `tunnel.sh init/run` ของ baseline เพื่อเปิด Dev เพราะสคริปต์เลือก production profile.
6. Refresh plugin tools ตรวจ version/revision และจำนวน tools ตาม config ก่อนส่ง benign task; ตรวจ status/result และไฟล์จริงเมื่อทดสอบเขียนไฟล์ Retry งานเดิมใช้ request ID/input เดิม ห้ามส่งซ้ำเพราะ reconnect.
7. Rollback: รอ/ตรวจงานของ instance ใหม่ให้จบก่อนหยุด tunnel แล้วคืน profile command เป็น deployment เดิม อย่า replay งานที่มีผลข้างเคียง และอย่ารวม state database ต่างชุดโดยเดา หากมี `unknown_exit` ให้ตรวจ process/workspace ก่อน.

## จาก v1.2.2 เป็น v1.2.3

1. ดาวน์โหลด `hermes-mcp-bridge-v1.2.3.zip` และ external `SHA256SUMS` จาก [GitHub Release v1.2.3](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.3). ตรวจ archive ด้วย `sha256sum -c SHA256SUMS`; checksum ที่เผยแพร่คือ `c231f8563543dbfa9eafa240c5e8e15f44434103940352066e65b58162cb5458`.
2. รอ Codex job สำคัญเป็น terminal status. หยุด tunnel ของ deployment เดิม แล้วแตก archive ไปยัง directory ใหม่. ห้ามเขียนทับ deployment เดิม.
3. Copy เฉพาะ `bridge-config.json` และ `state/` ที่ตรวจแล้ว. ห้าม copy `.venv`, key หรือ `.env`.
4. รัน `bash install.sh`, `./bridge.sh version`, `./bridge.sh doctor`, `./bridge.sh codex-doctor`, และ `./bridge.sh diagnostics`. ต้องตรวจว่า version เป็น `1.2.3` และ `release_identifier` เป็น `v1.2.3`.
5. restart tunnel ของ instance ใหม่, เปิด chat ใหม่, และตรวจ discovery ตาม canonical contract ใน `TESTING.md` ก่อนส่ง read-only job. งาน `workspace-write` ยังต้อง local terminal approval.
6. หาก worker หายแต่ Codex child ยังทำงานอยู่, bridge จะคืน `running` พร้อม `supervision_lost`. ห้ามส่งงานซ้ำหรือสรุป `unknown_exit` จนกว่า child จะจบ.

## จาก v1.2.1 เป็น v1.2.2

1. ดาวน์โหลด `hermes-mcp-bridge-v1.2.2.zip` และ external `SHA256SUMS` จาก [GitHub Release v1.2.2](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.2), แล้วรัน `sha256sum -c SHA256SUMS`; รอ Codex job สำคัญเป็น terminal status ก่อน upgrade.
2. แตก archive/checkout ไป directory ใหม่ แล้ว copy เฉพาะ `bridge-config.json` และ `state/` ที่ตรวจแล้ว; ห้าม copy `.venv`, key หรือ `.env`.
3. รัน `bash install.sh`, `./bridge.sh version`, `./bridge.sh doctor`, `./bridge.sh codex-doctor` และ `./bridge.sh diagnostics`.
4. หากใช้ `codex.workspaces`, ย้าย allowlist เดิมจาก `codex.allowed_workspaces` มาเป็น policy entries ทั้งหมดก่อน restart; เมื่อมี `workspaces` runtime จะไม่รวม legacy allowlist.
5. restart tunnel ของ instance ที่อัปเกรด, เปิด chat ใหม่ และตรวจ `bridge_version` กับ canonical discovery count ใน `TESTING.md` ก่อน read-only smoke test. workspace-write ยังคงต้อง local approval.

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

## OpenCode adapter และ stdio guard — released v1.2.4 (18 ตุลาคม 2026; production ยัง v1.2.3)

release v1.2.4 เผยแพร่แล้ว (18 ตุลาคม 2026) ผ่าน signed tag `v1.2.4` บน main `2133056` ดาวน์โหลด ZIP และ `SHA256SUMS` จาก [GitHub Release v1.2.4](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.4), ตรวจด้วย `sha256sum -c SHA256SUMS` (ZIP SHA-256 `e6deb0e6ab16d669836b0e361e2e875858e19597ef35dc7e4fc19010a6a5f3a9`) แล้วจึงติดตั้ง/อัปเกรดตามแนวทาง download-verify-install เดิม การอัปเกรดเป็นทางเลือกของ operator ตามจังหวะของตน: production deployment ยังคงรัน released v1.2.3 และ release นี้ไม่ต้องการ rollout, service, config หรือการ restart ใด ๆ ข้อจำกัดที่บันทึกไว้คงอยู่: live tunnel acceptance เป็น bounded PASS (identity/status/tool visibility) ส่วน guard outcome บน tunnel ยังสังเกตไม่ได้ — รายละเอียดใน LIVE-ACCEPTANCE-TH.md

อัปเกรดเป็น v1.2.4: `sha256sum -c SHA256SUMS`, แตก archive ไปยัง directory ใหม่, `bash install.sh` และ health checks ตาม RELEASE-RUNBOOK-TH.md. หัวข้อ `opencode` เป็น optional และ disabled by default — ไม่มีการเปิดใช้อัตโนมัติและไม่ต้องแก้ config ใด ๆ ระหว่างอัปเกรด. stdio guard ทำงานเองบน `bridge.py serve` โดยไม่ต้องแก้ config

หมายเหตุ (19 ตุลาคม 2026): production deployment อัปเกรดเป็น released v1.2.5 แล้ว ข้อความ "production ยัง v1.2.3" ในหัวข้อ v1.2.4 ข้างต้นเป็นบันทึก ณ วันเผยแพร่ v1.2.4 คงไว้ตามหลักฐานเดิม (checkpoint การอัปเกรดอยู่ใน [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)).

## OpenCode execution — released v1.2.5 (opt-in)

ส่วนส่งงาน OpenCode ใน [OPENCODE-TH.md](OPENCODE-TH.md) เผยแพร่ใน v1.2.5 แล้ว
การติดตั้ง ZIP v1.2.4 ไม่ทำให้มี execution tools และไม่ควรแก้ไฟล์ใน production deployment เดิม
ทดสอบ release v1.2.5 ใน directory/state แยกสำหรับ Dev พร้อม explicit execution config
ก่อนเปลี่ยน Dev route ต้องรอ job เดิมจบและเก็บ config/profile เดิมไว้สำหรับ rollback
restart/refresh เฉพาะ Dev แล้วตรวจ discovery 33 tools และทดสอบหนึ่งงานกับ session reuse
การ merge PR หรือการเผยแพร่ release ไม่ได้เปิด execution หรือติดตั้ง production ให้อัตโนมัติ

