# OpenCode B4 — offline supervision source candidate

วันที่: 3 พฤศจิกายน 2026 (Asia/Bangkok)
Input: แผน B1–B7 ที่ผู้ใช้ยอมรับ ณ
`1dd77c131e8f3bee2fd61b8285ed9a150f4c793f` และคำสั่ง “ทำขั้นถัดไป”
ไม่มี exact approval timestamp ที่ยืนยันได้
สถานะ: **SOURCE CANDIDATE / รอ exact-source review / B4 ยัง OPEN**

## 1. ขอบเขต source ที่เสนอให้รับ

เพิ่ม [supervision.py](../acceptance/handoff/opencode/supervision.py) เป็น primitive
แยกจาก [Facts/Owner เดิม](../acceptance/handoff/opencode/facts.py)
trusted standalone fixture launcher เท่านั้นที่เรียกได้ใน profile นี้
ไม่มี production authority resolver, public parser/CLI/MCP/dispatcher หรือ backend call
ไม่ได้เชื่อม primitive เข้ากับ Facts, Batch, planner หรือ checkpoint store
จึงไม่อ้างว่า recovery/integration ทำงานครบ หรือยก B4 เป็น CLOSED

เพิ่ม [29 controls](../acceptance/handoff/opencode/test_supervision.py),
[manifest](../acceptance/handoff/opencode/supervision-hashes.json) และ
[workflow แยก](../.github/workflows/opencode_supervision_source.yml)
source เดิมที่ผ่านรีวิว, hash manifest เดิม, workflow เดิม, OC definitions,
schema/SPEC/runtime/config/receipt/experiment guards ไม่เปลี่ยน

## 2. Actor และ retained capability protocol

| Actor | หน้าที่และขอบเขต |
| --- | --- |
| Trusted fixture launcher / independent observer | สร้าง disposable owner และ supervisor เป็น direct children ของตน; เปิด owner pidfd ก่อนปล่อยคำสั่ง; ให้ retained read-only root/helper handles, measured expected helper hash, exact synthetic IDs และ monotonic start; retain supervisor pidfd/report reader; ไม่มี credential หรือ Dev binding |
| External owner fixture | ถือ command-pipe write end แต่ไม่ถือ helper pipes/report write end; ส่ง A เพื่อ arm, รอ READY, ส่ง G เพื่อ capture; ต้องถือ lease จนจบ; fixture นี้ไม่ใช่ Facts.Owner และไม่มี authority API |
| Supervisor | อยู่คนละ process กับ owner; เป็นผู้ fork helper โดยตรงเพียงหนึ่งตัว; ถือ helper pidfd และ waitpid/reap เอง; owner pidfd readiness หรือ lease EOF ยกเลิก attempt; ไม่ signal owner หรือ original OpenCode worker |
| Native helper | ใช้ retained ELF fd และ fixed argv `--batch 3 4 5`; fd 3=job DB, 4=context DB, 5=root, 6=helper ELF; ปิด fd อื่นก่อน exec; query/context/job/context bytes ส่งครั้งเดียวแล้ว EOF; ไม่รับ checkpoint-selected path/SQL/argv |

A/G เป็น startup/capture barrier ของ process fixture ไม่ใช่ authority token
คำสั่งซ้ำ, ลำดับผิด หรือข้อมูลอื่น reject โดยไม่มี retry/respawn
owner death ที่เกิดพร้อม helper output มี precedence เหนือ capture completion
pidfd ของ owner มีไว้ observe เท่านั้น; signal ทั้ง TERM/KILL ใช้ helper pidfd เท่านั้น
ไม่มี numeric-PID/PGID signal fallback
กรณี helper pidfd เปิดไม่สำเร็จ ปิด stdin และลองยืนยัน direct-child reap/EOF
ภายใน budget; หากยืนยันไม่ได้ให้ STOP_UNCONFIRMED ไม่ signal ด้วย PID

source ใช้ Linux fork/execve-by-fd, procfs pidfd descriptor validation และ select
hash/mode/ELF checks เป็น binding checks จาก trusted fixture launcher
ไม่พิสูจน์ compiler/library/host authenticity หรือ hostile same-uid/same-process isolation
เพิ่ม actor supervisor หนึ่งตัวใน profile นี้อย่างเปิดเผย ไม่ใช่ capability ที่ซ่อนใน Batch เดิม

## 3. Budget และ stop semantics

| Resource | Enforcement / ข้อจำกัด |
| --- | --- |
| Shared outer deadline | supervisor ใช้ inherited monotonic start +45 s; ไม่รับ future/stale start; SIGALRM และ select ใช้ deadline เดียว; ไม่เริ่ม clock ใหม่หลัง handoff |
| Attempt/helper lifetime | ค่าไม่เกิน 20 s นับตั้งแต่ supervisor entry รวม admission/arm/idle/capture; ใช้ค่าที่สั้นลงใน controls เท่านั้น; reserve cleanup ก่อน outer deadline 2 s |
| Cleanup | TERM grace <=0.2 s แล้ว KILL wait <=1 s; stop routine cap <=1.5 s และไม่เกิน outer deadline; unconfirmed ไม่ได้ budget ใหม่ |
| Native transaction | ใช้ C helper เดิมที่มี alarm 1 s ครอบ open/lock/query/close; source ไม่แก้ timer หรือ VFS |
| Memory | supervisor และ helper จำกัด RLIMIT_AS คนละ 256 MiB; เป็นสอง address-space caps ไม่ใช่ aggregate cap 256 MiB; trusted test observer/owner อยู่นอก caps สองตัวนี้ |
| Captured stream | stdout สะสม <=64 KiB; stderr <=4 KiB และข้อมูล stderr ใดก็ reject; stop drain discard เป็น bounded reads จน EOF/deadline; ไม่ส่ง raw captured bytes ออก report |
| Report | READY/CAPTURE/FINAL เป็น allowlisted JSON; แต่ละ write <=512 bytes แบบ nonblocking atomic pipe write; full/closed report channel ไม่ยืด stop deadline |

Supervisor ไม่เป็น parent ของ external owner และไม่หยุด owner
owner deadline/cessation ต้อง enforce โดย owner implementation/launcher ที่รับแยก
primitive นี้ไม่ใช่หลักฐานว่า Facts.Owner integration ทั้งชุดอยู่ใน 45 s แล้ว
uninterruptible kernel I/O, fork/exec stalls และ supervisor SIGKILL หลังสร้าง helper
ยังไม่สามารถรับรอง complete stop/reap ได้จาก profile นี้
ไม่มีการขยาย timer เพื่อปิดข้อจำกัดนั้น

FINAL แยก `helper_reaped`, `pipes_eof`, `helper_stopped` และ `owner_lost`
post-fork setup failure ต้องรักษา child identity เพื่อ cleanup
หาก fork return ถูก interrupt จนไม่รู้ว่าเกิด child หรือไม่ ให้
`helper_started=null`, `helper_stopped=false`, STOP_UNCONFIRMED ไม่อ้าง no helper
ไม่รวม helper exit กับ pipe completion เป็นข้ออ้างเดียวที่ตรวจไม่ได้
`CAPTURE_COMPLETE` ต้องมีสาม frames ที่ framing/type/role ถูกต้อง, exit zero,
reap และ stdout/stderr EOF พร้อม owner ที่ยังไม่ถูก observe ว่าตาย
เป็น capture/stop result เท่านั้น ไม่เทียบ job goal/context association/current authority
`goal_verified=false`, `authorizes_actions=false`, `dev_observed=false` เสมอ
ไม่มี ADVISORY_DONE ใน primitive นี้

owner ตาย => OWNER_LOST; helper reap/EOF ไม่ครบ => STOP_UNCONFIRMED
ไม่มี final report, report framing ไม่ครบ หรือ supervisor exit ไม่ยืนยัน => observer UNKNOWN
final report เป็น assertion จาก trusted source ไม่ใช่ independent production attestation
observer ต้องตรวจ exact final framing/EOF/supervisor exit และ source binding ก่อนรับหลักฐาน
ไม่มี production observer/verifier implementation ใน source package นี้

## 4. Controls และหลักฐานจริง

| Case family | Stimulus และสิ่งที่พิสูจน์ |
| --- | --- |
| Native positive | compile C helper เดิมด้วย existing compiler/library; actual native-schema SQLite context/job/context สาม frames; source files bytes คงเดิม; ไม่อ้าง goal success |
| Owner death | SIGKILL ก่อน arm, หลัง READY/ก่อน G, ระหว่าง owned hung fixture, หลัง actual partial success prefix, ระหว่าง fixture ไม่อ่าน stdin และช่วง startup handoff; independent harness reap supervisor หลังอ่าน final |
| Owned targeting | helper fixture ignore TERM ต้องจบด้วย bounded retained-pidfd stop; owner และอีก attempt ยังมีชีวิต; ไม่ใช้ original worker/PID หรือ process-group cleanup |
| Deadline/lease | shortened deadlines, idle no-arm timeout, owner ยังมีชีวิตแต่ lease EOF, invalid/widened/stale deadline reject |
| Stop unconfirmed | test-only spawn instrumentation retain real stdout write end; native helper reap แล้ว แต่ pipe EOF ไม่มี => STOP_UNCONFIRMED, helper_reaped=true, pipes_eof=false, ไม่มี frames ที่ยอมรับ; ไม่มี orphan/descendant process |
| Framing/privacy | over-cap stdout, stderr sentinel, malformed output, nonzero exit, wrong/duplicate commands, helper hash mismatch; public report ไม่คืน raw stderr/output |
| Lost observer/supervisor | report reader ปิดแล้ว supervisor cleanup และ exit failure; supervisor SIGKILL ก่อน arm ให้ missing report/UNKNOWN; ไม่อ้างว่า control นี้พิสูจน์ supervisor death หลัง spawn |
| Identity | new source/workflow และ unchanged dependencies ต้องตรง manifest จริง; controls ไม่ skip หาก platform/native SQLite ใช้ไม่ได้ |
| Startup failure | actual post-fork fd setup failure ยังรักษา child ownership; uncertain fork return ใช้ injected boundary ที่ไม่สร้าง orphan และต้องไม่อ้าง no helper |

Author-local Python 3.12.14, native SQLite 3.45.1:
**29 controls OK**, ResourceWarning-as-error, ไม่มี skips
source controls เดิม **48/48 OK** จาก unchanged source manifest
ผล CI ของ candidate ต้องบันทึกตาม exact commit/job logs ใน PR แยกจาก local
ไม่ได้รัน broad baseline ใหม่ locally และไม่เปลี่ยนประวัติ local baseline NOT PASS

Development iterations 20/25/26 เป็น snapshots ของ suite เดียว ไม่ใช่เพิ่ม trial count
การลอง control แบบ local AF_UNIX descriptor transfer ถูก runtime ปฏิเสธด้วย EPERM
จึงถอด socket design นั้นออก แล้วใช้ real pipe-end retention ใน test-only instrumentation
assertion เดิมว่า reap แต่ไม่มี EOF ต้อง STOP_UNCONFIRMED ยังคงอยู่และผ่าน
final source/workflow ไม่สร้าง socket หรือใช้ network
fixtures สร้าง/หยุดเฉพาะ process และ files ใหม่ของตน; ไม่มี Dev/VM/SSH/CIM/model/API/key action

## 5. ข้อที่ยัง OPEN และ disposition ที่ขอรีวิว

ขอ exact-source acceptance เฉพาะ **independent live supervisor หยุด/reap direct helper
หลัง external disposable owner ตาย** ใน Linux POSIX fixture profile ที่ระบุ
ไม่ขอ whole B4 closure หรือ action approval
ข้อจำกัดที่ยังเปิด:

1. เชื่อม protocol กับ Facts.Owner/Batch admission, full verifier และ receipt commit
   ต้องมี source และ joined controls ใหม่; primitive นี้ยังไม่ได้ถูกเรียกจากเส้นทางนั้น
2. production trusted launcher/observer/source authentication, private binding,
   one-attempt cross-process authority และ retention/admission ยังไม่มี
3. supervisor เองตายหลัง helper spawn, independent observer ตาย และ kernel I/O
   ที่ไม่ตอบสนองต่อ signal ยังเป็น feasibility/STOP_UNCONFIRMED boundary
4. aggregate memory/actor budget และ actual deployment feasibility ยังต้องรับแยก
   ไม่ใช้การเพิ่ม supervisor เป็นข้ออ้างขยาย 1/20/45 s เดิม
5. actual SQLite lock/device/output race schedules ไม่ exhaustive; existing VFS 48
   controls และ B4 native positive ไม่ใช่ proof ของทุก owner-death-at-lock interleaving

โยง [B4/OC15–16 และ B6](OPENCODE-HANDOFF-BLOCKER-CLOSURE-TH.md)
โดยไม่เปลี่ยนสถานะ B1–B7 หรือ [OC definitions](OPENCODE-HANDOFF-CONTROLS-TH.md)
ขั้นถัดไปคือ independent exact-source review และ disposition ของข้อจำกัด
ไม่เริ่ม integration/Dev จาก green CI โดยอัตโนมัติ
J0 PAUSED; #112 ไม่เปลี่ยน; R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN
PR #117 คง draft/unmerged; ไม่มี archive invocation/arm trial/release/deployment ใหม่
