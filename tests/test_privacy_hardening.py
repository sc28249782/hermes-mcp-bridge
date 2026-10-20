"""Synthetic privacy regressions; no native model executable is invoked."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx

from core import Bridge, BridgeError, METADATA_MAX_BYTES
from codex_core import CodexRunner, CodexError, RESULT_READ_MAX_BYTES, RESULT_READ_CHUNK_BYTES
from test_bridge import FakeHermes


class TestHermesMetadata(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fake = FakeHermes()
        self.bridge = Bridge('http://127.0.0.1:8642', 'test-secret-123', self.root,
                             httpx.MockTransport(self.fake))
        self.rid = self.bridge.submit('fixture', 'privacy-fixture')['run_id']

    def tearDown(self):
        self.bridge.client.close()
        self.tmp.cleanup()

    def test_status_excludes_nested_sensitive_and_oversized_upstream_fields(self):
        self.fake.runs[self.rid].update(status='waiting_for_approval',
            error={'private': 'SENSITIVE_FIXTURE' * 10000},
            approval={'command': 'SENSITIVE_FIXTURE', 'description': 'x' * 100000},
            last_event={'private': 'SENSITIVE_FIXTURE'}, model='private value with spaces',
            usage={'total_tokens': 3, 'input_tokens': True, 'output_tokens': -1,
                   'cache_read_tokens': 2**53, 'nested': {'private': 'SENSITIVE_FIXTURE'}},
            private='SENSITIVE_FIXTURE')
        status = self.bridge.status(self.rid)
        self.assertEqual(status['approval'], {'required': True})
        self.assertEqual(status['error'], 'Hermes reported an error; inspect Hermes locally.')
        self.assertEqual(status['usage'], {'total_tokens': 3})
        self.assertEqual(status['last_event'], 'unknown')
        self.assertNotIn('model', status)
        encoded = json.dumps(status, ensure_ascii=True, separators=(',', ':')).encode('ascii')
        self.assertLessEqual(len(encoded), METADATA_MAX_BYTES)
        self.assertNotIn(b'SENSITIVE_FIXTURE', encoded)

    def test_result_filters_metadata_but_preserves_explicit_content(self):
        self.fake.runs[self.rid].update(output='EXPLICIT_CONTENT_FIXTURE',
            error='SENSITIVE_ERROR_FIXTURE', usage={'total_tokens': 4, 'private': 'SENSITIVE_ERROR_FIXTURE'})
        result = self.bridge.result(self.rid)
        self.assertEqual(result['output'], 'EXPLICIT_CONTENT_FIXTURE')
        self.assertIsNone(result['next_offset'])
        self.assertEqual(result['usage'], {'total_tokens': 4})
        self.assertNotIn('SENSITIVE_ERROR_FIXTURE', json.dumps(result))

    def test_unknown_status_shapes_remain_unknown_across_cached_fetches(self):
        for value in ({'private': 'fixture'}, ['completed'], 'private-status-fixture'):
            with self.bridge.db() as db:
                db.execute('UPDATE runs SET result=NULL WHERE run_id=?', (self.rid,))
            self.fake.runs[self.rid]['status'] = value
            self.assertEqual(self.bridge.status(self.rid)['status'], 'unknown')
            self.assertEqual(self.bridge.status(self.rid)['status'], 'unknown')

    def test_local_approval_still_previews_and_revalidates_exact_request(self):
        self.fake.pending = 'exact-fixture-request'
        self.assertEqual(self.bridge.status(self.rid)['approval'], {'required': True})
        previews = []
        def confirm(value, choice):
            previews.append(value)
            return True
        self.bridge.resolve_local(self.rid, 'once', confirm)
        self.assertEqual(previews[0]['command'], 'rm example.txt')
        self.assertEqual(self.fake.approvals, [{'choice': 'once', 'request_id': self.fake.pending, 'resolve_all': False}])

    def test_known_key_cannot_reappear_in_legacy_model_metadata(self):
        self.fake.runs[self.rid]['model'] = 'test-secret-123'
        with self.bridge.db() as db:
            db.execute('UPDATE runs SET requested_model=? WHERE run_id=?', ('test-secret-123', self.rid))
        self.assertNotIn('test-secret-123', json.dumps(self.bridge.status(self.rid)))

    def test_metadata_size_guard_fails_closed(self):
        with patch.object(self.bridge, '_metadata', return_value={'status': 'running', 'unexpected': 'x' * 8193}):
            with self.assertRaisesRegex(BridgeError, '^Hermes metadata exceeds the bridge limit'):
                self.bridge.status(self.rid)

    def test_transport_limits_are_explicit_and_errors_do_not_echo_exception(self):
        self.assertEqual(self.bridge.client.timeout.connect, 5)
        for attr in ('read', 'write', 'pool'):
            self.assertEqual(getattr(self.bridge.client.timeout, attr), 25)
        oversized = httpx.MockTransport(lambda _: httpx.Response(200, content=b' ' * 4000001))
        with httpx.Client(transport=oversized) as client, patch.object(self.bridge, 'client', client):
            with self.assertRaisesRegex(BridgeError, 'response exceeds'):
                self.bridge.request('GET', 'http://127.0.0.1:8642/fixture')
        def timeout(_):
            raise httpx.ReadTimeout('SENSITIVE_EXCEPTION_FIXTURE')
        with httpx.Client(transport=httpx.MockTransport(timeout)) as client, patch.object(self.bridge, 'client', client):
            with self.assertRaises(BridgeError) as caught:
                self.bridge.request('GET', 'http://127.0.0.1:8642/fixture')
            self.assertNotIn('SENSITIVE_EXCEPTION_FIXTURE', str(caught.exception))

    def test_existing_state_mode_is_repaired(self):
        self.bridge.client.close()
        self.root.chmod(0o755)
        self.bridge = Bridge('http://127.0.0.1:8642', 'test-secret-123', self.root,
                             httpx.MockTransport(self.fake))
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)

    def test_state_permission_failure_is_sanitized(self):
        with patch.object(Path, 'chmod', side_effect=PermissionError('/private-fixture-path')):
            with self.assertRaisesRegex(BridgeError, '^Bridge state directory could not be secured.$'):
                Bridge('http://127.0.0.1:8642', 'test-secret-123', self.root)


class TrackedReader:
    def __init__(self, stream, sizes, after_read=None):
        self.stream, self.sizes, self.after_read = stream, sizes, after_read

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()

    def fileno(self):
        return self.stream.fileno()

    def read(self, size):
        if not 0 < size <= RESULT_READ_CHUNK_BYTES:
            raise AssertionError('unbounded read')
        self.sizes.append(size)
        data = self.stream.read(size)
        if self.after_read:
            callback, self.after_read = self.after_read, None
            callback()
        return data


class TestCodexBoundedResults(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / 'work'
        self.workspace.mkdir()
        self.runner = CodexRunner({'allowed_workspaces': [str(self.workspace)]}, self.root / 'state')
        self.job = self.runner.submit('fixture', str(self.workspace), 'workspace-write')['job_id']
        self.log = Path(self.runner._row(self.job)['log_path'])

    def tearDown(self):
        self.tmp.cleanup()

    def tracked(self, sizes, callback=None):
        original = Path.open
        def opened(path, *args, **kwargs):
            stream = original(path, *args, **kwargs)
            return TrackedReader(stream, sizes, callback) if path == self.log else stream
        return patch.object(Path, 'open', opened)

    def test_unicode_newlines_invalid_utf8_and_offsets_across_chunks(self):
        data = b'a' * 65535 + 'ไทย😀\r\n'.encode() + b'\xff\r' + b'b' * 70000
        self.log.write_bytes(data)
        expected = data.decode('utf-8', errors='replace').replace('\r\n', '\n').replace('\r', '\n')
        sizes = []
        with self.tracked(sizes), patch.object(Path, 'read_text', side_effect=AssertionError('whole-file read')):
            for offset, count in ((0, 24000), (65534, 10), (65538, 12000), (len(expected) - 3, 100), (10**12, 10)):
                result = self.runner.result(self.job, offset, count)
                self.assertEqual(result['output'], expected[offset:offset + count])
                self.assertEqual(result['total_chars'], len(expected))
                end = min(len(expected), offset + count)
                self.assertEqual(result['next_offset'], end if end < len(expected) else None)
        self.assertTrue(sizes)
        self.assertLessEqual(max(sizes), 65536)

    def test_oversized_sparse_snapshot_rejected_before_any_content_read(self):
        with self.log.open('wb') as stream:
            stream.truncate(RESULT_READ_MAX_BYTES + 1)
        sizes = []
        with self.tracked(sizes), self.assertRaisesRegex(CodexError, '^Codex output exceeds the result read limit'):
            self.runner.result(self.job)
        self.assertEqual(sizes, [])

    def test_exact_cap_is_read_in_bounded_chunks(self):
        with self.log.open('wb') as stream:
            stream.truncate(RESULT_READ_MAX_BYTES)
        sizes = []
        with self.tracked(sizes):
            result = self.runner.result(self.job, RESULT_READ_MAX_BYTES - 2, 2)
        self.assertEqual(result['output'], '\x00\x00')
        self.assertEqual(result['total_chars'], RESULT_READ_MAX_BYTES)
        self.assertEqual(sum(sizes), RESULT_READ_MAX_BYTES)

    def test_append_during_read_does_not_expand_snapshot_budget(self):
        initial = b'a' * 70000
        self.log.write_bytes(initial)
        def append():
            with open(self.log, 'ab') as stream:
                stream.write('ไทย'.encode())
        sizes = []
        with self.tracked(sizes, append):
            first = self.runner.result(self.job, 69998, 10)
        self.assertEqual(sum(sizes), len(initial))
        self.assertEqual(first['output'], 'aa')
        second = self.runner.result(self.job, 70000, 10)
        self.assertEqual(second['output'], 'ไทย')
        self.assertEqual(second['total_chars'], 70003)

    def test_append_before_read_does_not_prefetch_past_snapshot(self):
        initial = b'a' * 70000
        self.log.write_bytes(initial)
        sizes, raw_offsets = [], []
        original_read = TrackedReader.read

        def append_then_read(reader, size):
            if not raw_offsets:
                # Append after fstat but before the first content read.
                with open(self.log, 'ab') as stream:
                    stream.write(b'b' * (2 * RESULT_READ_CHUNK_BYTES))
            data = original_read(reader, size)
            raw_offsets.append(os.lseek(reader.fileno(), 0, os.SEEK_CUR))
            return data

        with self.tracked(sizes), patch.object(TrackedReader, 'read', append_then_read):
            result = self.runner.result(self.job, len(initial) - 2, 10)
        self.assertEqual(result['output'], 'aa')
        self.assertEqual(result['total_chars'], len(initial))
        self.assertIsNone(result['next_offset'])
        self.assertEqual(sum(sizes), len(initial))
        self.assertTrue(raw_offsets)
        self.assertLessEqual(max(raw_offsets), len(initial))

    def test_truncate_during_read_never_returns_a_partial_success(self):
        self.log.write_bytes(b'a' * 131072)
        def truncate():
            os.truncate(self.log, 0)
        with self.tracked([], truncate), self.assertRaisesRegex(CodexError, 'changed while reading'):
            self.runner.result(self.job)

    def test_missing_log_retains_empty_result(self):
        result = self.runner.result(self.job)
        self.assertEqual((result['output'], result['total_chars'], result['next_offset']), ('', 0, None))

    def test_existing_state_and_log_modes_are_repaired(self):
        self.runner.state.chmod(0o755)
        self.runner.logs.chmod(0o777)
        reloaded = CodexRunner({'allowed_workspaces': [str(self.workspace)]}, self.runner.state)
        for path in (reloaded.state, reloaded.logs):
            self.assertEqual(path.stat().st_mode & 0o777, 0o700)

    def test_directory_permission_failure_is_sanitized(self):
        original = Path.chmod
        for denied in (self.runner.state, self.runner.logs):
            def chmod(path, mode, **kwargs):
                if path == denied:
                    raise PermissionError('/private-fixture-path')
                return original(path, mode, **kwargs)
            with patch.object(Path, 'chmod', chmod), self.assertRaises(CodexError) as caught:
                CodexRunner({'allowed_workspaces': [str(self.workspace)]}, self.runner.state)
            self.assertNotIn('/private-fixture-path', str(caught.exception))

    def test_read_failure_is_sanitized(self):
        self.log.write_text('fixture')
        with patch.object(TrackedReader, 'read', side_effect=OSError('/private-fixture-path')):
            with self.tracked([]), self.assertRaisesRegex(CodexError, '^Codex output is unavailable.$'):
                self.runner.result(self.job)
