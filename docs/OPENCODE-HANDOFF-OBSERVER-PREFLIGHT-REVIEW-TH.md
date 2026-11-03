# Observer implementation package 1 — offline preflight/reservation

วันที่: 3 พฤศจิกายน 2026 (Asia/Bangkok)
Parent contract: `baf0c196693da54ac4bad665a3e20f89b2350c8b`, draft PR #117
สถานะ: **FIXTURE-SCOPED SOURCE CANDIDATE / รอ exact-source review / B4 OPEN**

## 1. ขอบเขตที่ส่งมอบ

ผู้ใช้ส่งผลรีวิวรอบ 7 APPROVE contract ณ parent โดย OA01–OA12 ยัง NOT RUN
คำสั่ง “ทำขั้นถัดไป” ให้เริ่ม bounded offline implementation/control package
ผลรีวิวเป็น operator-supplied ไม่มี exact approval timestamp ที่ยืนยันได้
รอบนี้เริ่ม preflight/single-use reservation ก่อน ไม่อ้างว่า implement OA ทั้ง 12 ครบ

เพิ่ม [observer_preflight.py](../acceptance/handoff/opencode/observer_preflight.py),
[22 controls](../acceptance/handoff/opencode/test_observer_preflight.py),
[source/contract manifest](../acceptance/handoff/opencode/observer-preflight-hashes.json) และ
[workflow แยก](../.github/workflows/opencode_observer_preflight.yml)
source component ใช้ stdlib เท่านั้น ไม่ import native runtime/Facts/Batch/planner
ไม่มี fork/exec/signal/DB/evidence read/backend/config/model/network/CLI/MCP path
process ที่ controls fork เป็น children ใหม่เพื่อแข่ง claim/จำลอง crash เท่านั้น
ไม่ใช่ O/S/H deployment และไม่ตั้ง observer/subreaper ในรอบนี้

FixtureIssuer เป็น **trusted fixture bootstrap scaffolding** ไม่ใช่ production
issuer authentication, authority resolver, independent rollback service หรือ external containment
register รับ Binding จาก trusted launcher เท่านั้น; ไม่มี caller JSON → authority/Facts
Python type/frozen object ไม่ป้องกัน hostile same-process/same-uid code
การสร้าง catalog/Binding หรือไฟล์ owner-only/hash ไม่ทำให้มี production permission

## 2. Implemented source path

| Path | Implemented behavior / acceptance limit |
| --- | --- |
| FixtureIssuer.register | รับ exact Binding type และ retained pipe read-end ที่ launcher เป็นเจ้าของ; registry ref เป็น opaque ASCII; source/dossier hashes เป็น fixture binding data ไม่ใช่ authenticity proof |
| _current → reserve | ตรวจ fixture environment, current epoch, active/expiry, exact scope set, cleanup-after-revoke, four-actor declaration, containment fixture tag, root/pipe identity และ shared time arithmetic ก่อนสร้าง claim |
| Exclusive claim | retain private owner-owned 0700 root handle; ชื่อ SHA256 ของ opaque attempt ref; open O_CREAT/O_EXCL/O_NOFOLLOW 0600; exact write, file fsync และ directory fsync; claim เป็น local single-use evidence ไม่ใช่ bearer token |
| Unknown/partial claim | crash/write/fsync/post-write failure คง claim ไว้; ไม่ unlink/chmod/retry; object/issuer ใหม่ที่ใช้ retained anchor เดิม redeem ref เดิมไม่ได้; existing symlink ไม่ถูก follow/repair |
| Budget.start | ล็อก Ta ครั้งเดียว; D_attempt=min(Ta+20,T0+45), D_capture=D_attempt−3; late/future/nonfinite/insufficient reserve reject; witness ไม่ reset clock |
| Reservation.witness | อ่านจาก retained bound pipe เท่านั้น; one atomic frame <=512 bytes, one bounded read, no partial reassembly/retry; strict duplicate-key/type/role/generation/nonce/source field checks และ pre/post authority validation |
| capture | **ปฏิเสธเสมอด้วย PIDFD_ACK_UNBOUND** แม้ fixture witness parse ผ่าน; ไม่มี source branch ที่เปิด G หรือ launch/stop process |
| cleanup_status | ตรวจเฉพาะ fixture eligibility หลัง capture revoke/expiry ภายใน original attempt/current issuer epoch; คืน OWNERSHIP_UNBOUND และ flags false; ไม่ให้ ownership/stop/reap capability |

Valid reservation หมายถึง durable fixture claim ถูกสร้างและ current fixture checks ผ่าน
ไม่ใช่ actual ARM, production launch authorization หรือ pidfd/parent provenance
Result ทุก path ที่คืนค่าเป็น capture_allowed=false/authorizes_actions=false/dev_observed=false
FIXTURE_WITNESS_PARSED ไม่ใช่ original FINAL, CAPTURE_COMPLETE หรือ advisory done

containment='fixture-owned-cleanup' เป็น test declaration ใน closed fixture catalog
ไม่พิสูจน์ observer-loss containment และใช้แทน real production binding ไม่ได้
environment='dev' และ missing/boolean containment ถูกปฏิเสธก่อน claim
ไม่เปิด production positive path ด้วย approved=true หรือ caller verifier_passed

## 3. Actual controls และ failures

Author-local Python 3.12.14: **22/22 OK**, ResourceWarning-as-error, ไม่มี skips
ใช้ disposable private roots และ anonymous pipes เท่านั้น ไม่มี dependency install
development run ก่อนสร้าง manifest พบ missing manifest ตามจริง ไม่ถือเป็น final pass
CI ต้องอ้าง exact candidate head แยก; historical local broad baseline NOT PASS ไม่เปลี่ยน

| Evidence family | Actual stimulus / asserted result |
| --- | --- |
| Preflight deny | forged dict/unknown ref, dev environment, missing/boolean containment, missing scopes/cleanup, wrong generation/boolean generation, hidden actor count และ expiry/revoke => ไม่มี claim ใหม่ |
| Cross-process single-use | fork สอง disposable children โดยปล่อย gate พร้อมกัน; O_EXCL ให้ winner หนึ่งคนและ ATTEMPT_CONSUMED อีกคน; exact child waitpid/reap และหนึ่ง claim เท่านั้น |
| Unknown crash | child ตายจริงหลัง exclusive create ก่อน write; zero-byte claim ยังคงอยู่; next reserve ต้อง ATTEMPT_CONSUMED ไม่ respawn/repair |
| Persistence failure | injected fsync error หลัง actual write => CLAIM_UNCONFIRMED; file ไม่ถูกลบ; next reserve ถูก deny; raw exception sentinel ไม่ถูก echo |
| Limited rollback | rollback data-file generation พร้อมสร้าง issuer/Binding object ใหม่จาก fixture snapshot โดย retained claim root แยกยังอยู่; claim เดิมยังกัน replay |
| Filesystem identity | symlink claim ไม่ follow/repair; root mode drift ถูก reject และไม่ chmod โดย source |
| Real pipe framing | wrong generation/role/hash/nonce/extra field, partial/two frames/EOF/no data/oversize/duplicate JSON keys/float/NaN/non-ASCII => reject ไม่มี successful capture; failed first read ไม่ retry |
| Revocation after reserve | actual frame อยู่ใน pipe แต่ source reject ก่อน read; limited cleanup eligibility ยังคืนได้ภายใน deadline/current fixture epoch โดยไม่มี action authority |
| Budget | future/stale/nonfinite T0 และเวลาที่กัน cleanup ไม่พอ reject; exact shared 3/20/45 arithmetic; witness ไม่เลื่อน deadline |
| Privacy/source | Result ไม่รวม refs/nonces/source/dossier hashes/paths; AST audit ไม่พบ process/backend/mutation dispatch; manifest เทียบ actual SHA256 และ byte length |

Rollback experiment นี้ไม่ใช่ real native DB+authority+dossier+context rollback corpus
และไม่พิสูจน์ anchor root/issuer restart state ว่าต้าน host snapshot/power-loss ได้
file/directory fsync ไม่ใช่ issuer authentication หรือ universal filesystem durability proof
ถ้าตัว claim domain ย้อนกลับ/หาย/ถูกแทน หรือ bootstrap เลือก root ใหม่โดยไม่ได้รับรอง
production B3 ยัง UNBOUND/HOLD; ไม่ claim ว่า field generation อย่างเดียวแก้ rollback

## 4. OA01–OA12 disposition ณ source package นี้

PARTIAL = มี named component evidence ใหม่ ไม่ใช่ full obligation PASS
ไม่มี OA row ใดถูกเปลี่ยนเป็น CLOSED/PASS ทั้งแถวจาก package นี้
ตารางใน [contract](OPENCODE-HANDOFF-OBSERVER-ADOPTION-CONTRACT-TH.md) เป็น historical
preregistration; ตารางนี้เพิ่ม actual disposition โดยไม่แก้นิยามเดิม

| OA | Source/control evidence ใหม่ | ยังเปิด / ไม่ได้รันใน source path นี้ |
| --- | --- | --- |
| OA01 PARTIAL | _current/reserve; forged/expiry/revoke/epoch/scope/containment tests และ claim absence | production issuer/anchor; integrated no-O/S/H/protected-read-before-admission trace |
| OA02 PARTIAL | Budget/reservation/witness strict real-pipe framing และ duplicate/role reject | actual R/O/S/H startup, parent/source-authenticated witness, pidfd acquisition/ACK-before-G |
| OA03 NOT RUN | capture remains denied; no PID selection/signal path | actual interrupted-launch/witness disappearance/PID-reuse controls ของ observer implementation |
| OA04 NOT RUN | ไม่มี adoption หรือ reaper code | actual production arbitration/concurrent-reaper path; 9 supervisor-loss controls เดิมเป็น input evidence เท่านั้น |
| OA05 NOT RUN | ไม่มี FINAL parser/observer receipt path | S-reaped-H/missing-FINAL disposition ใน joined implementation |
| OA06 NOT RUN | ไม่มี O/S/H process topology | joined simultaneous O/S death และ helper cleanup; ไม่ claim ด้วย claim-race children |
| OA07 PARTIAL | containment/dev guard reject ก่อน claim; no G branch | real accepted external containment/profile, actual R-death controls และ production positive ARM |
| OA08 PARTIAL | bounded atomic fixture witness parse/privacy/partial/duplicate reject | original FINAL, inherited output write end/full-pipe/drain/EOF joined source |
| OA09 PARTIAL | actual process race/crash/restart-object/retained-root replay deny | production one-use issuer, independent anti-rollback anchor และ full-store rollback corpus |
| OA10 PARTIAL | shared Budget arithmetic/time anomaly/three-second reserve | actual concurrent O/S stop→adopt H resource enforcement, aggregate physical memory, deployment feasibility |
| OA11 PARTIAL | new private claim retained on failure/symlink no repair; allowlisted Result | full private evidence/retention/audit/output ownership/cleanup acceptance |
| OA12 NOT RUN | ไม่มี Facts/planner/verifier/state capture path และไม่คืน Done | full joined original FINAL/context/head/authority/goal evidence; G ยังไม่ implement |

22 tests เป็น source controls ไม่ใช่ OA trial count หรือ recovery gain
type-check/AST/source identity และ green CI ไม่ใช่ production security boundary proof
B1–B7/OC18 ไม่ถูกปิด; actual Dev/current model/provider/job/context facts ไม่ถูกสังเกต

## 5. Next source boundary

หลัง independent exact-source review ของ foundation นี้ ให้ทำ bounded offline
R/O/S/H witness/pidfd/ACK/arbitration package ที่มี actual startup/loss trace
และ independent lifecycle evidence โดยคง production authority/containment UNBOUND
ต้อง integrate หรืออธิบาย failure ของ reservation consume-before-side-effect ให้ครบ
ไม่แปลง FixtureIssuer หรือ parsed witness เป็น production issuer โดยเปลี่ยนชื่อ/tag
เมื่อยังไม่มี accepted pidfd/ownership path ต้องไม่เปิด G เพื่อให้ได้ positive test
implementation merge ของ runtime/privacy/authority interface ต้องผ่าน SPEC §14 แยก

รอบนี้เพิ่ม source/tests/hash/workflow/review packet เท่านั้น ไม่มี public bridge tool/config
ไม่มี O/S/H launch, DB/evidence/credential access, checkpoint append, original FINAL,
Dev/pilot, archive invocation/evaluation arm, release หรือ deployment
source/29+9+48 controls/old workflows/hash manifests/schema/SPEC/OC definitions/receipts เดิมไม่เปลี่ยน
PR #117 draft/unmerged; B4 OPEN; J0 PAUSED; #112 ไม่เปลี่ยน
R1 NOT AUTHORIZED / R2 HOLD; OC18 NOT RUN
