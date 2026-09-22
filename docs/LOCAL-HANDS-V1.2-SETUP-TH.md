# Local Hands v1.2.0 — การเปิดใช้ read-only WSL2 Hands

สถานะ: implementation merge เข้า `main` แล้ว แต่ยังไม่ใช่ release tag  
ขอบเขต: `hands_health`, `hands_list`, `hands_read` เท่านั้น ไม่มี write, patch, shell หรือ executable

## ก่อนเปิดใช้

Local Hands ปิดเป็นค่าเริ่มต้นเสมอ แม้ upgrade bridge แล้วก็ตาม และไม่สร้าง workspace ให้เอง
เลือกเฉพาะ workspace ที่เป็น disposable project หรือเป็นโฟลเดอร์งานที่ยอมให้ส่งชื่อไฟล์และเนื้อหา UTF-8 ที่ไม่เป็นความลับไปยัง ChatGPT ได้

ห้ามตั้ง workspace เป็น home directory, credential directory หรือโฟลเดอร์ที่มีข้อมูลที่ไม่ควรเปิดเผยทั้งก้อน

## Config

เพิ่ม block นี้ใน `bridge-config.json` โดยใช้ absolute Linux path และเปลี่ยน path ให้ตรงเครื่องของตนเอง:

```json
{
  "hands": {
    "enabled": true,
    "workspaces": [
      {
        "name": "sample-project",
        "path": "/home/somchaip/work/sample-project"
      }
    ],
    "max_read_bytes": 65536,
    "max_read_chars": 65536,
    "max_list_entries": 200,
    "protected_name_patterns": [
      "customer-export-*.csv"
    ],
    "protected_paths": [
      "/home/somchaip/work/sample-project/private-fixtures"
    ]
  }
}
```

`protected_name_patterns` และ `protected_paths` เป็นการเพิ่มรายการป้องกันเท่านั้น ลบ baseline ไม่ได้ โดย baseline ครอบคลุม `.env*`, key/certificate ที่พบบ่อย, `id_rsa*`, `id_ed25519*`, และ `credentials*.json` ทุกตัวพิมพ์เล็ก/ใหญ่ รวมถึง credential directories ใต้ home เช่น `.ssh`, `.aws`, `.gnupg` และ `.kube`

## ตรวจและใช้งาน

1. Restart bridge/tunnel หลังแก้ config
2. รัน `./bridge.sh hands-doctor`
3. `hands_health` ต้องรายงาน workspace เป็น `available` จึงเรียก `hands_list` หรือ `hands_read` ได้

ตัว resolver ต้องใช้ Linux `openat2` แบบ descriptor-relative พร้อม `RESOLVE_BENEATH`, `RESOLVE_NO_SYMLINKS` และ `RESOLVE_NO_MAGICLINKS` หาก kernel/filesystem ใช้ไม่ได้ workspace จะเป็น `unavailable`; bridge จะไม่ fallback ไปตรวจ path แล้วเปิดไฟล์ภายหลัง

เมื่อ `hands.enabled=false` หรือไม่มี `hands` block ทั้งสาม tools ยัง discover ได้: `hands_health` คืน status `disabled` และ `hands_list`/`hands_read` คืน `{ "ok": false, "status": "disabled", "error_code": "disabled" }`

## ข้อจำกัดความปลอดภัย

- อ่านได้เฉพาะ regular file UTF-8 ที่มี hard link เดียว, ไม่มี NUL และไม่เกิน limit
- symlink, special file, traversal, protected path/name และ directory ที่มีชื่อชนกันต่างเฉพาะตัวพิมพ์ จะถูกปฏิเสธหรือไม่ถูกแสดง
- audit บันทึกเฉพาะ metadata เช่นจำนวน byte/entry ไม่บันทึก path, ชื่อไฟล์ หรือเนื้อหา
- การกรองชื่อไฟล์ช่วยลดความเสี่ยง แต่ไม่ทำให้ workspace เป็นแหล่งข้อมูลปลอด secret โดยอัตโนมัติ; เลือก workspace อย่างระมัดระวัง

การทดสอบ live บน WSL2/ext4 และ DrvFS รวมถึงกรณี Hermes/Codex unavailable ยังเป็น release gate ของ v1.2.0 ตาม [runbook live acceptance](LOCAL-HANDS-V1.2-LIVE-ACCEPTANCE-TH.md) และ [แผน implementation](LOCAL-HANDS-IMPLEMENTATION-PLAN-TH.md)
