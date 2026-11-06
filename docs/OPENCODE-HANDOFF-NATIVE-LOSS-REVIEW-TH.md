# Observer package 4 — native O/S loss controls candidate

## 1. Checkpoint

Parent `83aacfc10eb9fb2ddf704d1883eee07eb922e78e` ได้รับ operator-supplied
round-10 APPROVE สำหรับ native C helper integration ตามข้อความที่ผู้ใช้ส่งมา
เป็น record ของข้อความนั้น ไม่ใช่ GitHub review submission; ไม่มี timestamp
ของ review จึงไม่เติมเอง. Candidate นี้รอ independent exact-source review

แก้ fixlist รอบ 10: ลบบรรทัดว่างท้าย `observer_native.py` หนึ่งบรรทัด
source เดิมเท่ากับ source ใหม่บวก newline หนึ่ง byte; AST/พฤติกรรมไม่เปลี่ยน
อัปเดต source hash/byte count ตามจริง ไม่ใช้ hash เดิมกับ bytes ใหม่
[package 3](OPENCODE-HANDOFF-OBSERVER-NATIVE-REVIEW-TH.md) เป็น historical record
ของ parent; local 36 และ CI เดิมในนั้นไม่ใช่ผลรันใหม่ของ candidate นี้

PR #117 คง draft/unmerged; B1–B7 OPEN; OA ไม่มี whole-row PASS/CLOSED;
J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN
ไม่มี Dev/pilot/backend/model/API/config/credential action, original goal evaluation,
checkpoint/receipt append, archive invocation, release หรือ deployment

## 2. เพิ่มหลักฐาน OA06 ภายใต้ fixture profile เดิม

[Observer/adoption contract](OPENCODE-HANDOFF-OBSERVER-ADOPTION-CONTRACT-TH.md)
OA06 ต้องตรวจ O/S loss ร่วมกันระหว่าง hung/prefix/nonreading H
package 3 มี actual native S-only loss และ parent startup มี inert O/S loss
รอบนี้เพิ่ม **8 real native process schedules**: สี่ phase × สอง signal orders

| Phase | สิ่งที่ actual native H ทำถึงก่อน notification | สภาพขณะ O/S ถูก kill |
| --- | --- | --- |
| nonreading | retained-FD exec เข้า C wrapper แล้ว; ยังไม่เรียก accepted_main และไม่อ่าน stdin | H รอ private read barrier; ignore TERM |
| read_lock | accepted C capture อ่าน context ใน SQLite transaction แล้ว และยังถือ SHARED read lock ก่อน COMMIT | test-only control hook รอ barrier; native SIGALRM 1 s คงอยู่ |
| first_frame | native context capture ผ่าน COMMIT/close; first length header และ complete first payload ถูก write จริง | H ค้างใน test-only write hook ก่อน emit คืนค่า; ยังไม่อ่าน request ถัดไป |
| complete_prefix | unchanged accepted_main ส่ง native frames ครบ context/job/context และ return 0 แล้ว | H ค้างก่อน process exit; prefix ไม่ใช่ FINAL |

แต่ละ phase ทดสอบ O→S และ S→O โดย **back-to-back pidfd SIGKILL sends**
ไม่มี wait/reap ระหว่างสอง sends; จึงไม่อ้าง atomic simultaneous kernel event
ก่อนคืน execution ให้ source R harness ยืนยัน O/S pidfds ready ทั้งคู่และ H pidfd
ยังไม่ ready จริง แล้ว source R จึงดำเนิน adoption/cleanup ตาม path เดิม
ไม่มี numeric PID/PGID signal, process-group cleanup, host process scan หรือ respawn

ทุก barrier อยู่ใน **test-only compiled C shim** ของ unchanged `oc_snapshot_vfs.c`
ไม่แก้ production C helper/headers หรือ native runner semantic ใด
read_lock shim compile ด้วย OC_CONTROL_BUILD และเปลี่ยนเฉพาะการส่ง
CONTROL_READ_LOCK ไป private phase pipe เพื่อไม่ปล่อย diagnostic เป็น frame
normal positive build ยังคงไม่มี OC_CONTROL_BUILD/OC_CONTROL_AUTHORIZE

Test-only FD 198 เป็น phase notification write end, FD 199 เป็น never-released
barrier read end; trusted fixture R สร้าง pipe ทั้งสองและเก็บ write end ของ barrier
ไม่ให้ EOF ปลด H ก่อน stimulus. Closure hooks retain สอง FD นี้เฉพาะแปด controls
ไม่ใช่ native production launch handshake และไม่เข้าทาง public runner config
ไม่มี actor/watchdog เพิ่ม: R/O/S/H สี่ internal actors เดิม
compiler/build subprocesses จบก่อนเริ่ม R; ไม่ใช่ deployment actor-budget evidence

R harness อ่าน phase byte เพื่อจัดเวลาฉีด fault เท่านั้น ไม่ใช้ byte นี้แทน goal,
native result, original FINAL หรือ production authority. Public record มีแค่
phase/order และ booleans phase_seen/both_exited/h_live_after_loss
ไม่ส่ง PID, FD values, nonce, paths, raw output หรือ exception contents

## 3. Expected กับ measured results

Expected: G ส่งแล้ว; O/S ตายจริง; H ยังมีชีวิตตรง adoption boundary;
source ต้อง reap O/S แล้วพิสูจน์ direct adopted child ก่อน retained-pidfd stop H
helper exit/reap/EOF แยกจาก original FINAL; ไม่มี FINAL => UNKNOWN เสมอ

Author-local Python 3.12.14, Linux x86_64/native SQLite 3.45.1:
**44/44 OK**, exit 0, ResourceWarning-as-error, umask 022, ไม่มี skip
ประกอบด้วย original 36 test methods ซึ่ง AST/ทุก assertion เดิมคงอยู่ +8 ใหม่
มี **42 isolated R process cases** + manifest + source-path audit

Actual ทั้งแปด schedules: phase_seen=true, both_exited=true,
h_live_after_loss=true, actors_reaped=2, helper_reaped_by=R,
helper_exit_observed=true, stdout_eof=true, stderr_eof=true,
original_final=false, state=UNKNOWN, หนึ่ง consumed claim และ no remaining children
capture_allowed/authorizes_actions/dev_observed/goal_verified=false ทุก case
Synthetic database bytes และ parent subreaper setting คงเดิมตาม assertions เดิม
ไม่เปลี่ยน UNKNOWN เป็น FAIL/Done หรือแต่ง replacement FINAL

Source stop/reap/EOF semantics, Fraction 20/3/45 budget, 3 s cleanup reserve,
per-actor 256 MiB cap และ native 1 s alarm ไม่เปลี่ยน
fixture parent wait <=15 s และ phase/loss wait <=1 s เป็น test failure bounds
ไม่ใช่สิทธิ์ขยาย source attempt; ไม่ยืด timeout หรือลด assertion เมื่อ phase ไม่ทัน
ข้อยืนยัน H ยัง alive เป็นข้อกำหนดจริง: ถ้า native alarm ชนะ race test ต้อง fail

Local development run ก่อนอัปเดต manifest เจอ expected hash-length mismatch
14799/14800 หลังลบ newline; แก้ pins แล้ว final suite 44/44 ตามข้างต้น
ไม่ใช่ final pass ของ intermediate run และไม่มี blind rerun เพื่อซ่อน failure
CI ใหม่ต้องตรวจ exact-head logs แยก; CI หรือ local counts ไม่ใช่ source acceptance
historical broad local baseline NOT PASS คงเดิม ไม่ได้ rerun local broad suite

## 4. Disposition และ evidence record

OA06 มี PARTIAL evidence เพิ่มสำหรับทั้งแปด native schedules ที่วัดข้างต้น
ไม่ใช่ exhaustive arbitrary kill timing หรือ full OA06 closure
OA04/05/10 มีเพียง evidence ประกอบ ไม่เปลี่ยน required obligations
OA07 actual R death/external containment และ OA12 joined original-goal/Facts path
ยัง NOT RUN. OA อื่นคง disposition ของ package 3 ตามขอบเขต ไม่อ้างปิดแถวใด
unknown fork-return/pre-witness launch, production issuer/rollback anchor/containment,
aggregate physical resources/external actors, uninterruptible I/O ยังเป็น blockers
no-child oracle ใน owned fixtures ไม่ใช่ universal production no-orphan proof

| Evidence field | Record |
| --- | --- |
| ID/status/scope | B4 OPEN / OA06 PARTIAL; offline native loss schedules เท่านั้น |
| Requirement | OA06 / B4 / OC15 ตาม contract; ไม่เปลี่ยน OC definitions |
| Source SHA/path | Exact candidate commit ใน PR + [updated manifest](../acceptance/handoff/opencode/observer-native-hashes.json) |
| Task/control/stimulus | [8 added controls](../acceptance/handoff/opencode/test_observer_native.py): four phases × O→S/S→O |
| Expected outcome | Lifecycle cleanup เมื่อยืนยัน ownership ได้; missing FINAL => UNKNOWN |
| Actual outcome | Local 44/44 OK รวม eight actual native loss results ตาม §3 |
| Environment/dependency identities | Build facts ใน suite log; pinned C/headers/startup/preflight/owner ใน manifest |
| Private evidence locator | Original evidence/Dev bindings UNBOUND ไม่ได้อ่าน; owned workflow logs ใน PR |
| Privacy-safe summary | phase/order/booleans/finite counts; ไม่มี raw IDs/paths/frame payload |
| Independent review | Parent round-10 operator-supplied APPROVE; candidate PENDING exact-source review |
| Unresolved limits | §4; OA07/OA12 NOT RUN; B1–B7 OPEN |
| Handoff | Keep draft; source review/green CI ไม่ใช่ production action approval |

Delta จำกัดที่ new controls/test hooks, strict workflow 36→44, actual manifest,
one-byte whitespace correction และเอกสารนี้; source runtime/security/public schema
ไม่เปลี่ยน. การ merge implementation/interface ในอนาคตยังต้องผ่าน
[SPEC §14](SPEC.md#14-change-control) ตาม contract
