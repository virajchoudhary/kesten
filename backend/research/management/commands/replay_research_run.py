import hashlib
import json
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from research.models import ResearchRun
from research.services import runtime_manifest


def result_hash(result):
    return hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class Command(BaseCommand):
    help = "Recompute a private saved run without overwriting its inputs or result."

    def add_arguments(self, parser):
        parser.add_argument("--run", required=True, type=uuid.UUID)
        parser.add_argument("--owner", required=True)

    def handle(self, *args, **options):
        from research.quant import DatasetError, evaluate, parse_dataset

        try:
            run = ResearchRun.objects.select_related("dataset").get(id=options["run"], owner__username=options["owner"])
            dataset = parse_dataset(run.dataset.payload, now=timezone.now())
            current = runtime_manifest()
            replayed = evaluate(dataset, horizon=run.horizon_sessions)
            checks = {
                "dataset_matches": dataset.version == run.dataset.version,
                "engine_matches": current["engine_source_sha256"] == run.runtime["engine_source_sha256"],
                "dependency_lock_matches": current["dependency_lock_sha256"] == run.runtime["dependency_lock_sha256"],
                "runtime_versions_match": current["python"] == run.runtime["python"] and current["dependencies"] == run.runtime["dependencies"],
                "result_matches": result_hash(replayed) == result_hash(run.result),
            }
        except (ValueError, DatasetError, ResearchRun.DoesNotExist) as error:
            raise CommandError("The private run cannot be replayed under the current data/protocol.") from error
        self.stdout.write(json.dumps({"run_id": str(run.id), "result": "PASS" if all(checks.values()) else "FAIL", **checks, "result_sha256": result_hash(replayed)}))
        if not all(checks.values()):
            raise CommandError("Replay differs. Preserve the original evidence and inspect code, environment and data versions.")
