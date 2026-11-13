import json
import uuid
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase

from research.models import ResearchDataset, ResearchRun
from research.services import DatasetUnavailable, import_dataset, run_evaluation


class ResearchAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from research.quant.fixtures import make_fixture_payload

        users = get_user_model().objects
        cls.owner = users.create_user("research-owner", password="private-research-password-822!")
        cls.other = users.create_user("research-other", password="private-research-password-823!")
        cls.operator = users.create_user("research-operator", is_staff=True)
        cls.payload = make_fixture_payload()
        cls.dataset, _ = import_dataset(cls.payload, owner=cls.owner, operator=cls.operator)
        cls.other_dataset, _ = import_dataset(cls.payload, owner=cls.other, operator=cls.operator)

    def setUp(self):
        cache.clear()
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
        self.csrf = self.client.get("/api/v1/session/").json()["csrf_token"]

    def request_payload(self, **changes):
        return {"dataset_id": str(self.dataset.id), "horizon_sessions": 1, "idempotency_key": str(uuid.uuid4()), **changes}

    def post(self, payload, **kwargs):
        return self.client.post("/api/v1/research/runs/", payload, content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, **kwargs)

    def test_anonymous_cannot_read_or_create_private_research(self):
        self.client.logout()
        for path in ("datasets/", "runs/", f"runs/{uuid.uuid4()}/"):
            self.assertEqual(self.client.get("/api/v1/research/" + path).status_code, 403)
        self.assertEqual(self.post(self.request_payload()).status_code, 403)

    def test_dataset_list_is_private_and_contains_no_raw_observations(self):
        response = self.client.get("/api/v1/research/datasets/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json()["items"]], [str(self.dataset.id)])
        self.assertNotIn("observations", response.content.decode())
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_create_requires_csrf_and_foreign_dataset_is_not_found(self):
        payload = self.request_payload()
        response = self.client.post("/api/v1/research/runs/", payload, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.post(self.request_payload(dataset_id=str(self.other_dataset.id))).status_code, 404)
        self.assertFalse(ResearchRun.objects.exists())

    def test_horizon_types_bounds_unknown_fields_and_client_bars_are_rejected(self):
        for value in (True, "1", 2, -1, 1.0, None):
            with self.subTest(value=value):
                cache.clear()
                self.assertEqual(self.post(self.request_payload(horizon_sessions=value)).status_code, 400)
        for field in ("observations", "owner", "data_kind", "model"):
            cache.clear()
            self.assertEqual(self.post(self.request_payload(**{field: "untrusted"})).status_code, 400)
        self.assertFalse(ResearchRun.objects.exists())

    def test_real_evaluation_is_persisted_and_replay_does_not_recompute(self):
        payload = self.request_payload()
        response = self.post(payload)
        self.assertEqual(response.status_code, 201, response.content)
        run = response.json()
        self.assertEqual(run["status"], "succeeded")
        self.assertEqual(run["result"]["evidence_kind"], "synthetic_pipeline_check")
        self.assertFalse(run["result"]["empirical_performance_established"])
        self.assertEqual(run["result"]["dataset_version"], self.dataset.version)
        self.assertEqual(len(run["runtime"]["engine_source_sha256"]), 64)
        self.assertEqual(len(run["runtime"]["dependency_lock_sha256"]), 64)
        with patch("research.quant.evaluate", side_effect=AssertionError("Replay must use stored results")):
            repeated = self.post(payload)
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(repeated.json(), run)
        self.assertEqual(self.client.get(f'/api/v1/research/runs/{run["id"]}/').json(), run)
        self.assertEqual(self.client.get("/api/v1/research/runs/").json()["items"], [run])
        self.assertEqual(ResearchRun.objects.count(), 1)

    def test_request_key_conflict_preserves_original_run(self):
        payload = self.request_payload()
        original = self.post(payload).json()
        response = self.post({**payload, "horizon_sessions": 5})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "request_key_conflict")
        self.assertEqual(ResearchRun.objects.get().result, original["result"])

    def test_saved_results_do_not_cross_users(self):
        run = self.post(self.request_payload()).json()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/api/v1/research/runs/{run["id"]}/').status_code, 404)
        self.assertEqual(self.client.get("/api/v1/research/runs/").json()["items"], [])

    def test_corrupted_snapshot_fails_without_partial_run(self):
        payload = json.loads(json.dumps(self.dataset.payload))
        payload["observations"][-1]["close"] *= 1.5
        ResearchDataset.objects.filter(pk=self.dataset.pk).update(payload=payload)
        response = self.post(self.request_payload())
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "dataset_unavailable")
        self.assertFalse(ResearchRun.objects.exists())

    def test_interrupted_calculation_can_retry_without_partial_result(self):
        payload = self.request_payload()
        with patch("research.quant.evaluate", side_effect=DatasetUnavailable("controlled failure")):
            self.assertEqual(self.post(payload).status_code, 503)
        self.assertFalse(ResearchRun.objects.exists())
        self.assertEqual(self.post(payload).status_code, 201)
        self.assertEqual(ResearchRun.objects.count(), 1)

    def test_same_bytes_import_idempotently_and_nonstaff_cannot_attest_history(self):
        dataset, created = import_dataset(self.payload, owner=self.owner, operator=self.operator)
        self.assertFalse(created)
        self.assertEqual(dataset.id, self.dataset.id)
        with self.assertRaises(DatasetUnavailable):
            import_dataset(self.payload, owner=self.owner, operator=self.other)

    def test_inactive_owner_or_operator_is_rejected(self):
        self.other.is_active = False
        self.other.save(update_fields=["is_active"])
        with self.assertRaises(DatasetUnavailable):
            import_dataset(self.payload, owner=self.other, operator=self.operator)
        self.operator.is_active = False
        self.operator.save(update_fields=["is_active"])
        with self.assertRaises(DatasetUnavailable):
            import_dataset(self.payload, owner=self.owner, operator=self.operator)

    def test_fixture_seed_is_explicit_idempotent_and_disabled_outside_development(self):
        output = StringIO()
        with self.settings(DEBUG=True):
            call_command("seed_research_fixture", owner=self.owner.username, stdout=output)
        self.assertIn('"empirical_performance_established": false', output.getvalue())
        self.assertEqual(ResearchDataset.objects.filter(owner=self.owner).count(), 1)
        with self.settings(DEBUG=False), self.assertRaises(CommandError):
            call_command("seed_research_fixture", owner=self.owner.username, stdout=StringIO())

    def test_import_requires_explicit_terms_acknowledgement(self):
        with self.assertRaises(CommandError):
            call_command("import_research_dataset", file="not-read.json", owner=self.owner.username, approved_by=self.operator.username)

    def test_service_cannot_evaluate_another_owners_dataset(self):
        with self.assertRaises(DatasetUnavailable):
            run_evaluation(owner=self.other, dataset=self.dataset, horizon=1, idempotency_key=uuid.uuid4())

    def test_saved_run_replays_without_writing_and_detects_changed_runtime(self):
        run, _ = run_evaluation(owner=self.owner, dataset=self.dataset, horizon=5, idempotency_key=uuid.uuid4())
        saved_result = run.result
        output = StringIO()
        call_command("replay_research_run", run=str(run.id), owner=self.owner.username, stdout=output)
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt["result"], "PASS")
        self.assertTrue(receipt["result_matches"])
        run.refresh_from_db()
        self.assertEqual(run.result, saved_result)

        with self.assertRaises(CommandError):
            call_command("replay_research_run", run=str(run.id), owner=self.other.username, stdout=StringIO())
        run.runtime = {**run.runtime, "engine_source_sha256": "0" * 64}
        run.save(update_fields=["runtime"])
        output = StringIO()
        with self.assertRaises(CommandError):
            call_command("replay_research_run", run=str(run.id), owner=self.owner.username, stdout=output)
        self.assertFalse(json.loads(output.getvalue())["engine_matches"])
        run.refresh_from_db()
        self.assertEqual(run.result, saved_result)

    def test_running_engine_keeps_its_original_runtime_fingerprint(self):
        first, _ = run_evaluation(owner=self.owner, dataset=self.dataset, horizon=1, idempotency_key=uuid.uuid4())
        with patch("research.services.Path.read_bytes", return_value=b"subsequent checkout edit"):
            second, _ = run_evaluation(owner=self.owner, dataset=self.dataset, horizon=5, idempotency_key=uuid.uuid4())
        self.assertEqual(second.runtime, first.runtime)

    def test_research_creation_accepts_only_its_documented_json_encoding(self):
        response = self.client.post(
            "/api/v1/research/runs/", self.request_payload(), HTTP_X_CSRFTOKEN=self.csrf
        )
        self.assertEqual(response.status_code, 415)
        self.assertFalse(ResearchRun.objects.exists())
