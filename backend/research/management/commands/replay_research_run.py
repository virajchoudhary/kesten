import json
import uuid

from django.core.management.base import BaseCommand, CommandError

from research.models import ResearchRun
from research.quant import DatasetError
from research.replay import replay_run


class Command(BaseCommand):
    help = "Recompute a private saved run without overwriting its inputs or result."

    def add_arguments(self, parser):
        parser.add_argument("--run", required=True, type=uuid.UUID)
        parser.add_argument("--owner", required=True)

    def handle(self, *args, **options):
        try:
            run = ResearchRun.objects.select_related("dataset").get(id=options["run"], owner__username=options["owner"])
            receipt = replay_run(run)
        except (ValueError, DatasetError, ResearchRun.DoesNotExist) as error:
            raise CommandError("The private run cannot be replayed under the current data/protocol.") from error
        self.stdout.write(json.dumps(receipt))
        if receipt["result"] != "PASS":
            raise CommandError("Replay differs. Preserve the original evidence and inspect code, environment and data versions.")
