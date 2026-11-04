# OA07 alternate contract — pre-enrolled E launch broker / sole reaper

วันที่: 4 พฤศจิกายน 2026 (Asia/Bangkok)
Input: PR117 `7489aa4b59165bd8a589fc506d4636919e46622e`
สถานะ: **PROPOSED DESIGN / NOT IMPLEMENTED / NO NEW CAPABILITY GRANTED**

## 1. Checkpoint และข้อที่ต้องเปลี่ยน

ผู้ใช้ส่ง round-15 APPROVE (AS FEASIBILITY EVIDENCE) ณ input head
เป็น operator-supplied review ไม่ใช่ GitHub submission; ไม่มี timestamp จึงไม่เติมเอง
[registry-only protocol ที่ทดสอบ](OPENCODE-HANDOFF-ANCESTOR-FEASIBILITY-REVIEW-TH.md)
ถูกตัดออกจาก production-ready candidates ตาม live counterexample
เอกสาร/source evidence เดิมคง bytes เดิม ไม่ขยายข้อสรุปเป็นทุก ancestor-E family

แพ็กเกจนี้เสนอทางเลือกที่เปลี่ยนว่า **ใครเป็นผู้สร้าง/ถือ identity/reap**
แทนการเพิ่มช่องส่ง birth witness อีกช่องตามหลัง R/S fork
ไม่ใช้ diagnostic FD201 จาก test เป็น production authority โดยเปลี่ยนชื่อ
ไม่มี implementation/test ใหม่ และไม่เลือก/ติดตั้ง cgroup/service/container/VM/daemon จริง

ฐาน requirement: [OA07 design](OPENCODE-HANDOFF-OA07-CONTAINMENT-DESIGN-TH.md),
[observer/adoption contract](OPENCODE-HANDOFF-OBSERVER-ADOPTION-CONTRACT-TH.md),
[B1–B7](OPENCODE-HANDOFF-BLOCKER-CLOSURE-TH.md) และ [SPEC §14](SPEC.md#14-change-control)
นี่เป็น **alternative boundary proposal** ไม่ใช่ amendment ที่ effective แล้ว
accepted R-parent-O/S, S-parent-H topology เดิมยังไม่ถูกแทนที่ใน runtime/source

## 2. Candidate topology และ authority delta

B เป็น trusted bootstrap/lifecycle owner ของ E ตาม finite admission ที่ต้อง resolve แยก
E เป็น direct parent และ **sole launch/stop/reap owner ของ R/O/S/H ทั้งสี่ตัว**
ไม่มี O/S/H fork โดย R หรือ S; ไม่มี arbitrary descendant หรือ role replacement
R/O/S/H ยังเป็น logical work roles แต่ไม่ใช้ kernel adoption เป็น handoff ปกติ

| Role | Proposed responsibility | เปลี่ยนจาก source เดิมตรงไหน |
| --- | --- | --- |
| B | Resolve accepted issuer/anchor/profile; bind T0; launch/retain/reap exact E; final lifecycle accounting | B overhead/grant ยังต้องรับจริง ไม่ใช่ free/hidden guardian |
| E | Reserve finite roster; create/bind exact children; send gated commands; monitor/stop/reap/drain | จาก cleanup observer เป็น launch broker และ sole reaper; **new proposed boundary** |
| R | Authority/context/goal evidence join ตาม contract; ไม่มี process creation/reaping | ไม่เป็น parent/subreaper ของ O/S ใน family นี้ |
| O | Request G หลัง admitted R gate; ไม่มี helper gate-write/stop/reap authority | ไม่ส่ง G ตรงถึง H; request ไม่ใช่ permission |
| S | Fixed native request/response validation และ data-only terminal report | ไม่สร้าง H, ไม่ wait/reap H และไม่อ้าง helper_reaped=true |
| H | Fixed retained-FD helper/gate; ไม่มี descendants | Parent คือ E; native executable bytes ไม่ถูกแก้โดย contract นี้ |

E/R/O/S/H=5 actors + B แยก หาก broker/reaper/launcher ต้องแยก process ให้แจกแจงเพิ่ม
ไม่มี E2 chain, helper broker subprocess หรือ manager worker ที่ไม่นับ cost
หาก concrete source ต้องให้ R/S fork เพิ่ม จะไม่ใช่ profile ที่เสนอและต้อง HOLD

Authority ใหม่ที่ต้อง review ก่อนใช้จริง: finite launch/install-FD capability ของ E,
sole-reaper grant, E-gated helper start และ typed data/lifecycle join semantics
การถือ readonly DB/executable handles ไม่ให้ E สิทธิ์ query/evidence-read/model action
B ต้องมี independently admitted physical-state/metadata/source-read scope ก่อนเปิด handles
E รับได้เฉพาะ pre-bound fixed inventory ไม่รับ path/argv/SQL/PID จาก caller/checkpoint
Production issuer/anchor/profile/grants ทั้งหมดยัง UNBOUND

## 3. Pre-enrollment ที่มีสาระ มากกว่าการจองชื่อ

ก่อน side effect แรกของแต่ละ child E ต้อง reserve slot แบบ single-use ใน roster
`{R,O,S,H}` ซึ่ง bind attempt/generation/source/role/FD map และ absolute deadlines
slot state และ create-result storage อยู่ใน E boundary **ก่อน** child launch
role request ซ้ำ/ผิดลำดับ/ผิด generation ห้ามสร้าง process เพิ่ม; unknown creation consumes slot
ไม่มี respawn/replay/stale-slot repair หรือ retry ด้วย primitive อื่นหลังผลไม่ชัด

การจอง slot **ยังไม่ใช่ proof ว่า identity ถูก retain**
E ต้องใช้ birth primitive และ result-handling protocol ที่ให้ retained exact-child identity
โดยไม่ต้องให้ R/S ส่ง PID กลับมา และ child ยังเปิดได้แค่ closed startup gate
ก่อน E commit binding; gate wrapper ห้าม exec native program/read DB ก่อน approved G

| Slot stage | Required invariant | Missing/ambiguous result |
| --- | --- | --- |
| RESERVED | One finite role budget; no child yet claimed | ไม่อ้าง no child หาก create เริ่มแล้ว |
| CREATING | One create operation; fixed result destination; independent of R/S replies | Consume; no retry/no scan; explicit unknown launch |
| BOUND | E retains exact child identity and parent proof; no concurrent reaper | ไม่ส่ง ready/G ถ้า pidfd/source/FD map ไม่ครบ |
| READY | Fixed child acknowledges own gate/role/source; E still current | READY ไม่ใช่ capture grant |
| STARTED | One admitted G หลัง R/O/S readiness/current bindings | Revocation/R loss ปิด gate ไม่ restart |
| EXIT_OBSERVED | Retained identity signals termination evidence | ไม่ใช้แทน wait/reap/EOF |
| REAPED | Exact E child wait consumes status; evidence per role | ECHILD ที่อธิบายไม่ได้ => unconfirmed |
| CHANNELS_CLOSED | Required per-role/report/helper stream EOF แยก | Full/retained writer ไม่เปลี่ยนเป็น complete |

R อาจตายขณะ E create/bind H: E ไม่รอ R relay เพื่อรู้ว่า H เป็นลูกที่ตนสร้าง
เมื่อ R loss observed ให้ปิด further launch/G แล้วเก็บ create result ที่ in-flight ตาม
accepted birth protocol; cleanup เฉพาะ owned bound identities และไม่เริ่ม create รอบสอง
นี่คือจุดต่างจาก round-15 counterexample ที่ **S สร้าง H แล้ว E ต้องรอ R ส่ง identity**

## 4. Birth primitive และ gap ที่ยังไม่ถูกปิดด้วยกระดาษ

**E creator-side uncertainty ยังเป็น blocker ของ candidate นี้**
E อาจถูก interrupt/หมด budgetหลัง kernel create แต่ก่อน source บันทึก result
ย้ายผู้สร้างมา E ไม่ได้พิสูจน์ว่าช่องนี้หาย และไม่อนุญาตการหา child ใหม่ด้วย scan

| Primitive family สำหรับ feasibility review เท่านั้น | ข้อที่ต้องพิสูจน์ | Current disposition |
| --- | --- | --- |
| fork + E-owned pidfd acquisition | Exact returned child, no SIGCHLD auto-reap/concurrent reaper, no lost-return interval และ result durability ก่อน gate | UNBOUND; lost result หรือ pidfd failure ห้าม numeric fallback |
| clone/clone3 with CLONE_PIDFD | Exact child pidfd/result copyout ที่ E เก็บได้, source interruption/FD allocation failure, fixed non-thread child/flags และ deployment support | UNBOUND; ไม่เรียก syscall/เลือก actual implementation ในรอบนี้ |
| R/S/helper registration หรือ extra diagnostic witness | ไม่ทำให้ E เป็น creator และยังขึ้นกับ relay | REJECTED เป็นวิธีแก้ gap ของ profile นี้ |

Primary interface background ตรวจเอกสาร 4 พ.ย. 2026:
[pidfd_open](https://www.man7.org/linux/man-pages/man2/pidfd_open.2.html)
อธิบายเงื่อนไขของ fork-child handle เมื่อ child ยังไม่ถูก reap;
[clone/clone3 CLONE_PIDFD](https://www.man7.org/linux/man-pages/man2/clone.2.html)
คืน child pidfd ผ่านตำแหน่งใน parent memory;
[wait/waitid](https://www.man7.org/linux/man-pages/man2/waitpid.2.html)
แยก child status observation/WNOWAIT จาก subsequent reap

ข้อเท็จจริงเหล่านี้ **ไม่**พิสูจน์ E ledger commit, interrupted source wrapper,
rollback-resistant authority, child FD closure หรือ actual kernel availability
ไม่มีการอนุมานว่า CLONE_PIDFD ปิดทุก fork-return race โดยอัตโนมัติ
หากไม่มี finite atomic/observable result protocol ที่พิสูจน์ได้ => candidate infeasible/HOLD
ไม่มี fallback fork/scan/PGID kill/SCM_RIGHTS/pidfd_getfd หรือเปิดเพิ่มจาก review นี้

## 5. Startup, FD map และ data path ที่เสนอ

B/E ต้องเตรียม fixed pipes และ approved retained resources ก่อนสร้าง work roles
เพราะ family นี้ไม่ส่ง file descriptors เข้า process ที่รันอยู่ด้วย mechanism ใหม่
E ส่งเฉพาะ handles ที่ role นั้นต้องใช้ผ่าน fixed inheritance/closure map

- R/O ไม่มี helper output write ends, native helper executable/DB handles หรือ stop authority
- S รับ actual helper stdout/stderr read ends และ fixed request write end เท่านั้น
  ไม่มี helper PID/pidfd เพื่อ signal/reap; ไม่มี native API/constructor fallback
- H รับ stdin/stdout/stderr จริง, fixed helper executable/readonly DB/root handles ตาม scope เดิม
- E retain child pidfds และ cleanup stream read copies; ปิด unused write ends ตาม stage
  ไม่อ่านแย่ง S ใน normal path; terminal drain เริ่มหลัง S stopped/stream ownership ปิดแล้ว
- B ไม่ถือ accidental helper/report write ends; E ใช้ exclusive source-bound role channels

E เก็บสิทธิ์เขียน first gate byte; O ส่งเพียง bounded start request หลัง R อนุมัติ
E revalidate current authority/context/deadline/role bindings แล้วส่ง G ครั้งเดียว
S มี request writer ที่ provision ไว้ก่อน fork แต่ต้องรอ E G acknowledgement จึงส่ง
context/job/context. H gate wrapper consume G ก่อน exec; C stdin EOF หลัง request สุดท้าย
ต้องมี exact writer-closure proof. ไม่ใช้ duplicated-writer timing assumption แทน handshake

R/O/S/H ต้องเป็น reviewed closed call graph ที่ไม่สร้าง descendants
source restrictions นี้ไม่ใช่ kernel isolation จาก hostile same-uid/compromised code
ถ้า threat model ต้องการ kernel-enforced no-fork/migration control ให้เสนอ capability
และหลักฐานเพิ่มก่อน implementation; เอกสารนี้ไม่เปิด sandbox/seccomp/cgroup operation

## 6. Reaper ownership และ proposed FINAL split

E เป็น reaper ตั้งแต่ birth จึงไม่ต้องรับ adoption/reap authority จาก R/S ที่ตาย
ก่อนทุก signal/reap ต้องพิสูจน์ exact direct child/retained identity/generation/current cleanup grant
No concurrent reaper, SIGCHLD auto-reap หรือ role thread ที่ consume wait status ลับหลัง E
R/S loss ไม่ทำให้ E signal backend worker/provider หรือ actors นอก roster

S ยังตรวจ native frames/oracle และส่ง **S_DATA_FINAL** ซึ่งยืนยัน data path เท่านั้น
E ตรวจ H exit=0/exact reap/actual helper stream EOF แล้วส่ง **E_H_CLOSED**
H-reaped evidence ห้ามให้ S อ้างว่าเป็นผู้ reap; ECHILD ไม่สร้าง receipt สำเร็จ
ชื่อสองชนิดนี้เป็น proposed private labels ไม่ใช่ schema/state ที่ implement แล้ว

| Evidence | พิสูจน์อะไร | ไม่พิสูจน์อะไร |
| --- | --- | --- |
| S_DATA_FINAL | Fixed context/job/context frames, bounded decode/oracle/data checks | H exit/reap, full goal/current authority หรือ action approval |
| E_H_CLOSED | Exact helper lifecycle + required stream closure + cleanup generation/deadline | Original goal หรือ S_DATA_FINAL ที่หายไป |
| R sealed verification record | Existing independent full-goal/current authority/context/head requirements เมื่อ implement join แล้ว | E/B termination ที่ยังไม่เกิด หรือ blanket all-actors-stopped |
| E_ATTEMPT_CLOSED to B | Exact per-role cleanup facts หลัง R/O/S/H จบ | Replacement missing R goal/S data final |
| B exact E reap | E termination ของ exact admitted child | Reconstruct work outcome จาก exit0 |

S_DATA_FINAL และ E_H_CLOSED ต้อง bind attempt/source/generation เดียวกัน
R/O/S ยัง alive ในบาง stage จึงห้ามให้ E_H_CLOSED หมายถึง all actors stopped
ลำดับ sealed record → normal R exit → E closure → B reap ต้องแก้ causal ordering
ใน joined receipt contract ก่อน merge; OA12 ยัง NOT RUN ไม่ถือว่าเอกสารนี้ implement แล้ว

Missing/duplicate/partial/trailing/stale data/lifecycle record => UNKNOWN/HOLD
E ห้ามสร้าง S_DATA_FINAL แทน และห้ามส่ง G/query/verifier ต่อเมื่อ active R ตาย
R loss ก่อน valid completion commit แม้ native exit0/prefix/data-final ครบ => UNKNOWN
Valid record ที่ commit/ปิด attempt ไปก่อนแล้วไม่ถูกย้อนแก้; normal exitต้องมี sealed proof
ไม่ใช้ R/E exit0 อย่างเดียวตีความ completion. authorizes_actions=false ตามเดิม

## 7. Bounded control protocol และ resource/time envelope

Concrete profile ต้องเสนอ strict closed message schemas ก่อน implementation review
proposed upper bounds: frame<=512 bytes, **รวมไม่เกิน24 control messages/attempt**
โดยรวม role bound/ready สูงสุด4+4, one G request/ack, data/helper/attempt closure,
sealed-record reference และ finite aborts; ไม่มี heartbeat/poll/retry/duplicate admission
เกิน count/size/type/key set => abort/HOLD ไม่ขยาย queue. Binding refs จาก trusted catalog
ไม่ส่ง raw PID/paths/config/credentials/native output ใน public record/control summary
Result/binding copyout ภายใน E ต้องมี finite per-slot storage และ private retention scope

T0 ก่อน E bootstrap; Ta lockedก่อน first R/O/S/H create; D=min(Ta+20,T0+45)
D_capture<=D−3; no fresh timer at R/S loss, create-result handoff หรือ reaping
Existing native alarm1s/stdout64KiB/stderr4KiB/control512 bounds คง requirement เดิม
E as sole parentอาจหยุด known remaining O/S/H concurrently ด้วย retained identities
TERM grace<=0.2s/KILL wait<=1s ภายใต้ shared absolute phase deadline
นี่เป็น proposed **ownership change** ไม่ใช่สิทธิ์ใช้ current R/S stop path แบบใหม่ทันที

แม้ proposed stop phase ใช้ allowed waits<=1.2s ก็ไม่เพิ่ม capture window/reserve ใหม่
ยังต้อง fit original3sรวม detection, result arbitration, per-role reap/drain/EOF,
E/B closure/metadata; ต้องวัดจริง ไม่ claim worst-case guarantee จาก phase arithmetic
Late loss/in-flight create/kernel I/O ที่ทำไม่ทัน => STOP_UNCONFIRMED ไม่เพิ่ม3/20/45s

5 actor address-space caps 256MiB×5 ไม่ใช่ approved1,280MiB aggregate RSS budget
B/controller/library/runtime/FD/thread/CPU/retention/startup overhead ยังต้องนับ
หากต้องเพิ่ม launcher actor หรือ manager worker ต้องประกาศก่อน feasibility ไม่ซ่อนใน E
E failure/host compromiseยังเป็น explicit external-boundary limit; no E2 watchdog chain
ไม่มี accepted E availability/lifecycle owner/profile => production HOLD ก่อน ARM/G

## 8. Change-control matrix — ทุกข้อยัง PROPOSED

| Delta | Existing accepted profile | Proposed alternative | ก่อน source integration/merge |
| --- | --- | --- | --- |
| Parentage | R→O/S; S→H | E→R/O/S/H | SPEC14 security/lifecycle amendment + exact role inventory |
| Launch grant | Fixed R/S launches หลัง fixture admission | E closed-roster creator, no R/S fork | Independent issuer/anchor + finite broker scope |
| Birth identity | S witnessผ่าน R | E-owned create result ไม่พึ่ง R relay | Actual primitive/result-interruption feasibility |
| Reaper | S primary, R adopted cleanup | E sole reaperตั้งแต่แรก | Exact wait/arbitration/no-auto-reap controls |
| Gate | R/O/S ACK/G chain | O request, E single G + S request acknowledgement | New private protocol review; existing guardไม่ปิด |
| FINAL | S native finalรวม lifecycle fields | S data + E per-H lifecycle, sealed R/B closure | Typed joined semantics + negative controls; no public-state rewrite |
| Implementation reuse | Native supervisor creates/reaps H | New data-only S; shared low-level functionsเท่าที่พิสูจน์ได้ | ห้าม wire existing NativeRun/Batch ให้แอบเปลี่ยน parentage |

ยังไม่แก้ SPEC.md หรือ runtime; การรับเอกสารนี้ไม่เท่ากับรับ amendment/implementation
No actual host/system service/cgroup/VM/key action ได้รับอนุญาตจาก package นี้

## 9. PB controls preregistration — ทุกแถว NOT RUN

PB IDs เป็น obligation IDs ของ alternative นี้ ไม่ใช่ OC/OA rows หรือ test counts

| ID / mapping | Required owned real stimulus / oracle | Acceptance หรือ HOLD |
| --- | --- | --- |
| PB01 / EC01,10 | Absent/forged/expired issuer/profile/anchor; duplicate role request/restart | No production launch/G; no slot reuse หรือ cross-process authorityจาก Python object |
| PB02 / EC02,03 | R SIGKILL ขณะ E create/bind H และ drop R relay ทุกจุด | E independent exact H binding/cleanup หรือ infeasible; diagnostic witnessใช้แทนไม่ได้ |
| PB03 / EC02,03 | Interrupted/ambiguous E create result, failed pidfd copyout/open/FD exhaustion | Consume slot; no retry/scan/numeric signal; unknown childไม่กลายเป็น absent |
| PB04 / EC04,09 | R/S/O พยายาม forkเพิ่มหรือ arbitrary role/path/argv; wrong FD map/READY/G | Closed roster/path rejection ก่อน protected capture; unsupported enforcement HOLD |
| PB05 / EC04,05 | R lossก่อน/หลัง G ระหว่าง native query/read-lock/first/full frames/data-final | Stop/close exact actors; observation UNKNOWN ไม่มี replacement FINAL |
| PB06 / EC06 | H exitsก่อน binding, S loss, concurrent reap attempt, SIGCHLD auto-reap | E exact reaper only; no double signal/wait; missing proof HOLD |
| PB07 / EC07 | Retained writer/full report/stalled request consumer ระหว่าง broker cleanup | No blocked stop path; actual reap/EOF/closureแยกและ bounded |
| PB08 / EC05,12 | Missing/malformed/replayed S_DATA_FINAL/E_H_CLOSED/sealed-record ordering | Same attempt/source join only; no prefix/exit0/cleanup⇒goal inference |
| PB09 / EC08,10 | Revoke/expiry/R lossขณะ pending role/G; rollback/resetสร้างEใหม่ | No new work; pre-granted finite cleanup only; independent anchor required |
| PB10 / EC08,11 | E/B death, late cutoff, kernel I/O/resource/retention failure | Explicit unconfirmed/infeasible; no fresh time/actor/diagnostic capability |
| PB11 / EC11,12 | Five actors+B actual costs, source/FD closure และ record privacy | Exact resource account; no hidden actor/raw private data; full budgets preserved |

ของเดิม source probes12/native53 และ CI เป็น input/regressionเท่านั้น ไม่ทำ PB rows PASS
Concrete kernel/runtime/birth primitive/private profile ยัง UNBOUND; ไม่เรียกจริงเพื่อเติมตาราง

## 10. Evidence record และ next delivery boundary

| Field | Current record |
| --- | --- |
| ID/status/scope | OA07 NOT RUN full obligation / B4 OPEN; alternative contract only |
| Requirement | EC launch-gap/reaper obligations + round15 live counterexample |
| Source SHA/path | Exact documentation commit; source/runtime/manifest unchanged |
| Task/control/stimulus | PB01–PB11 preregistration only; NOT RUN |
| Expected | E identity independent of R relay, exact sole reaper, unchanged denial/goal rules |
| Actual | Design proposal only; no primitive/enforcement profile implemented or selected |
| Environment/dependencies | Abstract Linux candidate; actual kernel/runtime/library/headroom UNBOUND |
| Private evidence locator | UNBOUND; no original Dev/private binding read |
| Privacy-safe summary | Role/slot/protocol requirements and finite bounds; no actual IDs/paths/keys |
| Independent review | Parent round15 operator-supplied feasibility APPROVE; alternative design PENDING |
| Unresolved limits | E create-result uncertainty, authority/rollback/E availability, closed-call graph, causal receipt/B6/OA12 |
| Handoff | Review boundary + SPEC14 scope ก่อน finite owned-offline primitive feasibility |

หลัง design review จึงเสนอ finite offline birth-primitive feasibility package ที่พิสูจน์
PB02/PB03 โดยไม่เปลี่ยน source guardหรือขอ host capabilityจริงแบบเงียบ
หาก proof ไม่พอให้ alternative infeasible/HOLD ไม่ promote pre-reserved ledgerเป็นcontainment
PR117 draft/unmerged; B1–B7 OPEN; OA06/OA08 PARTIAL; OA07/OA12 NOT RUN
J0 PAUSED (#112 e7142cf7); OC18 NOT RUN; R1 NOT AUTHORIZED / R2 HOLD
ไม่มี Dev/pilot/backend/model/API/credential/config/checkpoint/archive/release/deployment
