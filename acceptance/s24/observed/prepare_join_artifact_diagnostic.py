"""E13 diagnostic variant FOR REVIEW, no live invocation authorized.

CI executes offline controls only. --download-and-inspect requires separate review;
no extraction, WSL invocation, guest execution, package install or setup is present.
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


STAGES = frozenset(('START', 'GUARD', 'RESOURCE_LIMITS', 'RECEIPT_BINDING',
                    'TEMPFILE', 'HTTP_OPEN', 'HTTP_HEADERS', 'HTTP_BODY',
                    'ARCHIVE_HASH', 'ARCHIVE_PARSE', 'RECEIPT_ENCODE', 'CLEANUP', 'COMPLETE'))
ERRORS = frozenset(('PREDICATE_REJECTED', 'REDIRECT_REJECTED', 'HTTP_403', 'HTTP_404',
                    'HTTP_429', 'HTTP_5XX', 'HTTP_OTHER', 'TLS_ERROR', 'TIMEOUT',
                    'TRANSPORT_ERROR', 'IO_ERROR', 'MEMORY_LIMIT', 'ARCHIVE_ERROR',
                    'JSON_ERROR', 'UNEXPECTED_ERROR', 'NONE'))


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

    def frame(self, error):
        code = error_code(error)
        require(self.stage in STAGES and code in ERRORS)
        require(0 <= self.received_bytes <= MAX_ARCHIVE + 1)
        require(0 <= self.hashed_bytes <= MAX_ARCHIVE + 1)
        require(0 <= self.parsed_members <= MAX_MEMBERS)
        require(self.archive_sha256 is None or re.fullmatch('[0-9a-f]{64}', self.archive_sha256))
        # No error object/args/reason/URL/path/header/content appears in this frame.
        return {'evidence_class': 'j0-artifact-diagnostic-only', 'schema': 1,
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


class RedirectHold(Hold):
    pass


class DeadlineHold(Hold):
    pass


def require(value):
    if not value:
        raise Hold()


def digest(stream, ceiling, progress=None):
    total = 0
    h = hashlib.sha256()
    while True:
        block = stream.read(min(CHUNK, ceiling - total + 1))
        if not block:
            return total, h.hexdigest()
        total += len(block)
        if progress is not None:
            progress.hashed_bytes = total
        require(total <= ceiling)
        h.update(block)


def member_name(name):
    require(isinstance(name, str) and 0 < len(name) <= 4096)
    while name.startswith('./'):
        name = name[2:]
    if name in ('', '.'):
        return '.'
    require(not name.startswith('/') and '\\' not in name)
    name = name.rstrip('/')
    require(all(part not in ('', '.', '..') for part in name.split('/')))
    require(not any(ord(c) < 32 or ord(c) == 127 for c in name))
    return name


def selected(name):
    return name in {'etc/os-release', 'usr/lib/os-release', 'usr/bin/python3',
                    'usr/sbin/sshd', 'var/lib/dpkg/status', 'etc/wsl.conf',
                    'etc/wsl-distribution.conf'} or re.fullmatch(r'usr/bin/python3\.[0-9]+', name) is not None


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
    targets = []
    if progress is not None:
        progress.stage = 'ARCHIVE_PARSE'
    with tarfile.open(fileobj=stream, mode='r|*') as archive:
        for item in archive:
            require(len(seen) < MAX_MEMBERS)
            name = member_name(item.name)
            require(name not in seen and 0 <= item.size <= MAX_LOGICAL_BYTES)
            seen.add(name)
            if progress is not None:
                progress.parsed_members = len(seen)
            logical += item.size
            require(logical <= MAX_LOGICAL_BYTES)
            require(len(item.linkname) <= 4096 and not item.sparse)
            require(item.isreg() or item.isdir() or item.issym() or item.islnk())
            require(name != '.' or item.isdir())
            record = {'name': name, 'type_hex': item.type.hex(), 'size': item.size,
                      'mode': item.mode, 'uid': item.uid, 'gid': item.gid,
                      'link': item.linkname}
            catalog.update((json.dumps(record, sort_keys=True, ensure_ascii=True,
                                       separators=(',', ':')) + '\n').encode('ascii'))
            if selected(name):
                require(len(targets) < 32)
                target = dict(record)
                # No link following/resolution. Only regular selected file data
                # receives a content hash; links are disclosed, not admitted.
                if item.isreg():
                    require(item.size <= MAX_SELECTED_FILE)
                    data = archive.extractfile(item)
                    require(data is not None)
                    with data:
                        read_size, content_sha = digest(data, MAX_SELECTED_FILE)
                    require(read_size == item.size)
                    target['content_sha256'] = content_sha
                targets.append(target)
    require(seen)
    return {'evidence_class': 'j0-archive-inspection-only', 'archive_bytes': size,
            'author_computed_archive_sha256': sha, 'archive_matches_provider_digest': True,
            'tar_header_count': len(seen), 'declared_logical_bytes': logical,
            'ordered_header_catalog_sha256': catalog.hexdigest(), 'selected_entries': targets,
            'catalog_scope': 'headers plus selected regular-file content hashes; no full content tree',
            'provider_signature_verified': False, 'links_resolved': False,
            'import_compatibility_tested': False, 'prepared_guest_artifact': False,
            'setup_ready': False, 'j0_ready': False, 'guest_imported': False,
            'guest_started': False, 'r1_complete': False, 'r2_authorized': False,
            'scope_granted': False}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RedirectHold()


def download(output, progress=None):
    # No proxy/redirect/retry/fallback, credentials or user-selected URL.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(URL, headers={'Accept-Encoding': 'identity'})
    if progress is not None:
        progress.stage = 'HTTP_OPEN'
    with opener.open(request, timeout=15) as response:
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
        require(sys.argv[1:] == ['--download-and-inspect-diagnostic'])
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
            detail = '{"evidence_class":"j0-artifact-diagnostic-unavailable","schema":1,"error":"DIAGNOSTIC_UNAVAILABLE"}'
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
