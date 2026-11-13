from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from accounts.models import AccountInvitation, LoginAttemptState, PasswordResetToken


class Command(BaseCommand):
    help = "Remove expired login-attempt and one-time-token records."

    def handle(self, *args, **options):
        now = timezone.now()
        attempts_deleted, _ = LoginAttemptState.objects.filter(expires_at__lte=now).delete()
        invitations_deleted, _ = AccountInvitation.objects.filter(
            Q(expires_at__lte=now)
            | Q(consumed_at__isnull=False)
            | Q(revoked_at__isnull=False)
        ).delete()
        resets_deleted, _ = PasswordResetToken.objects.filter(
            Q(expires_at__lte=now)
            | Q(consumed_at__isnull=False)
            | Q(revoked_at__isnull=False)
        ).delete()
        self.stdout.write(
            "Removed "
            f"{attempts_deleted} login-attempt record(s), "
            f"{invitations_deleted} invitation(s), and "
            f"{resets_deleted} password reset token(s)."
        )
