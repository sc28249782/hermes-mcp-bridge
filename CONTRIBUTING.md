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

1. รัน test suite ทั้งหมด
2. ตรวจ `bash -n install.sh bridge.sh tunnel.sh`
3. ตรวจว่า archive ไม่มี secrets/state/logs
4. ทำ live acceptance ตาม `RELEASE-STATUS-TH.md`
5. อัปเดต CHANGELOG และสร้าง signed/annotated tag ตามนโยบายผู้ดูแล
