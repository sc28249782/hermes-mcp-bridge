"""Test-only durable ledger and owned child. No real backend or model contract proof."""
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import sqlite3

from checkpoint import Facts, Hold, canonical

ROOT = Path(__file__).resolve().parents[2]


def envelope():
    return json.loads((ROOT/'docs/examples/handoff-checkpoint-v1.synthetic.json').read_bytes())


def encode(e):
    e['payload_sha256'] = hashlib.sha256(canonical(e['payload'])).hexdigest()
    return canonical(e)


def ready(backend='opencode', unknown_job=False):
    e = envelope()
    p = e['payload']
    p['repository']['worktree_state'] = 'clean'
    p['backend'].update(name=backend, request_id='request_fixture_001' if backend != 'codex' else None,
                        job_id=None if unknown_job else 'job_fixture_001', session_id='session_fixture_001',
                        input_fingerprint_ref='fingerprint_fixture_001')
    p['authorization'].update(authority_ref='authority_fixture_001', scope_refs=['scope_handoff_observe'])
    refs = frozenset([p['task']['goal_ref'], p['verification']['acceptance_profile_ref'],
                     *p['task']['criteria_refs'], *p['task']['pending_step_refs'],
                     'input_fixture_001', 'fingerprint_fixture_001'])
    raw = encode(e)
    facts = Facts((p['chain_id'], p['generation'], e['payload_sha256']), dict(p['repository']), refs,
                  'authority_fixture_001', frozenset(['scope_handoff_observe']),
                  '2026-11-02T01:00:00Z', '2026-11-02T00:00:00Z', backend,
                  p['backend']['workspace_ref'], None, True, {}, frozenset(), False,
                  p['task']['goal_ref'], frozenset(p['task']['criteria_refs']),
                  p['verification']['acceptance_profile_ref'])
    return e, raw, facts


def _worker(db_path, artifact, conn):
    try:
        with sqlite3.connect(db_path) as db:
            db.execute("UPDATE jobs SET status='running' WHERE job_id='job_fixture_001'")
            db.execute('INSERT INTO effects VALUES (?)', ('job_fixture_001',))
        conn.send('accepted')
        command = conn.recv()
        if command == 'crash':
            import os
            os._exit(91)
        with sqlite3.connect(db_path) as db:
            db.execute('BEGIN IMMEDIATE')
            cancelled = db.execute('SELECT cancel_flag FROM jobs').fetchone()[0]
            if command == 'complete' and not cancelled:
                Path(artifact).write_bytes(b'fixture verified artifact\n')
                status, exit_code = 'completed', 0
            else:
                status, exit_code = 'cancelled', -15
            db.execute('UPDATE jobs SET status=?,exit_code=? WHERE job_id=?', (status, exit_code, 'job_fixture_001'))
        conn.send('terminal')
    finally:
        conn.close()


class BackendFixture:
    def __init__(self, root):
        self.db = str(Path(root)/'fixture.sqlite3')
        self.artifact = Path(root)/'artifact.txt'
        self.child = None
        self.channel = None
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE IF NOT EXISTS jobs(request_id TEXT PRIMARY KEY,job_id TEXT UNIQUE,fingerprint TEXT,status TEXT,exit_code INTEGER,cancel_flag INTEGER)')
            db.execute('CREATE TABLE IF NOT EXISTS effects(job_id TEXT PRIMARY KEY)')

    def admit(self, fingerprint='fingerprint_fixture_001'):
        with sqlite3.connect(self.db) as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT job_id,fingerprint FROM jobs WHERE request_id=?', ('request_fixture_001',)).fetchone()
            if row:
                if row[1] != fingerprint:
                    raise Hold('BINDING_MISMATCH')
                return row[0]
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?)', ('request_fixture_001', 'job_fixture_001', fingerprint, 'pending', None, 0))
        parent, child = mp.get_context('fork').Pipe()
        self.child = mp.get_context('fork').Process(target=_worker, args=(self.db, str(self.artifact), child))
        self.child.start()
        child.close()
        self.channel = parent
        if not parent.poll(5):
            raise AssertionError('fixture did not reach accepted boundary')
        parent.recv()  # Deliberately discard ACK: recovery must use durable ledger.
        return 'job_fixture_001'

    def observation(self):
        with sqlite3.connect(self.db) as db:
            row = db.execute('SELECT request_id,job_id,fingerprint,status,exit_code FROM jobs').fetchone()
        return dict(zip(('request_id','job_id','input_fingerprint_ref','status','exit_code'), row), session_id='session_fixture_001', workspace_ref='workspace_fixture_001')

    def effects(self):
        with sqlite3.connect(self.db) as db:
            return db.execute('SELECT count(*) FROM effects').fetchone()[0]

    def cancel_request(self):
        with sqlite3.connect(self.db) as db:
            return db.execute("UPDATE jobs SET cancel_flag=1 WHERE status='running'").rowcount == 1

    def finish(self, command):
        self.channel.send(command)
        self.child.join(5)
        if self.child.is_alive():
            raise AssertionError('fixture termination not observed')

    def close(self):
        if self.child is not None:
            if self.child.is_alive():
                # Fixture-owned direct child only; no stored backend PID signalling.
                self.child.terminate()
                self.child.join(5)
            if self.child.is_alive():
                self.child.kill()
                self.child.join(5)
            self.child.close()
        if self.channel is not None:
            self.channel.close()
