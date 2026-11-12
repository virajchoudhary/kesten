import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from research.services import import_dataset


class Command(BaseCommand):
    help = "Explicitly install a synthetic pipeline fixture for one development account."

    def add_arguments(self, parser):
        parser.add_argument("--owner", required=True)

    def handle(self, *args, **options):
        from research.quant.fixtures import make_fixture_payload

        if not settings.DEBUG:
            raise CommandError("Synthetic fixture bootstrap requires development settings.")
        try:
            owner = get_user_model().objects.get(username=options["owner"], is_active=True)
        except get_user_model().DoesNotExist as error:
            raise CommandError("The active development owner does not exist.") from error
        dataset, created = import_dataset(make_fixture_payload(), owner=owner, operator=owner, synthetic_bootstrap=True)
        self.stdout.write(json.dumps({"dataset_id": str(dataset.id), "version": dataset.version, "created": created, "data_kind": "synthetic_fixture", "empirical_performance_established": False}))
