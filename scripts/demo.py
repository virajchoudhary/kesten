"""Explicitly prepare a private synthetic account, watchlist and baseline evaluations, then run Kerquant."""

import argparse
import atexit
import io
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = {"schema_version": 1, "purpose": "kerquant-portfolio-demo"}


def demo_environment(directory, *, api_port=8000, web_port=3000):
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / ".local") or directory == ROOT / ".local":
        raise ValueError("The demo directory must be a dedicated folder inside repository .local.")
    marker = directory / "demo-workspace.json"
    if directory.exists():
        if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")) != MARKER:
            raise ValueError("Refusing to use a directory that is not an existing Kerquant demo workspace.")
    else:
        directory.mkdir(parents=True)
        sys.path.insert(0, str(ROOT))
        from scripts.ops.prepare_local_tls import protect_directory

        protect_directory(directory)
        with marker.open("x", encoding="utf-8") as output:
            json.dump(MARKER, output)
    secret_file = directory / "django-secret"
    if not secret_file.exists():
        with secret_file.open("x", encoding="utf-8") as output:
            output.write(secrets.token_urlsafe(64))
    environment = os.environ.copy()
    for name in ("DJANGO_SECRET_KEY_FILE", "DATABASE_URL_FILE", "DJANGO_CACHE_URL_FILE"):
        environment.pop(name, None)
    environment.update({
        "DJANGO_DEBUG": "true",
        "CADRISYN_RELEASE_PROFILE": "development",
        "CADRISYN_WEB_RELEASE_PROFILE": "development",
        "DJANGO_SECRET_KEY": secret_file.read_text(encoding="utf-8").strip(),
        "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1,[::1]",
        "DJANGO_CSRF_TRUSTED_ORIGINS": f"http://localhost:{web_port},http://127.0.0.1:{web_port}",
        "DJANGO_CORS_ALLOWED_ORIGINS": "",
        "DJANGO_SECURE_SSL_REDIRECT": "false",
        "DJANGO_TRUST_X_FORWARDED_PROTO": "false",
        "CADRISYN_DB_PATH": str(directory / "workspace.sqlite3"),
        "DATABASE_URL": "",
        "DJANGO_CACHE_URL": "",
        "CADRISYN_MARKET_DATA_ENABLED": "false",
        "CADRISYN_YAHOO_PERSONAL_USE_ACKNOWLEDGED": "false",
        "CADRISYN_LEGACY_ENABLED": "false",
        "CADRISYN_LEGACY_SCHEDULER_ENABLED": "false",
        "DJANGO_API_URL": f"http://127.0.0.1:{api_port}",
        "DJANGO_SETTINGS_MODULE": "quantvision.settings",
        "PYTHONUNBUFFERED": "1",
        "NEXT_TELEMETRY_DISABLED": "1",
        "HOSTNAME": "127.0.0.1",
        "PORT": str(web_port),
    })
    return environment


def prepare_workspace(directory):
    import django

    django.setup()
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import transaction
    from research.quant.fixtures import make_fixture_payload
    from research.services import import_dataset, run_evaluation
    from workspace.models import WatchlistEntry

    call_command("migrate", interactive=False, verbosity=0)
    credentials_file = directory / "credentials.json"
    users = get_user_model().objects
    new_account = not credentials_file.exists()
    if credentials_file.exists():
        credentials = json.loads(credentials_file.read_text(encoding="utf-8"))
        user = users.filter(username=credentials["username"], is_active=True).first()
        if user is None:
            raise ValueError("The demo account is absent or inactive. Refusing to reset or replace it.")
        if not user.check_password(credentials["password"]):
            print("The initial demo password has changed. Use your current password to sign in.", flush=True)
    else:
        if users.exists():
            raise ValueError("The demo database already contains accounts but has no credentials. Refusing to change them.")
        credentials = {"username": "analyst", "password": secrets.token_urlsafe(32)}
        with transaction.atomic():
            user = users.create_user(**credentials)
            with credentials_file.open("x", encoding="utf-8") as output:
                json.dump(credentials, output)
    dataset, _ = import_dataset(
        make_fixture_payload(), owner=user, operator=user, synthetic_bootstrap=True,
    )
    for horizon in (1, 5):
        run_evaluation(
            owner=user, dataset=dataset, horizon=horizon,
            idempotency_key=uuid.uuid5(uuid.NAMESPACE_URL, f"kerquant-demo/{dataset.version}/{horizon}"),
        )
    if new_account:
        for instrument in ("xnas-aapl", "xnys-jpm", "xnas-msft"):
            WatchlistEntry.objects.get_or_create(owner=user, instrument_id=instrument)


def require_free_ports(*ports):
    for port in ports:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", port))


def prepare_browser_fixtures(directory, *, web_port):
    from accounts.services import issue_password_reset
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import transaction
    from research.quant.fixtures import make_fixture_payload
    from research.services import import_dataset, run_evaluation
    from workspace.models import WatchlistEntry

    names = ("account-e2e-invitation.txt", "account-e2e-reset.json", "research-e2e-isolation.json")
    if any((directory / name).exists() for name in names):
        raise ValueError("Browser fixtures already exist. Choose a new demo directory for another full lifecycle test.")
    users = get_user_model().objects
    suffix = uuid.uuid4().hex[:12]
    with transaction.atomic():
        operator = users.create_user("browser_operator_" + suffix, is_staff=True)
        invitation = io.StringIO()
        call_command(
            "issue_invitation", username="browser_invited_" + suffix, issued_by=operator.username,
            base_url=f"http://127.0.0.1:{web_port}", stdout=invitation, no_color=True,
        )
        password = secrets.token_urlsafe(32)
        reset_user = users.create_user("browser_reset_" + suffix, password=password)
        isolation_password = secrets.token_urlsafe(32)
        isolation_user = users.create_user("browser_isolation_" + suffix, password=isolation_password)
        _, token = issue_password_reset(user=reset_user, issued_by=operator)
        fixtures = {
            names[0]: invitation.getvalue(),
            names[1]: json.dumps({"username": reset_user.username, "initial_password": password, "token": token}),
            names[2]: json.dumps({"username": isolation_user.username, "password": isolation_password}),
        }
        for name, value in fixtures.items():
            with (directory / name).open("x", encoding="utf-8") as output:
                output.write(value)
        for spec in (ROOT / "web/e2e").glob("*.spec.ts"):
            account = {"username": "browser_spec_" + uuid.uuid4().hex[:12], "password": secrets.token_urlsafe(32)}
            owner = users.create_user(**account)
            dataset, _ = import_dataset(make_fixture_payload(), owner=owner, operator=owner, synthetic_bootstrap=True)
            for horizon in (1, 5):
                run_evaluation(owner=owner, dataset=dataset, horizon=horizon, idempotency_key=uuid.uuid4())
            for instrument in ("xnas-aapl", "xnys-jpm", "xnas-msft"):
                WatchlistEntry.objects.create(owner=owner, instrument_id=instrument)
            account_directory = directory / "browser-spec-accounts" / spec.stem
            account_directory.mkdir(parents=True)
            with (account_directory / "credentials.json").open("x", encoding="utf-8") as output:
                json.dump(account, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / ".local/portfolio-demo")
    parser.add_argument("--prepare-only", action="store_true", help="Prepare the isolated synthetic workspace without starting servers.")
    parser.add_argument("--browser-fixtures", action="store_true", help="With --prepare-only, add private one-use lifecycle accounts for the browser suite.")
    parser.add_argument("--api-only", action="store_true")
    parser.add_argument("--build", action="store_true", help="Build and run the optimized local frontend. This does not deploy.")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--web-port", type=int, default=3000)
    args = parser.parse_args()
    if args.browser_fixtures and not args.prepare_only:
        parser.error("--browser-fixtures requires --prepare-only and a disposable demo directory.")
    if any(not 1024 <= port <= 65535 for port in (args.api_port, args.web_port)) or args.api_port == args.web_port:
        parser.error("Choose distinct API and web ports between 1024 and 65535.")
    interpreter = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not interpreter.is_file():
        parser.error("Run scripts/setup.ps1 or scripts/setup.sh to install the locked workspace dependencies.")
    if not args.prepare_only and not args.api_only and (not npm or not (ROOT / "web/node_modules").is_dir()):
        parser.error("Install frontend dependencies with npm ci in web first.")
    try:
        if not args.prepare_only:
            require_free_ports(args.api_port, *(() if args.api_only else (args.web_port,)))
        environment = demo_environment(args.directory, api_port=args.api_port, web_port=args.web_port)
        os.environ.update(environment)
        sys.path.insert(0, str(ROOT / "backend"))
        prepare_workspace(args.directory.resolve())
        if args.browser_fixtures:
            prepare_browser_fixtures(args.directory.resolve(), web_port=args.web_port)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Demo credentials: {args.directory.resolve() / 'credentials.json'}", flush=True)
    print("Synthetic charts and research only. No empirical forecasting performance established.", flush=True)
    if args.prepare_only:
        return
    if args.build and not args.api_only:
        subprocess.run([npm, "run", "build"], cwd=ROOT / "web", env=environment, check=True)
    commands = [
        ([str(interpreter), "manage.py", "runserver", f"127.0.0.1:{args.api_port}", "--noreload"], ROOT / "backend"),
    ]
    if not args.api_only:
        frontend = [npm, "start"] if args.build else [npm, "run", "dev", "--", "--hostname", "127.0.0.1", "--port", str(args.web_port)]
        commands.append((frontend, ROOT / "web"))
    children = []

    def stop():
        for process in children:
            if process.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
                else:
                    os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)

    atexit.register(stop)
    for shutdown_signal in (signal.SIGINT, signal.SIGTERM):
        signal.signal(shutdown_signal, lambda *_: sys.exit(0))
    for command, cwd in commands:
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
        children.append(subprocess.Popen(command, cwd=cwd, env=environment, **options))
    if not args.api_only:
        print(f"Kerquant: http://127.0.0.1:{args.web_port}/app/markets", flush=True)
    print(f"API health: http://127.0.0.1:{args.api_port}/health/", flush=True)
    while all(process.poll() is None for process in children):
        time.sleep(0.5)
    failed = next(process for process in children if process.poll() is not None)
    raise SystemExit(failed.returncode or 1)


if __name__ == "__main__":
    main()
