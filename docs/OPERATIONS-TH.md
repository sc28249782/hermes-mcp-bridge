# คู่มือปฏิบัติการ — release v1.2.6 / production checkpoint v1.2.5

## v1.2.6 — released privacy hardening (SPEC §19)

ส่วนนี้อธิบาย hardening ใน signed release `1.2.6/v1.2.6` ที่ยังไม่ deploy production. Release assets ผ่านการตรวจหลังดาวน์โหลดแล้ว; GitHub badge เป็น `no_user` แยกจากผล GPG ที่ผ่าน. ดู [release record](RELEASE-STATUS-TH.md).
Build input คือ `e3e698a7a220bf14a8bb4d1260bf2ded7e666b56`; ไม่ใช่ final tag commit. ดู [release-preparation record](V1.2.6-RELEASE-PREP-TH.md).
Operator อนุมัติ scope v1.2.6 เมื่อ 20 ตุลาคม 2026; release preparation และ signing/publication ผ่านแล้ว; deployment decision ยังแยกกันตาม [scope decision record](PRIVACY-RELEASE-DECISION-TH.md).
Hermes task metadata จำกัด compact ASCII-escaped JSON เป็น 8,192 bytes.
Status ส่งเฉพาะ fields ที่กำหนด; error เป็นข้อความคงที่ และ approval เป็น `{"required": true}`.
ใช้ `./bridge.sh approve run_ID` หรือ `deny` ใน local terminal ตามขั้นตอนเดิมเพื่อตรวจรายละเอียดและยืนยัน exact request.
Upstream decoded JSON จำกัด 4,000,000 bytes; HTTP connect timeout 5 วินาที และ read/write/pool inactivity timeout 25 วินาที ไม่ใช่ wall-clock deadline รวม.

Codex result อ่าน snapshot ไม่เกิน 8,388,608 bytes ครั้งละไม่เกิน 65,536 bytes.
Offset และ page size ยังนับเป็น characters.
ถ้าเกิน read cap ให้ตรวจ log ในเครื่องตามสิทธิ์ที่มี; ห้ามถือว่า result ว่างหรือส่งงานซ้ำ.
Append ระหว่างคำขอไม่ขยาย read budget ของคำขอนั้น.
ผลระหว่างหลายคำขออาจเห็น output เพิ่มขึ้น.
Cap นี้ไม่จำกัด worker log capture และไม่มี automatic cleanup เพิ่ม.

| Operational store | ข้อมูลที่เก็บ | การควบคุมและ lifecycle |
| --- | --- | --- |
| `runs.sqlite3` | Cached upstream JSON รวม output/error/approval ที่ upstream ส่งมา; อาจมี input ที่ upstream echo | Database `0600`, state directory `0700`; ไม่มี artifact retention/deletion ใหม่ใน v1.2.6 |
| `codex.sqlite3`, `codex-logs/` | Prompt และ captured CLI output | Database `0600`, state/log directories `0700`; wrapper ใช้ umask `077`; read cap ไม่ใช่ disk capture cap |
| `opencode-tasks.sqlite3`, `opencode-task-logs/` | Prompt, stdout และ stderr | Database/files `0600`, directories `0700`, per-stream execution cap เดิม; v1.2.6 ไม่เปลี่ยน backend นี้ |

Private operational stores ไม่ใช่ audit log.
ป้องกัน backup ด้วย access controls เดียวกัน.
Audit rotation ไม่ลบ job artifacts.
OS permissions ไม่ใช่ encryption และไม่แยก process ที่ใช้ OS user เดียวกัน.
Native OpenCode session storage อยู่นอกขอบเขต bridge.

## Version และ provenance

```bash
./bridge.sh version
```

`version` และ MCP `bridge_version` ทำงานในเครื่องเท่านั้น: ไม่เรียก Hermes, Codex, tunnel, GitHub หรือ network. Build ที่ยังไม่ได้ stamp provenance อาจรายงาน revision เป็น `unknown` อย่างปลอดภัย; ห้ามเดา revision จากชื่อ directory และไม่ต้องส่ง path, secret, prompt หรือ output ผ่านผลนี้.

## ตรวจสุขภาพ

1. ตรวจการเชื่อมต่อ Hermes:

   ```bash
   ./bridge.sh doctor
   ```

   ผลต้องมี `"ok": true` และ `"authentication": "verified"`; หากขาด capability ตัวตรวจจะหยุดพร้อมระบุชื่อที่ขาด
2. ตรวจ Codex workspace policy:

   ```bash
   ./bridge.sh codex-doctor
   ```

   ผลต้องแสดง policy ของ workspace ตรงกับที่ตั้งใจ
3. ตรวจ state และ audit configuration:

   ```bash
   ./bridge.sh diagnostics
   ```

`diagnostics` เป็น read-only: ใช้ตรวจ API/auth ของ Hermes, Codex CLI, state directory mode และ audit log configuration เท่านั้น ไม่เริ่ม model turn หรือ Codex job

## Audit log

ไฟล์หลักคือ `state/audit.jsonl`; ไฟล์เก่าจะเป็น `audit.jsonl.1`, `.2` ตาม retention ที่กำหนดใน `bridge-config.json`

## Heartbeat และ Hermes stale labels

ใช้ `bridge_status` เพื่อตรวจว่า bridge/state/audit พร้อมใช้งานโดยไม่ยิง request ไป Hermes หรือ Codex. ใน `hermes_task_status`, `age_seconds` คืออายุของ local registration; เมื่อเกิน `hermes.stale_run_seconds` จะมี `stale: true`. งานที่ `waiting_for_approval` และเกิน `hermes.approval_stale_seconds` จะมี `approval_stale: true`. ทั้งสองค่าเป็น local warning เท่านั้น—bridge จะไม่ stop หรือ deny Hermes run เอง.

```json
"audit": {
  "enabled": true,
  "max_bytes": 1000000,
  "retention_files": 7
}
```

ไม่ควรตั้ง `enabled: false` นอกการแก้ปัญหาแบบชั่วคราว เพราะจะทำให้ไม่มีหลักฐาน lifecycle ของงานใหม่ ห้าม commit `state/` หรือ audit log เข้าสู่ GitHub

## Recovery หลัง restart

1. อย่าส่ง job เดิมซ้ำโดยเดาจากสถานะก่อน restart
2. เรียก `codex_recent_tasks` แล้วใช้ `codex_task_status` กับ job ที่เกี่ยวข้อง
3. ถ้าได้ `recovered_after_restart: true` ให้ตรวจ `codex_task_result` และ workspace ก่อนดำเนินการต่อ; หาก status เป็น `unknown_exit` ห้ามถือว่างานสำเร็จจนกว่าจะตรวจผลกระทบเอง
4. ถ้างานเป็น `workspace-write` ที่ค้าง `pending_local_approval` ให้ตรวจรายละเอียดแล้ว approve/deny ผ่าน terminal เท่านั้น
5. งาน `workspace-write` ที่ถูก approve จะมี detached worker เป็นเจ้าของ Codex process จนบันทึก exit code/terminal record แล้ว. หาก worker หายไปแต่ Codex child ยังมีชีวิต สถานะต้องคงเป็น `running` พร้อม hint `supervision_lost`; ห้ามสรุปเป็น `unknown_exit` จนกว่า child จะจบ. หากยังได้ `unknown_exit` ต้องถือว่าผลยืนยันไม่ได้และตรวจ workspace แบบ read-only ก่อนดำเนินการต่อ.
6. การ restart tunnel ไม่ได้หยุด Hermes หรือ Codex job ที่เริ่มไปแล้ว; ใช้ cancel tool หากต้องการหยุด

## Workspace policy และ approval expiry

ตรวจ policy ที่มีผลจริงผ่าน `codex_health` หรือ `./bridge.sh codex-doctor` ก่อนส่งงาน แต่ละ workspace กำหนด sandbox mode, prompt/runtime limit และ concurrency ของตัวเองได้

งาน `workspace-write` จะมีเวลาอนุมัติตาม `codex.approval_ttl_seconds` (ค่าเริ่มต้น 3,600 วินาที) เมื่อหมดอายุสถานะเปลี่ยนเป็น `expired`; ให้สร้าง job ใหม่และตรวจ prompt อีกครั้ง ห้ามพยายามเปลี่ยน state database ด้วยตนเอง

Codex watchdog ตาม `codex.watchdog_interval_seconds` (ค่าเริ่มต้น 15 วินาที) เป็น background thread ของ persistent MCP server process เท่านั้น จึงบังคับ runtime limit ได้แม้ไม่มีการ poll เฉพาะขณะที่ tunnel/bridge server ยังทำงานอยู่. การสั่ง `codex-approve` จาก CLI เป็นเพียง local approval helper และไม่ทำให้ watchdog คงอยู่; หาก server หยุดหลังเริ่ม job จะไม่มี background timeout enforcement จนกว่าจะเปิด server ใหม่ หรือมีผู้เรียก `codex_task_status` เพื่อให้ status-poll path ตรวจงาน. ระหว่าง cancellation หาก process ยังไม่จบ status จะยังเป็น `running` พร้อม `cancellation_pending: true` หรือ `timeout_enforcement_pending: true`; อย่าส่งงานใหม่จนกว่าจะได้ terminal status.

ใช้ `bridge_audit_recent` หรือ `./bridge.sh audit-recent` เพื่ออ่าน event ที่ redacted ล่าสุด การตั้ง deny prompt patterns เป็นเพียง guard ก่อนเริ่มงาน; workspace allowlist, Codex sandbox และ local approval ยังคงเป็นชั้นควบคุมหลัก

## Codex model และ reasoning effort

ก่อนส่ง override ให้เรียก `codex_health` และใช้เฉพาะ model ID/effort ที่แสดงใน `workspace_policies` ของ workspace นั้น หากไม่ส่ง `model` หรือ `reasoning_effort` Codex CLI จะใช้ค่า default local. การเลือก override ไม่ข้าม sandbox หรือ local approval สำหรับ `workspace-write`.

หาก Codex CLI ตอบว่า model ไม่รองรับ ให้แก้ `allowed_models` เป็น model ID จริงที่บัญชีใช้งานได้—not display name—แล้ว restart tunnel และตรวจ `codex_health` ใหม่.

## Migration จาก `allowed_workspaces`

หาก config เดิมใช้ `codex.allowed_workspaces` แล้วเพิ่ม `codex.workspaces`, runtime จะใช้ `workspaces` เป็น policy source of truth. ต้องย้าย workspace เดิมทั้งหมดเป็น entries แบบ explicit ก่อน restart; อย่าเพิ่ม policy ทดสอบเพียงรายการเดียวจนทำให้ policy เดิมหาย. เก็บ backup mode 0600 และลบ policy ทดสอบหลัง acceptance.

## OpenCode health adapter (released v1.2.4 — 18 ตุลาคม 2026; บันทึก ณ วันเผยแพร่: production deployment ยัง v1.2.3)

adapter ถูกรวมแล้วใน released v1.2.4 (PR #34) ซึ่งเผยแพร่แล้วผ่าน signed tag. ณ วันเผยแพร่ v1.2.4 production deployment ยังรัน released v1.2.3 จึงยังไม่จำเป็นต้องมีขั้นตอนติดตั้ง อัปเกรด หรือ restart ใด ๆ จาก release นี้ อัปเดต (19 ตุลาคม 2026): operator อัปเกรด production deployment เป็น released v1.2.5 แล้ว ตรวจ identity/health/discovery แบบ read-only ผ่าน production plugin แล้ว (ขอบเขตหลักฐานและ checkpoint อยู่ใน [RELEASE-STATUS-TH.md](RELEASE-STATUS-TH.md)). adapter เป็น disabled by default: ถ้าไม่มี section `opencode` หรือ `enabled` เป็น `false` discovery ยังอยู่ที่ canonical 27 tools และทุก health check fail closed โดยไม่ spawn process ใด ๆ เมื่อเปิดใช้ `opencode_health` ลงทะเบียนเพิ่มหนึ่ง read-only tool และ discovery เป็น 28 tools

เมื่อเปิดใช้ (adapter ตีพิมพ์แล้วใน released v1.2.4) ให้เพิ่ม section `opencode` ลงใน `bridge-config.json` แบบ merge — เก็บ key เดิมทั้งหมด ห้ามแทนที่ทั้งไฟล์:

```json
{
  "opencode": {
    "enabled": true,
    "binary": "/home/<user>/.opencode/bin/opencode",
    "version_timeout_seconds": 10,
    "max_output_bytes": 65536
  }
}
```

- `enabled` (boolean, default `false`): เปิดด้วยมือเท่านั้น ไม่มี auto-enable
- `binary` (จำเป็นเมื่อ enabled): absolute path เช่น `/home/<user>/.opencode/bin/opencode` ยาวไม่เกิน 4096 ตัวอักษร ไม่มี control characters และต้องเป็น regular executable file
- `version_timeout_seconds` (1-120, default 10) และ `max_output_bytes` (1024-1048576, default 65536): ค่านอกช่วง reject ตอนโหลด config; key ที่ไม่รู้จักถูกเตือนและข้าม

เรียกผ่าน MCP `tools/call` ชื่อ `opencode_health` (ไม่มี subcommand ของ `bridge.sh`): `{"name": "opencode_health", "arguments": {}}` เมื่อ enabled และ probe สำเร็จ ผลเป็น structured output ตรงตามนี้ (`version` มาจาก live acceptance จริง 2026-10-18):

```json
{
  "ok": true,
  "enabled": true,
  "version": "opencode v2.0.32",
  "binary": "/home/<user>/.opencode/bin/opencode",
  "version_timeout_seconds": 10,
  "max_output_bytes": 65536,
  "probe": "bounded --version with fixed argv, shell disabled, process-group cleanup",
  "execution_scope": "The probe runs the configured executable with the full privileges of the bridge process. The bridge adds no sandbox and makes no network, model, or authentication calls.",
  "runner_scope": "health probe only; native task execution requires the separate opencode.execution opt-in; event subscription and native permission replies are not implemented"
}
```

เมื่อ disabled จะ fail closed ด้วย error `OpenCode integration is disabled in bridge-config.json; review docs/SECURITY.md before enabling it`

ข้อจำกัด: live acceptance ยืนยันเฉพาะผล `--version` (`opencode v2.0.32`) execution เปิดได้เฉพาะด้วย opt-in แยกตามหัวข้อถัดไป (released v1.2.5) ส่วน native permission replies และ event subscriptions ยังไม่รองรับ bridge ไม่เพิ่ม sandbox — executable ที่กำหนดรันด้วยสิทธิ์เต็มของ bridge process และอ่าน global configuration/credentials ได้ จึงต้องอ่าน `SECURITY.md` ก่อนเปิดใช้ runner ไม่ส่ง `--auto`; flag `--standalone` ทำให้ CLI ทำงานเป็น exclusive in-process private server ไม่ใช่ sandbox OpenCode CLI ต่างจาก provider `opencode-go` ใน Hermes config

## Legacy stdio discovery guard (released v1.2.4 — ทำงานเองบน stdio ไม่ต้องแก้ config)

อาการที่อาจเจอและสาเหตุ:

- client ส่ง probe `server/discover` ผ่าน stdio แล้วได้ `-32601 Method not found` — พฤติกรรมตั้งใจตาม SPEC.md §17: guard ตอบที่ boundary ด้วย id เดิม ไม่มี params echo ไม่ถึง low-level server และไม่พิมพ์ payload ลง log ไม่ใช่ความผิดพลาดของ bridge
- probe ซ้ำยังตอบ `-32601` ทุกครั้งแต่ไม่ flood log (มีแค่ constant-text debug line)
- `initialize` / `notifications/initialized` / `tools/list` ต้องปกติ (27 tools; 28 เมื่อเปิดเฉพาะ OpenCode health ตาม §16; 33 เมื่อเปิด execution ตาม §18 — released v1.2.5) — ถ้าจำนวน tools เปลี่ยน แปลว่า guard รั่ว ให้หยุดและรีวิว `stdio_guard.py`
- method อื่นที่ไม่รู้จักยังได้ `-32602` พร้อม warning `Failed to validate request` จาก SDK เหมือนเดิม — guard ไม่กด warning ใด ๆ
- ปิด stdin (EOF) แล้ว process ต้องออก rc=0; ถ้าค้างให้เช็คว่า `guarded_stdio_streams` finally มีการ cancel forwarder และปิด reply stream ครบ — guard ครอบเฉพาะ `bridge.py serve` (stdio) tunnel/HTTP ไม่เกี่ยว

## OpenCode task execution (released v1.2.5)

ส่วน execution ตาม SPEC.md section 18 เผยแพร่ใน signed v1.2.5 แล้ว (v1.2.4 ยังคงเป็น
health-only ตามประวัติ) โค้ดรวมผ่าน PR #40 และ release preparation ผ่าน PR #41.
การเปิด execution ต้องเป็นการเลือก config โดย operator. Production checkpoint เป็น v1.2.5; publication ของ v1.2.6 ไม่เปลี่ยน configuration หรือ deployment นี้. หลักการสำหรับ
operator: เปิดด้วย `opencode.execution.enabled=true` พร้อม `opencode.enabled` +
`opencode.binary`, `allowed_workspaces` (canonical absolute path) และ `allowed_models`
(เช่น `opencode-go/glm-5.3-flash`) ไม่ว่าง; จำกัดด้วย `max_prompt_chars`,
`max_runtime_seconds`, `max_output_bytes` แยกจากของ health. executable รันด้วยสิทธิ์เต็ม
ของ bridge process — workspace allowlist คือ cwd เท่านั้น ไม่ใช่ filesystem/network
isolation; bridge ไม่ inject permission และไม่ส่ง `--auto` — native policy ของ OpenCode
ฝั่งคุณคือชั้นบังคับจริง. lifecycle: submit → status → result (untrusted ตรวจเอง) →
cancel; `completed` = native turn จบ ไม่ได้แปลว่าเป้าหมายสำเร็จ; `permission_required`
เกิดเฉพาะเมื่อเห็น protocol event ชัด มิฉะนั้นจบเป็น failed ตาม deadline; retry ด้วย
`request_id` เดิมได้ acknowledgement เดิมโดยไม่เรียก model ซ้ำ; resume ได้เฉพาะ session
ที่ bridge เป็นเจ้าของด้วย workspace/model เดิม. รายละเอียดครบ: [OPENCODE-TH.md](OPENCODE-TH.md)


### ข้อมูล OpenCode ที่เก็บในเครื่อง

prompt ของทุกงานเก็บเป็น plaintext ใน `state/opencode-tasks.sqlite3` คอลัมน์
`jobs.prompt` (mode 0600) ส่วน stdout/stderr เก็บเป็น plaintext ตาม `log_path`/
`err_path` ใน `state/opencode-task-logs/` (directory 0700, ไฟล์ 0600).
permission เหล่านี้ไม่ใช่ encryption; audit/status/recent ที่ redact แล้วไม่ได้ทำให้
ข้อมูลใน database และ task logs ถูก redact ตามไปด้วย ห้ามใส่ credentials ใน prompt
หรือเผยแพร่ database/task logs เป็นหลักฐานสาธารณะ และต้องป้องกัน backup เช่นเดียวกัน.
Native OpenCode อาจเก็บ session ของตัวเองตาม configuration เดิมด้วย.
ดู [SECURITY.md](SECURITY.md). การเลือก workspace จำกัด cwd เท่านั้น ไม่จำกัด
filesystem หรือ network และไม่เปลี่ยน native permissions.

