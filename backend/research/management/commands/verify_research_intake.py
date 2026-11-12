import json
import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from research.intake_replay import verify_intake
from research.models import ResearchIntakeReceipt


class Command(BaseCommand):
    help = "Verify retained source bytes and normalization without overwriting the saved receipt."

    def add_arguments(self, parser):
        parser.add_argument("--receipt", required=True, type=uuid.UUID)
        parser.add_argument("--owner", required=True)

    def handle(self, *args, **options):
        try:
            owner = get_user_model().objects.get(username=options["owner"], is_active=True)
            receipt = ResearchIntakeReceipt.objects.select_related("dataset").get(
                pk=options["receipt"], dataset__owner=owner,
            )
            result = verify_intake(receipt, owner=owner)
        except (ValueError, ResearchIntakeReceipt.DoesNotExist, get_user_model().DoesNotExist) as error:
            raise CommandError("Intake verification failed or the receipt is unavailable.") from error
        self.stdout.write(json.dumps(result))
