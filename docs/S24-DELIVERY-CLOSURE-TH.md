# S24 — ภาพรวมการส่งมอบและเกณฑ์จบงาน

วันที่ตรวจสถานะ: 30 ตุลาคม 2026 (Asia/Bangkok)
ฐานที่ตรวจ: main `d839b74eeaa4460aa7e14ca9b8012f3f4bb73d09`
สถานะ: **SOURCE/INTEGRATION IN PROGRESS — R1 NOT AUTHORIZED / R2 HOLD**

เอกสารนี้จัดลำดับและรวมงานเดิม ไม่แก้ SPEC ไม่ลด acceptance gate ไม่อนุมัติ
VM/host/API/plugin action และไม่กำหนดเลขรุ่นหรือวัน release ใหม่
เมื่อขัดกับ SPEC หรือ approved design ให้ HOLD และ review ตาม §14 ก่อนใช้
ประวัติในเอกสารเดิมยังคงอยู่; checkpoint นี้แยกสถานะปัจจุบันจากข้อความในอดีต

## 1. เป้าหมายและตำแหน่งปัจจุบัน

Release ล่าสุดคือ v1.2.8 (22 ตุลาคม 2026); deployment record ยังระบุ production
v1.2.7 การเผยแพร่กับ deployment เป็นคนละการตัดสินใจ ไม่ได้ตรวจ production สด
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
