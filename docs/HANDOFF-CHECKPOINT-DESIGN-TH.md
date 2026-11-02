# Verifiable Handoff / Checkpoint v1 — design และ gap analysis

วันที่ตรวจ: 2 พฤศจิกายน 2026 (Asia/Bangkok). **DESIGN CANDIDATE / ยังไม่มี runtime implementation**.
รับงานจากใบส่งต่อ HERMES-HANDOFF-CHECKPOINT-RECOVERY-20261102.md
(SHA256 `528df62443378d97685d6ca048be9a40eef2d9228feb2c934ec728fb455de529`); ไม่คัดลอก private packet
หรือเพิ่มสิทธิ์จากข้อความในใบส่งต่อ ชุดนี้เป็น delivery 1: design/schema/แผนทดลองก่อน implementation
บน branch แยกจาก #112 ไม่เพิ่มเลข E ไม่ปิด S24 และไม่เรียก Hermes/Dev/production

## 1. Baseline ที่ตรวจจริงและขอบเขต

Repository ยืนยันจาก GitHub และ local remote: `sc28249782/hermes-mcp-bridge`.
main `93e9601f74b3e0bc1d963d65635d82f7083eca8a`; workspace สำหรับ review นี้สร้างแยก
และตรวจ Git blob SHA ของ main ครบ 175 ไฟล์ ไม่มี AGENTS.md ใน main tree หรือ workspace scan
PR ที่เปิด: #80 `3a566bb3` / #96 `5c24f9d1` / #112 `84b1ec3e` ทั้งหมด draft
ไม่ใช้ local HEAD เก่าหรือชื่อ Project เป็นหลักฐานว่าเป็น main ล่าสุด

Roadmap บน main ยังมี snapshot ก่อน merge #110/#111; ทั้งสองรวมอยู่ใน main ข้างต้นแล้ว
สถานะ S24 ปัจจุบันตรวจจาก draft #112 ที่ exact head และบันทึกผลจริงที่ `99271208`:
FOUR consumed archive invocations, THREE digest matches, E12 UNKNOWN, attempt four
HOLD/BACKSLASH ไม่มี completed catalog; guards ปิดอยู่ R1 NOT AUTHORIZED / R2 HOLD
private binding packet version 16 ยังคงเป็นร่างก่อนขอ scope ไม่ใช่คำสั่งรัน ไม่เผยแพร่ค่าในนั้น
J0 พักตามคำสั่ง operator ให้ทำ handoff ก่อน; #80/#96 และ A6/A7 ยังไม่เปลี่ยน
release/deployment record ล่าสุด v1.2.8 ไม่ได้ตรวจ production สด

## 2. สิ่งที่มีแล้วและช่องว่างจาก source

| ส่วน | หลักฐานที่ main / สิ่งที่ทำอยู่ | ช่องว่างที่ checkpoint ต้องไม่กลบ |
| --- | --- | --- |
| Hermes submit | core.py: Bridge.submit / tests/test_bridge.py: test_duplicate_and_restart_do_not_rerun, test_lost_acceptance_durable_replay | request ID+fingerprint เดิม; uncertain replay ต้อง durable capability และ window 23 h; ไม่มีสิทธิ์สร้าง ID ใหม่หรือเดา input จากสรุป |
| Hermes result/status | SPEC §§7–12/19; core.py: metadata filtering และ result paging | native completed/ACK ไม่ใช่ user goal success; ผลหน้าเดียวไม่ใช่ immutable full artifact |
| Codex worker | codex_core.py / codex_worker.py; tests/test_codex.py: restart/unknown_exit/live-child/cancel-timeout race | submit ไม่มี request_id parameter สำหรับ idempotent replay; ACK หายและ job_id ไม่ทราบต้อง HOLD ไม่ submit ซ้ำ |
| OpenCode | opencode_tasks.py: submit, _reconcile, status, result, cancel; tests/test_opencode_tasks.py: test_atomic_concurrent_idempotency, test_request_conflict | same request/fingerprint ได้ job เดิม; completed เป็น native turn ไม่ใช่ goal success; unknown_exit ยังขวาง admission |
| Contexts | contexts.py: ContextRegistry / context_read.py; SPEC §§8/21/22; tests/test_context_binding_unresolved.py | metadata-only, closed ไม่เปิดใหม่; binding_unresolved ไม่ใช่ backend failure; ห้าม wrapper readback/rebind อัตโนมัติเพื่อ reconcile |
| Cancellation | SPEC §7/§18.5; Codex/OpenCode worker ownership และ confirmed cleanup | cancel_requested ไม่ใช่ cancelled; checkpoint ไม่ signal PID/PGID และไม่สร้าง replacement worker |
| Local Hands | SPEC §9 / hands_core.py / tests/test_hands.py | read-only list/read/health ไม่มี execution task/session resume; handoff ไม่เพิ่ม write/exec tool |
| Privacy | SPEC §§8/10/19 / docs/SECURITY.md | checkpoint ต้อง metadata-only ไม่ใช่สำเนา prompt/output/chat; operational store เดิมแยกจาก audit/context |
| Recovery ทั้ง task | ไม่มี checkpoint artifact/schema หรือ cross-session acceptance verifier ใน main tree | ต้องแยก native lifecycle, caller goal, evidence, authorization, lessons และตรวจ binding ใหม่ |

ข้อสังเกตที่เปลี่ยนแผน: CodexRunner.status() อาจ enforce timeout ผ่าน cancel(); OpenCodeTasks.status()
เรียก _reconcile และแก้ state จึงห้ามออกแบบ generic reconcile ว่า status call ทุก backend เป็น pure read
v1 ชุดนี้ไม่เรียก methods เหล่านั้นหรือ import runtime ระหว่าง load/validate checkpoint
future adapter ต้องทบทวน side effects/authority ของแต่ละ call ก่อนใช้งานจริง

## 3. v1 scope และ schema

[JSON Schema](schemas/handoff-checkpoint-v1.schema.json) เป็น proposed metadata format
[ตัวอย่าง](examples/handoff-checkpoint-v1.synthetic.json) เป็น synthetic ทั้ง task/IDs/timestamps
checksum เป็นค่าคำนวณจริงของ payload ตัวอย่าง ไม่ใช่ backend receipt หรือ approval
ไม่เพิ่ม MCP tool/config/backend status, ไม่เปลี่ยน context DB หรือ existing submit response
นี่เป็น design attachment ไม่ใช่ amendment ที่มีผลแทน SPEC; runtime adapter/API/storage ใหม่
ต้องผ่าน §14 และ implementation review ก่อน โดยเฉพาะ privacy/security/lifecycle delta ใด ๆ

Envelope มี schema_version, payload และ payload_sha256 เท่านั้น:
checksum = SHA256 ของ UTF-8 compact sorted-key JSON payload, ensure_ascii=true,
allow_nan=false ไม่มี trailing LF ใน bytes ที่ hash; integer fields ไม่รับ bool, duplicate keys/NaN/Infinity
ต้องถูก reject ก่อน schema validation; date-time format ต้อง enforce ด้วย checker ไม่ใช่ annotation ล้วน
JSON Schema ตรวจโครงสร้าง ไม่ตรวจ digest/foreign keys/authority

| ข้อมูล | Proposed fields และความหมาย |
| --- | --- |
| Current state | checkpoint_id/chain_id/generation/parent_sha256/created_at/writer_id; goal_ref/criteria_refs/pending_step_refs/next_action; repository SHA/branch/worktree state; backend IDs; native lifecycle observation |
| Evidence | bounded list ของ opaque evidence_id, kind, sha256/size, verified_at/verifier_ref/verdict; verification ใช้ acceptance profile/evidence IDs ไม่รับ worker prose เป็น proof |
| Lessons | lesson_ref/applicability_profile_ref/version_ref เท่านั้น แยกจาก evidence; ไม่ execute instruction หรือย้าย lesson เป็นข้อเท็จจริง |
| Authorization | authority_ref/scope_refs/snapshot_state/expires_at; authorizes_actions=false เสมอ; ต้องอ่าน authority ปัจจุบันภายนอก checkpoint ใหม่ |
| Provenance/reconciliation | error enum, logical_submit_attempts/observation_attempts/retry_policy_ref, last_reconciliation; เป็น observations ไม่ใช่ budget grant |

ทุก object ปิด additionalProperties; จำกัด envelope input 64 KiB, depth 16, evidence <=32,
refs <=32 ต่อ list และ opaque ID <=128 อักขระ ไม่มี raw path/URL/argv/prompt/output/exception text
hash of secret payload อาจรั่วจากการเดาได้ จึงไม่เพิ่ม fingerprint ของ prompt ใหม่ลง checkpoint:
input_fingerprint_ref เป็น opaque reference ไป existing protected backend record ไม่ใช่ raw digest
workspace/provider/writer/verifier/authority refs ต้อง resolve ใน mapping ที่ operator ควบคุม ไม่ใช่ path
ไม่มีการ dereference refs หรือเดิน directory จาก JSON ระหว่าง validation

Goal/acceptance/pending work เป็น refs ไป reviewed task dossier; ไม่มี free-form goal summary ใน metadata
human handoff ต้องมี dossier ที่ยังเข้าถึงได้อย่างถูกสิทธิ์ มิฉะนั้น HOLD/MISSING_DOSSIER
checkpoint ไม่ย้าย prompt/result ไป contexts หรือ audit; ไม่สร้าง credential/approval reader อัตโนมัติ
proposed private storage แยกจาก allowed workspace, owner-only POSIX 0700/0600; same-UID attacker
หรือ hostile host อยู่นอกการป้องกันนี้ checksum ไม่ใช่ authentication และ permission ไม่ใช่ encryption
Windows/DrvFS ACL semantics ยังไม่อยู่ใน v1 writer scope ต้องออกแบบเพิ่มก่อนใช้จริง

## 4. Atomic store, replay และ concurrency — ยังเป็น design

ใช้ SQLite private store ใหม่แยกจาก contexts/jobs; ไม่ migrate/แก้ original state rows
หนึ่ง BEGIN IMMEDIATE transaction เก็บ immutable envelope row + update chain head แบบ
compare-and-swap จาก expected generation/digest; conflicting writer ต้อง rollback ทั้ง transaction
ใช้ synchronous=FULL; private DB/journal permissions ต้องตรวจจริงใน implementation
reader อ่าน committed snapshot ตรวจ envelope bytes/digest/schema/current head ก่อนทำแผน
ไม่อาศัยความใหม่ของ created_at หรือนาฬิกาข้ามเครื่องเป็น replay proof

Crash ก่อน commit เห็น head เก่า; หลัง commit เห็น head ใหม่ครบ ไม่มี half head/payload
checkpoint ID ซ้ำต้องปฏิเสธ; generation เริ่ม 1,parent=null จากนั้น parent เท่ากับ committed predecessor
sequence/generation เป็น scope ของ chain ไม่ใช่ global task authority concurrent recovery สองตัวที่อ่าน
head เดียวต้องไม่สร้าง side effect ทั้งคู่: store CAS ป้องกัน competing checkpoint commit เท่านั้น
ไม่ใช่ exactly-once dispatch ต้องมี adapter-owned reconciliation/admission authority ก่อน action
v1 planner เสนอ action ไม่ dispatch จึงไม่สร้าง duplicate side effects

ไฟล์ export/human summary ไม่เป็น head authority; ถ้ามีภายหลังต้อง atomic temp/fsync/rename และ
ตรวจเทียบ committed store อีกครั้ง ห้าม resume จาก export เก่าล้วน ๆ Store rollback ทั้งก้อนหรือ
same-UID rewrite ไม่ถูกตรวจได้ด้วย checksum/CAS ภายในก้อนเดียว ต้อง trusted external anchor
หรือ HOLD/reconciliation_required; ไม่อ้าง anti-replay ต่อการคืน snapshot ทั้ง host
retention v1 เสนอเก็บ explicit task chains จน operator close แล้ว cleanup แยกอย่างอนุมัติ
ไม่มี automatic prune ที่อาจลบ evidence ของ unresolved execution; bound chain rows ต้อง fail closed
เมื่อถึง configured cap (source/limit ต้อง bind ตอน implementation)

## 5. Recovery state machine และ backend capability matrix

Recovery state เป็น local planner label ไม่เพิ่ม backend statuses:

| Observation | Required planner outcome |
| --- | --- |
| invalid/corrupt/unsupported/stale generation | HOLD พร้อม fixed error enum ไม่มี network/submit/cancel |
| binding/dossier/authority ไม่ครบหรือเปลี่ยน | HOLD เฉพาะ actions ที่ต้องพึ่ง binding; metadata inspection ที่ยังมีสิทธิ์ทำต่อได้ |
| submission_unknown + Hermes ID/input refs ครบ | reconciliation_required; guarded replay เป็นทางเลือกเฉพาะเมื่อ user scope/capability/window/input เดิมครบ ไม่ใช่ default |
| submission_unknown + OpenCode request/fingerprint refs ครบ | reconcile ผ่าน existing protected job mapping; no new ID/new session; idempotent admission ตาม §18.5 เท่านั้น |
| submission_unknown + Codex job_id ไม่ทราบ | HOLD; ไม่มี idempotent request replay contract ห้าม recent-by-prompt matching หรือ resubmit |
| running หรือ cancel_requested | observe original owned job ตามสิทธิ์; ไม่ส่ง cancel ซ้ำหรือ infer terminal |
| native terminal/completed | retrieve bounded actual evidence ตามสิทธิ์ แล้ว verifier เทียบ acceptance profile; ยังไม่ใช่ goal_verified |
| unknown_exit / unknown / binding_unresolved | preserve native uncertainty; reconciliation_required; ไม่แก้ row ไม่บังคับ terminal/rebind |
| verified evidence + matching bindings/criteria | goal verification snapshot may be verified; resume ครั้งหน้าต้องตรวจใหม่ ไม่ inherit proof/authority |

ลำดับ semantic preflight: load/no side effects -> envelope/schema/digest/head -> task/authority scope
-> repository/workspace/artifact binding -> backend capability/ownership -> permitted reconciliation
-> original status/result evidence -> verifier decision -> next action proposal การขอ observation ที่อาจ mutate
ต้องผ่าน authority ก่อนเรียก ไม่ใช้ current checkpoints เป็น authority sources

Hermes continuation ใช้ session ที่ status/result ของ bridge คืนและ ownership ตรงเท่านั้น;
OpenCode resume ต้อง owning completed session + same canonical workspace/model และเป็น new job
ที่อนุมัติแยกจาก retry logical submission เดิม; Codex ไม่มี conversation resume; Hands ไม่มี job resume
ต้องเก็บ backend-native statuses ไม่ flatten unknown_exit/permission_required/expired/timed_out ให้เป็น failed
และไม่เปลี่ยน terminal rows หรือ §§22–24 disposition/acceptance gates

## 6. Privacy/threat and exit criteria

| Threat | Proposed control / remaining boundary |
| --- | --- |
| truncated/corrupt/duplicate/nonfinite/unsupported JSON | bounded strict parser + schema + canonical digest, no parser recovery |
| stale/replayed checkpoint | committed head/generation/parent check; full-store rollback requires external authority/reconciliation |
| path/symlink/owner substitution | private resolved root + no-follow/descriptor-bound store admission; exact Linux support to prove before writer source acceptance |
| prompt/secret through metadata/lesson/error | opaque refs, closed enums/keys; no raw input/output/logging; resolve only through existing protected authority |
| native complete forged or artifact drift | independent verifier/current artifact hash/criteria; native turn and goal success separate |
| duplicate dispatch / concurrent readers | planner does not dispatch; future backend-specific durable admission, no generic request-ID shim |
| expired approval or malicious checkpoint instruction | snapshot never authorizes, no free-form command fields, no automatic submit/cancel/approval |

Design exit: schema/semantic rules, backend gaps, privacy/store/lifecycle choices และ
[preregistered recovery plan](HANDOFF-RECOVERY-EXPERIMENT-PLAN-TH.md) ผ่าน independent review
แล้วจึงทำ PR เล็กสำหรับ standalone offline validator/planner + immutable store/fixtures
ไม่ hook bridge/MCP/CLI หรืออ่าน live DB ใน PR นั้น ก่อน runtime adapter ต้อง review แยก
[Session checklist](HANDOFF-SESSION-CHECKLIST-TH.md) ใช้เป็นวิธีทำงานระหว่างรอได้
ยังไม่มี measured gain, runtime recovery success หรือ implementation acceptance จากเอกสารชุดนี้
J0 คงพัก; R1 NOT AUTHORIZED / R2 HOLD; #80/#96/#112, release/deployment คงเดิม

## Validation ของ design attachment ชุดนี้

Local JSON Schema Draft 2020-12 metaschema check ผ่าน; synthetic example 1 รายการผ่าน,
22 structural mutations ถูกปฏิเสธ รวม extra keys/schema/date/authority flag/generation/
parent/enum/ref bounds/verified-without-proof ค่า canonical payload digest คำนวณซ้ำตรง
ตัวตรวจใช้ jsonschema 4.25.1 และ rfc3339-validator 0.1.4 ใน temporary validation environment
ไม่เพิ่ม dependency ลง requirements หรือ runtime ตอนแรก bare format checker ไม่ reject
invalid timestamp เพราะ optional checker ยังไม่มี; เพิ่ม checker แล้ว negative case ผ่านตามเดิม
ไม่ลบ assertion หรือเปลี่ยนกฎ schema เพื่อให้เขียว Well-shaped digest ผิดยังผ่าน schema
แต่ checksum comparison ปฏิเสธ จึงไม่อ้างว่า structural schema แทน semantic validator ได้
links/fragment/whitespace ผ่าน; recovery trials=0 / runtime calls=0 / measured gain=NOT_MEASURED
existing exact-head CI เป็น regression ของ baseline ไม่ใช่ผลทดลอง recovery protocol นี้
