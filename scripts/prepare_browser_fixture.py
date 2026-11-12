"""Create disposable lifecycle fixtures only in the isolated local workspace."""

import argparse
import io
import json
import os
import secrets
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configured-preview', action='store_true')
    parser.add_argument('--research-owner')
    args = parser.parse_args()
    if args.configured_preview:
        if os.environ.get('CADRISYN_PREVIEW_PROFILE') != 'true':
            parser.error('Configured-database fixtures require the explicit isolated preview marker.')
    else:
        from dev import development_environment
        os.environ.update(development_environment())
    sys.path.insert(0, str(ROOT / "backend"))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quantvision.settings')
    import django

    django.setup()
    from accounts.services import issue_password_reset
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    if not settings.DEBUG:
        parser.error('Disposable browser accounts are forbidden outside development.')
    if args.configured_preview and (settings.DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql' or settings.DATABASES['default']['NAME'] != 'cadrisyn'):
        parser.error('Configured fixtures require the isolated cadrisyn PostgreSQL preview database.')
    (ROOT / '.local').mkdir(exist_ok=True)
    call_command("migrate", interactive=False, verbosity=0)
    if not args.configured_preview:
        call_command("create_local_user", stdout=io.StringIO())
    credentials = ROOT / ".local/credentials.json"
    owner_name = args.research_owner
    if owner_name is None and credentials.is_file():
        owner_name = json.loads(credentials.read_text(encoding="utf-8"))["username"]
    if owner_name:
        call_command("seed_research_fixture", owner=owner_name, stdout=io.StringIO())
    suffix = uuid.uuid4().hex[:12]
    users = get_user_model().objects
    operator = users.create_user("e2e_operator_" + suffix, is_staff=True)
    invitation = io.StringIO()
    call_command("issue_invitation", username="e2e_invited_" + suffix, issued_by=operator.username, base_url="http://127.0.0.1:3000", stdout=invitation, no_color=True)
    initial_password = secrets.token_urlsafe(32)
    reset_user = users.create_user("e2e_reset_" + suffix, password=initial_password)
    isolation_password = secrets.token_urlsafe(32)
    isolation_user = users.create_user("e2e_isolation_" + suffix, password=isolation_password)
    _, token = issue_password_reset(user=reset_user, issued_by=operator)
    files = {
        "account-e2e-invitation.txt": invitation.getvalue(),
        "account-e2e-reset.json": json.dumps({"username": reset_user.username, "initial_password": initial_password, "token": token}),
        "research-e2e-isolation.json": json.dumps({"username": isolation_user.username, "password": isolation_password}),
    }
    for name, contents in files.items():
        path = ROOT / ".local" / name
        path.write_text(contents, encoding="utf-8")
        if os.name != "nt":
            path.chmod(0o600)
    print("Prepared disposable local browser accounts. One-use secrets remain in ignored .local files.")


if __name__ == "__main__":
    main()
