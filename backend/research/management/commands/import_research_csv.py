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
        parser.add_argument("--owner", required=True)
        parser.add_argument("--approved-by", required=True)
        parser.add_argument("--acknowledge-terms", action="store_true")

    def handle(self, *args, **options):
        if not options["acknowledge_terms"]:
            raise CommandError("Review source rights, actions and publication evidence before import.")
        try:
            intake = prepare_csv_intake(
                csv_bytes=_read(options["csv"], 2_000_000),
                metadata=strict_json_loads(_read(options["metadata"], 2_000_000)),
                source_record=strict_json_loads(_read(options["source"], 2_000_000)),
                terms_bytes=_read(options["terms"], 1_000_000),
                availability_bytes=_read(options["availability"], 2_000_000),
                now=timezone.now(),
            )
            users = get_user_model().objects
            owner = users.get(username=options["owner"], is_active=True)
            operator = users.get(username=options["approved_by"], is_active=True, is_staff=True)
            payload = json.loads(json.dumps(intake.dataset.payload, allow_nan=False))
            dataset, created = import_dataset(payload, owner=owner, operator=operator, intake=intake)
            receipt = ResearchIntakeReceipt.objects.get(dataset=dataset, version=intake.version)
        except (OSError, ValueError, get_user_model().DoesNotExist) as error:
            raise CommandError("CSV intake failed. Check source evidence, protocol, rights and active actors.") from error
        self.stdout.write(json.dumps({
            "dataset_id": str(dataset.id), "dataset_version": dataset.version,
            "receipt_id": str(receipt.id), "receipt_version": receipt.version,
            "created": created, "data_kind": intake.dataset.data_kind,
            "independently_verified_source": False,
        }))
