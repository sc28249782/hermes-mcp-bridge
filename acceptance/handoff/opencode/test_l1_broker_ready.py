import os
import unittest
from unittest.mock import patch

from l1_broker_ready import Broker, MS, READY_CAP, ReaderResult, release_reader


class BrokerControls(unittest.TestCase):
    def setUp(self):
        self.now = 1000 * MS
        self.binding = (1, 2, "fixture")
        self.broker = Broker(self.binding, 8000 * MS, lambda: self.now)

    def pipe(self, payload=b"", *, eof=True):
        reader, writer = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
        self.addCleanup(os.close, reader)
        os.write(writer, payload)
        if eof:
            os.close(writer)
        else:
            self.addCleanup(os.close, writer)
        return reader

    def reap_e(self):
        event = (42, 1, 0)
        return self.broker.record_e_reap(self.binding, event, event)

    def test_b_cannot_read_before_handoff(self):
        fd = self.pipe(b"unconsumed")
        self.assertFalse(self.broker.drain_ready(fd))
        self.assertEqual(os.read(fd, 32), b"unconsumed")

    def test_e_closes_before_publishing_result(self):
        fd = self.pipe(b"suffix")
        e_fd = os.dup(fd)
        result = release_reader(e_fd, self.binding, True)
        with self.assertRaises(OSError):
            os.fstat(e_fd)
        self.assertTrue(self.broker.accept_reader_result(result))
        self.assertFalse(self.broker.accept_reader_result(result))
        self.assertTrue(self.broker.drain_ready(fd))
        self.assertTrue(self.broker.reported_ready)
        self.assertFalse(self.broker.drain_ready(fd))

    def test_failed_e_close_cannot_publish(self):
        with patch("l1_broker_ready.os.close", side_effect=OSError):
            with self.assertRaises(OSError):
                release_reader(5, self.binding, True)

    def test_e_loss_rejects_queued_ready_and_drains_suffix_after_exact_reap(self):
        fd = self.pipe(b"suffix")
        e_fd = os.dup(fd)
        self.assertEqual(os.read(e_fd, 2), b"su")
        os.close(e_fd)
        self.broker.record_e_loss()
        self.assertFalse(self.broker.accept_reader_result(ReaderResult(self.binding, True)))
        self.assertFalse(self.broker.drain_ready(fd))
        self.assertTrue(self.reap_e())
        self.assertTrue(self.broker.drain_ready(fd))
        self.assertTrue(self.broker.unknown)
        self.assertFalse(self.broker.reported_ready)

    def test_bad_binding_mismatch_and_late_reap_do_not_handoff(self):
        fd = self.pipe()
        self.assertFalse(self.broker.accept_reader_result(ReaderResult((3,), True)))
        self.assertFalse(self.broker.record_e_reap(self.binding, (42, 1, 0), (42, 1, 1)))
        self.now = 7000 * MS
        self.assertFalse(self.reap_e())
        self.assertFalse(self.broker.drain_ready(fd))

    def test_retained_writer_and_excess_bytes_hold(self):
        for payload, eof in ((b"suffix", False), (b"x" * (READY_CAP + 1), True)):
            with self.subTest(eof=eof):
                self.set_broker()
                self.assertTrue(self.reap_e())
                self.assertFalse(self.broker.drain_ready(self.pipe(payload, eof=eof)))
                self.assertTrue(self.broker.hold)
                self.assertFalse(self.broker.ready_eof)

    def set_broker(self):
        self.broker = Broker(self.binding, 8000 * MS, lambda: self.now)

    def test_ambiguous_birth_stays_hold_even_with_e_eof(self):
        self.broker.record_ambiguous_birth()
        self.assertTrue(self.reap_e())
        self.assertTrue(self.broker.drain_ready(self.pipe()))
        self.assertTrue(self.broker.hold)
        self.assertTrue(self.broker.unknown)

    def test_deadline_without_separate_h_evidence_holds(self):
        self.assertTrue(self.reap_e())
        self.assertTrue(self.broker.drain_ready(self.pipe()))
        self.now = 8000 * MS
        self.broker.finish_at_deadline(h_reaped=False, streams_eof=True)
        self.assertTrue(self.broker.hold)


if __name__ == "__main__":
    unittest.main()
