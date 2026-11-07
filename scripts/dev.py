"""Start the local workspace and stop its child processes together."""

import argparse
import atexit
import os
import secrets
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def development_environment():
    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    secret_file = local / "django-secret"
    if not secret_file.exists():
        secret_file.write_text(secrets.token_urlsafe(64), encoding="utf-8")
        if os.name != "nt":
            secret_file.chmod(0o600)
    environment = os.environ.copy()
    for name in ('DJANGO_SECRET_KEY_FILE', 'DATABASE_URL_FILE', 'DJANGO_CACHE_URL_FILE'):
        environment.pop(name, None)
    environment.update({
        "DJANGO_DEBUG": "true",
        "CADRISYN_RELEASE_PROFILE": "development",
        "DJANGO_SECRET_KEY": secret_file.read_text(encoding="utf-8").strip(),
        "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1,[::1]",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "http://localhost:3000,http://127.0.0.1:3000",
        "CADRISYN_DB_PATH": str(local / "cadrisyn.sqlite3"),
        "DATABASE_URL": "",
        "DJANGO_CACHE_URL": "",
        "CADRISYN_LEGACY_ENABLED": "false",
        "CADRISYN_LEGACY_SCHEDULER_ENABLED": "false",
        "DJANGO_API_URL": "http://127.0.0.1:8000",
        "DJANGO_SETTINGS_MODULE": "quantvision.settings",
        "PYTHONUNBUFFERED": "1",
        "NEXT_TELEMETRY_DISABLED": "1",
    })
    return environment


def main():
    parser = argparse.ArgumentParser(description="Run the Cadrisyn local workspace using an isolated development database.")
    parser.add_argument("--api-only", action="store_true")
    args = parser.parse_args()
    interpreter = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not interpreter.is_file():
        parser.error("Create .venv and install backend/requirements-workspace.txt first. See README.md.")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not args.api_only and (not npm or not (ROOT / "web/node_modules").is_dir()):
        parser.error("Install Node dependencies with npm ci in web/ first.")
    environment = development_environment()
    for command in ([str(interpreter), "manage.py", "migrate", "--noinput"], [str(interpreter), "manage.py", "create_local_user"]):
        subprocess.run(command, cwd=ROOT / "backend", env=environment, check=True)
    children = []

    def stop(*_):
        for child in children:
            if child.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], capture_output=True, check=False)
                else:
                    os.killpg(child.pid, signal.SIGTERM)

    atexit.register(stop)
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    commands = [([str(interpreter), "manage.py", "runserver", "127.0.0.1:8000", "--noreload"], ROOT / "backend")]
    if not args.api_only:
        commands.append(([npm, "run", "dev", "--", "--hostname", "127.0.0.1"], ROOT / "web"))
    for command, directory in commands:
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
        children.append(subprocess.Popen(command, cwd=directory, env=environment, **options))
    if not args.api_only:
        print("Cadrisyn workspace: http://127.0.0.1:3000", flush=True)
    print("Django API health: http://127.0.0.1:8000/health/", flush=True)
    print("Local login is stored in .local/credentials.json. Original research database is untouched.", flush=True)
    while all(child.poll() is None for child in children):
        time.sleep(0.5)
    failed = next(child for child in children if child.poll() is not None)
    raise SystemExit(failed.returncode or 1)


if __name__ == "__main__":
    main()
