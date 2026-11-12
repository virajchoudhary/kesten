import json
import tempfile
import uuid
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from research.ingestion import prepare_csv_intake
from research.intake_replay import verify_intake
from research.models import ResearchDataset, ResearchIntakeReceipt
from research.replay import replay_run
from research.services import DatasetUnavailable, import_dataset, run_evaluation
from research.tests.intake_fixtures import intake_arguments


class IntakeStorageTests(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.owner = users.create_user("intake-owner")
        self.other = users.create_user("intake-other")
        self.operator = users.create_user("intake-operator", is_staff=True)
        self.arguments = intake_arguments()
        self.prepared = prepare_csv_intake(**self.arguments)
        self.payload = json.loads(json.dumps(self.prepared.dataset.payload))

    def import_prepared(self, **overrides):
        options = {"owner": self.owner, "operator": self.operator, "intake": self.prepared}
        options.update(overrides)
        return import_dataset(self.payload, **options)

    def test_exact_artifacts_repeat_acquisitions_and_baseline_replay(self):
        dataset, created = self.import_prepared()
        receipt = ResearchIntakeReceipt.objects.get(dataset=dataset)
        self.assertTrue(created)
        self.assertEqual(bytes(receipt.csv_content), self.arguments["csv_bytes"])
        self.assertEqual(bytes(receipt.terms_content), self.arguments["terms_bytes"])
        self.assertEqual(bytes(receipt.availability_content), self.arguments["availability_bytes"])
        self.assertEqual(receipt.approved_by_id, self.operator.pk)
        self.assertTrue(verify_intake(receipt, owner=self.owner)["match"])
        self.assertFalse(self.import_prepared()[1])
        self.assertEqual(ResearchIntakeReceipt.objects.count(), 1)

        self.arguments["source_record"]["acquired_at"] = (
            datetime.fromisoformat(self.arguments["source_record"]["acquired_at"]) + timedelta(seconds=1)
        ).isoformat()
        self.arguments["now"] += timedelta(seconds=1)
        repeated = prepare_csv_intake(**self.arguments)
        self.assertEqual(repeated.dataset.version, dataset.version)
        self.assertNotEqual(repeated.version, receipt.version)
        self.import_prepared(intake=repeated)
        self.assertEqual(ResearchDataset.objects.count(), 1)
        self.assertEqual(ResearchIntakeReceipt.objects.count(), 2)
        receipt.refresh_from_db()
        self.assertEqual(receipt.version, self.prepared.version)
        for horizon in [1, 5]:
            run, _ = run_evaluation(owner=self.owner, dataset=dataset, horizon=horizon, idempotency_key=uuid.uuid4())
            self.assertEqual(replay_run(run)["result"], "PASS")
            self.assertFalse(run.result["empirical_performance_established"])

    def test_historical_declarations_without_source_receipt_are_rejected(self):
        self.payload.update(
            data_kind="historical", name="Declared archive", source_id="declared-source",
            license_reference="Claimed permission", availability_evidence="Claimed publication archive",
        )
        with self.assertRaises(DatasetUnavailable):
            import_dataset(self.payload, owner=self.owner, operator=self.operator)
        self.assertEqual(ResearchDataset.objects.count(), 0)
        self.assertEqual(ResearchIntakeReceipt.objects.count(), 0)

    def test_mismatched_source_and_unauthorized_operator_leave_no_rows(self):
        changed = json.loads(json.dumps(self.payload))
        changed["observations"][10]["close"] += 1
        with self.assertRaises(DatasetUnavailable):
            import_dataset(changed, owner=self.owner, operator=self.operator, intake=self.prepared)
        with self.assertRaises(DatasetUnavailable):
            self.import_prepared(operator=self.other)
        self.assertEqual(ResearchDataset.objects.count(), 0)
        self.assertEqual(ResearchIntakeReceipt.objects.count(), 0)

    def test_private_receipt_isolation_and_tamper_detection(self):
        dataset, _ = self.import_prepared()
        receipt = ResearchIntakeReceipt.objects.get(dataset=dataset)
        with self.assertRaises(DatasetUnavailable):
            verify_intake(receipt, owner=self.other)
        with self.assertRaises(CommandError):
            call_command("verify_research_intake", receipt=receipt.id, owner=self.other.username, stdout=StringIO())
        self.client.force_login(self.owner)
        response = self.client.get("/api/v1/research/datasets/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        for key in ["csv_content", "terms_content", "availability_content", "intake_receipts"]:
            self.assertNotIn(key, response.content.decode())

        ResearchIntakeReceipt.objects.filter(pk=receipt.pk).update(csv_content=b"corrupt archive")
        receipt.refresh_from_db()
        with self.assertRaises(DatasetUnavailable):
            verify_intake(receipt, owner=self.owner)
        with self.assertRaises(DatasetUnavailable):
            self.import_prepared()
        receipt.refresh_from_db()
        self.assertEqual(bytes(receipt.csv_content), b"corrupt archive")

    def test_csv_command_and_duplicate_json_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = {
                "csv": self.arguments["csv_bytes"], "terms": self.arguments["terms_bytes"],
                "availability": self.arguments["availability_bytes"],
                "metadata": json.dumps(self.arguments["metadata"]).encode(),
                "source": json.dumps(self.arguments["source_record"]).encode(),
            }
            paths = {}
            for key, content in inputs.items():
                paths[key] = root / key
                paths[key].write_bytes(content)
            output = StringIO()
            call_command("import_research_csv", **paths, owner=self.owner.username, approved_by=self.operator.username, acknowledge_terms=True, stdout=output)
            report = json.loads(output.getvalue())
            self.assertEqual(report["dataset_version"], self.prepared.dataset.version)
            self.assertFalse(report["independently_verified_source"])
            verify_output = StringIO()
            call_command("verify_research_intake", receipt=uuid.UUID(report["receipt_id"]), owner=self.owner.username, stdout=verify_output)
            self.assertTrue(json.loads(verify_output.getvalue())["match"])

            for token, replacement in [
                ('"schema_version": 1', '"schema_version": 1, "schema_version": 1'),
                ('"close":', '"close": 1, "close":'),
            ]:
                path = root / "duplicate.json"
                path.write_text(json.dumps(self.payload).replace(token, replacement, 1), encoding="utf-8")
                with self.assertRaises(CommandError):
                    call_command("import_research_dataset", file=path, owner=self.owner.username, approved_by=self.operator.username, acknowledge_terms=True, stdout=StringIO())
            self.assertEqual(ResearchIntakeReceipt.objects.count(), 1)
