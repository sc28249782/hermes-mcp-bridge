# Context P1 — Dev transport acceptance preparation

วันที่: 20 ตุลาคม 2026.
สถานะ: **fixture และแผนเตรียมแล้ว; live Dev acceptance ยัง pending**.
ฐาน runtime: PR #59 merge `5685e11` หลัง external APPROVE ที่ `b7ff97a` และ operator ยืนยัน merge.
เอกสารนี้ไม่อนุมัติการเปลี่ยน Dev route, release หรือ production deployment.

## Scope และ fixture honesty

`tests/mock_context_p1_server.py` ใช้ production `server`, `ContextRegistry` และ read-only observer กับ disposable temporary state. ไม่อ่าน state/config/credentials ของ deployment. Backend ทั้งสามเป็น stubs ที่คืน local status ว่า `fixture_only=true`, `backend_initialized=false` และปฏิเสธ operations อื่น. Watchdog hook ไม่เริ่ม native worker. Audit เป็น no-op stub; ไม่ทดสอบ production audit persistence ในรอบนี้.

Healthy scenario ใช้ soft-cap 3 และเริ่มจาก 0 rows. Create label `P1_FIXTURE_CREATE_READ_FAILURE` เป็น **test-only trigger**: fixture patch ตัวเปิด read-only connection ให้เกิด `sqlite3.OperationalError` ระหว่าง real create/status/observation call. Row ยังคงถูกบันทึกผ่าน production create ตามปกติ. นี่เป็น explicit fault injection ไม่ใช่ label/control ที่ production รองรับ และไม่ใช่ natural storage failure หลัง create.

Missing scenario ลบเฉพาะ disposable DB หลัง init. Locked scenario ถือ `BEGIN EXCLUSIVE` บน disposable DB. สอง scenario นี้ใช้ actual SQLite read failures และ production error handling; ไม่มี fabricated observation object. ห้าม create ในสอง scenario นี้ เพราะกำลังทดสอบ status/unavailable เท่านั้น.

Temporary state อยู่เฉพาะอายุ fixture process และ reset เมื่อเริ่ม process ใหม่. หาก connection restart แล้ว counts ไม่ตรง ให้หยุดและเริ่มรอบ probe ใหม่อย่างชัดเจน; อย่า retry create ที่ได้รับ acknowledgement แล้ว. ไม่อ้าง process-restart persistence ของ fixture.

Fixture ไม่เพิ่ม MCP tools หรือเปิด preview ผ่าน MCP. Canonical default 27 tools มาจาก SDK `tools/list` regression; ต้องแยกจำนวนที่เห็นจาก parent registry กับ raw wire capture ระหว่าง live probe. Inherited stamp 1.2.6 ไม่ใช่ release ใหม่. Root config schema อาจเป็น unknown ใน fresh checkout ที่ไม่มี config; ต้องบันทึกตามผลจริง.

CLI preview ยังคงเป็น local command ตาม §20.3. Dev MCP aggregate checks ไม่ใช่ acceptance ของ CLI dispatch, read-only mount หรือ native backend. ผล isolated CLI เดิมอยู่ใน [P1 acceptance](CONTEXT-P1-ACCEPTANCE-TH.md).

## Preparation ก่อนขอ maintenance window

1. เตรียม clean candidate checkout ใน directory ใหม่จาก exact PR head ที่ CI 3.12/3.14 ผ่าน. อย่าใช้ production หรือ Dev deployment directory. อย่า copy state/config/credentials ไป candidate.
2. สร้าง candidate venv จาก Python ที่รองรับและติดตั้ง requirements ของ checkout. ตรวจ HEAD และ working tree สะอาด. บันทึก identity แบบ redacted; อย่าเผยแพร่ host/user paths.
3. รัน focused context tests กับ packaging tests จาก candidate checkout. Full-suite evidence ต้องแยกตาม interpreter/head; อย่าใช้ cloud process-test failures เป็น WSL pass.

```bash
.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -p 'test_context*.py' -v
```

```bash
.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -p test_packaging.py -v
```

4. ตรวจ Dev route เดิมและงานที่ยังไม่ terminal โดยไม่อ่าน prompt/result/config secret. เตรียมวิธีคืน route เดิมก่อนหยุด Dev. อย่าเปลี่ยน production profile.
5. ขอ operator ยืนยัน temporary Dev maintenance window หลังเตรียม exact head และ rollback พร้อม. Scope คือ synthetic fixture เท่านั้น; ไม่มี model/backend tasks หรือ production upgrade.

## Expected checks ผ่าน connection จริง

| Scenario | Calls | Expected result |
| --- | --- | --- |
| healthy เริ่มต้น | `bridge_version`, `bridge_status` | Exact candidate identity; registry count 0, no warning, root ok true; child backend status เป็น stub |
| healthy create 1–2 | Create แล้ว status แต่ละครั้ง | Counts 1, 2; ไม่ถึง cap; root ok true |
| healthy create 3 | Create แล้ว status | Count 3, cap reached, warning, `count_capped=false`; root ok true |
| healthy create 4–5 | Create แล้ว status | Lower bound 4, capped true, warning; create สำเร็จทั้งสองครั้ง |
| injected create failure | Create ด้วย reserved label ครั้งเดียว | Successful context acknowledgement; registry unavailable/null และไม่มี raw storage marker |
| readback หลัง injected create | Context status ของ ID ที่เพิ่งคืน, recent, bridge status | Row เดิมอ่านได้; recent มี 6 rows และ ID นั้นหนึ่งครั้ง; registry กลับ available/lower bound 4. ห้าม retry create |
| missing | เริ่ม fixture ใหม่; version แล้ว status สองครั้ง | Structured result ไม่ใช่ tool exception; root ok false, null counts, constant warning |
| locked | เริ่ม fixtureใหม่; version แล้ว status สองครั้ง | ผล unavailable เช่นเดียวกัน; reader ใช้ lock timeout เดิม. อย่าอ้าง whole-call latency bound |

Registry object ต้องมีเพียง 6 scalar fields ตาม §20 และไม่เกิน 512 compact ASCII-escaped JSON bytes. Limit นี้ไม่ใช่ whole-MCP-envelope cap. Context create/status/recent ยังคงส่ง metadata เดิม เช่น label/ID; ห้ามอ้างว่า aggregate filter redact ทั้ง response. Public record ให้เก็บเฉพาะผล/counts และ redacted identity ไม่แนบ returned IDs หรือ raw context metadata.

## Terminal handoff หลัง operator ยืนยัน

กำหนด `BRIDGE_P1_CANDIDATE` เป็น absolute path ของ clean candidate checkout ที่ pin แล้ว. ใช้ Dev terminal ที่ authenticate อยู่และบันทึก original launch command ไว้แบบ private. หยุด Dev เดิมด้วย Ctrl+C เฉพาะหลัง maintenance ได้รับอนุมัติ.

```bash
tunnel-client run --profile hermes-wsl-dev \
  --health.listen-addr 127.0.0.1:8081 \
  --mcp.command "${BRIDGE_P1_CANDIDATE:?Set the pinned candidate path}/.venv/bin/python $BRIDGE_P1_CANDIDATE/tests/mock_context_p1_server.py --scenario healthy"
```

Parent ต้องตรวจ exact identity และทำ healthy checks ให้จบก่อนเปลี่ยน scenario. หยุด fixture ด้วย Ctrl+C แล้วเปลี่ยนเพียง scenario เป็น missing:

```bash
tunnel-client run --profile hermes-wsl-dev \
  --health.listen-addr 127.0.0.1:8081 \
  --mcp.command "${BRIDGE_P1_CANDIDATE:?Set the pinned candidate path}/.venv/bin/python $BRIDGE_P1_CANDIDATE/tests/mock_context_p1_server.py --scenario missing"
```

หยุด fixture แล้วเปิด locked scenario เพื่อทดสอบ actual SQLite contention:

```bash
tunnel-client run --profile hermes-wsl-dev \
  --health.listen-addr 127.0.0.1:8081 \
  --mcp.command "${BRIDGE_P1_CANDIDATE:?Set the pinned candidate path}/.venv/bin/python $BRIDGE_P1_CANDIDATE/tests/mock_context_p1_server.py --scenario locked"
```

ใช้ ephemeral `--mcp.command` เท่านั้น; ไม่แก้ profile YAML. ตัวอย่าง command string นี้ใช้ candidate path ที่ไม่มีช่องว่าง; หาก path มีช่องว่างให้หยุดและตรวจ quoting ตาม tunnel client ก่อนใช้. อย่าเดารูปแบบ parser.

## Restoration และ stop conditions

หาก identity/scenario/field shape ไม่ตรง, มี backend call หรือผลเกิน scope ให้หยุด probe และคืน route เดิม. อย่า retry create เมื่อ acknowledgement กลับมาแล้ว แม้ registry unavailable. ระหว่าง restore อย่าส่งงานใหม่ไป Dev จนตรวจ identity กลับครบ.

หยุด fixture แล้วเปิด profile เดิมโดยไม่มี command override:

```bash
tunnel-client run --profile hermes-wsl-dev --health.listen-addr 127.0.0.1:8081
```

ตัวอย่าง restore นี้ใช้ได้ต่อเมื่อ preflight ยืนยันว่า original launch ใช้ profile/default command ตามตัวอย่าง. ถ้าเดิมมี flags อื่น ให้คืน exact original command ที่บันทึกไว้; อย่าแทนด้วยตัวอย่าง. Parent ต้องตรวจ revision/configured discovery/state/watchdog และจำนวน registrations เทียบ preflight แบบ metadata-only. เป้าหมาย pin เดิมจาก checkpoint ก่อนหน้าคือ `e7add7e`; ห้ามอ้างว่าเครื่องปัจจุบันตรงจนตรวจใหม่.

ห้ามบันทึก restoration ผ่านเพียงเพราะ tunnel process start สำเร็จ. หาก restore ไม่ผ่าน ให้บันทึก unavailable และหยุด acceptance; อย่าเปลี่ยน production เพื่อชดเชย. การ activate fixture ไม่ใช่ deployment approval ของ P1.

## ผลการเตรียมและสิ่งที่ยังรอ

Local SDK stdio tests ใหม่ผ่าน 3/3: healthy threshold/fault/readback, actual missing/locked SQLite และ backend guard. นี่เป็น maintainer automation ไม่ใช่ external review หรือ live Dev evidence. Focused/CI exact-head results ให้บันทึกใน PR receipt หลังรันเสร็จ; อย่าใส่ผลที่ยัง pending เป็น PASS.

Live Dev connection, current-route preflight, candidate preparation บน WSL, temporary-window approval และ restoration ยัง pending. Dedicated read-only mount probe ยังไม่ทำ; tests ก่อนหน้าครอบคลุม POSIX permissions เท่านั้น. Release/deployment decisions แยกจากงานนี้. Production signed v1.2.6, P2/race และ Hands/Events gates ไม่เปลี่ยน.
