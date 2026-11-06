"""Offline B/E READY arbitration model. No child, pidfd or wait operations."""

from dataclasses import dataclass
import os


MS = 1_000_000
READY_CAP = 512


@dataclass(frozen=True)
class ReaderResult:
    binding: tuple
    ready: bool


def release_reader(fd, binding, ready):
    """E closes its owned reader before it can publish its result."""
    os.close(fd)
    return ReaderResult(binding, ready)


class Broker:
    def __init__(self, binding, deadline, clock):
        self.binding = binding
        self.deadline = deadline
        self.clock = clock
        self.reader_released = False
        self.e_reaped = False
        self.reported_ready = False
        self.unknown = False
        self.hold = False
        self.drain_started = False
        self.ready_eof = False

    def accept_reader_result(self, result):
        if (self.reader_released or self.e_reaped or self.hold or self.unknown or
                self.clock() >= self.deadline - 3000 * MS or
                result.binding != self.binding):
            return False
        self.reader_released = True
        self.reported_ready = result.ready
        return True

    def record_e_loss(self):
        self.unknown = True
        self.reported_ready = False

    def record_e_reap(self, binding, observed, consumed):
        """Accept scripted E wait tuples only. The caller owns the oracle."""
        if (self.e_reaped or self.clock() >= self.deadline - 1000 * MS or
                binding != self.binding or observed is None or observed != consumed):
            return False
        self.record_e_loss()
        self.e_reaped = True
        return True

    def record_ambiguous_birth(self):
        self.record_e_loss()
        self.hold = True

    def drain_ready(self, fd):
        """B's one-shot terminal drain. Never interpret bytes as READY."""
        cutoff = self.deadline - 500 * MS
        if (self.drain_started or not (self.reader_released or self.e_reaped) or
                self.clock() >= cutoff or os.get_blocking(fd)):
            return False
        self.drain_started = True
        try:
            discarded = os.read(fd, READY_CAP + 1)
            if len(discarded) > READY_CAP or self.clock() >= cutoff:
                self.hold = True
                return False
            self.ready_eof = not discarded or not os.read(fd, 1)
        except OSError:
            self.hold = True
            return False
        self.ready_eof = self.ready_eof and self.clock() < cutoff
        self.hold = self.hold or not self.ready_eof
        return self.ready_eof

    def finish_at_deadline(self, *, h_reaped, streams_eof):
        if self.clock() >= self.deadline and not (
            self.e_reaped and h_reaped and streams_eof and self.ready_eof
        ):
            self.hold = True
