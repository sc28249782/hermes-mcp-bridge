"""Reviewable SPEC 24 synthetic fixture; never loads operator configuration.

All hooks and extra status metadata are TEST-ONLY instrumentation. Local SDK
smoke is offline evidence. A separately approved route is required for live use.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import closing, contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys

PIN = "02d7e8bb1e1902ca33a574ab904a6e5b0f441785"
CASES = ("NORMAL", "OP_PRE", "OP_COMMIT", "OP_POST", "CTX_PRE",
         "CTX_COMMIT", "CTX_POST", "CLOSED", "EXCLUDED")
BACKENDS = ("hermes", "codex")
BINDING = {"context_id", "context_binding", "context_binding_note"}
UNRESOLVED = ("Context binding outcome is unresolved. The task remains owned by this bridge "
              "and the context binding may already be recorded. Do not resubmit; retrieve the "
              "task by its existing identifiers and check task status.")
CLOSED = ("Context was closed before binding. The task remains owned by this bridge. "
          "Do not resubmit; retrieve it by its existing identifiers.")
EXPECTED = {"contexts": 18, "closed": 2, "bound": 7, "runs": 10,
            "audit_create": 18, "audit_close": 2, "audit_submit": 10,
            "audit_total": 30, "hermes_posts": 10, "codex_submits": 10}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode()).hexdigest()


def artifact_identity():
    root = Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in ("s24_fixture.py", "candidate_manifest.json")}


def label(backend, case):
    return f"S24_{backend.upper()}_{case}"


def verify_candidate(candidate):
    candidate = Path(candidate).absolute()
    require(candidate == candidate.resolve(strict=True), "candidate symlink boundary")
    manifest = json.loads(Path(__file__).with_name("candidate_manifest.json").read_text())
    require(manifest["candidate_commit"] == PIN, "manifest candidate mismatch")
    allowed = {Path(p).parts[0] for p in manifest["git_blob_sha1"]}
    allowed.update((".git", ".venv", "__pycache__"))
    require(all(p.name in allowed for p in candidate.iterdir()), "unexpected candidate input")
    for relative, expected in manifest["git_blob_sha1"].items():
        path = candidate / relative
        require(not path.is_symlink() and path.resolve().is_relative_to(candidate),
                "candidate file boundary")
        raw = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(actual == expected, "candidate content mismatch: " + relative)
    require(not (candidate / "bridge-config.json").exists(), "operator config is not fixture input")
    return candidate


def build(candidate, state):
    """Create NEW state only, using verified candidate code and no env/config loader."""
    candidate = verify_candidate(candidate)
    state = Path(state).absolute()
    require(state.parent == state.parent.resolve(strict=True), "state parent boundary")
    require(state.parent.stat().st_mode & 0o077 == 0, "state parent must be private")
    state.mkdir(mode=0o700, exist_ok=False)
    sys.path.insert(0, str(candidate))
    import httpx
    import bridge
    from contexts import ContextError, ContextRegistry

    class MockHermes:
        def __init__(self):
            self.posts = 0

        def __call__(self, request):
            if request.method == "POST" and request.url.path == "/v1/runs":
                self.posts += 1
                return httpx.Response(200, json={"run_id": f"run_s24_{self.posts:02d}",
                                                "status": "started"})
            if request.method == "GET" and request.url.path == "/v1/capabilities":
                return httpx.Response(200, json={"features": {"runs_idempotency": {
                    "supported": True, "durable": True}}})
            raise AssertionError("unexpected mock transport request")

    transport = MockHermes()

    class FixtureBridge(bridge.Bridge):
        def __init__(self):
            self.acks = {}
            super().__init__("http://127.0.0.1:1", "SYNTHETIC-NOT-A-CREDENTIAL", state,
                             transport=httpx.MockTransport(transport))

        def submit(self, *args, **kwargs):
            out = super().submit(*args, **kwargs)
            self.acks[out["run_id"]] = digest(deepcopy(out))
            return out

        def local_status(self):
            return {"fixture_only": True, "posts": transport.posts,
                    "ack_hashes": dict(self.acks)}

    class CodexStub:
        def __init__(self):
            self.submits = 0
            self.acks = {}

        def start_watchdog(self):
            return False

        def submit(self, prompt, workspace, mode, model, reasoning_effort):
            require(prompt == "S24_SYNTHETIC" and workspace == "fixture-workspace",
                    "unexpected stub stimulus")
            self.submits += 1
            job_id = "codex_" + f"{self.submits:032x}"
            pending = mode == "workspace-write"
            out = {"job_id": job_id, "status": "pending_local_approval" if pending else "queued",
                   "approval": {"required": True, "fixture": {"sequence": self.submits}}
                   if pending else None, "next": "Synthetic stub; no native task exists."}
            self.acks[job_id] = digest(deepcopy(out))
            return out

        def local_status(self):
            return {"fixture_only": True, "submits": self.submits,
                    "ack_hashes": dict(self.acks)}

        def __getattr__(self, name):
            raise ContextError("Fixture backend operation disabled.")

    class HandsStub:
        def local_status(self):
            return {"fixture_only": True, "backend_initialized": False}

        def __getattr__(self, name):
            raise ContextError("Fixture backend operation disabled.")

    class Registry(ContextRegistry):
        def __init__(self, *args):
            self.commit_failure = None
            self.consumed = set()
            self.labels = set()
            super().__init__(*args)

        @contextmanager
        def db(self):
            db = sqlite3.connect(self.path)
            db.row_factory = sqlite3.Row
            try:
                yield db
                if self.commit_failure is not None and db.in_transaction:
                    failure, self.commit_failure = self.commit_failure, None
                    raise failure
                db.commit()
            finally:
                db.close()

        def create(self, text):
            allowed = {label(b, c) for b in BACKENDS for c in CASES}
            require(text in allowed and text not in self.labels, "unexpected/duplicate fixture label")
            out = super().create(text)
            self.labels.add(text)
            return out

        def bind(self, backend, cid, *args):
            row = self.status(cid)
            prefix = f"S24_{backend.upper()}_"
            require(row["label"].startswith(prefix), "backend/label mismatch")
            case = row["label"][len(prefix):]
            original = super().bind_hermes_run if backend == "hermes" else super().bind_codex_job
            if cid in self.consumed:
                return original(cid, *args)
            self.consumed.add(cid)
            failure = (sqlite3.OperationalError("Synthetic binding failure.")
                       if case.startswith("OP_") else ContextError("Synthetic binding failure."))
            if case.endswith("_PRE"):
                raise failure
            if case == "EXCLUDED":
                raise sqlite3.ProgrammingError("Synthetic excluded binding failure.")
            if case == "CLOSED":
                self.close(cid)
            if case.endswith("_COMMIT"):
                self.commit_failure = failure
            try:
                original(cid, *args)
            finally:
                self.commit_failure = None
            if case.endswith("_POST"):
                raise failure

        def bind_hermes_run(self, cid, run_id):
            return self.bind("hermes", cid, run_id)

        def bind_codex_job(self, cid, workspace, job_id):
            return self.bind("codex", cid, workspace, job_id)

    b = FixtureBridge()
    try:
        c, h = CodexStub(), HandsStub()
        registry = Registry(state, b.audit)
        mcp = bridge.server(b, c, h, registry, None, None)
    except BaseException:
        b.client.close()
        raise
    return mcp, b, registry


async def matrix(call, evidence_class="driver-observations", checkpoint=None):
    """Transport-independent stimulus driver; call returns a CallToolResult."""
    require(evidence_class in ("driver-observations", "offline-sdk-smoke", "parent-route-observations"),
            "unknown evidence class")
    if evidence_class == "parent-route-observations":
        require(callable(checkpoint), "live controller checkpoints required")
    expected_rows, submissions = {}, {}
    expected_audit, registered_runs = [], {}
    posts, codex_calls = 0, 0

    async def observe(stage):
        if checkpoint is not None:
            require(await checkpoint(stage) is True, "controller checkpoint failed: " + stage)

    async def tool(name, args, error=False):
        response = await call(name, args)
        require(bool(response.isError) == error, "unexpected tool error state: " + name)
        if error:
            return None
        require(isinstance(response.structuredContent, dict), "missing structured output")
        return response.structuredContent

    async def status():
        out = await tool("bridge_status", {})
        require(out["ok"], "fixture registry unavailable")
        require(out["hermes"]["posts"] == posts and out["codex"]["submits"] == codex_calls,
                "unexpected backend call count")
        require(out["hermes"]["fixture_only"] and out["codex"]["fixture_only"],
                "fixture status marker missing")
        return out

    async def verify_rows():
        actual = await tool("bridge_context_recent", {"limit": 100})
        actual = {r["context_id"]: r for r in actual["contexts"]}
        require(actual == expected_rows, "unexpected row/state drift")

    await observe("before-matrix")
    await status()
    await verify_rows()
    for backend in BACKENDS:
        for case in CASES:
            await observe(label(backend, case) + ":before")
            await verify_rows()

            out = await tool("bridge_context_create", {"label": label(backend, case)})
            cid = out["context_id"]
            row = {k: v for k, v in out.items() if k != "registry"}
            require(row["closed"] is None and row["hermes_run_id"] is None
                    and row["codex_job_id"] is None, "invalid new row")
            expected_rows[cid] = row
            expected_audit.append(["context", "create", cid, "created"])
            args = {"prompt": "S24_SYNTHETIC", "context_id": cid}
            if backend == "hermes":
                args["request_id"] = f"s24-{backend}-{case}"
                posts += 1
            else:
                args.update(workspace="fixture-workspace", mode="workspace-write")
                codex_calls += 1
            submissions[backend, case] = deepcopy(args)
            out = await tool(backend + "_submit_task", args, error=case == "EXCLUDED")
            if backend == "hermes":
                run_id = f"run_s24_{posts:02d}"
                registered_runs[args["request_id"]] = run_id
                expected_audit.append(["hermes", "submit", run_id, "started"])
            if case == "CLOSED":
                expected_audit.append(["context", "close", cid, "closed"])
            observed = await tool("bridge_context_status", {"context_id": cid})
            expected = dict(row)
            expected["updated"] = observed["updated"]
            if case == "CLOSED":
                require(observed["closed"] is not None, "close did not persist")
                expected["closed"] = observed["closed"]
            bound = case in ("NORMAL", "OP_POST", "CTX_POST")
            if bound:
                key = "hermes_run_id" if backend == "hermes" else "codex_job_id"
                expected[key] = out["run_id" if backend == "hermes" else "job_id"]
                if backend == "codex":
                    expected["codex_workspace"] = "fixture-workspace"
            require(observed == expected, "unexpected binding/transaction state")
            expected_rows[cid] = expected
            state = await status()
            if out is not None:
                outcome = ("bound" if case == "NORMAL" else "closed_rejected"
                           if case == "CLOSED" else "binding_unresolved")
                require(out["context_binding"] == outcome and out["context_id"] == cid,
                        "wrong binding outcome")
                note = None if case == "NORMAL" else CLOSED if case == "CLOSED" else UNRESOLVED
                require(out.get("context_binding_note") == note, "wrong constant note")
                key = out["run_id" if backend == "hermes" else "job_id"]
                require(digest({k: v for k, v in out.items() if k not in BINDING})
                        == state[backend]["ack_hashes"][key], "ACK changed")
                if backend == "codex":
                    require(out["status"] == "pending_local_approval"
                            and out["approval"]["required"] is True, "stub approval lost")
            await verify_rows()
            await observe(label(backend, case) + ":after")

    # Known-ID replay consumes no new POST; one-shot PRE hook now permits normal bind.
    await observe("replay:before")
    args = submissions["hermes", "OP_PRE"]
    out = await tool("hermes_submit_task", args)
    require(out["replayed_locally"] is True and out["context_binding"] == "bound", "replay failed")
    cid = args["context_id"]
    row = await tool("bridge_context_status", {"context_id": cid})
    expected = dict(expected_rows[cid])
    expected.update(updated=row["updated"], hermes_run_id=out["run_id"])
    require(row == expected, "replay row mismatch")
    expected_rows[cid] = expected
    replay_state = await status()
    require(digest({k: v for k, v in out.items() if k not in BINDING})
            == replay_state["hermes"]["ack_hashes"][out["run_id"]], "replay ACK changed")
    await verify_rows()
    await observe("replay:after")

    for backend in BACKENDS:
        await observe(backend + ":precheck-plain:before")
        # Closed prechecks must add zero backend calls.
        await tool(backend + "_submit_task", submissions[backend, "CLOSED"], error=True)
        await status()
        plain = {"prompt": "S24_SYNTHETIC"}
        if backend == "hermes":
            plain["request_id"] = "s24-hermes-plain"
            posts += 1
        else:
            plain.update(workspace="fixture-workspace", mode="read-only")
            codex_calls += 1
        out = await tool(backend + "_submit_task", plain)
        if backend == "hermes":
            run_id = f"run_s24_{posts:02d}"
            registered_runs[plain["request_id"]] = run_id
            expected_audit.append(["hermes", "submit", run_id, "started"])
        require(not BINDING.intersection(out), "no-context binding fields present")
        state = await status()
        key = out["run_id" if backend == "hermes" else "job_id"]
        require(digest(out) == state[backend]["ack_hashes"][key], "plain ACK changed")
        await verify_rows()
        await observe(backend + ":precheck-plain:after")
    require(posts == EXPECTED["hermes_posts"] and codex_calls == EXPECTED["codex_submits"],
            "final counter mismatch")
    await observe("after-matrix")
    return {"evidence_class": evidence_class, "expected": EXPECTED,
            "rows": expected_rows, "audit_projection": expected_audit,
            "registered_runs": registered_runs,
            "transport_counters": {"hermes_posts": posts,
                                                           "codex_submits": codex_calls}}


def inspect_stopped_state(state, expected=None):
    """Caller MUST stop all fixture writers before calling this read-only check."""
    state = Path(state).resolve(strict=True)
    with closing(sqlite3.connect((state / "contexts.sqlite3").as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        rows = [dict(r) for r in db.execute("SELECT * FROM contexts")]
    with closing(sqlite3.connect((state / "runs.sqlite3").as_uri() + "?mode=ro", uri=True)) as db:
        runs = db.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        registered = dict(db.execute("SELECT request_id,run_id FROM runs"))
    events = [json.loads(line) for line in (state / "audit.jsonl").read_text().splitlines()]
    counts = {"contexts": len(rows), "closed": sum(r["closed"] is not None for r in rows),
              "bound": sum(bool(r["hermes_run_id"] or r["codex_job_id"]) for r in rows),
              "runs": runs, "audit_create": sum(e["action"] == "create" for e in events),
              "audit_close": sum(e["action"] == "close" for e in events),
              "audit_submit": sum(e["action"] == "submit" for e in events),
              "audit_total": len(events)}
    require(all(counts[k] == EXPECTED[k] for k in counts), "durable aggregate mismatch")
    if expected is not None:
        require({r["context_id"]: r for r in rows} == expected["rows"], "durable row drift")
        require(registered == expected["registered_runs"], "durable registration drift")
        projection = [[e[k] for k in ("component", "action", "subject", "outcome")] for e in events]
        require(projection == expected["audit_projection"], "durable audit drift")
    return counts


async def offline(candidate, state):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    before = artifact_identity()
    parameters = StdioServerParameters(command=sys.executable, args=["-B", str(Path(__file__).resolve()),
        "serve", "--candidate", str(candidate), "--state", str(state)],
        env={"PYTHONDONTWRITEBYTECODE": "1"})
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            require(len((await session.list_tools()).tools) == 27, "discovery mismatch")
            result = await asyncio.wait_for(matrix(session.call_tool, "offline-sdk-smoke"), timeout=90)
    # SDK context has stopped/reaped its child before any snapshot read.
    verify_candidate(candidate)
    require(artifact_identity() == before, "artifact changed during smoke")
    result["input_identity"] = before
    result["durable"] = inspect_stopped_state(state, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "serve", "offline"))
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    candidate = verify_candidate(args.candidate)
    if args.mode == "verify":
        print(json.dumps({"candidate_commit": PIN, "content_verified": True}))
        return
    require(args.state is not None, "new private state path required")
    if args.mode == "serve":
        mcp, bridge, _ = build(candidate, args.state)
        try:
            from stdio_guard import run_stdio_guarded
            run_stdio_guarded(mcp)
        finally:
            bridge.client.close()
    else:
        require(args.receipt is not None and not args.receipt.exists(), "new receipt path required")
        receipt = args.receipt.absolute()
        require(receipt.parent == receipt.parent.resolve(strict=True), "receipt parent boundary")
        require(receipt.parent.stat().st_mode & 0o077 == 0, "receipt parent must be private")
        result = asyncio.run(offline(candidate, args.state))
        raw = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
        fd = os.open(args.receipt, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
        print(json.dumps({"evidence_class": result["evidence_class"], "durable": result["durable"],
                          "receipt_sha256": hashlib.sha256(raw).hexdigest()}))


if __name__ == "__main__":
    main()
