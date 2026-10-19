# Privacy metadata — boundary connection probe

วันที่: 19 ตุลาคม 2026.
สถานะ: เตรียม fixture และ local stdio regression แล้ว; Dev tunnel probe และ restoration รอบนี้ยังไม่ผ่านการตรวจ.
ฐาน: `f4f500967463a77adf737535825ab27bc3092fc8` หลัง merge PR #48.

## ขอบเขต

เพิ่มเฉพาะ test fixture, regression และเอกสาร. ไม่เปลี่ยน runtime, SPEC, tool schema, release หรือ production.
Fixture `tests/mock_privacy_boundary_server.py` ใช้ runtime จริงกับ in-process `httpx.MockTransport`.
ไม่มี actual Hermes HTTP, model/provider, native worker หรือ native approval ถูกเรียก.
ใช้ disposable state; ไม่อ่าน state หรือ credentials ของ deployment.

การทดสอบ cap เป็น **fault injection หลัง status filtering**.
Test-only `BoundaryBridge.status` เรียก production `Bridge.status` ก่อน แล้วเพิ่ม `fixture_padding` ให้ compact ASCII-escaped JSON มีขนาดตามเป้าหมาย.
จากนั้นเรียก production `_check_metadata_size` โดยไม่แก้ constant หรือ guard implementation.
Field นี้ไม่อยู่ใน allowlist และไม่ใช่รูปแบบที่ runtime ปกติส่งออก.
ผลทดสอบจึงพิสูจน์ size guard และการส่ง success/error ผ่าน MCP connection; ไม่พิสูจน์ว่า upstream payload ปกติสามารถผ่าน filter จนได้ขนาดดังกล่าว.
ไม่ทดสอบ boundary ของ result metadata หรือ transport envelope ทั้งก้อนในรอบนี้.

Approval cases ไม่เพิ่ม padding และผ่าน status/result implementation ปกติ.
Fake upstream ส่ง approval เป็น object, list, scalar, null และ absent โดยทุก case มีสถานะ `waiting_for_approval`.
Object มี `required: false` พร้อม synthetic command/request/description เพื่อยืนยันว่า upstream field ไม่ได้ควบคุม public approval indicator.
ทุก case ต้องส่งเพียง `approval: {required: true}` ใน status พร้อม local-review instruction; result ต้องไม่ส่ง approval payload.
นี่ไม่ใช่การยอมรับ exact local approve/deny; ข้อนั้นยังอ้าง regression ของ PR #47.
Fixture ปฏิเสธการ resolve approval หรือ stop run; ห้ามเรียกสอง action นี้เพื่อปิด synthetic pending task.

## Expected checks ผ่าน Dev connector

ก่อน submit ให้ตรวจ `bridge_version` ตรง exact fixture head ที่เตรียมบน WSL.
ใช้ request ID ใหม่เฉพาะรอบ; prompt เลือกตามตาราง.

| Prompt | Expected status response |
| --- | --- |
| `boundary-8191` | Success; compact ASCII JSON ของ structured metadata = 8,191 bytes |
| `boundary-8192` | Success; compact ASCII JSON ของ structured metadata = 8,192 bytes |
| `boundary-8193` | Tool error; ข้อความคงที่ `Hermes metadata exceeds the bridge limit.` พร้อม MCP tool-name prefix ได้; ไม่มี padding หรือ private marker ใน error |
| `approval-object`, `approval-list`, `approval-scalar`, `approval-null`, `approval-absent` | Success; status approval มีเพียง `required: true`, usage มีเพียง `total_tokens: 7`; ไม่ส่ง `PRIVATE_BOUNDARY_FIXTURE` |

สำหรับ approval cases ให้เรียก result ด้วย: ไม่มี approval/raw private marker และ explicit output ยังคง configured-key substitution.
ห้ามใช้ marker absence เป็นหลักฐาน generic secret scanning.
Tool visibility คาดว่า canonical default 27; แยก parent registry ออกจาก raw wire `tools/list`.

## Operator handoff หลังเตรียม exact head

ใช้ candidate project venv ที่ผ่าน tests บน WSL และ terminal ที่ authenticate Dev ได้อยู่แล้ว.
อย่าเริ่มก่อน parent ตรวจ jobs เดิมและเตรียม pin เสร็จ.
หยุด Dev เดิมด้วย `Ctrl+C` แล้วเปิด:

```bash
tunnel-client run --profile hermes-wsl-dev \
  --health.listen-addr 127.0.0.1:8081 \
  --mcp.command "$HOME/workspace/hermes-mcp-bridge-privacy-dev/.venv/bin/python $HOME/workspace/hermes-mcp-bridge-privacy-dev/tests/mock_privacy_boundary_server.py"
```

ไม่แก้ profile YAML. หลังทดสอบให้หยุด fixture และคืน Dev:

```bash
tunnel-client run --profile hermes-wsl-dev --health.listen-addr 127.0.0.1:8081
```

Parent ต้องตรวจ revision กลับ `e7add7e` พร้อม state/status เดิมก่อนบันทึก restoration ผ่าน.
Approval cases และ cap faults เป็น synthetic tests; อย่า approve/cancel หรือสรุปว่า production privacy rollout ผ่าน.

## หลักฐานและสิ่งที่ยังรอ

- Local SDK stdio regression ตรวจ exact 8,191/8,192 success และ 8,193 error พร้อม approval ทั้งห้ารูปแบบ.
- Focused privacy tests: 19/19 ผ่าน รวม fail-closed action assertion ใน fixture; exact-head CI และ WSL full-suite ต้องตรวจอีกครั้งก่อน live handoff.
- Dev tunnel activation, exact-head identity, live boundary/approval results และ restored-route proof ของรอบนี้ยัง pending.
- Privacy follow-up ยังเปิดจน independent review, applicable live acceptance และ release/deployment decision ผ่านตาม [SPEC.md](SPEC.md) §19.4.
- Local Hands mutation และ MCP Events gates คงเดิม. ดู [ROADMAP.md](ROADMAP.md) และ scoped acceptance รอบก่อนใน [PRIVACY-DEV-ACCEPTANCE-TH.md](PRIVACY-DEV-ACCEPTANCE-TH.md).
