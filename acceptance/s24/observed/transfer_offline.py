"""Synthetic offline transfer profile; no crypto, custody, filesystem or action API."""
import hashlib
import io
import json
import re
import struct
import tarfile

MAX_FIXTURE = 8 * 1024**2
MAX_META = 1024**2
MAX_HEADER = 16384
MAX_ROWS = 128
MAGIC = b'J0XFER1\0'
ROLES = ('rootfs_tar', 'private_index', 'manifest')
BINDINGS = ('generation', 'repository_id', 'run_id', 'run_attempt', 'head_sha',
            'workflow', 'builder_sha256', 'receiver_sha256', 'policy_sha256',
            'recipient_fingerprint')
LOCK_KEYS = set(BINDINGS) | {'kind', 'schema', 'expires_at', 'allow_actions'}
DESC_KEYS = set(BINDINGS) | {'kind', 'schema', 'expires_at', 'allow_actions',
                           'ciphertext_bytes', 'ciphertext_sha256', 'parts'}
FLAGS = ('crypto_authenticated', 'provenance_authenticated', 'scope_granted',
         'j0_ready', 'r1_complete', 'r2_authorized', 'import_authorized')
REQUIRED_FIXTURE_FILES = ('python', 'sshd')


class Hold(Exception):
    def __str__(self):
        return 'HOLD: offline transfer fixture rejected'


def need(value):
    if not value:
        raise Hold()


def integer(value, low, high):
    need(type(value) is int and low <= value <= high)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(',', ':'), allow_nan=False).encode('ascii')


def pairs(values):
    result = {}
    for key, value in values:
        need(key not in result)
        result[key] = value
    return result


def read_json(raw, limit):
    try:
        need(type(raw) is bytes and 0 < len(raw) <= limit)
        depth = 0
        quoted = escaped = False
        for c in raw:
            if quoted:
                if escaped:
                    escaped = False
                elif c == 92:
                    escaped = True
                elif c == 34:
                    quoted = False
            elif c == 34:
                quoted = True
            elif c in (91, 123):
                depth += 1
                need(depth <= 16)
            elif c in (93, 125):
                depth -= 1
                need(depth >= 0)
        need(depth == 0 and not quoted)
        value = json.loads(raw.decode('ascii'), object_pairs_hook=pairs,
                           parse_float=lambda _: (_ for _ in ()).throw(Hold()),
                           parse_constant=lambda _: (_ for _ in ()).throw(Hold()))
        need(encoded(value) == raw)
        return value
    except Exception:
        raise Hold() from None


def hexdigest(value, length=64):
    need(type(value) is str and re.fullmatch('[0-9a-f]{'+str(length)+'}', value) is not None)


def validate_lock(raw, fixture_now):
    lock = read_json(raw, MAX_HEADER)
    need(type(lock) is dict and set(lock) == LOCK_KEYS)
    need(lock['kind'] == 'j0-offline-fixture-lock-v1' and type(lock['schema']) is int and lock['schema'] == 1)
    need(lock['allow_actions'] is False and lock['workflow'] == 'fixture/builder.yml')
    for key in ('repository_id', 'run_id'):
        integer(lock[key], 1, 2**63-1)
    integer(lock['run_attempt'], 1, 1)
    integer(fixture_now, 0, 2**63-1801)
    integer(lock['expires_at'], fixture_now+1, fixture_now+1800)
    hexdigest(lock['generation'], 32)
    hexdigest(lock['head_sha'], 40)
    for key in ('builder_sha256', 'receiver_sha256', 'policy_sha256', 'recipient_fingerprint'):
        hexdigest(lock[key])
    return lock


def validate_parts(parts):
    need(type(parts) is list and len(parts) == 3)
    for expected, part in zip(ROLES, parts):
        need(type(part) is dict and set(part) == {'role', 'size', 'sha256'})
        need(part['role'] == expected)
        integer(part['size'], 1, MAX_FIXTURE if expected == 'rootfs_tar' else MAX_META)
        hexdigest(part['sha256'])
    need(sum(p['size'] for p in parts) <= MAX_FIXTURE)
    need(parts[1]['size']+parts[2]['size'] <= MAX_META)


def validate_descriptor(raw, lock):
    desc = read_json(raw, MAX_HEADER)
    need(type(desc) is dict and set(desc) == DESC_KEYS)
    need(desc['kind'] == 'j0-offline-fixture-descriptor-v1' and type(desc['schema']) is int and desc['schema'] == 1)
    need(desc['allow_actions'] is False and desc['expires_at'] == lock['expires_at'])
    for key in BINDINGS:
        need(type(desc[key]) is type(lock[key]) and desc[key] == lock[key])
    integer(desc['ciphertext_bytes'], 1, MAX_FIXTURE)
    hexdigest(desc['ciphertext_sha256'])
    validate_parts(desc['parts'])
    return desc


def name(value):
    need(type(value) is str and 0 < len(value) <= 4096)
    need(all(32 <= ord(c) < 127 for c in value))
    need(not value.startswith('/') and all(p not in ('', '.', '..') for p in value.split('/')))
    return value


def target(link_name, value):
    need(type(value) is str and 0 < len(value) <= 4096)
    need(all(32 <= ord(c) < 127 for c in value))
    parts = [] if value.startswith('/') else link_name.split('/')[:-1]
    for part in value.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            need(parts)
            parts.pop()
        else:
            parts.append(part)
    need(parts)
    return '/'.join(parts)


def verify_graph(rows):
    mapping = {r['name']: r for r in rows}
    need(len(mapping) == len(rows))
    for r in rows:
        bits = r['name'].split('/')
        for i in range(1, len(bits)):
            need('/'.join(bits[:i]) in mapping and mapping['/'.join(bits[:i])]['type'] == 'DIRECTORY')
        if r['type'] == 'SYMLINK':
            current = r
            seen = set()
            for _ in range(16):
                need(current['name'] not in seen)
                seen.add(current['name'])
                path = target(current['name'], current['link'])
                need(path in mapping)
                current = mapping[path]
                if current['type'] != 'SYMLINK':
                    break
            else:
                raise Hold()
            need(current['type'] in ('REGULAR', 'DIRECTORY'))
    for required in REQUIRED_FIXTURE_FILES:
        need(required in mapping and mapping[required]['type'] == 'REGULAR' and mapping[required]['mode'] == 0o755)


def verify_payloads(artifact, index_raw, manifest_raw, generation):
    """Canonical ASCII USTAR fixture subset, not a production rootfs admission policy."""
    need(0 < len(artifact) <= MAX_FIXTURE and 0 < len(index_raw) <= MAX_META)
    need(index_raw.endswith(b'\n'))
    lines = index_raw[:-1].split(b'\n')
    need(1 <= len(lines) <= MAX_ROWS)
    rows = [read_json(line, MAX_HEADER) for line in lines]
    manifest = read_json(manifest_raw, MAX_HEADER)
    need(type(manifest) is dict and set(manifest) == {
        'kind', 'schema', 'generation', 'artifact_sha256', 'index_sha256',
        'entry_count', 'regular_count', 'regular_bytes', 'allow_actions'})
    need(manifest['kind'] == 'j0-offline-fixture-manifest-v1' and type(manifest['schema']) is int and manifest['schema'] == 1)
    need(manifest['generation'] == generation and manifest['allow_actions'] is False)
    need(manifest['artifact_sha256'] == digest(artifact) and manifest['index_sha256'] == digest(index_raw))
    for key in ('entry_count', 'regular_count'):
        integer(manifest[key], 0, MAX_ROWS)
    integer(manifest['regular_bytes'], 0, MAX_FIXTURE)
    actual = []
    regular_count = regular_bytes = 0
    canonical = io.BytesIO()
    try:
        with tarfile.open(fileobj=io.BytesIO(artifact), mode='r:') as reader, \
             tarfile.open(fileobj=canonical, mode='w', format=tarfile.USTAR_FORMAT, encoding='ascii') as writer:
            for member in reader:
                need(len(actual) < MAX_ROWS and member.sparse is None and not member.pax_headers)
                n = name(member.name)
                need(member.type in (tarfile.REGTYPE, tarfile.DIRTYPE, tarfile.SYMTYPE))
                kind = {tarfile.REGTYPE: 'REGULAR', tarfile.DIRTYPE: 'DIRECTORY', tarfile.SYMTYPE: 'SYMLINK'}[member.type]
                integer(member.size, 0, MAX_FIXTURE)
                need(member.uid == member.gid == member.mtime == 0 and member.uname == member.gname == '')
                need(member.mode in ((0o644, 0o755) if kind == 'REGULAR' else ((0o755,) if kind == 'DIRECTORY' else (0o777,))))
                need(member.devmajor == member.devminor == 0)
                row = dict(name=n, type=kind, mode=member.mode, uid=member.uid,
                           gid=member.gid, size=member.size, link=member.linkname)
                data = None
                if kind == 'REGULAR':
                    need(member.linkname == '')
                    stream = reader.extractfile(member)
                    need(stream is not None)
                    with stream:
                        body = stream.read(MAX_FIXTURE+1)
                    need(len(body) == member.size and len(body) <= MAX_FIXTURE)
                    regular_count += 1
                    regular_bytes += len(body)
                    need(regular_bytes <= MAX_FIXTURE)
                    row['sha256'] = digest(body)
                    data = io.BytesIO(body)
                else:
                    need(member.size == 0)
                    if kind == 'DIRECTORY':
                        need(member.linkname == '')
                actual.append(row)
                writer.addfile(member, data)
    except Exception:
        raise Hold() from None
    need(canonical.getvalue() == artifact)
    need(encoded(rows) == encoded(actual))
    verify_graph(actual)
    need(manifest['entry_count'] == len(actual) and manifest['regular_count'] == regular_count
         and manifest['regular_bytes'] == regular_bytes)
    return {'entries': len(actual), 'regular_payloads_verified': regular_count,
            'regular_bytes_verified': regular_bytes, 'artifact_sha256': digest(artifact)}


class OfflineQuarantine:
    """In-memory synthetic state machine. Never yields plaintext or a usable import token."""
    def __init__(self, lock_raw, descriptor_raw, fixture_now):
        self.state = 'NEW'
        self._buffer = bytearray()
        try:
            self._lock = validate_lock(lock_raw, fixture_now)
            self._desc = validate_descriptor(descriptor_raw, self._lock)
        except Exception:
            self._hold()

    def _hold(self):
        self.state = 'HELD'
        self._buffer.clear()
        raise Hold() from None

    def admit_fixture_ciphertext(self, raw):
        try:
            need(self.state == 'NEW' and type(raw) is bytes and len(raw) <= MAX_FIXTURE)
            need(len(raw) == self._desc['ciphertext_bytes'] and digest(raw) == self._desc['ciphertext_sha256'])
            self.state = 'QUARANTINED'
        except Exception:
            self._hold()

    def feed_fixture_plaintext(self, chunk):
        try:
            need(self.state == 'QUARANTINED' and type(chunk) is bytes)
            need(len(self._buffer)+len(chunk) <= MAX_FIXTURE+MAX_HEADER+12)
            self._buffer.extend(chunk)
        except Exception:
            self._hold()

    def finish_fixture_stream(self):
        # Fixture EOF is NOT an age authenticated EOF/provenance/custody result.
        try:
            need(self.state == 'QUARANTINED')
            raw = bytes(self._buffer)
            need(len(raw) >= 12 and raw[:8] == MAGIC)
            length = struct.unpack('>I', raw[8:12])[0]
            integer(length, 1, MAX_HEADER)
            need(len(raw) >= 12+length)
            header = read_json(raw[12:12+length], MAX_HEADER)
            need(type(header) is dict and set(header) == {'kind', 'schema', 'generation', 'parts'})
            need(header['kind'] == 'j0-offline-fixture-envelope-v1' and type(header['schema']) is int and header['schema'] == 1)
            need(header['generation'] == self._lock['generation'])
            validate_parts(header['parts'])
            need(encoded(header['parts']) == encoded(self._desc['parts']))
            pos = 12+length
            parts = []
            for part in header['parts']:
                end = pos+part['size']
                need(end <= len(raw))
                body = raw[pos:end]
                need(digest(body) == part['sha256'])
                parts.append(body)
                pos = end
            need(pos == len(raw))
            summary = verify_payloads(*parts, self._lock['generation'])
            self.state = 'OFFLINE_VERIFIED_NOT_AUTHORIZED'
            self._buffer.clear()
            return dict(summary, state=self.state, **dict.fromkeys(FLAGS, False))
        except Exception:
            self._hold()
