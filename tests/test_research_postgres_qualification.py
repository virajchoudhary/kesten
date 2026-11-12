import unittest
from copy import deepcopy

from scripts.qualify_research_postgres import compare_snapshots, verify_runtime_privileges


class PostgresQualificationTests(unittest.TestCase):
    def test_runtime_rejects_database_create_or_another_writable_schema(self):
        for permission in ("create_schema", "writable_schema", "temporary", "owns_objects", "role_membership"):
            with self.subTest(permission=permission), self.assertRaises(ValueError):
                verify_runtime_privileges("cadrisyn", {permission: True})

    def test_runtime_accepts_only_constrained_role(self):
        verify_runtime_privileges("cadrisyn", {"create_schema": False, "writable_schema": False})
        with self.assertRaises(ValueError):
            verify_runtime_privileges("cadrisyn_migrator", {"create_schema": False})

    def setUp(self):
        self.snapshot = {
            "qualification_schema_version": 2,
            "data_kind": "synthetic_fixture", "empirical_evaluation": False,
            "tables": {"research_run": {"rows": 2, "sha256": "table-hash"}},
            "intakes": [{"receipt_id": "receipt", "artifact_sha256": {"csv": "raw-hash"}}],
            "replays": [{"horizon_sessions": horizon, "result": "PASS", "run_id": str(horizon)} for horizon in (1, 5)],
        }

    def test_exact_snapshot_passes(self):
        compare_snapshots(self.snapshot, deepcopy(self.snapshot))

    def test_changed_tables_evidence_or_replay_are_rejected(self):
        for key, value in [("tables", {}), ("intakes", []), ("replays", []), ("data_kind", "historical")]:
            actual = {**self.snapshot, key: value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                compare_snapshots(self.snapshot, actual)

    def test_matching_but_empty_incomplete_or_failed_proof_is_rejected(self):
        for key, value in [
            ("tables", {}), ("intakes", []), ("replays", []),
            ("replays", [{"horizon_sessions": 1, "result": "PASS"}] * 2),
            ("replays", [{"horizon_sessions": 1, "result": "FAIL"}, {"horizon_sessions": 5, "result": "PASS"}]),
            ("empirical_evaluation", True),
            ("qualification_schema_version", 1),
        ]:
            invalid = {**self.snapshot, key: value}
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                compare_snapshots(invalid, invalid)
