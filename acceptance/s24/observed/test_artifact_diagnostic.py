"""Offline diagnostic contract; no live network, resource limit or alarm changes."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import ssl
import unittest
from unittest import mock
import urllib.error

HERE = Path(__file__).parent

def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

D = load('diagnostic_candidate', 'prepare_join_artifact_diagnostic.py')
B = load('baseline_artifact_controls', 'test_join_artifact.py')


# Reuse the 12 original mechanic controls against the new variant, unchanged.
# Original guard-output test belongs to the old one-line protocol; the new
# two-line guard contract is tested below. Original 13 controls still run in CI.
class SharedMechanicControls(unittest.TestCase):
    def setUp(self):
        self.binding = mock.patch.object(B, 'P', D)
        self.binding.start()
        self.addCleanup(self.binding.stop)

for name in sorted(B.ArtifactControls.__dict__):
    if name.startswith('test_') and name != 'test_main_rejects_without_ci_before_network':
        setattr(SharedMechanicControls, name, getattr(B.ArtifactControls, name))


class DiagnosticControls(unittest.TestCase):
    def test_broken_failure_stdout_does_not_escape_with_chained_private_error(self):
        sink = mock.Mock()
        sink.write.side_effect = OSError('PRIVATE_SENTINEL')
        with mock.patch.object(D.sys, 'argv', []), mock.patch.object(D.sys, 'stdout', sink):
            self.assertEqual(D.main(), 2)

    def test_main_success_two_frames_with_synthetic_receipt_binding(self):
        import resource
        raw = B.archive([('usr/bin/python3.12','file',b'synthetic never executed')])
        sha = hashlib.sha256(raw).hexdigest()
        receipt = json.dumps({'selection':{'url':D.URL,'provider_reported_archive_sha256':sha}}).encode()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(D.sys, 'platform', 'linux'))
            stack.enter_context(mock.patch.object(D.sys, 'argv', ['script','--download-and-inspect-diagnostic']))
            stack.enter_context(mock.patch.dict(D.os.environ, {'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted','RUNNER_OS':'Linux'}, clear=True))
            stack.enter_context(mock.patch.object(resource, 'setrlimit'))
            stack.enter_context(mock.patch.object(D.signal, 'signal'))
            alarm = stack.enter_context(mock.patch.object(D.signal, 'alarm'))
            stack.enter_context(mock.patch.object(D, 'ARCHIVE_SHA256', sha))
            stack.enter_context(mock.patch.object(D, 'SOURCE_RECEIPT_SHA256', hashlib.sha256(receipt).hexdigest()))
            stack.enter_context(mock.patch.object(D.Path, 'read_bytes', return_value=receipt))
            opener = mock.Mock()
            opener.open.return_value = B.Response(raw, {'Content-Length':str(len(raw))})
            stack.enter_context(mock.patch.object(D.urllib.request, 'build_opener', return_value=opener))
            out = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            self.assertEqual(D.main(), 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        result, frame = map(json.loads, lines)
        self.assertEqual(result['author_computed_archive_sha256'], sha)
        self.assertEqual((frame['stage'],frame['error']), ('COMPLETE','NONE'))
        self.assertTrue(frame['download_complete'] and frame['hash_complete'] and frame['digest_matches'])
        self.assertEqual(frame['received_bytes'], len(raw))
        self.assertFalse(result['j0_ready'] or frame['j0_ready'])
        self.assertEqual(alarm.call_args_list, [mock.call(120),mock.call(0)])
        opener.open.assert_called_once()

    def test_main_http_error_uses_actual_control_flow_without_network_or_limits(self):
        import resource
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(D.sys, 'platform', 'linux'))
            stack.enter_context(mock.patch.object(D.sys, 'argv', ['script', '--download-and-inspect-diagnostic']))
            stack.enter_context(mock.patch.dict(D.os.environ, {'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted','RUNNER_OS':'Linux'}, clear=True))
            stack.enter_context(mock.patch.object(resource, 'setrlimit'))
            stack.enter_context(mock.patch.object(D.signal, 'signal'))
            alarm = stack.enter_context(mock.patch.object(D.signal, 'alarm'))
            opener = mock.Mock()
            opener.open.side_effect = urllib.error.HTTPError('PRIVATE_SENTINEL',404,'PRIVATE_SENTINEL',{},None)
            stack.enter_context(mock.patch.object(D.urllib.request, 'build_opener', return_value=opener))
            out = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            self.assertEqual(D.main(), 2)
        frame = json.loads(out.getvalue().splitlines()[1])
        self.assertEqual((frame['stage'], frame['error']), ('HTTP_OPEN', 'HTTP_404'))
        self.assertFalse(frame['download_complete'])
        self.assertNotIn('PRIVATE_SENTINEL', out.getvalue())
        self.assertEqual(alarm.call_args_list, [mock.call(120),mock.call(0)])
        opener.open.assert_called_once()

    def test_diagnostic_failure_has_fixed_fallback_without_exception_text(self):
        with mock.patch.object(D.sys, 'argv', []), \
             mock.patch.object(D, 'diagnostic_line', side_effect=ValueError('PRIVATE_SENTINEL')), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(D.main(), 2)
        self.assertEqual(len(out.getvalue().splitlines()), 2)
        frame = json.loads(out.getvalue().splitlines()[1])
        self.assertEqual(frame, {'evidence_class':'j0-artifact-diagnostic-unavailable','schema':1,'error':'DIAGNOSTIC_UNAVAILABLE'})
        self.assertNotIn('PRIVATE_SENTINEL', out.getvalue())

    def test_fixed_error_enums_hide_exception_payloads(self):
        private = 'PRIVATE_SENTINEL_path_url_key'
        errors = [(D.Hold(private), 'PREDICATE_REJECTED'),
                  (D.RedirectHold(private), 'REDIRECT_REJECTED'),
                  (D.DeadlineHold(private), 'TIMEOUT'),
                  (TimeoutError(private), 'TIMEOUT'),
                  (ssl.SSLError(private), 'TLS_ERROR'),
                  (urllib.error.URLError(ssl.SSLError(private)), 'TLS_ERROR'),
                  (urllib.error.URLError(TimeoutError(private)), 'TIMEOUT'),
                  (urllib.error.URLError(private), 'TRANSPORT_ERROR'),
                  (OSError(private), 'IO_ERROR'), (MemoryError(private), 'MEMORY_LIMIT'),
                  (D.tarfile.ReadError(private), 'ARCHIVE_ERROR'),
                  (json.JSONDecodeError(private, private, 0), 'JSON_ERROR'),
                  (ValueError(private), 'UNEXPECTED_ERROR')]
        for code in (403, 404, 429, 500, 599, 302):
            errors.append((urllib.error.HTTPError(private, code, private, {}, None),
                           {403:'HTTP_403',404:'HTTP_404',429:'HTTP_429'}.get(code, 'HTTP_5XX' if code>=500 else 'HTTP_OTHER')))
        for error, expected in errors:
            with self.subTest(expected=expected):
                frame = json.loads(D.diagnostic_line(D.Diagnostic(), error))
                self.assertEqual(frame['error'], expected)
                self.assertNotIn(private, json.dumps(frame))
                self.assertEqual(frame['stage'], 'START')

    def test_guard_emits_constant_then_bounded_diagnostic_before_network(self):
        with mock.patch.object(D.sys, 'argv', ['script', '--download-and-inspect-diagnostic']), \
             mock.patch.dict(D.os.environ, {}, clear=True), \
             mock.patch.object(D, 'download', side_effect=AssertionError('network reached')), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(D.main(), 2)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0], 'HOLD: artifact preparation incomplete')
        self.assertEqual(len(lines), 2)
        frame = json.loads(lines[1])
        self.assertEqual((frame['stage'], frame['error']), ('GUARD', 'PREDICATE_REJECTED'))
        self.assertLessEqual(len(lines[1].encode()), 2048)

    def test_hash_mismatch_milestones_precede_parser(self):
        progress = D.Diagnostic()
        raw = b'wrong synthetic bytes'
        with mock.patch.object(D.tarfile, 'open', side_effect=AssertionError('parser reached')):
            with self.assertRaises(D.Hold):
                D.inspect(io.BytesIO(raw), 'a'*64, progress)
        frame = progress.frame(D.Hold())
        self.assertEqual(frame['stage'], 'ARCHIVE_HASH')
        self.assertEqual(frame['hashed_bytes'], len(raw))
        self.assertTrue(frame['hash_complete'])
        self.assertFalse(frame['digest_matches'])
        self.assertEqual(frame['archive_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(frame['parsed_members'], 0)

    def test_incomplete_hash_does_not_emit_partial_digest(self):
        progress = D.Diagnostic()
        with mock.patch.object(D, 'MAX_ARCHIVE', 4), self.assertRaises(D.Hold):
            D.inspect(io.BytesIO(b'12345'), 'a'*64, progress)
        frame = progress.frame(D.Hold())
        self.assertEqual(frame['hashed_bytes'], 5)
        self.assertFalse(frame['hash_complete'])
        self.assertIsNone(frame['archive_sha256'])
        self.assertIsNone(frame['digest_matches'])

    def test_real_parser_failure_stage_without_names(self):
        raw = B.archive([('../PRIVATE_SENTINEL', 'file', b'x')])
        progress = D.Diagnostic()
        with self.assertRaises(D.Hold):
            D.inspect(io.BytesIO(raw), hashlib.sha256(raw).hexdigest(), progress)
        line = D.diagnostic_line(progress, D.Hold('PRIVATE_SENTINEL'))
        self.assertEqual(json.loads(line)['stage'], 'ARCHIVE_PARSE')
        self.assertNotIn('PRIVATE_SENTINEL', line)
        self.assertTrue(progress.digest_matches)

    def test_download_complete_and_partial_body_milestones(self):
        for length, completed in [('3', True), ('4', False)]:
            progress = D.Diagnostic()
            opener = mock.Mock()
            opener.open.return_value = B.Response(b'123', {'Content-Length':length})
            with mock.patch.object(D.urllib.request, 'build_opener', return_value=opener):
                if completed:
                    D.download(io.BytesIO(), progress)
                else:
                    with self.assertRaises(D.Hold):
                        D.download(io.BytesIO(), progress)
            self.assertEqual(progress.stage, 'HTTP_BODY')
            self.assertEqual(progress.received_bytes, 3)
            self.assertIs(progress.download_complete, completed)
            self.assertFalse(progress.hash_complete)

    def test_http_error_and_header_rejection_are_distinct_stages(self):
        for opened in (False, True):
            progress = D.Diagnostic()
            opener = mock.Mock()
            if opened:
                opener.open.return_value = B.Response(b'x', {'Content-Encoding':'gzip'})
            else:
                opener.open.side_effect = urllib.error.HTTPError('PRIVATE_SENTINEL',404,'PRIVATE_SENTINEL',{},None)
            with mock.patch.object(D.urllib.request, 'build_opener', return_value=opener):
                try:
                    D.download(io.BytesIO(), progress)
                except Exception as error:
                    line = D.diagnostic_line(progress, error)
                else:
                    self.fail('expected failure')
            frame = json.loads(line)
            self.assertEqual(frame['stage'], 'HTTP_HEADERS' if opened else 'HTTP_OPEN')
            self.assertEqual(frame['error'], 'PREDICATE_REJECTED' if opened else 'HTTP_404')
            self.assertEqual(frame['received_bytes'], 0)
            self.assertNotIn('PRIVATE_SENTINEL', line)

    def test_instrumentation_preserves_success_receipt_and_limits(self):
        raw = B.archive([('usr/bin/python3.12','file',b'synthetic'), ('usr/bin/python3','link','python3.12')])
        expected = hashlib.sha256(raw).hexdigest()
        progress = D.Diagnostic()
        result = D.inspect(io.BytesIO(raw), expected, progress)
        self.assertEqual(result, B.P.inspect(io.BytesIO(raw), expected))
        self.assertEqual(progress.parsed_members, 2)
        for name in ('MAX_ARCHIVE','MAX_MEMBERS','MAX_LOGICAL_BYTES','MAX_SELECTED_FILE','CHUNK','URL','ARCHIVE_SHA256','SOURCE_RECEIPT_SHA256'):
            self.assertEqual(getattr(D,name),getattr(B.P,name))

    def test_frame_allowlist_and_false_flags(self):
        frame = D.Diagnostic().frame(None)
        self.assertEqual(set(frame), {'evidence_class','schema','stage','error','received_bytes','hashed_bytes',
            'download_complete','hash_complete','archive_sha256','digest_matches','parsed_members',
            'archive_verified_receipt','j0_ready','setup_ready','guest_imported','guest_started',
            'r1_complete','r2_authorized','scope_granted'})
        for key in ('archive_verified_receipt','j0_ready','setup_ready','guest_imported','guest_started','r1_complete','r2_authorized','scope_granted'):
            self.assertIs(frame[key], False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
