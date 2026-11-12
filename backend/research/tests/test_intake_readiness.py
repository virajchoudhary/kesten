"""Schema-only fixtures prove admission rules; no market evidence is used."""

import hashlib
import json
import tempfile
import uuid
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from research.ingestion import prepare_csv_intake
from research.models import ResearchDataset, ResearchIntakeReceipt, ResearchRun
from research.quant import parse_dataset
from research.quant.dataset import canonical_json
from research.quant.fixtures import make_fixture_payload
from research.replay import replay_run, result_hash
from research.services import import_dataset
from research.tests.intake_fixtures import intake_arguments


class IntakePreflightTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        arguments = intake_arguments()
        contents = {
            "csv": arguments["csv_bytes"], "terms": arguments["terms_bytes"],
            "availability": arguments["availability_bytes"],
            "metadata": json.dumps(arguments["metadata"]).encode(),
            "source": json.dumps(arguments["source_record"]).encode(),
        }
        self.paths = {}
        for name, content in contents.items():
            self.paths[name] = Path(directory.name) / name
            self.paths[name].write_bytes(content)

    def test_dry_run_validates_without_actors_or_database_and_does_not_certify_source(self):
        output = StringIO()
        call_command("import_research_csv", **self.paths, dry_run=True, stdout=output)
        report = json.loads(output.getvalue())
        self.assertTrue(report["validation_only"])
        self.assertFalse(report["imported"])
        self.assertFalse(report["empirical_evaluation"])
        self.assertFalse(report["independently_verified_source"])
        self.assertEqual(report["source_attestation"], "operator_attested")
        self.assertEqual(report["data_kind"], "synthetic_fixture")
        self.assertEqual(report["dataset_version"], "9203cba1c9d58f65505fc7c05120669be1829719c7d033d58ab8155387a47a94")
        self.assertNotIn("dataset_id", report)

    def test_preflight_rejects_missing_rights_and_tampered_bytes_without_database(self):
        source = json.loads(self.paths["source"].read_bytes())
        source["permissions"]["backup"] = False
        self.paths["source"].write_text(json.dumps(source), encoding="utf-8")
        with self.assertRaisesRegex(CommandError, "four internal uses"):
            call_command("import_research_csv", **self.paths, dry_run=True, stdout=StringIO())
        source["permissions"]["backup"] = True
        self.paths["source"].write_text(json.dumps(source), encoding="utf-8")
        self.paths["terms"].write_bytes(b"altered terms")
        with self.assertRaisesRegex(CommandError, "terms_sha256"):
            call_command("import_research_csv", **self.paths, dry_run=True, stdout=StringIO())

    def test_write_mode_still_requires_acknowledgement_and_both_actors(self):
        with self.assertRaisesRegex(CommandError, "Review source rights"):
            call_command("import_research_csv", **self.paths, stdout=StringIO())
        with self.assertRaisesRegex(CommandError, "owner and --approved-by"):
            call_command("import_research_csv", **self.paths, acknowledge_terms=True, stdout=StringIO())


class HistoricalEvaluationReadinessTests(TestCase):
    def setUp(self):
        cache.clear()
        users = get_user_model().objects
        self.owner = users.create_user("readiness-owner")
        self.operator = users.create_user("readiness-operator", is_staff=True)
        self.payload = make_fixture_payload()
        self.payload.update(
            data_kind="historical",
            name="Schema-only admission test",
            source_id="admission-test-source",
            license_reference="Test declaration, not a market-data grant",
            availability_evidence="Test declaration, not a publication archive",
        )
        parsed = parse_dataset(self.payload, now=timezone.now())
        self.dataset = ResearchDataset.objects.create(
            owner=self.owner, approved_by=self.operator,
            version=parsed.version, payload=json.loads(json.dumps(parsed.payload)),
        )
        self.client.force_login(self.owner)
        self.csrf = self.client.get("/api/v1/session/").json()["csrf_token"]

    def request_run(self, *, horizon=1, key=None):
        return self.client.post(
            "/api/v1/research/runs/",
            {"dataset_id": str(self.dataset.id), "horizon_sessions": horizon,
             "idempotency_key": str(key or uuid.uuid4())},
            content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf,
        )

    def attach_schema_only_receipt(self, *, acquisition_offset=0):
        arguments = intake_arguments()
        arguments["metadata"] = {key: value for key, value in self.dataset.payload.items() if key != "observations"}
        source = arguments["source_record"]
        source["source_id"] = self.payload["source_id"]
        source["acquired_at"] = (datetime.fromisoformat(source["acquired_at"]) + timedelta(seconds=acquisition_offset)).isoformat()
        arguments["now"] += timedelta(seconds=acquisition_offset)
        availability = json.loads(arguments["availability_bytes"])
        availability["source_id"] = source["source_id"]
        arguments["availability_bytes"] = canonical_json(availability).encode()
        source["availability_sha256"] = hashlib.sha256(arguments["availability_bytes"]).hexdigest()
        intake = prepare_csv_intake(**arguments)
        dataset, created = import_dataset(
            self.dataset.payload, owner=self.owner, operator=self.operator, intake=intake,
        )
        self.assertFalse(created)
        self.assertEqual(dataset.id, self.dataset.id)
        return ResearchIntakeReceipt.objects.get(dataset=dataset, version=intake.version)

    def test_historical_dataset_without_source_receipt_cannot_start_new_run(self):
        response = self.request_run()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "dataset_unavailable")
        self.assertFalse(ResearchRun.objects.exists())

    def test_corrupt_archive_blocks_new_runs_but_preserves_saved_results_and_replay(self):
        receipt = self.attach_schema_only_receipt()
        key = uuid.uuid4()
        response = self.request_run(key=key)
        self.assertEqual(response.status_code, 201)
        run = ResearchRun.objects.get()
        original_hash = result_hash(run.result)
        self.assertFalse(run.result["empirical_performance_established"])
        ResearchIntakeReceipt.objects.filter(pk=receipt.pk).update(terms_content=b"corrupt archive")

        for horizon in (1, 5):
            with self.subTest(horizon=horizon):
                self.assertEqual(self.request_run(horizon=horizon).status_code, 503)
        self.assertEqual(self.request_run(key=key).status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/research/runs/{run.id}/").status_code, 200)
        run.refresh_from_db()
        self.assertEqual(result_hash(run.result), original_hash)
        self.assertEqual(replay_run(run)["result"], "PASS")
        self.assertEqual(ResearchRun.objects.count(), 1)
        receipt.refresh_from_db()
        self.assertEqual(bytes(receipt.terms_content), b"corrupt archive")

    def test_invalid_newest_receipt_is_not_hidden_by_an_older_valid_acquisition(self):
        self.attach_schema_only_receipt()
        latest = self.attach_schema_only_receipt(acquisition_offset=1)
        ResearchIntakeReceipt.objects.filter(pk=latest.pk).update(availability_content=b"corrupt archive")
        self.assertEqual(self.request_run().status_code, 503)
        self.assertFalse(ResearchRun.objects.exists())
