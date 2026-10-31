"""Offline protocol gate fixtures, never the live preparation CLI."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock

HERE=Path(__file__).parent

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

G=load('gate_candidate','gate_artifact_diagnostic.py')
D=load('diag_candidate','prepare_join_artifact_diagnostic.py')
B=load('archive_fixtures','test_join_artifact.py')

def line(value):
    return json.dumps(value,ensure_ascii=True,separators=(',',':')).encode()

def failure():
    d=D.Diagnostic();d.stage='HTTP_OPEN'
    frame=d.frame(D.Hold())
    return b'HOLD: artifact preparation incomplete\n'+line(frame)+b'\n',frame

def success():
    raw=B.archive([('usr/bin/python3.12','file',b'synthetic')])
    sha=hashlib.sha256(raw).hexdigest()
    progress=D.Diagnostic();progress.received_bytes=len(raw);progress.download_complete=True
    receipt=D.inspect(io.BytesIO(raw),sha,progress)
    progress.stage='COMPLETE'
    return receipt,progress.frame(None),sha


class GateControls(unittest.TestCase):
    def test_enums_and_false_flags_match_reviewed_producer(self):
        self.assertEqual(G.STAGES,D.STAGES)
        self.assertEqual(G.ERRORS,D.ERRORS)
        self.assertEqual(G.DIAG_KEYS,set(D.Diagnostic().frame(None)))

    def test_valid_hold_remains_failed(self):
        raw,frame=failure();out,code=G.validate(raw,2)
        self.assertEqual(code,2)
        self.assertEqual(out['diagnostic'],frame)
        self.assertIs(out['archive_inspection_verified'],False)

    def test_success_uses_real_parser_fixture_and_cross_frame_binding(self):
        receipt,frame,sha=success()
        with mock.patch.object(G,'SHA',sha):
            out,code=G.validate(line(receipt)+b'\n'+line(frame)+b'\n',0)
        self.assertEqual(code,0)
        self.assertTrue(out['archive_inspection_verified'])
        self.assertFalse(out['inspection']['j0_ready'])

    def test_framing_and_warning_fail_closed(self):
        raw,_=failure()
        for bad in (raw.rstrip(b'\n'),raw+b'extra\n',raw.replace(b'\n',b'\r\n'),
                    b'ResourceWarning\n'+raw,b'Exception ignored while calling deallocator\n'+raw,
                    b'Traceback\n'+raw,b'x'*67587):
            with self.subTest(size=len(bad)),self.assertRaises(G.Rejected):
                G.validate(bad,2)

    def test_duplicates_unknown_keys_and_enum_rejected(self):
        raw,frame=failure()
        mutations=[dict(frame,stage='UNKNOWN'),dict(frame,error='PRIVATE_SENTINEL'),
                   dict(frame,exception='PRIVATE_SENTINEL'),dict(frame,schema=True)]
        for d in mutations:
            with self.assertRaises(G.Rejected):G.validate(raw.splitlines()[0]+b'\n'+line(d)+b'\n',2)
        bad=line(frame).replace(b'"schema":1',b'"schema":1,"schema":1')
        with self.assertRaises(G.Rejected):G.validate(raw.splitlines()[0]+b'\n'+bad+b'\n',2)

    def test_false_scope_and_milestone_types_enforced(self):
        raw,frame=failure()
        for key,value in [('j0_ready',True),('received_bytes',True),('hashed_bytes',G.MAX_ARCHIVE+2),
                          ('hash_complete',True),('archive_sha256','a'*64),('digest_matches',False)]:
            d=dict(frame);d[key]=value
            with self.subTest(key=key),self.assertRaises(G.Rejected):
                G.validate(raw.splitlines()[0]+b'\n'+line(d)+b'\n',2)

    def test_unavailable_or_wrong_exit_never_success(self):
        raw,_=failure()
        for code in (-9,1,0):
            with self.assertRaises(G.Rejected):G.validate(raw,code)
        unavailable={'evidence_class':'j0-artifact-diagnostic-unavailable','schema':1,'error':'DIAGNOSTIC_UNAVAILABLE'}
        with self.assertRaises(G.Rejected):G.validate(raw.splitlines()[0]+b'\n'+line(unavailable)+b'\n',2)

    def test_success_must_agree_across_frames(self):
        receipt,frame,sha=success()
        for key,value in [('received_bytes',0),('parsed_members',0),('error','HTTP_OTHER'),
                          ('digest_matches',False),('archive_sha256','a'*64)]:
            d=dict(frame);d[key]=value
            with self.subTest(key=key),mock.patch.object(G,'SHA',sha),self.assertRaises(G.Rejected):
                G.validate(line(receipt)+b'\n'+line(d)+b'\n',0)
        with mock.patch.object(G,'SHA','b'*64),self.assertRaises(G.Rejected):
            G.validate(line(receipt)+b'\n'+line(frame)+b'\n',0)

    def test_success_receipt_unknown_field_or_scope_rejected(self):
        receipt,frame,sha=success()
        for key,value in [('exception','PRIVATE_SENTINEL'),('r1_complete',True)]:
            r=dict(receipt);r[key]=value
            with mock.patch.object(G,'SHA',sha),self.assertRaises(G.Rejected):
                G.validate(line(r)+b'\n'+line(frame)+b'\n',0)
        r=copy.deepcopy(receipt);r['selected_entries'][0]['secret']='PRIVATE_SENTINEL'
        with mock.patch.object(G,'SHA',sha),self.assertRaises(G.Rejected):
            G.validate(line(r)+b'\n'+line(frame)+b'\n',0)

    def test_cli_never_echoes_invalid_private_input(self):
        fake=io.BytesIO(b'PRIVATE_SENTINEL\n')
        with mock.patch.object(G.sys,'argv',['gate','ignored','2']), \
             mock.patch.object(G.Path,'open',return_value=fake), \
             mock.patch('sys.stdout',new_callable=io.StringIO) as out:
            self.assertEqual(G.main(),2)
        self.assertEqual(out.getvalue(),'HOLD: diagnostic gate rejected output\n')

if __name__=='__main__':
    unittest.main(verbosity=2)
