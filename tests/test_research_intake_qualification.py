import unittest
from copy import deepcopy

from scripts.check_research_intake import verify_restored_result


class RestoredIntakeQualificationTests(unittest.TestCase):
    def setUp(self):
        self.receipt = {
            "receipt_id": "receipt", "receipt_version": "receipt-sha",
            "dataset_id": "dataset", "dataset_version": "dataset-sha",
            "data_kind": "synthetic_fixture",
        }
        self.artifacts = {"csv_content": "csv-sha", "terms_content": "terms-sha", "availability_content": "availability-sha"}
        self.runs = [("run-one", "result-one-sha"), ("run-five", "result-five-sha")]
        self.result = {
            "data_kind": "synthetic_fixture",
            "intake": {**self.receipt, "match": True},
            "artifact_sha256": dict(self.artifacts),
            "runs": [{"run_id": key, "result_sha256": digest, "result": "PASS"} for key, digest in self.runs],
        }

    def verify(self, result):
        verify_restored_result(result, receipt=self.receipt, artifacts=self.artifacts, runs=self.runs)

    def test_exact_restored_receipt_bytes_and_two_runs_pass(self):
        self.verify(self.result)

    def test_missing_duplicate_changed_or_failed_runs_are_rejected(self):
        variants = [[], self.result["runs"][:1], self.result["runs"] * 2]
        for field, value in [("run_id", "different-run"), ("result_sha256", "different-result"), ("result", "FAIL")]:
            rows = deepcopy(self.result["runs"])
            rows[0][field] = value
            variants.append(rows)
        for rows in variants:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.verify({**self.result, "runs": rows})

    def test_changed_receipt_and_archived_bytes_are_rejected(self):
        variants = []
        for key in self.receipt:
            result = deepcopy(self.result)
            result["intake"][key] = "different"
            variants.append(result)
        for key in self.artifacts:
            result = deepcopy(self.result)
            result["artifact_sha256"][key] = "changed-bytes"
            variants.append(result)
        for result in variants:
            with self.subTest(result=result), self.assertRaises(ValueError):
                self.verify(result)
