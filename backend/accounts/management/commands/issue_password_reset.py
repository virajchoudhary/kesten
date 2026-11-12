from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.services import issue_password_reset


class Command(BaseCommand):
    help = "Issue a single-use password reset token and print its private token once."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--issued-by", required=True, help="Existing staff username for the audit record.")
        parser.add_argument("--expires-in-hours", type=int, default=1)
        parser.add_argument("--base-url", required=True, help="Public application origin, for example https://app.example.com.")

    def handle(self, *args, **options):
        base_url = self._base_url(options["base_url"])
        operator = self._staff_operator(options["issued_by"])
        hours = options["expires_in_hours"]
        if not 1 <= hours <= 24:
            raise CommandError("--expires-in-hours must be between 1 and 24.")

        try:
            user = get_user_model()._default_manager.get(username=options["username"])
        except get_user_model().DoesNotExist as error:
            raise CommandError("The requested account does not exist.") from error

        try:
            reset, token = issue_password_reset(
                user=user,
                issued_by=operator,
                expires_in=timedelta(hours=hours),
            )
        except ValueError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                "Password reset issued. The fragment URL contains a one-time secret; keep it private."
            )
        )
        self.stdout.write(f"Open once: {base_url}/account/reset/#token={token}")
        self.stdout.write(
            f"API endpoint: POST {base_url}/api/v1/account/password-reset/confirm/"
        )
        self.stdout.write(f"Expires at (UTC): {reset.expires_at.isoformat()}")

    @staticmethod
    def _staff_operator(username):
        user_model = get_user_model()
        try:
            operator = user_model._default_manager.get(username=username)
        except user_model.DoesNotExist as error:
            raise CommandError("The issuing operator does not exist.") from error
        if not operator.is_staff or not operator.is_active:
            raise CommandError("The issuing operator must be an active staff account.")
        return operator

    @staticmethod
    def _base_url(value):
        parsed = urlsplit(value)
        local_http = settings.DEBUG and parsed.scheme == "http" and parsed.hostname in {
            "localhost",
            "127.0.0.1",
            "::1",
        }
        if (
            not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or (parsed.scheme != "https" and not local_http)
        ):
            raise CommandError(
                "--base-url must use HTTPS (HTTP is allowed only for a debug loopback host)."
            )
        return value.rstrip("/")
