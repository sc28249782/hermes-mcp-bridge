# OA07 — external containment และ feasibility contract candidate

วันที่: 4 พฤศจิกายน 2026 (Asia/Bangkok)
Input: PR #117 `be0a012962fac6432e132fabd635ad1b0b2f2640`
สถานะ: **DESIGN ONLY / NOT IMPLEMENTED / PROFILE UNBOUND / OA07 NOT RUN**

## 1. Checkpoint และขอบเขต

ผู้ใช้ส่ง round-13 APPROVE ณ input head สำหรับ interpreter-scope note
เป็น operator-supplied review ไม่ใช่ GitHub submission; ไม่มี review timestamp จึงไม่เติมเอง
รอบนี้จัดทำ requirement/feasibility package ของ external containment สำหรับ R loss
ไม่เลือก/สร้าง/ติดตั้ง service, cgroup, container, daemon, VM control หรือ authority issuer
ไม่เปิด Dev/private bindings และไม่เริ่ม implementation/controls ใหม่

ฐาน requirement คือ [observer/adoption contract §7–9](OPENCODE-HANDOFF-OBSERVER-ADOPTION-CONTRACT-TH.md),
[B1–B7](OPENCODE-HANDOFF-BLOCKER-CLOSURE-TH.md) และ
[native pipe/source scope](OPENCODE-HANDOFF-NATIVE-PIPE-REVIEW-TH.md)
เอกสาร/source/OC definitions เดิมคง bytes เดิม; design นี้ไม่ amend runtime spec โดยอัตโนมัติ

Source ที่ผ่าน review ใช้ fixture R เป็น parent/subreaper ของ O/S และ S เป็น parent H
ถ้า R ตาย ผู้ยืนยัน stop/reap/EOF เดิมหายไปด้วย; existing 53/22/24/48/29/9 controls
ไม่ใช่ OA07 positive evidence และไม่ใช่ production external containment
OA06/OA08 partial evidence ไม่ทำให้ external profile พร้อมใช้งาน

## 2. สิ่งที่ external profile ต้องพิสูจน์

ใช้ชื่อ **E** เป็น logical external cleanup role ไม่ใช่ process/API ที่มีอยู่แล้ว
E ต้องอยู่นอก failure domain ของ R สำหรับ named fault ที่รับจริง
ถ้า E ใช้ controller กับ reaper คนละตัว ต้องประกาศทั้งคู่และนับ actor/resources ทั้งคู่
คำว่า external/host-managed ไม่ให้สิทธิ์ host-wide process control โดยปริยาย
ถ้า E เป็น process ใหม่ launcher/B ต้องรับผิดชอบ retained identity และ exact wait/reap
ของ E เองใน budget ที่ประกาศ; E ไม่ reap ตนเอง และห้ามซ่อน B/E2 watchdog เพิ่ม
ถ้าไม่มี accepted lifecycle owner ของ E ให้คง profile UNBOUND

| Responsibility | Requirement ก่อน actual production ARM/G | สิ่งที่ไม่ใช่หลักฐานแทน |
| --- | --- | --- |
| Launch containment | Attempt-scoped ownership domain ถูก bind ก่อน R/descendants เริ่ม และครอบ launch ที่ fork สำเร็จแต่ witness ยังไม่ถึง | Register PID หลัง fork, current directory name หรือ checksum อย่างเดียว |
| Identity | Retained instance/source/generation handles ของ exact actor inventory; unknown launch มี explicit disposition | PID/PGID เดี่ยว, host scan, recent-job search, reconstructed backend PID |
| R-loss detection | มี independent retained R identity และ event/liveness semantics ที่วัดได้; exit status กับ normal completion แยกกัน | R heartbeat/lease/exit0 ที่อธิบายตนเอง |
| Stop ownership | Finite terminal-cleanup grant ตั้งแต่ admission; capture revocation ไม่ให้ capture ต่อ แต่ cleanup เฉพาะ owned actors ยังใช้ได้ถึง deadline เดิม | ถือ handle แล้วถือว่ามี permission, implicit root/service authority |
| Reaper | ระบุ exact parent/adoption owner และ arbitration ก่อนทุก reap; ECHILD ไม่แปลว่า reap สำเร็จ | pidfd readable, unit empty, EOF หรือ kill command สำเร็จ |
| Streams | Independent stdout/stderr/report EOF พร้อม bounded drain และ FD inventory ของทุก actor รวม E | helper exit/reap หรือ valid FINAL อย่างเดียว |
| Budget | ล็อก T0/Ta/deadlines และนับ controller/reaper/resource costs ตั้งแต่ bootstrap | เริ่ม 20/45 s ใหม่เมื่อ E รับช่วง หรือมี hidden watchdog |
| Publication | E ส่งได้เพียง cleanup evidence; active attempt ที่ R loss คง UNKNOWN | Reconstruct FINAL, verified goal หรือ planner Done จาก cleanup |

Unknown/missing/stale binding ช่องใด => PRE_ARM_HOLD ไม่มี actual production ARM/G
fixture-owned-cleanup tag จาก source ปัจจุบันไม่ใช่ external-profile binding
production issuer/independent rollback anchor ของ B1/B3 ยัง UNBOUND

## 3. เส้นทาง admission และ irreducible launch gap

ชื่อในตารางเป็น proposed private design labels ไม่ใช่ implemented states/tool schema

| Stage | Required binding / action | Failure disposition |
| --- | --- | --- |
| PREPARE | B ล็อก T0, finite scope, E source/controller/reaper/profile instance และ resource envelope | Missing profile => HOLD ก่อน R launch |
| DOMAIN_READY | Prove exact containment/ownership domain และ cleanup grant ก่อนมี R; no inherited unrelated actor/FD | Domain identity/membership guarantee ไม่ชัด => HOLD |
| ATTEMPT_CONSUMED | Consume one attempt ใน accepted independent rollback domain; ล็อก Ta ก่อน R launch ใน proposed profile นี้ | Unknown launch/partial claim คง consumed; ห้าม retry/delete marker |
| R_LAUNCHED | Retain R identity และ prove launch membership โดยไม่มี escape interval | Unknown R fork return ไม่กลายเป็น no process; cleanup-only/unconfirmed |
| OWNED_EXPANSION | O/S/H เกิดครั้งเดียวใน covered domain; exchange retained identity/parent/source/generation acknowledgements | R ตายก่อน registration ต้องยังมี independent containment/reaper proof หรือ profile infeasible |
| CAPTURE_ELIGIBLE | B1/B3/current context/source/goal scope + accepted E profile ครบ; R/S/owner handshake เดิมยังต้องผ่าน | E-ready ไม่ใช่ capture authority; missing field ไม่ส่ง G |
| R_LOST | Unexpected R exit/loss ก่อน valid completion commit; E takeover ตาม bounded terminal grant | Observation UNKNOWN; ไม่อ่าน DB/evidence หรือเริ่ม verifier ต่อ |
| TERMINAL | Stop/exit/reap/EOF facts ครบตาม exact inventory หรือประกาศ unconfirmed ณ deadline | ห้ามสรุป all-stopped จาก partial facts หรือเติม FINAL |

การล็อก Ta ก่อน R launch เป็น **stricter proposed allocation** ภายใน maximum20/45 s เดิม
ไม่อ้างว่า fixture source ที่ reserve ใน R implement allocation นี้แล้ว
B/E setup อยู่ใน T0+45 ตั้งแต่แรก ไม่มี free preflight/process startup time

**Known-pidfd registry อย่างเดียวไม่ปิด gap:** R อาจ fork O/S หรือ S fork H สำเร็จ
แล้ว R/S ตายก่อนส่ง identity ให้ E. Missing handle ไม่ใช่ no child
profile ต้องพิสูจน์ coverage ที่เป็นอิสระจาก R ตลอดช่วงนั้น และ exact reaping/stream closure
หากทำไม่ได้ภายใต้ no-host-scan/no-numeric-signal/no-respawn ให้คง production infeasible/HOLD
ไม่ผ่อนข้อกำหนดด้วย test cleanup ที่เปิด capability เกิน profile

ถ้า candidate ต้องใช้ unit-scoped membership enumeration, bulk-stop หรือ launch API ใหม่
ต้องเสนอ boundary/authority/source/control amendment ให้ review ผ่าน SPEC §14 ก่อน merge
เอกสารนี้ไม่เปิดข้อยกเว้นให้ existing closed call graph หรือ no-scan policy

## 4. Candidate families — ยังไม่เลือก actual implementation

| Family | สิ่งที่อาจนำมาพิสูจน์ได้ | ช่องที่ต้องแก้ก่อนรับ profile | Current disposition |
| --- | --- | --- | --- |
| Existing fixture R / parent-death signal / lease only | Named idle/loss behavior ใน controls เดิม | ผู้ยืนยันหายไปพร้อม R; no independent reaper/coverage | ไม่เพียงพอสำหรับ OA07 |
| Fresh E เป็น ancestor subreaper + retained identities | Known-child R exit/adoption และ exact pidfd stop | ต้องแก้ pre-registration launch gap, reaper arbitration และ actor budget | DESIGN CANDIDATE / UNBOUND |
| Attempt-scoped kernel containment + separately bound E/reaper | ศึกษา coverage ของ descendants และ no-live membership condition | ต้องพิสูจน์ pre-enrollment/no migration/instance identity; kill ไม่ใช่ reap/EOF; bulk-stop อาจขัด S/R ownership protocol เดิม | DESIGN CANDIDATE / UNBOUND |
| Existing host manager + dedicated owned reaper | ศึกษา independent lifecycle/retention capability | ระบุ service permission, exact kill set, reaper source, persistence/restart และ actors จริง; ไม่ใช้ label ว่ามี service อยู่แล้วแทน proof | DESIGN CANDIDATE / UNBOUND |
| Whole-host/VM shutdown หรือ unrestricted process-tree repair | ไม่อยู่ใน finite admitted attempt scope | กระทบ unrelated production actors และไม่มี approved action scope | EXCLUDED จากแพ็กเกจนี้ |

ไม่มี family ใดได้ SELECTED/PASS จากเอกสารนี้ ไม่มีการ probe cgroup/service/VM ปัจจุบัน
ไม่เลือก host control ของ #112/S24 หรือ production bridge มาเป็น E โดยอนุมาน

Technical reference constraints จาก primary documentation (ตรวจเอกสาร 4 พ.ย. 2026):

- [Linux cgroup v2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html):
  cgroup.kill ส่ง SIGKILL ใน hierarchy; populated บอก live-process membership
  ข้อมูลสองอย่างนี้ไม่มี exact wait/reap และ stream EOF receipt ของเรา จึงไม่รับเป็น complete cleanup proof
- [PR_SET_CHILD_SUBREAPER](https://www.man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html):
  adoption ใช้ nearest living ancestor subreaper; flag ไม่สืบทอดผ่าน fork
  profile ต้องพิสูจน์ actor ที่เป็น ancestor/ตั้ง flag จริง ไม่ใช่ process ข้างเคียง
- [pidfd_open](https://www.man7.org/linux/man-pages/man2/pidfd_open.2.html) และ
  [wait/waitid](https://www.man7.org/linux/man-pages/man2/waitpid.2.html):
  retained task handle กับ child wait/reap เป็นคนละ obligation; WNOWAIT ยังไม่ consume wait status
  E ต้องพิสูจน์ child eligibility และ exact subsequent reap ตาม accepted source protocol

เอกสาร upstream เป็น interface background ไม่ใช่ evidence ของ kernel/version/delegation
หรือสิทธิ์ใน deployment ของผู้ใช้. Concrete profile ต้อง pin actual kernel/source/library
และ test semantics ของระบบเป้าหมายแยก ไม่อ้าง latest docs รับรอง host ปัจจุบัน

## 5. Takeover, reaper arbitration และ audit

Candidate ancestor-E path ต้องทำลำดับนี้เมื่อ R ตายจริง:
ใน family นี้ E ต้องเป็น direct parent ของ R และตั้ง/ตรวจ subreaper ก่อน R launch
ส่วน family ที่ใช้ reaper คนละตัวต้องเสนอ parent/arbitration proof แยก ไม่ยืมข้อสรุปนี้

1. Independent R exit evidence และ exact ownership/reap ของ R ตาม bound reaper
   Fence further capture/publication; consumed attempt ห้ามเปิดใหม่
2. ระบุ O/S ที่ adopt/ยังอยู่จาก independently retained identities และ granted terminal scope
   หยุด O/S ภายใต้ shared phase deadline; ไม่ signal original backend worker/provider
3. เมื่อ S exit/reap แล้วจึงพิสูจน์ H direct-adopted eligibility ก่อน stop/reap H
   ถ้า S reap H ก่อนตาย ให้เก็บ accepted S proof หรือ unknown reaper ตาม evidence
   ห้าม E claim own reap หรือ signal H ซ้ำเพราะ ECHILD
4. Drain/discard ด้วย bounded reads; ยืนยัน helper stdout/stderr และ report EOF แยกกัน
   E/reaper ต้องไม่ถือ accidental write-end ที่ทำให้ EOF ค้าง
5. Return cleanup-only record ถ้าส่ง/เก็บ record ไม่ได้ให้ disposition UNKNOWN
   report-full/logging failure ต้องไม่ block terminal stop, retry หรือเริ่ม helper รอบสอง

ลำดับนี้เป็น proof obligation ไม่ใช่ implementation ในแพ็กเกจนี้
R ตายแล้วแต่ S ยังเป็น parent ของ H => E ยังไม่มี direct-child reaping right ของ H
Kernel adoption ให้ parent relationship ไม่ได้สร้าง authority grant ใหม่
Concurrent reaper/late R report/wrong generation ต้อง reject ตาม accepted arbitration

Bulk-stop family ที่หยุด H ขณะ S ยังอยู่ไม่ถือว่าผ่านลำดับข้างต้นโดยอัตโนมัติ
ต้องมี alternate arbitration contract ที่ independently review แล้ว
ไม่อ้าง unit empty เป็นหลักฐานว่า E reap ทุก actor; zombie/EOF ต้องมี evidence แยก

R exit0 หลัง FINAL แต่ก่อน completion commit เป็น unexpected loss สำหรับ active attempt
Normal completed R exit ต้องมี independently validated sealed completion/closure protocol
ซึ่งยังไม่ implement; exit0/final-prefix อย่างเดียวไม่พอ
ถ้ามี valid completion ที่ commit และปิด attempt ไปก่อนแล้ว ให้ตรวจ immutable record เดิม
ไม่ใช้เอกสารนี้ย้อนแก้ committed history หรือสร้าง observation ใหม่

E ตาย/สูญเสีย authority/สูญเสีย reaper ระหว่าง cleanup => UNKNOWN/STOP_UNCONFIRMED
ไม่มี implicit E2/E3 watchdog chain. Availability ของ accepted external boundary
เป็น explicit threat-model assumption; ถ้า requirement ต้องรับ E/host failure ด้วยแต่ไม่มี
accepted proof ให้สรุป profile infeasible ไม่ตั้งสมมติฐานว่า E ไม่มีวันตาย

## 6. Budget และ deployment feasibility gate

D_outer=T0+45 s; D_attempt=min(Ta+20 s,D_outer); D_capture<=D_attempt−3 s
T0/Ta ผูกครั้งเดียวใน trusted boundary ตาม §3; ห้าม reset ตอน R loss/adoption/restart
native open/lock/query/close alarm1s และ inherited byte caps คง requirement เดิม

หลัง actual R death candidate ancestor-E มี two stop phases เช่นเดียวกับกรณี S loss:
O/S concurrent TERM<=0.2 s + KILL wait<=1 s; แล้ว H TERM<=0.2 s + KILL wait<=1 s
รวม allowed stop waits<=2.4 s; remaining<=0.6 s สำหรับ R-loss detection, R reap,
arbitration, bounded drain/EOF และ metadata. **ไม่ใช่ 0.6 s เพิ่มจาก reserve3 s**
ต้องวัด operation ทั้งหมด; หากต้องเพิ่ม phase/controller handoff ที่ไม่ fit ให้ HOLD
ไม่ซ่อน R-reap หรือ receipt I/O เป็นงานนอก budget

E อาจพบ R loss หลัง D_capture หรือเหลือเวลาน้อยกว่า3 s ระหว่าง R cleanup เดิม
ใช้แค่เวลาที่เหลือจริง ห้ามให้ fresh3 s; incomplete => STOP_UNCONFIRMED
การบันทึกผล unconfirmed อย่างซื่อสัตย์ไม่ใช่ positive complete-stop proof
ถ้าต้องการรองรับ schedule นั้นแบบ confirmed แต่ทำไม่ทัน => feasibility blocker
scheduler stalls/uninterruptible I/O ไม่รับประกัน hard real-time cessation

Internal4 actor address-space caps 256 MiB×4 ไม่ใช่ approved total deployment budget
ถ้า E เป็น process ใหม่ => อย่างน้อย5 actors; controller/reaper/bootstrap แยกให้นับเพิ่ม
ต้องมี exact max processes/threads/FDs/memory/CPU/retention/startup cost พร้อม headroom
aggregate physical-memory enforcement และ environment support ยัง UNBOUND (B6/gate4)
Existing manager cost ต้องระบุ allocated share ไม่ถือว่า free และห้าม hidden helper/watchdog

control/report frames ต้องอยู่ใน inherited <=512-byte bounds ไม่มี raw capture
profile ต้องเสนอ closed message types, finite message count, queue/retention bounds
ก่อน implementation review; ส่ง binding refs ไป trusted catalog ไม่ dump secret-bearing config
overflow/full channel/missing audit => UNKNOWN/HOLD ไม่เพิ่ม bounds หรือ skip เป็น pass

## 7. Required OA07 evidence — ทุกแถว NOT RUN

EC IDs เป็น design obligations ใหม่ ไม่ใช่ OC/OA row ใหม่หรือ test counts

| ID | Real owned stimulus / oracle ที่ต้องมี | Acceptance / HOLD criterion |
| --- | --- | --- |
| EC01 | Profile absent/forged/expired/revoked/wrong boot/generation/delegation | ไม่มี R/descendant/protected capture ก่อน independent admission; fake tag ไม่พอ |
| EC02 | R ตายก่อน O/S spawn และหลัง R fork แต่ก่อน caller รับ return/identity | Consumed + bounded exact containment/reaper evidence หรือ infeasible; ไม่อ้าง no R |
| EC03 | R ตายขณะ O/S/H fork สำเร็จแต่ก่อน E registration/witness | Independent launch-gap coverage; ไม่มี new PID lookup/host scan/respawn |
| EC04 | R ตายหลัง retain/ACK ก่อน G และหลัง G ก่อน native query | ไม่มี new capture/publication; exact owned set stop/reap/EOF ตาม grant |
| EC05 | R ตายระหว่าง native read lock, first frame, complete prefix และ valid S FINAL ก่อน commit | Observation UNKNOWN แม้ cleanup confirmed; ไม่ reconstruct FINAL/goal |
| EC06 | S ยัง alive กับ H; S ตายพร้อม R; S reap H ก่อน R loss | Correct parent/arbitration; no double signal/reap; unknown facts ไม่ default |
| EC07 | Inherited writer/full report/stalled consumer ระหว่าง R loss | Stop ไม่รอ logging/EOF เกิน absolute deadline; reap/EOF แยก |
| EC08 | Revoke/expire หลัง G; E cleanup grant ถูก revoke/หาย; controller/reaper ตาย | No capture continuation; finite grant/disposition ตาม threat model; ไม่มี watchdog chain |
| EC09 | Wrong unit/foreign actor/handle drift และ attempted membership escape | Reject before ARM หรือ prove no escape under admitted boundary; ไม่ signal unrelated actor |
| EC10 | Restart/whole-domain rollback ของ store+authority+dossier+context/profile refs | Accepted independent anchor กัน retry; checksum-valid rollback ยัง reject |
| EC11 | R loss ที่ cutoff/late cleanup, resource pressure และ report retention failure | Same T0/Ta/deadlines; no fresh time/caps; infeasible ไม่ relax assertion |
| EC12 | Independent harness ตรวจ exit, exact reap, streams, all remaining children และ public record | Finite owned oracle; private data ไม่รั่ว; controls results ไม่แทน source acceptance |

Harness นอก R ที่ใช้ทดสอบต้องประกาศ actor/resource cost และ diagnostic cleanup แยก
ห้าม cleanup ของ harness กลายเป็น E positive proof ถ้า production profile ไม่มี capability นั้น
Unknown/unavailable kernel device-I/O schedule ใช้ NOT RUN/UNBOUND ไม่ mock เป็น complete-stop pass
ทั้ง positive และ negative expected outcomes ต้อง preregister ก่อน run

## 8. Binding decision และ handoff

Concrete-profile dossier ต้องมีอย่างน้อย closed refs สำหรับ issuer/independent anchor,
exact source/interpreter/dependencies/kernel/boot/launch inventory, containment instance,
controller/reaper grants/expiry/revoke, pre-enrollment/identity protocol, T0/Ta/deadlines,
all actor resources, FD/channel map, private retention และ EC evidence locators
ตอนนี้ทั้งหมด **UNBOUND**; ไม่มี actual unit/service/path/PID หรือ private key ในเอกสารนี้

| Evidence field | Current record |
| --- | --- |
| ID/status/scope | OA07 NOT RUN; B4 OPEN; design-only external containment requirements |
| Requirement | Observer/adoption §7–9 / B4,B6 / OC15; ไม่เปลี่ยน OC definitions |
| Source SHA/path | Exact documentation commit ใน PR; source implementation unchanged |
| Task/control/stimulus | EC01–EC12 preregistration obligations เท่านั้น ยังไม่มี tests |
| Expected | No ARM/G without accepted external profile; R loss => UNKNOWN + separate cleanup facts |
| Actual | Design document only; EC controls NOT RUN; no runtime/containment binding selected |
| Environment/dependencies | Abstract Linux candidate; deployment kernel/permissions/headroom UNBOUND |
| Private evidence locator | UNBOUND; ไม่มี Dev/private evidence read |
| Privacy-safe summary | Opaque future binding refs และ requirement tables เท่านั้น |
| Independent review | Parent round-13 operator-supplied APPROVE; current design PENDING review |
| Unresolved limits | Launch gap, reaper/controller availability, 3s feasibility, B1/B3/B6/OA12 |
| Handoff | Review contract/feasibility ก่อน source package; no installation/action approval |

ขั้นถัดไปหลัง design review คือเลือก narrow owned-offline feasibility candidate จาก
actual supported capabilities ที่ได้รับ scope แยก และออกแบบ controls โดยรักษา gaps ที่ยังพิสูจน์ไม่ได้
ถ้าไม่มี candidate ที่ผ่านข้อจำกัด ให้รายงาน production infeasible/HOLD
ไม่เลือกระบบที่มีอยู่จริง/ขอ credential/เริ่ม service/cgroup/VM action จาก contract acceptance

Interface/security boundary change ต้องผ่าน [SPEC §14](SPEC.md#14-change-control)
ก่อน implementation merge; design/source review และ green CI ไม่ใช่ action approval
PR117 draft; B1–B7 OPEN; OA06/OA08 PARTIAL; OA07/OA12 NOT RUN; J0 PAUSED
(#112 `e7142cf71792475af9375140df39acd55944d8d1`); OC18 NOT RUN;
R1 NOT AUTHORIZED / R2 HOLD. ไม่มี Dev/pilot/release/deployment
