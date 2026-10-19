# v1.x repeatable acceptance (ปรับปรุงสำหรับ v1.2.5 candidate; tag pending)

1. ตรวจ SHA-256 ของ archive ก่อนแตกไฟล์ และไม่ใช้ archive ที่มี `.venv`, `state/`, `.env` หรือ `bridge-config.json`.
2. คัดลอกเฉพาะ `bridge-config.json` และ `state/` ที่ตรวจแล้วจาก release ก่อนหน้า, รัน `bash install.sh`, แล้วตรวจ `./bridge.sh doctor` และ `./bridge.sh codex-doctor`.
3. รัน regression suite: `.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -v` และ `bash -n bridge.sh tunnel.sh install.sh`.
4. เลือก profile ของ instance ที่ทดสอบให้ชัดแล้ว restart/refresh tools ตรวจ discovery ตาม `TESTING.md`: 27 default / 28 health / 33 execution opt-in. `tunnel.sh init/run` ของ baseline ใช้ production profile; สำหรับ Dev ให้ใช้ `hermes-wsl-dev` และ health port 8081 ตาม `OPENCODE-TH.md`.
5. เรียก `bridge_status`: ทั้ง Hermes/Codex ต้องมี `upstream_checked: false`; จากนั้นเรียก `bridge_diagnostics` เพื่อตรวจ upstream health แยกต่างหาก.
6. ทดสอบ Hermes read-only, result pagination และ durable idempotency โดยไม่ส่ง secret ใน prompt.
7. ทดสอบ Codex read-only และ workspace-write approval (ต้อง approve จาก terminal) รวม cancellation/watchdog ตาม policy.
8. บันทึก capability `run_approval_response` หาก Hermes ประกาศไว้; v1.0.1 ยังไม่ subscribe SSE approval event และไม่มี bridge approval tool. ห้าม bypass หรืออ้างว่า upstream approval ผ่าน acceptance; งานนี้เป็น v1.1.0.

9. เมื่อทดสอบ OpenCode execution ให้ใช้ workspace ทดสอบ/model ที่ allowlist ส่ง benign task แล้วอ่าน status/result, ต่อ session เดิม, retry request/input เดิมและตรวจ job เดิม ตรวจ bytes จริงเมื่อทดสอบเขียนไฟล์ ผล cancellation ที่ controller และ permission-required ที่ fixture ต้องแยกจากหลักฐาน Work-chat ตาม `LIVE-ACCEPTANCE-TH.md`. ไม่มี native permission reply หรือ event subscription.
