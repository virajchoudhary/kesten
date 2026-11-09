import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from research.services import DatasetUnavailable, import_dataset
from research.ingestion import strict_json_loads


class Command(BaseCommand):
    help = "Import a frozen daily-close manifest for a private account after operator review."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, type=Path)
        parser.add_argument("--owner", required=True)
        parser.add_argument("--approved-by", required=True)
        parser.add_argument("--acknowledge-terms", action="store_true")

    def handle(self, *args, **options):
        from research.quant import DatasetError

        if not options["acknowledge_terms"]:
            raise CommandError("An operator must review storage, private-research and transfer rights before import.")
        path = options["file"]
        try:
            with path.open("rb") as source:
                payload = strict_json_loads(source.read(2_000_001))
            users = get_user_model().objects
            owner = users.get(username=options["owner"], is_active=True)
            operator = users.get(username=options["approved_by"], is_active=True, is_staff=True)
            dataset, created = import_dataset(payload, owner=owner, operator=operator)
        except (OSError, ValueError, get_user_model().DoesNotExist, DatasetError, DatasetUnavailable) as error:
            raise CommandError("Import failed. Check the manifest, data rights, protocol and active operator/owner.") from error
        self.stdout.write(json.dumps({"dataset_id": str(dataset.id), "version": dataset.version, "created": created, "data_kind": dataset.payload["data_kind"]}))
