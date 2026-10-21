# Context P2 — lifecycle/concurrency design proposal

วันที่: 21 ตุลาคม 2026.
สถานะ: **PROPOSAL — รอ review เท่านั้น**. เอกสารนี้ไม่ใช่ SPEC amendment ที่ผ่านการตัดสินใจแล้ว, ไม่ใช่การอนุมัติ implementation, และไม่ใช่การเปลี่ยน contract ปัจจุบัน.
ขอบเขต: docs-only. เอกสารนี้ไม่เปลี่ยน runtime, tests, config, schema หรือ discovery count.
ฐานอ้างอิง: `origin/main` ที่ `420fd76bc79fd1c1128f6f61000786354b374639` (merge ของ PR #66).
ข้อกำหนดเดิมอยู่ใน [SPEC §8](SPEC.md#8-work-contexts) และ [SPEC §20](SPEC.md#20-context-p1--v127-target-scope-approved-released); บันทึก scoping P1/P2 อยู่ใน [CONTEXT-RETENTION-SCOPE-TH.md](CONTEXT-RETENTION-SCOPE-TH.md).

## 1. ขอบเขตและข้อจำกัดของเอกสาร

เอกสารนี้ออกแบบ lifecycle/concurrency ของ context registry สำหรับ P2 ก่อนการอนุญาต destructive prune.

- ทุกข้อ "เสนอ" ในเอกสารนี้ต้องผ่าน [SPEC §14 change control](SPEC.md#14-change-control) ก่อน implementation เพราะแตะ context/session semantics.
- เอกสารนี้ไม่อ้างว่า race ที่บันทึกไว้เป็นหลักฐาน incident ของ production; หลักฐานเดิมเป็นระดับ synthetic registry mutation เท่านั้น ตามข้อความ baseline ใน [CONTEXT-RETENTION-SCOPE-TH.md](CONTEXT-RETENTION-SCOPE-TH.md).
- เอกสารนี้คง tools, tool signatures, config schema version 1 และ discovery count 27 (default), 28 (OpenCode health-only opt-in), 33 (OpenCode execution opt-in) ตามที่ release ปัจจุบันกำหนด; การเปลี่ยนใด ๆ เป็น SPEC amendment แยกในอนาคตเท่านั้น.
- P1 warning/preview คงค่าที่อนุมัติไว้เดิมทั้งหมด; เอกสารนี้ไม่เสนอการเปลี่ยน P1.

## 2. พฤติกรรมปัจจุบันจาก source

ข้อความนี้อ่านจาก source ที่ commit `420fd76`; ไม่มีการเปลี่ยน behavior จากเอกสารนี้.

| เส้นทาง | Source | ลักษณะปัจจุบัน |
| --- | --- | --- |
| create | `contexts.py` `ContextRegistry.create` | INSERT row ใหม่หนึ่ง transaction; ไม่มี binding fields |
| close | `bridge.py` tool `bridge_context_close` → `contexts.py` `ContextRegistry.close` | `_row` (SELECT) อีก transaction แล้ว UPDATE `closed` อีก transaction; row ไม่ถูกลบ; `_row` ปฏิเสธการใช้งาน context ที่ `closed` ไม่เป็น NULL |
| Hermes submit+bind | `bridge.py` `hermes_submit_task` เรียก `core.py` `Bridge.submit` แล้ว `contexts.bind_hermes_run` | submit บันทึก row ในตาราง `runs` (request_id, fingerprint, run_id, result) และคืน `run_id`/`request_id` ใน response ก่อน; bind เป็น precheck SELECT แล้ว UPDATE คนละ transaction |
| Codex submit+bind | `bridge.py` `codex_submit_task` เรียก `codex_core.py` `CodexBackend.submit` แล้ว `contexts.bind_codex_job` | submit INSERT ลงตาราง `jobs` ของ `codex.sqlite3` พร้อม audit `submit` ก่อน; bind เป็น precheck SELECT แล้ว UPDATE คนละ transaction |
| Hermes late observation | `bridge.py` เรียก `contexts.observe_hermes` หลัง task status/result | ค้นหา context ด้วย `hermes_run_id=? AND closed IS NULL` แล้ว UPDATE session; เงื่อนไข `closed IS NULL` อยู่ที่ lookup แต่ lookup กับ UPDATE ยังเป็นสอง statement |
| continuation gate | `contexts.py` `ContextRegistry.hermes_session` | ใช้ `_row` แบบ usable; context ที่ close แล้วไม่ให้ดึง session ต่อ |

### Interleavings ที่สังเกตได้จากโครงสร้างข้างต้น

- close ทำงานเป็นสอง transaction ติดกัน (SELECT แล้ว UPDATE). bind ที่อ่าน precheck ก่อน UPDATE ของ close สามารถเขียน binding ลง row ที่ close เสร็จหลังจากนั้นได้. นี่ตรงกับ synthetic interleaving ที่บันทึกไว้ใน [CONTEXT-RETENTION-SCOPE-TH.md](CONTEXT-RETENTION-SCOPE-TH.md).
- bind ที่ commit ก่อน close คือ state "bound แล้วถูก close". row เก็บ binding เดิม; continuation ถูกปฏิเสธโดย `_row` เพราะ `closed` ไม่เป็น NULL.
- หาก bind ล้มเหลวหลัง backend รับ task แล้ว (เพราะ close, DB error หรือ process จบ) การส่ง task ยังคงอยู่กับ backend store: Hermes run อยู่ในตาราง `runs` และ Codex job อยู่ในตาราง `jobs` ของ `codex.sqlite3`. Tool call คืน error แทน response ปกติ; run/job ยังดึงได้ตาม id ผ่าน status/result และ audit เดิม.
- `observe_hermes` มี guard `closed IS NULL` ที่ lookup แล้ว แต่ยังเป็น check-then-act สอง statement ในหลักการเดียวกัน.
- SPEC §11 ห้าม restart ส่ง task ซ้ำเงียบ ๆ และ SPEC §12 ห้ามนับ transport failure เป็นเหตุ resubmit; ทั้งสองข้อยังใช้อยู่และ design นี้ไม่ขัด.

ข้อความสรุป: baseline มีช่อง check-then-act จากการแยก transaction ของ close/bind/observe; ช่องนี้ไม่พิสูจน์ว่า production เคยเกิด submission หลัง close จริง.

## 3. ค่าและ invariants ที่ design ต้องคง

- SPEC §8: การ close ต้องป้องกัน binding/continuation ผ่าน context นั้นในอนาคต; continuation ต้องระบุ context_id ชัดเจน.
- SPEC §11: ห้าม resubmit หลัง restart; terminal records คงเดิม; migrations เป็นแบบ additive หรือ versioned.
- SPEC §12: transport failure ไม่ใช่เหตุ resubmit/cancel/success inference.
- SPEC §19/§20: contexts ไม่เก็บ prompts/outputs; P1 คงค่าเดิม.
- เครื่องมือ MCP และ CLI เดิมไม่ถูกเพิ่มหรือเปลี่ยน signature ใน scope นี้; config schema คง version 1 จนกว่า SPEC amendment อนุมัติแยก.

## 4. Approach A — conditional atomic UPDATE (ไม่เปลี่ยน schema)

เสนอให้ทุก mutation ที่รับ context_id ใช้ statement เดียวที่เช็คเงื่อนไขในตัว แทน check-then-act:

- `bind_hermes_run`: `UPDATE contexts SET hermes_run_id=?, updated=? WHERE context_id=? AND closed IS NULL`; rowcount เป็น 0 แล้วค้น row แยกเพื่อแยก unknown กับ closed และคืน error คงที่ตามข้อความเดิม.
- `bind_codex_job`: เช่นเดียวกันกับ `codex_workspace`, `codex_job_id`.
- `observe_hermes`: `UPDATE contexts SET hermes_session_id=?, updated=? WHERE hermes_run_id=? AND closed IS NULL` — รวม lookup กับ update เป็น statement เดียว.
- `close`: `UPDATE contexts SET closed=?, updated=? WHERE context_id=? AND closed IS NULL` แล้วค้น row แยกเพื่อรายงาน unknown หรือ terminal state.

### Linearization points และ open/closed semantics

- จุด linearization ของทุก mutation คือ commit ของ statement เดียวของ mutation นั้นใน `contexts.sqlite3`.
- open คือ `closed IS NULL`; closed คือ `closed` มีค่า timestamp; closed เป็น terminal และไม่มี reopen ใน scope นี้.
- close wins: เมื่อ close commit ก่อน bind commit, bind เห็น rowcount 0 และ fail ด้วย error คงที่; row จบแบบ closed และไม่มี binding ใหม่.
- bind wins: เมื่อ bind commit ก่อน close commit, row จบแบบ closed พร้อม binding เดิม; binding ถูกเก็บเป็น historical metadata บน row ที่ close แล้ว; continuation ยังถูกปฏิเสธด้วย `_row`.
- หลัง restart: state ของ statement ที่ commit แล้วคงอยู่; ไม่มี transaction ที่ค้างข้าม crash; ไม่มี auto-rebind และไม่มี resubmit ตาม SPEC §11.
- cross-process: CLI (`bridge.sh`) และ MCP serve เป็น process แยกแชร์ไฟล์เดียว; การ commit ของ SQLite เป็นกลไกเดียวที่ guarantee ordering ข้าม process; design นี้ไม่พึ่ง in-process lock เพียงอย่างเดียว.
- ไม่มี transaction ค้างข้าม network/external call: ทุก bind เกิดหลัง submit ของ backend คืนผลแล้ว; submit ไม่ถูกเรียกข้างใน transaction ของ registry.

### Failure หลัง backend ยอมรับ (acceptance-before-binding)

- ownership ของ task อยู่ที่ backend store เดิมตั้งแต่ submit: ตาราง `runs` ของ Hermes และตาราง `jobs` ของ Codex พร้อม audit event การ submit.
- ห้าม retry โดยไม่ตรวจสถานะก่อน: ไม่มี resubmit อัตโนมัติ; `request_id` ที่ reuse ต่าง input ถูกปฏิเสธอยู่แล้วใน `core.py` submit.
- outcome ที่ไม่ทราบถูกแยกชัด: ถ้าผลจาก backend มาไม่ครบ ให้คงพฤติกรรม unknown ของ status/result เดิม; ห้ามแปลงเป็น completed หรือ failed.
- reconciliation เสนอเป็นขั้นตอนชัดเจนของผู้ใช้: ดึง status/result ตาม `run_id`/`job_id` เดิม แล้ว (ถ้าต้องการ) บันทึก binding ใหม่ด้วยเครื่องมือเดิมต่อ context ที่ยัง open; ถ้า context close แล้ว ให้ผูก context ใหม่เมื่อ SPEC อนุมัติเส้นทางนั้น.

### Tradeoffs ของ Approach A

| ประเด็น | ผล |
| --- | --- |
| ขอบเขตเปลี่ยนแปลง | เล็ก; ไม่เพิ่มตาราง, ไม่เปลี่ยน config keys, ไม่เปลี่ยน tool signature |
| ช่องที่ปิดได้ | check-then-act ทั้งของ bind และ observe; close กลายเป็น idempotent-capable |
| ช่องที่ยังไม่ปิด | crash ระหว่าง submit กับ bind ยังคงทำให้ run ไม่มี binding; ต้องพึ่ง reconciliation ด้วยมือตาม id |
| Error contract | ถ้าข้อความ error เดิมคงที่ ไม่เปลี่ยน response shape; ถ้าต้องการ error ใหม่ ต้องผ่าน §14 |
| ความเสี่ยง | ต่ำ; ลักษณะ UPDATE มีอยู่แล้วใน `observe_hermes` และตาราง `runs` |

## 5. Approach B — durable intent/reservation (ต้องผ่าน SPEC/schema review)

**ตัวเลือกนี้เป็น proposal ที่ต้องมี SPEC amendment แยกและ migration review; schema version 1 ปัจจุบันไม่รองรับโดยอัตโนมัติ และเอกสารนี้ไม่อ้างว่ารองรับ.**

โครงร่างที่พิจารณา:

- เพิ่ม store ของ submission intent ที่บันทึกก่อนเรียก backend เช่น state `intent` → `accepted` → `bound` ต่อ 1 submission พร้อม backend id ที่ได้หลังยอมรับ.
- Hermes submit รับ `request_id` จาก caller อยู่แล้ว จึงผูก intent กับ request ที่รู้ค่าล่วงหน้าได้; Codex job_id ถูกสร้างภายใน `codex_core.py` จึงต้องออกแบบการสร้าง id ล่วงหน้าเพิ่ม.
- ถ้า crash ระหว่าง call: state ค้างที่ `intent` หรือ "accepted-unknown"; restart reconciliation อ่าน status ตาม id ที่รู้และต้องยังห้าม resubmit ตาม §11/§12.
- tradeoffs: ปิดช่อง crash ระหว่าง submit กับ bind ที่ Approach A ไม่ปิด; แต่ต้องเพิ่มตาราง/state machine, ต้อง migration อย่างระวัง (§11), ต้องเพิ่ม tests จำนวนมาก และต้อง review SPEC §8/§11/§14; ค่าที่ได้มากมายอยู่ที่กรณี crash ซึ่ง §11/§12 และ backend store เดิมช่วยป้องกัน resubmit/lost-result อยู่แล้ว.

## 6. เปรียบเทียบสอง approach

| เกณฑ์ | Approach A (conditional UPDATE) | Approach B (durable intent) |
| --- | --- | --- |
| แก้ interleaving ปัจจุบัน | ครบ สำหรับ close/bind/observe | ครบ |
| แก้ crash ระหว่าง submit→bind | ไม่ครบ (พึ่ง reconciliation ด้วยมือ) | ครบเชิงระบบ |
| Schema | ไม่เปลี่ยน | เพิ่มตาราง/state; ต้อง migration |
| SPEC ที่ต้องแก้ | §8/§14 review ตามการเปลี่ยน semantics | §8/§11/§14 review + migration |
| ขนาดงาน tests | ชุด interleaving matrix เล็ก | matrix เดิม + state machine + crash cases เพิ่ม |
| ความเสี่ยง production | ต่ำสุด | กลาง; มี state ใหม่ต้องดูแล |

คำแนะนำเบื้องต้นที่ยังไม่ผูกมัด: เริ่มจาก Approach A เป็นขั้นแรก และเก็บ Approach B ไว้พิจารณาเป็น SPEC amendment แยกเมื่อมีกรณีจริงที่ Approach A ไม่พอ. ทั้งสองทางต้องผ่าน §14 review ก่อน implementation.

## 7. ชุดทดสอบที่เสนอ (deterministic, ไม่ใช้ sleep)

ทุกกรณีคุมจังหวะด้วย `threading.Event`/`threading.Barrier` หรือ hook ที่จุด commit เพื่อ block ตามจุดที่กำหนด; ห้ามใช้ time.sleep เพื่อจัดเรียง.

| กรณี | ควบคุมอย่างไร | Observable ที่ต้องผ่าน |
| --- | --- | --- |
| close wins | Barrier ก่อน commit ของ bind; ให้ close commit ก่อน | bind คืน error คงที่; row closed; ไม่มี binding; audit มี close; ไม่มี duplicate job |
| bind wins | Barrier ก่อน commit ของ close; ให้ bind commit ก่อน | row closed พร้อม binding เดิม; continuation ถูกปฏิเสธ; `observe_hermes` ไม่เขียนลง closed row |
| submit accepted → close → bind | Event หลัง backend ยอมรับ submit แล้วปล่อยหลัง close commit | tool คืน error; run/job ยังดึงได้ตาม id; mock backend นับ submit 1 ครั้ง; request_id reuse ถูกปฏิเสธ |
| crash/restart ระหว่าง submit กับ bind | สร้าง bridge ใหม่จาก state เดิมหลัง submit | row `runs`/`jobs` คงอยู่; ไม่มี resubmit; context ยัง open และไม่มี binding; ไม่มี auto-rebind |
| concurrent actors | สอง process ใช้ state เดียว; ทดสอบคนละ context และ context เดียว | คนละ context สำเร็จทั้งคู่; context เดียวจบตาม commit order ใด order หนึ่งที่ผ่านเกณฑ์ close/bind wins; ไม่มี state ที่ทำลายเกณฑ์ |
| backend unavailable ตอน submit | mock backend ให้ unavailable | error explicit; ไม่มี bind; context ไม่เปลี่ยน; audit ไม่บันทึก submit |
| transport timeout หลัง acceptance | mock ให้ตอบช้า/ตัด connection หลังยอมรับ | status คง unknown เดิม; ไม่ resubmit; ไม่ infer success |
| double close | เรียก close สองครั้ง | พฤติกรรมตามที่ operator เลือก (ดู §9); ทั้งสองแบบเขียน test ได้หลังเลือก |

เกณฑ์รวม: ทุก case ต้องแสดง row state, ลำดับ audit event ที่เกิดจริง, จำนวน submit ที่ mock backend เห็นเท่ากับ 1 ในกรณีที่ยอมรับ และข้อความ error คงที่เดิมเมื่อไม่เปลี่ยน contract.

## 8. แยก lifecycle fix ออกจาก P2 prune mutation

- การแก้ lifecycle ข้างบนไม่อนุญาต destructive prune; P2 apply/delete ยัง deferred จนกว่าจะมี scope/SPEC/operator local approval แยก ตาม [CONTEXT-RETENTION-SCOPE-TH.md](CONTEXT-RETENTION-SCOPE-TH.md).
- P1 warning/preview คงเดิมทั้งหมด: cap 1,000 rows, preview อย่างน้อย 30 วัน, batch default 100/สูงสุด 1,000, predicate แบบ unbound.
- เมื่อ P2 เปิดจริง การอนุมัติต้องผ่าน atomic eligibility recheck: predicate ต้องถูกตรวจใหม่ใน transaction เดียวกับ DELETE; preview ไม่ใช่ authorization และไม่ใช่ snapshot ถาวร.
- stale plan: plan ที่เก็บไว้ต้องถูกสร้างใหม่และตรวจใหม่ก่อนใช้; ห้าม execute plan เก่าโดยไม่ recheck.
- backup/recovery: ต้องมี backup ก่อน mutation พร้อม audit ที่มีเฉพาะ action/count/result; ไม่มี labels/refs/content.
- unknown/active refs: rows ที่มี reference ใดของสี่ fields ไม่เป็น NULL ถูก skip; ไม่ใช้ upstream 404 หรืออายุ row เป็นหลักฐาน terminal เด็ดขาด.
- การแก้ lifecycle เป็นข้อสังเกตเพิ่มเติม: เกณฑ์ deterministic interleavings ใน acceptance ของ P1 เดิม (ข้อ 111 ของ [CONTEXT-RETENTION-SCOPE-TH.md](CONTEXT-RETENTION-SCOPE-TH.md)) ยังคงเป็นเงื่อนไขก่อนเปิด P2.

## 9. Operator decisions ที่ยังค้าง

1. Double-close semantics: คงพฤติกรรมปัจจุบัน (error "Context is closed; create a new context_id instead.") หรือเปลี่ยนเป็น terminal response แบบ idempotent; การเปลี่ยนนี้แตะ close contract และต้องผ่าน §14.
2. ข้อความ error ของ bind หลัง close: คงข้อความเดิม หรือเพิ่ม error เฉพาะกรณี; การเพิ่มต้องผ่าน §14.
3. การบันทึก bind ที่ถูกปฏิเสธเพราะ close ลง audit เป็น event ใหม่หรือไม่; หากเพิ่ม ต้องระบุ fields ที่ปลอดภัยตาม §10/§19.
4. Approach B (durable intent) จำเป็นหรือไม่ในระยะนี้; ถ้าใช่ ต้องเปิด SPEC/schema review แยก.
5. การให้ tool คืน backend id ใน response เมื่อ bind ล้มเหลว: เสนอเป็นทางเลือกเพื่อการ reconciliation; ยังไม่เปลี่ยน contract จนกว่า §14 อนุมัติ.

คำแนะนำรายข้อ พร้อมทางเลือก/ผลต่อ contract และร่างถ้อยคำ amendment ของทั้ง 5 ข้อ (ยังไม่มีผลจนกว่า operator อนุมัติและ SPEC PR แยก merge) อยู่ใน [decision packet](CONTEXT-LIFECYCLE-DECISION-PROPOSAL-TH.md).

## 10. ขอบเขตที่เอกสารนี้ไม่แตะ

- ไม่แก้ runtime, tests, config, schema, tool signatures, discovery counts หรือ backend ใด ๆ.
- ไม่เปลี่ยน P1 ที่ merge แล้ว; ไม่เปิด P2 apply/delete.
- ไม่แตะ Hands, MCP Events และ capability gates เดิม.
- ไม่ทำ release, deployment หรือการเปลี่ยน production.
