# v1.0.0 repeatable acceptance

1. ตรวจ SHA-256 ของ archive ก่อนแตกไฟล์ และไม่ใช้ archive ที่มี `.venv`, `state/`, `.env` หรือ `bridge-config.json`.
2. คัดลอกเฉพาะ `bridge-config.json` และ `state/` ที่ตรวจแล้วจาก release ก่อนหน้า, รัน `bash install.sh`, แล้วตรวจ `./bridge.sh doctor` และ `./bridge.sh codex-doctor`.
3. รัน regression suite: `.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -v` และ `bash -n bridge.sh tunnel.sh install.sh`.
4. ใช้ `bash tunnel.sh init tunnel_IDเดิม --force`, restart tunnel, เปิด ChatGPT chat ใหม่ และตรวจ discovery 19 tools.
5. เรียก `bridge_status`: ทั้ง Hermes/Codex ต้องมี `upstream_checked: false`; จากนั้นเรียก `bridge_diagnostics` เพื่อตรวจ upstream health แยกต่างหาก.
6. ทดสอบ Hermes read-only, result pagination และ durable idempotency โดยไม่ส่ง secret ใน prompt.
7. ทดสอบ Codex read-only และ workspace-write approval (ต้อง approve จาก terminal) รวม cancellation/watchdog ตาม policy.
8. หาก Hermes ประกาศ `run_approval: true`, ทดสอบ local approval/deny และ `approval_stale`; หากไม่ประกาศ ให้บันทึก capability-blocked โดยไม่ bypass.
