"""S24 candidate protocol. Source review only; correlation is not authentication."""
import hashlib
import json
import os
from pathlib import Path
import re
import select
import stat
import time
import types

FRAME_LIMIT = 1024
HOST_LIMIT = 2048
LOG_LIMIT = 65536
FALSE_FLAGS = {"r1_complete": False, "r2_authorized": False,
               "authenticated": False, "complete_writer_coverage": False,
               "host_identity_proved": False, "scope_granted": False}


class Hold(Exception):
    pass


def require(value):
    if not value:
        raise Hold()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def reject(*_):
    raise Hold()


def loads(raw):
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject)


def encode(value, maximum=FRAME_LIMIT):
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    require(len(raw) <= maximum)
    return raw


def correlation(binding, challenge):
    require(all(type(s) is str and re.fullmatch("[a-f0-9]{64}", s) for s in (binding, challenge)))


def load_source(name, digest, anchor):
    path = Path(anchor).absolute().with_name(name)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid in (0, os.getuid())
                and info.st_nlink == 1 and not info.st_mode & 0o022 and info.st_size <= 131072)
        raw = bytearray()
        while True:
            chunk = os.read(fd, 131073 - len(raw))
            if not chunk:
                break
            raw.extend(chunk)
            require(len(raw) <= 131072)
        after = os.fstat(fd)
        fields = ('st_dev', 'st_ino', 'st_uid', 'st_gid', 'st_mode', 'st_nlink',
                  'st_size', 'st_mtime_ns', 'st_ctime_ns')
        require(hashlib.sha256(raw).hexdigest() == digest
                and all(getattr(after, field) == getattr(info, field) for field in fields))
    finally:
        os.close(fd)
    module = types.ModuleType(name.removesuffix('.py'))
    module.__file__ = str(path)
    exec(compile(bytes(raw), str(path), 'exec'), module.__dict__)
    return module


def identity(pid):
    require(int(Path('/proc/self/stat').read_text().split(' ', 1)[0]) == os.getpid())
    root = Path('/proc') / str(pid)
    raw = (root / 'stat').read_text()
    require(int(raw.split(' ', 1)[0]) == pid)
    fields = raw.rsplit(')', 1)[1].split()
    return {'pid': pid, 'start_ticks': int(fields[19]), 'ppid': int(fields[1]),
            'uid': root.stat().st_uid, 'exe': os.readlink(root / 'exe'),
            'argv': [os.fsdecode(a) for a in (root / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')]}


def fingerprint(value):
    return hashlib.sha256(encode(value, 65536)).hexdigest()


def live(fd):
    return not select.select([fd], [], [], 0)[0]


class Marker:
    def __init__(self, fd, binding, challenge):
        correlation(binding, challenge)
        require(type(fd) is int and fd >= 3 and stat.S_ISFIFO(os.fstat(fd).st_mode)
                and os.get_blocking(fd) is False
                and os.fpathconf(fd, 'PC_PIPE_BUF') >= FRAME_LIMIT)
        self.fd, self.binding, self.challenge = fd, binding, challenge
        self.phase = 'new'

    def emit(self, kind, worker, ok):
        correlation(self.binding, self.challenge)
        require(kind in ('worker_bound', 'collect_entered', 'collect_leaving')
                and type(ok) is bool and type(worker['pid']) is int)
        raw = encode({'kind': kind, 'binding': self.binding, 'challenge': self.challenge,
                      'pid': worker['pid'], 'identity': fingerprint(worker), 'ok': ok})
        require(os.write(self.fd, raw) == len(raw))  # One atomic nonblocking write; no retry.

    def boundary(self, kind, ok):
        try:
            require((self.phase, kind) in (('new', 'collect_entered'), ('inside', 'collect_leaving')))
            self.emit(kind, identity(os.getpid()), ok)
            self.phase = 'inside' if kind == 'collect_entered' else 'left'
        except BaseException:
            os._exit(72)  # Fatal: never return outside collect with a missing boundary.


class Lines:
    def __init__(self, maximum, total):
        self.maximum, self.total = maximum, total
        self.pending = bytearray()
        self.used = 0
        self.eof = False

    def feed(self, data):
        require(type(data) is bytes and not self.eof)
        if not data:
            self.eof = True
            require(not self.pending)
            return []
        self.used += len(data)
        require(self.used <= self.total)
        self.pending.extend(data)
        result = []
        while b'\n' in self.pending:
            pos = self.pending.index(10)
            require(0 < pos + 1 <= self.maximum)
            result.append(loads(bytes(self.pending[:pos])))
            del self.pending[:pos + 1]
        require(len(self.pending) < self.maximum)
        return result


class Window:
    def __init__(self, binding, challenge):
        correlation(binding, challenge)
        self.binding, self.challenge = binding, challenge
        self.phase = 'new'
        self.worker = None
        self.opened = self.confirmed = self.held = False

    def hold(self):
        self.held = True
        raise Hold()

    def event(self, value):
        try:
            require(type(value) is dict and set(value) == {'kind', 'binding', 'challenge', 'pid', 'identity', 'ok'})
            require(value['binding'] == self.binding and value['challenge'] == self.challenge
                    and type(value['pid']) is int and value['pid'] > 0
                    and type(value['identity']) is str and re.fullmatch('[a-f0-9]{64}', value['identity'])
                    and type(value['ok']) is bool)
            pair = (value['pid'], value['identity'])
            kind = value['kind']
            require((self.phase, kind) in (('new', 'worker_bound'), ('bound', 'collect_entered'),
                                          ('inside', 'collect_leaving')))
            if self.phase == 'new':
                self.worker = pair
            require(pair == self.worker and value['ok'])
            self.phase = {'worker_bound': 'bound', 'collect_entered': 'inside', 'collect_leaving': 'left'}[kind]
        except BaseException:
            self.hold()

    def pre(self, is_live, partial=False, eof=False):
        if not (not self.held and not self.opened and self.phase == 'inside'
                and is_live is True and partial is False and eof is False):
            self.hold()
        self.opened = True

    def post(self, value, is_live, partial=False, eof=False):
        try:
            require(type(value) is dict and set(value) == {'kind', 'binding', 'challenge'}
                    and value == {'kind': 'check_window_after', 'binding': self.binding, 'challenge': self.challenge})
            require(not self.held and self.opened and not self.confirmed and self.phase == 'inside'
                    and is_live is True and partial is False and eof is False)
            self.confirmed = True
        except BaseException:
            self.hold()

    def finish(self):
        require(not self.held and self.confirmed and self.phase == 'left')


class PrivateLog:
    def __init__(self, path):
        # The future launcher must bind a canonical private parent. This function checks
        # every ancestor without following links and rejects a permissive immediate parent.
        path = Path(path)
        require(path.is_absolute() and str(path) == os.path.normpath(str(path)))
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in path.parent.parts[1:]:
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = nxt
            info = os.fstat(fd)
            require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700)
            self.fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                              0o600, dir_fd=fd)
            try:
                require(stat.S_IMODE(os.fstat(self.fd).st_mode) == 0o600)
                os.fsync(self.fd)
                os.fsync(fd)
            except BaseException:
                os.close(self.fd)
                raise
        finally:
            os.close(fd)
        self.used = 0

    def append(self, value):
        raw = encode(value, HOST_LIMIT)
        require(self.used + len(raw) <= LOG_LIMIT)
        view = memoryview(raw)
        while view:
            n = os.write(self.fd, view)
            require(n > 0)
            self.used += n
            view = view[n:]
        os.fsync(self.fd)

    def close(self):
        os.close(self.fd)
