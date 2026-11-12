"""Run preserved research tools locally using a cloned database and staff authentication."""

import json
import os
import secrets
import sqlite3
import subprocess

from dev import ROOT, development_environment


def main():
    interpreter = ROOT / "backend/venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not interpreter.is_file():
        raise SystemExit("The preserved backend/venv environment is unavailable. Install the research requirements in a separate environment.")
    environment = development_environment()
    environment.update({
        "DJANGO_SETTINGS_MODULE": "quantvision.legacy_settings",
        "CADRISYN_LEGACY_ENABLED": "true",
        "CADRISYN_DB_PATH": str(ROOT / ".local/legacy.sqlite3"),
        "CADRISYN_LEGACY_API_URL": "http://127.0.0.1:8001/api",
    })
    destination = ROOT / ".local/legacy.sqlite3"
    if not destination.exists():
        with sqlite3.connect((ROOT / "backend/db.sqlite3").resolve().as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(destination) as copy:
            source.backup(copy)
    credentials_file = ROOT / ".local/research-credentials.json"
    if not credentials_file.exists():
        credentials_file.write_text(json.dumps({"username": "researcher", "password": secrets.token_urlsafe(24)}), encoding="utf-8")
        if os.name != "nt":
            credentials_file.chmod(0o600)
    credentials = json.loads(credentials_file.read_text(encoding="utf-8"))
    environment["CADRISYN_LEGACY_USERNAME"] = credentials["username"]
    environment["CADRISYN_LEGACY_PASSWORD"] = credentials["password"]
    subprocess.run([str(interpreter), "manage.py", "migrate", "--noinput"], cwd=ROOT / "backend", env=environment, check=True)
    command = "import os; from django.contrib.auth import get_user_model; User=get_user_model(); user,created=User.objects.get_or_create(username=os.environ['CADRISYN_LEGACY_USERNAME']); user.is_staff=True; user.set_password(os.environ['CADRISYN_LEGACY_PASSWORD']); user.save()"
    subprocess.run([str(interpreter), "manage.py", "shell", "-c", command], cwd=ROOT / "backend", env=environment, check=True)
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    api = subprocess.Popen([str(interpreter), "manage.py", "runserver", "127.0.0.1:8001", "--noreload"], cwd=ROOT / "backend", env=environment, **options)
    try:
        subprocess.run([str(interpreter), "-m", "streamlit", "run", "Home.py", "--server.address", "127.0.0.1", "--server.port", "8501", "--server.headless", "true"], cwd=ROOT / "frontend", env=environment, check=True)
    finally:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(api.pid), "/T", "/F"], capture_output=True, check=False)
        else:
            api.terminate()
        api.wait(timeout=10)


if __name__ == "__main__":
    main()
