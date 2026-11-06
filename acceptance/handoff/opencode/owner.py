"""Owned native capture primitives. No native OpenCode method or public CLI.

Only the private admission path in facts.py may use these primitives in the
supported application profile. Direct primitive tests use new synthetic files.
"""
import hashlib
import math
import os
import resource
import signal
import stat
import struct
import subprocess
import time


class Hold(Exception):
    def __init__(self, code='CAPTURE_REJECTED'):
        self.code = code if code in {'CAPTURE_REJECTED','STOP_UNCONFIRMED','BUDGET_EXHAUSTED',
                                    'BINDING_MISMATCH','AUTHORITY_UNAVAILABLE','AUTHORITY_EXPIRED',
                                    'CONTEXT_UNBOUND','VERIFIER_REJECTED','RECONCILIATION_REQUIRED',
                                    'JOB_ID_UNKNOWN','EVIDENCE_MISMATCH'} else 'CAPTURE_REJECTED'
        super().__init__()


def need(value, code='CAPTURE_REJECTED'):
    if not value:
        raise Hold(code)


def identity(info):
    return info.st_dev, info.st_ino


def private_dir(fd):
    s = os.fstat(fd)
    need(stat.S_ISDIR(s.st_mode) and s.st_uid == os.geteuid() and stat.S_IMODE(s.st_mode) == 0o700)
    return identity(s)


def open_file(parent, name, maximum, mode=0o600):
    need(type(name) is str and name not in ('','.','..') and '/' not in name and '\x00' not in name)
    private_dir(parent)
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
    try:
        s = os.fstat(fd)
        need(stat.S_ISREG(s.st_mode) and s.st_uid == os.geteuid() and s.st_nlink == 1
             and stat.S_IMODE(s.st_mode) == mode and 0 < s.st_size <= maximum)
        need(identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) == identity(s))
        return fd
    except BaseException:
        os.close(fd)
        raise


def unchanged(parent, name, fd):
    a, b = os.fstat(fd), os.stat(name, dir_fd=parent, follow_symlinks=False)
    need(stat.S_ISREG(b.st_mode) and identity(a) == identity(b)
         and a.st_uid == b.st_uid == os.geteuid() and a.st_nlink == b.st_nlink == 1
         and stat.S_IMODE(a.st_mode) == stat.S_IMODE(b.st_mode), 'BINDING_MISMATCH')


def read_all(fd, maximum):
    before = os.fstat(fd)
    need(0 < before.st_size <= maximum)
    parts, offset = [], 0
    while offset < before.st_size:
        data = os.pread(fd, min(65536, before.st_size-offset), offset)
        need(data)
        parts.append(data)
        offset += len(data)
    need(os.pread(fd, 1, offset) == b'')
    after = os.fstat(fd)
    need((identity(before), before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
         (identity(after), after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'EVIDENCE_MISMATCH')
    return b''.join(parts)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024,)*2)
    resource.setrlimit(resource.RLIMIT_CORE, (0,0))


def _stop(proc, pidfd, deadline):
    # No backend PID. If pidfd acquisition failed, WNOWAIT must first prove this
    # remains our unreaped direct child; this single-thread owner has no reaper.
    def send(sig):
        try:
            if pidfd is not None:
                signal.pidfd_send_signal(pidfd, sig)
            else:
                try:
                    os.waitid(os.P_PID,proc.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
                except ChildProcessError:
                    raise Hold('STOP_UNCONFIRMED') from None
                os.kill(proc.pid,sig)
        except ProcessLookupError:
            pass
    send(signal.SIGTERM)
    try:
        proc.wait(timeout=max(0.001,min(0.2,deadline-time.monotonic())))
    except subprocess.TimeoutExpired:
        send(signal.SIGKILL)
        try:
            proc.wait(timeout=max(0.001,min(1,deadline-time.monotonic())))
        except subprocess.TimeoutExpired:
            raise Hold('STOP_UNCONFIRMED') from None
    need(proc.returncode is not None, 'STOP_UNCONFIRMED')


def _decode(raw, role):
    need(type(raw) is bytes and len(raw) <= 65536 and raw[:8] == b'OCSNAP1\0')
    need(len(raw) >= 10 and raw[8] == (1 if role == 'jobs' else 2))
    count = 14 if role == 'jobs' else 2
    need(raw[9] == count)
    pos, values = 10, []
    for _ in range(count):
        need(pos < len(raw))
        tag, pos = raw[pos], pos+1
        if tag == 5:
            values.append(None)
        elif tag in (1,2):
            need(pos+8 <= len(raw))
            value = struct.unpack('>q' if tag == 1 else '>d', raw[pos:pos+8])[0]
            need(tag != 2 or math.isfinite(value))
            values.append(value)
            pos += 8
        elif tag == 3:
            need(pos+4 <= len(raw))
            size = struct.unpack('>I',raw[pos:pos+4])[0]
            pos += 4
            need(size <= 8192 and pos+size <= len(raw))
            try:
                value = raw[pos:pos+size].decode('utf-8')
            except UnicodeError:
                raise Hold() from None
            need('\x00' not in value)
            values.append(value)
            pos += size
        else:
            raise Hold()
    need(pos == len(raw))
    return tuple(values)
