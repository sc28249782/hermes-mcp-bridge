#!/usr/bin/env python3
"""Deterministic fixture CLI for OpenCode execution tests (SPEC section 18).

Behavior is selected by the single content marker inside the prompt read from
stdin. It never touches the network and prints bounded JSONL events:
- marker "OK": step_start + text, exit 0 (completion evidence)
- marker "NOEVENT": prints nothing, exit 0 (no completion evidence -> failed)
- marker "ERREVENT0": prints an error event, exit 0 (error with exit 0 -> failed)
- marker "PERMISSION": prints a permission request event, then blocks until
  killed (unresolved ask -> permission_required at the deadline)
- marker "SPAWNCHILD": behaves like OK and also leaves a sleep descendant
  alive for a moment to prove group cleanup
"""
import json
import os
import sys
import time

marker = sys.stdin.read()
session = os.environ.get("FIXTURE_SESSION", "ses_fixture")


def emit(event_type, part):
    print(json.dumps({"type": event_type, "timestamp": int(time.time() * 1000),
                      "sessionID": session, "part": part}), flush=True)


if "ERREVENT0" in marker:
    emit("error", {"type": "error", "message": "synthetic error"})
    sys.exit(0)
if "NOEVENT" in marker:
    sys.exit(0)
if "PERMISSION" in marker:
    emit("permission", {"type": "permission", "request": "shell"})
    time.sleep(3600)
if "SPAWNCHILD" in marker:
    if os.fork() == 0:
        time.sleep(60)
    emit("step_start", {"type": "step-start"})
    emit("text", {"type": "text", "text": "done"})
    sys.exit(0)
emit("step_start", {"type": "step-start"})
emit("text", {"type": "text", "text": "fixture-ok"})
sys.exit(0)
