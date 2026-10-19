# ผล Live Acceptance

## v1.2.4 release candidate — live tunnel acceptance บน Dev route จริง: ผ่านแบบมีเงื่อนไข (18 ตุลาคม 2026)

สถานะ: executed แล้วเมื่อ 18 ตุลาคม 2026 ผ่าน plugin จริง `Hermes Local Bridge - Dev` ที่ชี้ไปยัง candidate deployment `~/hermes-mcp-bridge-v1.2.4-dev-candidate` (ติดตั้งจาก candidate ZIP ที่สร้างจาก commit `00245f45da2142dfd86de6741272632f1e1b0407` และตรวจ SHA-256 `431cb064ad27408ad4ab4199f3452f811ffd16f27ddfc31a33b2e5f5e99eb363` แล้ว) ข้อสรุปเป็น **bounded PASS**: ยืนยัน identity, status และ tool visibility ของ candidate บน Dev route จริงเท่านั้น **ไม่ใช่**การพิสูจน์ guard ผ่าน tunnel ทั้งหมด (ดูข้อจำกัดหลักฐานด้านล่าง) ส่วน `--version` จริงของ OpenCode CLI (`opencode v2.0.32`, 18 ตุลาคม 2026) ยังเป็น live acceptance เดียวของ adapter ตามขอบเขต PR #34 OpenCode ยัง disabled by default และ acceptance นี้ไม่ได้เปิด OpenCode ผ่าน MCP

ข้อสังเกตบน plugin Dev จริง (จาก tool call จริงของ parent):

- `bridge_version`: ok — version `1.2.4`, release identifier `v1.2.4`, build provenance `release`, source kind `release-archive`, source revision `0884482d8cf74d696b6c52a785282f65f2bd40fa`, revision source `embedded-build-input`, schema `1/1`, discovery count `27`
- `bridge_status`: ok — hermes ok, codex ok, watchdog running ทุก 15 วินาที, Hands false, upstream_checked false
- Dev chat แสดง 27 callable tools (นับจาก ALL_TOOLS ของ parent) — เป็นหลักฐานฝั่ง parent ไม่ใช่ raw `tools/list` response บน wire; raw `tools/list` = 27 ถูกพิสูจน์แยกใน offline suite และ real-stdio probe จาก tree ที่แตกจาก candidate
- production ไม่ถูกแตะ: plugin production ยังรายงาน `1.2.3` / revision `60de77fa8945a67eb578828e710f1cacc63680e5` / 27 tools (ตรวจ read-only)
- receipt ส่วนตัว `guard-tunnel-acceptance-receipt-20261018.md` (เก็บในพื้นที่ backup 0600; parse แบบ metadata-only): log โตจาก byte 320572 เป็น 323717 ในช่วง 21:16:04–21:16:07 +07 มี event forward command 6 รายการและ acknowledged notification 2 รายการ หลัง ready ไม่มี error ใหม่และไม่มี validation flood เพิ่ม ก่อนหน้านั้น start ล้มเหลว 3 ครั้งเพราะ environment ของ authentication ไม่ครบ ผู้ใช้ relaunch ให้ครบแล้วจึง start ได้ (recovery โดย operator แบบสั้น ไม่มี secret, path ของ env, ค่า env หรือข้อความจาก history ใดถูกบันทึก)

| รายการตรวจ | ผล |
| --- | --- |
| identity ตรง candidate stamp ผ่าน real Dev route (`bridge_version`) | ผ่าน |
| `bridge_status` สุขภาพครบบน real Dev route | ผ่าน |
| tool visibility: 27 tools บน Dev chat (parent count) | ผ่าน |
| production ยังเป็น v1.2.3 / 27 tools (read-only) | ผ่าน |
| ไม่มี error ใหม่ / ไม่มี validation flood หลัง activation (log metadata) | ผ่าน |
| raw `tools/list` = 27 บน tunnel (wire evidence ผ่าน tunnel) | ไม่สังเกตได้ — ใช้หลักฐาน offline/stdio แทน |
| `server/discover` → `-32601` ตรง ๆ ผ่าน tunnel | ไม่สังเกตได้ — ดูข้อจำกัดหลักฐาน |
| release review → archive สุดท้ายจาก signed tag → tag/sign/publish | ค้าง — release gates ถัดไป |

ข้อจำกัดของหลักฐาน (สำคัญ ห้ามมองข้าม): dispatcher log ไม่บันทึกชื่อ method, ชื่อ tool หรือ JSON-RPC outcome code และ guard ออกแบบให้ไม่ log payload จึงไม่มีใครสังเกต `server/discover` → `-32601` บน tunnel ได้จาก log นี้ ทั้งตอนนี้และในอนาคตจากไฟล์ log เดียวกัน การที่ไม่พบ flood ห้ามนำไปสรุปว่า guard จัดการ probe จริง (ห้ามอนุมานจากการขาดหลักฐาน) พฤติกรรม guard ถูกพิสูจน์ด้วย offline suite 129/129 และ real-stdio probe (same id / no echo / `-32601` / 27 tools / EOF สะอาด) ซึ่งตรงกับ acceptance mapping ของ SPEC.md section 17 ที่ระบุชุดทดสอบ real-stdio อย่างชัดเจน ไม่ใช่การสังเกต guard code ผ่าน tunnel และ LIVE-ACCEPTANCE ของ candidate กำหนดให้มี live smoke ผ่าน Secure MCPs จริงโดยไม่มีเกณฑ์พิเศษให้สังเกต probe ตรง ๆ — เอกสารนี้บันทึกผลตามขอบเขตนั้น ไม่แก้ SPEC และไม่ลดเกณฑ์ย้อนหลัง

สิ่งที่ยังไม่อ้างและสถานะคงเดิม: ไม่อ้างการพิสูจน์ guard แบบ live ครบทั้งหมดบน tunnel ไม่อ้าง production accepted หรือ released ห้ามติดตั้ง candidate ลง runtime การผลิตหรือ restart production จนกว่า release จะเผยแพร่ MCP Events ยังคงสถานะ deferred BLOCKED ตาม section ถัดไป และ production ยังเป็น released v1.2.3

อัปเดตสถานะ (18 ตุลาคม 2026): แถว "release review → archive สุดท้ายจาก signed tag → tag/sign/publish" ที่บันทึกไว้ว่า "ค้าง" ได้เสร็จสมบูรณ์แล้วในวันเดียวกัน — released v1.2.4 ผ่าน signed tag ที่ `2133056` พร้อม ZIP (`e6deb0e6ab16d669836b0e361e2e875858e19597ef35dc7e4fc19010a6a5f3a9`) และ SHA256SUMS ภายนอกที่ตรวจซ้ำหลังดาวน์โหลด (ดู [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)) บันทึก bounded PASS และข้อจำกัดหลักฐานข้างต้นคงเป็นหลักฐานเดิมตามที่เกิดขึ้น ส่วน production deployment ยังเป็น v1.2.3 จนกว่า operator จะเลือกอัปเกรด

## v1.2.4 — MCP Events Dev probe: discovery confirmed, subscription unproven (4 ตุลาคม 2026)

- รอบแรกบน Dev revision `897639028e718f4708c62bf2a595b89b5acd3636` ไม่มี protocol trace; คำตอบใน chat ว่า subscribe ไม่ได้และ “Stopped monitoring” ไม่ยืนยัน protocol outcome.
- หลัง PR #31 เพิ่ม `tools/list` และ metadata-only trace ผู้ใช้ refresh plugin **Hermes Local Bridge - Dev** ขณะรัน fixture ด้วย `BRIDGE_EVENTS_PROBE=1`. Trace ที่ให้มาระบุ `server/discover` (12:39:55Z), `tools/list` และ `events/list` (12:39:56Z) ทุก method มี outcome `ok`; tunnel dispatcher บันทึกการ forward ของแต่ละ request. หน้า plugin แสดง event `bridge.probe.ready` หนึ่งรายการ.
- ใน Work chat คำขอ subscribe ถูกปฏิเสธด้วยข้อความ “the plugin exposes no event-subscription interface in this chat.” Trace ที่ได้รับ **ไม่มี** `events/subscribe` หรือ `events/unsubscribe`; ยังไม่มีหลักฐาน callback challenge, signed delivery หรือ receipt. ข้อความจาก chat ไม่ใช่ protocol error และไม่พิสูจน์ว่า tunnel/client ไม่รองรับ Events โดยทั่วไป.
- เมื่อปิด probe แล้ว refresh Dev plugin หน้า plugin แสดง Write 6 + Read 21 = 27 tools และไม่มี event. การสลับรายการนี้เป็นพฤติกรรมของ fixture ที่แทน Dev MCP server ชั่วคราว; production ไม่ได้เปลี่ยน.
- **Decision:** discovery ผ่านเฉพาะชั้นที่วัดได้; gate ของ subscription/callback ยังไม่ผ่าน. ตรวจสิทธิ์/โหมด Work chat และ plugin event controls ขณะ fixture ยังเปิด แล้วเก็บ trace ว่ามี `events/subscribe` เข้าถึง fixture หรือไม่. ใช้ allowlist ว่างในรอบวินิจฉัยเพื่อกัน outbound callback. ห้ามเริ่ม runtime implementation หรือรายงานว่า push ใช้งานได้. Explicit user-directed polling ยังใช้ได้.
- รอบวินิจฉัยถัดมาใน Dev tunnel เดิมมี discovery สำเร็จอีกสองชุด: `server/discover`, `tools/list`, `events/list` outcome `ok` ที่ 13:15:03–05Z และ 13:17:30–31Z (20:15 และ 20:17 น. เวลาไทย) พร้อม dispatcher forwarding. Work chat ตอบว่า “I can’t monitor it: this Work-chat session does not expose the Dev plugin’s event-subscription channel to the model.” Trace ที่ได้รับยังไม่มี `events/subscribe` หลังคำขอ monitor.
- **Gate result for this Dev Work-chat session: no subscription request reached the fixture.** หยุด retry ด้วย prompt เดิมและพัก runtime v1.2.4; ยังไม่ทดสอบ callback, signed delivery หรือ unsubscribe. คำตอบของโมเดลอธิบายอาการ ไม่ใช่ protocol response และไม่พิสูจน์ว่าผู้ใช้/Work chat ทุกแบบไม่รองรับ Events. เปิด gate ใหม่เมื่อยืนยันสิทธิ์/การเปิดใช้ event-triggered tasks ฝั่ง Work chat แล้วเห็น `events/subscribe` ใน trace จริง; เริ่มด้วย allowlist ว่าง.

## v1.2.3 — Worker supervision (4 ตุลาคม 2026)

- ทำบน WSL2 branch `feat/v1-2-3-worker-supervision` ที่ commit `7755f1219a54dd4c8cef6d6d17482e8c8c983478`.
- fault injection ทำให้ detached worker เป็น zombie ขณะที่ Codex child ยังมีชีวิต. สถานะคงเป็น `running`, `exit_code: null`, `supervision_lost: true`, และ reason เป็น `worker_unavailable_child_alive`. ไม่มี terminal record ถูกสร้าง.
- หลัง child จบโดยไม่มี durable terminal record, bridge เปลี่ยนเป็น `unknown_exit` แบบ fail-closed. terminal record ระบุ actor `worker_recovery`, reason `worker_ended_without_terminal_record`, และระบุว่า exit status ของ Codex ใช้ยืนยันไม่ได้.
- cancel หลัง worker หายยังส่งสัญญาณไปยัง process group เดิมได้. งานจบเป็น `cancelled` โดย terminal actor เป็น `local_operator` และ reason เป็น `cancellation_requested`.
- รัน `.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -v` ผ่าน 75 tests โดยไม่มี `ResourceWarning`. ข้อความยืนยันคือ `V123_WSL_REGRESSION_CLEAN`.
- independent review ผ่านแล้ว. signed tag `v1.2.3` ชี้ commit `c610660637dbdcfa0b8ddb7bbf01ed22ae66055d`; GPG verify ผ่านด้วย EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- [GitHub Release v1.2.3](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.3) แนบ ZIP และ external `SHA256SUMS`; SHA-256 ของ ZIP คือ `c231f8563543dbfa9eafa240c5e8e15f44434103940352066e65b58162cb5458`.
- ดาวน์โหลด asset กลับจาก GitHub แล้ว `sha256sum -c SHA256SUMS` และ `unzip -t` ผ่านครบ. ผลนี้เป็น release ที่เผยแพร่แล้ว.


## v1.2.2 — Bridge version/provenance (23 กันยายน 2026)

- ทำบน Dev working copy ที่ commit `5fcac967bc69e82e546a710702454464e52b86be` ผ่าน Secure MCP Tunnel ของ `Hermes Local Bridge - Dev`; Production ไม่ถูกเปลี่ยนแปลง.
- `./bridge.sh version` และ MCP `bridge_version` ให้ identity ตรงกันทุก field: version `1.2.2`, release identifier `v1.2.2-candidate`, source kind `git-worktree`, revision `5fcac967bc69e82e546a710702454464e52b86be`, schema `1`, และ discovery contract `27` tools.
- ตั้ง Dev config ชั่วคราวให้ Hermes ชี้ `http://127.0.0.1:1` และ Codex binary เป็น path ที่ไม่มีอยู่, restart เฉพาะ Dev tunnel, แล้ว MCP `bridge_version` ยังตอบผล identity เดิมได้. ระหว่างทดสอบไม่เรียก Hermes/Codex task หรือ tool อื่น.
- response ไม่มี filesystem path, credential, prompt, output หรือ audit content. หลังทดสอบ restore config จาก backup แล้ว `cmp` ผ่านแบบ byte-for-byte. ต้องเริ่ม Dev tunnel ด้วย config ปกติก่อนใช้งานต่อ; การยืนยัน restart ปกติบันทึกเป็น recovery check แยกต่างหาก.
- signed tag `v1.2.2` ชี้ commit `f8f1d93930882dc3e669dab0a05b4bd5c1834bef`; `git verify-tag --verbose` ผ่านด้วย GPG EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- [GitHub Release v1.2.2](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.2) แนบ ZIP และ external `SHA256SUMS`; SHA-256 ZIP คือ `e9582153c57458e3ca73a4c169f46653662377b004c9c2ee552824c4ffce5dc5`.
- ดาวน์โหลด asset กลับจาก GitHub แล้ว `sha256sum -c SHA256SUMS` และ `unzip -t` ผ่านครบ.

## v1.2.0 — Local Hands read-only released (22 กันยายน 2026)

- ทดสอบ deployment `/home/somchaip/hermes-mcp-bridge-v1.2.0-rc` ผ่าน Secure MCP Tunnel; discovery พบ 22 tools (base 19 + Hands 3) และ `bridge_diagnostics` ไม่มี `config_warnings`.
- รอบ ext4: `hands_health` เป็น available; list แสดงเฉพาะไฟล์/ไดเรกทอรีที่อนุญาต, ซ่อน `.env` และ symlink `escape`; read `allowed.txt` และ `nested/allowed.txt` ได้ fixture ที่คาดไว้.
- รอบ DrvFS ที่ `/mnt/e` (mount รายงาน `9p`/DrvFS): ได้ผล read/list/deny และ audit-redaction แบบเดียวกับ ext4. ไดเรกทอรี Windows ที่เปิด case-sensitive และมีทั้ง `A.txt`/`a.txt` ถูก `hands_list` ปฏิเสธแบบ fail-closed.
- deny matrix ปฏิเสธ `.env`, `binary.txt`, `escape`, traversal, absolute path และ normalized path; audit ไม่บันทึก secret, fixture content, file name หรือ absolute fixture path.
- ทดสอบ critical fallback โดย Hermes หยุดและตั้ง `codex.binary` เป็น `/definitely-missing-codex`: Hermes/Codex health ใช้ไม่ได้ตามคาด ขณะที่ Hands health/list/read ยังทำงานได้; ไม่ได้ submit task ไปยัง Hermes หรือ Codex.
- คืน config และบริการแล้ว `./bridge.sh doctor`, `./bridge.sh codex-doctor` และ diagnostics ผ่าน; cleanup เสร็จและ production Local Hands กลับสู่ `disabled` โดย workspaces ว่าง.

หลักฐาน provenance: live acceptance ทำบน checkout ที่สะอาด `9d00431975a61dc7fd67b521180f4e8669d84479`; `uname -r` = `6.18.33.2-microsoft-standard-WSL2`; WSL `2.7.14.0` (kernel package `6.18.33.2-2`, WSLg `1.0.73.2`); Windows `10.0.26300.9539`.

- released เป็น signed tag `v1.2.0` ที่ commit `bd56bafd4fcefcfbdf26699ab281cc1a6798bfc9`; GPG verify ผ่านด้วย EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`.
- GitHub Release แนบ `hermes-mcp-bridge-v1.2.0.zip` และ `SHA256SUMS`; SHA-256 ของ ZIP คือ `621db6718323fb0639c67a9eac677af23de31a4f0f6e4d09b413d05f82960d08`.
- download asset กลับจาก GitHub แล้ว `sha256sum -c SHA256SUMS` และ `unzip -t` ผ่านครบ.

## v1.0.1 — maintenance release acceptance (21 กันยายน 2026)

- เชื่อมผ่าน `Hermes Local Bridge` จาก deployment `/home/somchaip/hermes-mcp-bridge-v1.0.1` ได้สำเร็จ
- `bridge_status` ยืนยัน state mode `0700`, audit เปิดใช้งาน, ไม่มี `config_warnings` และ Codex watchdog ทำงานทุก 15 วินาที
- `hermes_health` ยืนยัน authentication ที่ `127.0.0.1:8642`; `codex_health` ยืนยัน Codex CLI `0.155.1`, workspace policy และ approval TTL 3,600 วินาที
- Codex job แบบ `read-only` ที่ห้ามแก้ไขไฟล์และห้ามใช้เครือข่ายจบด้วย exit code `0` และตอบ `V101_READ_ONLY_ACCEPTANCE_OK`; audit บันทึก lifecycle แบบ redacted
- signed tag `v1.0.1` ถูก GitHub ยืนยัน signature แล้ว; release archive ผ่าน `sha256sum -c` ด้วย SHA-256 `a20a07aaeb0baeb885c85223dab9eba61c8a0ce1be20bb83d0e422faaa45c9d3`

## v1.0.0 — release deployment health check (21 กันยายน 2026)

- เชื่อมผ่าน `Hermes Local Bridge` จาก deployment ที่ checkout signed tag `v1.0.0` ได้สำเร็จ
- `bridge_status` ยืนยัน state mode `0700`, watchdog ทำงานทุก 15 วินาที, audit เปิดใช้งาน และไม่มี `config_warnings`
- `hermes_health` ยืนยัน authentication ที่ `127.0.0.1:8642`, capabilities `run_submission`, `run_status`, `run_stop`, `run_approval_response` และ durable idempotency 86,400 วินาที
- `codex_health` ยืนยัน Codex CLI `0.155.1`, workspace policy `/mnt/e/Projects/OpenHDK-validation`, model allowlist `gpt-5.6-sol`/`gpt-5.6-terra`/`gpt-5.6-luna` และ reasoning `low`/`medium`/`high`
- tag `v1.0.0` ถูก GitHub ยืนยัน signature แล้ว; SHA-256 ของ archive คือ `04421690f877807975810dfeffb29ec6412d8313103409cfd5713300e32de793`

## v1.1.0 approval-event SSE POC — deferred (21 กันยายน 2026)

- `GET /v1/runs/{run_id}/events` ผ่าน authentication ด้วย `HTTP 200 text/event-stream`; event ทุกตัวมี `run_id` ที่ตรงกับ run ที่ subscribe.
- POC read-only เห็น `message.delta`, `reasoning.available` และ `run.completed`; POC terminal `true` เห็น `tool.started`, `tool.completed`, `message.interim` และ `run.completed`.
- stream มี message/output/reasoning payload ด้วย จึงไม่เหมาะให้ relay ผ่าน MCP; bridge ต้องไม่ทำ general output streaming.
- หลังตั้ง `approvals.mode: manual` และ restart Hermes, terminal `true` ยังจบทันทีโดยไม่มี approval event หรือ `request_id`.
- ข้อสรุป: SSE transport ใช้ได้ แต่ approval-event contract สำหรับ API profile ยังพิสูจน์ไม่ได้; deferred integration ตาม `ROADMAP.md` และไม่เพิ่ม approval MCP tool.

## v1.0.0-rc.2 — full acceptance (21 กันยายน 2026)

- `bridge_status` ยืนยัน local-only heartbeat, schema ไม่มี warning, discovery มี 19 tools และ Hermes/Codex health ผ่าน
- Hermes read-only ตอบ `V100RC2_HERMES_OK`; ส่ง request ID เดิมซ้ำแล้ว replay locally โดยไม่สร้าง run ซ้ำ
- Codex read-only ที่ `gpt-5.6-sol` + `low` จบ exit code `0` และตอบ `V100RC2_CODEX_OK`
- Codex workspace-write ผ่าน local terminal approval: สร้าง/ตรวจ/ลบ `.hermes-mcp-bridge-v100rc2-acceptance.txt` แล้วตรวจว่าไม่มีไฟล์เหลือ
- write job ถูกรายงาน `unknown_exit` เนื่องจาก bridge restart/recovery ระหว่าง process; JSONL output และ audit ยืนยัน create/verify/delete/verify ครบ จึงไม่เดา exit code เป็น `completed`
- Codex read-only cancellation ระหว่าง `sleep 120` จบเป็น `cancelled`

watchdog timeout และ `unknown_exit` recovery ได้ผ่าน WSL2 live acceptance แล้วใน v0.8.0 บน policy/runtime เดียวกัน. Hermes upstream approval-event integration เป็นงาน v1.1.0 แยกต่างหาก.

## v0.9.0 — partial live acceptance (21 กันยายน 2026)

- `bridge_status` ผ่าน Secure MCP Tunnel โดยรายงาน `upstream_checked: false` สำหรับทั้ง Hermes และ Codex; schema migration ไม่มี `config_warnings` และ discovery พบ 19 tools.
- ตั้ง `hermes.stale_run_seconds` ชั่วคราวเป็น 1 วินาที แล้วส่ง Hermes task read-only ที่รอ 30 วินาที: ระหว่างรัน status มี `age_seconds: 10` และ `stale: true`.
- Bridge ไม่ส่ง stop; Hermes จบเองเป็น `completed` พร้อมยืนยันว่าไม่แตะไฟล์/เครือข่าย. Audit เก็บ submit แบบ redacted เท่านั้น.

`approval_stale` มี regression coverage แต่ยังไม่ได้สร้าง Hermes approval workflow จริงในการ acceptance เพื่อหลีกเลี่ยงผลกระทบจาก upstream approval; คืน threshold production ก่อนใช้งานต่อ.

ข้อสรุปเดิมจาก `run_approval: null` ถูกแก้ใน v0.9.1: Hermes ใช้ capability canonical ชื่อ `run_approval_response`. v1.0.0 ตรวจพบ capability แล้ว แต่ upstream approval-event SSE acceptance เป็นงาน v1.1.0.

วันที่ 14 กันยายน 2026 ทดสอบผ่าน Secure MCP Tunnel ไปยัง Hermes API `127.0.0.1:8642` ที่มี Bearer authentication โดยไม่เปิดพอร์ตสู่ public network

ผ่านครบ 10 tools: health, model info/catalog, recent tasks, usage summary/export, submit, status, result และ cancel

- `usage_export` ตรวจว่าไม่มี prompt, output หรือ API key
- smoke run ตอบ `HERMES_CANCEL_TEST_OK` ผ่าน submit/status/result
- cancel semantic: run `run_8980a67a66a94135a46f8b9d87dc4389` รัน `sleep 60` แบบไม่มี file/network operation แล้วเปลี่ยน `stopping` เป็น `cancelled`

ข้อจำกัด: model catalog ของ Hermes Runs API ประกาศ virtual model `hermes-agent` เพียงรายการเดียว แม้ config ปัจจุบันใช้ `deepseek/deepseek-v4-flash-0731` กับ provider `nous`

## v0.5.0 — 20 กันยายน 2026

ผ่าน Secure MCP Tunnel ไปยัง bridge `/home/somchaip/hermes-mcp-bridge-v0.5.0`:

- discovery 17 tools: Hermes 10, Codex 6 และ `bridge_diagnostics`
- `bridge_diagnostics`: Hermes authenticated, Codex CLI `0.155.1`, allowed workspace `/mnt/e/Projects/OpenHDK-validation`, state mode `700`, audit enabled
- Codex read-only: `git status --short` สำเร็จโดยไม่มีการแก้ไขไฟล์ และ `state/audit.jsonl` ถูกสร้าง
- Codex workspace-write: ผู้ใช้ตรวจ prompt และพิมพ์ `APPROVE` ใน WSL terminal; job สร้าง/ตรวจ/ลบ `.hermes-mcp-bridge-v050-acceptance.txt` สำเร็จและยืนยันว่าไฟล์หายไป
- Codex cancel: job read-only ที่รอ 60 วินาทีถูก cancel ขณะรันและจบด้วย `cancelled`

หมายเหตุ: write job แสดง `recovered_after_restart: true` เพราะ terminal helper เริ่ม process แล้ว tunnel-backed bridge process อ่านสถานะต่อจาก SQLite; bridge ไม่ส่ง job ซ้ำและไม่อ้าง exit code ที่ไม่ได้สังเกตเอง

## v0.6.0 — 20 กันยายน 2026

ผ่าน Secure MCP Tunnel ไปยัง bridge `/home/somchaip/hermes-mcp-bridge-v0.6.0`:

- discovery 18 tools รวม `bridge_audit_recent`
- `codex_health` รายงาน policy ต่อ workspace และ approval TTL 3,600 วินาที
- read-only acceptance จบสำเร็จ; audit export แสดง lifecycle `submit`, `start`, `finish` แบบ redacted
- workspace-write job ที่ยังไม่อนุมัติคืน expiry/policy context; `codex_cancel_task` เปลี่ยนเป็น `denied` โดยไม่เริ่มงาน
- policy probe ที่ workspace `/mnt/e` ถูกปฏิเสธก่อนเริ่มด้วย allowlist guard

## v0.7.0 — 20 กันยายน 2026

ผ่าน Secure MCP Tunnel ไปยัง bridge `/home/somchaip/hermes-mcp-bridge-v0.7.0`:

- `bridge_diagnostics` ยืนยัน Hermes authenticated, Codex CLI `0.155.1`, workspace policy และ audit state mode `700`
- `codex_health` แสดง allowlist ต่อ workspace: `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`; reasoning effort `low`, `medium`, `high`
- งาน `read-only` ที่ไม่ส่ง override จบด้วย `V070_DEFAULT_OK` และ exit code `0`
- งาน `read-only` ที่ร้องขอ `model: gpt-5.6-sol` และ `reasoning_effort: high` จบด้วย `V070_MODEL_POLICY_OK` และ exit code `0`
- `bridge_audit_recent` แสดง lifecycle `submit → start → finish` พร้อม model/effort ที่ร้องขอ โดยไม่มี prompt, output หรือ credential

ระหว่าง acceptance พบว่า display name `GPT-5.6 Sol` ใช้เป็น model ID ไม่ได้และถูก Codex CLI ปฏิเสธ; แก้เป็น `gpt-5.6-sol` แล้วผ่าน จึงต้องใช้ model ID จริงใน `allowed_models` เสมอ

## v0.8.0 — full live acceptance (21 กันยายน 2026)

ผ่าน Secure MCP Tunnel ไปยัง bridge `/home/somchaip/hermes-mcp-bridge-v0.8.0`:

- `bridge_diagnostics` และ `codex_health` ยืนยัน Hermes authenticated, Codex CLI `0.155.1`, workspace allowlist, model/effort allowlist และ watchdog ทำงานอยู่ทุก 15 วินาที
- งาน `read-only` ที่ตั้งใจรอ 120 วินาทีเริ่มทำงานจริง (Codex เรียก `sleep 120`) แล้ว `codex_cancel_task` ยุติงานเป็น `cancelled`
- `codex_task_status` และ `codex_task_result` ยืนยันสถานะปลายทาง `cancelled`; audit แสดง `submit → start → cancel` แบบ redacted และไม่มีการแก้ไขไฟล์หรือเรียกเครือข่าย
- ลด `max_runtime_seconds` ชั่วคราวเหลือ 5 วินาทีแล้วส่งงานที่รอ 120 วินาทีโดยไม่ poll; watchdog ยุติงานเองเป็น `timed_out` และ audit บันทึก `cancel` outcome เดียวกัน
- คืน runtime policy เป็น 1,800 วินาที, restart tunnel ระหว่างงาน read-only `sleep 30`, แล้วเชื่อมต่อใหม่หลังงานจบ: status เป็น `unknown_exit`, result มี `recovered_after_restart: true` และ audit บันทึก `finish` outcome `unknown_exit` พร้อม `exit_code: null`

ทั้ง timeout watchdog และ restart recovery ผ่านแล้ว; คืน policy production เป็น `max_runtime_seconds: 1800` ก่อนจบ acceptance.


## 19 ตุลาคม 2026 — OpenCode execution (release candidate v1.2.5 ที่ยังไม่แท็ก; PR #40)

Code head: `ee62fe84e0474ccd34ccda1b42ba7e59700da479`; source worktree แยกจาก runtime
ผลนี้ไม่ใช่ release claim และไม่แก้หลักฐาน v1.2.4 ที่บันทึกไว้ก่อนหน้า
WSL ผ่าน 162/162 tests ด้วย `-W error::ResourceWarning`, shellcheck และ Bash syntax
[CI ที่ code head เดียวกัน](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/39209783419) ผ่าน

ใช้ actual `OpenCodeTasks` controller กับ OpenCode CLI v2.0.32 และ
`opencode-go/glm-5.3-flash` ใน workspace/state ชั่วคราวแยกกัน
กำหนด runtime 60 วินาที, per-stream output cap 262144 bytes ด้วย in-memory config
ใช้ native policy เดิม ไม่ส่ง `--auto` และไม่เปลี่ยน permission config

| ข้อทดสอบ | หลักฐานและผล |
| --- | --- |
| Submit/status/result | native response parsed จาก JSONL; terminal `completed` |
| Request replay | input และ request ID เดิมคืน job/session เดิม ไม่เรียก model ซ้ำ |
| Session context | prompt ถัดไปใช้ session เดิมและตอบ token ที่ให้จำได้จริง |
| Native read/edit | ใช้ absolute fixture path; tool state `completed`; ตรวจ bytes ว่า `BEFORE → AFTER` จริง |
| Resumed edit | session เดิมแก้ไฟล์เดิมเป็น `SECOND`; ตรวจ bytes ตรงค่า ไม่อาศัยคำกล่าวของ model |
| Cancel | พบ CLI child ของ worker ก่อนส่ง cancel; terminal `cancelled` และ child exit ยืนยันด้วย owned process identity |
| MCP fixture | actual SDK stdio initialize/discovery = 33; submit/replay/status/result/resume/cancel/recent ผ่านด้วย fixture CLI |

ข้อจำกัดที่ยังคงบันทึก:

- การแก้ fixture ด้วย relative path รอบแรก failed เพราะ native tool แจ้ง file not found
  bridge จัดเป็น `tool_error_event` และไฟล์ไม่เปลี่ยน
  การทดสอบ absolute path สองรอบผ่าน แต่ยังไม่พิสูจน์สาเหตุภายในของ relative-path failure
  ให้ระบุ workspace และ absolute target path ในคำขอแก้ไฟล์ที่ต้องการความชัดเจน
- ไม่อ้าง HTTP API, ACP, native permission reply, read-only sandbox หรือ network isolation
- การทดสอบ model จริงผ่าน controller และการทดสอบ MCP ผ่าน fixture เป็นคนละชั้น
  ยังไม่อ้างว่า model จริงถูกสั่งผ่าน authenticated Dev tunnel ใน Work chat รอบนี้
- Production ยังคง v1.2.3 และ Dev ยังเป็น v1.2.4 candidate เดิม
  ยังไม่ได้ติดตั้งหรือ restart ทั้งสอง runtime, ไม่แตะ shared OpenCode service
  temp fixtures และ process ที่สร้างเพื่อทดสอบถูก cleanup
- Dev ไม่มี supervisor สำหรับ restart อัตโนมัติที่ตรวจพบ
  การเปิด candidate ใหม่ผ่าน tunnel ต้องใช้ launcher/env เดิมของ operator
  ห้ามอ่าน/คัดลอก key จาก process environment และห้ามใช้ production profile แทน Dev

ขั้นรับรองที่เหลือ: เปิด Dev candidate ที่เตรียมจาก PR head, refresh discovery
แล้วตรวจ 33 tools และสั่งงาน benign หนึ่งเที่ยวผ่าน Dev plugin จริง
ดูขั้นปฏิบัติใน [OPENCODE-TH.md](OPENCODE-TH.md)

Final code head `85e3bcdb8696517c18b48657dfdd2244f43f824a` adds the cleanup-unconfirmed
regression and redacted audit checks; [CI passes with 163 tests](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/39210918304).
The earlier native-model proof above remains scoped to `ee62fe8`.
New Dev candidate preparation paused at the Hermes local terminal approval gate
for an operator-launcher draft. That draft contains unverified profile/key assumptions
and is not an approved activation procedure. At that checkpoint candidate readiness had not been recorded. Authenticated
Dev tunnel acceptance remains pending. No current Dev/production route was switched.


### Final source/candidate checkpoint — 19 October 2026

- Code head `e7add7e594fb2cc0029dd53b628c85f9a7c1a87c`: WSL **164/164** tests and shellcheck pass. [Exact-head CI](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/39212518227) passes.
- The isolated git-worktree candidate at `~/hermes-mcp-bridge-opencode-dev` is prepared at that code head with its own venv and fresh private state. Its config is mode 0600; state/workspace are mode 0700.
- Execution is enabled only for `~/hermes-opencode-dev-workspace` and model `opencode-go/glm-5.3-flash`. Prompt/runtime/output limits are 32000 characters / 1800 seconds / 524288 bytes per stream.
- Candidate config validation returns an empty warnings list. Actual SDK stdio against its own `bridge.sh serve` discovers **33 tools**. `bridge_version` reports that git revision and `opencode_health` reports `opencode v2.0.32`.
- The launcher-writing operation was cancelled without approval or execution. No launcher was written, no substitute activation was attempted, and no approval remains pending for that run.
- Current Dev and production routes remain unchanged. The candidate is ready locally; the remaining gate is operator-controlled Dev profile selection, restart from the existing authenticated environment, plugin discovery refresh and a real Work-chat task over that Dev tunnel.
- The later documentation-only commit does not change the pinned candidate code. Real model read/edit/context evidence remains scoped to the earlier `ee62fe8` record above; the final source is covered by the full suite and candidate stdio verification.


### Work-chat Dev tunnel acceptance — 19 October 2026: PASS within scope

This supersedes the pending-activation status at the preceding historical checkpoint.
The operator selected the prepared candidate in `hermes-wsl-dev`, restarted the Dev
tunnel and refreshed plugin tools. Parent Work chat then called the real Dev plugin:

- Callable registry contains **33 Dev tools**, including all six OpenCode tools.
  This is parent registry evidence, not a raw wire `tools/list` capture.
- `bridge_version.source_kind` = `git-worktree`; `source_revision` =
  `e7add7e594fb2cc0029dd53b628c85f9a7c1a87c`; `opencode_health` reports v2.0.32.
  The version response's canonical `mcp_discovery_count` remains 27 as documented.
- Model = `opencode-go/glm-5.3-flash`; workspace = `~/hermes-opencode-dev-workspace`.
- Submit/status/result: `oct_601b8c9f62f8d20254a77dce` completed, exit 0,
  response `OC_TUNNEL_READY`.
- Resume: `oct_b2c34f716a3c07be14252aaf` completed in the same bridge-owned
  session and returned the previously remembered token without it being repeated
  in the follow-up prompt.
- Native write in that same session: `oct_740bdef27eed489b36f0afff` completed,
  exit 0; native glob found no existing target, and native write created
  `workchat-acceptance-20261019-b7.txt` using its absolute path.
- Independent read-only verification through Hermes compared actual file bytes:
  exactly `b'OC_TUNNEL_EDIT_OK\n'` (18 bytes), `exact_match: True`.
  The verification also observed database mode 0600 and task-log directory 0700.
- Replaying the identical first request returned its original job/session IDs.
  `opencode_recent_tasks` then listed exactly the three completed jobs above.

No production activation, release or tag is claimed. This run proves real-model
submit/result, session continuity, replay/recent and native file creation through
an authenticated Dev tunnel. Cancellation evidence remains scoped to the earlier
controller run; native permission-required coverage remains fixture-only, not a
live permission interaction. No permission configuration was changed by this test.


## v1.2.5 — released (19 October 2026)

- Signed annotated tag `v1.2.5`: object `11420f1ae968244195701b296db2f8ce419b793a`, peeled commit `6fbcd7ef278d5e45a95b7328c719c5b01cbcf522`; EDDSA fingerprint `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`. Local and fresh-fetch remote `git verify-tag` pass; GitHub reports the signature valid.
- [GitHub Release v1.2.5](https://github.com/sc28249782/hermes-mcp-bridge/releases/tag/v1.2.5) publishes exactly `hermes-mcp-bridge-v1.2.5.zip` and external `SHA256SUMS`. ZIP SHA-256: `1f1c8a583cf7f51a88ec35ca3023c86342220f5baba37faed3f1724b04bf8d5f`.
- Built from the signed tag: 79 files under the single root `hermes-mcp-bridge-v1.2.5/`, no private config/state/venv/env/git/cache entries. Fresh-download `sha256sum -c SHA256SUMS`, `unzip -t` and byte comparison against the built assets pass.
- Extracted identity: version `1.2.5`, release identifier `v1.2.5`, source kind `release-archive`, embedded build input `a666d626da1fe716ce4b259d49eedfc3f97acc7d`, canonical default discovery 27. The signed tag identifies the final commit; the embedded revision identifies its reviewed build input.
- Scope: opt-in OpenCode execution from PR #40; release preparation from PR #41. Candidate WSL/archive suite 164/164 and discovery 27/28/33 pass; exact-head CI `39224170181` passes. Work-chat proof remains scoped to the recorded Dev candidate; cancellation remains controller evidence and permission-required remains fixture-only.
- Production remains v1.2.3; active Dev remains the tested git-worktree candidate. Publishing does not change profiles, runtimes or permission configuration. This post-tag documentation record does not modify the tag or assets.

### Deployment checkpoint — production อัปเกรดเป็น v1.2.5 (19 ตุลาคม 2026, ~18:44 +07)

Production deployment อัปเกรดเป็น released v1.2.5 แล้วในวันเดียวกัน ตรวจแบบ read-only ผ่าน plugin production จริง ย่อหน้า "Production remains v1.2.3" ข้างบนคือบันทึก ณ วันเผยแพร่ ก่อนการอัปเกรด คงไว้ตามหลักฐานเดิม (checkpoint เดียวกันแบบสังเขปใน [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md))

- Identity: `bridge_version` — version `1.2.5`, release identifier `v1.2.5`, source kind `release-archive`, build provenance `release`, embedded build input `a666d626da1fe716ce4b259d49eedfc3f97acc7d`
- State/watchdog: `bridge_status` — state path `~/hermes-mcp-bridge-v1.2.5/state`, mode `0700`, ไม่มี config warnings, watchdog ทำงาน
- Backend health: `hermes_health` — authentication verified, durable idempotency 86,400 วินาที; `codex_health` — `0.160.0` ok; `opencode_health` — `v2.0.32` ok
- Registry: parent tool registry แสดง 33 tools (นับฝั่ง parent ไม่ใช่ raw `tools/list` บน wire)
- Jobs: `opencode_recent_tasks` ok พร้อม `jobs` ว่าง; Local Hands disabled
- Scope: identity/health/discovery และ execution API listing เท่านั้น ไม่มีการส่ง production model task ระหว่าง checkpoint นี้ และ checkpoint นี้ไม่ถือเป็นการยอมรับ production acceptance

### Fresh artifact chain re-verification (19 ตุลาคม 2026)

Automation ฝั่ง maintainer ตรวจ artifact chain ของ v1.2.5 ซ้ำทั้งสายจากข้อมูลดิบใหม่ทั้งหมด ไม่ใช้ไฟล์ที่เคยดาวน์โหลดหรือ tag ที่มีอยู่ก่อน ผลตรวจผ่านทุกรายการ บันทึกนี้เป็นการตรวจโดย automation ไม่ใช่การอนุมัติโดย external reviewer ภายนอก

- Fresh fetch จาก origin ลง temporary bare repository ที่แยกจาก working copies เดิม (ไม่แตะ tag ที่มีอยู่): `git verify-tag v1.2.5` แสดง `Good signature` ด้วย EDDSA key `C4E9AFA9C97FC94CA2448E9218BDAEA561529B86`; tag object `11420f1a…` และ peeled commit `6fbcd7e…` ตรงกับค่าที่บันทึกไว้ใน section นี้
- ดาวน์โหลด asset ใหม่ทั้งสองไฟล์จาก GitHub Release ลง scratch directory ใหม่: `sha256sum -c SHA256SUMS` รายงาน `OK` และ digest ฝั่ง GitHub ของ asset ทั้งสองตรงกับที่ดาวน์โหลด
- ZIP structure: 79 entries ใต้ root เดียว `hermes-mcp-bridge-v1.2.5/` ไม่มี duplicate entry และไม่มี traversal entry ไม่พบ symlink หรือ special file และไม่พบ `.git/`, `.venv/`, `__pycache__/`, `state/`, `.env`, `bridge-config.json*`
- สร้าง `git archive --format=zip --prefix=hermes-mcp-bridge-v1.2.5/ v1.2.5` ใหม่จาก signed tag ใน bare repository แล้ว `cmp` กับ ZIP ที่ดาวน์โหลด: byte-identical ที่ SHA-256 `1f1c8a583cf7f51a88ec35ca3023c86342220f5baba37faed3f1724b04bf8d5f` (271,346 bytes)
- แตกไฟล์จาก ZIP ที่ดาวน์โหลดแล้วตรวจ stamp: version `1.2.5`, identifier `v1.2.5`, provenance `release`, embedded build input `a666d626…`, discovery 27 จากนั้นรัน version CLI offline ด้วย venv เดิมของ working copy จาก tree ที่ไม่มี `.git`: `ok: true`, source kind `release-archive`, discovery 27 (ไม่มี network หรือ model call)
- ยืนยันความต่างสองค่าตาม runbook: signed tag คือ authority ของ final commit `6fbcd7e…` ส่วน embedded revision `a666d626…` คือ reviewed build input ซึ่งเป็น ancestor ของ final commit (ยืนยันด้วย `git merge-base --is-ancestor`)
- ขอบเขต: ตรวจเฉพาะ artifact chain ไม่มีการแก้ tag, assets, release หรือ runtime สถานะ independent external reviewer approval ยังค้างตาม [ROADMAP.md](ROADMAP.md)

### External artifact audit approval (19 ตุลาคม 2026)

Operator ส่งรายงาน external review ของ Hermes Agent สำหรับ [PR #45](https://github.com/sc28249782/hermes-mcp-bridge/pull/45) ที่ head `c3754c9` เมื่อ 19 ตุลาคม 2026 เวลา 19:32 +07.
Reviewer รายงานผลตรวจจาก fresh inputs ของตนเอง: fetch tag ใน temporary bare repository, ตรวจ signature, ดาวน์โหลด assets ทั้งสองใหม่, ตรวจ checksum/ZIP structure, rebuild เทียบ byte-identical, ตรวจ ancestry และรัน version CLI offline จาก archive ที่แตกใหม่.
ผลทุกรายการผ่านและตรงกับ record ของ automation.
Reviewer ให้ verdict `APPROVE`; external artifact-audit follow-up ของ v1.2.5 ปิดแล้ว.
ข้อความ pending ใน checkpoint automation ข้างบนเป็นสถานะก่อน review นี้.
การอนุมัตินี้ไม่ขยายขอบเขตไปยัง production model-task acceptance หรือ SPEC privacy contract review.

### Privacy candidate preparation only — not Dev tunnel acceptance (19 ตุลาคม 2026)

Candidate pin `db00968230fd4aee5690c361b11c8bc8fc36dabc` เตรียมใน isolated detached worktree บน WSL แล้ว.
Project-venv full suite 183/183, privacy tests 18/18 และ shellcheck ผ่าน.
Local SDK stdio fixture แสดง 27 tools และ filtered status metadata 415 bytes; ไม่ส่ง synthetic raw approval/error marker.
นี่เป็น in-process fake Hermes transport; ไม่ใช่ actual Dev tunnel, Hermes HTTP หรือ model acceptance.
Dev เดิมยัง pin `e7add7e`; production/profile/auth references ไม่ถูกเปลี่ยน.
Live step รอ operator เปิด ephemeral command override จาก authenticated terminal.
วิธีเปิดและคืน route อยู่ใน [PRIVACY-DEV-ACCEPTANCE-TH.md](PRIVACY-DEV-ACCEPTANCE-TH.md).
Privacy follow-up ยังเปิดอยู่.
