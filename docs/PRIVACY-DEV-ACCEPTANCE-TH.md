# Privacy candidate — Dev transport acceptance

สถานะ: Dev transport fixture และ restored-route verification ผ่านตามขอบเขตที่บันทึก; acceptance-record review ยังรอ.
วันที่: 19 ตุลาคม 2026.
Candidate: `db00968230fd4aee5690c361b11c8bc8fc36dabc` หลัง merge PR #47.
Directory ที่เตรียม: `~/workspace/hermes-mcp-bridge-privacy-dev` (detached worktree).

## หลักฐานที่เตรียมแล้ว

- Full suite บน WSL ด้วย candidate project venv: 183/183 ผ่าน พร้อม `-W error::ResourceWarning`.
- Privacy regressions 18/18 ผ่าน. Tests ใช้ไฟล์/dir จริงสำหรับ mode repair และ bounded reads.
- Shellcheck ผ่าน. Candidate worktree clean และ requirements parity ตรงกับ Dev เดิม.
- Local SDK stdio fixture แสดง 27 tools. Status metadata 415 serialized bytes มี approval เฉพาะ `{"required": true}` และ usage เฉพาะ `{"total_tokens": 7}`; ไม่ส่ง synthetic private marker.
- ข้อข้างต้นเป็น local code/stdio fixture evidence ไม่ใช่ Dev tunnel หรือ actual Hermes/provider acceptance.
- Dev เดิมยัง pin `e7add7e`. การเตรียมไม่เปลี่ยน profile, auth references, service, tunnel หรือ production.

## Transport และขอบเขต

ใช้ tracked `tests/mock_mcp_server.py --privacy-fixture` จาก candidate.
Fixture import runtime จริงของ candidate และใช้ in-process `httpx.MockTransport`.
URL loopback ใน fixture ไม่ถูก dial จริง.
ไม่มี actual Hermes HTTP server, model, Codex CLI หรือ OpenCode CLI ถูกเรียกโดย fixture.
Directory และ state ของ fixture เป็น disposable synthetic data.

ใช้ `--mcp.command` เป็น ephemeral override.
Public help ระบุ `stringArray` และ precedence `flags > environment > YAML > defaults`.
Bounded scratch probes ของ `dev proxy` และ `run` ยืนยันว่า flag แทน command ใน profile ไม่ append; command string รองรับ args.
Probe ใช้ synthetic scratch configuration และ dead loopback control-plane endpoint เท่านั้น.
ไม่ได้ทดสอบ live control-plane authentication ด้วย probe เหล่านั้น.
ไม่ต้องแก้หรือ backup YAML เพื่อใช้ override นี้.

## Operator handoff

ใช้ terminal ที่เคย authenticate Dev สำเร็จ.
Background task ไม่มี environment key ที่ Dev profile อ้างถึง.
อย่าคัดลอก key ไปแชต, command line, source หรือ log.

1. รอ jobs ของ Dev ให้เป็น terminal. ถ้ามี `unknown_exit` ให้ตรวจ process ก่อน.
2. กด `Ctrl+C` ใน terminal ของ Dev เดิมเท่านั้น. ต้องไม่มี instance อื่นใช้ profile เดียวกันหรือ health port 8081.
3. เปิด fixture จาก authenticated terminal เดิม:

   ```bash
   tunnel-client run --profile hermes-wsl-dev \
     --health.listen-addr 127.0.0.1:8081 \
     --mcp.command "$HOME/workspace/hermes-mcp-bridge-privacy-dev/.venv/bin/python $HOME/workspace/hermes-mcp-bridge-privacy-dev/tests/mock_mcp_server.py --privacy-fixture"
   ```

   เปิด terminal ค้างไว้เมื่อเชื่อมต่อสำเร็จ. หากรายงาน auth/port/command error ให้หยุดแก้สาเหตุก่อน ไม่เปิด instance ซ้อน.
4. แจ้ง ChatGPT ให้ตรวจ Dev tools. Refresh เฉพาะ Dev tools ถ้าจำเป็น.
5. Parent ต้องเรียก `bridge_version` และยืนยัน `source_kind: git-worktree`, `source_revision: db009682...` ก่อน submit synthetic task.
6. ใช้ request ID เฉพาะรอบทดสอบ. เรียก submit/status/result จาก Dev connector แล้วตรวจว่า status ไม่ส่ง raw approval/error marker, metadata ไม่เกิน 8,192 bytes และ result ยังมี explicit fixture output.
7. แยก cached parent registry ออกจาก fresh discovery. Local fixture discovery 27 ไม่ใช่ raw tunnel `tools/list` capture. อย่าอ้าง live 28/33 จากรอบนี้.
8. Synthetic pending approval ไม่ใช่ native approval acceptance. ห้าม approve หรือเริ่ม native CLI เพื่อทำให้ fixture จบ.

## คืน Dev เดิม

1. หลังเก็บผล ให้กด `Ctrl+C` ใน terminal ที่รัน fixture.
2. เริ่ม Dev เดิมโดยไม่ใส่ command override:

   ```bash
   tunnel-client run --profile hermes-wsl-dev --health.listen-addr 127.0.0.1:8081
   ```

3. Parent ตรวจ `bridge_version` กลับเป็น pin `e7add7e` และตรวจสถานะเดิม. YAML ไม่ถูกแก้จึงไม่มี restore-file step.
4. บันทึกผล Dev transport และ restoration ก่อนปิด acceptance record. หากยังคืน route ไม่สำเร็จ ให้บันทึกค้างและหยุดเริ่มงานใหม่.

## สิ่งที่ยังไม่ผ่านใน preparation นี้

- Actual Dev transport และ restored-route proof ผ่านแล้วตาม checkpoint ด้านล่าง; ไม่ครอบคลุม actual Hermes HTTP/native approval/model acceptance.
- Production OpenCode benign model acceptance.
- Release/version decision, signed assets และ deployment.
- Privacy follow-up closure และ gates ของ MCP Events/Local Hands.

ดูข้อกำหนดใน [SPEC.md](SPEC.md), ผล implementation ใน [PRIVACY-CONTRACT-REVIEW-TH.md](PRIVACY-CONTRACT-REVIEW-TH.md) และสถานะใน [ROADMAP.md](ROADMAP.md).

## Dev transport checkpoint — scoped fixture PASS (19 ตุลาคม 2026, ~21:11 +07)

Operator เปิด ephemeral command override แล้ว parent เรียก actual Dev connector ผ่าน Secure MCP Tunnel.
Fixture ใช้ runtime candidate จริงร่วมกับ in-process fake Hermes transport; ไม่ใช่ actual Hermes HTTP, native approval หรือ model/provider acceptance.

| หลักฐานจาก Dev connector | ผลที่สังเกตได้ |
| --- | --- |
| Identity | `source_kind: git-worktree`, revision `db00968230fd4aee5690c361b11c8bc8fc36dabc`; version stamp `1.2.5/v1.2.5` ไม่ใช่ release ใหม่ |
| Config identity | `config_schema_version: unknown`, embedded schema 1; fixture สร้าง runtime โดยตรงและไม่มี root config file จึงไม่ใช่การตรวจ config migration |
| State | Disposable fixture state mode `0700`; ไม่ใช่ live repair ของ production directory เดิม |
| Tool visibility | Parent registry เห็น 27 tools และ version รายงาน canonical default 27; ไม่ใช่ raw wire `tools/list` capture และไม่อ้าง live 28/33 |
| Synthetic submit/status | `run_1`, `waiting_for_approval`; compact ASCII JSON metadata 416 bytes ≤ 8,192; error เป็นข้อความคงที่ และ approval มีเพียง `required: true` |
| Sensitive fixture marker | `PRIVATE_MCP_FIXTURE` ไม่ปรากฏใน status/result ที่ตรวจ |
| Result pages | offset 0/max_chars 4 แล้ว offset 4; ต่อกันตรงกับ full result 29 characters; configured-key replacement marker ยังคงอยู่ |
| Ownership | Run ที่ไม่ registered ถูกปฏิเสธ (`INVALID_ARGUMENT`) |
| Replay | Request/input เดิมคืน `run_1` พร้อม `replayed_locally: true` |

ไม่ได้ approve หรือ cancel synthetic pending approval และไม่มี native worker ถูกเริ่ม.
Hands ที่ available เป็น read-only synthetic fixture workspace เท่านั้น; ไม่ใช่การเปิด Hands ใน Dev configuration เดิมหรือ production.
Directory repair และ bounded Codex reads อ้างผล real-filesystem tests บน WSL ที่ candidate เดียวกัน; ไม่ได้ probe Codex result ผ่าน Dev tunnel ในรอบนี้.
สถานะ `PASS` จำกัดเฉพาะรายการในตาราง.

**Restored-route verification: ผ่าน.** หลัง operator คืน route แล้ว parent เรียก Dev connector ซ้ำ: revision `e7add7e594fb2cc0029dd53b628c85f9a7c1a87c`, source `git-worktree`, schema 1 และ default discovery count 27. `bridge_status` กลับสู่ state เดิม mode 0700; Hermes/Codex registered jobs เป็น 0, watchdog ทำงาน และ Local Hands disabled. `hermes_recent_tasks` และ `codex_recent_tasks` ว่าง. รอบนี้ไม่ได้เรียก OpenCode recent เพราะ tool ไม่ปรากฏใน registry ที่ parent ใช้ จึงไม่ยืนยันจำนวน OpenCode jobs หลัง restore.
Privacy follow-up ยังเปิดรอ acceptance-record review และ release/deployment decision.
