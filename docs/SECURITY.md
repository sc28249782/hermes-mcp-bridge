# Security policy

## Supported versions

เฉพาะ release ล่าสุดได้รับ security fixes

## Reporting a vulnerability

อย่าเปิดเผย API keys, credentials, local paths ที่อ่อนไหว หรือ exploit ที่ใช้งานได้จริงใน public issue กรุณาติดต่อผู้ดูแล repository ผ่านช่องทาง private security reporting ของ GitHub เมื่อเปิดใช้งาน

## Security boundaries

- Hermes API ต้อง bind ที่ `127.0.0.1` และใช้ bearer key
- Codex workspace จำกัดด้วย canonical allowlist
- ไม่รองรับ `danger-full-access` (Codex)
- งาน `workspace-write` ของ Codex ต้องผ่าน local terminal approval
- agent ไม่มี MCP tool สำหรับอนุมัติตัวเอง
- ห้าม commit `bridge-config.json`, `.env`, `state/`, logs และ tunnel key
- Release production ต้องเผยแพร่ checksum และ signed tag ที่ตรวจสอบได้; private signing key อยู่กับ maintainer เท่านั้น

## OpenCode adapter (`opencode_health`)

`opencode_health` (รวมใน released v1.2.4 แล้ว — 18 ตุลาคม 2026; deployment ที่ยังรัน v1.2.3 จะไม่มี adapter นี้จนกว่า operator จะอัปเกรด) เป็น disabled by default: เมื่อไม่กำหนด section `opencode` หรือ `enabled` เป็น `false` ทุก health check fail closed โดยไม่ spawn process และไม่มีการเรียก network/model/auth. การเปิดใช้ต้องกำหนด `opencode.binary` เป็น absolute path (ไม่เกิน 4096 ตัวอักษร ไม่มี control characters ต้องเป็น regular executable file) พร้อม `version_timeout_seconds` (1-120) และ `max_output_bytes` (1024-1048576); ไม่มีการเปิดใช้อัตโนมัติ

ขอบเขต OpenCode ที่เผยแพร่ใน v1.2.4 เป็น health เท่านั้น; execution รวมใน `main` แล้วผ่าน PR #40 และเผยแพร่ใน v1.2.5 แล้ว อธิบายใน section ด้านล่าง ส่วน native permission replies และ event subscriptions ยังไม่รองรับ. bridge ไม่เพิ่ม sandbox — executable ที่กำหนดรันด้วยสิทธิ์เต็มของ bridge process และอ่าน global configuration/credentials ได้ จึงเปิดใช้เฉพาะ binary ที่ตรวจแล้ว. runner ไม่ส่ง `--auto`; flag `--standalone` ทำให้ CLI ทำงานเป็น exclusive in-process server ไม่ใช่ sandbox

Local Hands read-only (`hands_health`/`hands_list`/`hands_read`) released ใน v1.2.0 และ disabled โดยค่าเริ่มต้น; mutation/execution ยังเป็น deferred track ที่ v1.3.0 สงวนไว้ (ดู ROADMAP.md) ขอบเขตที่อนุมัติไว้สำหรับ implementation คือ workspace/capability allowlist, local digest-bound approval, protected paths/names, baseline no deletion และไม่มี model-relayed nonce เป็น authorization ห้ามนำ allow-by-default deny-list sandbox, read-anywhere policy, shell-bypass accepted gap หรือ dynamic MCP-to-MCP trust bypass มาใช้

Execution ที่อ้างว่า no-delete/no-unapproved-truncate ต้องมี kernel enforcement ที่ probe ได้จริง เช่น [Landlock](https://docs.kernel.org/userspace-api/landlock.html) หรือกลไกเทียบเท่า Landlock เริ่มใน Linux 5.13 และยังขึ้นกับ kernel configuration/boot/ABI จึงห้ามสรุปว่ารองรับเพียงเพราะเป็น WSL2 หรือดูเฉพาะเลข kernel หาก enforcement ที่ profile ต้องใช้ไม่มี ให้ปิด profile แบบ fail closed Exact `hands_write`/`hands_patch` ที่วางแผนไว้สำหรับ v1.3.0 (ยังไม่มีใน release ปัจจุบัน) จะผูก local approval และ digest เป็น operation แยกซึ่งแตะได้เฉพาะ target ที่อนุมัติ

รายละเอียด threat model และข้อจำกัดดู `HERMES-MCP-BRIDGE-TECHNICAL-ARCHITECTURE-TH.md`, `CODEX-WSL2-TH.md` และ `LOCAL-HANDS-ARCHITECTURE-TH.md`

`deny_prompt_patterns` ใน workspace policy เป็น guard ก่อนเริ่มงานเท่านั้น ผู้โจมตีอาจเปลี่ยนถ้อยคำเพื่อหลบ pattern ได้ จึงห้ามถือว่าเป็น command sandbox หรือ authorization boundary; allowlist, Codex sandbox และ local approval เป็น controls ที่บังคับใช้จริง.

## OpenCode execution (released v1.2.5 — SPEC.md section 18)

ส่วน execution ที่เผยแพร่ใน v1.2.5 (รวมใน `main` ผ่าน PR #40) เปิดด้วย opt-in เดียว
`opencode.execution.enabled` ซึ่งต้องมี health adapter เปิดอยู่และมี
`allowed_workspaces`/`allowed_models` แบบ canonical ที่ไม่ว่าง พร้อมขอบเขตตัวเลขชัดเจน
ขอบเขตความปลอดภัยแตกต่างจาก Codex: executable รันด้วย **สิทธิ์เต็มของ bridge process**,
bridge **ไม่เพิ่ม sandbox**, workspace selection เป็น **cwd allowlist เท่านั้น — ไม่ใช่
filesystem หรือ network isolation**; bridge **ไม่ inject permission configuration**
(ไม่ตั้ง `OPENCODE_CONFIG*`, ไม่ส่ง flag ด้าน permission) และ native OpenCode
configuration/plugins/saved permissions ของ operator ทำงานตามปกติ ห้าม `--auto` และ
bridge ไม่เคยอนุมัติ native permission แทน: unresolved ask จบเป็น `failed` ตาม bounded
deadline หรือ `permission_required` เฉพาะเมื่อเห็น protocol event จริง การเปิดใช้จึงเป็น
trust decision แบบชัดเจนเทียบเท่าการปล่อยให้ model ทำงานในเครื่องโดยตรง output เป็น
untrusted model output, status/recent ถูก redact และ audit ไม่เก็บ prompt/output/
credentials. รายละเอียด: [OPENCODE-TH.md](OPENCODE-TH.md)


### OpenCode local data at rest (v1.2.5 execution)

OpenCode task prompts are stored as plaintext in `state/opencode-tasks.sqlite3`
(the `jobs.prompt` column). This database is mode 0600. Native stdout/stderr are
stored as plaintext files referenced by `log_path`/`err_path`, also mode 0600,
under `state/opencode-task-logs/` (0700); the state directory is 0700.
These are OS access permissions, not encryption. Redaction of audit/status/recent
responses does not remove prompts or outputs from these local artifacts.
Do not submit credentials in prompts or publish/copy state databases and task logs
into public evidence. Protect local backups with the same access controls.
Native OpenCode may retain its own sessions under its own configuration; bridge
redaction does not govern those native stores. See [OPERATIONS-TH.md](OPERATIONS-TH.md).

## Content retrieval and privacy-contract review

Result pages และไฟล์ที่ Hands policy อนุญาตอาจมีข้อมูลอ่อนไหว.
Pagination และ protected filenames ไม่ใช่ generic content-secret redaction.
Hermes แทนค่าเฉพาะ configured API key ใน upstream JSON; status ยังส่งต่อ upstream error และ approval payload.
อย่าถือว่าข้อมูลเหล่านี้เป็น metadata ที่ไม่มีเนื้อหาอ่อนไหว.
ข้อเสนอแยก audit/metadata ออกจาก content retrieval และ private operational stores อยู่ใน [PRIVACY-CONTRACT-REVIEW-TH.md](PRIVACY-CONTRACT-REVIEW-TH.md).
รายงานนั้นยังรอ review และไม่เปลี่ยน normative SPEC หรือ runtime permissions.
