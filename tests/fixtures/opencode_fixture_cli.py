#!/usr/bin/env python3
"""Network-free subprocess fixture; only this test's children are created."""
import json
import os
import signal
import sys
import time

if "--version" in sys.argv:
    print("opencode v2.0.32")
    sys.exit(0)

if os.environ.get("HMB_FIXTURE_NOREAD") == "1":
    time.sleep(60)
    sys.exit(1)
prompt = sys.stdin.read()
session = sys.argv[sys.argv.index("--session") + 1]

def emit(kind, part=None, sid=None):
    value = {"type": kind, "sessionID": sid or session, "part": part or {}}
    print(json.dumps(value, ensure_ascii=False), flush=True)

def text(value):
    emit("text", {"type": "text", "text": value})

if prompt == "empty":
    sys.exit(0)
if prompt == "error0":
    emit("error", {"type": "error"})
    sys.exit(0)
if prompt == "tool_error":
    emit("tool_use", {"type": "tool", "state": {"status": "error"}})
    sys.exit(0)
if prompt == "permission":
    emit("permission", {"request": "shell"})
    time.sleep(60)
if prompt == "wrong_session":
    emit("text", {"type": "text", "text": "bad"}, "ses_foreign123")
    sys.exit(0)
if prompt == "missing_session":
    print('{"type":"text","part":{"type":"text","text":"bad"}}')
    sys.exit(0)
if prompt == "malformed":
    print('not JSON')
    sys.exit(0)
if prompt == "truncated":
    sys.stdout.write(json.dumps({"type": "text", "sessionID": session, "part": {"type": "text", "text": "bad"}}))
    sys.exit(0)
if prompt == "flood":
    sys.stdout.write("x" * 500000)
    sys.exit(0)
if prompt == "stderr_flood":
    sys.stderr.write("x" * 500000)
    sys.exit(0)
if prompt == "slow":
    emit("step_start", {"type": "step-start"})
    time.sleep(60)
if prompt == "descendant":
    child = os.fork()
    if child == 0:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        time.sleep(60)
        os._exit(0)
    text("child=" + str(child))
    sys.exit(0)
if prompt == "inspect":
    text(json.dumps({"argv": sys.argv[1:], "stdin": prompt, "native_config": os.environ.get("OPENCODE_CONFIG_CONTENT")}))
elif prompt.startswith("length:"):
    text(str(len(prompt)))
elif prompt == "unicode":
    text("ภาษาไทย 😀 中文")
elif prompt == "tool_calls_only":
    emit("step_finish", {"type": "step-finish", "reason": "tool-calls"})
elif prompt == "permission_word":
    text('The literal string "permission" is ordinary text.')
else:
    text("fixture-ok")
if prompt == "nonzero":
    sys.exit(7)
