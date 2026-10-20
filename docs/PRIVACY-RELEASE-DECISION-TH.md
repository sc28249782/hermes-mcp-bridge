# Privacy hardening — release scope ที่ได้รับอนุมัติ

วันที่: 20 ตุลาคม 2026.
สถานะ: operator อนุมัติ scope สำหรับ release preparation แล้วเมื่อ 20 ตุลาคม 2026 เวลา 11:26 +07.
รุ่นเป้าหมาย: `v1.2.6`. ยังไม่ stamped, tagged, published หรือ deployed.
เอกสารตั้งต้น: `290a9d6a98182a4b248de349d2ad2f4383860518` หลัง merge PR #49.

## Operator decision

Operator ยืนยันในแชตว่า “อนุมัติ scope v1.2.6 และอัปเดตเอกสารที่เกี่ยวข้องด้วย”.
จึงกำหนด privacy hardening ตาม SPEC §4/§10/§19 เป็น scope ของ maintenance release เป้าหมาย `v1.2.6`.
Scope คือ implementation จาก PR #47 และ regression/acceptance จาก PR #48/#49.
การอนุมัติครอบคลุม scope และลำดับ release preparation ตาม PR #50 ที่ผ่าน review แล้ว.
ขั้นถัดไปคือ release-preparation PR พร้อม stamp และ exact-head verification ตาม runbook.
การอนุมัติ scope ไม่ครอบคลุม signed tag, publish assets หรือ production upgrade.
Privacy follow-up ยังเปิดสำหรับ release verification และ deployment decision; operator ต้องยืนยันสองส่วนนี้ก่อนปิดตาม §19.4.

| รายการ | Decision / สถานะ |
| --- | --- |
| Release scope | Hermes metadata allowlist/cap, directory-mode enforcement และ bounded Codex result reads |
| Contract | ใช้ wording และ limits ที่ผ่าน review ใน SPEC §4/§10/§19 |
| Target version | Operator อนุมัติ `v1.2.6` เป็นรุ่นเป้าหมาย; stamp และ archive verification อยู่ใน release-preparation PR |
| Production | คง deployment เดิมระหว่าง preparation; checkpoint ล่าสุดที่บันทึกไว้คือ signed v1.2.5 |
| Local Hands / MCP Events | คง hard gates เดิม; ไม่อยู่ใน release scope |

## SPEC §14 — change-control record

Privacy review PR #46 ระบุว่า blanket full-output prohibition ไม่ตรงกับ explicit result APIs และ private operational storage ที่มีอยู่.
จึงถือ wording ใน §4/§10 เป็น security-contract amendment แม้ไม่เพิ่ม backend permissions.
SPEC §19 กำหนด behavior และ limits ก่อน merge implementation.

ลำดับ commit ที่ตรวจจาก PR #47:

1. `7781d98093679017bc1e2c8ffdab7a582fc874ff`: เพิ่ม SPEC และ unreleased contract note.
2. `3af56652c5f32645123615149f024dc77726920e`: แก้ Hermes runtime.
3. `ca08d74995238daa6f387f0e5d7c1e2c7eb7dade`: แก้ Codex runtime.

Reviewer อนุมัติ contract/implementation ที่ `c14cd8c` ใน PR #47.
ลำดับ commit ข้างต้นยืนยันว่าเพิ่ม SPEC ก่อนแก้ runtime ตามข้อกำหนด spec-first แล้ว.
บันทึกนี้รวมผลรีวิวที่เสร็จสิ้นแล้วและ operator scope decision.
ไม่เปลี่ยน MUST/MAY, allowlist, limits, permissions หรือ acceptance requirements ใน §19.

## หลักฐานและขอบเขตที่ review แล้ว

| Requirement | หลักฐาน | ขอบเขต |
| --- | --- | --- |
| Metadata field/value allowlist และ constant error/approval indicator | PR #47: external source/probe review; PR #49: approval object/list/scalar/null/absent ผ่าน status/result | Live Dev ใช้ fake upstream ใน process; ไม่ใช่ actual Hermes HTTP หรือ native approval |
| Metadata cap ≤ 8,192 bytes | PR #49 code head `f570d03`: 8,191/8,192 success และ 8,193 constant error ผ่าน actual Dev connector | Post-filter fault injection เข้า production guard; ไม่ใช่ natural upstream path, result-metadata boundary หรือ whole-envelope cap |
| Existing-directory repair และ failure handling | PR #47: tests บน filesystem และ independent existing-directory probe | ไม่อ้าง live repair ของ production state |
| Codex snapshot/read budgets และ pagination | PR #47: sparse/exact-cap logs, append/truncate, Unicode/newline/invalid UTF-8 และ tracked read sizes | Filesystem regression/probes; ไม่ใช่ live Codex result-cap probe ผ่าน tunnel |
| Regression suite | PR #49 code head `f570d03`: WSL 184/184, focused privacy 19/19 และ external reviewer rerun | ใช้ synthetic fixtures; ไม่มี production model task |
| Scoped Dev transport / restoration | PR #48 final `3004653b`; PR #49 final `04a0616`, CI `39363590669`, external APPROVE | คืน Dev pin `e7add7e`, schema 1, Hermes/Codex 0 registrations, mode 0700, watchdog และ Hands disabled; ไม่ recheck OpenCode count เพราะ tool ไม่อยู่ใน parent registry |

Operator ส่งรายงาน external review ที่อ้างในตารางมาในแชต.
External reviewer เป็นผู้ให้ verdict `APPROVE` สำหรับขอบเขตที่ระบุในแต่ละรายงาน.
ไม่ใช่การเรียกผล maintainer automation ว่า external review.
รายละเอียด: [PRIVACY-CONTRACT-REVIEW-TH.md](PRIVACY-CONTRACT-REVIEW-TH.md), [PRIVACY-DEV-ACCEPTANCE-TH.md](PRIVACY-DEV-ACCEPTANCE-TH.md) และ [PRIVACY-BOUNDARY-ACCEPTANCE-TH.md](PRIVACY-BOUNDARY-ACCEPTANCE-TH.md).

## Compatibility และ privacy disclosure

- Status/result metadata ไม่ส่ง raw Hermes error หรือ approval request อีกต่อไป. Client/operator ที่ใช้ข้อความเดิมต้องเปลี่ยนไปใช้ constant error และ local terminal review.
- Public approval indicator ไม่ใช่ authorization. Exact approve/deny ยังคง fetch และ revalidate request ใน local terminal.
- Result/file content เป็น untrusted content และอาจมีข้อมูลอ่อนไหว. หน้าเดียวอาจมี output สั้นครบทั้งชิ้น. Pagination ไม่ใช่ redaction.
- Prompt/output ใน operational stores ยังคงเป็น plaintext ที่ป้องกันด้วย OS permissions. ไม่มี at-rest encryption, generic secret scanner หรือ automatic artifact cleanup เพิ่ม.
- Directory เดิมต้องเปลี่ยนเป็น mode 0700 ได้. Init จะ fail closed หากทำไม่ได้; operator ต้องแก้สิทธิ์ก่อนรัน bridge ใหม่.
- Codex result snapshot เกิน 8,388,608 bytes จะคืน error ให้ตรวจในเครื่อง. Cap นี้ไม่จำกัด worker log capture, disk growth หรือ filesystem-call duration.
- HTTP cap 4,000,000 decoded bytes และ connect/inactivity timeouts 5/25 วินาทียังคงเดิม. ไม่ใช่ total wall-clock deadline.
- Tool/schema/config permissions ไม่เพิ่ม. Default discovery ยังคง 27; OpenCode health/execution opt-ins ยังคง 28/33 ตาม configuration เดิม.
- Native session storage, same-user process access และ backend/provider data handling คงขอบเขตเดิม. ไม่อ้าง sandbox หรือ filesystem/network confinement ใหม่.

## ขั้นตอนหลัง scope ได้รับอนุมัติ

1. เปิด release-preparation PR จาก main ที่มี decision record ผ่าน review แล้ว. กำหนด version/stamp และ reviewed build-input revision ตาม [RELEASE-RUNBOOK-TH.md](RELEASE-RUNBOOK-TH.md). อย่าใช้ build-input เป็น final tag identity.
2. ทบทวน README, installation, operations, compatibility, testing, roadmap, upgrade, security และ release notes ให้ตรง candidate ก่อน tag. คง signed/historical records เดิม.
3. รัน full suite, shellcheck, Bash syntax และ discovery 27/28/33 บน exact candidate. สร้าง candidate archive ชั่วคราวและตรวจ layout, CLI/MCP identity parity, provenance และการทำงานโดยไม่มี `.git`. บันทึกผลตามขอบเขต; ห้ามเรียก candidate archive ว่า signed release.
4. ส่ง exact-head release-preparation evidence ให้ review. หาก source/runtime/contract เปลี่ยน ให้ทบทวน acceptance ที่ได้รับผลกระทบก่อนเดินต่อ. หยุดเมื่อ verification ไม่ผ่าน.
5. เมื่อ operator อนุมัติ final target และ signing/publish แล้ว ให้ทำ Phase A/B ตาม runbook. ใช้ GPG private key ผ่าน operator terminal. ห้ามส่ง key/passphrase เข้า chat หรือ bridge.
6. สร้าง final archive จาก signed tag. ตรวจ signature, peeled commit, ZIP, external checksum และ fresh-download byte comparison ก่อนประกาศ released. ถ้าตรวจไม่ผ่าน ให้หยุด; ห้ามแทน tag ที่เผยแพร่แล้ว.
7. เปิด Phase C release-record PR. บันทึก tag authority, build input, assets และผล verification โดยไม่แก้ signed tag/assets.
8. ทำ production upgrade เฉพาะเมื่อ operator อนุมัติ deployment แยก. Backup config/state ตาม private permissions. ตรวจไม่มี active jobs ก่อนหยุด instance และเก็บไดเรกทอรีเดิมไว้ใช้ rollback.
9. ตรวจ deployed archive identity/stamp, config, state/log modes, health และ configured discovery. บันทึก applicable privacy acceptance ด้วย synthetic data ใน isolated state. การตรวจ identity/health อย่างเดียวไม่ใช่ production model-task acceptance. หากผิด target หรือ acceptance ไม่ผ่าน ห้ามเริ่มงานใหม่ และให้คืน deployment เดิมตาม upgrade runbook.
10. บันทึก release/deployment decision และผล acceptance ที่ตรวจสอบได้จริงก่อนปิด privacy follow-up ตาม §19.4. หากเลือกยังไม่ deploy ให้ระบุ decision นั้นชัดเจนและคงสถานะ production acceptance ตามหลักฐานจริง.

Production OpenCode benign-model acceptance ยังคงเป็น follow-up แยก.
Local Hands mutation/execution และ MCP Events subscription gate ไม่ถูกปลดล็อกด้วย release นี้.
