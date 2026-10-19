# Privacy contract review — SPEC §4 / §10

สถานะ: ข้อเสนอสำหรับ review; ยังไม่แก้ normative SPEC และยังไม่ปิด privacy follow-up.
วันที่ตรวจ: 19 ตุลาคม 2026.
Source ที่ตรวจ: `03470cbcb8b4571608dfe6fa712e674ece3180fd` หลัง merge PR #45.
ใช้เฉพาะ source และ synthetic fixtures; ไม่อ่าน production state, prompts, credentials หรือ task logs.

## ข้อสรุป

SPEC §4 ห้าม full outputs ใน MCP responses แต่ result API ส่ง output แบบแบ่งหน้าอยู่แล้ว.
หนึ่งหน้าอาจมี output สั้นครบทั้งชิ้น.
การอ่านทุกหน้าสามารถประกอบ output กลับได้.
Pagination จำกัดขนาดต่อหน้า; ไม่ใช่ redaction.

SPEC §10 ใช้คำว่า logging โดยไม่แยก audit log ออกจาก operational storage.
Implementation เก็บ prompt/output บางประเภทใน private database และ job files เพื่อทำงานต่อหรืออ่านผลภายหลัง.
การเก็บนี้ไม่ใช่ at-rest encryption.

การแก้สองข้อความนี้อย่างเดียวไม่เพียงพอ.
Hermes status ส่งต่อ upstream `error` และ `approval` ซึ่งไม่ใช่ metadata ที่รับประกันว่าไม่มีเนื้อหาอ่อนไหว.
ต้องแยกข้อเสนอปรับ contract ออกจากช่องว่าง implementation เหล่านี้.

## Source และ test mapping

| Surface | พฤติกรรมที่ตรวจพบ | หลักฐาน |
| --- | --- | --- |
| Hermes result | `Bridge.owned` ตรวจ local registration; `result` คืน output สูงสุด 24,000 characters ต่อหน้า; `fetch` cache upstream result ใน `runs.sqlite3` | [core.py](../core.py), `tests/test_bridge.py::test_auth_and_lifecycle_followup_pagination`, `test_unknown_runs_and_sessions_rejected`, `test_cached_output_survives_upstream_expiry` |
| Hermes redaction/status | `clean` แทนค่าเฉพาะ Hermes API key ที่ instance รู้จัก; `request` ใช้กับ JSON response; `status` ตัด output แต่ส่ง error สูงสุด 2,000 characters และ approval payload จาก upstream | [core.py](../core.py), `Bridge.clean/request/status`; synthetic method probe อธิบายด้านล่าง |
| Codex result/storage | `_row` ตรวจ job registration; `result` แบ่งหน้า log แต่โหลดไฟล์ทั้งชิ้นก่อน slice; prompt อยู่ใน `codex.sqlite3`; worker เก็บ output ใน `codex-logs/` | [codex_core.py](../codex_core.py), [codex_worker.py](../codex_worker.py), `test_result_page_rejects_non_integer_values`, `test_audit_is_redacted_and_records_lifecycle` |
| OpenCode result/storage | `_row_for` ตรวจ job registration; result จำกัดหน้าและอ่านภายใต้ execution cap; prompt อยู่ใน `opencode-tasks.sqlite3`; stdout/stderr อยู่ใน `opencode-task-logs/` | [opencode_tasks.py](../opencode_tasks.py), [opencode_worker.py](../opencode_worker.py), `test_private_state_files`, `test_unicode_pagination_is_lossless`, `test_redacted_metadata_and_pagination_validation` |
| Hands read/list | workspace policy และ strict resolver คุม path; `read` คืน UTF-8 content ภายใต้ byte/character limits; `list` คืนชื่อที่ผ่าน policy; ไม่ใช่ content-secret scanner | [hands_core.py](../hands_core.py), `test_list_and_read_are_bounded_and_audited_without_content`, `test_workspace_secret_filename_is_not_listed_or_read`, `test_traversal_and_symlink_escape_are_denied` |
| Audit | caller เลือก metadata ที่ส่งเข้า `AuditLog.record`; logger ไม่ใช่ generic redactor; audit rotation แยกจาก job artifacts | [audit.py](../audit.py), `AuditLog.record/recent/_rotate`; Codex, Hands และ OpenCode audit tests ข้างต้น |

ชื่อ test ในตารางอยู่ใน [test_bridge.py](../tests/test_bridge.py), [test_codex.py](../tests/test_codex.py), [test_opencode_tasks.py](../tests/test_opencode_tasks.py) และ [test_hands.py](../tests/test_hands.py).
ตารางเป็น source/test mapping; ไม่ได้อ้างว่ารันทุก test ในตารางใหม่ทั้งหมด.

## ช่องว่างที่ต้องตัดสินก่อนแก้ SPEC

1. **Content retrieval กับ metadata ต้องแยกกัน.** ข้อยกเว้นสำหรับ result/file content ต้องระบุ tool และ field ชัดเจน. ห้ามเขียนข้อยกเว้นกว้างสำหรับทุก MCP response.
2. **Hermes status มี content-bearing fields.** Synthetic probe ยืนยันว่า error และ approval ส่งต่อข้อความที่ไม่ใช่ configured Hermes key. Approval payload ไม่ถูกจำกัดขนาดที่ `Bridge.status`. ต้องกำหนด safe field allowlist และ bounds ก่อนอ้างว่า status เป็น metadata-only. ห้ามใช้การแก้ SPEC เพื่อยอมรับ raw approval/error โดยปริยาย.
3. **Private storage ไม่เท่ากับ audit.** `runs.sqlite3` cache upstream JSON response; Codex/OpenCode เก็บ prompt โดยตรง. Job stdout/stderr และ cached output ต้องมีข้อกำหนด permission, backup และ lifecycle ของตนเอง. Audit rotation ไม่ได้ลบ artifact เหล่านี้.
4. **Permission claim ต้องตรวจทั้งไฟล์ใหม่และ directory เดิม.** Hermes/Codex ใช้ `mkdir(..., mode=0700, exist_ok=True)` แต่ไม่แก้ mode ของ state directory ที่มีอยู่. Synthetic Codex constructor probe ยืนยันว่า directory เดิม mode 0755 ยังคง 0755 แม้ database เป็น 0600. OpenCode ตั้ง state/log directory เป็น 0700 โดยตรง. ข้อนี้ไม่ใช่หลักฐานว่าอ่าน database 0600 ของ user อื่นได้.
5. **Output cap แต่ละ backend ไม่เหมือนกัน.** OpenCode จำกัด stdout/stderr แต่ละ stream. Codex `result` แบ่ง response เป็นหน้า แต่ไม่ได้จำกัดขนาดไฟล์หรือการอ่านทั้งไฟล์ใน method นี้. ห้ามนำ execution cap ของ OpenCode ไปอ้างครอบ Codex.

## Threat model และขอบเขต

- Model output, file content และ upstream approval/error เป็น untrusted data. เนื้อหาอาจมี secrets หรือ prompt injection.
- ชื่อไฟล์ที่ผ่าน Hands policy ไม่รับรองว่า content ไม่มี secrets.
- Hermes exact-key substitution ไม่ใช่การตรวจ credentials ทุกชนิด. ไม่มีหลักฐานว่า Codex/OpenCode result ทำ general secret redaction.
- การส่ง prompt ให้ backend อาจส่งข้อมูลต่อถึง provider ตาม configuration และ permissions ของ backend. ข้อกำหนด audit ไม่ได้อนุญาตการส่งข้อมูลดังกล่าวแทน user.
- OS permissions จำกัดการเข้าถึงไฟล์; ไม่ป้องกัน process ที่รันด้วย user เดียวกัน และไม่ใช่ encryption.
- Backup ของ state/job artifacts ต้องรักษาการควบคุมการเข้าถึง. การลบ audit log ไม่ทำให้ prompt/output ใน artifacts หาย.
- Native OpenCode session storage อยู่นอกขอบเขต redaction ของ bridge.
- Review นี้ไม่เพิ่ม filesystem/network sandbox, permission bypass, tools หรือ discovery count.

## ร่าง wording สำหรับ amendment รอบถัดไป

ข้อความต่อไปนี้เป็นข้อเสนอภาษาอังกฤษสำหรับพิจารณา.
ไม่แทนที่ [SPEC.md](SPEC.md) ใน PR นี้.
ต้อง review ข้อกำหนด, threat model และ tests ก่อนนำไปใช้.

### §4 — Content retrieval exception ที่จำกัดขอบเขต

> The bridge MUST NOT serialize credential configuration, authentication headers, or submitted prompts as operational metadata.
> Audit responses MUST exclude prompts, job output, file content, and credentials.
> The documented content fields of `hermes_task_result`, `codex_task_result`, `opencode_task_result`, and `hands_read` MAY return task output or allowed file content within their existing ownership or workspace-policy checks and response limits.
> `hands_list` MAY return names and relative paths that pass its workspace policy.
> A bounded result page MAY contain the complete output of a short task.
> Pagination MUST NOT be described as redaction.
> Returned content MUST be treated as untrusted and potentially sensitive.
> This exception MUST NOT authorize raw content in status, diagnostics, audit, or unrelated response fields.
> Existing configured Hermes-key substitution and protected-file rules MUST remain in force.

ร่างนี้ยอมรับการส่ง content ที่มีอยู่แล้ว แต่ลดความหมายของข้อห้าม full outputs แบบครอบทุก response.
จึงต้องถือเป็น security-contract amendment ที่ต้อง review อย่างชัดเจน แม้ไม่มีการเพิ่ม runtime capability.
ข้อยกเว้นนี้ไม่แก้ช่องว่าง error/approval ใน status.

### §10 — Audit กับ protected operational storage

> Audit and diagnostic logging MUST exclude prompts, job output, file content, and credentials.
> Documented bridge-owned operational stores MAY retain submitted job prompts, cached task responses, and bounded or otherwise documented job output for execution, ownership, recovery, and explicit result retrieval.
> These stores MUST be protected separately from audit logs.
> Documentation MUST state the stored fields, access permissions, output limits, and retention or cleanup behavior for each backend.
> OS permissions MUST NOT be represented as at-rest encryption.
> Audit redaction MUST NOT be represented as artifact redaction.
> Metadata-only context records MUST NOT retain prompts or outputs.

ต้องกำหนด enforcement ของ directory เดิมและ output lifecycle เพิ่มเติมจาก source/test mapping ก่อนสรุปว่า implementation ผ่านร่างนี้ทั้งหมด.
ห้ามอ้าง automatic job-artifact deletion หรือ universal output cap ที่ยังไม่มีหลักฐาน.

## ลำดับงานที่เสนอ

1. Review รายงานนี้และเลือก contract ของ status error/approval รวมถึง operational storage ให้ชัดเจน.
2. ทำ SPEC amendment แยกตาม §14 พร้อม unreleased release note ที่ระบุการแก้ overbroad privacy guarantee.
3. แก้ implementation gaps ตาม contract ที่อนุมัติ พร้อม negative tests สำหรับ payload bounds, sensitive metadata และ directory modes.
4. ตรวจ fake-server/MCP regression และ acceptance ที่เกี่ยวข้องก่อนปิด privacy follow-up.
5. คง gate ของ Local Hands mutation/execution และ MCP Events ตาม ROADMAP เดิม.

ไม่มีการแก้ signed release, production runtime หรือ privacy guarantees ใน normative SPEC ในรอบนี้.

## Verification ของ review นี้

- Source review ครอบคลุม methods ในตารางที่ base SHA ข้างต้น.
- รัน existing focused tests 9/9 ผ่านด้วย `python -W error::ResourceWarning -m unittest`: Hands audit/content bounds, secret filenames, traversal; Codex lifecycle audit, recent audit, invalid result page; OpenCode private files, Unicode pagination, redacted metadata/page validation.
- ใช้ interpreter ของ environment สำหรับ modules ที่มีเฉพาะ standard-library dependencies; ไม่ได้ใช้ project venv และไม่ได้อ้าง full-suite acceptance.
- Synthetic Hermes probe compile เฉพาะ `clean/status/result` methods จาก AST ของ source จริง โดย mock fetch/ownership. ยืนยัน configured-key substitution, error/approval forwarding, approval payload 5,000 characters ที่ไม่ถูกตัด และ whole short result ในหน้าเดียว. ไม่ใช่ HTTP หรือ MCP wire test.
- Synthetic Hands fixture ยืนยันว่า content ในชื่อไฟล์ที่อนุญาตส่งกลับได้โดยไม่ผ่าน generic secret scanner.
- Synthetic Codex constructor probe ยืนยัน existing-directory mode ที่อธิบายด้านบน.
- ไม่ได้อ่าน credential จริง, production job artifacts หรือเรียก model/backend API.
