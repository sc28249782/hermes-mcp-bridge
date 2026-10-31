# S24 — ภาพรวมการส่งมอบและเกณฑ์จบงาน

## Latest J0 result — attempt four

ผล [attempt ครั้งที่ 4](../acceptance/s24/observed/CATALOG-ATTEMPT-FOUR.md)
ที่ operator อนุมัติ: activation `2ee4167d` / run `41213711915` / job `124573771376`
จบ **HOLD / gate exit 2 / job FAILURE** แม้ digest ตรง provider pin แล้ว
stage/error/reason = ARCHIVE_PARSE/PREDICATE_REJECTED/BACKSLASH; counts เป็น
partial และยังไม่มี completed catalog receipt ไม่อนุมานชื่อ member/path หรือเหตุอื่น

สถานะปัจจุบัน: consumed **4 ครั้ง**, digest match ที่มีหลักฐาน **3 ครั้ง**
(E14/E17/ครั้งที่ 4); E12 ยัง UNKNOWN ปิด catalog guard กลับใน record commit นี้
ไม่มี retry ครั้งที่ 5 หรือการผ่อน predicate ได้รับอนุมัติ ข้อความ 3/2 และ scope
ก่อนหน้าด้านล่างเป็นประวัติที่ named heads ของตน A2/A3 prerequisite ยังไม่ปิด
ทั้ง 18 แถวยัง OPEN · คง draft · J0 NOT READY · R1 NOT AUTHORIZED · R2 HOLD.

## Selected source-work scope

หลังอนุมัติภาพรวม/closure ledger และ E18 design แล้ว operator เลือก `1`:
เดิน CI route เดิมต่อเฉพาะ producer/gate/controls สำหรับ metadata catalog
เพื่อส่ง exact-source review ใน PR #112 เดิม รายละเอียดและ SHA อยู่ใน
[source candidate](../acceptance/s24/observed/CATALOG-SOURCE-REVIEW.md).
นี่คือ J0 prerequisite ของ A2/A3 ไม่ใช่การปิด joined-path หรือ source acceptance
ทั้งแพ็กเกจ พักการเพิ่มเลข E ต่อไป; ข้อความ pause ด้านล่างเป็นสถานะก่อนเลือกนี้
ไม่มี attempt ครั้งที่สี่/provisioning/merge ได้รับอนุมัติจากการเลือก source work นี้
A1–A7 ยัง incomplete · J0 NOT READY · R1 NOT AUTHORIZED · R2 HOLD.

## Current milestone status

วันที่: **31 ตุลาคม 2026 (Asia/Bangkok)** · ฐาน main `93e9601` · หลักฐานจาก
PR [#112](https://github.com/sc28249782/hermes-mcp-bridge/pull/112) ที่ `c5c2ea66`
ก่อน checkpoint เอกสารนี้ สถานะ **PRE-R1 / SOURCE ACCEPTANCE INCOMPLETE**.

Operator เห็นด้วยให้ **พักการเพิ่ม E ย่อยและ implementation รอบใหม่** แล้วปรับ
ภาพรวม/closure ledger ก่อน การตัดสินใจนี้ไม่อนุมัติ implementation E18, request
ครั้งที่สี่, operator probe, R1/R2, merge, release หรือ deployment ส่วน CI เดิม
ยังตรวจ regression ของเอกสารได้ตามเดิม ไม่มี live artifact action เปิดขึ้น

### แผนส่งมอบที่ใช้ติดตามต่อจากนี้

| Milestone | หลักฐาน/สถานะปัจจุบัน | สิ่งที่ยังต้องปิด |
| --- | --- | --- |
| A1 controls/dispositions | มี ledger ครบ 18 แถว; หลักฐานหลาย component ผ่าน review | disposition ของทุกแถวต่อ exact package ยังเปิด; ไม่มีแถวปิดจาก CI หรือ design approval โดยอัตโนมัติ |
| A2 joined observation | มี real collect/local sample (E4), real Linux SSH (E6), Windows entry/ACL/CIM (E7) | native Windows SSH → guest wrapper/collect → Windows CIM ใน invocation เดียว พร้อม negative window/worker-exit/post paths ยังไม่ครบ |
| A3 transport/failure/stop | E3/E5–E7 ให้ ACL/CIM/coordinator/provider/transport/log evidence ตาม fixture boundaries | combined path, blocked output/start/provider, owner loss, independent deadline/confirmed stop และ writer coverage ยังต้อง bind/prove/review |
| A4 identity/regression | baseline regressions, real adoption และ real exec/UID/PID reuse primitive controls (E8) มีหลักฐาน | disposition ใน full wrapper/joined package และรักษา regression/false-flag contract ไม่ใช่เริ่ม primitive work ใหม่ทั้งหมด |
| A5 exact source package | candidate hashes/pins และ supported CI suites มีผลผ่านที่ named heads | package รวมทุกข้อ/ขอบเขต substitutions/ข้อจำกัดและ source-acceptance review ยังไม่ complete; tests count ไม่ใช่ release readiness |
| A6 private bindings | nominations/ข้อเท็จจริงบางส่วนอยู่ใน private packet | bindings ส่วน 4 ยังไม่ครบ; ไม่ infer operator machine/authority/writer/stop จาก CI และไม่ probe เพิ่มโดยปริยาย |
| A7 source acceptance | design/component/source deltas หลายรอบได้รับ review | independent review ของ package + 18 dispositions + private bindings แล้ว operator จึงพิจารณา finite R1 scope |
| B1–B4 acquisition/metadata | R1 NOT AUTHORIZED; R2 HOLD | finite R1, metadata preparation, finite R2 และ independent outcome review ตามเกณฑ์ §3 ด้านล่าง |
| C1–C3 operational acceptance | ยังไม่พร้อม actual operational Phase B/closure | readiness + finite connector-route run + acceptance §22 ตามเกณฑ์ §4; R2 metadata ไม่แทนขั้นนี้ |
| C4–C5 release | ยังไม่กำหนด release scope/version/date ใหม่ | scope decision → candidate/docs/validation → signed tag/assets/checksum/download verification/record ตาม runbook |
| C6 deployment | deployment record ล่าสุดเป็น signed v1.2.8 วันที่ 22 ต.ค. | deploy/not-deploy เป็นการตัดสินใจแยกของ release ใหม่; ไม่ได้ตรวจ production สดใน checkpoint นี้ |

รายละเอียด 18 แถวฉบับปัจจุบัน: [current closure ledger](../acceptance/s24/observed/R1-INTEGRATION.md#current-closure-ledger).
เกณฑ์ A/B/C ใน sections 2–4 ด้านล่างยังใช้ครบ; dated status statements ใน snapshot
30 ต.ค. เป็นประวัติที่ checkpoint นี้ supersede เฉพาะสถานะ ไม่ลด obligation

### ตำแหน่งของ J0 และการนับหลักฐาน

J0 เป็น prerequisite ของเส้นทาง disposable Windows/Linux CI ที่เลือกมาทดสอบ
joined observer ใน A2/A3 ไม่ใช่ release milestone แยกหรือการรัน operator inventory
E4/E6/E7 เป็นคนละ run/คนละ fixture boundary; ห้ามประกอบ receipts แล้วอ้าง joined PASS

| J0 fact | ผลที่พิสูจน์ได้ |
| --- | --- |
| live archive invocations | 3 ครั้งที่อนุมัติและ consumed: E12, E14, E17 |
| full-archive digest equality | **2 ครั้งเท่านั้น: E14/E17**, 388,975,696 bytes, bb415d82… ตรง provider pin; E12 ยัง UNKNOWN |
| full inspection/catalog/selected binary hashes | ยังไม่มี completed receipt; E17 HOLD ที่ TYPE_REJECTED; parsed_members=5 ไม่ระบุ raw member ที่ 6/path/subtype |
| kernel/boot/guest/ports/lifecycle | ยังไม่ครบ/UNBOUND; snapshots ของไฟล์และ feature ไม่ใช่ route/boot/stop proof |
| E18 | metadata-catalog design PROPOSAL เท่านั้น; ยังไม่ implement และพักไว้รอ milestone/route decision |

E1–E18 ใน PR เป็น evidence/checkpoints ไม่ใช่ phases ไปสู่ release และไม่มีเลข E
สุดท้ายที่ใช้เป็น completion target ภาคผนวก F/G ใน private binding packet เป็น
บันทึก environment/source review และ publication/CI ที่มีแล้ว ไม่ใช่สอง phase
ท้ายที่เหลือก่อน final release อย่าปะปนกับ A1–A7 ใน delivery criteria นี้

### การตัดสินใจก่อนกลับไป implementation

1. Review ภาพรวม/18-row ledger นี้และยืนยัน blocker/disposition ที่ต้องการ ยังไม่มี
   row waiver หรือ source-acceptance PASS จากการอัปเดตเอกสาร
2. เลือกว่าจะเดินต่อบน CI route ปัจจุบัน, เสนอ environment/route อื่นให้ review,
   หรือ defer acceptance track โดยคง HOLD การเลือก route ใหม่ไม่ยกเว้นเกณฑ์เดิม
   E18 เป็น proposal หนึ่งของ prerequisite นี้; catalog สำเร็จอย่างเดียวไม่ปิด J0
3. ถ้าจะเดินต่อ ให้ bind งาน source/control แต่ละชิ้นกับแถวที่ยังเปิดและส่งเป็น
   joined package บน #112 เดิม โดยมี exact source/input/actor/budget/stop evidence
   อ้าง provenance และ substitutions ชัดเจน ไม่เพิ่มงานตาม test count หรือ E counter
4. ปิด A1–A5 และ A6/A7 ด้วย review ตามเดิมก่อนเสนอ finite R1; แยก authorization
   ของ setup/provisioning/แต่ละ live request ไม่ใช้ approval ของ design แทน action

Exit ของชุดก่อน R1 คือ **A1–A7 ผ่าน review และพร้อมเสนอ finite R1 scope**;
exit ของ source/integration PR ต้องมี disposition ชัดต่อ obligation ทั้ง 18 แถว
หรือ explicit approved disposition ตาม §14 เมื่อเกี่ยวข้อง ไม่มีข้อใดกลายเป็น
optional ผ่านการจัดตารางใหม่ หลังนั้นยังมี B/C ไม่ใช่เริ่ม tag/releaseทันที

Final release ใหม่อยู่ที่ C5 หลังเลือก scope/version และผ่าน acceptance/release
กฎเดิม Release ปัจจุบันยัง v1.2.8; Local Hands v1.3.0 ยัง deferred ที่ terminal-
status/subscription gate แยกต่างหาก S24 completion ไม่ปลด gate นั้นหรือส่งมอบ
Windows Host Adapter v1.4.0 / Computer Use v1.5.0 โดยอัตโนมัติ

รายงานรอบถัดไปต้องระบุ milestone/row ที่เปลี่ยน, evidence ก่อน/หลัง, blockers ที่
เหลือ, exact head และ scope ที่ได้รับอนุมัติ ไม่ใช้จำนวน PR/E/tests เป็นเปอร์เซ็นต์
ความพร้อม Current status: **J0 NOT READY · R1 NOT AUTHORIZED · R2 HOLD**;
#80/#96/Phase B/release/deployment คงเดิม

## Dated status snapshot — 30 October 2026

ข้อความสถานะด้านล่างคงไว้เป็นประวัติ ณ วันนั้น โดยเกณฑ์ A/B/C ยังใช้ตามที่ระบุ

วันที่ตรวจสถานะ: 30 ตุลาคม 2026 (Asia/Bangkok)
ฐานที่ตรวจ: main `d839b74eeaa4460aa7e14ca9b8012f3f4bb73d09`
สถานะ: **SOURCE/INTEGRATION IN PROGRESS — R1 NOT AUTHORIZED / R2 HOLD**

เอกสารนี้จัดลำดับและรวมงานเดิม ไม่แก้ SPEC ไม่ลด acceptance gate ไม่อนุมัติ
VM/host/API/plugin action และไม่กำหนดเลขรุ่นหรือวัน release ใหม่
เมื่อขัดกับ SPEC หรือ approved design ให้ HOLD และ review ตาม §14 ก่อนใช้
ประวัติในเอกสารเดิมยังคงอยู่; checkpoint นี้แยกสถานะปัจจุบันจากข้อความในอดีต

## 1. เป้าหมายและตำแหน่งปัจจุบัน

Release ล่าสุดคือ v1.2.8 (22 ตุลาคม 2026); deployment record ล่าสุดระบุ production
อัปเกรดเป็น signed v1.2.8 เมื่อ 22 ตุลาคม 2026 โดย signed v1.2.7 เป็น rollback baseline รุ่นเก่า
ตาม [deployment record](V1.2.8-DEPLOYMENT-TH.md) การเผยแพร่กับ deployment เป็นคนละการตัดสินใจ
checkpoint นี้ไม่ได้ตรวจ production สด
งาน S24 ปัจจุบันสร้าง source/control/evidence สำหรับ acceptance
ยังไม่เพิ่ม Local Hands write/exec และไม่ใช่ release candidate ใหม่

| งาน | สถานะ ณ checkpoint |
| --- | --- |
| #106 inventory controller | merged; baseline source และประวัติผลเดิมคงอยู่ |
| #107 observed candidate + Linux/Windows CI | merged `be88eef8`; 34/34 บน Linux 3.12/3.14 และ Windows 14+9 |
| #108 wrapper pipe rejection controls | merged `b6c07de8`; 37/37; controller/identity admission เป็น fixtures |
| #109 retained pidfd / identity revalidation | merged `d839b74e`; 40/40; exit จริง แต่ UID/argv drift เป็น injected reads |
| #110 local host handshake | draft/unmerged ที่ `f2dae6010ef03a6d9fc3eb9efaca51bfca20b0a7`; 43/43 และ Windows 14+9 เป็น CI evidence; รอ review ไม่ใช่ baseline ที่ merge แล้ว |

จำนวน tests บอก coverage ของ suite นั้น ไม่ใช่เปอร์เซ็นต์ความพร้อม release
CI/reviewer/operator evidence ต้องแยก attribution เสมอ ไม่ใช่ผลบน operator VM
ผล #110 เป็น local pipe handshake ที่ใช้ controller/identity fixtures ไม่มี memory sample
และไม่พิสูจน์ during-inventory observation จริง
ดู [coverage matrix](../acceptance/s24/observed/CONTROL-MATRIX.md)

## 2. ชุดส่งมอบ A — source acceptance และ bindings ก่อนขอ R1 inventory

**เป้าหมาย:** ได้ exact source package และ private invocation/control packet
ที่ reviewer ตรวจแล้ว พร้อมเสนอ finite R1 scope ได้ ไม่ใช่การรัน R1

| เกณฑ์จบ | หลักฐานที่ต้องส่ง / สถานะ |
| --- | --- |
| A1. ปิดรายการ controls ของ R1 | ทุกแถวใน observed CONTROL-MATRIX ต้องมี exact source/test/evidence reference, provenance และ disposition สำหรับ R1; แถวที่ยังบังคับตาม approved design แต่ไม่มีหลักฐานเป็น blocker |
| A2. Integration ที่ไม่ใช้ fixture แทน predicate ที่กำลังพิสูจน์ | พิสูจน์ worker/collect boundary, wrapper pre/drain/post, host sample association และ before/during/after ตาม approved contract; รวม worker จบเร็ว/ตาย, leaving ค้างใน pipe, EOF/cancel และ failure latch; local handshake ที่ stub identity ไม่แทนหลักฐานนี้ |
| A3. Host/transport/failure policy | bind framing/channel และ Windows sampler/provider, source/config/output ACL, child stop/confirmation, deadline, blocked provider/output และ log/fsync failure; ทดสอบ failure paths ด้วย disposable fixtures ภายใต้ขอบเขตที่ได้รับอนุมัติ ไม่ใช้ operator VM แทน source controls |
| A4. Identity และ regression | คง mandatory adoption, retained identity/pidfd และ baseline/false-flag controls; UID transition/exec/PID reuse จริงที่ matrix ยังเปิดต้องมีหลักฐานหรือได้รับ explicit reviewer disposition ตามข้อกำหนดเดิมก่อน source acceptance ไม่ย้ายเป็น optional เอง |
| A5. Exact package | source hashes จริงครบ, loader pins ตรง, supported-interpreter suites และ Windows checks ผ่านที่ exact head; เปิดเผย mocks, skipped/unrun/environment failures และ scope limits; ไม่ลด predicate, skip หรือยืด timer เพื่อให้ผ่าน |
| A6. Private bindings | ส่วน 4 ของ private R1 packet ครบ: source/destination/interpreter/argv, machine/control/authority, observer/writer/output, transport/correlation, budgets และ stop method; ไม่มีค่าจริงใน public PR; UNKNOWN ที่ต้องอ่านเพิ่มต้องเสนอ read scope แยก ไม่เดาค่า |
| A7. Source acceptance review | reviewer ตรวจ package + matrix dispositions + private bindings; ไม่มี blocking finding; operator จึงพิจารณา finite R1 request ที่ระบุ action/จำนวน launch/timer/read-write/stop/preserve policy ชัดเจน |

A1–A5 รวมเป็น **หนึ่ง R1 observer integration work package** ต่อเนื่อง ไม่เปิด PR
ตามจำนวน tests ที่เพิ่ม ใช้ draft integration PR เดียวจนถึงเกณฑ์ส่งรีวิว
แยก PR เมื่อขอบเขตความเชื่อถือ/SPEC/authorization เปลี่ยนและจำเป็นต่อการ review
#110 ที่เปิดอยู่ให้จบรอบ review ก่อนเริ่ม source increment ถัดไป; เอกสารนี้ไม่สั่ง merge

การย้ายแถวเป็น later-stage หรือ supplemental ต้องมีเหตุผลอ้าง approved scope
และ explicit reviewer disposition; หากเป็น normative change ต้องผ่าน §14
ห้ามใช้การจัดตารางใหม่ปิด obligation หรืออ้าง source acceptance เอง
fast worker ที่ทำให้ HOLD ตามดีไซน์เป็นผลยอมรับได้ ไม่สร้าง delay/SIGSTOP/ACK-wait
ใน production worker เพื่อให้ได้ sample หรือ success

## 3. ชุดส่งมอบ B — finite acquisition และ metadata route

ขั้นนี้เริ่มได้เมื่อแต่ละ scope ได้รับอนุมัติแยก ไม่ใช่ผลอัตโนมัติจากชุด A

| ลำดับ | เกณฑ์จบ |
| --- | --- |
| B1. R1 acquisition | รันเฉพาะ finite scope ที่อนุมัติ เก็บ inventory/observations/receipt ตามจริง; ตรวจผลและ private bindings โดยอิสระ; ขาด evidence หรือหยุดไม่ยืนยัน = HOLD ไม่มี retry โดยปริยาย |
| B2. Metadata preparation | ปิด installed client/peer/source/env/auth/port, original-runtime continuity และ complete metadata cohort/observer/stop bindings ตาม staged plan; transfer approval เดิมสำหรับ baseline สองไฟล์ไม่ขยายมาชุด observed/wrapper เอง |
| B3. R2 metadata attempt | หลัง exact source/private review และ finite approval: หนึ่ง attempt ตามเดิม ไม่เกิน 120 s รวม stop/evidence; peer 30 s; initialization/ping/list เท่านั้น ไม่ tools/call; บันทึก actual new namespace/metadata route และ stop/continuity evidence |
| B4. Review outcome | independent review + operator acceptance ของขอบเขต metadata ที่สังเกตได้; ความล้มเหลวหรือ capability ไม่พร้อมคง HOLD ไม่ใช้ SDK/mock/existing namespace แทน |

[Staged plan](S24-METADATA-PREBIND-PLAN-TH.md) และ
[binding work package](S24-METADATA-BINDING-WORK-PACKAGE-TH.md) เป็นรายละเอียดเดิม
R2 metadata ไม่อนุมัติ active fixture และไม่ปิด Phase B หรือ scoped §22

## 4. ชุดส่งมอบ C — Phase B acceptance และ release decision

| Milestone | เกณฑ์จบ |
| --- | --- |
| C1. Operational Phase B readiness | actual connector adapter/route, host/guest/continuity collectors, protected evidence carrier และ outer supervision ครบ client/fixture/observer/descendant/external writers; exact stop/cessation และ private bindings ผ่าน review; Phase A readiness acceptance และ setup/activation prerequisites ครบ |
| C2. Finite Phase B run | แยก approval ก่อน activation; actual connector discovery 27-tool contract และ matrix 124 tool calls / 44 ordered checkpoints / audit 30 ตาม plan พร้อม resource/continuity/cohort/stop evidence; mock/local SDK ไม่แทน Work-route evidence |
| C3. Acceptance closure | independent evidence review และ explicit operator acceptance ก่อนปิด scoped §22; ไม่ประกาศ complete writer cessation จาก known leaders, EOF หรือ PID absence อย่างเดียว; #80 historical HOLD และ #96 แยก disposition ไม่ปิดโดยอนุมาน |
| C4. Release scope decision | ระบุสิ่งที่จะส่งจริง ข้อจำกัดและ deferrals เลขรุ่น และเลือก release/defer อย่างชัดเจน; ไม่อนุมานว่า S24 ผ่านแล้วเท่ากับ v1.3.0 พร้อม |
| C5. Release integrity | documentation/version/discovery/compatibility/upgrade gate + reviewed candidate validation; signed tag โดย operator; assets จาก signed tag, external checksum และ post-download verification; post-tag record/fresh audit ตามขอบเขตที่กำหนด |
| C6. Deployment | แยก deploy/not-deploy decision, scoped validation และ rollback; release ไม่ใช่ deployment |

รายละเอียด: [Phase B plan](S22-PHASE-B-ADAPTER-CONTROL-PLAN-TH.md),
[integration package](../acceptance/s24/INTEGRATION.md) และ
[release runbook](RELEASE-RUNBOOK-TH.md)
Phase A/B/C ของ release runbook เป็นคนละลำดับกับ Phase A/B ของ S24 acceptance

Local Hands v1.3.0 ยังติด terminal-status/subscription capability gate ตาม
[ROADMAP](ROADMAP.md#deferred--v130-approval-bound-mutation-and-execution)
ส่วน Windows Host Adapter v1.4.0 และ Computer Use v1.5.0 ไม่ได้ถูกส่งมอบด้วย
Windows observer ของ S24 ไม่กำหนดวัน final release จากจำนวน PR หรือจำนวน tests

## 5. วิธีรายงานความคืบหน้าตั้งแต่ checkpoint นี้

ทุก integration review ต้องสรุป: milestone ที่กำลังปิด, blockers ก่อน/หลัง,
หลักฐานที่เพิ่มพร้อม exact head, สิ่งที่ยังเป็น fixture/UNKNOWN และเกณฑ์ที่เหลือ
รายงานแยก source acceptance, operator execution, acceptance closure และ release
ไม่ใช้จำนวน merged PR หรือ suite count เป็น completion claim
หากพบ prerequisite ทำไม่ได้ ให้เสนอทางเลือก design/defer พร้อมผลกระทบเพื่อ review
ไม่เพิ่ม controls เสริมต่อเนื่องโดยไม่มี requirement ที่ผูกกับเกณฑ์จบ

Checkpoint นี้เปลี่ยนเฉพาะเอกสาร ไม่เพิ่ม controls ไม่เปิด runtime scope
R1 **PENDING_BINDINGS / NOT AUTHORIZED**; R2 **HOLD**; #80/#96 คงเดิม
