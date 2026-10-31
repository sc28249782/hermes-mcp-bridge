"""Schema-2 reason labels: real synthetic tar cases and disclosed reader faults."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import unittest
from unittest import mock

HERE=Path(__file__).parent

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
D=load('predicate_producer','prepare_join_artifact_diagnostic.py')
G=load('predicate_gate','gate_artifact_diagnostic.py')
B=load('original_fixtures','test_join_artifact.py')


class PredicateReasonControls(unittest.TestCase):
    def reason(self, callback, expected, progress=None):
        progress=progress or D.Diagnostic()
        progress.stage='ARCHIVE_PARSE'
        with self.assertRaises(D.PredicateHold) as caught:
            callback()
        self.assertEqual(caught.exception.args, ())
        self.assertEqual(caught.exception.reason, expected)
        frame=progress.frame(caught.exception)
        self.assertEqual(frame['schema'],2)
        self.assertEqual(frame['predicate_reason'],expected)
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(frame))
        raw=b'HOLD: artifact preparation incomplete\n'+json.dumps(frame).encode()+b'\n'
        accepted,code=G.validate(raw,2)
        self.assertEqual(code,2)
        self.assertFalse(accepted['archive_inspection_verified'])
        return frame

    def inspect_reason(self, entries, expected):
        raw=B.archive(entries);progress=D.Diagnostic()
        return self.reason(lambda:D.inspect(io.BytesIO(raw),hashlib.sha256(raw).hexdigest(),progress),expected,progress)

    def reader_fault(self, item, expected, data=None):
        # ONLY reader/header fault injection; actual hash, validation and labels.
        archive=mock.MagicMock()
        archive.__enter__.return_value=archive
        archive.__iter__.return_value=iter([item])
        archive.extractfile.return_value=None if data is None else io.BytesIO(data)
        with mock.patch.object(D.tarfile,'open',return_value=archive):
            raw=b'synthetic-reader-fault';progress=D.Diagnostic()
            frame=self.reason(lambda:D.inspect(io.BytesIO(raw),hashlib.sha256(raw).hexdigest(),progress),expected,progress)
        return frame

    def test_name_labels_and_no_member_values(self):
        cases=[('x'*4097,'NAME_LENGTH_OR_TYPE'),('/PRIVATE_SENTINEL','ABSOLUTE_PATH'),
               ('PRIVATE_SENTINEL\\x','BACKSLASH'),('../PRIVATE_SENTINEL','PATH_COMPONENT'),
               ('PRIVATE_SENTINEL\x01','NAME_CONTROL')]
        for name,expected in cases:
            with self.subTest(reason=expected):self.inspect_reason([(name,'file',b'x')],expected)

    def test_duplicate_and_root_type_real_tar(self):
        self.inspect_reason([('PRIVATE_SENTINEL','file',b'x'),('./PRIVATE_SENTINEL','file',b'y')],'NAME_DUPLICATE')
        self.inspect_reason([('.','file',b'x')],'ROOT_NOT_DIRECTORY')

    def test_count_and_logical_limits_real_tar(self):
        with mock.patch.object(D,'MAX_MEMBERS',1):
            frame=self.inspect_reason([('one','file',b'x'),('two','file',b'y')],'COUNT_MEMBERS')
            self.assertEqual(frame['parsed_members'],1)
        with mock.patch.object(D,'MAX_LOGICAL_BYTES',5):
            self.inspect_reason([('one','file',b'123'),('two','file',b'456')],'SIZE_LOGICAL')

    def test_link_length_and_type_real_tar(self):
        self.inspect_reason([('PRIVATE_SENTINEL','link','x'*4097)],'LINK_LENGTH')
        self.inspect_reason([('PRIVATE_SENTINEL','device','')],'TYPE_REJECTED')

    def test_header_range_and_sparse_reader_faults(self):
        for size in (-1,D.MAX_LOGICAL_BYTES+1):
            item=tarfile.TarInfo('PRIVATE_SENTINEL');item.size=size
            with self.subTest(size=size):self.reader_fault(item,'HEADER_SIZE_RANGE')
        item=tarfile.TarInfo('PRIVATE_SENTINEL');item.sparse=[(0,1)];item.size=1
        self.reader_fault(item,'SPARSE')

    def test_selected_count_and_size_real_tar(self):
        self.inspect_reason([('usr/bin/python3.'+str(i),'file',b'x') for i in range(33)],'COUNT_SELECTED')
        with mock.patch.object(D,'MAX_SELECTED_FILE',1):
            self.inspect_reason([('usr/sbin/sshd','file',b'xx')],'SIZE_SELECTED')

    def test_selected_stream_reader_faults(self):
        item=tarfile.TarInfo('usr/sbin/sshd');item.size=2
        self.reader_fault(item,'SELECTED_STREAM_MISSING')
        self.reader_fault(item,'SELECTED_READ_SIZE',b'x')
        item.size=1
        with mock.patch.object(D,'MAX_SELECTED_FILE',1):
            self.reader_fault(item,'SIZE_SELECTED_READ',b'xx')

    def test_empty_archive_real_tar(self):
        self.inspect_reason([],'EMPTY_ARCHIVE')

    def test_null_reason_outside_parse_and_for_non_predicate_errors(self):
        for stage,error in [('HTTP_OPEN',D.PredicateHold('TYPE_REJECTED')),
                            ('ARCHIVE_PARSE',D.Hold('PRIVATE_SENTINEL')),
                            ('ARCHIVE_PARSE',OSError('PRIVATE_SENTINEL'))]:
            p=D.Diagnostic();p.stage=stage
            frame=p.frame(error)
            self.assertIsNone(frame['predicate_reason'])
            self.assertNotIn('PRIVATE_SENTINEL',json.dumps(frame))
        with self.assertRaises(D.Hold):D.PredicateHold('PRIVATE_SENTINEL')

    def test_gate_rejects_unknown_old_schema_and_wrong_stage_reason(self):
        self.assertEqual(D.PREDICATE_REASONS,G.PREDICATE_REASONS)
        self.assertEqual(len(D.PREDICATE_REASONS),19)
        p=D.Diagnostic();p.stage='ARCHIVE_PARSE'
        frame=p.frame(D.PredicateHold('TYPE_REJECTED'))
        for changes in ({'predicate_reason':'PRIVATE_SENTINEL'},{'schema':1},
                        {'stage':'HTTP_OPEN'},{'error':'IO_ERROR'},{'predicate_reason':['TYPE_REJECTED']}):
            d=dict(frame,**changes)
            with self.subTest(changes=changes),self.assertRaises(G.Rejected):
                G.validate(b'HOLD: artifact preparation incomplete\n'+json.dumps(d).encode()+b'\n',2)

    def test_success_receipt_unchanged_and_reason_null(self):
        raw=B.archive([('usr/bin/python3.12','file',b'synthetic'),('usr/bin/python3','link','python3.12')])
        expected=hashlib.sha256(raw).hexdigest();p=D.Diagnostic()
        self.assertEqual(D.inspect(io.BytesIO(raw),expected,p),B.P.inspect(io.BytesIO(raw),expected))
        p.stage='COMPLETE';frame=p.frame(None)
        self.assertIsNone(frame['predicate_reason'])
        self.assertFalse(frame['j0_ready'])

if __name__=='__main__':unittest.main(verbosity=2)
