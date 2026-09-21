# Release integrity runbook — v1.0.0

## ผู้สร้าง release

1. รัน test และ acceptance checklist ตาม `V1-ACCEPTANCE-TH.md`.
2. สร้าง archive โดยมี root directory เดียวชื่อ `hermes-mcp-bridge-vX.Y.Z/`; ต้อง exclude `.git/`, `.venv/`, `__pycache__/`, `state/`, `.env` และ `bridge-config.json*`.
3. สร้าง `SHA256SUMS` ด้วย `sha256sum hermes-mcp-bridge-vX.Y.Z.zip > SHA256SUMS` แล้วตรวจไฟล์ด้วย `sha256sum -c SHA256SUMS`.
4. commit source และ `SHA256SUMS`, แล้วลง signed tag ด้วย GPG key ของ maintainer:

```bash
git tag -s vX.Y.Z -m "hermes-mcp-bridge vX.Y.Z"
git verify-tag vX.Y.Z
git push origin main vX.Y.Z
```

ห้ามแทน `-s` ด้วย unsigned tag ใน release ที่อ้างว่า production baseline. การลงนามเป็นสิทธิ์ของ maintainer เท่านั้น; bridge ไม่เก็บหรือใช้ private signing key.

## ผู้ติดตั้ง

```bash
sha256sum -c SHA256SUMS
unzip -l hermes-mcp-bridge-vX.Y.Z.zip | head
```

รายการแรกต้องเป็น `hermes-mcp-bridge-vX.Y.Z/` และต้องไม่พบ `.venv/`, `state/`, `.env` หรือ `bridge-config.json`. เมื่อรับ public key ของ maintainer แล้วให้ตรวจ tag:

```bash
git fetch --tags
git verify-tag vX.Y.Z
```

หลังตรวจผ่านจึงแตก archive และทำ upgrade ตาม `UPGRADE-TH.md`.
