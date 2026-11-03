"""Synthetic-only controls. No key, archive URL, filesystem quarantine or consumer."""
import ast
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tarfile
import unittest
from unittest import mock

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('offline_transfer', HERE/'transfer_offline.py')
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
GEN = 'a'*32
NOW = 1000
CIPHER = b'opaque fixture bytes, NOT age ciphertext'


def enc(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()


def entries(extra=9):
    return [('python', tarfile.REGTYPE, b'synthetic-python', 0o755, ''),
            ('sshd', tarfile.REGTYPE, b'synthetic-sshd', 0o755, '')] + [
                ('data'+str(i), tarfile.REGTYPE, ('PRIVATE'+str(i)).encode(), 0o644, '')
                for i in range(extra)]


def components(items=None, edit_index=None, edit_manifest=None, artifact_transform=None):
    items = entries() if items is None else items
    out = io.BytesIO()
    rows = []
    with tarfile.open(fileobj=out, mode='w', format=tarfile.USTAR_FORMAT, encoding='ascii') as tf:
        for n, kind, body, mode, link in items:
            t = tarfile.TarInfo(n)
            t.type, t.mode, t.linkname = kind, mode, link
            t.size = len(body) if kind == tarfile.REGTYPE else 0
            tf.addfile(t, io.BytesIO(body) if kind == tarfile.REGTYPE else None)
            labels = {tarfile.REGTYPE:'REGULAR', tarfile.DIRTYPE:'DIRECTORY',
                      tarfile.SYMTYPE:'SYMLINK'}
            row = dict(name=n, type=labels.get(kind, 'UNSUPPORTED'), mode=mode,
                       uid=0, gid=0, size=t.size, link=link)
            if kind == tarfile.REGTYPE:
                row['sha256'] = hashlib.sha256(body).hexdigest()
            rows.append(row)
    artifact = out.getvalue()
    if artifact_transform:
        artifact = artifact_transform(artifact)
    if edit_index:
        edit_index(rows)
    index = b''.join(enc(r)+b'\n' for r in rows)
    regular = [r for r in rows if r['type']=='REGULAR']
    manifest = dict(kind='j0-offline-fixture-manifest-v1', schema=1, generation=GEN,
                    artifact_sha256=hashlib.sha256(artifact).hexdigest(),
                    index_sha256=hashlib.sha256(index).hexdigest(), entry_count=len(rows),
                    regular_count=len(regular), regular_bytes=sum(r['size'] for r in regular),
                    allow_actions=False)
    if edit_manifest:
        edit_manifest(manifest)
    return artifact, index, enc(manifest)


def fixture(parts=None, lock_edit=None, desc_edit=None, header_edit=None):
    parts = components() if parts is None else parts
    lock = dict(kind='j0-offline-fixture-lock-v1', schema=1, generation=GEN,
                repository_id=1, run_id=2, run_attempt=1, head_sha='b'*40,
                workflow='fixture/builder.yml', builder_sha256='c'*64,
                receiver_sha256='d'*64, policy_sha256='e'*64,
                recipient_fingerprint='f'*64, expires_at=1300, allow_actions=False)
    if lock_edit:
        lock_edit(lock)
    sizes = [dict(role=role, size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
             for role, raw in zip(('rootfs_tar','private_index','manifest'), parts)]
    desc = {k:lock[k] for k in P.BINDINGS}
    desc.update(kind='j0-offline-fixture-descriptor-v1', schema=1,
                expires_at=lock['expires_at'], allow_actions=False,
                ciphertext_bytes=len(CIPHER), ciphertext_sha256=hashlib.sha256(CIPHER).hexdigest(),
                parts=copy.deepcopy(sizes))
    header = dict(kind='j0-offline-fixture-envelope-v1', schema=1, generation=GEN,
                  parts=copy.deepcopy(sizes))
    if desc_edit:
        desc_edit(desc)
    if header_edit:
        header_edit(header)
    raw = enc(header)
    envelope = b'J0XFER1\0'+struct.pack('>I',len(raw))+raw+b''.join(parts)
    return enc(lock), enc(desc), envelope


def run_fixture(values=None):
    lock, desc, envelope = fixture() if values is None else values
    q = P.OfflineQuarantine(lock, desc, NOW)
    q.admit_fixture_ciphertext(CIPHER)
    q.feed_fixture_plaintext(envelope)
    return q.finish_fixture_stream()


class OfflineControls(unittest.TestCase):
    def hold(self, values):
        with self.assertRaises(P.Hold) as caught:
            run_fixture(values)
        self.assertEqual(str(caught.exception), 'HOLD: offline transfer fixture rejected')
        self.assertEqual(caught.exception.args, ())

    def test_roundtrip_all_regular_payloads_and_false_authority(self):
        summary = run_fixture()
        self.assertEqual(summary['regular_payloads_verified'], 11)
        self.assertEqual(summary['entries'], 11)
        self.assertEqual(summary['state'], 'OFFLINE_VERIFIED_NOT_AUTHORIZED')
        for flag in P.FLAGS:
            self.assertIs(summary[flag], False)
        self.assertNotIn('PRIVATE', json.dumps(summary))

    def test_incremental_chunks_and_clear_after_finish(self):
        lock, desc, raw = fixture()
        q = P.OfflineQuarantine(lock, desc, NOW)
        q.admit_fixture_ciphertext(CIPHER)
        for i in range(0,len(raw),7):
            q.feed_fixture_plaintext(raw[i:i+7])
        self.assertEqual(q.finish_fixture_stream()['entries'],11)
        self.assertEqual(len(q._buffer),0)

    def test_lock_types_expiry_scope_and_schema(self):
        for change in [{'schema':True}, {'allow_actions':True}, {'run_id':False},
                       {'run_attempt':2}, {'expires_at':NOW}, {'expires_at':NOW+1801},
                       {'generation':'PRIVATE'}, {'head_sha':'b'*39}, {'extra':1},
                       {'workflow':'PRIVATE/path'}, {'kind':'j0-live-lock-v1'}]:
            with self.subTest(change=change):
                self.hold(fixture(lock_edit=lambda x:x.update(change)))

    def test_every_descriptor_context_binding_must_match(self):
        for key in P.BINDINGS:
            def edit(d):
                d[key] = 999 if type(d[key]) is int else '0'*len(d[key])
            with self.subTest(key=key):
                self.hold(fixture(desc_edit=edit))
        for change in [{'allow_actions':True}, {'expires_at':1299}, {'extra':1},
                       {'kind':'j0-encrypted-fixture-transfer-v1'}, {'ciphertext_bytes':True}]:
            with self.subTest(change=change):
                self.hold(fixture(desc_edit=lambda x:x.update(change)))

    def test_json_duplicate_nonfinite_float_noncanonical_depth_and_size(self):
        for raw in [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}',
                    b'{"x":1.0}', b'{"x":1e2}', b'{"x": 1}', b'[]\n',
                    b'['*17+b'0'+b']'*17, b'"'+b'x'*16384+b'"', b'\xff']:
            with self.subTest(length=len(raw)), self.assertRaises(P.Hold):
                P.read_json(raw,16384)

    def test_wrong_cipher_digest_latches_and_never_recovers(self):
        lock, desc, raw = fixture()
        q = P.OfflineQuarantine(lock, desc, NOW)
        with self.assertRaises(P.Hold):
            q.admit_fixture_ciphertext(b'wrong')
        self.assertEqual(q.state,'HELD')
        for call in [lambda:q.admit_fixture_ciphertext(CIPHER),
                     lambda:q.feed_fixture_plaintext(raw),q.finish_fixture_stream]:
            with self.assertRaises(P.Hold):
                call()

    def test_plaintext_before_cipher_admission_latches(self):
        lock, desc, raw = fixture()
        q = P.OfflineQuarantine(lock,desc,NOW)
        with self.assertRaises(P.Hold):
            q.feed_fixture_plaintext(raw)
        self.assertEqual(q.state,'HELD')

    def test_truncated_prefix_and_part_eof_never_verify(self):
        lock, desc, raw = fixture()
        for end in [0,1,7,8,11,12,20,len(raw)-1]:
            q = P.OfflineQuarantine(lock,desc,NOW)
            q.admit_fixture_ciphertext(CIPHER)
            q.feed_fixture_plaintext(raw[:end])
            with self.subTest(end=end), self.assertRaises(P.Hold):
                q.finish_fixture_stream()
            self.assertEqual(q.state,'HELD')

    def test_header_magic_and_length_bounds(self):
        lock, desc, raw = fixture()
        for changed in [b'PRIVATE!'+raw[8:], raw[:8]+struct.pack('>I',16385)+raw[12:],
                        raw[:8]+b'\0\0\0\0'+raw[12:]]:
            self.hold((lock,desc,changed))

    def test_role_order_duplicate_lengths_and_extra_fields(self):
        edits = [lambda h:h['parts'].reverse(),
                 lambda h:h['parts'][0].update(role='manifest'),
                 lambda h:h['parts'][0].update(size=True),
                 lambda h:h['parts'][0].update(size=0),
                 lambda h:h.update(extra='PRIVATE'),
                 lambda h:h.update(schema=True),
                 lambda h:h.update(generation='0'*32)]
        for edit in edits:
            with self.subTest(edit=edits.index(edit)):
                self.hold(fixture(header_edit=edit))

    def test_trailing_envelope_and_payload_corruption(self):
        lock,desc,raw = fixture()
        self.hold((lock,desc,raw+b'x'))
        offset = 12+struct.unpack('>I',raw[8:12])[0]
        damaged = raw[:offset]+bytes([raw[offset]^1])+raw[offset+1:]
        self.hold((lock,desc,damaged))

    def test_manifest_counters_authority_and_cross_lane_reject(self):
        for change in [{'kind':'j0-wsl2-prepared-fixture-manifest-v1'},
                       {'allow_actions':True}, {'regular_count':7},
                       {'regular_bytes':0}, {'entry_count':True}, {'schema':True},
                       {'generation':'0'*32}, {'extra':'PRIVATE'}]:
            with self.subTest(change=change):
                self.hold(fixture(parts=components(edit_manifest=lambda x:x.update(change))))

    def test_index_only_seven_is_not_complete_verification(self):
        def only_seven(rows):
            del rows[7:]
        self.hold(fixture(parts=components(edit_index=only_seven)))

    def test_unselected_payload_drift_with_rebound_outer_hashes(self):
        a,index,m = components()
        altered = entries()
        n,k,_,mode,link = altered[-1]
        altered[-1]=(n,k,b'CHANGED',mode,link)
        changed,_,_ = components(altered)
        manifest = json.loads(m)
        manifest['artifact_sha256']=hashlib.sha256(changed).hexdigest()
        self.hold(fixture(parts=(changed,index,enc(manifest))))

    def test_index_metadata_and_hash_drift_reject(self):
        for change in [{'mode':0o777},{'uid':1},{'gid':1},{'size':False},
                       {'name':'PRIVATE'},{'type':'DIRECTORY'},{'sha256':'0'*64},
                       {'extra':False}]:
            def edit(rows):
                rows[-1].update(change)
            with self.subTest(change=change):
                self.hold(fixture(parts=components(edit_index=edit)))

    def test_missing_extra_and_duplicate_index_entries(self):
        for edit in [lambda rows:rows.pop(),lambda rows:rows.append(copy.deepcopy(rows[-1])),
                     lambda rows:rows[-1].update(name=rows[0]['name'])]:
            self.hold(fixture(parts=components(edit_index=edit)))

    def test_devices_fifo_hardlink_unknown_reached_and_not_read(self):
        original_next = tarfile.TarFile.next
        original_read = tarfile.TarFile.extractfile
        for kind in [tarfile.CHRTYPE,tarfile.BLKTYPE,tarfile.FIFOTYPE,tarfile.LNKTYPE,b'Z']:
            seen=[]
            def observe(reader):
                t=original_next(reader)
                if t is not None:
                    seen.append(t.type)
                return t
            def read_regular(reader,t):
                self.assertEqual(t.type,tarfile.REGTYPE)
                return original_read(reader,t)
            values=fixture(parts=components(entries(0)+[('PRIVATE',kind,b'',0o644,'python' if kind==tarfile.LNKTYPE else '')]))
            with mock.patch.object(P.tarfile.TarFile,'next',observe), \
                 mock.patch.object(P.tarfile.TarFile,'extractfile',read_regular):
                self.hold(values)
            self.assertIn(kind,seen)

    def test_guest_root_symlink_metadata_never_followed(self):
        items=entries(0)+[('link',tarfile.SYMTYPE,b'',0o777,'/python')]
        original=tarfile.TarFile.extractfile
        calls=[]
        def check(reader,t):
            self.assertEqual(t.type,tarfile.REGTYPE)
            calls.append(t.name)
            return original(reader,t)
        with mock.patch.object(P.tarfile.TarFile,'extractfile',check):
            summary=run_fixture(fixture(parts=components(items)))
        self.assertEqual(calls,['python','sshd'])
        self.assertEqual(summary['entries'],3)

    def test_graph_escape_cycle_missing_parent_and_parent_symlink(self):
        bad = [
            [('x',tarfile.SYMTYPE,b'',0o777,'../python')],
            [('x',tarfile.SYMTYPE,b'',0o777,'y'),('y',tarfile.SYMTYPE,b'',0o777,'x')],
            [('d/file',tarfile.REGTYPE,b'x',0o644,'')],
            [('d',tarfile.SYMTYPE,b'',0o777,'python'),('d/file',tarfile.REGTYPE,b'x',0o644,'')],
            [('x',tarfile.SYMTYPE,b'',0o777,'MISSING')]]
        original=P.verify_graph
        for addition in bad:
            with mock.patch.object(P,'verify_graph',wraps=original) as graph:
                self.hold(fixture(parts=components(entries(0)+addition)))
                self.assertEqual(graph.call_count,1)

    def test_required_fixture_binary_missing_link_or_nonexecutable(self):
        for items in [[entries(0)[0]], [entries(0)[1]],
                      [entries(0)[0],('sshd',tarfile.SYMTYPE,b'',0o777,'python')],
                      [entries(0)[0],('sshd',tarfile.REGTYPE,b'x',0o644,'')]]:
            self.hold(fixture(parts=components(items)))

    def test_canonical_tar_rejects_extra_unbound_trailing_bytes(self):
        self.hold(fixture(parts=components(artifact_transform=lambda a:a+b'PRIVATE')))

    def test_literal_names_and_directories_remain_metadata(self):
        items=entries(0)+[('d',tarfile.DIRTYPE,b'',0o755,''),
                         (r'd/C:\PRIVATE',tarfile.REGTYPE,b'body',0o644,'')]
        summary=run_fixture(fixture(parts=components(items)))
        self.assertEqual(summary['regular_payloads_verified'],3)
        self.assertNotIn('PRIVATE',json.dumps(summary))

    def test_fixture_caps_and_repeat_finish_are_fail_closed(self):
        self.hold(fixture(desc_edit=lambda d:d.update(ciphertext_bytes=P.MAX_FIXTURE+1)))
        self.hold(fixture(parts=components(entries(127))))
        lock,desc,raw=fixture()
        q=P.OfflineQuarantine(lock,desc,NOW)
        q.admit_fixture_ciphertext(CIPHER)
        q.feed_fixture_plaintext(raw)
        q.finish_fixture_stream()
        with self.assertRaises(P.Hold):
            q.finish_fixture_stream()
        self.assertEqual(q.state,'HELD')

    def test_no_host_files_or_member_extraction_calls(self):
        values=fixture()
        with mock.patch('builtins.open',side_effect=AssertionError('host file access')), \
             mock.patch.object(P.tarfile.TarFile,'extractall',side_effect=AssertionError('extractall')), \
             mock.patch.object(P.tarfile.TarFile,'extract',side_effect=AssertionError('extract')):
            self.assertEqual(run_fixture(values)['entries'],11)

    def test_import_audit_and_no_cli_or_action_interface(self):
        tree=ast.parse((HERE/'transfer_offline.py').read_text())
        imports={n.names[0].name for n in tree.body if isinstance(n,ast.Import)}
        self.assertEqual(imports,{'hashlib','io','json','re','struct','tarfile'})
        self.assertFalse(any(isinstance(n,ast.ImportFrom) for n in tree.body))
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls & {'eval','exec','open','compile','input','__import__'})
        self.assertFalse(hasattr(P,'main'))

    def test_no_caller_authenticated_or_authorizing_fields(self):
        for flag in P.FLAGS:
            self.hold(fixture(lock_edit=lambda d:d.update({flag:True})))
            self.hold(fixture(desc_edit=lambda d:d.update({flag:False})))
        self.assertTrue(all(run_fixture()[flag] is False for flag in P.FLAGS))


if __name__ == '__main__':
    unittest.main(verbosity=2)
