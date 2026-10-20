# OpenCode production benign-model acceptance

วันที่: 20 ตุลาคม 2026.
ผล: **PASS within scope** — submit/status/result, session resume, idempotent replay, result pagination และ recent ผ่าน production connector จริง.
หลักฐานมาจาก parent connector calls และการตรวจผลโดย maintainer automation; ไม่ใช่ external review.
Operator ให้ทำขั้นถัดไปหลัง merge deployment/closure record PR #54.

## Environment และขอบเขตคำขอ

Production `bridge_version` ยืนยัน `1.2.6/v1.2.6`, release-archive, embedded input `e3e698a7a220bf14a8bb4d1260bf2ded7e666b56` และ schema 1.
`opencode_health` ยืนยัน v2.0.32.
Parent registry มี 33 tools; ค่า default stamp 27 ไม่ใช่ configured discovery และไม่ใช่ raw wire capture.
ก่อนเริ่ม `opencode_recent_tasks` คืน jobs ว่าง.

ใช้ model ตาม allowlist เดิมกับ workspace ชั่วคราวที่ bridge ยอมรับ. ฉบับเผยแพร่นี้ไม่ระบุ workspace path หรือ private policy.
ไม่แก้ config หรือเพิ่ม workspace/model permissions.
งานแรกขอให้ตอบ synthetic marker ที่กำหนดไว้ล่วงหน้า. ฉบับเผยแพร่นี้ไม่แนบ prompt/output ดิบ.
Prompt ขอไม่ให้ใช้ tools, อ่าน/เขียนไฟล์ หรือเรียกคำสั่ง.
การเรียก model ใช้ provider ตาม configuration เดิม; ไม่อ้าง network isolation.

Acceptance ใช้ runtime tools และการตรวจ allowlist ตามปกติของ bridge.
ไม่มี raw config, key, DB, prompt archive หรือ raw JSONL result แนบในบันทึกนี้.

## Job evidence

| Stage | ผล |
| --- | --- |
| New session | completed / exit 0 / worker / response_completed |
| Resume | completed / exit 0 / worker / response_completed |

ทั้งสองงานใช้ session เดียวกันที่ bridge เป็นเจ้าของและ model เดิม. ฉบับเผยแพร่นี้ไม่ระบุ job/session/request IDs.
Resume ส่ง session ที่ bridge คืนมาและ workspace เดิม โดยไม่ส่ง model override.
Prompt รอบสองขอข้อความเดิมจากคำตอบก่อนหน้า; ไม่มี marker ที่คาดอยู่ใน prompt.
Text event ของทั้งสองงานตรงกับ synthetic marker แบบ exact match.
ไม่ใช้สถานะ completed เพียงอย่างเดียวเป็นหลักฐานว่า goal สำเร็จ.

## Checks

| Check | ผลที่สังเกตได้ |
| --- | --- |
| Worker lifecycle | Status ของทั้งสองงานยืนยัน exit 0, transition_actor worker, transition_reason response_completed |
| Result content | Parse text events แล้ว exact match ทั้งสองรอบ |
| Session resume | session เดียวกัน; marker ไม่อยู่ใน prompt รอบสอง |
| Idempotency | Replay แต่ละ request ด้วย input ทุก field เดิม คืน job/session เดิม; ไม่ส่ง logical task ใหม่ |
| Pagination | งานแรกอ่าน 100 + 983 ตัวอักษร ต่อกันตรงกับผลเดิม 1,083 ตัวอักษร; truncated=true แล้ว false |
| Recent | หลัง replay ทั้งสองรอบมี 2 jobs เท่านั้น ทั้งคู่ completed และ session เดียวกัน |
| Captured tool events | ไม่พบ model tool events ใน JSONL ที่อ่านจาก result ทั้งสองงาน |
| Production route | เรียก production connector โดยตรง; ไม่ใช้ fixture หรือเปลี่ยน route เป็น Dev |

Native OpenCode อาจทำ session storage และ snapshot I/O ตามปกติ.
ไม่ได้ตรวจ filesystem แบบ before/after และไม่รับรองว่าไม่มี filesystem side effects.
Workspace selection เป็น cwd allowlist ไม่ใช่ sandbox.
ข้อมูล prompt/output ใน operational store ยังเป็น plaintext ที่ป้องกันด้วย OS permissions.

## Follow-up status

ปิดงาน production OpenCode benign-model acceptance ตามขอบเขตในบันทึกนี้.
ไม่ขยายเป็น production write acceptance, cancel, timeout/cleanup, native permission handling หรือ provider/model อื่น.
หลักฐาน Dev write/cancel/permission fixtures ก่อนหน้ายังคงขอบเขตเดิม.
Privacy follow-up §19.4 ปิดแล้วใน PR #54; บันทึกนี้ไม่เปลี่ยนเงื่อนไขนั้น.
Python 3.14 truncate-race, context soft-cap/prune และ observation proposals ยังแยกติดตาม.
Local Hands mutation และ MCP Events gates ไม่เปลี่ยน.
