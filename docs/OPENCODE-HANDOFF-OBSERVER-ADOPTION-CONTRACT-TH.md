# OpenCode B4 — production observer/adoption contract candidate

วันที่: 3 พฤศจิกายน 2026 (Asia/Bangkok)
Input: draft PR #117 ณ `48716cbc07af3430b56a4edc738664d357a7eb5e`
สถานะ: **CONTRACT CANDIDATE / NOT IMPLEMENTED / NO PRODUCTION BINDINGS**

## 1. Review checkpoint และขอบเขต

ผู้ใช้ส่งผลรีวิวรอบ 6: APPROVE supervisor-loss controls ณ input head
ปิดข้อขาดเรื่องทดสอบ supervisor ตายหลัง spawn ใน named fixture profile
B4 ยัง OPEN เพราะ observer/adoption/cleanup เป็น test-only
บันทึกนี้เป็น operator-supplied review ไม่ใช่ GitHub review submission
ไม่มี exact approval timestamp จึงไม่เติมเวลา

คำสั่ง “ทำขั้นถัดไป” ให้จัดทำ contract นี้ตามที่เสนอ ไม่เริ่ม implementation
หรือเปิด Dev/pilot ภายใต้คำว่า production ในชื่อเอกสาร
contract ระบุสิ่งที่ production source ต้องพิสูจน์ ไม่อ้างว่ามี API/service/schema แล้ว

อ้างอิง:
[ผล supervisor-loss controls](OPENCODE-HANDOFF-SUPERVISOR-LOSS-REVIEW-TH.md),
[supervision primitive scope](OPENCODE-HANDOFF-B4-SOURCE-REVIEW-TH.md),
[B1–B7](OPENCODE-HANDOFF-BLOCKER-CLOSURE-TH.md),
[authority/Facts](OPENCODE-HANDOFF-FACTS-CONTRACT.md),
[snapshot/VFS](OPENCODE-HANDOFF-SNAPSHOT-CONTRACT.md),
[OC01–OC18](OPENCODE-HANDOFF-CONTROLS-TH.md)

หลักฐาน input: native idle helper exit จาก pipe EOF ได้ใน controls
แต่ TERM-ignore/nonreading helper ยังอยู่หลัง supervisor ตายจน test observer cleanup
ไม่มี FINAL => observation เดิม UNKNOWN แม้ observer ยืนยัน helper reap/EOF ภายหลัง
ผลเหล่านี้ไม่ใช่ production observer implementation หรือ independent authority issuer

## 2. Selected topology และ trust boundary

เลือก candidate เป็น **fresh per-attempt Linux x86_64 observer** ที่ตั้งและตรวจ
child-subreaper ก่อนสร้าง descendants; supported POSIX filesystem และ native
SQLite 3.45.1 ตาม capture source เดิม ไม่สมมติ Windows/DrvFS รองรับ
ไม่ตั้ง subreaper ใน bridge process เดิมหรือ process ของ operator
observer ต้องไม่มี child เดิมหรือ descendant นอก finite attempt นี้

| Actor | Parent / capability ที่ต้องรับก่อน ARM | สิ่งที่ห้ามอนุมาน |
| --- | --- | --- |
| B: trusted bootstrap boundary | เปิด observer ตาม accepted immutable source/interpreter profile; สร้าง private pipes/retained identities จาก issuer ที่รับแยก; ผูก T0 และ attempt admission | ชื่อไฟล์ owner-only/hash/PID/ข้อความใน checkpoint ไม่ใช่ issuer authentication; B ไม่ใช่ daemon/API ใหม่ที่อนุมัติแล้ว |
| R: observer | เป็น parent ของ O และ S; retain pidfds ของสอง direct children; เป็น subreaper ก่อน spawn; retain read ends ของ helper stdout/stderr และ control reports; มี bounded cleanup capability | subreaper setting ไม่ใช่สิทธิ์ signal ทุก process และไม่ทำให้ actor เดิมนอก attempt กลายเป็นของ R |
| O: observation owner | child ใหม่ของ R; ทำ admitted authority/context/evidence/Facts/verifier path ตาม contract เดิม; ถือ command lease ไป S; ไม่ถือ helper output write ends/observer report writer | O ไม่ใช่ original OpenCode worker/provider และไม่มีอำนาจ submit/resume/reconcile |
| S: supervisor | child ใหม่ของ R; สร้าง H เพียงหนึ่งตัว; retain H pidfd และเป็น reaper หลักขณะ S ยังอยู่ | source primitive เดิมยังไม่ได้ทำ handshake/production observer path ใน contract นี้ |
| H: retained-FD native helper | direct child ของ S ตอนเริ่ม; fixed source/argv/fd map; ไม่มี descendants; หลัง S ตายอาจ adopt มาที่ R ตาม kernel eligibility | helper exit, EOF, reap, native job terminal status และ verified goal เป็นคนละข้อเท็จจริง |

R/O/S/H คือ internal candidate 4 processes ไม่ใช่ deployment budget ที่อนุมัติแล้ว
B ต้องระบุว่าใช้ existing trusted launch surface ใดและมี process เพิ่มหรือไม่
external containment ใน section 7 ถ้าต้องมี actor เพิ่ม ต้องนับและรับ scope ใหม่
ไม่ซ่อน actor ที่ห้าหรือ watchdog chain ไว้ใต้ชื่อ bootstrap

host/same-uid/same-process compromise ไม่ถูกแก้ด้วย Python object privacy
ต้องบันทึก trust assumptions และ source/dependency/host ownership ที่รับจริง
ไม่ยืม bootstrap/key/tool/source หรือ seed ที่ยัง HOLD จาก #112/S24

## 3. Authority และ attempt admission

ก่อนสร้าง O/S/H หรือเปิด protected state/evidence handles ต้องมี independently
resolved current admission ตาม B1+B3; observer bootstrap เองก็ต้องมี finite launch scope
issuer/resolver/anchor implementation และ private bindings ยัง UNBOUND
การตรวจตาม contract ไม่แปลง checkpoint/caller JSON ให้เป็น authority

admission ต้อง bind อย่างน้อย:

- exact source/interpreter/dependency/host/boot/workspace/repo/head identities;
  one original job/request/session/fingerprint opaque mapping และ goal/profile refs
- observer/owner/supervisor/helper actor roles และ fixed launch inventory;
  permitted state/context/evidence/current-binary reads พร้อม physical DB/read-lock scope
- one attempt ref, fresh protected admission generation และ independent rollback anchor;
  exact T0/deadlines/byte/resource caps, revocation/expiry และ terminal cleanup policy
- pidfd/witness/control pipe identities และ exclusive private output/retention refs;
  public output allowlist ไม่รวม raw IDs/paths/config/output/fingerprint
- operator-independent control/containment profile ที่รับแล้วสำหรับ R failure;
  actor/resources/action ของ profile นั้นต้องชัด ไม่เติมจากความจำ

capture authority และ terminal cleanup authority ต้องแยกความหมาย
expiry/revocation หยุด capture/Facts/publication ทันที
cleanup capability ที่ issuer ให้ตั้งแต่ launch คงใช้ได้เฉพาะ owned admitted actors
จนถึง absolute cleanup deadline ที่ล็อกไว้ ไม่ใช่สิทธิ์อ่านต่อหรืออำนาจทั่วไป
ถ้า issuer ไม่ยอมให้ bounded cleanup หลัง revoke จะไม่เปิด ARM/G ใน profile นี้

single-use admission ต้องถูก consume ก่อน side effect แรกที่อาจสร้าง O/S/H
และอยู่ใน rollback domain ที่ B3 รับแล้ว
unknown launch/unknown execution/missing receipt ถือว่า consumed
restart/new Python object/new observer/renamed directory ไม่ reset attempt
ไม่มี retry/respawn/replay หรือ stale-claim deletion เพื่อทำให้ launch ผ่าน

## 4. Startup และ PID-reuse-safe witness protocol

ทุกชื่อ state/message ใน section นี้เป็น proposed private protocol labels
ไม่ใช่ new OpenCode native states, MCP scopes หรือ API ที่ implement แล้ว

1. B รับ admission, ล็อก source/dossier/anchor/T0 และตรวจ finite launch/containment gates
   R ตั้งและตรวจ process-local subreaper ก่อนสร้าง O/S
   source/interpreter/resource/FD checks ที่ไม่ผ่าน => PRE_ARM_HOLD ไม่มี protected capture
2. R สร้าง O/S ใหม่พร้อม retained pidfds; helper gate ยังปิด
   pipe map ต้องตัด inherited write ends ที่ทำให้ fake EOF หรือ lease ไม่จบ
   R retain เฉพาะ helper stdout/stderr read ends; O ไม่ได้รับ observer/witness handles
3. S fork H ครั้งเดียวโดย H ยังรอ startup gate และยังไม่อ่าน DB/evidence
   ส่ง bounded launch witness ที่ bind attempt/generation/role/parent identity
   ผ่าน dedicated private pipe; ไม่รับ arbitrary PID/path จาก checkpoint หรือ caller
4. R เปิด retained H pidfd จาก witness ขณะ S ยังมีชีวิตและรับประกัน H ยังไม่ถูก reap
   ผูก parent/child/launch identity และ channel provenance ให้ครบก่อน ACK
   PID เป็น correlation ใน trusted handshake เท่านั้น; ไม่เป็น signal target โดยลำพัง
   witness แก้/ซ้ำ/ช้า/ผิด generation, pidfd เปิดไม่ได้ หรือ S ตายก่อน ACK => ไม่ส่ง G
5. R และ S ยืนยัน ACK/source/current authority/deadline/FD map;
   O ส่ง capture G ได้หนึ่งครั้งหลัง R gate เปิดแล้วเท่านั้น
   READY อย่างเดียวไม่อนุญาต capture; EOF/broken pipe/extra frame ทุกจุดยกเลิก attempt
6. S ส่ง fixed context-before/job/context-after capture แค่ชุดเดียว
   R ไม่อ่านแย่ง stdout กับ S ระหว่าง normal path; retained read ends ใช้ witness EOF
   หรือ bounded drain หลัง S ตายเท่านั้น ไม่ hash/export raw shared DB/output แทน verifier

ไม่มีการใช้ /proc scan, recent-job search, pidfd_getfd, SCM_RIGHTS, stored backend PID
หรือ numeric-PID/PGID signal เป็น fallback
process witness/retained source handles ไม่พิสูจน์ original invocation binary provenance
B2 และ original-goal profile ตาม B5 ยังคงต้องผ่านแยก

ถ้า fork return/setup ถูก interrupt จนไม่รู้ว่า H เกิดหรือไม่ ให้
launch_known=false / helper_started=null / STOP_UNCONFIRMED
ไม่อ้าง no helper, ไม่เลือก PID ใหม่ และไม่ทำ launch รอบสอง
capture gate ปิด; cleanup ใช้ได้เฉพาะ identity/ownership ที่ยังพิสูจน์ได้
launch window ที่ยังไม่มี retained identity เป็น source-feasibility blocker ที่ต้องพิสูจน์
test-only witness hook ที่ผ่านแล้วไม่ใช่ implementation ของ production handshake นี้

## 5. Reaping owner และ adoption arbitration

ขณะ S อยู่และเป็น parent ของ H: S เป็น helper reaper/stop owner หลัก
R ไม่ signal H แข่งกับ S แม้ retain pidfd ได้แล้ว
ถ้า O ตาย/lease EOF/revoke/deadline ให้ S หยุด H ตาม finite cleanup path
ถ้า S ไม่ตอบ R มีสิทธิ์หยุดเฉพาะ admitted direct O/S wrappers ตาม cleanup capability
ไม่ signal original OpenCode job/provider/process group

หลัง R observe S exit และยืนยัน direct-child reap:
R ตรวจ H pidfd binding เดิม และ adopted direct-child eligibility ด้วย
waitid(P_PID, WEXITED|WNOHANG|WNOWAIT) ก่อนทุก signal/reap
running direct child ที่ waitid คืน None เป็น eligibility; ECHILD เป็นการปฏิเสธ
pidfd readiness อย่างเดียวไม่พิสูจน์ว่า R เป็น reaper

- adopted H ที่ยังอยู่: R ใช้ retained pidfd TERM แล้ว KILL ตาม shared deadline;
  ต้องยืนยัน waitpid ของ exact admitted child และ stdout/stderr EOF แยกกัน
- H ที่ exit/adopt มาแล้ว: reap โดยไม่ส่ง signal ซ้ำ
- H ที่ S reap ไปแล้วก่อนตาย: pidfd บอก exit ได้ แต่ ECHILD ไม่ใช่ observer reap;
  บันทึก helper_exit_observed=true / helper_reaped_by_observer=false
- ECHILD ที่อธิบายด้วย accepted lifecycle ไม่ได้, handle/parent drift หรือ witness ไม่ครบ:
  UNKNOWN/STOP_UNCONFIRMED ไม่ใช้ waitpid(-1), host inventory หรือ numeric signal เพื่อซ่อม

kernel adoption ไม่สร้าง authority ใหม่
สิทธิ์ของ R มาจาก bounded admission เดิมและจำกัด exact attempt เท่านั้น
production source ต้องมี arbitration ที่ไม่มี concurrent reaper หรือ signal จาก O
และต้องพิสูจน์ no-double-reap/no-PID-reuse ด้วย real races ก่อน source acceptance

## 6. หลักฐานและ disposition

original FINAL ในเอกสารนี้หมายถึง terminal report ของ S สำหรับ attempt นี้
ไม่ใช่ native completed flag หรือ output ของ original OpenCode job

private observation record ต้องเป็น closed schema พร้อม exact field types/size limits
อย่างน้อยมี:
attempt/source/admission-generation refs, original FINAL received/validated,
supervisor exit/reap, helper exit/adoption/reap-by-which-actor,
report_eof, helper_stdout_eof, helper_stderr_eof,
cleanup reason/authority/deadline, context/authority/head revalidation,
independent goal verifier result และ unresolved flags

null แปลว่า unobserved/unknown ไม่ default เป็น false หรือ true
capture/goal proof, helper cessation, reaping/EOF และ action authority ต้องไม่รวมเป็นบิตเดียว
ไม่มี observed exit-code/prefix/model text ที่แทน original-goal verifier ได้

| เหตุการณ์ | Observation disposition / publication |
| --- | --- |
| Valid original FINAL + exact completed capture + independent accepted full goal evidence + current authority/context/head + required stop/reap/EOF proof | eligible to call existing pure planner; advisory outcome only, authorizes_actions=false; ไม่มีการรับประกันว่า implementation นี้มีแล้ว |
| ไม่มี/ขาด/ซ้ำ/ผิด generation/over-cap original FINAL แม้ R cleanup สำเร็จ | UNKNOWN สำหรับ observation เดิม; lifecycle cleanup record แยกได้ ไม่สร้าง replacement FINAL/Done |
| บาง actor stop/reap หรือ EOF ไม่ยืนยัน | STOP_UNCONFIRMED และ UNKNOWN/HOLD ตาม receiving layer; ไม่อ้าง all actors stopped |
| native state active/failed/cancelled/permission_required/unknown_exit หรือ verifier ไม่ยอมรับ | ยังคง native facts และ restricted HOLD ตาม Facts contract; observer ไม่เปลี่ยน backend terminal status |
| R/issuer/anchor/current context หาย หรือ elapsed/clock/resource assumptions ผิด | หยุด publication; UNKNOWN/HOLD; consumed attempt ไม่ถูกปล่อยกลับ |

report EOF แปลว่า channel ปิด ไม่ใช่ helper stop proof
helper stdout/stderr EOF ก็ไม่ใช่ waitpid/reap proof
R cleanup receipt เป็น lifecycle evidence เท่านั้น ไม่ recover missing goal FINAL
public audit/receipt เก็บ opaque refs/allowlisted dispositions/counts/approved commitments
ไม่ส่ง raw PID/job/request/session/path/prompt/output/fingerprint/config/exception/credential
private retention/output creation ต้องมี explicit admission และ exclusive owner-only destination
partial record ไม่ถูกลบทิ้ง/reuse/chmod เพื่อทำให้ผ่าน
checkpoint append/commit ยังเป็น scope แยกและต้องใช้ original CAS/revalidation semantics

## 7. Observer death และ irreducible failure boundary

R ตายก่อน/หลัง G => ไม่มี trusted observer completion; observation เดิม UNKNOWN
subreaper ของ R ไม่ทำให้ R เป็นอมตะ และไม่รับประกันว่า H หยุดเมื่อตัว R ตาย
pdeath signal/pipe EOF/timeout อย่างเดียวไม่พิสูจน์ complete stop/reap
ไม่เพิ่ม observer-of-observer chain โดยอัตโนมัติ

ก่อน actual ARM/G ต้องมี separately accepted external containment/control profile
ที่ bind exact admitted actor set และวิธี detect R loss/stop/confirm exit/reap/EOF
พร้อม actor/resource/authority/deadline และ failure semantics
profile นี้ยัง UNBOUND; contract ไม่เลือก/ติดตั้ง systemd/cgroup/container/daemon
หรืออนุญาต shutdown VM, SSH/CIM, service restart หรือ process-tree kill

ถ้าเลือก profile ไม่ได้หรือพิสูจน์ภายใน budget ไม่ได้ => production infeasible/HOLD
ไม่ลดข้อกำหนดให้ observer death กลายเป็น supported success case
external profile ที่ยืนยัน stop ไม่ได้ต้องรายงาน UNKNOWN/STOP_UNCONFIRMED
uninterruptible kernel I/O อาจทำให้ stop ไม่ครบแม้ signal ถูกต้อง
จึงไม่อ้าง hard real-time all-process cessation หรือ all-writer quiescence
กรณีนี้เป็น explicit residual blocker ไม่ใช่การขยาย cleanup deadline แบบเงียบ

## 8. Shared time/resource budget

T0 ถูก B ล็อกก่อน observer launch; D_outer=T0+45 s
Ta ล็อกครั้งเดียวก่อน side effect แรกที่อาจสร้าง O/S/H หรือเริ่ม protected observation
D_attempt=min(Ta+20 s,D_outer); ไม่เลื่อน Ta หลัง READY/adopt/restart

เพื่อให้ stop O/S แล้ว adopt/stop H ต่อกันได้จริง เลือก capture cutoff
D_capture <= D_attempt-3 s
เหลือ cleanup ร่วมอย่างน้อย 3 s **ภายใน** D_attempt/D_outer เดิม
capture profile นี้อาจใช้ได้น้อยกว่า 17 s และต้อง HOLD ถ้าเวลาที่เหลือไม่พอ
ไม่มี fresh 20 s หรือ fresh 45 s ตอน handoff/adoption

O/S ที่ R เป็น direct parent หยุดพร้อมกันได้เฉพาะถ้า admission อนุญาต:
TERM grace <=0.2 s แล้ว KILL wait <=1 s โดยใช้ shared phase deadline
หลัง S reap จึง adopt H: TERM <=0.2 s / KILL wait <=1 s
สอง phase รวม worst allowed waits <=2.4 s; remaining <=0.6 s เป็น
bounded drain/reap/metadata budget ไม่ใช่สิทธิ์ retry
ถ้า scheduler/I/O ทำไม่ทัน ให้ STOP_UNCONFIRMED ไม่ขยายเวลา
native helper open/lock/query/close alarm 1 s เดิมต้องคงอยู่

proposed per-actor RLIMIT_AS <=256 MiB สำหรับ R/O/S/H
ผลรวม address-space caps สี่ตัว <=1,024 MiB ไม่ใช่ RSS/physical-memory guarantee
aggregate physical resource enforcement, external actor cost และ actual host headroom
ยัง UNBOUND ต้องผ่าน gate 4/B6 ก่อน pilot; ไม่อ้างว่า RLIMIT_AS สองตัวเดิมปิดประเด็นนี้
stdout cumulative <=64 KiB, stderr <=4 KiB และ reject diagnostic data ตาม profile เดิม
private control/report frames <=512 bytes ต่อ frame, fixed finite message count;
ไม่มี raw capture ใน control messages; extra/duplicate/trailing/partial frames reject
source ต้องแจกแจง FD/byte/memory limits ที่ทุก call site; bounds บนกระดาษไม่ใช่หลักฐาน

## 9. Required controls — NOT RUN สำหรับ contract นี้

OA01–OA12 เป็น obligation IDs ของ contract ไม่ใช่ S24 rows, OC trial counts หรือ
การแก้นิยาม OC01–OC18; controls 29/9/48 ที่รับแล้วเป็น input evidence เท่านั้น

| ID / mapping | Required real stimulus / acceptance evidence |
| --- | --- |
| OA01 / B1,B3 / OC02,03,13,14 | forged/expired/revoked/wrong-anchor admission; ไม่มี O/S/H/protected capture เมื่อ gates ไม่ครบ; checkpoint/caller booleans เข้าไม่ได้ |
| OA02 / B4 / OC04,05,15 | startup gate trace มี T0/Ta/ACK ก่อน G; helper ไม่มี state read/exec side effect นอก inventory; duplicate/wrong-role frames ไม่ทำ fork/capture เพิ่ม |
| OA03 / B4 / OC07,15 | S ตายก่อน witness/ระหว่าง pidfd ACK/หลัง fork-return gap; missing identity ต้อง UNKNOWN ไม่อ้าง no helper; ไม่มี PID-reuse signal หรือ respawn |
| OA04 / B4 / OC15 | ก่อน adoption cleanup ถูก deny; หลัง exact S reap จึง stop/reap adopted H; concurrent reaper/foreign child/wrong generation reject |
| OA05 / B4 / OC15,16 | H ถูก S reap ก่อน FINAL หาย: R ไม่ claim adopted/reaped และไม่ signal ซ้ำ; independently observed stdout/stderr/report EOF ไม่รวมเป็นหลักฐานเดียว |
| OA06 / B4 / OC15 | O/S ตายพร้อมกันระหว่าง hung/prefix/nonreading helper; exact admitted actor set cleanup ได้หรือ honest unconfirmed; ไม่มี group kill |
| OA07 / B4,B6 / OC15 | R ตายจริงก่อน/หลัง G กับ accepted external containment profile; ถ้า profile ยัง unbound ต้อง block ARM/G; ไม่มี self-certified observer-death pass |
| OA08 / B4 / OC09,15,16 | inherited write end/full pipe/trailing/partial/duplicate FINAL; reject publication; drain bounded และไม่มี raw output/ID/exception leaks |
| OA09 / B1,B3 / OC02,14 | concurrent/restarted observers และ whole-store rollback ไม่ redeem admission ซ้ำ; unknown launch consumes attempt; ไม่มี stale-claim repair |
| OA10 / B4,B6 / OC15 | shared Ta/D_outer, sequential adoption-stop และ aggregate resources ถูก enforce; no fresh timer/window/hidden actor; actual bound failure ไม่ skip/relax |
| OA11 / B4 / OC16 | private retention/output creation/partial evidence failure ไม่แตะไฟล์เดิม; allowlisted public lifecycle record ไม่เปิด sensitive values |
| OA12 / B1–B6 / OC11,12,17 | joined authority/context/capture/full goal verifier/Facts/planner path; valid original FINAL เท่านั้นที่ eligible; absent FINAL แม้ cleanup สำเร็จยัง UNKNOWN |

ก่อน implementation acceptance ต้องมี requirement → source → control →
actual evidence → exact commit SHA พร้อม independent review
contract acceptance ไม่ทำให้ controls ในตารางเป็น PASS หรือเลือก actual bindings
production interface ต้องผ่าน [SPEC section 14](SPEC.md) ก่อน implementation merge
B1 issuer/B3 rollback/B2 invocation/B5 goal และหก pilot gates ต้องมี disposition แยก
B4 ไม่ถูกปิดด้วยการรับ contract เพียงอย่างเดียว

## 10. Delivery boundary

รอบนี้เพิ่มเอกสาร contract เท่านั้น ไม่เพิ่ม source/schema/test/workflow/authority service
ไม่รัน OA controls, ไม่สร้าง private runtime binding หรือเปิด current Dev values
CI ที่อาจทำงานอัตโนมัติเป็น existing component regression ที่ต้องอ้าง exact head แยก
ไม่มี test count ใดเป็น production source acceptance/action approval

ขั้นถัดไปคือ independent contract/feasibility review โดยเฉพาะ launch-witness gap,
external containment ของ R loss, reaper arbitration และ shared stop/resource budget
เมื่อรับ contract จึงค่อยเตรียม bounded offline implementation/control package
production containment/authority ที่ยัง UNBOUND ต้องคงไว้ ไม่แทนด้วย fixture launcher

PR #117 draft/unmerged; B1–B7 OPEN; J0 PAUSED; #112/#80/#96/private bindings ไม่เปลี่ยน
R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN
ไม่มี Dev/pilot/archive invocation/evaluation arm/model/API/key/config/release/deployment
