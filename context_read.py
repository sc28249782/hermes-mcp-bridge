"""Read-only context aggregates and local preview; no runtime initialization."""
from contextlib import contextmanager
import argparse
import json
import math
from pathlib import Path
import re
import sqlite3
import stat
import time

DEFAULT_SOFT_CAP = 1000
LOCK_TIMEOUT = 1.0
PREVIEW_NOTE = "Preview only; no rows are deleted. SQLite may use locks or sidecar files."
ARG_ERROR = "Invalid context preview arguments."
UNAVAILABLE = "Context preview is unavailable."
_COLUMNS = [
    ("context_id", "TEXT", 0, None, 1, 0),
    ("label", "TEXT", 1, None, 0, 0),
    ("created", "REAL", 1, None, 0, 0),
    ("updated", "REAL", 1, None, 0, 0),
    ("closed", "REAL", 0, None, 0, 0),
    ("hermes_session_id", "TEXT", 0, None, 0, 0),
    ("hermes_run_id", "TEXT", 0, None, 0, 0),
    ("codex_workspace", "TEXT", 0, None, 0, 0),
    ("codex_job_id", "TEXT", 0, None, 0, 0),
]


def compact(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


@contextmanager
def registry_reader(path):
    """SQLite may use locks/sidecars; never request application-level writes."""
    path = Path(path)
    if not path.is_absolute() or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("Unsupported registry")
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=LOCK_TIMEOUT)
    try:
        table = db.execute("SELECT type, sql FROM sqlite_schema WHERE name='contexts'").fetchone()
        if not table or table[0] != "table" or not re.match(r"\s*CREATE\s+TABLE\b", table[1], re.I):
            raise ValueError("Unsupported registry")
        columns = db.execute("PRAGMA table_xinfo(contexts)").fetchall()
        if [tuple(row[1:]) for row in columns] != _COLUMNS:
            raise ValueError("Unsupported registry")
        # Reject constraints not represented by table_xinfo as well.
        if (re.search(r"\b(CHECK|REFERENCES|UNIQUE|COLLATE|GENERATED|STRICT|WITHOUT)\b", table[1], re.I)
                or db.execute("PRAGMA foreign_key_list(contexts)").fetchone()
                or any(row[3] != "pk" for row in db.execute("PRAGMA index_list(contexts)"))):
            raise ValueError("Unsupported registry")
        yield db
    finally:
        db.close()


def observe_registry(path, soft_cap=DEFAULT_SOFT_CAP):
    value = dict(state="unavailable", soft_cap=soft_cap, rows_lower_bound=None,
                 count_capped=None, soft_cap_reached=None, warning="context_registry_unavailable")
    try:
        with registry_reader(path) as db:
            # No labels, IDs or bindings enter Python. LIMIT is logical rows only.
            count = sum(1 for _ in db.execute("SELECT 1 FROM contexts LIMIT ?", (soft_cap + 1,)))
        reached = count >= soft_cap
        value.update(state="ok", rows_lower_bound=count, count_capped=count == soft_cap + 1,
                     soft_cap_reached=reached, warning="context_soft_cap_reached" if reached else None)
    except (OSError, sqlite3.Error, ValueError, OverflowError):
        pass
    return value


def preview(state_dir, older_than_days=30, limit=100):
    state = Path(state_dir)
    if not state.is_absolute() or not state.is_dir():
        raise OSError("Unavailable state")
    now = time.time()
    if type(now) not in (float, int) or not math.isfinite(now):
        raise ValueError("Invalid clock")
    cutoff = now - older_than_days * 86400
    with registry_reader(state / "contexts.sqlite3") as db:
        rows = db.execute("""SELECT 1 FROM contexts
            WHERE typeof(closed) IN ('integer','real') AND closed >= 0 AND closed <= ?
              AND hermes_session_id IS NULL AND hermes_run_id IS NULL
              AND codex_workspace IS NULL AND codex_job_id IS NULL
            ORDER BY closed ASC, context_id ASC LIMIT ?""", (cutoff, limit + 1)).fetchall()
    return dict(ok=True, mode="preview_only", cutoff_utc=cutoff, older_than_days=older_than_days,
                limit=limit, candidate_count=min(len(rows), limit), has_more=len(rows) > limit,
                note=PREVIEW_NOTE)


class _ArgumentsError(ValueError):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgumentsError()


def preview_cli(argv):
    parser = _Parser(prog="bridge.sh context-prune-preview", allow_abbrev=False,
                     description="Preview closed, unbound contexts. No rows are deleted.")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--older-than-days", type=int, default=30)
    parser.add_argument("--limit", type=int, default=100)
    try:
        args = parser.parse_args(argv)
        if (not Path(args.state_dir).is_absolute() or not 30 <= args.older_than_days <= 36500
                or not 1 <= args.limit <= 1000):
            raise _ArgumentsError()
    except (_ArgumentsError, ValueError):
        print(compact(dict(ok=False, error=ARG_ERROR)))
        return 2
    try:
        value = preview(args.state_dir, args.older_than_days, args.limit)
        output = compact(value)
        if len(output.encode("ascii")) > 1024:
            raise ValueError("Oversized result")
    except (OSError, sqlite3.Error, ValueError, OverflowError):
        print(compact(dict(ok=False, error=UNAVAILABLE)))
        return 1
    print(output)
    return 0
