# Contributing

## Development setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

## Pull requests

- อย่า commit `bridge-config.json`, `.env`, API keys, tunnel keys, `state/`, logs หรือ virtual environments
- รักษา backward compatibility ของ Hermes tools เดิม
- การเพิ่ม write-capable tool ต้องมี explicit ownership check, local approval policy และ negative tests
- อัปเดต README, CHANGELOG, UPGRADE และ architecture documentation เมื่อ behavior เปลี่ยน
- ทุก PR ต้องผ่าน unit tests, MCP stdio integration และ shell syntax check

## Release checklist

1. **Documentation gate ก่อน tag/release:** ทบทวนและอัปเดตเอกสารทุกฉบับที่อธิบายรุ่นปัจจุบันให้ตรงกับ source, tools, behavior, live acceptance, version, package และ checksum; commit เอกสารให้เรียบร้อยก่อนเริ่มสร้าง archive หรือ tag
2. รัน test suite ทั้งหมด
3. ตรวจ `bash -n install.sh bridge.sh tunnel.sh`
4. ตรวจว่า archive ไม่มี secrets/state/logs
5. ทำ live acceptance ตาม `RELEASE-STATUS-TH.md`
6. ตรวจ `git diff --check`, checksum และ archive layout; production release ต้องใช้ signed tag ที่ maintainer ตรวจสอบได้
