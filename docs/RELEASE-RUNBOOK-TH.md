# Release integrity runbook — v1.0.1

## ผู้สร้าง release

1. **Documentation gate (ต้องผ่านก่อน tag/release):** ทบทวนเอกสารทั้งหมดที่อธิบายรุ่นปัจจุบัน—อย่างน้อย README, installation/developer guide, architecture, operations, Codex policy, upgrade, testing, acceptance, compatibility matrix, changelog, release status/runbook, roadmap และ project history—ให้ตรงกับ source, tool discovery, live acceptance, version, package name และ checksum ที่จะเผยแพร่. คงข้อความของ release เก่าไว้เฉพาะส่วนที่ระบุชัดว่าเป็นประวัติหรือเส้นทาง upgrade.
2. Commit การอัปเดตเอกสารและตรวจ `git diff --check`; **ห้าม** สร้าง archive, signed tag หรือ GitHub Release หาก documentation gate ยังไม่ผ่าน.
3. รัน test และ acceptance checklist ตาม `V1-ACCEPTANCE-TH.md`.
4. สร้าง archive โดยมี root directory เดียวชื่อ `hermes-mcp-bridge-vX.Y.Z/`; ต้อง exclude `.git/`, `.venv/`, `__pycache__/`, `state/`, `.env` และ `bridge-config.json*`.
5. สร้าง `SHA256SUMS` ด้วย `sha256sum hermes-mcp-bridge-vX.Y.Z.zip > SHA256SUMS` แล้วตรวจไฟล์ด้วย `sha256sum -c SHA256SUMS`.
6. commit source และ `SHA256SUMS`, แล้วลง signed tag ด้วย GPG key ของ maintainer:

```bash
git tag -s vX.Y.Z -m "hermes-mcp-bridge vX.Y.Z"
git verify-tag vX.Y.Z
git push origin main vX.Y.Z
```

ห้ามแทน `-s` ด้วย unsigned tag ใน release ที่อ้างว่า production baseline. การลงนามเป็นสิทธิ์ของ maintainer เท่านั้น; bridge ไม่เก็บหรือใช้ private signing key.

## บันทึก v1.0.1

`v1.0.1` ถูกลงนามและ GitHub ยืนยัน signature แล้ว โดยชี้ commit `cbbdd4d6124e3673dccc7a5ae010c0054b2df832`. Release archive `hermes-mcp-bridge-v1.0.1.zip` ผ่าน `sha256sum -c` ด้วย SHA-256 `a20a07aaeb0baeb885c85223dab9eba61c8a0ce1be20bb83d0e422faaa45c9d3`.

## บันทึก v1.0.0

`v1.0.0` ถูกลงนามและ GitHub ยืนยัน signature แล้ว โดยชี้ commit `2b280b2d3a763f69afa417bc76bdca6b801553fc`. Archive `hermes-mcp-bridge-v1.0.0.zip` มี SHA-256 `04421690f877807975810dfeffb29ec6412d8313103409cfd5713300e32de793`.

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
