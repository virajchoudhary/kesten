import importlib.util
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("workspace_migration", ROOT / "scripts/migrate_workspace.py")
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


class WorkspaceMigrationTests(unittest.TestCase):
    def test_private_research_datasets_and_completed_results_are_preserved(self):
        rows = [
            {"model": "research.researchdataset", "pk": "dataset-1", "fields": {"version": "immutable", "payload": {"data_kind": "synthetic_fixture"}}},
            {"model": "research.researchrun", "pk": "run-1", "fields": {"result": {"empirical_performance_established": False}, "dataset": "dataset-1"}},
        ]
        transferred, _ = migration.transferable_fixture(json.dumps(rows))
        self.assertEqual(json.loads(transferred), rows)
        self.assertIn("research", migration.MODELS)

    def test_source_snapshot_is_consistent_and_handles_are_closed(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as directory:
            source = Path(directory) / "source.sqlite3"
            target = Path(directory) / "snapshot.sqlite3"
            with closing(sqlite3.connect(source)) as db:
                db.execute("CREATE TABLE retained (value TEXT)")
                db.execute("INSERT INTO retained VALUES ('original')")
                db.commit()
            migration.snapshot_sqlite(source, target)
            target.rename(Path(directory) / "moved.sqlite3")
            source.rename(Path(directory) / "original.sqlite3")
            with closing(sqlite3.connect(Path(directory) / "moved.sqlite3")) as db:
                self.assertEqual(db.execute("SELECT value FROM retained").fetchone(), ("original",))
    def test_personal_market_observations_are_not_transferred(self):
        rows = [
            {"model": "auth.user", "fields": {"username": "analyst"}},
            {"model": "workspace.marketsnapshot", "pk": "demo", "fields": {"data_mode": "demo"}},
            {"model": "workspace.marketsnapshot", "pk": "personal", "fields": {"data_mode": "market", "payload": {"private_observations": [101.0]}}},
        ]
        selected, excluded = migration.transferable_fixture(json.dumps(rows))
        self.assertEqual(json.loads(selected), rows[:2])
        self.assertEqual(excluded["restricted_snapshots"], 1)
        self.assertNotIn("private_observations", selected)

    def test_unused_account_bearer_tokens_do_not_cross_environments(self):
        rows = [
            {"model": "accounts.accountinvitation", "fields": {"token_digest": "pending-invitation", "consumed_at": None, "revoked_at": None}},
            {"model": "accounts.passwordresettoken", "fields": {"token_digest": "pending-reset", "consumed_at": None, "revoked_at": None}},
            {"model": "accounts.accountinvitation", "fields": {"token_digest": "revoked-history", "revoked_at": "2026-11-06T00:00:00Z"}},
            {"model": "accounts.passwordresettoken", "fields": {"token_digest": "consumed-history", "consumed_at": "2026-11-06T00:00:00Z"}},
            {"model": "accounts.accountsecuritystate", "fields": {"session_epoch": 4}},
        ]
        selected, excluded = migration.transferable_fixture(json.dumps(rows))
        self.assertEqual(json.loads(selected), rows[2:])
        self.assertEqual(excluded["unused_account_tokens"], 2)
        self.assertNotIn("pending-invitation", selected)
        self.assertNotIn("pending-reset", selected)
    def test_original_research_database_is_not_a_migration_source(self):
        with self.assertRaisesRegex(ValueError, "original research database"):
            migration.source_path(ROOT / "backend/db.sqlite3")

    def test_missing_source_is_not_created(self):
        (ROOT / ".local").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as directory:
            path = Path(directory) / "missing.sqlite3"
            with self.assertRaises(ValueError):
                migration.source_path(path)
            self.assertFalse(path.exists())

    def test_fixture_verification_is_order_independent_but_detects_data_changes(self):
        rows = [{"model": "auth.user", "fields": {"username": "a"}}, {"model": "workspace.watchlistentry", "pk": 3, "fields": {"instrument_id": "xnas-aapl"}}]
        self.assertEqual(migration.canonical_fixture(json.dumps(rows)), migration.canonical_fixture(json.dumps(rows[::-1])))
        changed = [{**rows[0], "fields": {"username": "b"}}, rows[1]]
        self.assertNotEqual(migration.canonical_fixture(json.dumps(rows)), migration.canonical_fixture(json.dumps(changed)))


if __name__ == "__main__":
    unittest.main()
