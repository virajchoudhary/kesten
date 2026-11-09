"""Safety boundaries for the isolated production rehearsal."""

import json
import subprocess
import tempfile
import unittest
from io import BytesIO
from unittest.mock import patch

from scripts.ops.qualify_production import (
    ROOT,
    Rehearsal,
    immutable_image,
    new_directory,
)


class ProductionQualificationTests(unittest.TestCase):
    def test_windows_bootstrap_refuses_missing_acl_preparation_before_writing(self):
        rehearsal = self.rehearsal()
        with patch("scripts.ops.prepare_local_tls.protect_directory", None, create=True), patch("scripts.ops.qualify_production.os.name", "nt"), patch.object(rehearsal, "refuse_existing_project") as inventory, self.assertRaisesRegex(RuntimeError, "ACL-protected"):
            rehearsal.prepare()
        inventory.assert_not_called()

    def rehearsal(self):
        return Rehearsal(ROOT / ".local/nonexistent-qualification-test", "sha256:" + "a" * 64, "sha256:" + "b" * 64, 8452, 8092, "openssl")

    def test_retained_volume_and_unavailable_inventory_are_refused(self):
        rehearsal = self.rehearsal()
        with patch("scripts.ops.qualify_production.command", side_effect=[
            subprocess.CompletedProcess([], 0, stdout=""),
            subprocess.CompletedProcess([], 0, stdout=rehearsal.project + "_database\n"),
        ]), self.assertRaises(ValueError):
            rehearsal.refuse_existing_project()
        with patch("scripts.ops.qualify_production.command", return_value=subprocess.CompletedProcess([], 1, stdout="")), self.assertRaises(RuntimeError):
            rehearsal.refuse_existing_project()

    def test_http_copy_cannot_satisfy_restore_marker_check(self):
        rehearsal = self.rehearsal()
        with patch.object(rehearsal, "container_probe"), patch.object(rehearsal, "login", return_value=(None, "csrf")), patch.object(rehearsal, "expect", return_value=({"items": []}, {})), self.assertRaisesRegex(RuntimeError, "restore-only marker"):
            rehearsal.verify_restored_http()

    def test_existing_or_external_directories_are_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as directory, self.assertRaises(ValueError):
            new_directory(directory)
        for directory in (ROOT, ROOT / ".local", ROOT.parent / "qualification-test"):
            with self.subTest(directory=directory), self.assertRaises(ValueError):
                new_directory(directory)

    def test_mutable_image_is_refused(self):
        for image in ("api:latest", "api:qualified", "sha256:abc", "api@sha256:" + "a" * 63):
            with self.subTest(image=image), self.assertRaises(ValueError):
                immutable_image(image)
        self.assertEqual(immutable_image("sha256:" + "a" * 64), "sha256:" + "a" * 64)

    def test_untrusted_origin_is_preserved_for_negative_csrf_test(self):
        class Response(BytesIO):
            status = 403

            def __init__(self, value):
                super().__init__(value)
                self.headers = {"Content-Type": "application/json"}

        class Opener:
            request = None

            def open(self, request, timeout):
                self.request = request
                return Response(json.dumps({"detail": "CSRF denied"}).encode())

        opener = Opener()
        with patch("scripts.ops.qualify_production.secrets.token_hex", return_value="test"):
            rehearsal = Rehearsal(ROOT / ".local/nonexistent-qualification-test", "sha256:" + "a" * 64, "sha256:" + "b" * 64, 8452, 8092, "openssl")
        status, _, _ = rehearsal.request("/api/v1/watchlist/", method="POST", body={}, csrf="test-token", opener=opener, headers={"Origin": "https://untrusted.invalid"})
        self.assertEqual(status, 403)
        self.assertEqual(opener.request.get_header("Origin"), "https://untrusted.invalid")


if __name__ == "__main__":
    unittest.main()
