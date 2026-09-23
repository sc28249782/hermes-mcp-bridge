# Release integrity runbook

## ผู้สร้าง release

### Phase A — ก่อนสร้าง signed tag

1. **Documentation gate:** ทบทวนเอกสารที่อธิบาย source, tool discovery, configuration, acceptance, compatibility, roadmap และ upgrade ให้ตรงกับ release candidate. Release status ต้องระบุผล acceptance และ provenance ได้ แต่ให้ใช้สถานะ `tag pending` จนกว่าจะ verify asset จริง. สำหรับ v1.2.2 ให้ตรวจ `./bridge.sh version` และ MCP `bridge_version` ตรงกัน, discovery count ตรง, และไม่มี upstream/network call.
2. Commit เอกสาร Phase A และตรวจ `git diff --check`; รัน test และ acceptance checklist ตาม `V1-ACCEPTANCE-TH.md`.
3. ตรวจ release checkout ให้สะอาด, ยืนยัน target commit และ version tag ยังไม่มีอยู่, แล้วตรวจว่า WSL มี private GPG key ที่ตรงกับ `user.signingkey`:

```bash
set -euo pipefail
test -z "$(git status --short)"
git config --show-origin --get user.signingkey
gpg --list-secret-keys --keyid-format=long
git ls-remote --exit-code --tags origin "refs/tags/vX.Y.Z" && exit 1 || true
```

4. หาก release ใช้ embedded provenance ให้ stamp `version_info.py` ด้วย release identifier/build provenance ตาม release candidate ที่ review แล้ว; ห้ามใช้ `.git` เป็นเงื่อนไขให้ archive ทำงานได้. ตรวจ output `./bridge.sh version` อีกครั้งก่อน tag.

5. สร้างและตรวจ signed tag ก่อน push:

```bash
git tag -s vX.Y.Z -m "hermes-mcp-bridge vX.Y.Z"
git verify-tag vX.Y.Z
git push origin main vX.Y.Z
```

ห้ามแทน `-s` ด้วย unsigned tag ใน production release. GitHub authentication token ไม่ใช่ GPG private key และห้ามใส่ private key/passphrase ใน bridge, chat, command history หรือ log.

### Phase B — สร้างและตรวจ release assets จาก signed tag

6. สร้าง archive จาก tag โดยมี root directory เดียวชื่อ `hermes-mcp-bridge-vX.Y.Z/`; ต้อง exclude `.git/`, `.venv/`, `__pycache__/`, `state/`, `.env` และ `bridge-config.json*`.
7. สร้าง `SHA256SUMS` เป็น **external release asset** หลังสร้าง archive, แล้วตรวจทั้ง non-empty archive, ZIP structure และ checksum:

```bash
RELEASE_DIR="$(mktemp -d)"
ZIP="$RELEASE_DIR/hermes-mcp-bridge-vX.Y.Z.zip"
git archive --format=zip --prefix="hermes-mcp-bridge-vX.Y.Z/" -o "$ZIP" vX.Y.Z
test -s "$ZIP"
unzip -t "$ZIP"
(cd "$RELEASE_DIR" && sha256sum "$(basename "$ZIP")" > SHA256SUMS)
(cd "$RELEASE_DIR" && sha256sum -c SHA256SUMS)
```

ห้าม commit checksum ของ archive ปัจจุบันลง source tree ก่อนสร้าง archive: archive ที่บรรจุ checksum ของตัวเองเป็น self-reference. Root `SHA256SUMS` ไม่ใช่ authoritative manifest สำหรับ release ใหม่; ให้แนบ `SHA256SUMS` เป็น asset เดียวกับ ZIP.

8. สร้าง GitHub Release พร้อม ZIP และ `SHA256SUMS`. หากทำงานนอก Git checkout ต้องระบุ `--repo owner/repo` กับ `gh release`.
9. ดาวน์โหลด asset จาก GitHub ลง directory ใหม่ แล้วรัน `sha256sum -c SHA256SUMS` และ `unzip -t` ซ้ำก่อนประกาศ release สำเร็จ.

### Phase C — release record หลัง tag

10. เปิด release-record commit/PR หลัง Phase B ผ่าน เพื่อบันทึก tag target, signer verification, archive checksum และผล post-download verification ใน changelog, release status และ live acceptance. Commit นี้ไม่แก้ tag หรือ release assets และเป็นเอกสารประวัติหลัง release โดยเจตนา.

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
