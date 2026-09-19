# ผล Live Acceptance — v0.3.2

วันที่ 14 กันยายน 2026 ทดสอบผ่าน Secure MCP Tunnel ไปยัง Hermes API `127.0.0.1:8642` ที่มี Bearer authentication โดยไม่เปิดพอร์ตสู่ public network

ผ่านครบ 10 tools: health, model info/catalog, recent tasks, usage summary/export, submit, status, result และ cancel

- `usage_export` ตรวจว่าไม่มี prompt, output หรือ API key
- smoke run ตอบ `HERMES_CANCEL_TEST_OK` ผ่าน submit/status/result
- cancel semantic: run `run_8980a67a66a94135a46f8b9d87dc4389` รัน `sleep 60` แบบไม่มี file/network operation แล้วเปลี่ยน `stopping` เป็น `cancelled`

ข้อจำกัด: model catalog ของ Hermes Runs API ประกาศ virtual model `hermes-agent` เพียงรายการเดียว แม้ config ปัจจุบันใช้ `deepseek/deepseek-v4-flash-0731` กับ provider `nous`
