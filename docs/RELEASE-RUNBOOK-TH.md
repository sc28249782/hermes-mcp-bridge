# Release integrity runbook

## ผู้สร้าง release

### Phase A — ก่อนสร้าง signed tag

ในตัวอย่างทุกคำสั่ง ให้แทน `vX.Y.Z` ด้วย tag ของรุ่นที่จะเผยแพร่ก่อนรัน ใช้ shell เดียวกันจาก release checkout ที่ operator เลือก

1. **Documentation gate:** ทบทวนเอกสารที่อธิบาย source, tool discovery, configuration, acceptance, compatibility, roadmap และ upgrade ให้ตรงกับ release candidate. Release status ต้องระบุผล acceptance และ provenance ได้ แต่ให้ใช้สถานะ `tag pending` จนกว่าจะ verify asset จริง. สำหรับ candidate ทุกรุ่น ให้ตรวจ `./bridge.sh version` และ MCP `bridge_version` ตรงกัน, discovery count ตรง, และไม่มี upstream/network call.
2. Commit เอกสาร Phase A และตรวจ `git diff --check`; รัน test และ acceptance checklist ตาม `V1-ACCEPTANCE-TH.md`.
3. ตรวจ release checkout ให้สะอาด, ยืนยัน target commit และ version tag ยังไม่มีอยู่, แล้วตรวจว่า WSL มี private GPG key ที่ตรงกับ `user.signingkey` รันทุกขั้นใน shell เดียวกัน:

   1. เปิด fail-fast สำหรับ shell นี้:

      ```bash
      set -euo pipefail
      ```

   2. ต้องจบด้วย exit code 0 ถ้าไม่ใช่ 0 ให้หยุดแล้วตรวจ `git status --short` ก่อนดำเนินการต่อ:

      ```bash
      test -z "$(git status --short)"
      ```

   3. ตรวจค่า `user.signingkey` ถ้ามี โดยยอมรับเฉพาะกรณีไม่พบ key (exit 1) เป็นค่าที่ยังไม่ได้ตั้ง:

      ```bash
      git config --show-origin --get user.signingkey || test "$?" -eq 1
      ```

   4. ตรวจว่ามี private key ตรงกับ fingerprint ที่อนุมัติ:

      ```bash
      gpg --list-secret-keys --keyid-format=long
      ```

   5. ตรวจ tag บน origin: อนุญาตให้ไปต่อเฉพาะ exit 2 ซึ่งหมายถึงไม่พบ tag ที่ระบุ หากพบ tag หรือเกิด network error ให้หยุด:

      ```bash
      if git ls-remote --exit-code --tags origin "refs/tags/vX.Y.Z"; then
        printf '%s\n' 'Tag already exists; stop without replacing it.' >&2
        exit 1
      else
        bridge_tag_status=$?
        test "$bridge_tag_status" -eq 2 || exit "$bridge_tag_status"
      fi
      ```

4. หาก release ใช้ embedded provenance ให้ stamp `version_info.py` ด้วย release identifier/build provenance และ **build-input revision** ตาม release candidate ที่ review แล้ว; build-input revision บอก source ที่ใช้เตรียม stamp ไม่ใช่การอ้างว่าเป็น final tag commit (ซึ่งเป็น self-reference ไม่ได้). signed tag คือ authority ของ final commit. ห้ามใช้ `.git` เป็นเงื่อนไขให้ archive ทำงานได้. ตรวจ output `./bridge.sh version` อีกครั้งก่อน tag.

5. เลือก signing key ที่ operator อนุมัติ แล้วทำขั้นตอนต่อไปนี้ใน shell เดิม:

   1. กำหนด fingerprint ของ key ที่จะใช้ ตัวอย่างนี้ใช้ key ของ maintainer ที่ตรวจแล้วสำหรับ v1.2.5 หากใช้ key อื่น ต้องให้ operator ตรวจและอนุมัติ fingerprint ก่อน:

      ```bash
      BRIDGE_SIGNING_FINGERPRINT='C4E9AFA9C97FC94CA2448E9218BDAEA561529B86'
      ```

   2. แทน `REPLACE_WITH_REVIEWED_COMMIT_SHA` ด้วย full SHA ของ commit ที่ผ่าน review และอยู่บน origin/main แล้ว:

      ```bash
      BRIDGE_RELEASE_COMMIT='REPLACE_WITH_REVIEWED_COMMIT_SHA'
      ```

   3. ตรวจว่า commit มีอยู่และ SHA ที่แสดงตรงกับ commit ที่อนุมัติ หากไม่ตรงให้หยุด:

      ```bash
      git rev-parse --verify "${BRIDGE_RELEASE_COMMIT}^{commit}"
      ```

   4. ตรวจว่า SHA ของ origin/main ตรงกับ commit ที่อนุมัติ หากคำสั่งล้มเหลวหรือ SHA ไม่ตรงให้หยุด:

      ```bash
      test "$(git ls-remote --exit-code origin refs/heads/main | cut -f1)" = "$BRIDGE_RELEASE_COMMIT"
      ```

   5. สร้าง signed tag จาก commit นี้โดยระบุ key ชัดเจน:

      ```bash
      git -c user.signingkey="$BRIDGE_SIGNING_FINGERPRINT" tag -s vX.Y.Z "$BRIDGE_RELEASE_COMMIT" -m "hermes-mcp-bridge vX.Y.Z"
      ```

   6. ตรวจว่าเป็น `Good signature` จาก fingerprint ที่อนุมัติ หากไม่ตรงให้หยุดและไม่ push:

      ```bash
      git verify-tag vX.Y.Z
      ```

   7. ตรวจ peeled commit ให้ตรงกับ `BRIDGE_RELEASE_COMMIT`:

      ```bash
      test "$(git rev-parse 'vX.Y.Z^{commit}')" = "$BRIDGE_RELEASE_COMMIT"
      ```

   8. Push เฉพาะ tag นี้เมื่อการตรวจทั้งหมดผ่านแล้ว:

      ```bash
      git push origin vX.Y.Z
      ```

ห้ามแทน `-s` ด้วย unsigned tag ใน production release. GitHub authentication token ไม่ใช่ GPG private key และห้ามใส่ private key/passphrase ใน bridge, chat, command history หรือ log.

### Phase B — สร้างและตรวจ release assets จาก signed tag

6. สร้าง archive จาก tag โดยมี root directory เดียวชื่อ `hermes-mcp-bridge-vX.Y.Z/`; ต้อง exclude `.git/`, `.venv/`, `__pycache__/`, `state/`, `.env` และ `bridge-config.json*`.
7. สร้าง `SHA256SUMS` เป็น **external release asset** หลังสร้าง archive, แล้วตรวจทั้ง non-empty archive, ZIP structure และ checksum รันทุกขั้นใน shell เดียวกัน:

   1. เตรียม directory ชั่วคราว:

      ```bash
      RELEASE_DIR="$(mktemp -d)"
      ```

   2. กำหนดตำแหน่ง ZIP:

      ```bash
      ZIP="$RELEASE_DIR/hermes-mcp-bridge-vX.Y.Z.zip"
      ```

   3. สร้าง archive จาก tag:

      ```bash
      git archive --format=zip --prefix="hermes-mcp-bridge-vX.Y.Z/" -o "$ZIP" vX.Y.Z
      ```

   4. ต้องจบปกติโดยไม่มี output (archive ไม่ว่าง):

      ```bash
      test -s "$ZIP"
      ```

   5. ตรวจ ZIP structure; ต้องจบด้วย `No errors detected in compressed data`:

      ```bash
      unzip -t "$ZIP"
      ```

   6. สร้าง checksum เป็น external asset:

      ```bash
      (cd "$RELEASE_DIR" && sha256sum "$(basename "$ZIP")" > SHA256SUMS)
      ```

   7. ต้องรายงาน `OK`:

      ```bash
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

1. ตรวจ checksum ก่อนแตกไฟล์; ต้องรายงาน `OK`:

   ```bash
   sha256sum -c SHA256SUMS
   ```

2. ตรวจ layout ของ archive:

   ```bash
   unzip -Z1 hermes-mcp-bridge-vX.Y.Z.zip
   ```

ทุกรายการต้องอยู่ใต้ `hermes-mcp-bridge-vX.Y.Z/` และต้องไม่พบ `.venv/`, `state/`, `.env` หรือ `bridge-config.json`. เมื่อรับ public key ของ maintainer แล้วให้ตรวจ tag:

1. ดึง tag ลงเครื่อง:

   ```bash
   git fetch --tags
   ```

2. ต้องแสดง `Good signature`:

   ```bash
   git verify-tag vX.Y.Z
   ```

หลังตรวจผ่านจึงแตก archive และทำ upgrade ตาม `UPGRADE-TH.md`.
