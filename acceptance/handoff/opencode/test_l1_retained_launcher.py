import errno
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from l1_retained_launcher import MAX_EXECUTABLE, verified_image


class ImageControls(unittest.TestCase):
    data = b"\x7fELFfixture bytes, never executed"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "image"
        self.path.write_bytes(self.data)
        self.digest = hashlib.sha256(self.data).hexdigest()

    def test_sealed_image_is_independent_of_replaced_path(self):
        fd = verified_image(self.path, self.digest)
        self.addCleanup(os.close, fd)
        replacement = self.path.with_suffix(".new")
        replacement.write_bytes(b"changed")
        replacement.replace(self.path)
        self.assertEqual(os.read(fd, len(self.data) + 1), self.data)
        with self.assertRaises(OSError) as error:
            os.pwrite(fd, b"x", 0)
        self.assertEqual(error.exception.errno, errno.EPERM)
        with self.assertRaises(OSError):
            os.ftruncate(fd, 0)
        self.assertFalse(os.get_inheritable(fd))

    def test_wrong_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verified_image(self.path, "0" * 64)

    def test_malformed_digest_rejected_before_open(self):
        with patch("os.open", side_effect=AssertionError("unexpected open")):
            with self.assertRaisesRegex(ValueError, "invalid reviewed"):
                verified_image(self.path, "bad")

    def test_non_elf_rejected_even_with_matching_hash(self):
        self.path.write_bytes(b"#!/bin/sh\n")
        with self.assertRaisesRegex(ValueError, "ELF"):
            verified_image(self.path, hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_symlink_rejected(self):
        link = self.path.with_suffix(".link")
        link.symlink_to(self.path)
        with self.assertRaises(OSError) as error:
            verified_image(link, self.digest)
        self.assertEqual(error.exception.errno, errno.ELOOP)

    def test_nonregular_and_oversize_rejected(self):
        fifo = self.path.with_suffix(".fifo")
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, "invalid executable source"):
            verified_image(fifo, self.digest)
        with self.path.open("r+b") as source:
            source.truncate(MAX_EXECUTABLE + 1)
        with self.assertRaisesRegex(ValueError, "invalid executable source"):
            verified_image(self.path, self.digest)


if __name__ == "__main__":
    unittest.main()
