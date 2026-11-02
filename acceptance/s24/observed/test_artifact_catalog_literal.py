"""V2 offline controls only: synthetic tar and disclosed header/network faults.

No provider archive, extraction, filesystem member lookup or live action. Reuse a
private copy of applicable V1/E11 controls; original files and assertions stay.
"""
import ast
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


P = load('literal_producer', 'catalog_join_artifact_literal.py')
G = load('literal_gate', 'gate_artifact_catalog_literal.py')
V = load('literal_v1_reference', 'catalog_join_artifact.py')
VG = load('literal_v1_gate_reference', 'gate_artifact_catalog.py')
S = load('literal_strict_reference', 'prepare_join_artifact_diagnostic.py')
B = load('literal_private_v1_controls', 'test_artifact_catalog.py')
B.P, B.G = P, G
item, archive, encode = B.item, B.archive, B.encode


def inspect(raw, progress=None, producer=P):
    return producer.inspect(io.BytesIO(raw), hashlib.sha256(raw).hexdigest(), progress)


def frames(producer, gate):
    raw = archive([item('usr/bin/python3.12', data=b'synthetic')])
    progress = producer.Diagnostic()
    result = inspect(raw, progress, producer)
    progress.received_bytes = len(raw)
    progress.download_complete = True
    progress.stage = 'COMPLETE'
    # Both fixture frames substitute provider digest; never actual provider bytes.
    result['author_computed_archive_sha256'] = gate.SHA
    progress.archive_sha256 = gate.SHA
    return result, progress.frame(None)


class LiteralControls(unittest.TestCase):
    def rejected(self, entries, reason):
        progress = P.Diagnostic()
        with self.assertRaises(P.PredicateHold) as caught:
            inspect(archive(entries), progress)
        self.assertEqual(caught.exception.args, ())
        self.assertEqual(caught.exception.reason, reason)
        d = progress.frame(caught.exception)
        self.assertFalse(d['type_counts_complete'])
        self.assertEqual(G.validate(encode('HOLD: artifact preparation incomplete', d), 2)[1], 2)

    def test_literal_names_no_rewrite_real_tar(self):
        names = [r'PRIVATE\x', r'..\x', r'C:\x', r'\\server\share',
                 r'a\n', r'a\x41', r'a\\b', r'a\../b']
        raw = archive([item(n) for n in names])
        self.assertEqual([P.member_name(n) for n in names], names)
        with mock.patch.object(P.tarfile.TarFile, 'extractfile', side_effect=AssertionError('content read')):
            result = inspect(raw)
        self.assertEqual(result['tar_header_count'], len(names))
        self.assertEqual(result['selected_entries'], [])
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_independent_digest_literal_slash_and_domain(self):
        names = [r'PRIVATE\x', 'PRIVATE/x']
        entries = [item(n) for n in names]
        expected = hashlib.sha256(b'ROOTFS_METADATA_CATALOG_V2_LITERAL_NAMES\0')
        for info, _ in entries:
            record = dict(name=info.name, type_hex=info.type.hex(), size=0,
                          mode=info.mode, uid=info.uid, gid=info.gid, link='')
            expected.update((json.dumps(record, sort_keys=True, ensure_ascii=True,
                                       separators=(',', ':'))+'\n').encode('ascii'))
        result = inspect(archive(entries))
        self.assertEqual(result['tar_header_count'], 2)
        self.assertEqual(result['ordered_header_catalog_sha256'], expected.hexdigest())
        self.assertNotEqual(inspect(archive([item(names[0])]))['ordered_header_catalog_sha256'],
                            inspect(archive([item(names[1])]))['ordered_header_catalog_sha256'])
        common = archive([item('ordinary')])
        self.assertNotEqual(inspect(common)['ordered_header_catalog_sha256'],
                            inspect(common, producer=V)['ordered_header_catalog_sha256'])

    def test_duplicate_normalization_kept(self):
        for left, right in [(r'./PRIVATE\x', r'PRIVATE\x'),
                            ('PRIVATE\\x/', r'PRIVATE\x'), ('././ordinary', 'ordinary')]:
            with self.subTest(left=left):
                self.rejected([item(left), item(right)], 'NAME_DUPLICATE')

    def test_slash_absolute_control_and_root_guards_kept(self):
        for name, reason in [('../PRIVATE', 'PATH_COMPONENT'), ('/PRIVATE', 'ABSOLUTE_PATH'),
                             ('a//b', 'PATH_COMPONENT'), ('a/./b', 'PATH_COMPONENT'),
                             ('a/../b', 'PATH_COMPONENT'), ('PRIVATE\n', 'NAME_CONTROL'),
                             ('PRIVATE\x7f', 'NAME_CONTROL'), ('x'*4097, 'NAME_LENGTH_OR_TYPE'),
                             ('.', 'ROOT_NOT_DIRECTORY')]:
            with self.subTest(reason=reason):
                self.rejected([item(name)], reason)

    def test_only_selected_regular_content_no_member_path_use(self):
        raw = archive([item(r'usr\bin\python3.12', data=b'PRIVATE'),
                       item(r'..\PRIVATE', data=b'PRIVATE'),
                       item('usr/bin/python3.12', data=b'selected')])
        original = tarfile.TarFile.extractfile
        calls = []
        def checked(handle, info):
            self.assertIsInstance(info, tarfile.TarInfo)
            self.assertTrue(info.isreg())
            self.assertEqual(info.name, 'usr/bin/python3.12')
            calls.append(info.name)
            return original(handle, info)
        with mock.patch.object(P.tarfile.TarFile, 'extractfile', checked), \
             mock.patch.object(P.Path, 'open', side_effect=AssertionError('member path opened')), \
             mock.patch.object(P.os, 'open', side_effect=AssertionError('member path opened')), \
             mock.patch.object(P.os, 'mkdir', side_effect=AssertionError('member directory')):
            result = inspect(raw)
        self.assertEqual(calls, ['usr/bin/python3.12'])
        self.assertEqual(result['selected_entries'][0]['content_sha256'], hashlib.sha256(b'selected').hexdigest())
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_selected_near_matches_rejected_by_gate(self):
        first, second = frames(P, G)
        for name in [r'usr\bin\python3.12', r'usr/bin/python3\.12', 'usr/bin/python3.12/extra']:
            self.assertFalse(P.selected(name))
            bad = copy.deepcopy(first)
            bad['selected_entries'][0]['name'] = name
            with self.subTest(name=name), self.assertRaises(G.Rejected):
                G.validate(encode(bad, second), 0)

    def test_same_literal_tar_rejected_by_v1_and_strict(self):
        raw = archive([item(r'PRIVATE\x')])
        self.assertEqual(inspect(raw)['tar_header_count'], 1)
        for producer in (V, S):
            with self.subTest(policy=producer.__name__), self.assertRaises(producer.PredicateHold) as caught:
                inspect(raw, producer=producer)
            self.assertEqual(caught.exception.reason, 'BACKSLASH')

    def test_cross_policy_success_frames_reject(self):
        old = frames(V, VG)
        new = frames(P, G)
        self.assertEqual(G.validate(encode(*new), 0)[1], 0)
        self.assertEqual(VG.validate(encode(*old), 0)[1], 0)
        for gate, wrong, right in [(G, old, new), (VG, new, old)]:
            for pair in (wrong, (wrong[0], right[1]), (right[0], wrong[1])):
                with self.subTest(gate=gate.__name__), self.assertRaises(gate.Rejected):
                    gate.validate(encode(*pair), 0)
            for index in (0, 1):
                pair = copy.deepcopy(right)
                pair[index]['policy_id'] = wrong[index]['policy_id']
                with self.assertRaises(gate.Rejected):
                    gate.validate(encode(*pair), 0)

    def test_cross_policy_hold_frames_reject(self):
        for producer, gate, other in [(P, G, VG), (V, VG, G)]:
            progress = producer.Diagnostic()
            progress.stage = 'ARCHIVE_PARSE'
            detail = progress.frame(producer.PredicateHold('PATH_COMPONENT'))
            raw = encode('HOLD: artifact preparation incomplete', detail)
            self.assertEqual(gate.validate(raw, 2)[1], 2)
            with self.assertRaises(other.Rejected):
                other.validate(raw, 2)

    def test_new_main_offline_success_and_failure(self):
        # Real main, TemporaryFile, hashing, tar parser and gate. Only provider
        # bytes/receipt/network/process limits are synthetic substitutions.
        raw = archive([item(r'PRIVATE\x'), item('usr/bin/python3.12', data=b'synthetic')])
        digest = hashlib.sha256(raw).hexdigest()
        receipt = json.dumps({'selection': {'url': P.URL, 'provider_reported_archive_sha256': digest}}).encode()
        def download(output, progress):
            output.write(raw)
            progress.received_bytes = len(raw)
            progress.download_complete = True
        import resource
        for failed in (False, True):
            with contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.object(P.sys, 'argv', ['fixture', '--download-and-catalog-literal-metadata']))
                stack.enter_context(mock.patch.dict(P.os.environ, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted', 'RUNNER_OS': 'Linux'}, clear=True))
                stack.enter_context(mock.patch.object(resource, 'setrlimit'))
                stack.enter_context(mock.patch.object(P.signal, 'signal'))
                alarm = stack.enter_context(mock.patch.object(P.signal, 'alarm'))
                stack.enter_context(mock.patch.object(P.Path, 'read_bytes', return_value=receipt))
                stack.enter_context(mock.patch.object(P, 'SOURCE_RECEIPT_SHA256', hashlib.sha256(receipt).hexdigest()))
                stack.enter_context(mock.patch.object(P, 'ARCHIVE_SHA256', digest))
                stack.enter_context(mock.patch.object(G, 'SHA', digest))
                stack.enter_context(mock.patch.object(P, 'download', side_effect=OSError('PRIVATE') if failed else download))
                output = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                code = P.main()
                self.assertEqual(code, 2 if failed else 0)
                accepted, accepted_code = G.validate(output.getvalue().encode(), code)
                self.assertEqual(accepted_code, code)
                self.assertFalse(accepted['archive_inspection_verified'])
                self.assertNotIn('PRIVATE', output.getvalue())
                self.assertEqual(alarm.call_args_list, [mock.call(120), mock.call(0)])

    def test_old_argv_and_non_ci_rejected_before_resource_or_network(self):
        for argv, env in [('--download-and-catalog-metadata', {'GITHUB_ACTIONS': 'true'}),
                          ('--download-and-catalog-literal-metadata', {})]:
            with mock.patch.object(P.sys, 'argv', ['fixture', argv]), \
                 mock.patch.dict(P.os.environ, env, clear=True), \
                 mock.patch.object(P, 'download', side_effect=AssertionError('network reached')), \
                 mock.patch.object(P.signal, 'alarm', side_effect=AssertionError('alarm reached')), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(P.main(), 2)
            self.assertEqual(G.validate(output.getvalue().encode(), 2)[1], 2)

    def test_unchanged_selector_network_type_and_budget_functions(self):
        def functions(path):
            return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body
                    if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        old, new = functions(HERE/'catalog_join_artifact.py'), functions(HERE/'catalog_join_artifact_literal.py')
        for name in ('selected', 'classify', 'device_metadata', 'digest', 'download',
                     'NoRedirect', 'error_code', 'predicate', 'require'):
            self.assertEqual(old[name], new[name], name)
        for name in ('URL', 'ARCHIVE_SHA256', 'SOURCE_RECEIPT_SHA256', 'MAX_ARCHIVE',
                     'MAX_MEMBERS', 'MAX_LOGICAL_BYTES', 'MAX_SELECTED_FILE', 'CHUNK'):
            self.assertEqual(getattr(P, name), getattr(V, name), name)

    def test_nonselected_literal_metadata_never_public(self):
        sentinel = r'PRIVATE_ResourceWarning\x'
        progress = P.Diagnostic()
        raw = archive([item(sentinel)])
        result = inspect(raw, progress)
        public = json.dumps(result)+P.diagnostic_line(progress, None)
        self.assertNotIn('PRIVATE', public)
        self.assertNotIn('ResourceWarning', public)
        self.assertIs(result['archive_inspection_verified'], False)
        self.assertEqual(result['selected_entries'], [])

    def test_literal_links_and_devices_never_followed(self):
        raw = archive([item('usr/bin/python3', tarfile.SYMTYPE, linkname=r'python3\x'),
                       item('etc/os-release', tarfile.LNKTYPE, linkname=r'..\x'),
                       item(r'PRIVATE\device', tarfile.CHRTYPE, devmajor=1, devminor=3)])
        with mock.patch.object(P.tarfile.TarFile, 'extractfile', side_effect=AssertionError('link/device read')):
            result = inspect(raw)
        self.assertFalse(result['links_resolved'])
        self.assertEqual([x['link'] for x in result['selected_entries']], [r'python3\x', r'..\x'])
        self.assertNotIn('PRIVATE', json.dumps(result))
        self.assertNotIn('devmajor', json.dumps(result))


def load_tests(loader, tests, pattern):
    # Only these three V1 methods assert intentionally different lane behavior:
    # old name rejection, evidence class, old success argv. Replaced above, while
    # all original 36 V1 tests still run in their original unchanged CI step.
    excluded = {'test_name_and_duplicate_guards_real_tar', 'test_gate_success_catalog_only_cross_frame',
                'test_main_offline_synthetic_success_and_failure'}
    names = loader.getTestCaseNames(B.CatalogControls)
    applicable = [n for n in names if n not in excluded]
    if len(names) != 25 or len(applicable) != 22:
        raise AssertionError('V1 applicable-control inventory changed')
    tests.addTests(B.CatalogControls(n) for n in applicable)
    original = load('literal_private_e11_controls', 'test_join_artifact.py')
    original.P = P
    excluded_e11 = {'test_special_file_rejected', 'test_main_rejects_without_ci_before_network',
                    'test_path_traversal_and_absolute_rejected'}
    applicable = [n for n in loader.getTestCaseNames(original.ArtifactControls) if n not in excluded_e11]
    if len(applicable) != 10:
        raise AssertionError('E11 applicable-control inventory changed')
    tests.addTests(original.ArtifactControls(n) for n in applicable)
    return tests


if __name__ == '__main__':
    unittest.main(verbosity=2)
