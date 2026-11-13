from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import AccountInvitation
from accounts.services import revoke_invitation


class Command(BaseCommand):
    help = "Revoke an unused account invitation without deleting its audit record."

    def add_arguments(self, parser):
        parser.add_argument("invitation_id", type=int)
        parser.add_argument(
            "--revoked-by",
            required=True,
            help="Active staff username authorizing this revocation.",
        )

    def handle(self, *args, **options):
        operator = self._staff_operator(options["revoked_by"])
        try:
            invitation = revoke_invitation(
                invitation_id=options["invitation_id"],
                revoked_by=operator,
            )
        except ValueError as error:
            raise CommandError(str(error)) from error
        except AccountInvitation.DoesNotExist as error:
            raise CommandError("The invitation does not exist.") from error

        if invitation.consumed_at is not None:
            self.stdout.write(
                f"Invitation {invitation.pk} was already consumed; no changes made."
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Invitation {invitation.pk} revocation is recorded.")
            )

    @staticmethod
    def _staff_operator(username):
        user_model = get_user_model()
        try:
            operator = user_model._default_manager.get(username=username)
        except user_model.DoesNotExist as error:
            raise CommandError("The revoking operator does not exist.") from error
        if not operator.is_staff or not operator.is_active:
            raise CommandError(
                "The revoking operator must be an active staff account."
            )
        return operator
