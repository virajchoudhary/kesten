"""Run a new loopback TLS release rehearsal, retaining all volumes and private evidence.

Never targets an existing project, provisions public trust, or declares deployment approval.
"""

import argparse
import hashlib
import http.cookiejar
import json
import os
import re
import secrets
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def new_directory(value):
    directory = Path(value).resolve()
    if not directory.is_relative_to(ROOT / ".local") or directory == ROOT / ".local" or directory.exists():
        raise ValueError("Choose a new directory strictly inside repository .local.")
    return directory


def immutable_image(value):
    if not re.fullmatch(r"(?:[^\s]+@)?sha256:[0-9a-f]{64}", value):
        raise ValueError("Supply an immutable local image ID or repository digest.")
    return value


def command(arguments, *, input_text=None):
    return subprocess.run([str(item) for item in arguments], cwd=ROOT, input=input_text, text=True, capture_output=True, timeout=480, check=False)


class Rehearsal:
    def __init__(self, directory, api_image, web_image, tls_port, http_port, openssl, cache_image=None, gateway_image=None, database_image=None):
        self.directory = new_directory(directory)
        if tls_port == http_port or any(not 1024 <= port <= 65535 for port in (tls_port, http_port)):
            raise ValueError("Choose two distinct unprivileged loopback ports.")
        self.project = "kerquant-qualification-" + secrets.token_hex(12)
        self.tls_port, self.http_port = tls_port, http_port
        self.api_image, self.web_image = immutable_image(api_image), immutable_image(web_image)
        self.infrastructure_images = {key: immutable_image(value) for key, value in {"cache": cache_image, "gateway": gateway_image, "database": database_image}.items() if value}
        self.openssl = openssl
        self.checks = []
        self.credentials = [{"username": "qualification_" + str(i), "password": secrets.token_urlsafe(32)} for i in (1, 2)]
        self.context = None
        tooling = ["scripts/ops/qualify_production.py", "scripts/ops/production_probe.py", "scripts/ops/prepare_local_tls.py", "scripts/qualify_research_postgres.py"]
        self.tooling_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in tooling}

    def compose(self, *arguments, input_text=None, expected=0):
        args = ["docker", "compose", "--project-name", self.project, "--env-file", self.directory / "stack.env",
                "-f", ROOT / "deploy/compose.production.yaml", "-f", ROOT / "deploy/compose.production-qualification.yaml", *arguments]
        result = command(args, input_text=input_text)
        # Logs stay private: Docker errors may include secret mount paths.
        with (self.directory / "commands.log").open("a", encoding="utf-8") as output:
            output.write(result.stdout + result.stderr + "\nexit=" + str(result.returncode) + "\n")
        if result.returncode != expected:
            raise RuntimeError("Container operation failed; inspect private commands.log.")
        return result.stdout

    def record(self, name, evidence=True):
        self.checks.append({"check": name, "status": "PASS", "evidence": evidence})
        self.save("IN_PROGRESS")
        print(name + ": PASS", flush=True)

    def save(self, result, error=None):
        receipt = {
            "schema_version": 1, "created_at": datetime.now(UTC).isoformat(), "result": result,
            "source_commit": command(["git", "rev-parse", "HEAD"]).stdout.strip(),
            "working_tree_dirty": bool(command(["git", "status", "--porcelain"]).stdout),
            "project": self.project, "checks": self.checks, "error": error,
            "images": {"api": self.api_image, "web": self.web_image, **self.infrastructure_images},
            "configuration_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT / "deploy/compose.production.yaml", ROOT / "deploy/compose.production-qualification.yaml", ROOT / "deploy/nginx.production.conf"]},
            "tooling_sha256": self.tooling_hashes,
            "data_kind": "synthetic_fixture", "empirical_evaluation": False,
            "scope": "Isolated local production-profile rehearsal with a job-local CA; not hosted CI, public TLS, off-host recovery, or deployment approval.",
        }
        (self.directory / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")

    def prepare(self):
        from scripts.ops import prepare_local_tls

        if os.name == "nt" and not callable(getattr(prepare_local_tls, "protect_directory", None)):
            raise RuntimeError("Windows qualification requires ACL-protected local TLS preparation; no secrets were generated.")
        self.refuse_existing_project()
        # mkdir(exist_ok=False) in prepare refuses old directories, volumes and secrets.
        prepare_local_tls.prepare(self.directory, self.openssl, self.api_image, self.web_image)
        gateway = (ROOT / "deploy/nginx.production.conf").read_text().replace("https://$host:8443$request_uri", f"https://$host:{self.tls_port}$request_uri")
        (self.directory / "nginx.conf").write_text(gateway, encoding="utf-8", newline="\n")
        environment = (self.directory / "rehearsal.env").read_text().replace(":8443", ":" + str(self.tls_port))
        environment += f"QUALIFICATION_TLS_PORT={self.tls_port}\nQUALIFICATION_HTTP_PORT={self.http_port}\nQUALIFICATION_GATEWAY_CONFIG={(self.directory / 'nginx.conf').as_posix()}\n"
        environment += "".join(f"QUALIFICATION_{name.upper()}_IMAGE={value}\n" for name, value in self.infrastructure_images.items())
        (self.directory / "stack.env").write_text(environment, encoding="utf-8", newline="\n")
        (self.directory / "credentials.json").write_text(json.dumps(self.credentials), encoding="utf-8")
        self.context = ssl.create_default_context(cafile=str(self.directory / "tls_ca"))
        self.compose("config", "--quiet")
        self.compose("up", "--detach", "--wait", "--wait-timeout", "240")
        self.record("fresh_tls_stack")

    def refuse_existing_project(self):
        inventories = [
            (["docker", "container", "ls", "--all", "--quiet", "--filter", "label=com.docker.compose.project=" + self.project], None),
            (["docker", "volume", "ls", "--quiet"], {self.project + "_database"}),
            (["docker", "network", "ls", "--format", "{{.Name}}"], {self.project + "_app", self.project + "_data"}),
        ]
        for arguments, names in inventories:
            result = command(arguments)
            if result.returncode:
                raise RuntimeError("Cannot establish an unused qualification project.")
            found = set(result.stdout.splitlines())
            if (found if names is None else found & names):
                raise ValueError("Qualification refuses existing Compose resources.")

    def container_probe(self, operation, payload, bootstrap=False):
        code = (ROOT / "scripts/ops/production_probe.py").read_text()
        code += "\nmain(" + repr(operation) + ", " + repr(payload) + ")\n"
        args = ["run", "--rm", "--no-deps", "-T", "-e", "KERQUANT_PRODUCTION_QUALIFICATION=isolated"]
        if bootstrap:
            args += ["-e", "DJANGO_DEBUG=true", "-e", "CADRISYN_RELEASE_PROFILE=development", "-e", "CADRISYN_WEB_RELEASE_PROFILE=development"]
        elif operation == "recover":
            recovery = self.directory / "recovery"
            recovery.mkdir(exist_ok=False)
            if os.name != "nt":
                # Match the newly created host backup directory's owner on Linux runners.
                args += ["--user", f"{os.getuid()}:{os.getgid()}"]
            args += ["-v", str(recovery) + ":/qualification", "-v", str(self.directory / "migration_url") + ":/run/secrets/migration_url:ro",
                     "-v", str(ROOT / "scripts/qualify_research_postgres.py") + ":/qualification-code/qualify_research_postgres.py:ro"]
        # /app is required for importing the existing operational recovery module.
        args += ["-e", "PYTHONPATH=/app:/qualification-code", "--entrypoint", "python", "api", "-"]
        return json.loads(self.compose(*args, input_text=code))

    def verify_restored_http(self):
        self.container_probe("marker", self.credentials[1]["username"])
        client, csrf = self.login(self.credentials[1])
        items, _ = self.expect("/api/v1/watchlist/", 200, opener=client)
        if [item["id"] for item in items["items"]] != ["xnas-msft"]:
            raise RuntimeError("HTTP did not observe the restore-only marker.")
        self.expect("/api/v1/watchlist/xnas-msft/", 204, method="DELETE", opener=client, csrf=csrf)
        self.record("restored_http_database_binding", {"database": "qualification_restore", "restore_only_marker_observed_and_removed": True})

    def request(self, path, method="GET", body=None, opener=None, csrf=None, headers=None):
        request_headers = {"Content-Type": "application/json", **(headers or {})}
        if csrf:
            request_headers["X-CSRFToken"] = csrf
            request_headers.setdefault("Origin", f"https://localhost:{self.tls_port}")
        req = urllib.request.Request(f"https://localhost:{self.tls_port}" + path, data=json.dumps(body).encode() if body is not None else None, headers=request_headers, method=method)
        opener = opener or urllib.request.build_opener(urllib.request.HTTPSHandler(context=self.context))
        try:
            response = opener.open(req, timeout=15)
        except urllib.error.HTTPError as error:
            response = error
        raw = response.read()
        content = json.loads(raw) if response.headers.get("Content-Type", "").startswith("application/json") else raw.decode(errors="replace")
        return response.status, content, response.headers

    def expect(self, path, status, **kwargs):
        actual, body, headers = self.request(path, **kwargs)
        if actual != status:
            raise RuntimeError(f"Unexpected HTTP status at {path}: {actual}, expected {status}.")
        return body, headers

    def login(self, account):
        cookies = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=self.context), urllib.request.HTTPCookieProcessor(cookies))
        session, _ = self.expect("/api/v1/session/", 200, opener=opener)
        self.expect("/api/v1/session/", 200, method="POST", body=account, csrf=session["csrf_token"], opener=opener)
        session, _ = self.expect("/api/v1/session/", 200, opener=opener)
        session_cookie = next(cookie for cookie in cookies if cookie.name == "cadrisyn_session")
        if not session_cookie.secure or not session_cookie.has_nonstandard_attr("HttpOnly") or session_cookie.get_nonstandard_attr("SameSite") != "Lax":
            raise RuntimeError("Session cookie protections failed.")
        return opener, session["csrf_token"]

    def accept(self, profile, label=None):
        policy, headers = self.expect("/health/release/", 200)
        if policy.get("profile") != profile or policy.get("debug") is not False:
            raise RuntimeError("Release policy mismatch.")
        if not headers.get("Strict-Transport-Security"):
            raise RuntimeError("HSTS is missing.")
        self.expect("/health/ready/", 200)
        self.expect("/api/v1/watchlist/", 403)
        owner, token = self.login(self.credentials[0])
        other, other_token = self.login(self.credentials[1])
        self.expect("/api/v1/watchlist/", 403, method="POST", body={"instrument_id": "xnas-aapl"}, opener=owner)
        self.expect("/api/v1/watchlist/", 403, method="POST", body={"instrument_id": "xnas-aapl"}, opener=owner, csrf=token, headers={"Origin": "https://untrusted.invalid"})
        self.expect("/api/v1/watchlist/", 201 if profile == "demo" else 200, method="POST", body={"instrument_id": "xnas-aapl"}, opener=owner, csrf=token)
        other_list, _ = self.expect("/api/v1/watchlist/", 200, opener=other)
        if other_list["items"]:
            raise RuntimeError("Private watchlist leaked across accounts.")
        bars, _ = self.expect("/api/v1/instruments/xnas-aapl/bars/?range=1y&mode=demo", 200, opener=owner)
        if "demo" not in json.dumps(bars).lower():
            raise RuntimeError("Demo provenance is absent.")
        self.expect("/api/v1/instruments/xnas-aapl/bars/?range=1y&mode=market", 503, opener=owner)
        if profile == "demo":
            for route in ("datasets/", "history/", "runs/"):
                self.expect("/api/v1/research/" + route, 404, opener=owner)
            self.expect("/api/v1/research/runs/", 404, method="POST", body={}, opener=owner, csrf=token)
        else:
            runs, _ = self.expect("/api/v1/research/runs/", 200, opener=owner)
            private, _ = self.expect("/api/v1/research/runs/", 200, opener=other)
            if len(runs["items"]) != 2 or private["items"]:
                raise RuntimeError("Research isolation or seeded identities failed.")
            for run in runs["items"]:
                prefix = "/api/v1/research/runs/" + run["id"] + "/"
                self.expect(prefix, 404, opener=other)
                self.expect(prefix + "export/", 404, opener=other)
                self.expect(prefix + "replay/", 404, method="POST", body={}, opener=other, csrf=other_token)
                replay, _ = self.expect(prefix + "replay/", 200, method="POST", body={}, opener=owner, csrf=token)
                if replay["result"] != "PASS":
                    raise RuntimeError("Saved replay changed.")
                exported, export_headers = self.expect(prefix + "export/", 200, opener=owner)
                if not exported or "no-store" not in export_headers.get("Cache-Control", ""):
                    raise RuntimeError("Export privacy failed.")
        self.expect("/api/v1/session/", 200, method="DELETE", opener=owner, csrf=token)
        self.expect("/api/v1/watchlist/", 403, opener=owner)
        self.record((label or profile) + "_https_auth_privacy_and_provenance")

    def faults(self):
        for service in ("cache", "database"):
            self.compose("stop", service)
            try:
                for _ in range(10):
                    status, _, _ = self.request("/health/ready/")
                    if status == 503:
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError("Readiness did not fail closed for " + service)
                self.expect("/health/", 200)
            finally:
                self.compose("start", service)
            for _ in range(60):
                if self.request("/health/ready/")[0] == 200:
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Dependency did not recover: " + service)
            self.record(service + "_failure_and_recovery")

    def role_drift(self):
        cases = [
            ("membership", "GRANT cadrisyn_migrator TO cadrisyn WITH INHERIT FALSE, SET TRUE", "REVOKE cadrisyn_migrator FROM cadrisyn"),
            ("routine_ownership", "CREATE FUNCTION public.qualification_role_probe() RETURNS integer LANGUAGE sql AS 'SELECT 1'; ALTER FUNCTION public.qualification_role_probe() OWNER TO cadrisyn", "ALTER FUNCTION public.qualification_role_probe() OWNER TO cadrisyn_migrator"),
            ("type_ownership", "CREATE TYPE public.qualification_role_enum AS ENUM ('fixture'); ALTER TYPE public.qualification_role_enum OWNER TO cadrisyn", "ALTER TYPE public.qualification_role_enum OWNER TO cadrisyn_migrator"),
            ("nonpublic_schema", "CREATE SCHEMA qualification_role_scope AUTHORIZATION cadrisyn", "ALTER SCHEMA qualification_role_scope OWNER TO cadrisyn_migrator; REVOKE ALL ON SCHEMA qualification_role_scope FROM cadrisyn"),
        ]
        for name, setup, cleanup in cases:
            self.compose("exec", "-T", "--user", "postgres", "database", "psql", "-v", "ON_ERROR_STOP=1", "-d", "cadrisyn", "-c", setup)
            try:
                body, _ = self.expect("/health/ready/", 503)
                if body["checks"].get("database_role") is not False:
                    raise RuntimeError("Role drift did not fail closed: " + name)
            finally:
                self.compose("exec", "-T", "--user", "postgres", "database", "psql", "-v", "ON_ERROR_STOP=1", "-d", "cadrisyn", "-c", cleanup)
            self.expect("/health/ready/", 200)
            self.record("role_drift_" + name)

    def run(self):
        self.prepare()
        self.record("synthetic_numerical_contract", self.container_probe("bootstrap", self.credentials, bootstrap=True))
        self.accept("demo")
        environment = (self.directory / "stack.env").read_text().replace("PROFILE=demo", "PROFILE=historical_research")
        (self.directory / "stack.env").write_text(environment, encoding="utf-8", newline="\n")
        self.compose("up", "--detach", "--wait", "--wait-timeout", "240")
        self.accept("historical_research")
        self.record("container_preflight", json.loads(self.compose("exec", "-T", "api", "python", "/app/scripts/ops/preflight.py", "--environment")))
        self.role_drift()
        init = (ROOT / "deploy/postgres-init.sh").read_text()
        schema = init[init.index("REVOKE ALL ON SCHEMA"):init.index("SQL", init.index("REVOKE ALL ON SCHEMA"))]
        self.compose("exec", "-T", "--user", "postgres", "database", "psql", "-v", "ON_ERROR_STOP=1", "-d", "postgres", "-c", "CREATE DATABASE qualification_restore OWNER cadrisyn_migrator")
        self.compose("exec", "-T", "--user", "postgres", "database", "psql", "-v", "ON_ERROR_STOP=1", "-d", "postgres", "-c", "REVOKE ALL ON DATABASE qualification_restore FROM PUBLIC, cadrisyn; GRANT CONNECT ON DATABASE qualification_restore TO cadrisyn_migrator, cadrisyn")
        self.compose("exec", "-T", "--user", "postgres", "database", "psql", "-v", "ON_ERROR_STOP=1", "-d", "qualification_restore", input_text=schema)
        self.compose("stop", "gateway", "web", "api")
        try:
            self.record("postgres_dump_restore_and_exact_replay", self.container_probe("recover", None))
            # Route only this disposable stack to the verified restored database.
            source_url = (self.directory / "database_url").read_text()
            (self.directory / "database_url").write_text(source_url.replace("/cadrisyn?", "/qualification_restore?"), encoding="utf-8")
        finally:
            self.compose("up", "--detach", "--wait", "--wait-timeout", "240")
        self.accept("historical_research", label="restored")
        self.verify_restored_http()
        self.faults()
        self.save("PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--api-image", required=True, type=immutable_image)
    parser.add_argument("--web-image", required=True, type=immutable_image)
    parser.add_argument("--cache-image", type=immutable_image)
    parser.add_argument("--gateway-image", type=immutable_image)
    parser.add_argument("--database-image", type=immutable_image)
    parser.add_argument("--tls-port", type=int, default=8452)
    parser.add_argument("--http-port", type=int, default=8092)
    parser.add_argument("--openssl", default="openssl")
    args = parser.parse_args()
    rehearsal = Rehearsal(args.directory, args.api_image, args.web_image, args.tls_port, args.http_port, args.openssl, args.cache_image, args.gateway_image, args.database_image)
    try:
        rehearsal.run()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        if rehearsal.directory.exists():
            rehearsal.save("FAIL", type(error).__name__ + ": acceptance incomplete; inspect private evidence.")
        print("Qualification failed; all files and volumes retained. " + type(error).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
