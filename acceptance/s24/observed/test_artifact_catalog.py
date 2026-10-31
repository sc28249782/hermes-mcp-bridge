"""Offline catalog controls: real synthetic tar; disclosed header/network faults.

No live URL, resource-limit change, provisioning or device operation. Reader
faults cover values that tar serialization cannot preserve (bool/invalid ints).
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import unittest
from unittest import mock

HERE = Path(__file__).parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = load('catalog_producer', 'catalog_join_artifact.py')
G = load('catalog_gate', 'gate_artifact_catalog.py')
S = load('catalog_strict_reference', 'prepare_join_artifact_diagnostic.py')


def item(name, kind=tarfile.REGTYPE, data=b'', **fields):
    info = tarfile.TarInfo(name)
    info.type = kind
    info.size = len(data)
    for key, value in fields.items():
        setattr(info, key, value)
    return info, data


def archive(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as handle:
        for info, data in entries:
            handle.addfile(info, io.BytesIO(data) if data else None)
    return output.getvalue()


def inspect(raw, progress=None):
    return P.inspect(io.BytesIO(raw), hashlib.sha256(raw).hexdigest(), progress)


def encode(first, second):
    def line(value):
        return value if isinstance(value, str) else json.dumps(value, separators=(',', ':'))
    return (line(first) + '\n' + line(second) + '\n').encode('ascii')


def success_frames():
    raw = archive([item('usr/bin/python3.12', data=b'synthetic'),
                   item('PRIVATE_DEVICE', tarfile.CHRTYPE, devmajor=1, devminor=3)])
    progress = P.Diagnostic()
    result = inspect(raw, progress)
    progress.received_bytes = len(raw)
    progress.download_complete = True
    progress.stage = 'COMPLETE'
    # Fixture digest substituted in both frames, not claimed as provider bytes.
    result['author_computed_archive_sha256'] = G.SHA
    progress.archive_sha256 = G.SHA
    return result, progress.frame(None)


class CatalogControls(unittest.TestCase):
    def reason(self, entries, expected):
        progress = P.Diagnostic()
        with self.assertRaises(P.PredicateHold) as caught:
            inspect(archive(entries), progress)
        self.assertEqual(caught.exception.args, ())
        self.assertEqual(caught.exception.reason, expected)
        frame = progress.frame(caught.exception)
        self.assertFalse(frame['type_counts_complete'])
        self.assertNotIn('PRIVATE', json.dumps(frame))
        accepted, code = G.validate(encode('HOLD: artifact preparation incomplete', frame), 2)
        self.assertEqual(code, 2)
        self.assertFalse(accepted['archive_inspection_verified'])
        return frame

    def test_all_six_classes_real_tar_no_device_content_read(self):
        entries = [item('.', tarfile.DIRTYPE), item('usr/bin/python3.12', data=b'x'),
                   item('usr/bin/python3', tarfile.SYMTYPE, linkname='python3.12'),
                   item('etc/os-release', tarfile.LNKTYPE, linkname='unresolved'),
                   item('PRIVATE_CHAR', tarfile.CHRTYPE, devmajor=1, devminor=3),
                   item('PRIVATE_BLOCK', tarfile.BLKTYPE, devmajor=8, devminor=0)]
        original = tarfile.TarFile.extractfile
        calls = []
        def guarded(handle, info):
            self.assertTrue(info.isreg())
            calls.append(info.name)
            return original(handle, info)
        with mock.patch.object(tarfile.TarFile, 'extractfile', guarded):
            result = inspect(archive(entries))
        self.assertEqual(calls, ['usr/bin/python3.12'])
        self.assertEqual(result['type_counts'], dict.fromkeys(P.TYPE_CLASSES, 1))
        self.assertEqual(result['tar_header_count'], 6)
        self.assertNotIn('PRIVATE', json.dumps(result))
        self.assertNotIn('devmajor', json.dumps(result))
        self.assertNotIn('content_sha256', result['selected_entries'][1])
        self.assertNotIn('content_sha256', result['selected_entries'][2])
        self.assertTrue(result['metadata_catalog_complete'])
        for key in G.RESULT_FLAGS:
            self.assertIs(result[key], False)

    def test_strict_lane_still_rejects_identical_devices(self):
        for kind in (tarfile.CHRTYPE, tarfile.BLKTYPE):
            raw = archive([item('PRIVATE_DEVICE', kind)])
            with self.subTest(kind=kind), self.assertRaises(S.PredicateHold) as caught:
                S.inspect(io.BytesIO(raw), hashlib.sha256(raw).hexdigest())
            self.assertEqual(caught.exception.reason, 'TYPE_REJECTED')
            self.assertEqual(inspect(raw)['tar_header_count'], 1)

    def test_catalog_domain_and_device_metadata_hash(self):
        info, data = item('PRIVATE_DEVICE', tarfile.CHRTYPE, devmajor=1, devminor=3)
        result = inspect(archive([(info, data)]))
        record = {'name': info.name, 'type_hex': info.type.hex(), 'size': 0,
                  'mode': info.mode, 'uid': info.uid, 'gid': info.gid, 'link': '',
                  'devmajor': 1, 'devminor': 3}
        encoded = (json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(',', ':'))+'\n').encode('ascii')
        expected = hashlib.sha256(P.POLICY_ID.encode('ascii')+b'\0'+encoded).hexdigest()
        self.assertEqual(result['ordered_header_catalog_sha256'], expected)
        self.assertNotEqual(expected, hashlib.sha256(encoded).hexdigest())
        info.devminor = 4
        self.assertNotEqual(expected, inspect(archive([(info, data)]))['ordered_header_catalog_sha256'])

    def test_device_size_and_link_rejected_real_tar(self):
        self.reason([item('PRIVATE_DEVICE', tarfile.CHRTYPE, b'x')], 'DEVICE_METADATA_REJECTED')
        self.reason([item('PRIVATE_DEVICE', tarfile.BLKTYPE, linkname='PRIVATE_LINK')], 'DEVICE_METADATA_REJECTED')

    def test_device_integer_bounds_reader_faults(self):
        # Direct header validator: tar would coerce bool to int before readback.
        for field, limit in [('devmajor', 2**32), ('devminor', 2**32),
                             ('mode', 2**63), ('uid', 2**63), ('gid', 2**63)]:
            for invalid in (True, False, -1, limit, 1.0, 'PRIVATE'):
                info, _ = item('PRIVATE_DEVICE', tarfile.CHRTYPE)
                setattr(info, field, invalid)
                with self.subTest(field=field, value=invalid), self.assertRaises(P.PredicateHold) as caught:
                    P.device_metadata(info)
                self.assertEqual(caught.exception.reason, 'DEVICE_METADATA_REJECTED')
            setattr(info, field, limit-1)
            P.device_metadata(info)

    def test_selected_device_collision_real_tar(self):
        for kind in (tarfile.CHRTYPE, tarfile.BLKTYPE):
            with self.subTest(kind=kind):
                self.reason([item('usr/sbin/sshd', kind)], 'SELECTED_DEVICE_COLLISION')

    def test_fifo_unknown_rejected_real_tar(self):
        for kind in (tarfile.FIFOTYPE, b'Z', b's'):
            with self.subTest(kind=kind):
                self.reason([item('PRIVATE', kind)], 'TYPE_REJECTED')

    def test_sparse_including_empty_extent_reader_faults(self):
        for sparse, kind in [([], tarfile.REGTYPE), ([(0, 1)], tarfile.REGTYPE),
                             (None, tarfile.GNUTYPE_SPARSE)]:
            info, _ = item('PRIVATE', kind)
            info.sparse = sparse
            reader = mock.MagicMock()
            reader.__enter__.return_value = reader
            reader.__iter__.return_value = iter([info])
            with mock.patch.object(P.tarfile, 'open', return_value=reader), self.assertRaises(P.PredicateHold) as caught:
                inspect(b'header-fault')
            self.assertEqual(caught.exception.reason, 'SPARSE')
            reader.extractfile.assert_not_called()

    def test_contiguous_regular_classification_matches_isreg(self):
        raw = archive([item('usr/bin/python3.12', tarfile.CONTTYPE, b'x')])
        result = inspect(raw)
        self.assertEqual(result['type_counts']['REGULAR'], 1)
        self.assertIn('content_sha256', result['selected_entries'][0])
        self.assertIn(tarfile.CONTTYPE.hex(), G.REGULAR_HEX)

    def test_hash_before_parser(self):
        with mock.patch.object(P.tarfile, 'open', side_effect=AssertionError('parser reached')), self.assertRaises(P.Hold):
            P.inspect(io.BytesIO(b'wrong'), 'a'*64)

    def test_name_and_duplicate_guards_real_tar(self):
        for name, reason in [('../PRIVATE', 'PATH_COMPONENT'), ('/PRIVATE', 'ABSOLUTE_PATH'),
                             ('PRIVATE\\x', 'BACKSLASH'), ('PRIVATE\x01', 'NAME_CONTROL'),
                             ('x'*4097, 'NAME_LENGTH_OR_TYPE')]:
            with self.subTest(reason=reason):
                self.reason([item(name)], reason)
        self.reason([item('PRIVATE'), item('./PRIVATE')], 'NAME_DUPLICATE')
        self.reason([item('.')], 'ROOT_NOT_DIRECTORY')

    def test_budgets_real_tar(self):
        entries = [item('one', data=b'123'), item('two', data=b'456')]
        for name, value, reason in [('MAX_MEMBERS', 1, 'COUNT_MEMBERS'),
                                    ('MAX_LOGICAL_BYTES', 5, 'SIZE_LOGICAL')]:
            with self.subTest(name=name), mock.patch.object(P, name, value):
                self.reason(entries, reason)
        with mock.patch.object(P, 'MAX_ARCHIVE', 1), self.assertRaises(P.Hold):
            inspect(archive(entries))
        with mock.patch.object(P, 'MAX_SELECTED_FILE', 1):
            self.reason([item('usr/sbin/sshd', data=b'xx')], 'SIZE_SELECTED')
        self.reason([item('usr/bin/python3.'+str(i)) for i in range(33)], 'COUNT_SELECTED')
        self.reason([], 'EMPTY_ARCHIVE')

    def test_failed_counts_never_complete_or_exceed_members(self):
        frame = self.reason([item('good'), item('PRIVATE', tarfile.FIFOTYPE)], 'TYPE_REJECTED')
        self.assertEqual(sum(frame['type_counts'].values()), 1)
        self.assertEqual(frame['parsed_members'], 2)
        progress = P.Diagnostic()
        inspect(archive([item('good')]), progress)
        progress.stage = 'RECEIPT_ENCODE'
        self.assertFalse(progress.frame(OSError('PRIVATE'))['type_counts_complete'])
        self.assertNotIn('PRIVATE', P.diagnostic_line(progress, OSError('PRIVATE')))

    def test_gate_success_catalog_only_cross_frame(self):
        result, detail = success_frames()
        accepted, code = G.validate(encode(result, detail), 0)
        self.assertEqual(code, 0)
        self.assertEqual(accepted['evidence_class'], 'j0-metadata-catalog-gate-only')
        self.assertTrue(accepted['metadata_catalog_complete'])
        self.assertFalse(accepted['archive_inspection_verified'])
        self.assertEqual(P.PREDICATE_REASONS, G.PREDICATE_REASONS)
        self.assertEqual(len(P.PREDICATE_REASONS), 21)

    def test_gate_counts_and_schema_rejections(self):
        first, second = success_frames()
        for which, changes in [('first', {'schema': 2}), ('second', {'schema': 2}),
                               ('first', {'policy_id': 'strict'}),
                               ('second', {'policy_id': 'strict'}),
                               ('first', {'evidence_class': 'j0-archive-inspection-only'}),
                               ('second', {'evidence_class': 'j0-artifact-diagnostic-only'}),
                               ('second', {'type_counts_complete': False}),
                               ('second', {'predicate_reason': 'TYPE_REJECTED'}),
                               ('first', {'metadata_catalog_complete': False}),
                               ('second', {'archive_sha256': 'a'*64}),
                               ('second', {'received_bytes': 1})]:
            a, b = copy.deepcopy(first), copy.deepcopy(second)
            (a if which == 'first' else b).update(changes)
            with self.subTest(which=which, changes=changes), self.assertRaises(G.Rejected):
                G.validate(encode(a, b), 0)
        for value in (True, -1, 200001, 1.5):
            a, b = copy.deepcopy(first), copy.deepcopy(second)
            a['type_counts']['REGULAR'] = value
            with self.subTest(value=value), self.assertRaises(G.Rejected):
                G.validate(encode(a, b), 0)
        for counts in ({}, dict(first['type_counts'], EXTRA=0),
                       dict(first['type_counts'], REGULAR=0)):
            with self.subTest(counts=counts), self.assertRaises(G.Rejected):
                G.validate(encode(dict(first, type_counts=counts), second), 0)
        changed = dict(second['type_counts'], REGULAR=0, DIRECTORY=1)
        with self.assertRaises(G.Rejected):
            G.validate(encode(first, dict(second, type_counts=changed)), 0)

    def test_gate_all_authority_flags_false(self):
        first, second = success_frames()
        for which, flags in [('first', G.RESULT_FLAGS), ('second', G.FLAGS)]:
            for flag in flags:
                a, b = copy.deepcopy(first), copy.deepcopy(second)
                (a if which == 'first' else b)[flag] = True
                with self.subTest(which=which, flag=flag), self.assertRaises(G.Rejected):
                    G.validate(encode(a, b), 0)

    def test_gate_rejects_selected_device_and_extra_fields(self):
        first, second = success_frames()
        for changes in ({'type_hex': '33'}, {'type_hex': '34'}, {'devmajor': 1},
                        {'name': 'PRIVATE'}, {'size': True}):
            value = copy.deepcopy(first)
            value['selected_entries'][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(G.Rejected):
                G.validate(encode(value, second), 0)
        with self.assertRaises(G.Rejected):
            G.validate(encode(dict(first, EXTRA=1), second), 0)

    def test_gate_hold_cannot_become_success(self):
        progress = P.Diagnostic()
        progress.stage = 'ARCHIVE_PARSE'
        detail = progress.frame(P.PredicateHold('DEVICE_METADATA_REJECTED'))
        raw = encode('HOLD: artifact preparation incomplete', detail)
        self.assertEqual(G.validate(raw, 2)[1], 2)
        with self.assertRaises(G.Rejected):
            G.validate(raw, 0)
        for changes in ({'type_counts_complete': True}, {'predicate_reason': 'PRIVATE'},
                        {'stage': 'HTTP_OPEN'}, {'error': 'NONE'}, {'metadata_catalog_complete': True}):
            with self.subTest(changes=changes), self.assertRaises(G.Rejected):
                G.validate(encode('HOLD: artifact preparation incomplete', dict(detail, **changes)), 2)

    def test_gate_framing_markers_duplicate_nonfinite(self):
        a, b = success_frames()
        raw = encode(a, b)
        for invalid in (raw+b'\n', raw.replace(b'\n', b'\r\n'), b'x'*67587,
                        raw+b'Traceback', raw.replace(b'"schema":1', b'"schema":1,"schema":1', 1),
                        raw.replace(b'"schema":1', b'"schema":NaN', 1),
                        raw.replace(b'"schema":1', b'"schema":Infinity', 1)):
            with self.subTest(length=len(invalid)), self.assertRaises(G.Rejected):
                G.validate(invalid, 0)
        for marker in ('ResourceWarning', 'Exception ignored', 'Traceback'):
            bad = copy.deepcopy(a)
            bad['selected_entries'][0]['link'] = marker
            with self.subTest(marker=marker), self.assertRaises(G.Rejected):
                G.validate(encode(bad, b), 0)

    def test_main_guard_and_new_argv_before_network(self):
        for argv, environment in [(['--download-and-catalog-metadata'], {}),
                                   (['--download-and-inspect-diagnostic'], {'GITHUB_ACTIONS': 'true'})]:
            with mock.patch.object(P.sys, 'argv', ['fixture']+argv), \
                 mock.patch.dict(P.os.environ, environment, clear=True), \
                 mock.patch.object(P, 'download', side_effect=AssertionError('network reached')), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(P.main(), 2)
            raw = output.getvalue().encode('ascii')
            self.assertEqual(G.validate(raw, 2)[1], 2)

    def test_main_offline_synthetic_success_and_failure(self):
        # Real main/TemporaryFile/hash/parser/encoding/gate. Network replaced by
        # local bytes; process limits/alarm and provider digest replaced in test.
        raw = archive([item('usr/bin/python3.12', data=b'synthetic'),
                       item('PRIVATE', tarfile.BLKTYPE)])
        expected = hashlib.sha256(raw).hexdigest()
        selection = {'selection': {'url': P.URL, 'provider_reported_archive_sha256': expected}}
        receipt = json.dumps(selection).encode('ascii')
        def download(output, progress):
            output.write(raw)
            progress.received_bytes = len(raw)
            progress.download_complete = True
        import resource
        for fail in (False, True):
            with contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.object(P.sys, 'argv', ['fixture', '--download-and-catalog-metadata']))
                stack.enter_context(mock.patch.dict(P.os.environ, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted', 'RUNNER_OS': 'Linux'}, clear=True))
                stack.enter_context(mock.patch.object(resource, 'setrlimit'))
                stack.enter_context(mock.patch.object(P.signal, 'signal'))
                alarm = stack.enter_context(mock.patch.object(P.signal, 'alarm'))
                stack.enter_context(mock.patch.object(P.Path, 'read_bytes', return_value=receipt))
                stack.enter_context(mock.patch.object(P, 'SOURCE_RECEIPT_SHA256', hashlib.sha256(receipt).hexdigest()))
                stack.enter_context(mock.patch.object(P, 'ARCHIVE_SHA256', expected))
                stack.enter_context(mock.patch.object(G, 'SHA', expected))
                stack.enter_context(mock.patch.object(P, 'download', side_effect=OSError('PRIVATE') if fail else download))
                output = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                code = P.main()
                self.assertEqual(code, 2 if fail else 0)
                self.assertEqual(G.validate(output.getvalue().encode('ascii'), code)[1], code)
                self.assertNotIn('PRIVATE', output.getvalue())
                self.assertEqual(alarm.call_args_list, [mock.call(120), mock.call(0)])

    def test_http_cleanup_and_redirect_response_closed(self):
        response = io.BytesIO(b'PRIVATE')
        with self.assertRaises(P.RedirectHold):
            P.NoRedirect().redirect_request(None, response, 302, '', {}, 'PRIVATE')
        self.assertTrue(response.closed)
        response = io.BytesIO(b'PRIVATE')
        error = P.urllib.error.HTTPError('PRIVATE', 403, 'PRIVATE', {}, response)
        opener = mock.Mock()
        opener.open.side_effect = error
        with mock.patch.object(P.urllib.request, 'build_opener', return_value=opener), self.assertRaises(P.urllib.error.HTTPError):
            P.download(io.BytesIO())
        self.assertTrue(response.closed)
        self.assertEqual(P.error_code(error), 'HTTP_403')

    def test_gate_frame_byte_limits(self):
        a, b = success_frames()
        first = json.dumps(a, separators=(',', ':'))
        second = json.dumps(b, separators=(',', ':'))
        exact = (first.ljust(65536)+'\n'+second.ljust(2048)+'\n').encode('ascii')
        self.assertEqual(len(exact), 67586)
        self.assertEqual(G.validate(exact, 0)[1], 0)
        for raw in ((first.ljust(65537)+'\n'+second+'\n').encode('ascii'),
                    (first+'\n'+second.ljust(2049)+'\n').encode('ascii')):
            with self.assertRaises(G.Rejected):
                G.validate(raw, 0)

    def test_fallback_diagnostic_never_accepted(self):
        with mock.patch.object(P.sys, 'argv', ['fixture']), \
             mock.patch.object(P, 'diagnostic_line', side_effect=MemoryError()), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(P.main(), 2)
        self.assertIn('DIAGNOSTIC_UNAVAILABLE', output.getvalue())
        with self.assertRaises(G.Rejected):
            G.validate(output.getvalue().encode('ascii'), 2)

    def test_gate_cli_fixed_rejection_no_raw_echo(self):
        with mock.patch.object(G.sys, 'argv', ['gate', 'PRIVATE', '0']), \
             mock.patch.object(G.Path, 'open', return_value=io.BytesIO(b'PRIVATE')), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(G.main(), 2)
        self.assertEqual(output.getvalue(), 'HOLD: metadata catalog gate rejected output\n')


def load_tests(loader, tests, pattern):
    # Rebind a private copy of the unchanged E11 test module to the NEW producer.
    # Eleven applicable original tests run unchanged. Device policy and two-line
    # main differ intentionally, so their two original tests remain strict-only;
    # the new controls above cover those contracts explicitly.
    baseline = load('catalog_e11_regression', 'test_join_artifact.py')
    baseline.P = P
    names = loader.getTestCaseNames(baseline.ArtifactControls)
    excluded = {'test_special_file_rejected', 'test_main_rejects_without_ci_before_network'}
    applicable = [name for name in names if name not in excluded]
    if len(applicable) != 11:
        raise AssertionError('baseline regression count changed')
    tests.addTests(baseline.ArtifactControls(name) for name in applicable)
    return tests


if __name__ == '__main__':
    unittest.main(verbosity=2)
