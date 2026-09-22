# Local Hands v1.2.0 — WSL2/DrvFS Live Acceptance

สถานะ: release gate สำหรับ `v1.2.0`; ต้องบันทึกผลจริงก่อน tag  
ใช้กับ: commit ที่ผ่าน CI แล้วเท่านั้น และใช้ dedicated disposable fixture เท่านั้น

## เงื่อนไขก่อนเริ่ม

- ทำบน WSL2 Ubuntu ของผู้ดูแล ด้วย user ปกติ ไม่ใช้ `sudo`
- ใช้ bridge checkout ที่จะเป็น release commit และ `bash install.sh` ผ่านแล้ว
- ห้ามใส่ home directory, project จริง หรือ credential directory เป็น Hands workspace
- เตรียม fixture แยก 2 แห่ง: ext4 ใต้ `/home/...` และ DrvFS ใต้ `/mnt/<drive>/...`
- บันทึก commit SHA, `uname -r`, `wsl.exe --version`, mount option ของ fixture และผล `./bridge.sh hands-doctor`

## 1. สร้าง fixture ที่ลบได้

ทำทีละ filesystem โดยกำหนด `ROOT` เป็น parent directory ที่ตั้งใจใช้ทดสอบเท่านั้น:

```bash
umask 077
ROOT=/home/$USER/local-hands-acceptance       # รอบ ext4
# ROOT=/mnt/e/local-hands-acceptance          # รอบ DrvFS, รันแยกอีกครั้ง
mkdir -p -- "$ROOT"
FIXTURE="$(mktemp -d "$ROOT/.v12-hands.XXXXXX")"
printf 'allowed fixture\n' > "$FIXTURE/allowed.txt"
printf 'API_KEY=must-not-leave-workspace\n' > "$FIXTURE/.env"
printf 'binary\0fixture' > "$FIXTURE/binary.txt"
ln -s /etc/hostname "$FIXTURE/escape"
mkdir "$FIXTURE/nested"
printf 'nested fixture\n' > "$FIXTURE/nested/allowed.txt"
printf '%s\n' "$FIXTURE"
```

เก็บค่าที่พิมพ์จากบรรทัดสุดท้ายไว้เพื่อ cleanup หลังจบเท่านั้น ตรวจชื่อให้เป็น `.v12-hands.*` ใต้ `ROOT` ก่อนลบ

## 2. เปิด policy แบบชั่วคราว

สำรอง `bridge-config.json` ก่อน แล้วเพิ่ม/แก้เฉพาะ block นี้ให้ `path` เป็นค่า `FIXTURE` ที่สร้างจริง:

```json
"hands": {
  "enabled": true,
  "workspaces": [{ "name": "acceptance", "path": "/absolute/path/to/FIXTURE" }],
  "max_read_bytes": 65536,
  "max_read_chars": 65536,
  "max_list_entries": 50
}
```

restart bridge/tunnel ตามวิธีปฏิบัติของ deployment แล้วรัน:

```bash
./bridge.sh hands-doctor
findmnt -T "$FIXTURE" -o TARGET,SOURCE,FSTYPE,OPTIONS
```

ต้องได้ workspace `acceptance` เป็น `available` และไม่ยอมรับ fallback resolver หากเป็น `unavailable` ให้บันทึก filesystem/kernel แล้วหยุดรอบนั้น

## 3. ตรวจผ่าน Secure MCP Tunnel

ใน ChatGPT connection เดียวกับ bridge ให้เรียกตามลำดับนี้:

1. `hands_health` — `ok: true`, workspace `acceptance` และ filesystem ที่รายงานตรงกับ mount
2. `hands_list(workspace="acceptance")` — เห็น `allowed.txt`, `nested` และอาจเห็น `binary.txt`; ต้องไม่เห็น `.env` หรือ `escape`
3. `hands_read(workspace="acceptance", path="allowed.txt")` — ได้ข้อความ fixture เท่านั้น
4. `hands_read(..., path="nested/allowed.txt")` — ได้ข้อความ nested fixture
5. ยืนยันถูกปฏิเสธ: `.env`, `binary.txt`, `escape`, `../etc/passwd`, `/etc/passwd`, `nested/../allowed.txt`
6. ตรวจ `bridge_audit_recent` — ไม่มี `API_KEY`, เนื้อหา fixture, `.env`, `allowed.txt` หรือ absolute fixture path

ทำครบชุดบน ext4 และ DrvFS แยกกัน สำหรับ DrvFS ให้เพิ่มไฟล์ `A.txt` และ `a.txt` ชั่วคราวใน fixture แล้ว `hands_list` ต้อง refuse directory เพราะ case collision จากนั้นลบเฉพาะสองไฟล์นี้และบันทึกผล

## 4. Critical fallback: Hermes OFF + Codex unavailable + Hands ON

การทดสอบนี้ต้องใช้ config backup ที่ย้อนกลับได้ และไม่ส่ง Hermes/Codex task ใด ๆ:

1. หยุด Hermes API ตาม runbook ปัจจุบัน แล้วตรวจว่า `hermes_health` ล้มเหลว
2. ตั้ง `codex.binary` ชั่วคราวเป็น absolute path ที่ไม่มีอยู่จริง เช่น `/definitely-missing-codex`; restart bridge/tunnel แล้วตรวจว่า `codex_health` ล้มเหลว
3. เรียก `hands_health`, `hands_list` และ `hands_read(allowed.txt)` ซ้ำ ต้องสำเร็จทั้งหมด
4. คืน `bridge-config.json` จาก backup และ restart Hermes/bridge/tunnel; ตรวจ `./bridge.sh doctor` และ `./bridge.sh codex-doctor`

ห้าม tag/release หาก step 3 ไม่ผ่าน หรือหากการเรียก Hands ทำให้ Hermes/Codex ถูกเรียกโดยปริยาย

## 5. Cleanup และหลักฐาน

หลังคืน config และตรวจ service ปกติแล้ว ให้ลบเฉพาะ fixture ที่สร้างใน step 1 หลังตรวจค่า path ซ้ำ:

```bash
rm -rf -- "$FIXTURE"
```

บันทึกใน `docs/LIVE-ACCEPTANCE-TH.md` อย่างน้อย: วันที่, release commit, WSL/Windows/kernel, ext4 และ DrvFS mount details, 22-tool discovery, ผล deny matrix, fallback result, audit redaction check, ผู้ทดสอบ และข้อยกเว้นใด ๆ
