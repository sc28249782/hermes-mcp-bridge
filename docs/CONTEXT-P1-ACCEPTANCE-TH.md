# Context P1 — candidate acceptance

วันที่: 20 ตุลาคม 2026.
สถานะ: **P1 ผ่าน external implementation review และ merge แล้ว; unreleased และ undeployed**.
Contract: [SPEC §20](SPEC.md#20-context-p1--approved-scope-future-implementation-no-assigned-release).
SPEC ผ่าน review และ merge ใน PR #58 ที่ `64eb0a1` ก่อน implementation ใน PR #59.
บันทึกนี้เป็น maintainer automation ไม่ใช่ external review.

## สิ่งที่ candidate เพิ่ม

- Optional `contexts.soft_cap`: default 1,000, integer 1–100,000 และไม่รับ boolean.
- Aggregate `registry` 6 fields บน status และ successful create. อ่านไม่เกิน cap+1 logical rows โดยไม่ดึง label/binding/ID มายัง observer.
- เมื่อถึง cap ให้ warning; create ยังสำเร็จ. เมื่ออ่าน observation ไม่ได้ให้ unavailable/null. Create ที่บันทึกสำเร็จยังคืน acknowledgement; status root `ok=false` เมื่อ registry unavailable.
- Local `context-prune-preview` dispatch ก่อน config/credentials/backend imports. Explicit preview ไม่ถูก `BRIDGE_EVENTS_PROBE` เปลี่ยนเป็น events-probe.
- SQLite URI `mode=ro`, lock timeout 1 วินาที, schema validation และ closed/unbound cutoff ตาม §20. ไม่มี immutable/nolock/write fallback.
- ผล preview เป็น aggregate เท่านั้น. ไม่มี apply/delete, plan file, schema migration, chmod, audit mutation หรือ native/backend calls ใน preview/observation.

## Acceptance mapping

| ข้อกำหนด | หลักฐาน synthetic |
| --- | --- |
| Config defaults/range/type/unknown values | `test_config_defaults_types_ranges_unknown_values` |
| Threshold และ capped lower bound, 512-byte shape | `test_threshold_and_bounded_lower_bound_shapes` |
| Create acknowledgement เมื่อ observation fail | `test_create_ack_survives_observation_failure_and_is_not_retried` |
| Warning ไม่ reject create; status/recent คงเดิม | `test_soft_cap_does_not_reject_creates_or_change_status_recent` และ context continuation tests เดิม |
| Missing/invalid schema ไม่สร้างหรือ migrate | `test_missing_observation_does_not_create_db`, `test_storage_schema_failure_has_constant_output_and_no_migration` |
| Cutoff equality, timestamps และ refs ทั้งสี่ | `test_selection_cutoff_types_and_each_reference` |
| Batch/default/max, ordering และ limit+1 | `test_batch_boundaries_and_deterministic_order` |
| URI encoding, read-only SQL, 1-second timeout, query projection | `test_read_only_uri_timeout_and_logical_sampling` |
| Constant JSON/exit codes, invalid clock, special files | `test_expected_argument_errors_never_echo_values`, `test_invalid_clocks_and_special_files` |
| Lock contention | `test_rollback_lock_wait_is_bounded_and_never_falls_back` |
| WAL committed/uncommitted visibility | `test_wal_reads_committed_rows_without_explicit_sidecar_changes` |
| Read-only file/directory permissions | `test_read_only_permissions_in_isolated_cli` |
| WAL ไม่มี sidecars และ directory เขียนไม่ได้ | `test_wal_without_sidecars_cannot_bypass_read_only_directory` |
| Early dispatch, config/constructor/import guards และ wrapper override | `test_main_early_dispatch_never_constructs_backends_or_reads_config`, `test_script_dispatch_never_imports_backends_and_wrapper_override` |
| Actual MCP status/create aggregate และ unavailable shape | `test_context_registry_warning_and_unavailable_on_real_stdio` |
| Discovery 27/28/33 และ packaging | MCP/OpenCode discovery tests เดิม และ `test_packaging.py` รวม module `context_read` |

## ผลที่ตรวจได้และข้อจำกัด

Runtime candidate `12a9588` ผ่าน CI matrix Python 3.12 และ 3.14 ใน [run 39402480021](https://github.com/sc28249782/hermes-mcp-bridge/actions/runs/39402480021). ทั้งสอง jobs ผ่าน full suite, shellcheck และ Bash syntax. Source catalog มี 203 tests; CI run นี้ไม่ครอบคลุมข้อความเอกสารที่เพิ่มภายหลัง. ต้องตรวจ exact-head CI ใหม่ก่อนส่ง review.

Runtime ของแชตใช้ Python 3.12.14. Focused P1 รัน 17 tests: ผ่าน 15 และข้าม 2 permission cases เพราะ process เป็น root. Actual stdio MCP suite ผ่าน 3/3 รวม P1 case ใหม่. Full local suite ก่อนเพิ่ม WAL-permission test รัน 202 tests และไม่ผ่าน (4 failures, 1 error, 1 skip) ใน process/zombie identity cases เดิม. จึงไม่อ้าง full local-suite pass. Baseline control ที่ source ก่อน P1 (`64eb0a1`) รัน 185 tests แล้วไม่ผ่านด้วย 4 failures และ 1 error ในกลุ่มเดียวกัน. ตัวเลขนี้ไม่ใช้แทน CI matrix หรือผลบน WSL.

ผล rollback-journal probe: aggregate/preview อ่านได้โดย source DB bytes และ permission ไม่เปลี่ยน. Exclusive lock ทำให้ได้ constant unavailable หลัง lock timeout. ผล WAL probe: reader เห็น committed row ระหว่าง writer ถือ uncommitted update; WAL bytes และรายชื่อไฟล์คงเดิมใน fixture นี้. ไม่อ้างว่า SQLite ไม่แตะ shared-memory read marks หรือไม่มี filesystem effects ทุกแบบ.

Permission tests ใช้ file/directory ที่ปิด write bits สำหรับผู้ใช้ทั่วไป; ไม่ใช่ dedicated read-only mount probe. WAL ที่ต้องสร้าง sidecars แต่เขียน directory ไม่ได้ต้องคืน unavailable. ห้ามเปลี่ยน permissions หรือใช้ immutable/nolock เพื่อหลบ failure.

ทั้งหมดใช้ public source และ isolated temporary state. ไม่มีการอ่าน production config/state, Dev route switch หรือส่ง model task. ไม่มี live Dev-tunnel/production acceptance ของ P1. ไม่มี release assigned, signed assets หรือ deployment จาก PR นี้. Signed v1.2.6 และ production คงเดิม.

P1 ไม่แก้ close/bind/submission race ที่บันทึกใน scope proposal. P2 apply/delete, observation counters/annotations, native history compaction, Hands และ MCP Events ยังแยกติดตามตาม gates เดิม.


## Implementation review และ merge checkpoint (20 October 2026)

Operator ส่ง external review verdict APPROVE สำหรับ PR #59 ที่ `b7ff97a`. Reviewer รายงาน full suite 203 tests บน Python 3.12, focused context 19/19 และตรวจ CI matrix 3.12/3.14 ที่ exact head. Reviewer probe aggregate shape, bool/range rejection, CLI exit/stderr/error shapes, limit+1 และ wrapper override ด้วยตนเอง. ผลนี้แยกจาก maintainer automation ข้างต้น.

Operator ยืนยัน merge แล้ว; PR #59 merge ที่ `5685e11`. การอนุมัติที่ `b7ff97a` ไม่ครอบคลุม checkpoint ที่เพิ่มภายหลังนี้. คำว่า review pending ในบันทึกเตรียม candidate เดิมเป็นสถานะ ณ เวลานั้น. P1 อยู่บน main แต่ยังไม่มี release/deployment. ขั้นถัดไปคือ [Dev transport acceptance](CONTEXT-P1-DEV-ACCEPTANCE-TH.md); live Dev และ dedicated read-only mount probe ยังไม่ได้ดำเนินการ.
