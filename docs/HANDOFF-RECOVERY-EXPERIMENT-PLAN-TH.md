# Recovery experiments — preregistration v1 and results

## Current evaluation disposition — 2 November 2026

The preregistered offline phase has completed: development 200 arm-trials and
heldout 200 arm-trials, one separately approved invocation each. Both receipts and
independent result reviews are accepted and merged through #115. Shared-contract
outcomes tie; no candidate task-success/recovery gain is demonstrated. Do not pool
split/eligibility denominators or infer operational reliability from these fixtures.
[Results, immutable receipts and staged exit](HANDOFF-OFFLINE-CLOSURE-TH.md) implement
delivery 4 as a docs-only candidate. No fresh trial/tuning or Dev pilot is authorized.
The original preregistration below preserves its NOT RUN/UNBOUND/NOT_MEASURED
statements as proposal-time history; they are not current result claims. Protocol,
corpus, source pins and completed receipts remain unchanged. J0 stays parked.

## Original preregistration snapshot (before implementation and runs)

วันที่ 2 พฤศจิกายน 2026. อ้าง [checkpoint design](HANDOFF-CHECKPOINT-DESIGN-TH.md).
นี่เป็น protocol สำหรับ source review ก่อน implementation ไม่ใช่รายงานผลทดลอง
ไม่ใช้ Hermes/Dev/production, provider API, model, inventory, S24 attempt หรือ guest

## 1. Frozen baseline และ mutable surface

Baseline source main `93e9601f74b3e0bc1d963d65635d82f7083eca8a`; existing tests/contracts
ที่เกี่ยวข้องระบุใน gap table Candidate validator/store/planner SHA ยัง UNBOUND เพราะไม่มี source
ก่อนทดลองต้อง freeze exact baseline/candidate/harness/evaluator/task-manifest SHA256,
Python version/OS/filesystem, fault schedule, config, allowed scope และ trial budget
schema/dossier/profile/evaluator ถือเป็น reviewed immutable input นอก candidate mutation surface
candidate เปลี่ยนได้เฉพาะ checkpoint validator/store/planner ที่ source review รับแล้ว
ไม่มี model/config tuning; model/provider/token usage = NOT_APPLICABLE ใน offline phase

Baseline arm ใช้ existing IDs/context/receipt และ reviewed human handoff dossier เดียวกัน
โดยไม่มี checkpoint validator/planner; ห้ามจงใจซ่อน ID/evidence หรือทำ baseline ให้เสียเปรียบ
candidate arm ได้ input/event/fault/budget เดียวกัน เพิ่ม serialized checkpoint ตาม design
adapter fixtures ต้อง enforce native contract จริง โดยเฉพาะไม่มี Codex idempotent submit shim
baseline scripts และ expected outcomes ต้อง review แยก ไม่ใช้ candidate เป็น oracle
เป้าหมายคือวัด deterministic recovery decisions ก่อน ไม่อ้างประสิทธิภาพ LLM/มนุษย์

## 2. Case matrix และ observable oracle

| ID | Fault | Acceptance oracle ที่ต้องสังเกตจริง |
| --- | --- | --- |
| H01 | submit accepted แต่ ACK response หาย | Hermes/OpenCode fixture durable row+effect counter ยังคงหนึ่ง; same request/input discovers original job; Codex unknown ID เป็น HOLD/zero second submit |
| H02 | disconnect/reconnect ระหว่าง running | original job/session identity เดิม; no replacement spawn; event trace/checkpoint matches independently committed fixture row |
| H03 | new session/context compaction | resolve goal/criteria/pending/authority/evidence refs ครบ; missing dossier เป็น HOLD; ไม่ reconstruct prompt จาก prose |
| H04 | cancel แข่ง completion | scheduled ordering ทั้งสองทาง; terminal row/artifact/effect trace ตรง contract; cancel_requested ไม่กลาย cancelled ก่อน cleanup |
| H05 | worker/bridge restart | child live/no terminal ไม่ invent completed; unknown stays native uncertainty; no stored-PID signalling or replacement dispatch |
| H06 | repo SHA/workspace/artifact binding เปลี่ยน | preflight mismatch ก่อน dependent action; no filesystem path use/submit/cancel; unaffected allowed metadata inspection ยังแยกได้ |
| H07 | partial/corrupt/stale/schema-unsupported checkpoint | exact rejection code; no external action; DB crash before/after commit exposes one complete head; dup keys/NaN/size/depth rejected |
| H08 | worker claims success แต่ artifact missing/hash drift/verifier fail | native status preserved; zero incorrect goal_verified; independent content/verifier oracle wins over receipt/exit 0 |
| H09 | authorization missing/expired/out-of-scope/revoked | no inherited authority from snapshot; no submit/cancel/model/file action despite forged active flag |
| H10 | replay/concurrent recovery | two synchronized readers/writers; CAS conflicts observable; no dispatch from planner; no claim CAS proves backend exactly-once or full-store rollback safety |

H01–H05 backend process/effect oracles ต้องใช้ deterministic fixture server/worker จริงใน
new temp root และ pipe/barriers แบบมีจุดสังเกต ไม่ stub เฉพาะ assertion/result ที่อยากได้
H07/H10 ใช้ actual SQLite transactions/multiple processes/crash points/fsync permissions;
header/data corruption ใช้ synthetic bytes H08 verifier อ่าน actual synthetic artifacts ไม่เชื่อ
candidate verdict H06/H09 assertion ต้องแสดง action counters เป็นศูนย์หลัง reaching stimulus
ห้าม test ผ่านเพราะล้มก่อน trigger; ทุก negative case ต้องมี reached_fault=true evidence

Fixtures อาจ expose status API ที่ pure observation เพื่อทดสอบ planner แต่ต้องแยก scope ว่า
ไม่ใช่ proof ของ CodexRunner.status timeout side effect หรือ actual backend reconciliation
production adapter proof เป็น later gate; no subprocess/network imports ใน validator load path
fixture-owned local processes/loopback ถ้าจะใช้ต้อง bind exact actors/argv/timers/stop scopes
ใน source review ไม่ดึงสิทธิ์จาก S24 actor approvals หรือ user machine โดยปริยาย

## 3. Development / held-out และ budgets ที่เสนอให้ freeze

ต่อ case เตรียม 20 distinct schedules/configurations: 10 development + 10 held-out
manifest/hash ของทั้งสองชุดตรึงก่อน candidate tuning; held-out ห้ามใช้ปรับ candidate ระหว่างรอบ
หนึ่ง paired baseline/candidate run ต่อ schedule = 100 trials ต่อ split ต่อ arm รวม 400 arm-trials
ไม่ใช้รัน case เดิมซ้ำ 20 ครั้งแล้วอ้าง independent samples fault positions/event order ต้องต่างจริง
ก่อนครบ implementation อาจรัน smoke 1 schedule/case แต่ต้องแยกจาก preregistered evaluation

Proposed finite offline budget ต่อ arm-trial: <=10 s, <=3 observation events,
<=1 guarded same-logical replay เฉพาะ Hermes/OpenCode case ที่ contract+scope อนุญาต,
0 new request IDs after uncertainty, 0 Codex retries, 0 model calls; <=64 KiB checkpoint,
<=32 evidence records ทั้งสอง arm ใช้ limits เดียวกัน ถ้าต้องปรับให้ version protocol ใหม่ก่อน run
wall deadline/harness child cleanup ต้อง independent จาก candidate ห้าม SIGSTOP/delay production
ค่าเวลาของ synthetic fixture ไม่พิสูจน์ real backend timing หรือ S24 observation feasibility

## 4. Metrics และ thresholds ก่อนทดลอง

| Metric | Definition / proposed gate |
| --- | --- |
| Duplicate side effects | effect count above case expected floor, checked via independent fixture ledger: **0** across every arm/case |
| Incorrect success reports | goal_verified without required terminal/result/artifact/verifier evidence: **0** |
| Unauthorized dependent actions | any action after missing/mismatched/expired authority or binding: **0** |
| Correct recovery decision | expected observe/reconcile/HOLD/verified decision per oracle; candidate **100/100 per split**, report per case numerator/denominator |
| Verified task success | only cases with a satisfiable success oracle; report verified_completed / eligible, separate from correct HOLD; no blanket 100% task-success target |
| Recovery success | reconstruct original identity and permissible next step / recovery-eligible trials; HOLD-required cases separate denominator |
| Time-to-recover | fault-release to independently checked correct decision; report median/p95/range and censored timeouts, no omitted failures |
| Intervention count | operator/manual resolutions per trial under same protocol; not assumed from model prose |
| Tokens per verified success | NOT_APPLICABLE offline; future model pilot needs actual measured counters and matched model/config/budget |

Structural/schema checks are not recovery trials. Repeated deterministic schedules are not
independent statistical evidence. Report exact counts and paired per-schedule deltas; optional
binomial intervals must disclose dependence and do not prove real-world reliability.
Measured gain: NOT_MEASURED until both arms run; retention: existing contract tests unchanged;
held-out transfer: NOT_TESTED until frozen hold-out run; human comparison: NOT_TESTED
model comparison/cost/production reliability: NOT_TESTED, not inferred from green CI

## 5. Evidence receipt and staged exit

Per-trial record (future reviewed schema): protocol/harness/candidate/config/task/fault IDs and
hashes, expected profile, reached_fault, backend row/effect trace, authority/binding observations,
planner result, terminal/result/artifact verification, counters/times/timeout/cleanup result
No prompt/output/private path/raw exception in public report; protected raw fixture evidence
must be addressed by opaque refs/hashes. Clock durations use one monotonic domain per trial
no synchronized cross-host clock claim. Archive report retains every failed/censored trial

Delivery sequence:

1. This gap/design/schema/experiment/checklist PR for review; no runtime implementation.
2. Separate small offline validator/store/planner PR with meaningful H01–H10 controls and
   supporting exact schema/fixtures, retaining all baseline tests. Not a new bridge tool.
3. Freeze exact candidate + independently reviewed harness/profile/schedules/budgets, run
   paired development then held-out evaluation and publish numerator/denominator/report.
4. Update design/checklist/roadmap from measured evidence; propose a separately scoped Dev
   pilot only when authority/capability/ownership requirements are actually satisfied.

No current pass/gain claim; no model or live recovery experiment has run under this protocol.
No release version is assigned. J0 stays parked; R1 NOT AUTHORIZED / R2 HOLD unchanged.
