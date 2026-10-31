"""J0 source candidate: bounded provider download/inspection, NEVER provisioning.

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

URL = 'https://releases.ubuntu.com/24.04.5/ubuntu-24.04.5-wsl-amd64.wsl'
ARCHIVE_SHA256 = 'bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e'
SOURCE_RECEIPT_SHA256 = '41e2e56ff490475d899894e61c93b0e518439551f193031a8bef38b447805fbc'
MAX_ARCHIVE = 1024 * 1024 * 1024
MAX_MEMBERS = 200000
MAX_LOGICAL_BYTES = 4 * 1024 * 1024 * 1024
MAX_SELECTED_FILE = 32 * 1024 * 1024
CHUNK = 1024 * 1024


class Hold(Exception):
    pass


def require(value):
    if not value:
        raise Hold()


def digest(stream, ceiling):
    total = 0
    h = hashlib.sha256()
    while True:
        block = stream.read(min(CHUNK, ceiling - total + 1))
        if not block:
            return total, h.hexdigest()
        total += len(block)
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


def inspect(stream, expected_sha):
    # Same already-open stream; hash verified BEFORE any archive parser sees bytes.
    stream.seek(0)
    size, sha = digest(stream, MAX_ARCHIVE)
    require(size > 0 and sha == expected_sha)
    stream.seek(0)
    seen = set()
    logical = 0
    catalog = hashlib.sha256()
    targets = []
    with tarfile.open(fileobj=stream, mode='r|*') as archive:
        for item in archive:
            require(len(seen) < MAX_MEMBERS)
            name = member_name(item.name)
            require(name not in seen and 0 <= item.size <= MAX_LOGICAL_BYTES)
            seen.add(name)
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
        raise Hold()


def download(output):
    # No proxy/redirect/retry/fallback, credentials or user-selected URL.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(URL, headers={'Accept-Encoding': 'identity'})
    with opener.open(request, timeout=15) as response:
        require(response.status == 200 and response.geturl() == URL)
        require(response.headers.get('Content-Encoding', 'identity') == 'identity')
        length = response.headers.get('Content-Length')
        if length is not None:
            require(length.isascii() and length.isdecimal() and 0 < int(length) <= MAX_ARCHIVE)
        count = 0
        while True:
            data = response.read(min(CHUNK, MAX_ARCHIVE - count + 1))
            if not data:
                break
            count += len(data)
            require(count <= MAX_ARCHIVE)
            require(output.write(data) == len(data))
        require(count > 0 and (length is None or count == int(length)))
    output.flush()


def main():
    try:
        require(sys.argv[1:] == ['--download-and-inspect'])
        require(sys.platform == 'linux' and os.environ.get('GITHUB_ACTIONS') == 'true'
                and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
                and os.environ.get('RUNNER_OS') == 'Linux')
        # New artifact process only: wall time and address-space containment, not
        # guest/operational stop proof. Production observer timers are untouched.
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        def expired(_signum, _frame):
            raise Hold()
        signal.signal(signal.SIGALRM, expired)
        signal.alarm(120)
        receipt = Path(__file__).with_name('J0-PROVIDER-SOURCE.json').read_bytes()
        require(hashlib.sha256(receipt).hexdigest() == SOURCE_RECEIPT_SHA256)
        selection = json.loads(receipt)['selection']
        require(selection['url'] == URL and selection['provider_reported_archive_sha256'] == ARCHIVE_SHA256)
        # Automatically deletes ONLY its new private temporary archive on exit.
        # No extraction directory or persistent prepared rootfs is created.
        with tempfile.TemporaryFile(mode='w+b') as output:
            download(output)
            result = inspect(output, ARCHIVE_SHA256)
        encoded = json.dumps(result, sort_keys=True, ensure_ascii=True, separators=(',', ':'))
        require(len(encoded.encode('ascii')) <= 65536)
        signal.alarm(0)
        print(encoded)
        return 0
    except Exception:
        print('HOLD: artifact preparation incomplete')
        return 2


if __name__ == '__main__':
    sys.exit(main())
