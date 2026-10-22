# Validation record — v1.2.5 released (2026-10-19)

## Unreleased — unresolved binding outcome after acceptance (SPEC §22)

Implementation ของ [SPEC §22](SPEC.md#22-context-binding-unresolved-proposed) ใน runtime PR นี้ pending review; สถานะคือ implemented pending review — ยังไม่ released และยังไม่ deployed, ไม่มี release ที่ได้รับมอบหมาย และไม่มี acceptance claim (scoped Dev acceptance เป็นขั้นถัดไป). ฐานอ้างอิง: suite เต็ม ณ base `4ed8765` คือ 227 tests; ส่วนขยายเพิ่ม `tests/test_context_binding_unresolved.py` (7 deterministic tests ตาม §22.5) และปรับ 2 lifecycle tests จาก pre-§22 expectation ของ `sqlite3.OperationalError` ที่ binding call ให้เป็น conversion contract ตาม §22.2 (ชื่อ method เปลี่ยนตาม, ไม่มี coverage เดิมถูกลบ).

Receipt ฝั่งผู้เขียนด้านล่างเป็นผล ณ `11aa70115922dd14340561bca8a328b166a81253`; commit ถัดมาเสริมการเทียบ ACK ทุกค่าจาก snapshot และ fixture ที่ commit synthetic Codex job row ก่อน submit raise. Runtime ไม่เปลี่ยนจาก `11aa701`; ไม่ขยายผล local receipt เดิมว่าเป็นการรัน tests ฉบับที่เสริมแล้ว และต้องตรวจ CI ที่ exact head ใหม่แยกต่างหาก.

ทุกชุดรันด้วย `-W error::ResourceWarning` และ `unittest discover -s tests`; ผลเป็น maintainer automation ไม่ใช่ external review. ไม่มี real model/backend task.

| ชุด | Interpreter | ผล | Exit |
| --- | --- | --- | --- |
| Focused `tests/test_context_binding_unresolved.py` ณ `11aa701` | Python 3.12.3 | 7 tests, OK | 0 |
| Focused `tests/test_context_binding_unresolved.py` ณ `11aa701` | Python 3.14.7 | 7 tests, OK | 0 |
| Full suite ณ `11aa701` | Python 3.12.3 | 234 tests, OK, 0 skip/fail/error | 0 |
| Full suite ณ `11aa701` | Python 3.14.7 | 234 tests, OK, 0 skip/fail/error | 0 |
| Full suite ณ `11aa701` | Python 3.11.15 | 234 tests, OK, 0 skip/fail/error | 0 |

## v1.2.7 preparation — exact-head receipt

Source stamp 1.2.7/v1.2.7 ใช้ reviewed input `07ec0069b952f08a49adbd0ec778c204f85ee282`. [Preparation record](V1.2.7-RELEASE-PREP-TH.md) กำหนด source/extracted suite, packaging/identity/discovery และ CI 3.12/3.14; ผลของ exact tested head กับ candidate checksum อยู่ใน PR receipt. ข้อความนี้ไม่เพิ่มผล PASS ล่วงหน้า. หลักฐาน P1 ที่ `27030bb` และ Codex fix ที่ reviewed head เดิมยังคงขอบเขตเดิม. Candidate ZIP ไม่ใช่ signed release.

อัปเดตสถานะ (20 ตุลาคม 2026): v1.2.7 เผยแพร่ผ่าน signed tag ที่ `625ea117aa693f577872638a6353b1408fb405aa`; prep evidence ด้านบนคงผูกกับ prep head `013fd28` ตามเดิม. External fresh-input audit ผ่าน (extracted suite 206/206 จาก fresh venv); ไม่มี WSL-suite rerun ใหม่จาก record นี้. ดู [release record](V1.2.7-RELEASE-RECORD-TH.md).

## Unreleased — context lifecycle closed-binding outcome (SPEC §21)

Implementation ของ [SPEC §21](SPEC.md#21-context-lifecycle--closed-binding-outcome-approved-design-implementation-not-started) ใน PR นี้ pending review; ยังไม่ released, ไม่ deployed และไม่ได้รับการยอมรับจาก external review. ฐานอ้างอิง baseline suite คือ 206 tests.

อัปเดตสถานะ (21 ตุลาคม 2026): implementation ถูกรวมใน PR #70 ที่ main `227f2ad1f43ff64c6c4866595c9ea705fd7977b3` (review head `07bfe82`). ข้อความ "pending review" ข้างต้นคงเป็นหลักฐานย้อนหลังของ PR นี้. Scoped synthetic Dev acceptance ผ่านแล้ว (ตารางด้านล่าง). ยังไม่ released และยังไม่ deployed; ไม่มี release ที่ได้รับมอบหมาย.

อัปเดตสถานะ 2 (21 ตุลาคม 2026): §21 delta เข้า scope v1.2.8 release candidate ตาม [scope decision packet](V1.2.8-RELEASE-DECISION-PROPOSAL-TH.md) ที่ operator อนุมัติแล้ว; suite/identity receipts อยู่ที่ [preparation record](V1.2.8-RELEASE-PREP-TH.md). อัปเดตสถานะ 3 (22 ตุลาคม 2026): v1.2.8 เผยแพร่แล้ว; extracted suites จาก release asset 227/227 OK ทั้งสอง interpreter ตาม [release record](V1.2.8-RELEASE-RECORD-TH.md).

### v1.2.8 release candidate preparation (21 ตุลาคม 2026)

รายละเอียดเต็มอยู่ที่ [preparation record](V1.2.8-RELEASE-PREP-TH.md). ทุกชุดรันด้วย `-W error::ResourceWarning` และ `unittest discover -s tests`; ผลเป็น maintainer automation ไม่ใช่ external review. ไม่มี real model/backend task; identity checks ใช้ isolated synthetic/no-backend state เท่านั้น.

| ชุด | Interpreter | ผล | Exit |
| --- | --- | --- | --- |
| Source ณ prep commit `52d9505` | Python 3.12.3 | 227 tests, OK, 0 skip/fail/error | 0 |
| Source ณ prep commit `52d9505` | Python 3.14.7 | 227 tests, OK, 0 skip/fail/error | 0 |
| Extracted จาก untagged diagnostic archive | Python 3.12.3 | 227 tests, OK, 0 skip/fail/error | 0 |
| Extracted จาก untagged diagnostic archive | Python 3.14.7 | 227 tests, OK, 0 skip/fail/error | 0 |

Identity parity (extracted candidate): `./bridge.sh version` และ SDK stdio `bridge_version` ตรง stamp `1.2.8`/`v1.2.8`/`release-archive`/`887436f`/`embedded-build-input` ทุก field; SDK `tools/list` = 27 tools (default; opt-in 28/33 ครอบด้วย opt-in tests ใน suite เดิม). หมายเหตุขั้นตอน: extract ด้วย zipfile ปกติ drop executable bit ของไฟล์ 755 — restore ตาม git mode ก่อนรัน (ครั้งแรกพบ 34 errors จาก fixture ไม่ executable; ไม่ใช่ defect ของ source) ตามรายละเอียดใน preparation record.

- Registry mutation: `close`, `bind_hermes_run`, `bind_codex_job` เป็น conditional atomic UPDATE เงื่อนไข `closed IS NULL` หนึ่ง statement; classification unknown/closed ทำใน transaction เดียวกันด้วย error คงที่เดิม; `observe_hermes` อัปเดตได้มากที่สุด 1 row พร้อม guard ป้องกัน stale write; เพิ่ม `ContextClosedError` (subclass ของ `ContextError`).
- Wrapper D5: precheck invalid/unknown/closed ก่อน backend call (0 backend calls); หลัง backend ACK ปกติ ถ้า bind ถูกปฏิเสธเพราะ close → success response คง output เดิมครบ + `context_binding="closed_rejected"` + note คงที่ตาม SPEC; bind สำเร็จ → `"bound"` ไม่มี note; ไม่มี context_id → ไม่มีทั้งสอง field; DB error/submit raise คง error เดิม ไม่ถูกแปลง.
- ชุดทดสอบ: `tests/test_context_lifecycle.py` 21 tests ตาม acceptance matrix ของ §21.3; deterministic gates อยู่ก่อน UPDATE execute (หลัง precheck SELECT, ก่อน writer transaction เริ่ม — assert `in_transaction` เป็น false ก่อนรอ ไม่มี SQLite writer lock ค้างขณะรอ; bounded timeout fail ทันทีเมื่อหมดเวลา; ไม่มี time.sleep เป็นตัวจัดคิว); test at-most-one-row ไม่ผูกว่า candidate ใดชนะ (เช็คเฉพาะ "exactly one of two มี session, อีก row None, run id คงเดิม" ตาม contract — ไม่อ้างลำดับ lexicographic); รวม cross-process shared-state test (multiprocessing fork, queue reads แบบ bounded 2 ครั้ง + try/finally join/terminate), close-wins/bind-wins/double-close, late observe, precheck 0 backend calls (รวม context_id ว่าง), ACK→close→bind ครบทั้ง Hermes/Codex, replay ไม่เพิ่ม submission, DB error ไม่ถูกแปลง, restart ไม่ resubmit.
- ผลรัน (interpreter จริง): Python 3.12.3 (project venv) — ชุดเต็ม 227/227, ResourceWarning-as-error, no skips; Python 3.11.15 (project venv) — 227/227 เช่นกัน. Python 3.14 ยังไม่รันในเครื่อง (ไม่มี venv ที่ติดตั้ง dependencies ครบ) — CI matrix 3.12/3.14 เป็นผลที่ต้องยืนยันที่ pushed head.
- Regression receipt เทียบ base ตรง `98adf8826ffe70bd22ea014a2f5ae170d6e8e16b` (วัดจริง 3 รัน — ลิสต์ fail เหมือนกันทุกครั้ง): **14 จาก 21 fail = 4 race + 10 contract**.
  - Race 4 กรณี (พิสูจน์ด้วย focused probe อ่าน row state จริงหลัง interleave บน baseline): close-wins Hermes (bind outcome `written`; row วัดได้ `closed` set และ `hermes_run_id='run_x'` บน closed row), close-wins Codex (outcome `written` กลไก UPDATE เดียวกัน), observe stale rebind (row วัดได้ `hermes_run_id='run_new'` แต่ `hermes_session_id='stale_session'` — session เก่าเขียนทับ row ที่ rebind), และ cross-process (worker คืน `bound`; row วัดได้ `closed` set + `hermes_run_id='run_x'` — การเขียนลง closed row ข้าม process วัดจาก row ไม่ใช่จาก crash).
  - Contract 10 กรณี: typed `ContextClosedError` ขาด (double close, bind-after-close, precheck Hermes/Codex), `context_binding` field ขาด (bound/closed_after_ack ฝั่ง Hermes/Codex, replay bound), context_id ว่างถูก bypass ไปเรียก backend — เป็น contract-gap evidence ไม่ใช่หลักฐาน functional race. ไม่มี skip หรือ baseline-fake.
- ข้อจำกัดของ receipt เก่า: การรันบน head ก่อนหน้าของ PR นี้ (`525286a`, ชุด 18 tests) ให้ 10/18 ที่ไม่ stable (รันใหม่ได้ 11/18) เพราะ random context id และ baseline SELECT ของ observe ที่ไม่มี ordering — ตัวเลขนั้นจึงไม่ใช่ universal regression count และข้ออ้าง "cross-process baseline เขียน closed row" เดิมที่อิงจาก typed-exception crash ถือว่าถอน; receipt ที่ใช้ได้คือตัววัดล่าสุดด้านบนเท่านั้น.
- Replay: ไฟล์ใหม่ครอบเฉพาะ known-id replay ไม่เพิ่ม submission (`hermes_recent_tasks`/POST ไม่ถูกเรียกซ้ำ); uncertain guarded replay (หน้าต่าง 23 ชั่วโมง + capabilities check) ยังครอบด้วยชุดเดิมระดับ core ใน `tests/test_bridge.py` (`test_lost_acceptance_durable_replay`, `test_uncertain_without_durable_replay_is_blocked`, `test_old_replay_blocked`) เพราะ core.py ไม่ถูกเปลี่ยน — ไม่มีการอ้างเกิน.
- ขอบเขตที่ไม่แตะ: ไม่เปลี่ยน schema/config schema/discovery 27/28/33/tool signature; ไม่มี P2 apply/delete, durable intent, new audit event; ข้อจำกัด submit-admission/crash ระหว่าง submit→bind คงตามที่ SPEC §21 ระบุ.

### Scoped synthetic Dev acceptance (21 ตุลาคม 2026)

รายละเอียดครบอยู่ที่ [acceptance record](CONTEXT-LIFECYCLE-DEV-ACCEPTANCE-TH.md). Fixture ใช้ `server()` และ `ContextRegistry` ของ candidate จริง (main `227f2ad1f43ff64c6c4866595c9ea705fd7977b3`) ผ่าน Dev tunnel จริง; Hermes เป็น synthetic ACK ผ่าน mock transport และ Codex เป็น stub — นี่เป็น mock-backend evidence ไม่ใช่ real-backend acceptance. ไม่มี model/backend task จริง; ไม่มี credentials; ไม่เพิ่ม MCP tools (SDK `tools/list` = 27 tools).

| ชั้นหลักฐาน | ผล |
| --- | --- |
| Durable (rows/audit ของ fixture state) | runs 4 แถว (`p1l-hermes-bound-01`, `p1l-hermes-close-bind-01`, `p1l-hermes-plain-01`, `p1l-hermes-db-error-01` — แต่ละอัน 1 ACK); contexts 5 แถวตรงสถานะ = 3 closed / 2 open — Hermes bound scenario row closed หลังขั้น close โดยคง `hermes_run_id` เดิมไว้ (double-close ไม่เพิ่ม audit record), Hermes close-at-bind row closed ไม่มี binding, Codex bound row open พร้อม binding, Codex close-at-bind row closed ไม่มี binding, DB-error row open ไม่มี binding; audit 12 records = 5 create + 3 close + 4 hermes submit; close audit 3 records ตรง 3 rows ที่ closed; precheck rejection ไม่มี record (zero-POST); replay มี runs row + audit submit อย่างละ 1 (ไม่มี duplicate) |
| Parent live observation (ผ่าน Dev connector จริง) | identity ของ fixture ตาม `bridge_version`; counters ก่อน restore: hermes 4 / codex 4; response payload (`replayed_locally`, `pending_local_approval` ครบ, ข้อความ DB-error) |
| Offline smoke (maintainer automation ในเครื่อง — ไม่ใช่ transport evidence) | in-process scenarios ครบ; SDK stdio init/tools/calls = 27 tools; focused lifecycle tests 21/21 บน Python 3.14.7 |

ข้อจำกัด: counter ฝั่ง codex (4) พึ่ง parent observation เท่านั้น เพราะ fake Codex ไม่เขียน audit; ข้อความ response รายละเอียดพึ่ง parent observation; การที่ audit ไม่มี record ไม่พิสูจน์ด้วยตัวเองว่าคำขอ invalid แต่ละรายการได้รับการจัดการ; timestamp ในวินาทีเดียวกันไม่พิสูจน์ลำดับ. Restoration ตรวจแล้ว: identity `1.2.4`/`e7add7e` คืนแล้ว (offline CLI + parent live) และ state/config/profile ตรง backup byte-identical; production `1.2.7`/`07ec0069` ไม่ถูกแตะ.

อัปเดตสถานะ (21 ตุลาคม 2026): acceptance record PR #71 ผ่าน external APPROVE ที่ review head `70bdd2154cfbadd8f2526dca2b07a173fb232a1e` (commit แก้ไข enumerate จาก re-review) และ merge ที่ `753f5b4fa1d9994964b78990d1efecedea9d765b` — checkpoint นี้ปิดแล้ว; ยังคงเป็น mock-backend evidence ไม่ใช่ real-backend acceptance. [Release readiness proposal v1.2.8](V1.2.8-RELEASE-DECISION-PROPOSAL-TH.md) รอ operator scope decision; ยังไม่มี release ที่ได้รับมอบหมาย.

## Unreleased — Codex result read-ahead fix

Public baseline: `b3fa3b7`. Runtime/test/CI candidate: `799acc3d131e60a65fe085ff1e0c48d1e7c73f76`.
เอกสารที่เพิ่มภายหลังไม่เปลี่ยน code head นี้.
หลักฐานด้านล่างเป็น maintainer validation ของ public source และ synthetic files; ไม่ใช่ external review หรือ production acceptance.

| Check | ผล |
| --- | --- |
| Baseline truncate test, 3 runs | Python 3.12.3 ผ่าน 3/3; Python 3.14.7 ไม่ผ่าน 3/3 เพราะ error ที่คาดไม่เกิด |
| Buffer probe | 3.14.7 default buffer 131,072 bytes อ่าน raw ถึง 131,072 เมื่อขอ 65,536; หลัง truncate ยังคืนอีก 65,536 จาก buffer |
| Buffered snapshot characterization | เคสข้างต้นคืนครบ initial snapshot 131,072 bytes; ไม่ใช่ partial result แต่ไม่มี short read ให้ guard ตรวจพบ |
| New regression negative control | Snapshot 70,000 bytes แล้ว append ก่อน read: runtime เดิมอ่าน raw ถึง 73,728 บน 3.12.3 และ 131,072 บน 3.14.7; test ใหม่ fail ทั้งคู่ |
| Candidate WSL full suites | Python 3.12.3: 185/185; Python 3.14.7: 185/185, ResourceWarning-as-error, no skips |
| Focused chat-runtime tests | Python 3.12.14: privacy hardening 19/19 และ MCP boundary 1/1; รวม 20/20 |
| Chat-runtime full-suite limitation | Main เดิม 184 tests และ candidate 185 tests ต่างมี 4 failures/35 errors ในชุด process/executable checks; ไม่อ้าง full-suite pass ใน runtime นี้ |
| Shell checks | WSL shellcheck, Bash syntax และ whitespace ผ่าน |
| CI | เพิ่ม matrix Python 3.12/3.14; ผล exact-head ของ PR บันทึกใน PR body |

ใช้ `path.open("rb", buffering=0)` เพื่อไม่ให้ read-ahead ดึงข้อมูลเกิน snapshot budget.
Contract §19.3 เดิมกำหนด read budget อยู่แล้ว; PR นี้ไม่แก้ normative SPEC.
Guard ยัง fail เมื่ออ่าน snapshot ไม่ครบ.
การแก้นี้ไม่สร้าง atomic filesystem snapshot และไม่ตรวจ concurrent overwrite, shrink-and-regrow หรือการเปลี่ยนไฟล์หลังอ่านครบ.
Raw read calls ยังมีขอบเขตไม่เกิน 65,536 bytes และ cap รวม 8,388,608 bytes; decoding/pagination ไม่เปลี่ยน.
Stamp ยังคงค่าเดิมจาก v1.2.6 แต่ patch นี้ unreleased และไม่ deploy production.

แหล่งอ้างอิง: [Python 3.14 open buffering](https://docs.python.org/3.14/library/functions.html#open) และ [BufferedReader read-ahead](https://docs.python.org/3.14/library/io.html#io.BufferedReader).

## Production v1.2.6 — deployment checkpoint (20 October 2026)

Operator อนุมัติ deployment และ maintenance window เมื่อ 13:52:34 +07. Production อัปเกรดเป็น v1.2.6 แล้ว. Parent connector ยืนยัน release-archive/input `e3e698a7`, schema 1, state `0700`, watchdog ทำงาน, Hermes authentication verified และ OpenCode v2.0.32. Parent registry มี 33 tools ตาม config; ไม่ใช่ raw wire `tools/list` capture. Hands ยัง disabled. ดู [deployment record](V1.2.6-DEPLOYMENT-TH.md) สำหรับผลทดสอบ ข้อจำกัด และ rollback. ข้อความ deployment pending/v1.2.5 ด้านล่างเป็น checkpoint ก่อนอัปเกรด. Privacy follow-up ปิดตาม §19.4 หลัง external reviewer ให้ APPROVE แก่ PR #54 ที่ `7b2886d` เมื่อ 20 ตุลาคม 2026 ตามรายงานที่ operator ส่งในแชต; production OpenCode benign-model acceptance ผ่านแยกแล้วเมื่อ 20 ตุลาคม 2026 ตาม [acceptance record](OPENCODE-PRODUCTION-ACCEPTANCE-TH.md); ไม่ขยายเป็น write/cancel/native-permission acceptance.

## v1.2.6 — released privacy hardening (SPEC §19)

Post-tag verification (20 October 2026): fresh tag `a9a15e08…` peels to `cee144e14e53d971d986de346aab58c51bca97f0`; expected-signer cryptographic verification passed. Final ZIP `acf6c38ca371acd73d31099c5448d6ef9c3588020e74d0c0bfe3769736b1664e` (321,434 bytes, 87 unique entries) and external SHA256SUMS passed fresh-download checks and byte comparison against signed-tag rebuild. GitHub badge is `no_user`; the external signed-release fresh-input audit passed in the operator-supplied review of PR #53 at `88fb58f` on 20 October 2026. The external reviewer separately ran the extracted full suite in a fresh venv: 184/184 passed. This external evidence is separate from maintainer automation and does not establish production acceptance. Offline archive version is 1.2.6/v1.2.6, release-archive, embedded input `e3e698a7a220bf14a8bb4d1260bf2ded7e666b56`, embedded schema 1/default 27; config schema is unknown because no config ships. No publication-time suite rerun or production acceptance is claimed. [Release record](RELEASE-STATUS-TH.md).

Historical preparation checkpoint (20 October 2026, before publication): the operator approved the v1.2.6 scope. External review of PR #48/#49 accepted the scoped Dev records and restoration. PR #49 code head `f570d03` passed WSL 184/184 and focused privacy 19/19; its boundary/approval results and limitations are in [PRIVACY-BOUNDARY-ACCEPTANCE-TH.md](PRIVACY-BOUNDARY-ACCEPTANCE-TH.md). The dated checkpoints below retain the preparation-stage evidence and pending status as written at that time. The 1.2.6/v1.2.6 release candidate uses reviewed build input `e3e698a7a220bf14a8bb4d1260bf2ded7e666b56`. Exact candidate WSL/archive/CLI-MCP/discovery checks must have a receipt in the release-preparation PR before merge; see [V1.2.6-RELEASE-PREP-TH.md](V1.2.6-RELEASE-PREP-TH.md). Prior counts in this paragraph apply to `f570d03`; the new receipt must identify its own tested head. No production acceptance is claimed. See [PRIVACY-RELEASE-DECISION-TH.md](PRIVACY-RELEASE-DECISION-TH.md).

Dev transport fixture checkpoint (19 October 2026, ~21:11 +07): parent called the actual Dev connector at `db009682`; filtered status metadata was 416 bytes, explicit result pagination matched all 29 characters, unknown-run ownership was denied, and an identical retry returned the existing run. The parent registry exposed 27 tools; no raw wire discovery or live 28/33 proof is claimed. This used in-process fake Hermes transport, not actual Hermes HTTP/native approval/model execution. Codex bounds and mode repair remain WSL filesystem-test evidence. Restoration was verified through the Dev connector at `e7add7e`: schema 1, original state mode 0700, zero Hermes/Codex registrations, running watchdog, Hands disabled and empty Hermes/Codex recent lists. OpenCode job count was not rechecked because its recent tool was absent from the parent registry. Acceptance-record review remains pending: [PRIVACY-DEV-ACCEPTANCE-TH.md](PRIVACY-DEV-ACCEPTANCE-TH.md).

WSL preparation checkpoint (19 October 2026): isolated candidate `db009682` passed 183/183 full-suite tests in its own venv, 18/18 privacy regressions and shellcheck. Local SDK stdio fixture discovery was 27; status metadata was 415 bytes with filtered approval/error. This supplements the earlier host limitation below; it is not live Dev transport evidence. Operator handoff: [PRIVACY-DEV-ACCEPTANCE-TH.md](PRIVACY-DEV-ACCEPTANCE-TH.md).

- `tests/test_privacy_hardening.py`: 18 process-free synthetic regressions cover metadata allowlists, numeric/size limits, exact local approval, legacy key exclusion, timeout/error behavior, existing-directory enforcement and failures, bounded snapshot reads, Unicode/newlines/invalid UTF-8, sparse/oversize logs, append/truncate races and read-budget assertions.
- `tests/test_mcp.py::test_privacy_metadata_is_bounded_on_real_stdio` checks the actual SDK stdio boundary with fake Hermes data. It verifies no raw approval/error fixture reaches metadata and discovery remains at the canonical default.
- Focused local suite: 40/40 pass with the project venv and `-W error::ResourceWarning` (`test_privacy_hardening`, `test_bridge`, `test_mcp`). No real model/provider call is made.
- Four pre-existing Codex process/identity tests fail in this execution environment on both baseline and candidate: unreaped-zombie detection, detached-approver result, model override forwarding, and fixed-argv result capture. The baseline comparison also failed to obtain a start-ticks identity. These are not counted as passing local full-suite evidence. Exact-head Linux CI must pass the full suite and shell checks; its result is recorded on the candidate PR.
- External review supplied by the operator on 19 October 2026 approved `c14cd8c` ([PR #47](https://github.com/sc28249782/hermes-mcp-bridge/pull/47)). The reviewer reported 183/183 tests on a clean worktree, independent metadata/directory/Unicode/read-limit probes, and exact-head CI `39260476787` passing. This supplements, and does not replace, the local-environment limitation recorded above.
- This is fixture acceptance, not production or Dev rollout acceptance. Signed v1.2.5 evidence below remains historical and unchanged.

## v1.2.4 candidate gates (historical pre-tag record; v1.2.4 released 2026-10-18)

> สถานะอัปเดต (18 ตุลาคม 2026): v1.2.4 เผยแพร่แล้วผ่าน signed tag พร้อม release assets ที่ตรวจแล้ว (ดู [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)) ข้อความ "not published, not installed" และรายการ "Pending: live Secure MCP Tunnel acceptance" ด้านล่างคงไว้เป็นหลักฐานก่อน tag ตามเดิม; live tunnel acceptance เกิดขึ้นจริงในวันเดียวกันเป็น bounded PASS บน Dev route (ดู [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md))

- Offline suite: all tests pass with the project-interpreter recipe below (`env -u PYTHONPATH`, `-W error::ResourceWarning`), including the 13 stdio-guard tests and the new packaging tests; `bash -n install.sh bridge.sh tunnel.sh` and `shellcheck -S warning install.sh bridge.sh tunnel.sh` pass.
- Local archive candidate verification (Phase B minus tag/publish): ZIP structure test, exclusion check (no `.venv/`, `state/`, `.env`, `bridge-config.json*`, `.git/`, `__pycache__/`), re-extraction, `./bridge.sh version` from the extracted tree, and the extracted-tree stdio fixture probe (pre-init `server/discover` → `-32601` with the same id, no params echo, no log flood; `initialize` → `tools/list` = 27 tools; EOF → exit code 0). No real Hermes/Codex/OpenCode/provider call is made.
- The optional 28-tool discovery is proven inside the suite by `tests/mock_opencode_server.py` with `tests/test_opencode.py`; the default and canonical count remains 27.
- `tests/test_packaging.py` (new): derives `bridge.py`'s real root-module import surface and proves `opencode_core.py`, `stdio_guard.py`, and the three stdio fixture servers are present and git-tracked. `install.sh` runs from the extracted `git archive` and copies nothing, so an untracked module would silently break the release archive.
- Pending: live Secure MCP Tunnel acceptance. Until it passes, the candidate is implemented and tested, not accepted and not released.

## v1.2.3 release record (2026-10-04)

Target contract reviewed: Hermes v0.21.1, commit 8d79c2ff.

## MCP tool contract (canonical count)

The normative bridge contract is defined in [SPEC.md](SPEC.md). The canonical discovery contract is **27 tools** (unchanged since v1.2.2: v1.2.1's 26 plus local-only `bridge_version`); it becomes 28 tools when only `opencode` health is enabled. The section 18 execution opt-in (v1.2.5 released) adds five more tools for 33; this does not change the released v1.2.4 contract. Other documents should refer here instead of maintaining an independent count. `bridge_version` and `./bridge.sh version` must agree on shared identity fields and must not contact Hermes, Codex, Tunnel, GitHub, or another network endpoint.

## Current context and Hands coverage

- `tests/test_hands.py` covers disabled stable results, additive schema validation, dependency direction, workspace secret-name protection, protected-name case folding, traversal, symlink escape, binary/oversize/hard-link rejection, case-colliding entries, strict-resolver failure, and audit content/path non-leakage.
- `tests/test_mcp.py` verifies discovery of 27 tools, the three read-only Hands tools, and explicit context creation/binding against a disposable fixture. `tests/test_hands_fallback_mcp.py` proves health/list/read continue to work when the Hermes transport is unreachable and the configured Codex binary is absent.
- The Hands path suite includes a deterministic generative invariant: only explicit safe fixture paths may return content; generated traversal, absolute, separator, protected-name, and missing-path candidates must be denied.
- Automated tests are necessary but do not satisfy the remaining WSL2/ext4/DrvFS and Hermes-off/Codex-unavailable live-acceptance gates for v1.2.0.

Installer coverage includes pip presence detection and ensurepip bootstrap for an existing pip-less venv in the non-uv path.

- Core tests cover authenticated discovery, run lifecycle, follow-up sessions, pagination, key redaction, persistence, duplicate suppression, durable recovery, unsafe replay rejection, run/session ownership, approvals, cached output, stop, loopback/redirect guards, model override fingerprinting, follow-up model policy, model discovery and SQLite migration.
- MCP stdio integration covers initialization and the canonical 27-tool discovery contract, diagnostics, local-only heartbeat, model discovery, model-aware submission, usage tools, polling, output retrieval and foreign run rejection.
- Codex tests cover audit redaction/rotation, recovery visibility after a bridge restart, `unknown_exit`, atomic concurrency reservation, start failure, cancellation/timeout races, watchdog enforcement, workspace allowlist enforcement, symlink escape rejection, write approval staging, fixed-argv subprocess/result capture, and model/reasoning policy forwarding.
- Tunnel tests cover secure key loading/mode and generated systemd unit without embedded key.
- CI runs shellcheck and `bash -n` for install.sh, bridge.sh and tunnel.sh.

The test server mocks the Hermes HTTP contract; it does not replace workstation/tunnel validation. Shell syntax checking does not prove runtime integration.

Live acceptance is recorded in `LIVE-ACCEPTANCE-TH.md`: v1.0.0 RC2 validated 19-tool discovery, Hermes idempotent read-only execution, Codex `gpt-5.6-sol` + `low`, local workspace-write approval, and cancellation through the Secure MCP Tunnel. v1.0.1 then passed its WSL2 deployment health check and a no-write/no-network Codex read-only acceptance with no configuration warnings.

## OpenCode health foundation (disabled by default)

- The `opencode` configuration section is optional, additive, and disabled by default (`enabled` defaults to `false`). Strict validation covers the type of `enabled`, an absolute control-character-free `binary` path up to 4096 characters, `version_timeout_seconds` in 1-120, and `max_output_bytes` in 1024-1048576. Enabling without an explicit `binary` is a configuration error. Unknown keys warn and are ignored. See `tests/test_opencode.py`.
- Default discovery stays at the canonical **27 tools**. When `opencode.enabled` is `true`, registration adds exactly one read-only tool, `opencode_health`, and discovery becomes 28 tools. The registration tests and the `tests/mock_opencode_server.py` stdio fixture prove both counts.
- `tests/test_opencode.py` uses fake executables and runs offline. It covers: disabled fail-closed behavior with no process spawn; enabled validation that requires a regular executable file (missing path, directory, and non-executable file are rejected at startup); one valid probe that asserts fixed argv (`binary --version`), symlink acceptance, and version reporting; malformed version rejection (invalid UTF-8, control characters, empty output, output without digits); nonzero exit rejection without output leakage; timeout enforcement with process-group termination; per-stream memory caps for oversized stdout and stderr; descendant cleanup when a child holds the pipes and ignores `SIGTERM` (the group receives `SIGTERM`, then `SIGKILL`); and the leader-reap ordering regression set (`TestOpenCodeCleanupOrdering`), which records real `killpg`/`wait` calls and proves every `killpg` happens before the single leader reap on the success, nonzero-exit, timeout, and pipe-descendant paths, that exit observation is nonreaping `waitid` with `WNOWAIT` and bounded by the probe deadline, that `EINTR` is retried without reaping, and that unknown leader ownership sends no signal.
- Fake executables do not prove real OpenCode CLI behavior beyond the version probe. Live acceptance recorded 2026-10-18 covers `--version` ONLY: the fixed pipeline against the real binary returned `ok: true` with `opencode v2.0.32` under an in-memory configuration (no settings change). In that historical health-only acceptance, task submission, sessions, JSON event output, cancellation, and permissions were unverified and unimplemented. The separate execution record below (v1.2.5 released) covers later work.

## v1.2.2 provenance and durable-worker gates

- `tests/test_version.py` covers worktree enrichment, embedded build-input provenance, archive/malformed-config fail-safe output, CLI parity, and the version action bypassing configured Hands/Hermes backends.
- MCP stdio and Hands fallback suites require 27-tool discovery, including `bridge_version`.
- Codex regression covers the detached worker retaining a real exit record after the local approver instance exits.
- WSL2 live acceptance passed CLI/MCP identity parity, unavailable-upstream behavior, and no secret/path leakage; the durable-worker acceptance separately passed exact marker bytes, terminal exit code, and JSONL result retrieval.

## Dev MCP Events probe fixture (originally planned for v1.2.4 — now deferred, no assigned release)

- `tests/test_events_probe.py` covers protocol discovery, empty-allowlist denial, exact/wildcard label-boundary matching, HTTPS/port rejection, callback challenge and one redacted delivery, idempotent unsubscribe, invalid allowlist forms, and Standard Webhooks signing inputs.
- This fixture test suite does not prove Secure MCP Tunnel, Work-chat subscription, callback ownership, persistence, expiry/refresh, retry, or Hermes terminal delivery. Those require the recorded Dev live probe before any runtime Events implementation.

## v1.2.3 implementation and acceptance contract

The v1.2.3 maintenance scope is limited to the worker-supervision invariant in SPEC.md: a worker that is unavailable MUST NOT cause `unknown_exit` while its Codex child is still alive.

Automated regression coverage includes worker-only loss, child liveness, delayed child exit, cancellation, restart recovery, PID-reuse start-time rejection, and a real unreaped-zombie liveness probe on Linux `/proc`. Automated CI passed on the current PR head.

WSL2 live acceptance passed on commit `7755f1219a54dd4c8cef6d6d17482e8c8c983478`: worker-zombie/child-alive retained `running` with the redacted supervision hint; a later child exit without a terminal record became `unknown_exit`; and cancel after worker loss became `cancelled`. The project interpreter completed 75 tests without `ResourceWarning`. Independent review passed.

Release verification passed for signed tag `v1.2.3` at `c610660637dbdcfa0b8ddb7bbf01ed22ae66055d`. The published archive SHA-256 is `c231f8563543dbfa9eafa240c5e8e15f44434103940352066e65b58162cb5458`. A fresh GitHub download passed both `sha256sum -c SHA256SUMS` and `unzip -t`.

## Legacy stdio discovery guard (released v1.2.4)

- `tests/test_stdio_guard.py` (13 tests): in-memory boundary pump (int/string id reply shape, no params echo, notification pass-through, non-matching requests, metadata preservation, parse-error forwarding, forward failure logged once, EOF) + guarded `stdio_server` lifecycle + real-stdio subprocess probes (pre-init probe, legacy initialize/initialized/tools-list = 27 tools, repeated probes, unchanged `-32602` validation, clean EOF shutdown rc=0).
- Run: `PROJECT_PYTHON=/absolute/path/to/bridge/.venv/bin/python` followed by `env -u PYTHONPATH "$PROJECT_PYTHON" -W error::ResourceWarning -m unittest discover -s tests`

## OpenCode task execution (v1.2.5; SPEC.md section 18)

- Verified 19 October 2026 at code head `e7add7e594fb2cc0029dd53b628c85f9a7c1a87c`: **164/164 tests pass** in WSL with `env -u PYTHONPATH .venv/bin/python -W error::ResourceWarning -m unittest discover -s tests`. Shellcheck and Bash syntax checks pass. [CI at the same code head](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/39212518227) passes. This is implementation/test evidence, not a release claim.
- Historical checkpoints: the initial `ee62fe8` WSL/CI run passed 162 tests, and `85e3bc` passed 163 after the cleanup-confirmation regression. The final config-load regression proves `opencode.execution` produces no false unknown-key warning while genuine unknown keys still warn.
- Coverage: 34 tests in `tests/test_opencode_tasks.py` and one actual SDK stdio lifecycle test in `tests/test_opencode_execution_mcp.py`, in addition to the existing 129 tests (164 total). Contract per SPEC section 18: disabled fail-closed; `opencode.execution` validation (parent enabled + binary, nonempty canonical workspaces/models, control characters, ranges); fixed argv with no `--auto`/`--server`/`--continue`/caller flags and no `OPENCODE_CONFIG*` env injection; prompt over stdin, shell disabled; session minted and stored before spawn (`ses_` shape); idempotency by `request_id` + fingerprint with conflict rejection; global and per-session concurrency 1 with busy rejection; deterministic fixture CLI paths for error-with-exit-0 (must fail), no completion evidence (must fail), streaming events, permission-request detection (`permission_required`), output caps, cancellation race, worker restart, and descendant cleanup under the WNOWAIT invariant (all `killpg` while the leader is unreaped; single reap after the final signal); redaction of `status`/`recent`/audit; 0600/0700 file modes; and 33-tool discovery through the real stdio fixture.
- Baseline parity passed on WSL and CI: 27 default / 28 health / 33 execution. The hosted editing environment passes the execution fixture checks, but its full run has four existing Codex `/proc` failures and one existing zombie-observation error. The four Codex failures reproduce on a clean `f58a36d` checkout; these baseline tests were not changed or skipped to obtain the WSL/CI pass.
- Release preparation (local): `version_info.py` stamped `v1.2.5` (build provenance `release`, reviewed build input `a666d626da1fe716ce4b259d49eedfc3f97acc7d` — `main` with PR #40 merged). A local candidate ZIP built from the release-prep head per RELEASE-RUNBOOK-TH.md Phase B minus tag/publish passed `unzip -t`, the exclusion check (no `.venv/`, `state/`, `.env`, `bridge-config.json*`, `.git/`, `__pycache__/`, single root `hermes-mcp-bridge-v1.2.5/`), and re-extraction: `bridge.py version` from the extracted tree reports version `1.2.5`, source kind `release-archive`, embedded build input `a666d626`, discovery 27; the extracted tree passes the full 164-test suite with `-W error::ResourceWarning`, including the real stdio fixture proofs of 27 default / 28 health / 33 execution tools. No real model call is made. No archive checksum is committed to the source tree.
- Real CLI v2.0.32 through the actual task controller: submission, same-request replay, same-session remembered-context reply and cancellation with observed CLI exit pass. Native absolute-path read/edit and same-session second edit pass with exact fixture-byte checks. Authenticated Dev Work-chat acceptance passed on 19 October 2026 at `e7add7e`: real-model submission, resumed context, request replay/recent and independent byte verification of native file creation; cancellation remains scoped to the earlier controller run and permission-required remains fixture-only; the scoped records are in [LIVE-ACCEPTANCE-TH.md](LIVE-ACCEPTANCE-TH.md); do not infer either from the fixture tests.
- See [OPENCODE-TH.md](OPENCODE-TH.md) for the operator-facing contract. This surface ships in signed v1.2.5; historical candidate records above retain their original evidence scope.


## v1.2.5 — released (19 October 2026)

- Signed annotated tag `v1.2.5`: object `11420f1ae968244195701b296db2f8ce419b793a`, peeled commit `6fbcd7ef278d5e45a95b7328c719c5b01cbcf522`; EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`. Local and fresh-fetch remote `git verify-tag` pass; GitHub reports the signature valid.
- [GitHub Release v1.2.5](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.5) publishes exactly `hermes-mcp-bridge-v1.2.5.zip` and external `SHA256SUMS`. ZIP SHA-256: `1f1c8a583cf7f51a88ec35ca3023c86342220f5baba37faed3f1724b04bf8d5f`.
- Built from the signed tag: 79 files under the single root `hermes-mcp-bridge-v1.2.5/`, no private config/state/venv/env/git/cache entries. Fresh-download `sha256sum -c SHA256SUMS`, `unzip -t` and byte comparison against the built assets pass.
- Extracted identity: version `1.2.5`, release identifier `v1.2.5`, source kind `release-archive`, embedded build input `a666d626da1fe716ce4b259d49eedfc3f97acc7d`, canonical default discovery 27. The signed tag identifies the final commit; the embedded revision identifies its reviewed build input.
- Scope: opt-in OpenCode execution from PR #40; release preparation from PR #41. Candidate WSL/archive suite 164/164 and discovery 27/28/33 pass; exact-head CI `39224170181` passes. Work-chat proof remains scoped to the recorded Dev candidate; cancellation remains controller evidence and permission-required remains fixture-only.
- Production remains v1.2.3; active Dev remains the tested git-worktree candidate. Publishing does not change profiles, runtimes or permission configuration. This post-tag documentation record does not modify the tag or assets.
- Deployment checkpoint (19 October 2026, ~18:44 +07): production was upgraded to released v1.2.5 later that day. Identity, health, discovery, and the execution API listing were verified read-only through the production plugin (`opencode_recent_tasks` returned an empty `jobs` list; no production model task was submitted during this checkpoint, and the checkpoint does not establish production acceptance). See [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md). The bullet above preserves the post-tag record as written at release time.


## Context retention scope — baseline inspection (20 October 2026)

Source `e24fa3e`: context tests 2/2 ผ่านบน Python 3.12.14. Temporary-state probe ยืนยัน recent limit เป็น response limit และ close ไม่ลบ row. Synthetic precheck/close interleaving เขียน binding หลัง close ได้; ไม่อ้าง production incident หรือ native-task reproduction. ดู [scope proposal](CONTEXT-RETENTION-SCOPE-TH.md) สำหรับ phase boundaries และ acceptance ที่ยังต้องทำ. ไม่มี runtime/schema/config/SPEC change และไม่มี full WSL-suite rerun claim จาก docs-only proposal นี้.

## Context P1 — future acceptance contract (SPEC §20)

Operator อนุมัติ scope เมื่อ 20 ตุลาคม 2026 เวลา 15:57:29 +07. [SPEC §20](SPEC.md#20-context-p1--v127-target-scope-approved-released) กำหนด aggregate output, warning/error shape, preview-only CLI, cutoff/batch predicate และ read-only/WAL acceptance สำหรับ implementation review. ต้องทดสอบ early dispatch รวม wrapper override, ไม่มี credential/backend initialization, create acknowledgement เมื่อ observation อ่านไม่ได้, 512/1,024-byte output limits และ no-data-mutation ก่อนอ้าง implemented/accepted. ยังไม่มี P1 tests/runtime หรือผล live preview acceptance จาก amendment นี้; evidence baseline ใน PR #57 คงขอบเขตเดิม.


## Context P1 candidate — PR #59

PR #58 merge `64eb0a1` เป็น contract ก่อน implementation. [Candidate acceptance](CONTEXT-P1-ACCEPTANCE-TH.md) แม็ป tests กับ §20: config/threshold/error/ack, read-only URI/lock wait, early CLI dispatch รวม wrapper override, cutoff/reference/batch และ WAL/permission cases. MCP fixture ตรวจ warning กับ unavailable ผ่าน stdio จริง. เป็น synthetic/local evidence ไม่ใช่ Dev tunnel หรือ production acceptance. ยังไม่อ้าง full-suite pass จาก runtime ของแชต; ใช้ exact-head CI matrix 3.12/3.14 เป็นหลักฐานแยก.


## Context P1 — implementation merged / Dev preparation

PR #59 ผ่าน operator-supplied external APPROVE ที่ `b7ff97a` และ merge ที่ `5685e11`; full suite 203 และ focused context 19/19 เป็นผลที่ reviewer รายงาน. PR ถัดไปเพิ่ม `mock_context_p1_server.py` กับ SDK stdio tests สำหรับ threshold/create acknowledgement และ actual missing/locked DB. Fixture ใช้ isolated registry กับ backend stubs; local/CI ผ่านไม่ใช่ live Secure MCP Tunnel acceptance. ดู [Dev plan](CONTEXT-P1-DEV-ACCEPTANCE-TH.md). Production และ release คงเดิม.


## Context P1 — scoped live Dev checkpoint (20 October 2026)

Candidate `27030bb` บน WSL Python 3.12.3 ผ่าน full suite 206/206, focused context 22/22 และ packaging 3/3 ไม่มี skips; shellcheck/Bash syntax ผ่าน. Parent ตรวจ real Dev connector: cap=3, count+1 lower bound, six successful creates รวม injected-observation failure พร้อม readback/recent 6, missing/locked unavailable อย่างละ 2 calls และ restoration กลับ `e7add7e`. [Live record](CONTEXT-P1-DEV-ACCEPTANCE-TH.md) แยก SDK/source proof จาก operator-selected scenarios และระบุขอบเขต restoration. ยังรอ external review; ไม่ใช่ release/production/native-backend/CLI-through-MCP/read-only-mount acceptance. ไม่มี WSL-suite rerun บน docs-only record head นี้; ผลข้างต้นผูกกับ candidate ที่ทดสอบ.


## v1.2.7 proposal / P1 review status

External live-record review ของ PR #61 ผ่านที่ `6d93808` และ merge ที่ `4513b30`. ผล preparation/live/CI ก่อนหน้ายังคงผูกกับ candidate/reviewed heads เดิม; review นี้ไม่ครอบคลุม proposal note ที่เพิ่มภายหลัง. [Release scope proposal](V1.2.7-RELEASE-DECISION-TH.md) ยังรอ operator decision. ไม่มี WSL-suite rerun หรือ release/production acceptance ใหม่จาก docs-only proposal นี้.


## v1.2.7 target scope approved (20 October 2026)

Operator อนุมัติ [scope v1.2.7](V1.2.7-RELEASE-DECISION-TH.md) เมื่อ 18:47:56 +07 หลัง PR #62 ผ่าน external review. คำว่า proposal/decision pending ข้างต้นเป็นสถานะก่อน approval นี้. ยังต้องทำ release-preparation source/extracted verification และ exact-head CI ตาม runbook; scope approval ไม่เพิ่มผลทดสอบหรือ production acceptance. ไม่มี WSL-suite rerun claim จาก docs-only decision update นี้.
