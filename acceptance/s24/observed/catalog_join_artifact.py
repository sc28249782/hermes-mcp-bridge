"""ROOTFS_METADATA_CATALOG_V1 source candidate; no live action authorized.

Separate from strict inspection. Headers only for devices; no extraction,
node creation, link following, guest execution or import authority.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import tarfile
import tempfile
import urllib.request
import urllib.error
import ssl

URL = 'https://releases.ubuntu.com/24.04.5/ubuntu-24.04.5-wsl-amd64.wsl'
ARCHIVE_SHA256 = 'bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e'
SOURCE_RECEIPT_SHA256 = '41e2e56ff490475d899894e61c93b0e518439551f193031a8bef38b447805fbc'
MAX_ARCHIVE = 1024 * 1024 * 1024
MAX_MEMBERS = 200000
MAX_LOGICAL_BYTES = 4 * 1024 * 1024 * 1024
MAX_SELECTED_FILE = 32 * 1024 * 1024
CHUNK = 1024 * 1024
POLICY_ID = 'ROOTFS_METADATA_CATALOG_V1'
TYPE_CLASSES = ('REGULAR', 'DIRECTORY', 'SYMLINK', 'HARDLINK', 'CHAR_DEVICE', 'BLOCK_DEVICE')
DEVICE_CLASSES = frozenset(('CHAR_DEVICE', 'BLOCK_DEVICE'))


STAGES = frozenset(('START', 'GUARD', 'RESOURCE_LIMITS', 'RECEIPT_BINDING',
                    'TEMPFILE', 'HTTP_OPEN', 'HTTP_HEADERS', 'HTTP_BODY',
                    'ARCHIVE_HASH', 'ARCHIVE_PARSE', 'RECEIPT_ENCODE', 'CLEANUP', 'COMPLETE'))
ERRORS = frozenset(('PREDICATE_REJECTED', 'REDIRECT_REJECTED', 'HTTP_403', 'HTTP_404',
                    'HTTP_429', 'HTTP_5XX', 'HTTP_OTHER', 'TLS_ERROR', 'TIMEOUT',
                    'TRANSPORT_ERROR', 'IO_ERROR', 'MEMORY_LIMIT', 'ARCHIVE_ERROR',
                    'JSON_ERROR', 'UNEXPECTED_ERROR', 'NONE'))


PREDICATE_REASONS = frozenset(('NAME_LENGTH_OR_TYPE', 'ABSOLUTE_PATH', 'BACKSLASH', 'PATH_COMPONENT', 'NAME_CONTROL', 'NAME_DUPLICATE', 'COUNT_MEMBERS', 'HEADER_SIZE_RANGE', 'SIZE_LOGICAL', 'LINK_LENGTH', 'SPARSE', 'TYPE_REJECTED', 'ROOT_NOT_DIRECTORY', 'COUNT_SELECTED', 'SIZE_SELECTED', 'SELECTED_STREAM_MISSING', 'SIZE_SELECTED_READ', 'SELECTED_READ_SIZE', 'EMPTY_ARCHIVE', 'DEVICE_METADATA_REJECTED', 'SELECTED_DEVICE_COLLISION'))


class Diagnostic:
    def __init__(self):
        self.stage = 'START'
        self.received_bytes = 0
        self.hashed_bytes = 0
        self.download_complete = False
        self.hash_complete = False
        self.archive_sha256 = None
        self.digest_matches = None
        self.parsed_members = 0
        self.type_counts = dict.fromkeys(TYPE_CLASSES, 0)
        self.type_counts_complete = False

    def frame(self, error):
        code = error_code(error)
        require(self.stage in STAGES and code in ERRORS)
        require(0 <= self.received_bytes <= MAX_ARCHIVE + 1)
        require(0 <= self.hashed_bytes <= MAX_ARCHIVE + 1)
        require(0 <= self.parsed_members <= MAX_MEMBERS)
        require(self.archive_sha256 is None or re.fullmatch('[0-9a-f]{64}', self.archive_sha256))
        require(set(self.type_counts) == set(TYPE_CLASSES))
        require(all(type(v) is int and 0 <= v <= MAX_MEMBERS for v in self.type_counts.values()))
        require(sum(self.type_counts.values()) <= self.parsed_members)
        complete = error is None and self.type_counts_complete
        if complete:
            require(sum(self.type_counts.values()) == self.parsed_members)
        # No error object/args/reason/URL/path/header/content appears in this frame.
        reason = None
        if (isinstance(error, PredicateHold) and code == 'PREDICATE_REJECTED'
                and self.stage == 'ARCHIVE_PARSE'):
            require(type(error.reason) is str and error.reason in PREDICATE_REASONS)
            reason = error.reason
        return {'evidence_class': 'j0-metadata-catalog-diagnostic-only', 'schema': 1,
                'policy_id': POLICY_ID, 'type_counts': dict(self.type_counts),
                'type_counts_complete': complete, 'metadata_catalog_complete': False,
                'archive_inspection_verified': False, 'extraction_authorized': False,
                'prepared_guest_artifact': False, 'import_compatibility_tested': False,
                'predicate_reason': reason,
                'stage': self.stage, 'error': code, 'received_bytes': self.received_bytes,
                'hashed_bytes': self.hashed_bytes, 'download_complete': self.download_complete,
                'hash_complete': self.hash_complete, 'archive_sha256': self.archive_sha256,
                'digest_matches': self.digest_matches, 'parsed_members': self.parsed_members,
                'archive_verified_receipt': False, 'j0_ready': False, 'setup_ready': False,
                'guest_imported': False, 'guest_started': False, 'r1_complete': False,
                'r2_authorized': False, 'scope_granted': False}


def error_code(error):
    # Exact fixed classifications only. Never stringify exceptions, URL/reason,
    # SSL verification text, filenames, errno or server response headers/bodies.
    if error is None:
        return 'NONE'
    if isinstance(error, RedirectHold):
        return 'REDIRECT_REJECTED'
    if isinstance(error, DeadlineHold) or isinstance(error, TimeoutError):
        return 'TIMEOUT'
    if isinstance(error, Hold):
        return 'PREDICATE_REJECTED'
    if isinstance(error, urllib.error.HTTPError):
        if error.code in (403, 404, 429):
            return {403: 'HTTP_403', 404: 'HTTP_404', 429: 'HTTP_429'}[error.code]
        return 'HTTP_5XX' if isinstance(error.code, int) and 500 <= error.code <= 599 else 'HTTP_OTHER'
    if isinstance(error, ssl.SSLError):
        return 'TLS_ERROR'
    if isinstance(error, urllib.error.URLError):
        # Inspect type only, never serialize the reason. DNS and other transport
        # failures intentionally share one coarse code.
        if isinstance(error.reason, ssl.SSLError):
            return 'TLS_ERROR'
        return 'TIMEOUT' if isinstance(error.reason, TimeoutError) else 'TRANSPORT_ERROR'
    if isinstance(error, MemoryError):
        return 'MEMORY_LIMIT'
    if isinstance(error, tarfile.TarError) or isinstance(error, EOFError):
        return 'ARCHIVE_ERROR'
    if isinstance(error, json.JSONDecodeError):
        return 'JSON_ERROR'
    return 'IO_ERROR' if isinstance(error, OSError) else 'UNEXPECTED_ERROR'


def diagnostic_line(progress, error):
    encoded = json.dumps(progress.frame(error), sort_keys=True, ensure_ascii=True, separators=(',', ':'))
    require(len(encoded.encode('ascii')) <= 2048)
    return encoded


class Hold(Exception):
    pass


class PredicateHold(Hold):
    def __init__(self, reason):
        require(type(reason) is str and reason in PREDICATE_REASONS)
        self.reason = reason
        # No input member name/value/error text is stored in exception args.
        super().__init__()


def predicate(value, reason):
    if not value:
        raise PredicateHold(reason)


class RedirectHold(Hold):
    pass


class DeadlineHold(Hold):
    pass


def require(value):
    if not value:
        raise Hold()


def digest(stream, ceiling, progress=None, reason=None):
    total = 0
    h = hashlib.sha256()
    while True:
        block = stream.read(min(CHUNK, ceiling - total + 1))
        if not block:
            return total, h.hexdigest()
        total += len(block)
        if progress is not None:
            progress.hashed_bytes = total
        if reason is None:
            require(total <= ceiling)
        else:
            predicate(total <= ceiling, reason)
        h.update(block)


def member_name(name):
    predicate(isinstance(name, str) and 0 < len(name) <= 4096, 'NAME_LENGTH_OR_TYPE')
    while name.startswith('./'):
        name = name[2:]
    if name in ('', '.'):
        return '.'
    predicate(not name.startswith('/'), 'ABSOLUTE_PATH')
    predicate('\\' not in name, 'BACKSLASH')
    name = name.rstrip('/')
    predicate(all(part not in ('', '.', '..') for part in name.split('/')), 'PATH_COMPONENT')
    predicate(not any(ord(c) < 32 or ord(c) == 127 for c in name), 'NAME_CONTROL')
    return name


def selected(name):
    return name in {'etc/os-release', 'usr/lib/os-release', 'usr/bin/python3',
                    'usr/sbin/sshd', 'var/lib/dpkg/status', 'etc/wsl.conf',
                    'etc/wsl-distribution.conf'} or re.fullmatch(r'usr/bin/python3\.[0-9]+', name) is not None


def classify(item):
    # Match the strict lane's original method order, then exactly two types.
    if item.isreg():
        return 'REGULAR'
    if item.isdir():
        return 'DIRECTORY'
    if item.issym():
        return 'SYMLINK'
    if item.islnk():
        return 'HARDLINK'
    if item.type == tarfile.CHRTYPE:
        return 'CHAR_DEVICE'
    if item.type == tarfile.BLKTYPE:
        return 'BLOCK_DEVICE'
    raise PredicateHold('TYPE_REJECTED')


def device_metadata(item):
    predicate(item.size == 0 and item.linkname == '', 'DEVICE_METADATA_REJECTED')
    for value in (item.devmajor, item.devminor):
        predicate(type(value) is int and 0 <= value <= 2**32-1, 'DEVICE_METADATA_REJECTED')
    for value in (item.mode, item.uid, item.gid):
        predicate(type(value) is int and 0 <= value <= 2**63-1, 'DEVICE_METADATA_REJECTED')


def inspect(stream, expected_sha, progress=None):
    # Same already-open stream; hash verified BEFORE any archive parser sees bytes.
    if progress is not None:
        progress.stage = 'ARCHIVE_HASH'
    stream.seek(0)
    size, sha = digest(stream, MAX_ARCHIVE, progress)
    if progress is not None:
        progress.hash_complete = True
        progress.archive_sha256 = sha
        progress.digest_matches = sha == expected_sha
    require(size > 0 and sha == expected_sha)
    stream.seek(0)
    seen = set()
    logical = 0
    catalog = hashlib.sha256()
    catalog.update(POLICY_ID.encode('ascii') + b'\0')
    targets = []
    counts = dict.fromkeys(TYPE_CLASSES, 0)
    if progress is not None:
        progress.type_counts = counts
        progress.type_counts_complete = False
    if progress is not None:
        progress.stage = 'ARCHIVE_PARSE'
    with tarfile.open(fileobj=stream, mode='r|*') as archive:
        for item in archive:
            predicate(len(seen) < MAX_MEMBERS, 'COUNT_MEMBERS')
            name = member_name(item.name)
            predicate(name not in seen, 'NAME_DUPLICATE')
            predicate(0 <= item.size <= MAX_LOGICAL_BYTES, 'HEADER_SIZE_RANGE')
            seen.add(name)
            if progress is not None:
                progress.parsed_members = len(seen)
            logical += item.size
            predicate(logical <= MAX_LOGICAL_BYTES, 'SIZE_LOGICAL')
            predicate(len(item.linkname) <= 4096, 'LINK_LENGTH')
            # Reject sparse encoding even when its extent list is empty.
            predicate(item.sparse is None and item.type != tarfile.GNUTYPE_SPARSE, 'SPARSE')
            kind = classify(item)
            predicate(name != '.' or item.isdir(), 'ROOT_NOT_DIRECTORY')
            if kind in DEVICE_CLASSES:
                device_metadata(item)
            counts[kind] += 1
            if kind in DEVICE_CLASSES:
                predicate(not selected(name), 'SELECTED_DEVICE_COLLISION')
            record = {'name': name, 'type_hex': item.type.hex(), 'size': item.size,
                      'mode': item.mode, 'uid': item.uid, 'gid': item.gid,
                      'link': item.linkname}
            if kind in DEVICE_CLASSES:
                # Hash only; these numbers and the device name never enter output.
                record['devmajor'] = item.devmajor
                record['devminor'] = item.devminor
            catalog.update((json.dumps(record, sort_keys=True, ensure_ascii=True,
                                       separators=(',', ':')) + '\n').encode('ascii'))
            if kind not in DEVICE_CLASSES and selected(name):
                predicate(len(targets) < 32, 'COUNT_SELECTED')
                target = dict(record)
                # No link following/resolution. Only regular selected file data
                # receives a content hash; links are disclosed, not admitted.
                if kind == 'REGULAR':
                    predicate(item.size <= MAX_SELECTED_FILE, 'SIZE_SELECTED')
                    data = archive.extractfile(item)
                    predicate(data is not None, 'SELECTED_STREAM_MISSING')
                    with data:
                        read_size, content_sha = digest(data, MAX_SELECTED_FILE, reason='SIZE_SELECTED_READ')
                    predicate(read_size == item.size, 'SELECTED_READ_SIZE')
                    target['content_sha256'] = content_sha
                targets.append(target)
    predicate(seen, 'EMPTY_ARCHIVE')
    if progress is not None:
        progress.type_counts_complete = True
    return {'evidence_class': 'j0-rootfs-metadata-catalog-only', 'schema': 1,
            'policy_id': POLICY_ID, 'metadata_catalog_complete': True,
            'type_counts': dict(counts), 'archive_inspection_verified': False,
            'extraction_authorized': False, 'archive_bytes': size,
            'author_computed_archive_sha256': sha, 'archive_matches_provider_digest': True,
            'tar_header_count': len(seen), 'declared_logical_bytes': logical,
            'ordered_header_catalog_sha256': catalog.hexdigest(), 'selected_entries': targets,
            'catalog_scope': 'policy-prefixed headers including device metadata; selected regular hashes; no full content tree',
            'provider_signature_verified': False, 'links_resolved': False,
            'import_compatibility_tested': False, 'prepared_guest_artifact': False,
            'setup_ready': False, 'j0_ready': False, 'guest_imported': False,
            'guest_started': False, 'r1_complete': False, 'r2_authorized': False,
            'scope_granted': False}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            if fp is not None:
                fp.close()
        finally:
            raise RedirectHold()


def download(output, progress=None):
    # No proxy/redirect/retry/fallback, credentials or user-selected URL.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(URL, headers={'Accept-Encoding': 'identity'})
    if progress is not None:
        progress.stage = 'HTTP_OPEN'
    try:
        response = opener.open(request, timeout=15)
    except urllib.error.HTTPError as error:
        # HTTPError owns a response wrapper even before with-entry. Close it
        # explicitly: finalizer warnings could otherwise stringify private text.
        error.close()
        raise
    with response:
        if progress is not None:
            progress.stage = 'HTTP_HEADERS'
        require(response.status == 200 and response.geturl() == URL)
        require(response.headers.get('Content-Encoding', 'identity') == 'identity')
        length = response.headers.get('Content-Length')
        if length is not None:
            require(length.isascii() and length.isdecimal() and 0 < int(length) <= MAX_ARCHIVE)
        if progress is not None:
            progress.stage = 'HTTP_BODY'
        count = 0
        while True:
            data = response.read(min(CHUNK, MAX_ARCHIVE - count + 1))
            if not data:
                break
            count += len(data)
            if progress is not None:
                progress.received_bytes = count
            require(count <= MAX_ARCHIVE)
            require(output.write(data) == len(data))
        require(count > 0 and (length is None or count == int(length)))
    output.flush()
    if progress is not None:
        progress.download_complete = True


def main():
    progress = Diagnostic()
    alarm_armed = False
    try:
        progress.stage = 'GUARD'
        require(sys.argv[1:] == ['--download-and-catalog-metadata'])
        require(sys.platform == 'linux' and os.environ.get('GITHUB_ACTIONS') == 'true'
                and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
                and os.environ.get('RUNNER_OS') == 'Linux')
        # New artifact process only: wall time and address-space containment, not
        # guest/operational stop proof. Production observer timers are untouched.
        progress.stage = 'RESOURCE_LIMITS'
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        def expired(_signum, _frame):
            raise DeadlineHold()
        signal.signal(signal.SIGALRM, expired)
        signal.alarm(120)
        alarm_armed = True
        progress.stage = 'RECEIPT_BINDING'
        receipt = Path(__file__).with_name('J0-PROVIDER-SOURCE.json').read_bytes()
        require(hashlib.sha256(receipt).hexdigest() == SOURCE_RECEIPT_SHA256)
        selection = json.loads(receipt)['selection']
        require(selection['url'] == URL and selection['provider_reported_archive_sha256'] == ARCHIVE_SHA256)
        # Automatically deletes ONLY its new private temporary archive on exit.
        # No extraction directory or persistent prepared rootfs is created.
        progress.stage = 'TEMPFILE'
        with tempfile.TemporaryFile(mode='w+b') as output:
            download(output, progress)
            result = inspect(output, ARCHIVE_SHA256, progress)
            progress.stage = 'CLEANUP'
        progress.stage = 'RECEIPT_ENCODE'
        encoded = json.dumps(result, sort_keys=True, ensure_ascii=True, separators=(',', ':'))
        require(len(encoded.encode('ascii')) <= 65536)
        signal.alarm(0)
        alarm_armed = False
        progress.stage = 'COMPLETE'
        detail = diagnostic_line(progress, None)
        print(encoded)
        print(detail)
        return 0
    except Exception as error:
        if alarm_armed:
            signal.alarm(0)
        try:
            detail = diagnostic_line(progress, error)
        except Exception:
            # Diagnostic allocation/serialization may itself fail under pressure.
            # Fixed fallback, never a traceback containing the original error.
            detail = '{"evidence_class":"j0-metadata-catalog-diagnostic-unavailable","schema":1,"error":"DIAGNOSTIC_UNAVAILABLE"}'
        try:
            print('HOLD: artifact preparation incomplete')
            print(detail)
        except Exception:
            # Closed/broken output remains failure; do not propagate an error
            # whose chained traceback could stringify the original exception.
            pass
        return 2


if __name__ == '__main__':
    sys.exit(main())
