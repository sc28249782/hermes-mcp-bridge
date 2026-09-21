"""Private, single-user Hermes Runs API bridge. Target: Hermes 8d79c2ff."""
from __future__ import annotations

import hashlib
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import urlsplit

import httpx
from dotenv import dotenv_values
from yaml import YAMLError, safe_load
from audit import AuditLog
from config_schema import ConfigError, load_bridge_config

TERMINAL = {"completed", "failed", "cancelled"}
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
MODEL_IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,255}$")
PROVIDER_IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
OPTION_VALUE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,63}$")
MODEL_OPTION_KEYS = {"reasoning_effort", "service_tier"}


class BridgeError(RuntimeError):
    pass


class Bridge:
    def __init__(self, base: str, key: str, state: Path, transport=None, model_config=None, audit_config=None,
                 operational_config=None):
        u = urlsplit(base)
        if (u.scheme != "http" or u.hostname != "127.0.0.1" or
                u.username or u.password or u.path not in ("", "/") or u.query or u.fragment):
            raise BridgeError("This version requires http://127.0.0.1:PORT (no path).")
        if not key or any(c in key for c in "\r\n\x00"):
            raise BridgeError("Missing or invalid Hermes API key.")
        self.base, self.key, self.state = base.rstrip("/"), key, Path(state)
        self.model_config = Path(model_config).expanduser() if model_config else None
        self.config_warnings = []
        operational_config = operational_config or {}
        self.stale_run_seconds = operational_config.get("stale_run_seconds", 3600)
        self.approval_stale_seconds = operational_config.get("approval_stale_seconds", 1800)
        for label, value in (("hermes.stale_run_seconds", self.stale_run_seconds),
                             ("hermes.approval_stale_seconds", self.approval_stale_seconds)):
            if not isinstance(value, int) or not 1 <= value <= 86400:
                raise BridgeError(f"{label} must be 1-86400")
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.audit = AuditLog(self.state, audit_config)
        self.dbpath = self.state / "runs.sqlite3"
        self.client = httpx.Client(base_url=self.base, timeout=httpx.Timeout(25, connect=5),
                                   trust_env=False, follow_redirects=False, transport=transport)
        with self.db() as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, created REAL NOT NULL, run_id TEXT UNIQUE, session_id TEXT, result TEXT)")
            existing = {row[1] for row in db.execute("PRAGMA table_info(runs)")}
            for name, definition in (
                ("requested_model", "TEXT"),
                ("requested_provider", "TEXT"),
                ("requested_model_options", "TEXT"),
                ("reported_model", "TEXT"),
            ):
                if name not in existing:
                    db.execute(f"ALTER TABLE runs ADD COLUMN {name} {definition}")
        self.dbpath.chmod(0o600)

    @classmethod
    def from_config(cls):
        root = Path(__file__).resolve().parent
        try:
            config, warnings = load_bridge_config(root)
        except ConfigError as exc:
            raise BridgeError(str(exc)) from exc
        env_path = Path(config["hermes_env"]).expanduser()
        # Read only this key; never source the file as shell code or export other secrets.
        key = dotenv_values(env_path, interpolate=False).get("API_SERVER_KEY") or ""
        model_config = Path(config.get("hermes_config", env_path.parent / "config.yaml")).expanduser()
        bridge = cls(config["api_url"], key, root / "state", model_config=model_config,
                     audit_config=config.get("audit"), operational_config=config.get("hermes"))
        bridge.config_warnings = warnings
        return bridge

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.dbpath, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def clean(self, value):
        if isinstance(value, str):
            return value.replace(self.key, "[REDACTED_HERMES_KEY]")
        if isinstance(value, dict):
            return {k: self.clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.clean(v) for v in value]
        return value

    @staticmethod
    def optional_identifier(value, label, pattern):
        if value is None:
            return None
        if not isinstance(value, str) or not pattern.fullmatch(value):
            raise BridgeError(f"Invalid {label}.")
        return value

    def model_selection(self, model=None, provider=None, model_options=None):
        model = self.optional_identifier(model, "model", MODEL_IDENT)
        provider = self.optional_identifier(provider, "provider", PROVIDER_IDENT)
        if model_options is None:
            return model, provider, None
        if not isinstance(model_options, dict) or not model_options:
            raise BridgeError("model_options must be a non-empty object.")
        if set(model_options) - MODEL_OPTION_KEYS:
            raise BridgeError("Unsupported model_options key.")
        clean_options = {}
        for key in sorted(model_options):
            value = model_options[key]
            if not isinstance(value, str) or not OPTION_VALUE.fullmatch(value):
                raise BridgeError(f"Invalid model_options.{key}.")
            clean_options[key] = value
        return model, provider, clean_options

    def configured_model(self):
        if not self.model_config or not self.model_config.is_file():
            return {"available": False}
        try:
            raw = safe_load(self.model_config.read_text())
        except (OSError, UnicodeError, YAMLError):
            return {"available": False, "error": "Hermes model config could not be read safely."}
        model = raw.get("model") if isinstance(raw, dict) else None
        if not isinstance(model, dict):
            return {"available": False, "error": "Hermes model config has no model object."}
        out = {"available": True}
        for key in ("default", "provider"):
            value = model.get(key)
            if isinstance(value, str) and value:
                out[key] = value[:256]
        out["base_url_configured"] = bool(model.get("base_url"))
        return out

    def models(self):
        raw = self.request("GET", "/v1/models")
        entries = raw.get("data", raw.get("models", []))
        if not isinstance(entries, list):
            raise BridgeError("Hermes returned an unexpected model catalog.")
        models = []
        for item in entries[:200]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            row = {"id": item["id"][:256]}
            for key in ("provider", "owned_by", "object"):
                if isinstance(item.get(key), str):
                    row[key] = item[key][:128]
            models.append(row)
        return {"models": models, "truncated": len(entries) > len(models)}

    def model_info(self):
        features = self.request("GET", "/v1/capabilities").get("features", {})
        return {
            "configured": self.configured_model(),
            "bridge": {
                "per_run_model_override": True,
                "followup_model_override": False,
                "allowed_model_options": sorted(MODEL_OPTION_KEYS),
            },
            "hermes_advertised": {
                "run_model_override": features.get("run_model_override"),
            },
            "note": "The Hermes model catalog is available through hermes_models. New sessions may override model/provider; follow-ups retain their session model.",
        }

    @staticmethod
    def row_selection(row):
        options = row["requested_model_options"]
        return {
            "requested_model": row["requested_model"],
            "requested_provider": row["requested_provider"],
            "requested_model_options": json.loads(options) if options else None,
        }

    def request(self, method, path, body=None, headers=None):
        try:
            with self.client.stream(method, path, json=body,
                    headers={"Authorization": f"Bearer {self.key}", **(headers or {})}) as r:
                if not 200 <= r.status_code < 300:
                    # Do not expose raw server errors, config, headers, or credentials.
                    raise BridgeError(f"Hermes HTTP {r.status_code} on {method} {path}.")
                chunks, size = [], 0
                for chunk in r.iter_bytes():
                    size += len(chunk)
                    if size > 4_000_000:
                        raise BridgeError("Hermes response exceeds the 4 MB bridge limit.")
                    chunks.append(chunk)
                value = json.loads(b"".join(chunks))
        except httpx.RequestError as exc:
            raise BridgeError("Hermes transport failed or timed out; acceptance may be uncertain.") from exc
        except (ValueError, UnicodeError) as exc:
            raise BridgeError("Hermes returned invalid JSON.") from exc
        if not isinstance(value, dict):
            raise BridgeError("Hermes returned an unexpected response shape.")
        return self.clean(value)

    def health(self):
        try:
            unauth = self.client.get("/v1/models")
        except httpx.RequestError as exc:
            raise BridgeError("Cannot reach the Hermes API.") from exc
        if unauth.status_code != 401:
            raise BridgeError("Expected HTTP 401 without a key; check Hermes authentication.")
        self.request("GET", "/v1/models")
        cap = self.request("GET", "/v1/capabilities")
        features = cap.get("features", {})
        needed = ("run_submission", "run_status", "run_stop")
        missing = [x for x in needed if not features.get(x)]
        if missing:
            raise BridgeError("Hermes does not advertise: " + ", ".join(missing))
        return {"ok": True, "authentication": "verified", "api_url": self.base,
                "features": {k: features.get(k) for k in (*needed, "run_approval", "runs_idempotency")},
                "approval_handling": "Pending Hermes approvals require the local approve/deny command.",
                "execution_scope": "Uses the configured Hermes API profile and its OS/tool permissions; no filesystem sandbox is added."}

    def diagnostics(self):
        try:
            hermes = self.health()
        except BridgeError as exc:
            hermes = {"ok": False, "error": str(exc)}
        return {"hermes": hermes, "config_warnings": self.config_warnings, "audit": self.audit.status(),
                "state": {"directory": str(self.state), "mode": oct(self.state.stat().st_mode & 0o777)}}

    def local_status(self):
        """Fast local heartbeat. This deliberately makes no Hermes HTTP request."""
        with self.db() as db:
            run_count = db.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        return {"ok": True, "upstream_checked": False, "registered_runs": run_count,
                "stale_run_seconds": self.stale_run_seconds,
                "approval_stale_seconds": self.approval_stale_seconds, "config_warnings": self.config_warnings,
                "audit": self.audit.status(),
                "state": {"directory": str(self.state), "mode": oct(self.state.stat().st_mode & 0o777)}}

    @staticmethod
    def ident(value, label):
        if not isinstance(value, str) or not IDENT.fullmatch(value):
            raise BridgeError(f"Invalid {label}.")
        return value

    def owned(self, run_id):
        self.ident(run_id, "run ID")
        with self.db() as db:
            row = db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            raise BridgeError("Run is not registered to this bridge.")
        return row

    def submit(self, prompt, request_id, session_id=None, model=None, provider=None, model_options=None):
        self.ident(request_id, "request ID")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 32000:
            raise BridgeError("Prompt must be 1-32000 characters.")
        model, provider, model_options = self.model_selection(model, provider, model_options)
        body = {"input": prompt}
        if session_id:
            self.ident(session_id, "session ID")
            with self.db() as db:
                owned = db.execute("SELECT 1 FROM runs WHERE session_id=?", (session_id,)).fetchone()
            if not owned:
                raise BridgeError("Continue only a session returned by this bridge's task status.")
            if model or provider or model_options:
                raise BridgeError("Model overrides are only allowed for a new session; continue this session without model fields.")
            body["session_id"] = session_id
        else:
            if model:
                body["model"] = model
            if provider:
                body["provider"] = provider
            if model_options:
                body["model_options"] = model_options
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        options_json = json.dumps(model_options, sort_keys=True, separators=(",", ":")) if model_options else None
        with self.db() as db:
            db.execute("INSERT OR IGNORE INTO runs(request_id,fingerprint,created,requested_model,requested_provider,requested_model_options) VALUES(?,?,?,?,?,?)",
                       (request_id, digest, time.time(), model, provider, options_json))
            row = db.execute("SELECT * FROM runs WHERE request_id=?", (request_id,)).fetchone()
            fresh = db.execute("SELECT changes()").fetchone()[0] == 1
        if row["fingerprint"] != digest:
            raise BridgeError("Request ID already used with different input; do not reuse it.")
        if row["run_id"]:
            return {"run_id": row["run_id"], "request_id": request_id, "replayed_locally": True,
                    **self.row_selection(row)}
        if not fresh:
            if time.time() - row["created"] > 23 * 3600:
                raise BridgeError("Uncertain submission is older than the safe replay window. Inspect Hermes locally; do not submit a new request blindly.")
            contract = self.request("GET", "/v1/capabilities").get("features", {}).get("runs_idempotency", {})
            if not isinstance(contract, dict) or not contract.get("supported") or not contract.get("durable"):
                raise BridgeError("Previous acceptance is uncertain and durable replay is not advertised. Inspect Hermes locally before retrying.")
        result = self.request("POST", "/v1/runs", body,
                              {"Idempotency-Key": "chatgpt-bridge-" + request_id})
        run_id = self.ident(result.get("run_id"), "Hermes response run ID")
        with self.db() as db:
            db.execute("UPDATE runs SET run_id=? WHERE request_id=?", (run_id, request_id))
        self.audit.record("hermes", "submit", run_id, str(result.get("status", "started")),
                          {"request_id": request_id, "prompt_chars": len(prompt),
                           "model_override": bool(model), "provider_override": bool(provider)})
        return {"run_id": run_id, "request_id": request_id, "status": result.get("status", "started"),
                "replayed": bool(result.get("replayed", False)),
                "requested_model": model, "requested_provider": provider,
                "requested_model_options": model_options,
                "next": "Use hermes_task_status; this response only acknowledges submission."}

    def fetch(self, run_id):
        row = self.owned(run_id)
        if row["result"]:
            cached = json.loads(row["result"])
            if cached.get("status") in TERMINAL:
                return cached
        result = self.request("GET", f"/v1/runs/{run_id}")
        if result.get("run_id") != run_id:
            raise BridgeError("Hermes returned a mismatched run ID.")
        session = result.get("session_id")
        if session:
            self.ident(session, "Hermes response session ID")
        reported_model = result.get("model") if isinstance(result.get("model"), str) else None
        with self.db() as db:
            db.execute("UPDATE runs SET session_id=COALESCE(?,session_id),reported_model=COALESCE(?,reported_model),result=? WHERE run_id=?",
                       (session, reported_model, json.dumps(result, ensure_ascii=False), run_id))
        return result

    def status(self, run_id):
        result = self.fetch(run_id)
        row = self.owned(run_id)
        out = {k: result[k] for k in ("run_id", "status", "session_id", "model", "usage", "last_event") if k in result}
        out.update(self.row_selection(row))
        if row["reported_model"]:
            out["reported_model"] = row["reported_model"]
        out["output_chars"] = len(str(result.get("output") or ""))
        age_seconds = max(0, int(time.time() - row["created"]))
        out["age_seconds"] = age_seconds
        if result.get("status") not in TERMINAL and age_seconds >= self.stale_run_seconds:
            out["stale"] = True
        if result.get("error"):
            out["error"] = str(result["error"])[:2000]
        if result.get("status") == "waiting_for_approval":
            out["approval"] = result.get("approval")
            if age_seconds >= self.approval_stale_seconds:
                out["approval_stale"] = True
            out["next"] = f"Ask the user to review locally: ./bridge.sh approve {run_id} (or deny). Do not bypass the pending approval."
        return out

    def result(self, run_id, offset=0, max_chars=12000):
        if offset < 0 or not 1 <= max_chars <= 24000:
            raise BridgeError("Invalid result page: offset >= 0, max_chars 1-24000.")
        raw = self.fetch(run_id)
        row = self.owned(run_id)
        output = str(raw.get("output") or "")
        end = min(len(output), offset + max_chars)
        return {"run_id": run_id, "status": raw.get("status"), "session_id": raw.get("session_id"),
                "output": output[offset:end], "total_chars": len(output),
                "next_offset": end if end < len(output) else None,
                "error": str(raw.get("error") or "")[:2000], "usage": raw.get("usage"),
                **self.row_selection(row), "reported_model": row["reported_model"]}

    def stop(self, run_id):
        self.owned(run_id)
        result = self.request("POST", f"/v1/runs/{run_id}/stop", {})
        self.audit.record("hermes", "cancel", run_id, str(result.get("status", "stopping")), {})
        return {"run_id": run_id, "status": result.get("status", "stopping"),
                "note": "Stop is cooperative. Poll status until cancelled/completed/failed; previous effects are not undone."}

    def recent(self):
        with self.db() as db:
            rows = db.execute("SELECT request_id,run_id,session_id,created,requested_model,requested_provider,requested_model_options,reported_model FROM runs ORDER BY created DESC LIMIT 30").fetchall()
        return {"runs": [dict(r) for r in rows], "note": "Local registration list, not live run status."}

    def usage_summary(self, limit=1000):
        if not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise BridgeError("limit must be 1-1000.")
        with self.db() as db:
            rows = db.execute("SELECT run_id,requested_model,requested_provider,reported_model,result FROM runs WHERE result IS NOT NULL ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
        totals = {"runs_with_usage": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        by_model = {}
        for row in rows:
            try: usage = json.loads(row["result"]).get("usage") or {}
            except (ValueError, TypeError): continue
            if not isinstance(usage, dict): continue
            vals = {k: usage.get(k, 0) for k in ("input_tokens", "output_tokens", "total_tokens")}
            if not all(isinstance(v, (int, float)) and v >= 0 for v in vals.values()): continue
            totals["runs_with_usage"] += 1
            for k, v in vals.items(): totals[k] += v
            model = row["reported_model"] or row["requested_model"] or "unknown"
            bucket = by_model.setdefault(model, {"runs": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
            bucket["runs"] += 1
            for k, v in vals.items(): bucket[k] += v
        return {"scope": "bridge-owned runs with cached Hermes usage", "sample_limit": limit, "totals": totals, "by_model": by_model,
                "cost": "not calculated; pricing is provider-specific and not stored by the bridge."}

    def usage_export(self, limit=1000):
        if not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise BridgeError("limit must be 1-1000.")
        with self.db() as db:
            rows = db.execute("SELECT request_id,run_id,created,requested_model,requested_provider,reported_model,result FROM runs WHERE result IS NOT NULL ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
        records = []
        for row in rows:
            try: raw = json.loads(row["result"]); usage = raw.get("usage") or {}
            except (ValueError, TypeError): usage = {}
            records.append({"request_id": row["request_id"], "run_id": row["run_id"], "created": row["created"], "status": raw.get("status") if isinstance(raw, dict) else None,
                            "requested_model": row["requested_model"], "requested_provider": row["requested_provider"], "reported_model": row["reported_model"],
                            "input_tokens": usage.get("input_tokens") if isinstance(usage, dict) else None, "output_tokens": usage.get("output_tokens") if isinstance(usage, dict) else None, "total_tokens": usage.get("total_tokens") if isinstance(usage, dict) else None})
        return {"records": records, "format": "JSON; contains no prompts, output, API keys, or provider pricing."}

    def resolve_local(self, run_id, choice, confirm):
        if choice not in ("once", "deny"):
            raise BridgeError("Only once or deny is permitted by the local helper.")
        current = self.fetch(run_id)
        approval = current.get("approval") or {}
        req_id = approval.get("request_id")
        if current.get("status") != "waiting_for_approval" or not isinstance(req_id, str) or not req_id:
            raise BridgeError("No exact pending approval request ID. Inspect Hermes locally.")
        if not confirm(self.clean(approval), choice):
            return {"sent": False}
        # Re-read after the human decision to avoid approving a different/stale request.
        check = self.fetch(run_id)
        if check.get("status") != "waiting_for_approval" or (check.get("approval") or {}).get("request_id") != req_id:
            raise BridgeError("Approval changed during review; review the new request.")
        return self.request("POST", f"/v1/runs/{run_id}/approval",
                            {"choice": choice, "request_id": req_id, "resolve_all": False})
