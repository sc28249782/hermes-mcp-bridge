"""SPEC §20: synthetic registry/CLI acceptance, without any native backend."""
from contextlib import ExitStack, closing, redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import bridge
import context_read as cr
from config_schema import ConfigError, load_bridge_config
from contexts import ContextRegistry, ContextError
from test_contexts import Audit

ROOT = Path(__file__).resolve().parents[1]


class TestContextP1(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='context #?% ')
        self.state = Path(self.tmp.name)
        self.audit = Audit()
        self.registry = ContextRegistry(self.state, self.audit, soft_cap=2)
        self.path = self.registry.path

    def tearDown(self):
        self.tmp.cleanup()

    def insert(self, name, closed=0, **refs):
        values = {k: None for k in ('hermes_session_id', 'hermes_run_id', 'codex_workspace', 'codex_job_id')}
        values.update(refs)
        with self.registry.db() as db:
            db.execute('INSERT INTO contexts VALUES(?,?,?,?,?,?,?,?,?)',
                       (name, 'PRIVATE_LABEL', 1, 1, closed, *values.values()))

    def cli(self, *argv):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cr.preview_cli(list(argv))
        self.assertEqual(err.getvalue(), '')
        return code, json.loads(out.getvalue())

    def test_config_defaults_types_ranges_unknown_values(self):
        config = dict(schema_version=1, api_url='unused', hermes_env='unused')
        path = self.state / 'bridge-config.json'
        path.write_text(json.dumps(config))
        self.assertNotIn('contexts', load_bridge_config(self.state)[0])
        self.assertEqual(ContextRegistry(self.state, self.audit).soft_cap, 1000)
        for value in (1, 1000, 100000):
            config['contexts'] = dict(soft_cap=value, unknown='PRIVATE_VALUE')
            path.write_text(json.dumps(config))
            loaded, warnings = load_bridge_config(self.state)
            self.assertEqual(loaded['contexts']['soft_cap'], value)
            self.assertTrue(any('contexts.unknown' in w for w in warnings))
            self.assertNotIn('PRIVATE_VALUE', str(warnings))
        for value in (True, False, 0, -1, 100001, 1.5, '2', None):
            config['contexts'] = dict(soft_cap=value)
            path.write_text(json.dumps(config))
            with self.subTest(value=value), self.assertRaises(ConfigError):
                load_bridge_config(self.state)
            with self.assertRaises(ContextError):
                ContextRegistry(self.state, self.audit, value)
        for value in (None, [], 'invalid'):
            config['contexts'] = value
            path.write_text(json.dumps(config))
            with self.assertRaises(ConfigError):
                load_bridge_config(self.state)

    def test_threshold_and_bounded_lower_bound_shapes(self):
        fields = {'state', 'soft_cap', 'rows_lower_bound', 'count_capped', 'soft_cap_reached', 'warning'}
        for n in range(6):
            value = self.registry.observation()
            self.assertEqual(set(value), fields)
            self.assertEqual(value['rows_lower_bound'], min(n, 3))
            self.assertEqual(value['count_capped'], n >= 3)
            self.assertEqual(value['soft_cap_reached'], n >= 2)
            self.assertEqual(value['warning'], 'context_soft_cap_reached' if n >= 2 else None)
            self.assertLessEqual(len(cr.compact(value)), 512)
            self.assertNotIn('PRIVATE', cr.compact(value))
            self.insert(str(n))

    def test_create_ack_survives_observation_failure_and_is_not_retried(self):
        with patch('context_read.registry_reader', side_effect=sqlite3.OperationalError('PRIVATE')):
            value = self.registry.create('created once')
        self.assertEqual(value['registry']['state'], 'unavailable')
        self.assertIsNone(value['registry']['rows_lower_bound'])
        self.assertEqual(len(self.registry.recent()['contexts']), 1)
        self.assertEqual(len(self.audit.events), 1)
        self.assertNotIn('PRIVATE', cr.compact(value))
        self.assertNotIn('registry', self.registry.status(value['context_id']))
        self.assertNotIn('registry', self.registry.recent()['contexts'][0])

    def test_soft_cap_does_not_reject_creates_or_change_status_recent(self):
        for i in range(5):
            created = self.registry.create('fixture')
            self.assertEqual(created['registry']['rows_lower_bound'], min(i + 1, 3))
            self.assertNotIn('registry', self.registry.status(created['context_id']))
        self.assertEqual(len(self.registry.recent()['contexts']), 5)
        self.assertEqual(len(self.audit.events), 5)

    def test_missing_observation_does_not_create_db(self):
        missing = self.state / 'absent.sqlite3'
        value = cr.observe_registry(missing)
        self.assertEqual(value['state'], 'unavailable')
        self.assertEqual(value['warning'], 'context_registry_unavailable')
        for key in ('rows_lower_bound', 'count_capped', 'soft_cap_reached'):
            self.assertIsNone(value[key])
        self.assertFalse(missing.exists())

    def test_selection_cutoff_types_and_each_reference(self):
        now = 100 * 86400
        cutoff = now - 30 * 86400
        for name, closed in [('equal', cutoff), ('older', 0), ('newer', cutoff + 1),
                             ('open', None), ('negative', -1), ('text', 'PRIVATE_TIMESTAMP'),
                             ('infinite', float('inf')), ('nan', float('nan'))]:
            self.insert(name, closed)
        for ref in ('hermes_session_id', 'hermes_run_id', 'codex_workspace', 'codex_job_id'):
            self.insert(ref, cutoff, **{ref: 'PRIVATE_BINDING'})
        before = self.path.read_bytes()
        mode = self.path.stat().st_mode
        with patch('context_read.time.time', return_value=now) as clock:
            value = cr.preview(self.state)
        clock.assert_called_once()
        self.assertEqual(value['candidate_count'], 2)
        self.assertFalse(value['has_more'])
        self.assertEqual(value['cutoff_utc'], cutoff)
        self.assertEqual(set(value), {'ok', 'mode', 'cutoff_utc', 'older_than_days', 'limit', 'candidate_count', 'has_more', 'note'})
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(mode, self.path.stat().st_mode)
        self.assertNotIn('PRIVATE', cr.compact(value))
        self.assertLessEqual(len(cr.compact(value)), 1024)

    def test_batch_boundaries_and_deterministic_order(self):
        for n in range(1002):
            self.insert(str(1002-n), n % 2)
        seen = []
        original = sqlite3.connect
        class Recording(sqlite3.Connection):
            def execute(self, sql, parameters=()):
                seen.append((sql, parameters))
                return super().execute(sql, parameters)
        with patch('context_read.sqlite3.connect', side_effect=lambda *a, **kw: original(*a, factory=Recording, **kw)):
            for limit in (1, 100, 1000):
                result = cr.preview(self.state, limit=limit)
                self.assertEqual(result['candidate_count'], limit)
                self.assertTrue(result['has_more'])
        selects = [(sql, params) for sql, params in seen if 'ORDER BY closed' in sql]
        self.assertEqual([params[1] for _, params in selects], [2, 101, 1001])
        self.assertTrue(all('closed ASC, context_id ASC' in sql and 'SELECT 1' in sql for sql, _ in selects))

    def test_read_only_uri_timeout_and_logical_sampling(self):
        self.insert('one')
        original = sqlite3.connect
        connections, queries = [], []
        class Recording(sqlite3.Connection):
            def execute(self, sql, parameters=()):
                queries.append((sql, parameters))
                return super().execute(sql, parameters)
        def connect(database, **kwargs):
            connections.append((database, kwargs))
            return original(database, factory=Recording, **kwargs)
        before = self.path.read_bytes()
        with patch('context_read.sqlite3.connect', side_effect=connect):
            self.registry.observation()
            cr.preview(self.state)
        self.assertTrue(all(u.endswith('?mode=ro') and '%23%3F%25' in u for u, _ in connections))
        self.assertTrue(all(k == dict(uri=True, timeout=1.0) for _, k in connections))
        self.assertIn(('SELECT 1 FROM contexts LIMIT ?', (3,)), queries)
        self.assertEqual(before, self.path.read_bytes())
        with cr.registry_reader(self.path) as db:
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('DELETE FROM contexts')

    def test_storage_schema_failure_has_constant_output_and_no_migration(self):
        self.path.unlink()
        cases = ['CREATE TABLE contexts(x TEXT)', 'CREATE VIEW contexts AS SELECT 1 AS x',
                 'CREATE TABLE contexts(context_id TEXT PRIMARY KEY, label TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL, closed REAL, hermes_session_id TEXT, hermes_run_id TEXT, codex_workspace TEXT, codex_job_id TEXT, extra TEXT)',
                 'CREATE TABLE contexts(context_id TEXT PRIMARY KEY, label TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL, closed REAL CHECK(closed>=0), hermes_session_id TEXT, hermes_run_id TEXT, codex_workspace TEXT, codex_job_id TEXT)']
        for sql in cases:
            # The connection context commits/rolls back; closing releases it.
            with closing(sqlite3.connect(self.path)) as db, db:
                db.execute(sql)
            before = self.path.read_bytes()
            code, result = self.cli('--state-dir', str(self.state))
            self.assertEqual((code, result), (1, dict(ok=False, error=cr.UNAVAILABLE)))
            self.assertEqual(before, self.path.read_bytes())
            self.path.unlink()
        self.assertEqual(self.cli('--state-dir', str(self.state))[0], 1)
        self.assertFalse(self.path.exists())
        self.path.write_bytes(b'PRIVATE_BAD_DATABASE')
        self.assertEqual(self.cli('--state-dir', str(self.state))[1]['error'], cr.UNAVAILABLE)

    def test_expected_argument_errors_never_echo_values(self):
        for args in [[], ['--state-dir', 'PRIVATE_RELATIVE'], ['--state-dir', str(self.state), '--apply'],
                     ['--state-dir', str(self.state), '--limit', 'PRIVATE'],
                     ['--state-dir', str(self.state), '--limit', '0'],
                     ['--state-dir', str(self.state), '--limit', '1001'],
                     ['--state-dir', str(self.state), '--older-than-days', '29'],
                     ['--state-dir', str(self.state), '--older-than-days', '36501'],
                     ['--state', str(self.state)]]:
            self.assertEqual(self.cli(*args), (2, dict(ok=False, error=cr.ARG_ERROR)))
        for age in (30, 36500):
            self.assertEqual(self.cli('--state-dir', str(self.state), '--older-than-days', str(age))[0], 0)

    def test_invalid_clocks_and_special_files(self):
        for now in (None, True, 'PRIVATE_CLOCK', float('nan'), float('inf'), -float('inf')):
            with patch('context_read.time.time', return_value=now):
                self.assertEqual(self.cli('--state-dir', str(self.state))[0], 1)
        self.path.unlink()
        os.mkfifo(self.path)
        self.assertEqual(self.cli('--state-dir', str(self.state))[0], 1)
        self.path.unlink()
        self.path.symlink_to('/dev/null')
        self.assertEqual(self.cli('--state-dir', str(self.state))[0], 1)

    def test_rollback_lock_wait_is_bounded_and_never_falls_back(self):
        db = sqlite3.connect(self.path)
        try:
            db.execute('BEGIN EXCLUSIVE')
            started = time.monotonic()
            self.assertEqual(self.cli('--state-dir', str(self.state))[0], 1)
            self.assertLess(time.monotonic() - started, 2)
            self.assertEqual(self.registry.observation()['state'], 'unavailable')
        finally:
            db.rollback()
            db.close()

    def test_wal_reads_committed_rows_without_explicit_sidecar_changes(self):
        db = sqlite3.connect(self.path)
        try:
            self.assertEqual(db.execute('PRAGMA journal_mode=WAL').fetchone()[0], 'wal')
            db.execute("INSERT INTO contexts VALUES('wal','PRIVATE',0,0,0,NULL,NULL,NULL,NULL)")
            db.commit()
            files = set(self.state.iterdir())
            wal_bytes = Path(str(self.path) + '-wal').read_bytes()
            db.execute('BEGIN IMMEDIATE')
            db.execute("UPDATE contexts SET closed=NULL")
            result = cr.preview(self.state)
            self.assertEqual(result['candidate_count'], 1)
            self.assertEqual(files, set(self.state.iterdir()))
            self.assertEqual(wal_bytes, Path(str(self.path) + '-wal').read_bytes())
            # SQLite may update shared-memory read marks; no byte-stability claim for shm.
        finally:
            db.rollback()
            db.close()

    @unittest.skipIf(os.geteuid() == 0, "root bypasses POSIX write permissions; run this case as an unprivileged user")
    def test_read_only_permissions_in_isolated_cli(self):
        self.insert('old')
        self.path.chmod(0o444)
        self.state.chmod(0o555)
        try:
            with self.assertRaises(PermissionError):
                self.path.open("ab").close()
            script = 'import sys; from context_read import preview_cli; sys.exit(preview_cli(sys.argv[1:]))'
            run = subprocess.run([sys.executable, '-c', script, '--state-dir', str(self.state)],
                                 cwd=ROOT, capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['candidate_count'], 1)
            self.assertEqual(run.stderr, '')
        finally:
            self.state.chmod(0o700)
            self.path.chmod(0o600)

    @unittest.skipIf(os.geteuid() == 0, "root bypasses POSIX write permissions; run this case as an unprivileged user")
    def test_wal_without_sidecars_cannot_bypass_read_only_directory(self):
        with self.registry.db() as db:
            db.execute('PRAGMA journal_mode=WAL')
        self.assertFalse(Path(str(self.path) + '-shm').exists())
        before = self.path.read_bytes()
        self.path.chmod(0o444)
        self.state.chmod(0o555)
        try:
            code, value = self.cli('--state-dir', str(self.state))
            self.assertEqual((code, value), (1, dict(ok=False, error=cr.UNAVAILABLE)))
            self.assertEqual(before, self.path.read_bytes())
            self.assertEqual(set(self.state.iterdir()), {self.path})
        finally:
            self.state.chmod(0o700)
            self.path.chmod(0o600)

    def test_main_early_dispatch_never_constructs_backends_or_reads_config(self):
        with ExitStack() as stack:
            for target in ('bridge.Bridge.from_config', 'bridge.CodexRunner.from_config',
                           'bridge.HandsRuntime.from_config', 'bridge.OpenCodeRunner.from_config',
                           'bridge.OpenCodeTasks.from_config', 'bridge.ContextRegistry',
                           'config_schema.load_bridge_config'):
                stack.enter_context(patch(target, side_effect=AssertionError(target)))
            stack.enter_context(patch.object(sys, 'argv', ['bridge.py', 'context-prune-preview', '--state-dir', str(self.state)]))
            out = stack.enter_context(redirect_stdout(StringIO()))
            with self.assertRaises(SystemExit) as done:
                bridge.main()
            self.assertEqual(done.exception.code, 0)
            self.assertTrue(json.loads(out.getvalue())['ok'])

    def test_script_dispatch_never_imports_backends_and_wrapper_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('bridge.py', 'bridge.sh', 'context_read.py'):
                (root / name).write_bytes((ROOT / name).read_bytes())
            for name in ('core', 'codex_core', 'hands_core', 'contexts', 'opencode_core', 'opencode_tasks', 'config_schema', 'events_probe'):
                (root / (name + '.py')).write_text('raise AssertionError("BACKEND_IMPORT")')
            (root / '.venv/bin').mkdir(parents=True)
            (root / '.venv/bin/python').symlink_to(sys.executable)
            env = dict(os.environ, BRIDGE_EVENTS_PROBE='1')
            for args in (['--state-dir', str(self.state)], ['--state-dir', 'PRIVATE_RELATIVE'], ['--help']):
                run = subprocess.run(['bash', str(root / 'bridge.sh'), 'context-prune-preview', *args],
                                     capture_output=True, text=True, env=env, timeout=10)
                self.assertEqual(run.returncode, 2 if 'PRIVATE_RELATIVE' in args else 0, run.stderr)
                self.assertEqual(run.stderr, '')
                self.assertNotIn('PRIVATE', run.stdout)


if __name__ == '__main__':
    unittest.main()
