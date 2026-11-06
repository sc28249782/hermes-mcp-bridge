# Ancestor-E registry feasibility — owned offline counterexample package

## 1. Checkpoint และผลที่เสนอให้รีวิว

Parent `057a0e9c4fd54119c9586a0f39da75703f99fa34` ได้รับ operator-supplied
round-14 APPROVE (DESIGN) ตามข้อความที่ผู้ใช้ส่งมา ไม่ใช่ GitHub review submission
ไม่มี review timestamp จึงไม่เติมเอง. Package ใหม่นี้รอ exact-source review

อ้างอิง [OA07 design](OPENCODE-HANDOFF-OA07-CONTAINMENT-DESIGN-TH.md)
และ [observer/adoption contract](OPENCODE-HANDOFF-OBSERVER-ADOPTION-CONTRACT-TH.md)
รอบนี้เป็น **executable feasibility probe เท่านั้น** ไม่ใช่ production E/containment API
ไม่มีการเลือกหรือติดตั้ง service/cgroup/container/VM/control profile จริง

**ข้อสรุปจำกัด profile ที่ทดสอบ: registry + ancestor subreaper อย่างเดียวไม่ผ่าน
launch-gap requirement จึงเป็น INFEASIBLE/HOLD สำหรับ protocol นี้**
Known-set cleanup ที่สำเร็จไม่แก้ช่องที่ H ถูกสร้างจริงแต่ E ไม่ได้รับ identity
ไม่ใช่ theorem ว่า ancestor-E ทุกแบบทำไม่ได้ และไม่ปฏิเสธ alternative pre-enrollment
family ที่จะต้องเสนอ/review แยก. Production bindings/authority/anchor ยัง UNBOUND

## 2. Source และ topology จริง

เพิ่ม [ancestor_probe.py](../acceptance/handoff/opencode/ancestor_probe.py),
[12 controls](../acceptance/handoff/opencode/test_ancestor_probe.py),
[manifest](../acceptance/handoff/opencode/ancestor-probe-hashes.json),
[new workflow](../.github/workflows/opencode_ancestor_probe.yml) และเอกสารนี้
ไม่มีการแก้ source/test/workflow/manifest/contract เดิม

B = test driver เดิม สร้าง fresh isolated E; E ตั้ง/ตรวจ subreaper ก่อน fork R
R ตั้ง subreaperของตนและสร้าง O/S; S สร้าง H เพียงหนึ่งตัว
R/O/S/H ในแพ็กเกจนี้เป็น **inert Python fixtures**; ไม่เรียก native C/SQLite/CLI,
Facts/Owner/Batch/planner/verifier, backend/config/network/credential หรือ checkpoint
Prefix เป็น fixed synthetic bytes ไม่ใช่ native response หรือ original goal evidence
ไม่มี protected capture G path และไม่เปลี่ยน Reservation.capture() ที่ยัง deny

E/R/O/S/H รวม **5 per-attempt fixture actors**; B เป็น external test driver อีก actor
ไม่ซ่อน B เป็นส่วนฟรีของ approved deployment budget
E และ descendants มี RLIMIT_AS<=256 MiB, core=0; 5 caps ไม่ใช่ aggregate RSS proof
B memory/CPU/FD overhead ยังต้องนับใน deployment feasibility ซึ่งยัง UNBOUND
แต่ละ child สืบทอด absolute attempt timer ผ่าน fixed fork wrapper เดิม

E สร้าง private control/birth/report/stdout/stderr pipes ก่อน R
R รายงาน O/S identities แล้วรอ E; S สร้าง H และส่ง birth frame ให้ R
E เก็บ pidfds ขณะ R/S ยัง alive และ fixed fixture parents ไม่ reap ก่อน handshake
Frame parser เดิมจำกัด512 bytes/strict types; PID เป็น private witness correlation เท่านั้น
E-to-B test-result pipe มี cap4096 bytes เฉพาะ harness ไม่ใช่ candidate/runtime control frame
ไม่มี numeric-PID/PGID signal, host inventory, waitpid(-1) cleanup, pidfd_getfd/SCM_RIGHTS,
exec/subprocess/caller-selected argv/target หรือ respawn ใน probe source

H redirect actual stdout/stderr แล้ว ignore TERM และรอ; prefix mode เขียน synthetic
prefix ก่อนรอ เพื่อวัด bounded discard. ไม่มีการอ้าง production ACK/G ordering จาก mode นี้
S อาจจบจาก R command EOF หลัง R ตาย หรือ E หยุด S; E ยืนยัน exit/reap ของ exact S
ก่อน stop/reap H ที่ adopt จริง. Existing waitid-eligibility/retained-pidfd stop primitives
ถูก pin และใช้เดิม. E ไม่ signal H ก่อน adoption และไม่ reap/signal ซ้ำเมื่อ S reap ไปแล้ว

## 3. Candidate evidence เทียบ diagnostic harness

| Layer | ความสามารถจริง | ใช้สร้าง candidate success ได้หรือไม่ |
| --- | --- | --- |
| Candidate E | เฉพาะ R handle และ O/S/H registry ที่ส่งถึง E ผ่าน protocol | ยืนยัน cleanup ของ known set ใน named schedule เท่านั้น; production_feasible=false เสมอ |
| Test witness | S birth frame สำเนาผ่าน test-only FD201 ซึ่ง candidate source ไม่อ่าน; harness retain H pidfd แยก | ไม่ได้; อยู่นอก candidate registry/capability |
| Diagnostic rescue | หลัง probe คืน infeasible/unconfirmed แล้ว ใช้ extra H pidfd + actual adopted-child proof หยุด/reap/drain | ไม่ได้; record แยก diagnostic.used=true และไม่แก้ frozen candidate outcome |
| No-child oracle | waitpid(-1,WNOHANG) เฉพาะ isolated test E หลัง candidate/diagnostic จบ | เป็น fixture hygiene ไม่ใช่ production containment proof |

Gap mode สร้าง H จริงและ R รับ birth แล้ว **จงใจไม่ส่ง H identity ถึง E**
R ถูก SIGKILL จริงก่อน E cleanup; จึงแทนช่วง successful fork ก่อน E registration
ไม่ได้ฉีด failure ลง kernel fork return เอง และไม่อ้างว่าครอบทุก instruction-level race
Candidate E reap R/O/S ได้ แต่คืน helper_launch_known=false, helper_exit_observed=null,
helper_reaped_by=null, stdout/stderr EOF=false และ cleanup_confirmed=false
Independent harness ยืนยัน H **ยัง alive หลัง candidate คืนผล** และยังไม่ EOF
จากนั้นเท่านั้นจึงใช้ diagnostic witness เก็บกวาด H ภายใน original deadline

Malformed helper registration และ injected pidfd_open failure ให้ผลแยกแบบเดียวกัน
pidfd failure เป็น test fault; ตรวจ candidate open หนึ่งครั้งและไม่มี retry/fallback
Diagnostic handle มีไว้ก่อน fault/loss ใน test scope ไม่ใช่การซ่อม identity ของ candidate
Known cases ก็มี independent witness FD แต่ไม่ใช้ diagnostic stop
Python object privacy/fixture pipe/hash ไม่ใช่ hostile same-uid authentication

Source assessment `INFEASIBLE_TESTED_REGISTRY_PROFILE` และ production_feasible=false
เป็น safety disposition ที่กำหนดจาก profile ขาด pre-enrollment; counterexample
มี actual live-H/EOF evidence รองรับ ไม่ใช่อ้างว่าค่า false อย่างเดียวพิสูจน์ impossibility
attempt_consumed หมายถึง in-memory used guard ของ probe object เท่านั้น
ไม่ใช่ cross-process single-use issuer, persisted claim หรือ B3 rollback proof
helper_launch_known หมายถึง retained H binding สำเร็จ ไม่ใช่ proof ว่าไม่มี H เมื่อ false

## 4. Budget และ actual local controls

B ล็อก T0 ก่อน E fork; E ใช้ exact Budget.start ล็อก Ta **ก่อน R fork**
D_attempt=min(Ta+20,T0+45); probe เลือก stricter D=min(D_attempt,Ta+8)
D_capture=D−3 ไม่เริ่ม deadline ใหม่เมื่อ R ถูก kill หรือ H adopt
E มี outer timer ถึง T0+45; child timers ถึง original D
Known stop O/S แล้ว H ใช้ two phases เดิม; known-path R kill/exit/reap/EOF รวมในเวลาที่วัด
Candidate source failures cleanup ได้เฉพาะ retained eligible identities; unknown actors
ไม่ถูกหาใหม่/ส่ง numeric signal/launch ซ้ำเพื่อทำให้ผลผ่าน

Author-local Python3.12.14, Linux x86_64, umask022:
**12/12 OK, exit0**, ResourceWarning-as-error, ไม่มี skip
9 real E process cases + exact-budget arithmetic + AST source-path audit + source manifest
ทุก case ยืนยัน budget_preserved=true, elapsed<8s และ measured cleanup<3s,
ไม่มี fixture child ค้าง และ B subreaper setting ไม่เปลี่ยน
หลัง B wait/reap exact E จริง ยัง assert T0-to-B completion<8s ซึ่ง stricter กว่า Ta+8
เวลาที่รายงานปัดลงเป็น milliseconds; เป็น measured named-schedule evidence
ไม่ใช่ proof ของ worst-case0.6s metadata/2.4s stop, scheduler pressure หรือ kernel I/O
Diagnostic rescue สามกรณีตรวจ original D เดิม ไม่ได้รับ fresh cleanup budget

| Control / real stimulus | Candidate actual result | Diagnostic ใช้หรือไม่ |
| --- | --- | --- |
| known identities + actual R SIGKILL | Exact E reap H, O/S2, helper streams/report EOF; cleanup_confirmed=true; profileยัง infeasible | ไม่ใช้ |
| fixed prefix + R SIGKILL | Bounded discard/known cleanup; ไม่ได้ goal/native capture proof | ไม่ใช้ |
| S reap H ก่อน R SIGKILL | helper_reaped_by=S; ECHILD ไม่กลายเป็น E reap; signal trap กัน E stop H ซ้ำ | ไม่ใช้ |
| controlled R branch ยังไม่สร้าง O/S | R exact exit/reap, empty streams; ไม่อ้างครอบ unknown fork-return | ไม่ใช้ |
| actual H spawn แต่ registration ถูก withheld | Known O/S cleanup ได้; H alive/unregistered; incomplete EOF; infeasible | ใช้ extra witness หลัง candidate return |
| malformed H registration | ไม่แปลง bad frame เป็น capability; same unconfirmed live H | ใช้หลัง candidate return |
| injected H pidfd_open failure | One attempted acquisition; no fallback/repair; unconfirmed | ใช้หลัง candidate return |
| same probe object run ซ้ำ | ATTEMPT_CONSUMED ก่อน R launch ครั้งสอง; ไม่ replay | ไม่ใช้ |
| H stop ก่อน R/S death | Actual ECHILD + no-signal trap ก่อน R loss; cleanup หลัง adoption เท่านั้น | ไม่ใช้ |

ทุก candidate result มี profile_selected/production_feasible/capture_allowed/
authorizes_actions/dev_observed/goal_verified=false. ไม่มี original FINAL/Done claim
Public result เป็น closed dataclass fields ไม่มี PID/T0/paths/nonce/raw prefix/exception
ก่อน manifest มี local development run failed FileNotFoundError ของ new manifest
เมื่อสร้าง pins แล้ว final suiteผ่านตามด้านบน; ไม่ใช่ final pass ของ intermediate run
CI ต้องอ้าง exact published head/log แยก ไม่ใช้ local counts หรือ old-head green แทน
Historical broad local baseline NOT PASS คงเดิม ไม่ได้ rerun/อ้าง broad local PASS

## 5. EC/OA disposition

[EC01–EC12 ใน design เดิม](OPENCODE-HANDOFF-OA07-CONTAINMENT-DESIGN-TH.md)
เป็น historical preregistration. รายการด้านล่างอธิบาย incremental evidence เท่านั้น
ไม่มี EC whole-row PASS/CLOSED และไม่มี OA07 production profile acceptance

| EC | Incremental disposition | ส่วนที่ยังไม่พิสูจน์ |
| --- | --- | --- |
| EC01 | NOT RUN | Production issuer/profile/boot/delegation/expiry/revoke |
| EC02 | PARTIAL controlled empty-R branch | Actual interrupted fork return/unknown R launch |
| EC03 | PARTIAL counterexample: actual H born, withheld registration, R death | Independent gap coverage ที่ทำให้ production ready; ไม่ได้ implement pre-enrollment |
| EC04 | NOT RUN | Production ARM/G/native query phase กับ accepted external profile |
| EC05 | NOT RUN | Real native read-lock/prefix/FINAL/commit joined path ใน E profile |
| EC06 | PARTIAL known adoption + S-reaped-H + pre-adoption denial | Concurrent reapers/atomic races/unknown wrapper identity |
| EC07 | NOT RUN | E takeover กับ native full pipes/inherited writers |
| EC08 | NOT RUN | E/reaper death/revocation และ accepted availability boundary |
| EC09 | NOT RUN | Foreign membership/escape และ real kernel domain |
| EC10 | PARTIAL object reuse guard only | Cross-process restart/whole-domain rollback/independent anchor |
| EC11 | PARTIAL measured named budget schedules | Late loss, resource pressure, aggregate B/E cost, hard I/O |
| EC12 | PARTIAL independent diagnostic/no-child/privacy record | Deployment independent containment oracle/authority |

**OA07 ยัง NOT RUN ตาม full obligation ที่ต้องมี accepted external profile**
แม้ named inert R-death experiments จะรันจริงแล้ว; ไม่ซ่อน experiments เหล่านี้ว่าไม่ได้รัน
B4 OPEN; OA06/OA08 PARTIAL; OA12 NOT RUN; B1–B7 OPEN

## 6. Evidence record และ handoff

| Field | Record |
| --- | --- |
| ID/status/scope | OA07 NOT RUN full profile / B4 OPEN; owned inert ancestor registry feasibility |
| Requirement | Design EC02/03/06/10/11/12 subset; no OC/OA definition change |
| Source SHA/path | Exact candidate commit + [manifest](../acceptance/handoff/opencode/ancestor-probe-hashes.json) |
| Task/control/stimulus | Nine fixed process cases ตาม §4; no native/backend invocation |
| Expected | Known-set cleanup allowed; missing identity cannot borrow diagnostic authority |
| Actual | Local12/12 OK; real live-H counterexample; tested registry profile infeasible/HOLD |
| Environment/dependencies | Linux x86_64/Python3.12.14 local; CI target3.12/3.14; pinned S/P/design sources |
| Private evidence locator | Original/private bindings UNBOUND; only owned workflow logs |
| Privacy-safe summary | Closed booleans/counts/millisecond durations; no raw IDs/paths/output |
| Independent review | Parent round-14 operator-supplied DESIGN APPROVE; new exact source PENDING |
| Unresolved limits | Pre-enrollment, production authority/anchor/E availability, native integration, aggregate resources |
| Handoff | Do not promote registry-only E to production; review alternate gap coverage before implementation |

ข้อเสนอถัดไปหลัง review: ใช้ counterexample นี้ตัด registry-only profile ออกจาก
production-ready candidates แล้วประเมิน alternate pre-enrollment/reaper contract
หากต้องเพิ่ม scoped membership/bulk-stop/launch semantics ให้ผ่าน SPEC §14 ก่อน merge
ไม่เลือก/ติดตั้ง cgroup/service/VM action จริงจาก source review หรือ green CI
PR117 draft/unmerged; J0 PAUSED (#112 e7142cf7); OC18 NOT RUN
R1 NOT AUTHORIZED / R2 HOLD; no Dev/pilot/model/API/credential/config/checkpoint/release/deploy
