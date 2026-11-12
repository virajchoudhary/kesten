import hashlib
import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from research.ingestion import prepare_csv_intake
from research.models import ResearchDataset, ResearchIntakeReceipt
from research.quant.dataset import canonical_json
from research.quant.fixtures import make_fixture_payload
from research.services import import_dataset
from research.tests.intake_fixtures import intake_arguments


class DatasetProvenanceTests(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.owner = users.create_user("provenance-owner", is_staff=True)
        self.other = users.create_user("provenance-other")
        self.dataset, _ = import_dataset(make_fixture_payload(), owner=self.owner, operator=self.owner)
        self.path = f"/api/v1/research/datasets/{self.dataset.id}/provenance/"
        self.client.force_login(self.owner)

    def archive(self):
        prepared = prepare_csv_intake(**intake_arguments())
        import_dataset(
            json.loads(json.dumps(prepared.dataset.payload)), owner=self.owner,
            operator=self.owner, intake=prepared,
        )
        return ResearchIntakeReceipt.objects.get(dataset=self.dataset)

    def test_private_metadata_is_readable_before_evaluation_without_archived_receipt(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        evidence = response.json()
        self.assertEqual(evidence["dataset"]["id"], str(self.dataset.id))
        self.assertEqual(evidence["dataset"]["version"], self.dataset.version)
        self.assertEqual(evidence["intake"], {"status": "not_archived"})
        self.assertEqual(evidence["point_in_time_qualification"], "not_independently_verified")
        self.assertFalse(evidence["independently_verified_source"])
        self.assertNotIn("observations", evidence["dataset"])

    def test_matching_receipt_exposes_identities_and_declared_rights_not_source_qualification(self):
        receipt = self.archive()
        before = bytes(receipt.csv_content)
        evidence = self.client.get(self.path).json()
        intake = evidence["intake"]
        self.assertEqual(intake["status"], "verified")
        self.assertEqual(intake["receipt_id"], str(receipt.id))
        self.assertEqual(intake["receipt_version"], receipt.version)
        self.assertEqual(intake["source_attestation"], "operator_attested")
        self.assertFalse(intake["declared_permissions"]["redistribution"])
        self.assertFalse(evidence["independently_verified_source"])
        self.assertEqual(intake["artifact_sha256"]["csv"], hashlib.sha256(before).hexdigest())
        for field in ("csv_content", "terms_content", "availability_content", "observations"):
            self.assertNotIn(field, intake)
        receipt.refresh_from_db()
        self.assertEqual(bytes(receipt.csv_content), before)

    def test_failed_integrity_does_not_disclose_corrupt_source_fields_or_rewrite_evidence(self):
        receipt = self.archive()
        source = receipt.evidence
        source["source"]["source_url"] = "https://private-user:private-secret@example.invalid/source"
        ResearchIntakeReceipt.objects.filter(pk=receipt.pk).update(evidence=source)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["intake"], {"status": "failed", "receipt_id": str(receipt.id)})
        self.assertNotIn("private-secret", response.content.decode())
        receipt.refresh_from_db()
        self.assertEqual(receipt.evidence, source)

    def test_owner_lookup_is_not_limited_to_the_newest_hundred_datasets(self):
        rows = []
        for index in range(100):
            payload = json.loads(json.dumps(self.dataset.payload))
            payload["name"] = f"SYNTHETIC: newer dataset {index}"
            rows.append(ResearchDataset(
                owner=self.owner, approved_by=self.owner, payload=payload,
                version=hashlib.sha256(canonical_json(payload).encode()).hexdigest(),
            ))
        ResearchDataset.objects.bulk_create(rows)
        listed = self.client.get("/api/v1/research/datasets/").json()["items"]
        self.assertNotIn(str(self.dataset.id), [row["id"] for row in listed])
        self.assertEqual(self.client.get(self.path).json()["dataset"]["version"], self.dataset.version)

    def test_other_account_and_anonymous_cannot_inspect_provenance(self):
        self.archive()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.path).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.path).status_code, 403)

    def test_dataset_identity_mismatch_is_an_integrity_failure(self):
        payload = json.loads(json.dumps(self.dataset.payload))
        payload["observations"][0]["close"] += 1
        ResearchDataset.objects.filter(pk=self.dataset.pk).update(payload=payload)
        self.assertEqual(self.client.get(self.path).status_code, 503)
