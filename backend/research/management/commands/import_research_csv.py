import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from research.ingestion import prepare_csv_intake, strict_json_loads
from research.models import ResearchIntakeReceipt
from research.services import import_dataset


def _read(path, limit):
    with path.open("rb") as source:
        return source.read(limit + 1)


class Command(BaseCommand):
    help = "Import a private canonical daily CSV with archived operator-attested source evidence."

    def add_arguments(self, parser):
        for name in ("csv", "metadata", "source", "terms", "availability"):
            parser.add_argument(f"--{name}", required=True, type=Path)
        parser.add_argument("--owner")
        parser.add_argument("--approved-by")
        parser.add_argument("--acknowledge-terms", action="store_true")
        parser.add_argument("--dry-run", action="store_true", help="Validate the evidence package without database access or import.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if not dry_run and not options["acknowledge_terms"]:
            raise CommandError("Review source rights, actions and publication evidence before import.")
        if not dry_run and (not options["owner"] or not options["approved_by"]):
            raise CommandError("Import requires --owner and --approved-by.")
        try:
            intake = prepare_csv_intake(
                csv_bytes=_read(options["csv"], 2_000_000),
                metadata=strict_json_loads(_read(options["metadata"], 2_000_000)),
                source_record=strict_json_loads(_read(options["source"], 2_000_000)),
                terms_bytes=_read(options["terms"], 1_000_000),
                availability_bytes=_read(options["availability"], 2_000_000),
                now=timezone.now(),
            )
            if dry_run:
                evidence = json.loads(intake.receipt_json)
                self.stdout.write(json.dumps({
                    "validation_only": True, "imported": False, "empirical_evaluation": False,
                    "dataset_version": intake.dataset.version, "receipt_version": intake.version,
                    "data_kind": intake.dataset.data_kind,
                    "observation_count": evidence["observation_count"],
                    "first_session": evidence["first_session"], "last_session": evidence["last_session"],
                    "source_attestation": evidence["source_attestation"],
                    "independently_verified_source": False,
                    "source_id": evidence["source"]["source_id"],
                    "acquired_at": evidence["source"]["acquired_at"],
                    "artifact_sha256": {
                        key: evidence["source"][f"{key}_sha256"]
                        for key in ("csv", "terms", "availability")
                    },
                    "declared_permissions": evidence["source"]["permissions"],
                    "limitation": evidence["limitation"],
                }))
                return
            users = get_user_model().objects
            owner = users.get(username=options["owner"], is_active=True)
            operator = users.get(username=options["approved_by"], is_active=True, is_staff=True)
            payload = json.loads(json.dumps(intake.dataset.payload, allow_nan=False))
            dataset, created = import_dataset(payload, owner=owner, operator=operator, intake=intake)
            receipt = ResearchIntakeReceipt.objects.get(dataset=dataset, version=intake.version)
        except (OSError, ValueError, get_user_model().DoesNotExist) as error:
            if dry_run:
                raise CommandError(f"CSV preflight failed: {error}") from error
            raise CommandError("CSV intake failed. Check source evidence, protocol, rights and active actors.") from error
        self.stdout.write(json.dumps({
            "dataset_id": str(dataset.id), "dataset_version": dataset.version,
            "receipt_id": str(receipt.id), "receipt_version": receipt.version,
            "created": created, "data_kind": intake.dataset.data_kind,
            "independently_verified_source": False,
        }))
