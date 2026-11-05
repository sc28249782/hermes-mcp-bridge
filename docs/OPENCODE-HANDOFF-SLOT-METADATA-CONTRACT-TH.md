# Slot metadata commit/restore — proposed same-E contract

วันที่: 5 พฤศจิกายน 2026 (Asia/Bangkok)
Input: PR117 `355d13b0d21754e90709492dd8424d231e19a2c7`
สถานะ: **PROPOSED DESIGN / NOT IMPLEMENTED / NO CAPABILITY GRANTED**

## 1. Checkpoint และขอบเขต

Round-19 APPROVE ณ input head เป็น operator-supplied review ของ no-children
scope note ไม่ใช่ GitHub review submission; ไม่มี review timestamp จึงไม่เติมเอง
[Atomic birth evidence](OPENCODE-HANDOFF-ATOMIC-BIRTH-REVIEW-TH.md) ยังคงเป็น
feasibility evidence: PB02/PB03 PARTIAL ไม่ใช่ full atomicity หรือ production pass
[Pre-enrolled broker](OPENCODE-HANDOFF-PREENROLLED-BROKER-CONTRACT-TH.md)
ยังเป็น alternative design; runtime topology/grants เดิมไม่ถูกแทนที่

รอบนี้เสนอ bounded metadata protocol และ preregister controls เท่านั้น
ไม่มี source/test/workflow/manifest/SPEC edit, syscall experiment หรือ host inspection
ไม่มีการนำ diagnostic duplicate จาก erase/close controls มาเปลี่ยนชื่อเป็น production
ไม่มี profile selected, effective amendment หรือ permission เริ่ม protected capture

## 2. Capability cell กับ metadata view ต้องแยกกัน

Proposed E มี finite roster R/O/S/H ตาม contract เดิม ไม่มี process/role เพิ่ม
ก่อน create แต่ละ role ให้เตรียม fixed capability cell และ metadata view ภายใน E
ชื่อสองส่วนนี้เป็น design labels ไม่ใช่ class/schema/runtime interface ที่มีแล้ว

| ส่วน | สิ่งที่ถือ / อ้างได้ | สิ่งที่ห้ามอนุมาน |
| --- | --- | --- |
| Capability cell | Exact retained pidfd จาก reviewed birth result, role/attempt/generation/source/FD-map references และ original deadlines | Slot reservation หรือ checksum ไม่ได้พิสูจน์ live child identity |
| Metadata view | State/version/reference ไปยัง cell; readiness/closure observations ที่มีหลักฐาน | ไม่มีสิทธิ์ signal/reap/launch/G ในตัวเอง |
| Commit marker | Publication ว่า binding validation ครบตาม finite protocol | Atomic memory store ไม่ใช่ atomic kernel-create+ledger transaction |
| Terminal tombstone | Slot consumed และ monotonic closure facts ใน same E lifetime | ไม่ใช่ durable single-use authority หรือ B3 rollback protection |
| Audit record | Privacy-safe expected/actual outcome และ evidence references | Serialized FD/PID/record ไม่ใช่ retained capability หรือ reap receipt |

มีเพียง **หนึ่ง owned pidfd ต่อ child** ใน candidate นี้ ไม่เสนอ duplicate rescue
capability cell คือ owner เดิมของ handle ไม่ใช่ guardian/observer ใหม่
metadata view อ้าง cell ผ่าน fixed slot reference; ห้ามเก็บอีก handle เป็น shadow backup
ไม่มี dynamic target lookup, pidfd_open, FD passing, /proc scan หรือ numeric PID/PGID signal
เก็บ cell/metadata ใน bounded preallocated storage; actual layout/bytes ยัง UNBOUND
หาก implementation ต้องมี duplicate/actor/persistence/capability เพิ่ม ต้องเสนอใหม่ก่อน

Cell กับ view อยู่ใน address space เดียวกัน จึง **ไม่ใช่ kernel isolation**
การแยกชื่อ/struct ไม่ป้องกัน arbitrary memory corruption หรือ compromised E
fault ที่ทำลาย cell/handle/ownership proof ยังเป็น residual blocker ไม่ถูกตัดจาก
production requirement เพื่อให้ candidate ผ่าน; same-E metadata-loss subset เท่านั้น
ที่เสนอให้ศึกษาใน package ถัดไป

## 3. Binding publication และ monotonic slot lifecycle

Existing eight-stage role lifecycle ยังเป็น baseline obligation ของ broker
overlay ต่อไปนี้แยก binding publication จาก lifecycle ไม่แทน public terminal state

| Binding overlay | Required invariant | Failure disposition |
| --- | --- | --- |
| UNATTEMPTED | Preallocated role/cell; no create started | ไม่มี identity claim |
| CREATING | One create admitted; slot consumed before side effect; fixed copyout destination | Ambiguous result ห้าม retry/reuse/declare absent |
| BOUND_UNPUBLISHED | Retained exact-child handle and provenance validated; G closed | Cleanup-only หาก grant/identity ยังพิสูจน์ได้; otherwise HOLD |
| COMMITTED | One bounded publication after all required fields validate | Commit ไม่สร้าง READY/G/goal authority |
| VIEW_INVALID | Metadata view missing/stale/mismatched; cell may or may not remain valid | Freeze further launch/G; evaluate bounded same-E eligibility |
| TERMINAL | Exact closure facts + consumed tombstone, or explicit unconfirmed termination | No reopening, replacement child, replay or state downgrade |

Proposed order: reserve/consume → one reviewed birth operation → retain exact result
→ validate child ownership/role/source/FD-map/deadlines → publish binding once
no fallible caller callback, asynchronous exception escape or allocation in this path
เป็น implementation proof obligations ไม่ใช่สิ่งที่ source ปัจจุบันรับประกันแล้ว
nonthrowing post-return signal control เดิมไม่พิสูจน์ mid-syscall หรือ mid-commit safety

Fault ก่อน/ระหว่าง publication ห้ามอ้าง commit จาก marker เพียง field เดียว
validator ต้องอ่าน coherent complete tuple และ current cleanup grant ก่อนทุก target action
unknown create/commit consumes slot แม้ไม่เคย publish; no new create after R loss
การ publish ไม่เพิ่ม cleanup/capture deadline และไม่ลบ revocation/terminal facts

## 4. Same-E restore eligibility — metadata เท่านั้น

คำว่า restore ใน proposal หมายถึง **rebuild view จาก retained cell เดิม**
ไม่ใช่ reopen/reacquire pidfd, resurrect role, rewind attempt หรือ replay saved state

ต้องครบทุกข้อก่อน bounded rebuild หนึ่งครั้งต่อ role ต่อ attempt:
1. E ยังเป็น exact admitted live creator ใน lifetime เดิม; no exec/restart/fork copy
2. Cell ยัง intact และ handle ยัง owned/open; identity/provenance/ownership/current
   cleanup grant ต้องตรวจจาก accepted source path ไม่ใช่ caller-supplied boolean
3. Attempt/generation/source/role/FD-map/original deadlines ตรงกันครบ ไม่มี extra field
4. Slot consumed แล้ว; terminal/revocation/wait-consumed facts ไม่ถูกลบหรือย้อนกลับ
5. No concurrent writer/reaper; protocol serializes validation/publication/action
6. Remaining original budget เพียงพอ; no new timer, retry loop หรือ restore recursion

Rebuild view หนึ่งครั้งเป็น proposed bounded recovery operation ที่ต้องผ่าน SPEC14
ไม่ใช่ข้อยกเว้น retry ที่ effective แล้ว; birth operation ยังคงครั้งเดียว
หาก coherent cell/grant proof ไม่ครบ ให้หยุดที่ UNKNOWN/HOLD หรือ STOP_UNCONFIRMED
ตาม existing observation/lifecycle semantics ไม่เดาว่า child absent หรือ stopped

แม้ rebuild สำเร็จให้ **cleanup-only** ใน candidate นี้; G/further launch คงปิด
ห้ามเปลี่ยน UNKNOWN เป็น Done/FAIL หรือสร้าง S_DATA_FINAL/E_H_CLOSED/sealed goal แทน
restore ไม่เพิ่มสิทธิ์ E และไม่ขยาย finite launch-time cleanup grant
Exact stop, wait consumption และ per-stream EOF ต้องมีหลักฐานแยกตาม contract
No new public status value หรือ FINAL schema ถูกกำหนดจาก private overlay labels

## 5. Handle loss, rollback และ creator loss

| Fault | Proposed admissible result | สิ่งที่ยังห้าม |
| --- | --- | --- |
| View erased แต่ cell/proof intact | One bounded same-E rebuild, cleanup-only | No G/relaunch/goal upgrade |
| Partial commit marker / mixed version | Reject publication; cleanup only with intact validated cell/grant | No marker-only acceptance |
| Cell erased/corrupted | UNKNOWN/HOLD; no reconstructed target | No scan, guessed FD, diagnostic rescue |
| Retained handle closed | Binding lost/unconfirmed even if same FD number later opens | No FD-number equality as identity, no pidfd reacquisition |
| Stale record/generation/source/tombstone | Reject; retain consumed/revoked state | No rewind/recycle or cross-attempt repair |
| SIGCHLD policy/concurrent reaper invalid | Reject admission/action; missing reap evidence unconfirmed | ECHILD alone is not exact reap |
| E dies before/after copyout/commit | No trusted E completion; external containment UNBOUND | B exact-E reap is not R/O/S/H census |
| B dies / E authority expires | No new work; only previously finite cleanup if still valid | No new grant minted by restore |
| Budget exhausted/kernel I/O unresponsive | STOP_UNCONFIRMED/HOLD | No fresh 3/20/45 s or watchdog chain |

Memory/local journal/checksum/hash/current-source hash ไม่ใช่ external rollback anchor
cross-process restart/cross-E restore และ persisted handle restoration **out of this
candidate's implemented capability** (ยังไม่มี implementation ใด) และยังเป็น production
obligations ที่เปิดอยู่ ไม่ใช่ waived requirements. B1/B3 authority/rollback proof
ต้องมาจาก independently accepted resolver/anchor ก่อน promote
No persisted marker/nonce/time ที่ rollback ไปด้วยกันใช้ปิด B3

`no_children=true` scope ตาม round19 คงเดิม: isolated E's own waitable children
at the oracle point after separately recorded diagnostic cleanup. B waits/reaps E
เท่านั้น ไม่ใช่ host-wide no-orphans proof หรือ E-loss containment
same-E view recovery ไม่เปลี่ยนขอบเขตนี้

## 6. Time/resource/privacy envelope

T0 ก่อน E, Ta ก่อน first work-role create; D=min(Ta+20,T0+45), capture cutoff≤D−3
Any stricter feasibility bound8s ต้องเป็น subset เดิม ไม่ใช้8sใหม่ที่ restore
Binding validation/rebuild/cleanup/drain/reap/E+B closure รวมใน original D/reserve
TERM≤0.2s/KILL≤1s shared phase deadlines เดิมไม่เพิ่มเวลาให้ metadata repair
Native alarm1s/stdout64KiB/stderr4KiB/control512bytes/24messages requirements คงเดิม
Restore ภายใน E ไม่มี protocol message/actor ใหม่ที่ถูกอนุญาตจากเอกสารนี้
หากต้องเพิ่ม traffic/storage/FD ให้แจกแจงและ review ก่อน ไม่ซ่อนใน existing caps

Five proposed work actors E/R/O/S/H plus B; 256MiB/actor caps ไม่ใช่ aggregate RSS
Cell/view/tombstone sizes, FD counts, stack/heap/RSS/CPU and B overhead ยัง UNBOUND
ต้องวัด exact call-site limits ใน B6/PB11 ก่อน production feasibility claim
No raw PID/FD/path/private prompt/output/config/credential ใน public records
Source/issuer/anchor refs ต้องมี independently approved private retention scope

## 7. SM01–SM12 preregistration — ทุกแถว NOT RUN

SM เป็น local obligation IDs ไม่ใช่ PB/OA rows, test count หรือ acceptance substitute

| ID / mapping | Required stimulus / independent oracle | Acceptance-or-HOLD |
| --- | --- | --- |
| SM01 / PB01,03 | Wrong role/attempt/generation/source, duplicate admission | No extra create, consumed slot not recycled |
| SM02 / PB02,03 | Erase only view after actual retained birth binding | Same intact cell target; bounded cleanup-only, no G |
| SM03 / PB03 | Fault before/inside/after publication, mixed tuple/marker | No incomplete binding accepted; unknown consumes slot |
| SM04 / PB03,06 | Close actual pidfd then reuse numeric FD for unrelated owned fixture resource | Never signal/reap reused FD; binding remains unconfirmed |
| SM05 / PB03,10 | Erase/corrupt cell plus view; dropped kernel result | No target reconstruction/fallback; diagnostic separate/frozen if used |
| SM06 / PB02,05,09 | R loss/revoke during view validation or rebuild | No new launch/G; only valid pre-granted exact cleanup |
| SM07 / PB06 | H early exit, auto-reap policy, concurrent wait attempt | WNOWAIT/consume proof distinct; no double reap or signal |
| SM08 / PB09 | Stale/rolled-back view/tombstone/source; E restart/fork copy | No current authority from copied state; no B3 closure |
| SM09 / PB10 | Actual E death pre/post copyout, publication and rebuild | UNKNOWN/external containment HOLD; B reap not orphan proof |
| SM10 / PB07,10 | Late cutoff, retained writer/full pipes, resource/I/O failure | Original D preserved; missing EOF/reap unconfirmed |
| SM11 / PB04,11 | Fixed roster/FD-map audit, finite cells, resource/privacy accounting | No duplicate rescue/hidden actor/arbitrary targets |
| SM12 / PB08, OA12 | Restore+cleanup with absent/stale/malformed data/goal FINAL | No synthesized FINAL/goal/Done; full join remains NOT RUN |

Controls ต้องแยก expected vs actual, supported vs unsupported, candidate vs test-only
diagnostic, same-E vs creator-death cases และ stop/reap/EOF/goal facts
No row PASS จน stimulus+oracle+source/runtime bindings และ independent reviewครบ
Current atomic16/birth16/other CI counts เป็น prior input/regression เท่านั้น
SM01–SM12 ทุกแถว **NOT RUN**; PB02/PB03 ยัง PARTIAL; PB01/04–11 NOT RUN

## 8. Change control และ next delivery

[docs/SPEC §14](SPEC.md#14-change-control) ต้อง review/update ก่อน merge implementation
security-boundary/persistence/status/context changes. ตารางนี้ยังเป็น proposal:

| Proposed delta | Required before integration |
| --- | --- |
| Cell/view ownership and publication ordering | Exact layout/call graph, source-to-launch binding, single-owner/reaper proof |
| Bounded same-E view rebuild | Scope of invalidation and finite cleanup grant; one-shot semantics and fault controls |
| Terminal/tombstone validation | Monotonic consume/revoke rules; no persistence/B3 assumption |
| E/B loss handling | Accepted external profile or explicit production infeasible/HOLD |
| Evidence join | Existing S data/E lifecycle/R goal/B closure causal contract; OA12 evidence |

No SPEC amendment becomes effective here; old runtime/source guards remain unchanged
Next deliverable หลัง design review: owned offline cell/view primitive subset with
SM02–SM05 stimuli, fixed targets, no G, no external authority/profile claims
หาก handle validity/FD reuse/commit interruption proof ทำไม่ได้ใน original budget
ให้รายงาน infeasible/HOLD ไม่ promote redundancy/checksum เป็น containment

Evidence record: requirement=PB02/PB03 metadata gap; expected=bounded same-E view
repair only with retained capability; actual=design only; SM=NOT RUN; environment/
implementation/private locator=UNBOUND; independent review of this candidate=PENDING
Parent round19 review is operator-supplied; no new local runtime/production evidence
PR117 draft/unmerged; B1–B7 OPEN; B4 OPEN; OA07/OA12 NOT RUN; J0 PAUSED
(#112 e7142cf7); OC18 NOT RUN; R1 NOT AUTHORIZED / R2 HOLD
No Dev/pilot/backend/model/API/credential/config/checkpoint/archive/release/deployment
