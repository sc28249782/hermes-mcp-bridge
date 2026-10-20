# Privacy metadata — boundary connection probe

เตรียม: 19 ตุลาคม 2026. Dev transport probe: 20 ตุลาคม 2026 (~10:13 +07).
สถานะ: Dev transport ผ่านตามขอบเขต fixture/fault injection; restoration รอบนี้ยังรอตรวจ.
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
- Candidate `f570d03f998657a11fe77069120175030cc3c0d3`: WSL full suite 184/184, exit 0; focused privacy 19/19, shellcheck, Bash syntax และ whitespace checks ผ่าน. Code-head CI [39271455485](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/39271455485) ผ่าน. หลักฐานเป็น maintainer automation ไม่ใช่ external review.
- Dev tunnel activation, exact-head identity และ live boundary/approval checks ผ่านตามตารางด้านล่าง; restored-route proof ยัง pending.
- Privacy follow-up ยังเปิดจน independent review, applicable live acceptance และ release/deployment decision ผ่านตาม [SPEC.md](SPEC.md) §19.4.
- Local Hands mutation และ MCP Events gates คงเดิม. ดู [ROADMAP.md](ROADMAP.md) และ scoped acceptance รอบก่อนใน [PRIVACY-DEV-ACCEPTANCE-TH.md](PRIVACY-DEV-ACCEPTANCE-TH.md).

## Dev connector checkpoint — scoped PASS (20 ตุลาคม 2026)

Operator เปิด fixture ผ่าน ephemeral command override; parent เรียก Dev connector จริงผ่าน Secure MCP Tunnel.
Identity ตรง `f570d03f998657a11fe77069120175030cc3c0d3`, source `git-worktree`.
Inherited stamp `1.2.5/v1.2.5` ไม่ใช่ release ใหม่.
Root config schema เป็น `unknown` เพราะ fixture ไม่มี root config file; embedded schema 1.
Parent registry มี 27 tools และ version รายงาน canonical default 27; ไม่ใช่ raw wire `tools/list` และไม่อ้าง live 28/33.

| Case | Run | ผลจาก connection จริง |
| --- | --- | --- |
| `boundary-8191` | `run_1` | Success; structured metadata เป็น ASCII JSON 8,191 bytes |
| `boundary-8192` | `run_2` | Success; structured metadataเป็น ASCII JSON 8,192 bytes |
| `boundary-8193` | `run_3` | `isError: true`; constant limit error พร้อม tool-name prefix และ connector `error_code: INVALID_ARGUMENT`; ไม่ส่ง padding/private marker |
| `approval-object` | `run_4` | Status/result ผ่าน checks ของ approval matrix |
| `approval-list` | `run_5` | Status/result ผ่าน checks ของ approval matrix |
| `approval-scalar` | `run_6` | Status/result ผ่าน checks ของ approval matrix |
| `approval-null` | `run_7` | Status/result ผ่าน checks ของ approval matrix |
| `approval-absent` | `run_8` | Status/result ผ่าน checks ของ approval matrix |

วัดขนาดด้วย compact JSON ของ structured status metadata; ตรวจแล้วว่าทุกอักขระเป็น ASCII.
ไม่ได้วัดขนาด MCP envelope หรือ duplicated text representation.
Approval ทั้งห้า cases ได้สถานะ `waiting_for_approval`, approval มีเพียง `required: true`, usage มีเพียง `total_tokens: 7`, error เป็นข้อความคงที่ และมี local-review instruction.
ไม่พบ `fixture_padding` ใน approval status, ไม่พบ approval payload ใน result และไม่พบ synthetic private marker ใน status/result ที่ตรวจ.
Output ตรงกับ expected configured-key-substituted fixture output ทั้งห้า cases; ไม่เผยแพร่ raw result เป็นหลักฐาน.
ไม่มีการ approve/cancel และไม่มี native worker/model ถูกเริ่ม.

Boundary PASS นี้เป็น post-filter fault injection เข้า production size guard ตามขอบเขตด้านบน.
Approval PASS ใช้ in-process fake upstream; ไม่ใช่ actual Hermes HTTP หรือ native permission/approval acceptance.
ผลไม่ได้เปลี่ยน release, production, directory-repair หรือ Codex read-cap acceptance scope.

**Restoration ยัง pending:** operator ต้องคืน Dev โดยไม่ใส่ override แล้ว parent ตรวจ pin `e7add7e` และสถานะเดิม.
Privacy follow-up ยังเปิดรอ restoration, independent review และ release/deployment decision.
