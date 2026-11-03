"""Offline observer preflight/reservation candidate; no runtime dispatcher.

FixtureIssuer is a trusted test-bootstrap issuer, NOT production authentication.
Only fixture reservations are implemented. No O/S/H spawn, pidfd adoption, state
capture, Facts/planner call, checkpoint append or permission to send G exists.
Host/same-process/same-uid compromise is outside this fixture trust model.
"""
from dataclasses import dataclass
import fcntl
import hashlib
import json
import math
import os
import select
import stat
import time


class Hold(Exception):
    def __init__(self, reason):
        super().__init__()
        self.reason = reason


def require(value, reason='BINDING_UNAVAILABLE'):
    if not value:
        raise Hold(reason)


def _ref(value):
    require(type(value) is str and 0 < len(value) <= 64
            and all(c.isascii() and (c.isalnum() or c in '_-') for c in value))
    return value


def _hash(value):
    require(type(value) is str and len(value) == 64
            and all(c in '0123456789abcdef' for c in value))
    return value


def _number(value):
    require(type(value) in (int, float) and math.isfinite(value))
    return value


@dataclass(frozen=True)
class Binding:
    attempt_ref: str
    nonce: str
    generation: int
    source_sha256: str
    dossier_sha256: str
    scopes: frozenset
    containment: str
    t0: float
    expires: float
    actor_count: int = 4
    cleanup_after_revoke: bool = True
    environment: str = 'owned-offline-fixture'


@dataclass(frozen=True)
class Budget:
    t0: float
    ta: float
    attempt_deadline: float
    capture_deadline: float
    outer_deadline: float

    @classmethod
    def start(cls, t0, now):
        _number(t0); _number(now)
        require(0 <= now-t0 < 45, 'BUDGET_UNAVAILABLE')
        deadline = min(now+20, t0+45)
        require(deadline-now > 3, 'BUDGET_UNAVAILABLE')
        return cls(t0, now, deadline, deadline-3, t0+45)


@dataclass(frozen=True)
class Result:
    state: str
    reason: str
    reservation_consumed: bool
    capture_allowed: bool = False
    authorizes_actions: bool = False
    dev_observed: bool = False


SCOPES = frozenset(('fixture_observer_launch', 'fixture_terminal_cleanup',
                    'fixture_witness_read', 'fixture_physical_state_read',
                    'fixture_shared_read_lock'))


class FixtureIssuer:
    """Trusted fixture bootstrap owns registry, independent claim root and epoch.

    Inputs here must never come from checkpoint/caller JSON. Type/object privacy
    does not authenticate an issuer. There is deliberately no production issuer
    factory, exported capability token, arbitrary callback or dict-to-Facts path.
    The caller owns rootfd and witnessfd; this object duplicates the root handle.
    """
    def __init__(self, rootfd, generation):
        require(type(generation) is int and generation > 0)
        info = os.fstat(rootfd)
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) == 0o700)
        self.rootfd = os.dup(rootfd)
        self.root_identity = info.st_dev, info.st_ino
        self.generation = generation
        self.registry = {}

    def close(self):
        if self.rootfd is not None:
            os.close(self.rootfd)
            self.rootfd = None

    def register(self, binding, witnessfd):
        require(type(binding) is Binding)
        _ref(binding.attempt_ref); _ref(binding.nonce)
        _hash(binding.source_sha256); _hash(binding.dossier_sha256)
        require(binding.attempt_ref not in self.registry)
        info = os.fstat(witnessfd)
        require(stat.S_ISFIFO(info.st_mode)
                and fcntl.fcntl(witnessfd, fcntl.F_GETFL)&os.O_ACCMODE == os.O_RDONLY)
        self.registry[binding.attempt_ref] = (binding, witnessfd, (info.st_dev, info.st_ino), True)

    def revoke(self, ref):
        b, fd, identity, _ = self.registry[_ref(ref)]
        self.registry[ref] = b, fd, identity, False

    def _current(self, ref, expected=None, *, cleanup=False):
        try:
            item = self.registry[_ref(ref)]
        except (KeyError, TypeError):
            raise Hold('AUTHORITY_UNAVAILABLE') from None
        b, fd, pipe_identity, active = item
        require(expected is None or b is expected, 'AUTHORITY_CHANGED')
        require(type(b.generation) is int and b.generation == self.generation,
                'AUTHORITY_CHANGED')
        require(b.environment == 'owned-offline-fixture', 'PRODUCTION_BINDINGS_UNBOUND')
        require(b.containment == 'fixture-owned-cleanup', 'CONTAINMENT_UNBOUND')
        require(type(b.actor_count) is int and b.actor_count == 4, 'RESOURCE_UNBOUND')
        require(type(b.cleanup_after_revoke) is bool and b.cleanup_after_revoke,
                'CLEANUP_UNBOUND')
        require(type(b.scopes) is frozenset and b.scopes == SCOPES, 'AUTHORITY_UNAVAILABLE')
        _number(b.t0); _number(b.expires)
        now = time.monotonic()
        require(b.t0 <= now < b.t0+45 and b.t0 < b.expires <= b.t0+45,
                'BUDGET_UNAVAILABLE')
        if not cleanup:
            require(active is True and now < b.expires, 'AUTHORITY_UNAVAILABLE')
        info = os.fstat(self.rootfd)
        require((info.st_dev, info.st_ino) == self.root_identity
                and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700)
        pipe = os.fstat(fd)
        require(stat.S_ISFIFO(pipe.st_mode) and (pipe.st_dev, pipe.st_ino) == pipe_identity)
        return b, fd, now

    def reserve(self, ref):
        # Validate all fixture launch/cleanup/containment gates before any claim
        # write. No protected DB/evidence read or fork is present in this module.
        b, witnessfd, now = self._current(ref)
        budget = Budget.start(b.t0, now)
        name = hashlib.sha256(b.attempt_ref.encode('ascii')).hexdigest()+'.claim'
        raw = json.dumps({'kind': 'offline-observer-consumed-v1',
                          'generation': b.generation}, separators=(',', ':')).encode()
        claim = None
        created = False
        try:
            claim = os.open(name, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,
                            0o600, dir_fd=self.rootfd)
            created = True
            info = os.fstat(claim)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                    and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600)
            require(os.write(claim, raw) == len(raw), 'CLAIM_UNCONFIRMED')
            os.fsync(claim)
            os.fsync(self.rootfd)
            self._current(ref, b)
            require(time.monotonic() < budget.capture_deadline, 'BUDGET_UNAVAILABLE')
            return Reservation(self, b, budget, witnessfd)
        except FileExistsError:
            raise Hold('ATTEMPT_CONSUMED') from None
        except (OSError, Hold):
            # Existing/partial claims are never deleted, chmodded or retried.
            if created:
                raise Hold('CLAIM_UNCONFIRMED') from None
            raise
        finally:
            if claim is not None:
                os.close(claim)


def _frame(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 512
            and raw.endswith(b'\n') and raw.count(b'\n') == 1, 'WITNESS_REJECTED')
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, 'WITNESS_REJECTED')
            result[key] = value
        return result
    def bad(_):
        raise Hold('WITNESS_REJECTED')
    try:
        result = json.loads(raw.decode('ascii'), object_pairs_hook=pairs,
                            parse_float=bad, parse_constant=bad,
                            parse_int=lambda s: int(s) if len(s) <= 16 else bad(s))
    except (ValueError, UnicodeError, RecursionError):
        raise Hold('WITNESS_REJECTED') from None
    require(type(result) is dict, 'WITNESS_REJECTED')
    return result


class Reservation:
    """Consumed fixture reservation; it is not a runtime launch/cleanup token.

    Reading a framed witness does NOT authenticate S or acquire/ACK an H pidfd.
    Consequently this package has NO positive capture-G or process-signal path.
    """
    def __init__(self, issuer, binding, budget, witnessfd):
        self.issuer, self.binding, self.budget = issuer, binding, budget
        self.witnessfd = os.dup(witnessfd)
        self.used = False

    def close(self):
        if self.witnessfd is not None:
            os.close(self.witnessfd)
            self.witnessfd = None

    def witness(self):
        require(not self.used, 'WITNESS_REJECTED')
        self.used = True  # Unknown/failed frame consumes this read, never retry.
        self.issuer._current(self.binding.attempt_ref, self.binding)
        require(time.monotonic() < self.budget.capture_deadline, 'BUDGET_UNAVAILABLE')
        # Fixed atomic-frame profile: one bounded read, no partial reassembly,
        # poll or wait loop. No caller-selected fd/path or arbitrary JSON input.
        require(bool(select.select([self.witnessfd], [], [], 0)[0]), 'WITNESS_UNAVAILABLE')
        frame = _frame(os.read(self.witnessfd, 513))
        require(set(frame) == {'kind', 'nonce', 'generation', 'role', 'source_sha256'},
                'WITNESS_REJECTED')
        require(frame['kind'] == 'offline-observer-witness-v1'
                and frame['nonce'] == self.binding.nonce
                and type(frame['generation']) is int
                and frame['generation'] == self.binding.generation
                and frame['role'] == 'H'
                and frame['source_sha256'] == self.binding.source_sha256,
                'WITNESS_REJECTED')
        self.issuer._current(self.binding.attempt_ref, self.binding)
        return Result('FIXTURE_WITNESS_PARSED', 'PIDFD_ACK_UNBOUND', True)

    def capture(self):
        # Intentionally unavailable even after a well-formed fixture witness.
        # An accepted source/pidfd/ownership/channel ACK path is still absent.
        raise Hold('PIDFD_ACK_UNBOUND')

    def cleanup_status(self):
        self.issuer._current(self.binding.attempt_ref, self.binding, cleanup=True)
        require(time.monotonic() < self.budget.attempt_deadline, 'BUDGET_UNAVAILABLE')
        return Result('FIXTURE_CLEANUP_ELIGIBILITY', 'OWNERSHIP_UNBOUND', True)
