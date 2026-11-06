# OpenCode handoff — แผนปิด blockers หลัง source review รอบ 3

วันที่: 3 พฤศจิกายน 2026 (Asia/Bangkok)
สถานะ: **แผนงาน / ยังไม่ implement หรือรัน controls เพิ่ม / ไม่ใช่ pilot packet**

## 1. Checkpoint และขอบเขตการยอมรับ

ผู้ใช้ส่งผลรีวิวรอบ 3: **APPROVE — source candidate ผ่าน exact-source review**
ที่ `0e79bd00f54e33e4c462a2a37228b89316161794` บน draft PR #117
พร้อมระบุว่าไม่มี findings ในขอบเขต fixture/offline ที่ตรวจ
บันทึกนี้เป็น operator-supplied review ไม่ใช่ GitHub review submission ที่ผู้เขียนสร้างแทน
ไม่มี timestamp ของการอนุมัติที่ยืนยันได้ จึงไม่เติมเวลา

คำสั่งถัดมา “ทำขั้นถัดไป” ให้จัดทำ blocker closure plan ตามที่เสนอใน session
ผลรับ source จำกัดที่ head และขอบเขตข้างต้น ไม่ครอบคลุม source ที่จะเปลี่ยนในอนาคต
และไม่ทำให้ production integration หรือ OC18 ผ่าน
ข้อความสถานะเดิมในเอกสารต้นทางเป็นประวัติของแต่ละ checkpoint

หลักฐานฐาน:
[source review](../acceptance/handoff/opencode/SOURCE-REVIEW.md),
[source hashes](../acceptance/handoff/opencode/source-hashes.json),
[design และหก gates](OPENCODE-HANDOFF-INTEGRATION-DESIGN-TH.md),
[Facts contract](OPENCODE-HANDOFF-FACTS-CONTRACT.md),
[snapshot contract](OPENCODE-HANDOFF-SNAPSHOT-CONTRACT.md),
[OC01–OC18](OPENCODE-HANDOFF-CONTROLS-TH.md)

CI ของ source head เดิมมีสี่ workflows SUCCESS ตาม PR
จำนวนที่รายงานเดิมคือ source 48/48, baseline 234/234,
handoff 26/26 และ preparation 26+18 บน Python 3.12/3.14
ผลเหล่านี้ไม่ใช่ผลรันใหม่ของเอกสารนี้
Local broad baseline เดิมยังเป็น NOT PASS: 98 tests, 4 failures/14 errors
มี dependency imports ขาดและ Codex process assertions สี่ข้อที่ root cause ยัง UNKNOWN

## 2. Blocker matrix

ทุกแถวมีสถานะ **OPEN** การมีแผนหรือ fixture positive ไม่เปลี่ยนสถานะเป็น CLOSED
ผู้ทำงาน source ต้องแนบหลักฐาน และ independent review ต้องระบุขอบเขตที่รับจริง

| ID / gates / OC | ช่องว่างจาก source ที่รับแล้ว | งานและเกณฑ์ตรวจรับ | หลักฐานที่ต้องมี / เงื่อนไข HOLD |
| --- | --- | --- | --- |
| B1 / gates 1–2 / OC02,06,11,13 | `facts.py` รับ authority/dossier จาก trusted fixture launcher; model/provider และ context association เป็น fixture bindings | ระบุ issuer, protected resolver, threat model และ closed schema ที่อิสระจาก checkpoint; bind source/interpreter/Dev identity, repo/head/workspace, job/request/session/fingerprint refs, model/provider/current binary/config generation และ non-null existing context association; revalidate ก่อน capture และก่อน receipt | Private binding record + source/control receipts ที่แยก trusted issuer จาก untrusted input; เปลี่ยนทุก binding ทีละ field และแสดงว่า downstream capture/verifier/planner ไม่ถึง; unknown issuer/model/provider/context หรือ missing physical DB/read-lock scope => HOLD; owner-only JSON/hash หรือ provider prefix ไม่ใช่ production authority |
| B2 / gates 2,5 / OC06,12,13 | Native row เก็บ binary path; current digest ไม่พิสูจน์ executable/source ตอน original invocation | ระบุ original-run evidence ที่มีอยู่ก่อนและ independently accepted หาก locked goal ต้องการ; bind original job/source/binary/dependency provenance ตาม criterion | เปลี่ยน current binary ให้ตรงแต่ลบ original proof แล้วยังต้อง HOLD; ไม่มี original evidence ให้รายงาน infeasible สำหรับ criterion นั้น; ห้ามเติม provenance ย้อนหลังด้วย current hash หรือเปลี่ยน goal เพื่อให้ผ่าน |
| B3 / gate 2 / OC14 | `Store.head()`, CAS และ fixture epoch ตรวจ drift ได้ แต่ทั้ง store/authority/dossier อาจถูก rollback พร้อมกัน | ออกแบบ independent freshness anchor นอก rollback domain ของชุดที่สังเกต; กำหนด issuer, monotonic epoch semantics, restart/loss/revocation และ read authority; admission ต้องผูก anchor ก่อนและหลัง capture | Fixture คืน store+authority+dossier+context ทั้งชุดเป็น snapshot เก่าที่ checksum-valid แต่ external anchor ใหม่ต้อง reject; missing/stale/replayed anchor, clock anomaly หรือ anchor unavailable => HOLD; nonce/time/checksum ที่ย้อนกลับพร้อม store ไม่ปิด B3 |
| B4 / gate 4 / OC15,16 | `batch.py` หยุด/reap owned helper เมื่อ owner ยัง cleanup ได้; abrupt external-owner death ยังไม่พิสูจน์ | เสนอ supervisor/ownership protocol ที่ครอบ parent death, startup handoff, blocked pipe และ helper exit; ระบุ actors/argv/retained handles/FD closure/deadlines/memory/retention และว่าใครยืนยัน reap เมื่อ owner ตาย; ห้ามอ้าง parent-death signal อย่างเดียวเป็น complete stop proof | Owned disposable process fixtures: ตายก่อน handoff, หลัง helper start, ระหว่าง capture และหลัง success prefix; independent observer ยืนยัน exit/reap/EOF ตาม protocol; stop ไม่ยืนยัน => STOP_UNCONFIRMED/HOLD และไม่มี done; ไม่มี numeric-PID/PGID fallback หรือ signal original worker |
| B5 / gate 5 / OC09,12,17 | Goal ที่ implement คือ exact full-artifact size+SHA256 ซึ่ง independently locked ใน fixture; ยังไม่มี original Dev goal oracle | ล็อก original goal/criteria/profile/evidence/verifier ก่อน observation โดย independent acceptance; ระบุว่า exact artifact property พิสูจน์ criterion ใด และสิ่งใดพิสูจน์ไม่ได้ | Positive และ negative oracle ตาม original criterion; completed/exit-zero/reassuring text/expected hash ที่ตั้งหลังเห็น output ต้องไม่สร้าง pass; หลักฐานไม่พอ => HOLD; ไม่ใช้ model summary เป็น oracle หรือเรียก provider เพื่อเติมหลักฐาน |
| B6 / gates 3–4 / OC03–09,15–16 | Supported Linux x86_64 + native SQLite 3.45.1 fixture มี controls; ไม่ครอบทุก corruption/race/resource/dependency/retention condition ของ deployment | ทำ coverage inventory โดยคง OC definitions; ระบุ supported platform/filesystem/schema/library/build trust และตรวจ enforcement ของแต่ละ byte/memory/time limit ที่ call site; เพิ่ม controls ที่ถึง I/O gate จริง | ตรึง source/stimulus/environment/expected rejection/actual evidence ต่อ case; journal แม้ empty, truncated DB, output append/truncate/replacement/over-cap, denied native hook, owner/resource failures ต้องมี disposition; unsupported case => HOLD หรือ blocker ไม่ใช้ fallback/skip เป็น pass |
| B7 / gates 1–6 / OC18 | ไม่มี current Dev bindings และ finite action approval | เมื่อ B1–B6 มี source acceptance และ private bindings ครบ จึงจัดทำ one-observation packet สำหรับ original completed job ที่รู้ ID อยู่แล้ว; แยก permission ของ reads/optional new outputs/stop/retention ให้ตรวจรับได้ | Gate matrix ทั้งหกพร้อม exact-source receipts และ finite operator approval; field ใดยัง UNBOUND => NOT READY; OC18 NOT RUN จนอนุมัติ scope นั้น; source review/green CI ไม่ใช่ action approval |

B2 ไม่เปิดสิทธิ์อ่าน original evidence จริงในรอบนี้
B3 เป็น design obligation ไม่ได้เลือกหรือเปิด external service/credential ใหม่
B4 ต้องพิสูจน์ feasibility ภายใต้ helper <=20 s, outer owner <=45 s,
native open/lock/query/close alarm 1 s เดิม; ถ้าพิสูจน์ไม่ได้ให้คง blocker
ไม่ขยาย timer หรือลด assertion เพื่อให้ผ่าน

## 3. Review observations ที่ต้องตามใน source รอบถัดไป

ข้อความรีวิวมีบางส่วนคลุมเครือ จึงเก็บข้อสังเกตที่อ่านได้เป็น review targets
ไม่อ้างว่าเป็น findings ใหม่หรือการอนุมัติการตีความเพิ่ม

| ข้อสังเกต | งานตรวจที่ต้องทำ | หลักฐานรับงาน |
| --- | --- | --- |
| OC02 / config และ authority | แยก fixture model/provider mapping ออกจาก canonical production mapping; กำหนด allowlisted non-secret projection และ generation; unknown/extra/missing schema fields reject | Source branch coverage ที่แสดง rejection ก่อน capture; ไม่ dump/hash whole secret-bearing config |
| OC04 / attempt upper bound | อธิบาย enforcement ทั้ง owner และ native helper; `Owner.used` เป็น fixture object guard ไม่ใช่ cross-process one-attempt authority | Controls ของ duplicate object/cross-process admission/relaunch ตาม proposed authority; unknown execution consumes scope, ไม่ retry |
| OC05 / dispatch guard | เสริม explicit constructor/from_config/native-method/CLI/model/network traps ใน owned fixture แยกจาก AST audit | แสดงว่าแต่ละ prohibited hook fail เมื่อแตะ และ valid observation ไม่ถึง hook; ไม่เรียก real backend เพื่อทดสอบ trap |
| Facts / closed call graph | Trace authority → dossier → capture → exact evidence → verifier → Facts → planner; ปิด path ที่รับ serialized caller booleans | Every construction path มี source reference + positive/negative control; arbitrary caller Facts ไม่กลายเป็น trusted Facts |

## 4. ลำดับส่งมอบที่เสนอ

1. ทำ B4 เป็น bounded offline source package แรก พร้อม protocol และ owned-death controls
   ไม่พึ่ง actual Dev, #112, S24 guest หรือ credentials
   ผลต้องระบุว่าปิดได้เฉพาะ ownership profile ใด หรือยัง infeasible
2. ออกแบบ B1+B3 ร่วมกันก่อนทำ production resolver
   ข้อกำหนด issuer/rollback domain เป็น input ของ implementation ไม่เติมจาก fixture
3. ทำ B2+B5 จาก original-goal requirement ที่ล็อกไว้
   หากไม่มี historical evidence ให้คง HOLD และรายงานข้อจำกัดตรง ๆ
4. ปิด B6 และ review observations พร้อม OC disposition รายแถว
   รายงาน partial coverage แยกจาก row closure และแยก local failures จาก CI
5. เตรียม B7 เมื่อ prerequisites ครบ เพื่อขอ finite action approval เป็นขั้นสุดท้าย
   ข้อความนี้ไม่เริ่ม B4 implementation หรืออนุมัติขั้น Dev โดยอัตโนมัติ

Source package ถัดไปต้องใช้ requirement/blocker → task → control → evidence →
exact commit SHA; source เปลี่ยนต้อง review ใหม่ก่อนอ้าง acceptance
Runtime/authority/privacy interface ต้องผ่าน [SPEC section 14](SPEC.md)
ก่อน implementation merge

## 5. Evidence record และ handoff

แต่ละ blocker ต้องมีอย่างน้อย:
ID/status/scope, requirement ที่อ้าง, source SHA/path, task/control/stimulus,
expected outcome, actual outcome, environment/dependency identities,
private evidence locator, privacy-safe summary, independent review และ unresolved limits
ใช้ NOT RUN/UNBOUND/UNKNOWN เมื่อยังไม่มีหลักฐาน
Expected outcome ไม่ใช่ actual outcome และ test count ไม่ใช่ source acceptance

Public record เก็บเฉพาะ opaque refs และ approved source/evidence commitments
Native IDs/paths/prompt/output/fingerprint/config/credentials และ raw private audit
อยู่ใน private scope ที่อนุมัติแยก; ไม่เติมค่าจากความจำหรือสำรวจ Dev เพื่อเติมตาราง

รอบนี้เพิ่มเอกสารแผนเท่านั้น ไม่ implement resolver/supervisor/anchor/verifier ใหม่
ไม่มี controls/trials ใหม่, ไม่ append checkpoint/receipt หรือรัน archive invocation
หลักฐานต้นทางและ OC definitions เดิมยังคงอยู่
PR #117 คง draft/unmerged; J0 PAUSED; #112/#80/#96/private bindings ไม่เปลี่ยน
R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN
ไม่มี Dev/pilot, runtime/API/model/key/config action, release หรือ deployment
