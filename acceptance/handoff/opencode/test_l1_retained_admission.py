import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from l1_retained_admission import FD_ROLES, MAX_MANIFEST, MS, inspect
from l1_retained_launcher import verified_image


class AdmissionControls(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.manifest = Path(tmp.name) / "manifest"
        self.image = Path(tmp.name) / "image"
        data = b"\x7fELF review-only fixture bytes"
        self.image.write_bytes(data)
        self.record = {
            "kind": "l1-retained-preflight-v1",
            "image_sha256": hashlib.sha256(data).hexdigest(),
            "fd_roles": FD_ROLES,
            "t0_ns": 0,
            "ta_ns": 1000 * MS,
            "deadline_ns": 9000 * MS,
        }

    def write(self, raw=None):
        if raw is None:
            raw = json.dumps(self.record).encode()
        self.manifest.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def inspect(self, digest, clock=lambda: 2000 * MS):
        return inspect(self.manifest, digest, self.image, clock)

    def test_valid_inputs_still_hold_and_close_image(self):
        with patch("l1_retained_admission.verified_image", wraps=verified_image) as stage:
            with patch("l1_retained_admission.os.close", wraps=os.close) as close:
                self.assertEqual(self.inspect(self.write()), "E_LOSS_STOP_REAP_UNBOUND")
        stage.assert_called_once()
        image_fd = close.call_args.args[0]
        with self.assertRaises(OSError):
            os.fstat(image_fd)

    def test_wrong_manifest_digest_rejects_before_staging(self):
        self.write()
        with patch("l1_retained_admission.verified_image") as stage:
            self.assertEqual(self.inspect("0" * 64), "INPUT_REJECTED")
        stage.assert_not_called()

    def test_image_digest_mismatch_rejects(self):
        self.image.write_bytes(b"\x7fELF changed")
        self.assertEqual(self.inspect(self.write()), "INPUT_REJECTED")

    def test_fd_map_and_extra_fields_reject(self):
        self.record["fd_roles"] = {**FD_ROLES, "H": ["original-h-pidfd"]}
        self.assertEqual(self.inspect(self.write()), "INPUT_REJECTED")
        self.record["fd_roles"] = FD_ROLES
        self.record["cleanup_authorized"] = True
        self.assertEqual(self.inspect(self.write()), "INPUT_REJECTED")

    def test_duplicate_and_oversized_manifest_reject(self):
        for raw in (b'{"kind":1,"kind":2}', b" " * (MAX_MANIFEST + 1)):
            with self.subTest(size=len(raw)):
                self.assertEqual(self.inspect(self.write(raw)), "INPUT_REJECTED")

    def test_invalid_or_widened_deadline_rejects(self):
        for value in (True, 9001 * MS, 5000 * MS):
            with self.subTest(deadline=value):
                self.record["deadline_ns"] = value
                self.assertEqual(self.inspect(self.write()), "INPUT_REJECTED")

    def test_expiry_during_staging_rejects(self):
        clock = iter((2000 * MS, 6000 * MS))
        self.assertEqual(self.inspect(self.write(), lambda: next(clock)), "INPUT_REJECTED")


if __name__ == "__main__":
    unittest.main()
