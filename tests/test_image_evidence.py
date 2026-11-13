import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ops.image_evidence import ROOT, collect


class ImageEvidenceTests(unittest.TestCase):
    def scan_with_ignored_findings(self, ignored):
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as temporary:
            output = Path(temporary) / "evidence"
            identity = "sha256:" + "a" * 64

            def command(arguments, environment=None):
                args = list(map(str, arguments))
                stdout = "{}"
                if args[:3] == ["docker", "image", "inspect"]:
                    stdout = json.dumps([{"Id": identity, "Config": {}, "RepoDigests": []}])
                elif args[:2] == ["git", "rev-parse"]:
                    stdout = "b" * 40
                elif args[:2] == ["git", "status"]:
                    stdout = ""
                elif args[0] == "syft" and args[1].startswith("docker:"):
                    Path(args[-1].split("=", 1)[1]).write_text("{}")
                elif args[0] == "grype" and args[1].startswith("docker:"):
                    Path(args[-1]).write_text(json.dumps({"matches": [], "ignoredMatches": ignored}))
                return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

            with patch("scripts.ops.image_evidence.command", side_effect=command), contextlib.redirect_stdout(io.StringIO()):
                exit_code = collect([identity], output, "syft", "grype", Path(temporary))
            return exit_code, json.loads((output / "summary.json").read_text())

    def test_clean_scan_still_requires_release_review(self):
        exit_code, summary = self.scan_with_ignored_findings([])
        self.assertEqual(exit_code, 1)
        self.assertEqual(summary["scan_policy"], "PASS")
        self.assertEqual(summary["result"], "REVIEW_REQUIRED")
        self.assertEqual(summary["suppressions"], [])

    def test_suppressed_critical_finding_cannot_look_like_a_clean_scan(self):
        ignored = [{"vulnerability": {"id": "CVE-EXAMPLE", "severity": "Critical"}}]
        _, summary = self.scan_with_ignored_findings(ignored)
        self.assertEqual(summary["scan_policy"], "FAIL")
        self.assertEqual(summary["images"][0]["ignored_match_count"], 1)
        self.assertTrue(summary["suppressions"])


if __name__ == "__main__":
    unittest.main()
