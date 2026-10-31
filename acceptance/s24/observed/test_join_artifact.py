"""Offline synthetic archives only; no download/provisioning in these controls."""
import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('join_artifact', Path(__file__).with_name('prepare_join_artifact.py'))
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


def archive(entries):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w:gz') as tf:
        for name, kind, value in entries:
            item = tarfile.TarInfo(name)
            if kind == 'file':
                item.size = len(value)
                tf.addfile(item, io.BytesIO(value))
            elif kind == 'link':
                item.type = tarfile.SYMTYPE
                item.linkname = value
                tf.addfile(item)
            else:
                item.type = tarfile.CHRTYPE
                tf.addfile(item)
    return out.getvalue()


def inspect(raw):
    return P.inspect(io.BytesIO(raw), hashlib.sha256(raw).hexdigest())


class Response(io.BytesIO):
    status = 200

    def __init__(self, body, headers=None):
        super().__init__(body)
        self.headers = headers or {}

    def geturl(self):
        return P.URL


class ArtifactControls(unittest.TestCase):
    def test_hash_failure_precedes_parser(self):
        with mock.patch.object(P.tarfile, 'open', side_effect=AssertionError('parser reached')):
            with self.assertRaises(P.Hold):
                P.inspect(io.BytesIO(b'wrong'), 'a' * 64)

    def test_selected_regular_hash_and_link_not_followed(self):
        body = b'synthetic never-executed ELF'
        result = inspect(archive([('./usr/bin/python3.12', 'file', body),
                                  ('./usr/bin/python3', 'link', 'python3.12')]))
        self.assertEqual(result['selected_entries'][0]['content_sha256'], hashlib.sha256(body).hexdigest())
        self.assertNotIn('content_sha256', result['selected_entries'][1])
        self.assertFalse(result['links_resolved'])
        for key in ('j0_ready', 'setup_ready', 'guest_started', 'guest_imported', 'r1_complete', 'r2_authorized', 'scope_granted'):
            self.assertIs(result[key], False)

    def test_path_traversal_and_absolute_rejected(self):
        for name in ('../escape', '/absolute', 'a/../escape', 'a//b', 'a\\b'):
            with self.subTest(name=name), self.assertRaises(P.Hold):
                inspect(archive([(name, 'file', b'x')]))

    def test_normalized_duplicate_rejected(self):
        with self.assertRaises(P.Hold):
            inspect(archive([('./etc/os-release', 'file', b'x'), ('etc/os-release', 'file', b'y')]))

    def test_special_file_rejected(self):
        with self.assertRaises(P.Hold):
            inspect(archive([('dev/device', 'device', '')]))

    def test_archive_and_expansion_budgets(self):
        raw = archive([('one', 'file', b'1234'), ('two', 'file', b'5678')])
        for name, value in [('MAX_ARCHIVE', 4), ('MAX_MEMBERS', 1), ('MAX_LOGICAL_BYTES', 5)]:
            with self.subTest(budget=name), mock.patch.object(P, name, value), self.assertRaises(P.Hold):
                inspect(raw)

    def test_selected_content_budget(self):
        with mock.patch.object(P, 'MAX_SELECTED_FILE', 1), self.assertRaises(P.Hold):
            inspect(archive([('usr/sbin/sshd', 'file', b'big')]))

    def test_redirect_refused(self):
        with self.assertRaises(P.Hold):
            P.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.invalid/')

    def test_download_fixed_request_and_complete_bytes(self):
        opener = mock.Mock()
        opener.open.return_value = Response(b'bytes', {'Content-Length': '5'})
        with mock.patch.object(P.urllib.request, 'build_opener', return_value=opener):
            output = io.BytesIO()
            P.download(output)
        self.assertEqual(output.getvalue(), b'bytes')
        args, kwargs = opener.open.call_args
        self.assertEqual(args[0].full_url, P.URL)
        self.assertEqual(args[0].get_header('Accept-encoding'), 'identity')
        self.assertEqual(kwargs['timeout'], 15)

    def test_download_rejects_headers_or_status(self):
        for headers, status in [({'Content-Length': '0'}, 200),
                                ({'Content-Length': '-1'}, 200),
                                ({'Content-Encoding': 'gzip'}, 200), ({}, 206)]:
            response = Response(b'x', headers)
            response.status = status
            opener = mock.Mock()
            opener.open.return_value = response
            with self.subTest(headers=headers, status=status), \
                 mock.patch.object(P.urllib.request, 'build_opener', return_value=opener), \
                 self.assertRaises(P.Hold):
                P.download(io.BytesIO())

    def test_download_refuses_unannounced_oversize(self):
        opener = mock.Mock()
        opener.open.return_value = Response(b'12345')
        with mock.patch.object(P.urllib.request, 'build_opener', return_value=opener), \
             mock.patch.object(P, 'MAX_ARCHIVE', 4), self.assertRaises(P.Hold):
            P.download(io.BytesIO())

    def test_download_refuses_truncated_length(self):
        opener = mock.Mock()
        opener.open.return_value = Response(b'x', {'Content-Length': '2'})
        with mock.patch.object(P.urllib.request, 'build_opener', return_value=opener), self.assertRaises(P.Hold):
            P.download(io.BytesIO())

    def test_main_rejects_without_ci_before_network(self):
        with mock.patch.object(P.sys, 'argv', ['script', '--download-and-inspect']), \
             mock.patch.dict(P.os.environ, {}, clear=True), \
             mock.patch.object(P, 'download', side_effect=AssertionError('download reached')), \
             mock.patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertEqual(P.main(), 2)
            self.assertEqual(output.getvalue(), 'HOLD: artifact preparation incomplete\n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
