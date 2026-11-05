"""Offline L1 contract controls. Run this file directly with Python unittest.

The model receives scripted time, wait results and readiness evidence. It does
not launch children, arm timers, issue a wait syscall or run the bridge.
"""

from dataclasses import dataclass, replace
import os
import unittest


MS = 1_000_000


def observe(deadline, birth_pid, expected_exit, clock, sleep_until, wait):
    """Return a matching consume receipt or None. EOF is a separate fact."""
    cutoff = deadline - 1000 * MS

    def checked_wait(*, consume):
        if clock() >= cutoff:
            raise TimeoutError
        event = wait(birth_pid, consume=consume)
        if clock() >= cutoff:
            raise TimeoutError
        return event

    try:
        for index in range(16):
            slot = deadline - (3000 - 125 * index) * MS
            if clock() < slot:
                sleep_until(slot)
            now = clock()
            if now < slot:
                return None
            if now >= slot + 25 * MS:
                continue
            event = checked_wait(consume=False)
            if event is None:
                continue
            if event != (birth_pid, *expected_exit):
                return None
            if checked_wait(consume=False) != event:
                return None
            if checked_wait(consume=True) != event:
                return None
            return event
    except OSError:
        return None
    return None


@dataclass(frozen=True)
class Readiness:
    timer_clock: str
    target: int
    interval: int
    remaining: int
    before: int
    after: int
    signal_ready: bool
    source_bound: bool
    ready_matches_once: bool
    custody_intact: bool
    live: bool


def admit_close(fd, evidence, deadline, clock, close):
    """Test seam for the proposed close callsite, with scripted evidence."""
    target = deadline - 2000 * MS
    if evidence is None:
        return False
    if not (
        evidence.timer_clock == "MONOTONIC"
        and evidence.target == target
        and evidence.interval == 0
        and evidence.remaining > 0
        and 0 <= evidence.after - evidence.before <= 20 * MS
        and evidence.before + evidence.remaining
        <= target <= evidence.after + evidence.remaining
        and evidence.signal_ready
        and evidence.source_bound
        and evidence.ready_matches_once
        and evidence.custody_intact
        and evidence.live
        and evidence.after <= clock() < deadline - 3000 * MS
    ):
        return False
    close(fd)
    return True


class ScheduleControls(unittest.TestCase):
    deadline = 8000 * MS
    pid = 73  # Scripted correlation only.
    event = (pid, 1, 0)

    def run_schedule(self, script, *, wake_delay=0, delays=()):
        now = 0
        calls = []
        replies = iter(script)

        def sleep_until(slot):
            nonlocal now
            now = slot + wake_delay

        def wait(pid, *, consume):
            nonlocal now
            calls.append((now, pid, consume))
            if len(calls) <= len(delays):
                now += delays[len(calls) - 1]
            reply = next(replies)
            if isinstance(reply, OSError):
                raise reply
            return reply

        result = observe(
            self.deadline, self.pid, self.event[1:], lambda: now, sleep_until, wait
        )
        return result, calls

    def test_last_slot_can_consume_at_call_18(self):
        receipt, calls = self.run_schedule([None] * 15 + [self.event] * 3)
        self.assertEqual(receipt, self.event)
        self.assertEqual(len(calls), 18)
        self.assertEqual([t for t, _, _ in calls[:16]],
                         [self.deadline - (3000 - 125 * i) * MS for i in range(16)])
        self.assertTrue(all(pid == self.pid for _, pid, _ in calls))
        self.assertEqual([consume for _, _, consume in calls], [False] * 17 + [True])

    def test_no_event_uses_16_probes(self):
        receipt, calls = self.run_schedule([None] * 16)
        self.assertIsNone(receipt)
        self.assertEqual(len(calls), 16)
        self.assertFalse(any(consume for _, _, consume in calls))

    def test_expired_windows_do_not_burst(self):
        self.assertEqual(self.run_schedule([], wake_delay=25 * MS), (None, []))

    def test_late_probe_skips_elapsed_slots(self):
        receipt, calls = self.run_schedule(
            [None, self.event, self.event, self.event], delays=[260 * MS]
        )
        self.assertEqual(receipt, self.event)
        self.assertEqual(calls[1][0] - calls[0][0], 260 * MS)
        self.assertEqual(len(calls), 4)

    def test_errors_and_mismatches_do_not_retry(self):
        for script in (
            [InterruptedError()], [ChildProcessError()],
            [(99, 1, 0)], [(self.pid, 1, 2)],
            [self.event, None], [self.event, (self.pid, 1, 2)],
        ):
            with self.subTest(script=script):
                receipt, calls = self.run_schedule(script)
                self.assertIsNone(receipt)
                self.assertEqual(len(calls), len(script))
                self.assertFalse(any(consume for _, _, consume in calls))

    def test_mismatched_consume_is_not_a_receipt(self):
        receipt, calls = self.run_schedule([self.event, self.event, None])
        self.assertIsNone(receipt)
        self.assertEqual([consume for _, _, consume in calls], [False, False, True])

    def test_confirmation_completing_at_cutoff_prevents_consume(self):
        receipt, calls = self.run_schedule(
            [self.event, self.event], delays=[0, 2000 * MS]
        )
        self.assertIsNone(receipt)
        self.assertEqual([consume for _, _, consume in calls], [False, False])

    def test_late_consume_is_recorded_once_without_receipt(self):
        receipt, calls = self.run_schedule(
            [self.event] * 3, delays=[0, 0, 2000 * MS]
        )
        self.assertIsNone(receipt)
        self.assertEqual([consume for _, _, consume in calls], [False, False, True])


class PreCloseControls(unittest.TestCase):
    deadline = 8000 * MS
    ready = Readiness("MONOTONIC", 6000 * MS, 0, 2000 * MS, 3999 * MS,
                      4001 * MS, True, True, True, True, True)

    def assert_rejected(self, evidence, now=4500 * MS):
        # A real, owned pidfd stands in for H's handle. It targets this test
        # process and is never used for signalling, waiting or child proof.
        fd = os.pidfd_open(os.getpid())
        close_calls = []

        def counted_close(target):
            close_calls.append(target)
            if target == fd:
                os.close(fd)

        try:
            self.assertFalse(
                admit_close(fd, evidence, self.deadline, lambda: now, counted_close)
            )
            self.assertEqual(close_calls, [])
            os.fstat(fd)
        finally:
            if fd not in close_calls:
                os.close(fd)

    def test_missing_timer_evidence(self):
        self.assert_rejected(None)

    def test_invalid_timer_evidence(self):
        for changes in (
            {"timer_clock": "REALTIME"}, {"target": 6001 * MS},
            {"interval": MS}, {"remaining": 0}, {"remaining": 1900 * MS},
            {"after": 4020 * MS}, {"after": 3998 * MS},
        ):
            with self.subTest(changes=changes):
                self.assert_rejected(replace(self.ready, **changes))

    def test_signal_readiness_rejects(self):
        self.assert_rejected(replace(self.ready, signal_ready=False))

    def test_source_or_ready_rejects(self):
        self.assert_rejected(replace(self.ready, source_bound=False))
        self.assert_rejected(replace(self.ready, ready_matches_once=False))

    def test_custody_liveness_and_deadline_reject(self):
        self.assert_rejected(replace(self.ready, custody_intact=False))
        self.assert_rejected(replace(self.ready, live=False))
        self.assert_rejected(self.ready, now=self.deadline - 3000 * MS)
        self.assert_rejected(self.ready, now=self.ready.after - 1)

    def test_valid_evidence_reaches_only_a_mock_close(self):
        calls = []
        self.assertTrue(
            admit_close(19, self.ready, self.deadline, lambda: 4500 * MS, calls.append)
        )
        self.assertEqual(calls, [19])


if __name__ == "__main__":
    unittest.main()
