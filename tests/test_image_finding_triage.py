import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.security.triage_image_findings import analyze


class ImageFindingTriageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.images = {"images": [{"service": "database", "image_id": "sha256:index"}]}
        self.matches = [self.match("liba", "CVE-1"), self.match("libb", "CVE-1"),
                        self.match("liba", "CVE-2"), self.match("other", "CVE-1", "different-source")]
        self.save()

    def match(self, name, advisory, upstream="source"):
        return {"artifact": {"name": name, "version": "1.0-1+vendor1", "type": "deb", "upstreams": [{"name": upstream}]},
                "vulnerability": {"id": advisory, "severity": "High", "namespace": "debian:distro:debian:13"},
                "matchDetails": [{"type": "exact-indirect-match"}]}

    def save(self, raw_id="sha256:config", digest="repo@sha256:index"):
        report = {"source": {"target": {"imageID": raw_id, "repoDigests": [digest]}}, "matches": self.matches}
        data = json.dumps(report).encode()
        (self.directory / "1-vulnerabilities.json").write_bytes(data)
        scan = {"image_id": "sha256:index", "scan_completed": True, "result": "FAIL",
                "severity_counts": {"High": len(self.matches)},
                "artifacts": [{"path": "1-vulnerabilities.json", "sha256": hashlib.sha256(data).hexdigest()}]}
        (self.directory / "summary.json").write_text(json.dumps({"images": [scan]}))

    def test_split_packages_collapse_but_all_original_matches_survive(self):
        result = analyze(self.directory, self.images, {})
        self.assertEqual(result["counts"]["raw_matches"], 4)
        self.assertEqual(result["counts"]["advisory_ids"], 2)
        self.assertEqual(result["counts"]["source_advisory_pairs"], 3)
        self.assertEqual(len(result["advisories"]), 2)
        self.assertEqual(result["advisories"][0]["raw_count"], 3)
        self.assertEqual(result["advisories"][0]["source_groups"], ["different-source|CVE-1", "source|CVE-1"])
        self.assertEqual(sum(row["raw_count"] for row in result["groups"]), 4)
        self.assertEqual(len({row["raw_id"] for row in result["findings"]}), 4)
        self.assertEqual(result["classification"], "INCOMPLETE")

    def test_assessments_cannot_convert_failed_scans_into_a_release_pass(self):
        assessment = {"disposition": "vendor_backport_present", "exposure": "conditional",
                      "rationale": "Vendor source version contains the patch.", "evidence": ["https://example.test/vendor"]}
        result = analyze(self.directory, self.images, {"source|CVE-1": assessment})
        self.assertEqual(result["release_decision"], "NO_GO")
        self.assertFalse(result["classification_changes_policy"])
        self.assertEqual(result["disposition_raw_counts"], {"vendor_backport_present": 2})

    def test_tampered_report_is_rejected_before_classification(self):
        with (self.directory / "1-vulnerabilities.json").open("a") as stream:
            stream.write(" ")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            analyze(self.directory, self.images, {})

    def test_config_digest_can_differ_from_the_bound_multiarch_index(self):
        self.assertEqual(analyze(self.directory, self.images, {})["images"][0]["scanner_config_id"], "sha256:config")
        self.save(digest="repo@sha256:wrong")
        with self.assertRaisesRegex(ValueError, "image identity"):
            analyze(self.directory, self.images, {})

    def test_unknown_group_and_evidence_free_decisions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "absent"):
            analyze(self.directory, self.images, {"absent|CVE-1": {}})
        for invalid in ({}, None, {"disposition": "fixed"}):
            with self.subTest(assessment=invalid), self.assertRaisesRegex(ValueError, "lacks"):
                analyze(self.directory, self.images, {"source|CVE-1": invalid})

    def test_missing_local_evidence_cannot_count_as_reviewed(self):
        assessment = {"disposition": "fixed", "exposure": "conditional", "rationale": "Check the vendor receipt.",
                      "evidence": ["docs/absent-image-triage-receipt.json"]}
        with self.assertRaisesRegex(ValueError, "evidence"):
            analyze(self.directory, self.images, {"source|CVE-1": assessment})


if __name__ == "__main__":
    unittest.main()
