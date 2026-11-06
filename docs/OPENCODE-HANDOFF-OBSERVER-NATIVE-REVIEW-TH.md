# Observer package 3 — owned offline native integration candidate

## 1. Checkpoint และขอบเขต

Parent `8b41102ce9ed9a87a6df208ad6970f3381f90c6e` ได้รับ operator-supplied
round-9 APPROVE สำหรับ inert startup + exact-budget fix ตามข้อความที่ผู้ใช้ส่งมา
ไม่ใช่การ submit GitHub review และไม่มี timestamp ของ review จึงไม่เติมเวลาเอง
แพ็กเกจนี้เป็น source candidate ใหม่ที่รอ independent exact-source review

PR #117 คง draft/unmerged; B1–B7 OPEN; J0 PAUSED; R1 NOT AUTHORIZED / R2 HOLD;
OC18 NOT RUN. #112 ยังคง draft ที่ `e7142cf71792475af9375140df39acd55944d8d1`.
ไม่มี Dev/pilot, backend job, credential/config/model/network invocation,
checkpoint/receipt append, archive/arm trial, release หรือ deployment

เพิ่มห้าไฟล์เท่านั้น: native runner, controls, source manifest, workflow และเอกสารนี้
ไม่มีการแก้ source/test/workflow เดิม รวมทั้ง Fraction budget และ assertions เดิม
C helper/VFS และ headers ใช้ bytes เดิมจาก candidate ที่ผ่าน review
[contract](OPENCODE-HANDOFF-OBSERVER-ADOPTION-CONTRACT-TH.md) ยังมีผลตามขอบเขตเดิม

## 2. เส้นทางที่เพิ่ม

`NativeRun` ใช้ fresh trusted fixture R และ process-local FixtureIssuer เท่านั้น
R reserve single-use claim ก่อนอ่าน helper/database handles หรือสร้าง O/S/H
FixtureBundle มาจาก trusted test bootstrap: retained root/helper/job/context FDs,
measured helper hash และ expected-frame digest ที่ล็อกก่อน observation
ข้อมูลนี้ไม่ใช่ production issuer, authenticated launch, original binary provenance,
external rollback anchor หรือ external containment

R ตั้งและตรวจ subreaper; O/S เป็นลูก R; H เป็นลูก S
O ยังเป็น fixed byte relay ไม่ใช่ Facts.Owner และ S ในแพ็กเกจนี้เป็น native-specific
supervisor; `supervision.py` และ inert `Startup.run()` เดิมไม่เปลี่ยน
แชร์เฉพาะ private PIDFD/ACK/current/pipe/stop primitives ที่ pin ใน manifest
ส่วน run/cleanup แยกให้เห็นครบ จึงไม่ต้องเปลี่ยน executable profile เดิม

H เริ่มเป็น Python gate wrapper ที่ยังไม่อ่าน SQLite แล้วจึง exec ผ่าน retained
helper FD หลังรับ G เท่านั้น: `os.execve(bundle.helperfd, fixed --batch argv, fixed env)`
ยังเป็น PID เดิม ไม่มี actor ที่ห้า ไม่มี executable pathname lookup หรือ shell
stdin/stdout/stderr เป็น actual H standard streams; retain เฉพาะ directory และ
readonly DB handles ที่ C ต้องใช้ ไม่มี arbitrary target/path/SQL/argv จาก caller
ตัว wrapper ตรวจ bundle ซ้ำก่อน exec; R ตรวจซ้ำหลัง original FINAL

S ส่ง witness ขณะ H เป็น direct unreaped child; R ตรวจ nonce/generation/source,
parent/child correlation และ O/S liveness ก่อน/หลัง retain H pidfd
R ACK → S ACKED → R ส่ง NATIVE_FIXTURE_G ผ่าน O → S ส่ง G ไป H
G หมายถึงการอ่าน synthetic fixture ใน profile นี้เท่านั้น
`Reservation.capture()` เดิมยัง deny `PIDFD_ACK_UNBOUND` ทุกครั้ง

S ขอ `context(ctx_fixture) → jobs(oct_fixture) → context(ctx_fixture)` จาก C
helper ตัวเดียว อ่าน length-prefix แบบ bounded partial-read reassembly
ตรวจ role/field types ด้วย decoder เดิมแล้วเทียบทั้งสาม tuple กับ independent
fixture expectation ซึ่งมี digest ผูกกับ Binding.dossier_sha256 ก่อนเริ่ม
ชื่อ target และ tuple ทั้งหมดเป็น synthetic constants ใน controls
ไม่ใช่ canonical production mapping, original goal verifier หรือ model summary

S ส่ง typed FINAL เฉพาะเมื่อเฟรมครบและตรง oracle, native exit=0, exact reap,
stdout EOF ไม่มี trailing byte และ stderr EOF ไม่มีข้อมูล
R ตรวจ FINAL/current binding/bundle/deadline แล้ว reap O/S และตรวจ report EOF
UNKNOWN เมื่อ FINAL หาย/ผิด แม้ helper exit/reap/EOF จะยืนยันแล้ว
S ตาย: R ต้อง reap S และพิสูจน์ adopted direct child ก่อน retained-pidfd stop H
ไม่มี numeric-PID/PGID signal, `/proc` process scan หรือ old Owner._stop fallback
C VFS เดิมมี exact `/proc/self/fd/<retained DB fd>` alias ภายในอยู่แล้ว
จึงไม่อ้างว่า native C ไม่มีข้อความ `/proc` หรือไม่ใช้ dynamic libraries

## 3. ผลลัพธ์และขีดจำกัด

ผล positive คือ `OFFLINE_NATIVE_FIXTURE_CONFIRMED / NATIVE_FIXTURE_ONLY`
หมายถึงการอ่าน synthetic SQLite fixture สำเร็จภายใต้ lifecycle protocol นี้
ไม่ใช่ original observation Done, production capture acceptance หรือ action approval
`capture_allowed`, `authorizes_actions`, `dev_observed`, `goal_verified` ยังคง false
`native_fixture=true` เป็นชื่อ profile แม้ HOLD ก่อน exec; ไม่ใช่ proof ว่า exec เกิดขึ้น
`fixture_g_sent` คือ R เขียนไป O; actual native execution/response ต้องมีหลักฐานเพิ่ม
`original_final` คือ FINAL จาก S ของ fixture attempt นี้ ไม่ใช่ FINAL จาก original job
`actors_reaped` นับ O/S เท่านั้น; H มี helper_reaped_by แยก
S reap H แต่ FINAL หาย => helper_reaped_by=null ไม่แต่ง observer-reap evidence

Claim ไม่ย้อนใช้หลัง failure, object reuse หรือ duplicate reservation
Hash เช็คไฟล์/retained binary เป็น fixture identity measurement ไม่ใช่ loaded-code
หรือ hostile same-uid authentication; ไม่มี file seal/production launch provenance claim
C source ไม่มี flag test-only ใน positive production-helper build

Budget ใช้ Fraction endpoints เดิม: T0+45, attempt <=20 และ cutoff <=attempt−3
controls เลือก attempt 8 s และ shortened 3.5 s สำหรับ stalled/hung case
ไม่มี timer เริ่มใหม่เมื่อ ACK/adopt; cooperative 0.2 s และสอง stop phases รวม
<=2.4 s อยู่ใน reserve 3 s เดิม; remaining conversions ปัดเข้า deadline
C alarm 1 s ครอบ open/lock/query/close ต่อ capture ตาม source เดิม
C batch ระหว่างรอ request/output ไม่ได้มี full-attempt native alarm เพิ่มใหม่:
R/S absolute deadlines และ retained-pidfd cleanup ยังเป็นผู้คุม attempt
Late publication หลัง actual FINAL/reap/EOF เปลี่ยนเป็น UNKNOWN/BUDGET_EXHAUSTED

ขีดจำกัดที่ call sites: helper file <=4 MiB, DB แต่ละไฟล์ <=64 MiB,
stdout รวม length headers+สามเฟรม <=64 KiB, frame allocation <=65532 bytes
read แต่ละครั้ง <=4096 bytes; stderr read <=4096 และ nonempty ใด ๆ reject
control/witness/FINAL <=512 bytes; cleanup drain/reap ใช้ primitive เดิม
RLIMIT_AS 256 MiB ต่อ actor ×4 ไม่ใช่ aggregate RSS guarantee

## 4. Controls และหลักฐานที่วัด

Author-local Python 3.12.14: native **36/36 OK**, startup **22/22 OK**,
preflight **24/24 OK**, ResourceWarning-as-error, ไม่มี skip
native suite มี 34 isolated R process cases + manifest + source-path audit
ทุก process case ตรวจ ECHILD/no remaining fixture children และ parent subreaper
setting เดิม; เปรียบเทียบ bytes ของ synthetic state files ก่อน/หลังทุก case
public result ตรวจว่าไม่มี fixture nonce/ref/path/prompt/workspace/fingerprint

| กลุ่ม | Expected | Actual local evidence |
| --- | --- | --- |
| Native positive / fragmented reads / reuse guard | ACK-before-G; สาม native frames; S reap + EOF + FINAL; ไม่ซ้ำ attempt | ทั้งสาม positive fixture outcomes ตรง expected; reuse ครั้งสอง deny |
| Unbound / Dev / source/helper/oracle binding mismatch | ก่อน G; unbound/Dev ไม่มี claim/actor; mismatch หลัง claim ไม่คืน attempt | HOLD หรือ UNKNOWN ตามขอบเขต; ไม่มี FINAL |
| Wrong witness / revoke / S loss ก่อน retain/ACK / owner loss / pidfd failure / stalled ACK | ไม่มี G; ไม่ fallback/retry; adopted cleanup เฉพาะเมื่อพิสูจน์ได้ | ไม่มี positive; pidfd failure เป็น STOP_UNCONFIRMED |
| Actual native empty WAL / EXCLUSIVE writer lock / missing job / extra schema | Native C หรือ strict frame path reject | UNKNOWN; ไม่มี FINAL; fixture bytes คงเดิม |
| Wrong status / changed context | Expected tuple digest จากก่อน observation ไม่ตรง | UNKNOWN; ไม่มี FINAL |
| Partial prefix / oversized header / stderr / ill-typed FINAL | Bounded read/parse reject | UNKNOWN; ไม่มี FINAL |
| Full native frames + exit 2 / trailing stdout / late stderr / post-prefix hang | Success prefix ไม่พอ; ต้อง exit=0 + exact EOF | UNKNOWN; ไม่มี FINAL |
| S ตายหลัง G: Python hung fault และ actual native C post-frame fault | Adopt/reap/EOF แยกจาก observation | ทั้งคู่ R reap H ผ่าน retained pidfd; ไม่มี FINAL; UNKNOWN |
| S reap แล้ว drop FINAL | ไม่แต่ง reaper identity หรือ replacement FINAL | exit/EOF true, helper_reaped_by=null, UNKNOWN |
| Retained-FD exec failure / late publication | Consume ไม่มี retry; late completion ไม่สร้าง success | UNKNOWN แม้ late case มี actual FINAL/reap/EOF |

Normal/fragmented/reuse ใช้ unchanged C production-helper source build
negative native post-prefix executables เป็น **test-only C wrappers** ของ source เดิม:
เปลี่ยน exit/trailing/stderr/hang หลัง accepted_main จบ; native S-loss wrapper ใช้
pidfd ของ direct parent เพื่อสร้าง actual S death หลัง actual native frames
ไม่ใช่ production launcher หรือสิทธิ์ signal บนโฮสต์จริง
บาง controls ใช้ Python test-only frame/crash/read/clock/exec fault hooks
actual fork/exec/pidfd/death/adoption/reap/EOF ไม่ถูก mock เป็นผลสำเร็จ
`waitpid(-1,WNOHANG)` มีเฉพาะ no-child oracle ใน isolated test R ไม่ใช่ source cleanup

ก่อน source freeze มี local development failures (missing import/manifest,
fragment hook แตะ witness, shim build warning) ซึ่งแก้ใน new files ก่อน final run
ไม่ใช่ final acceptance/trial และไม่มีการลด assertion/count/timeout ให้ผ่าน
historical broad local baseline **NOT PASS** คงเดิม ไม่ได้ rerun หรืออ้าง local broad PASS
CI ที่เกิดหลัง publish ต้องอ้าง exact head/log แยก; local counts ไม่ใช่ CI

## 5. OA disposition และ blockers

| Obligation | สถานะในแพ็กเกจนี้ | สิ่งที่ยังขาด |
| --- | --- | --- |
| OA01 | PARTIAL fixture admission | production issuer/anchor/containment |
| OA02 | PARTIAL native witness/pidfd/ACK-before-G และ duplicate claim/object guards | production authenticated launcher/trace และ noninventory-side-effect proof |
| OA03 | PARTIAL S loss ก่อน retain/ACK | actual post-fork/pre-witness unknown-launch gap และ exhaustive races |
| OA04 | PARTIAL adopted native cleanup; pre-adoption deny มีใน parent startup controls | concurrent reaper/foreign child/wrong-generation production schedules |
| OA05 | PARTIAL S-reaped H ไม่มี FINAL; stdout/stderr/report EOF แยก | exhaustive descriptor inheritance และ independent deployment observer |
| OA06 | PARTIAL S-only native/Python hung loss; O/S simultaneous inert loss อยู่ใน parent controls | simultaneous O/S loss ระหว่าง actual native capture ยัง NOT RUN |
| OA07 | NOT RUN actual R death; มีเพียง fixture UNBOUND denial | accepted external containment ก่อน actual production ARM/G |
| OA08 | PARTIAL partial/trailing/stderr/ill-typed FINAL และ bounded discard | inherited write end/full pipe ใน native profile ยังไม่ครอบ |
| OA09 | PARTIAL consumed claim/object guard; concurrent fixture controls อยู่ใน parent preflight | restarted production issuer และ whole-store rollback anchor |
| OA10 | PARTIAL exact budget/cutoff/stop phases และ per-actor caps | aggregate resources/external actors/hard kernel I/O |
| OA11 | PARTIAL synthetic bytes/privacy-safe lifecycle record | approved private retention/output/partial-evidence failure path |
| OA12 | NOT RUN | original authority/context/evidence/full goal/Facts/planner/receipt join |

ทุก OA เป็น partial หรือ NOT RUN ไม่มี whole-row PASS/CLOSED
B4 ยัง OPEN รวมถึง real R death + external containment UNBOUND,
unknown actual post-fork/pre-witness launch, uncertain fork/pidfd acquisition,
uninterruptible kernel I/O และ aggregate/external-actor deployment budget
no-children ของ tested schedules ไม่ใช่ universal no-orphan guarantee
B1/B2/B3/B5/B6/B7 ไม่ถูกปิดด้วย fixture native success

## 6. Evidence record สำหรับ B4 increment นี้

| Field | Record |
| --- | --- |
| ID/status/scope | B4 OPEN; owned offline native integration candidate เท่านั้น |
| Requirement | Observer/adoption contract + B4 closure plan; ไม่เปลี่ยน OC definitions |
| Source SHA/path | Exact candidate commit ใน PR; [manifest](../acceptance/handoff/opencode/observer-native-hashes.json) ตรึง runner/controls/workflow/dependencies |
| Task/control/stimulus | [36 controls](../acceptance/handoff/opencode/test_observer_native.py) + ตารางด้านบน |
| Expected outcome | Positive เฉพาะ strict native fixture; failure/loss => UNKNOWN/HOLD |
| Actual outcome | Local 36/22/24 OK ตาม §4; exact-head CI แยกใน PR body |
| Environment/dependency identities | Linux x86_64, native SQLite 3.45.1; compiler/library/helper build commitments ใน suite log; source hashes ใน manifest |
| Private evidence locator | Original private evidence/Dev bindings UNBOUND ไม่ได้อ่าน; owned CI logs จาก workflow ใน PR เท่านั้น |
| Privacy-safe summary | Redacted lifecycle flags/counts; ไม่มี raw native frames/IDs/paths/prompt |
| Independent review | Parent round-9 operator-supplied APPROVE; candidate นี้ PENDING review |
| Unresolved limits | §3/§5; no production resolver/containment/full goal/Facts/planner |
| Disposition/handoff | Keep draft; exact-source review ก่อนอ้าง acceptance; B1–B7 OPEN |

Runtime/security interface ใดที่จะ merge ต้องผ่าน [SPEC §14](SPEC.md#14-change-control)
ก่อน implementation merge; private fixture states ในรอบนี้ไม่เปลี่ยน public schema
Source review/green CI ไม่ใช่ action approval. งานถัดไปต้องแก้ residual ownership /
containment / joined verifier ตาม contract โดยไม่ถือว่า fixture tag เป็น production binding
