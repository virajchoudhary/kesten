import os
import secrets
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a local development analyst without modifying an existing user's password."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="analyst")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Local-user bootstrap requires the explicit development settings profile.")
        user_model = get_user_model()
        username = options["username"]
        if user_model.objects.filter(username=username).exists():
            self.stdout.write(f"Local user {username} already exists. Password unchanged.")
            return
        password = os.environ.get("CADRISYN_LOCAL_PASSWORD") or secrets.token_urlsafe(24)
        user_model.objects.create_user(username=username, password=password)
        credentials = Path(settings.BASE_DIR).parent / ".local" / "credentials.json"
        credentials.parent.mkdir(parents=True, exist_ok=True)
        import json

        credentials.write_text(json.dumps({"username": username, "password": password}), encoding="utf-8")
        if os.name != "nt":
            credentials.chmod(0o600)
        self.stdout.write(f"Created local user {username}. Credentials saved to the ignored .local/credentials.json file.")
