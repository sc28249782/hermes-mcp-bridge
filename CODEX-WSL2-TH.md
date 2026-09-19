# Codex/WSL2 แบบควบคุมสิทธิ์ — v0.4.0

รุ่นนี้คง Hermes tools เดิม 10 ตัว และเพิ่ม Codex tools 6 ตัว รวม 16 tools

## ขอบเขตความปลอดภัย

- workspace ต้อง resolve แล้วอยู่ใต้ `codex.allowed_workspaces`
- ป้องกัน path traversal และ symlink escape ด้วย canonical path
- เรียก `codex` ด้วย argument array โดยตรง ไม่ผ่าน shell
- อนุญาตเฉพาะ `read-only` และ `workspace-write`; ไม่มี `danger-full-access`
- `workspace-write` จะไม่เริ่มจนกว่าผู้ใช้อนุมัติจาก terminal ใน WSL2
- ไม่มี MCP approval tool สำหรับ Codex จึงไม่สามารถให้ agent อนุมัติตัวเอง
- log และฐานข้อมูลงานอยู่ใน `state/` และตั้ง permission แบบ private
- จำกัด prompt 32,000 ตัวอักษรและ runtime เริ่มต้น 1,800 วินาที
- Codex sandbox ควบคุม filesystem/network ชั้นสุดท้าย; bridge ไม่เพิ่มสิทธิ์ network

## ตั้งค่า

ตรวจว่า Codex CLI ติดตั้งและ login ใน WSL2 แล้วด้วย `codex --version` จากนั้นเพิ่มใน `bridge-config.json` โดยรักษาค่า Hermes เดิมไว้:

```json
"codex": {
  "binary": "codex",
  "allowed_workspaces": [
    "/mnt/e/Projects/OpenHDK",
    "/mnt/e/Projects/HandyKaraoke"
  ],
  "max_prompt_chars": 32000,
  "max_runtime_seconds": 1800
}
```

ตรวจ policy ด้วย `./bridge.sh codex-doctor` แล้ว restart `tunnel.sh run` และเปิดแชทใหม่

## Codex tools 6 ตัว

1. `codex_health`
2. `codex_submit_task`
3. `codex_task_status`
4. `codex_task_result`
5. `codex_cancel_task`
6. `codex_recent_tasks`

งานอ่านอย่างเดียวเริ่มได้ทันทีด้วย `mode=read-only` ส่วนงานแก้ไขจะคืน `pending_local_approval` และ job ID

```bash
./bridge.sh codex-approve codex_แทนด้วย_JOB_ID
```

คำสั่งจะแสดง job ID, workspace, mode และ prompt ให้ตรวจ ต้องพิมพ์ `APPROVE` ตรงตัวจึงเริ่มทำงาน หากต้องการปฏิเสธใช้ `./bridge.sh codex-deny codex_แทนด้วย_JOB_ID`

การกดยืนยัน tool call ใน ChatGPT ไม่ทดแทนการอนุมัติใน terminal นี้

## Acceptance test ที่แนะนำ

1. เรียก `codex_health` และตรวจ version/allowlist
2. ส่ง `read-only` ให้ตรวจ `git status` และยืนยันว่าไม่มีไฟล์เปลี่ยน
3. ทดลอง workspace นอก allowlist และ symlink escape ต้องถูกปฏิเสธ
4. ส่ง `workspace-write`; ก่อน local approval ต้องไม่มี process Codex เริ่มทำงาน
5. deny หนึ่งงานและ approve หนึ่งงานที่แก้ไฟล์ทดสอบแบบย้อนกลับได้
6. ตรวจ status/result/cancel/recent และยืนยันว่า job ต่าง bridge ถูกปฏิเสธ

อ้างอิง: https://developers.openai.com/codex/cli
