# Repeat private container qualification

Use only isolated development databases and loopback ports. This guide reproduces Phase 3.5 infrastructure tests, not empirical market evaluation. No qualified historical dataset is included. Retain existing volumes, source databases and credentials.

## Resume the verified local stack

The current project is `cadrisyn-phase35`. Its private secrets and operator/test environments remain in ignored `.local/phase35/`. From the repository root in PowerShell:

```powershell
$taskComposeArgs = @('--project-name', 'cadrisyn-phase35', '--env-file', '.local/phase35/preview.env', '-f', 'compose.yaml', '-f', 'deploy/compose.qualification.yaml')
docker compose @taskComposeArgs up --detach --wait --wait-timeout 240
docker compose @taskComposeArgs ps
```

Open `http://127.0.0.1:8085/app/research`. Markets and account security use `/app/markets` and `/app/account`. Existing analyst credentials are in `.local/credentials.json`; no existing password was changed. The new database has explicit synthetic fixtures and disposable validation accounts only. The source SQLite preview on 3000/8000 is independent.

For a new clone/project, follow [foundation setup](FOUNDATION-OPERATIONS.md) using a new project name and new private environment file with four distinct generated secrets. Do not replace the retained Phase 3.5 file or initialize against an older volume. Build `api web` before startup. The [qualification override](../../deploy/compose.qualification.yaml) is the exact tested configuration: gateway 8085, PostgreSQL 15435 and Redis 16385, all loopback. It requires Compose 2.24.4 or later for `!override`; [Docker documents why port lists must be replaced](https://docs.docker.com/reference/compose-file/merge/#replace-value). These database/cache ports are for host-side tests only. Default `compose.yaml` still keeps them private. Check ports before starting; change all corresponding origins/DSNs deliberately if another service owns them.

## Repeat backend and database gates

The standard source command intentionally uses isolated SQLite and skips PostgreSQL-only cases:

```powershell
.venv/Scripts/python.exe scripts/check_backend.py
docker compose @taskComposeArgs exec -T api python -m pip check
```

For the full PostgreSQL selection, first provision a separate `test_cadrisyn` database owned by `cadrisyn_migrator`, migrate it with that role, and grant the runtime test role TRUNCATE plus sequence UPDATE in that test database only. The exact fresh-database setup is also recorded in [the PostgreSQL CI job](../../.github/workflows/workspace.yml). Do not grant those extra test permissions to the application database. The current qualification target already has this setup.

```powershell
docker compose @taskComposeArgs exec -T api python manage.py makemigrations --check --dry-run
docker compose @taskComposeArgs exec -T api python manage.py test workspace accounts research api.test_security --keepdb --noinput
```

All 120 tests should pass without skips under PostgreSQL. Runtime and migration credentials are separate. Container `exec` uses the configured constrained runtime role. Repeating a migration uses the migrator service, not runtime DDL privileges. The retained migration probe in [evidence](evidence/phase35/README.md) starts only in a new empty `cadrisyn_qualification_phase35` database; it refuses reuse. It simulates the enabled pre-research migration state with account/watchlist fixture rows, applies research, compares fields, repeats migration and verifies new synthetic storage. It does not alter an old user volume.

## Repeat browser and HTTP gates

Use the locked web dependencies. Install their matching Chromium into ignored workspace storage rather than selecting an older incompatible global cache:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) '.local/phase35/browsers'
Push-Location web
npx playwright install chromium
Pop-Location
```

Before each full browser run, prepare fresh invitation/reset fixtures in the migrated isolated preview. Compose's env file does not configure a host Python process. From the repository root, this command reads the retained preview secrets and supplies the explicit PostgreSQL/Redis/debug/preview environment only to a child process. It does not print a credential or change the parent shell environment. The preview must already contain the active `analyst` account described above. Preserve earlier disposable token files privately if retaining their evidence.

```powershell
@'
import os
import subprocess
import sys
from urllib.parse import quote

from dotenv import dotenv_values

values = dotenv_values('.local/phase35/preview.env', interpolate=False)
environment = os.environ.copy()
environment.update({
    'DJANGO_SETTINGS_MODULE': 'quantvision.settings',
    'DJANGO_SECRET_KEY': values['DJANGO_SECRET_KEY'],
    'DJANGO_DEBUG': 'true',
    'DJANGO_ALLOWED_HOSTS': 'localhost,127.0.0.1,testserver',
    'DJANGO_CSRF_TRUSTED_ORIGINS': 'http://127.0.0.1:8085,http://localhost:8085',
    'DATABASE_URL': 'postgresql://cadrisyn:' + quote(values['POSTGRES_PASSWORD'], safe='') + '@127.0.0.1:15435/cadrisyn',
    'DJANGO_CACHE_URL': 'redis://127.0.0.1:16385/1',
    'CADRISYN_PREVIEW_PROFILE': 'true',
    'CADRISYN_LEGACY_ENABLED': 'false',
    'CADRISYN_MARKET_DATA_ENABLED': 'false',
})
subprocess.run([sys.executable, 'scripts/prepare_browser_fixture.py', '--configured-preview', '--research-owner', 'analyst'], env=environment, check=True)
'@ | .venv/Scripts/python.exe -
```

The helper validates the development marker and PostgreSQL preview target. For a separately named fresh project, adjust only the private env-file path and the explicitly chosen test ports; do not point this command at an existing user store. The four secret values must be provisioned as described in foundation setup, not copied from this document.

```powershell
$env:PLAYWRIGHT_EXTERNAL_SERVER = '1'
$env:PLAYWRIGHT_PRODUCTION = '1'
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:8085'
Push-Location web
npm run test:e2e
Pop-Location
.venv/Scripts/python.exe scripts/smoke_api.py --origin http://127.0.0.1:8085 --include-research --concurrent-sign-in
```

Expect six browser passes, four with actual API journeys and two isolated UI cases, and 19 HTTP checks. The smoke command intentionally saves synthetic research and restores its original watchlist. Run the commands sequentially so writing acceptance checks cannot interfere. One-use lifecycle fixtures cannot be reused after successful consumption.

## Repeat recovery safely

Follow [recovery operations](../../scripts/ops/README.md). Create new archive names and a different empty destination. The application image includes PostgreSQL 17.11 clients. The executed backup was:

```powershell
docker compose @taskComposeArgs exec -T api python /app/scripts/ops/recovery.py backup-postgres --database-url-env DATABASE_URL --output /tmp/phase35.dump
```

That name now exists and must not be overwritten. Copy the archive and adjacent manifest together to private storage. Restore used a separate Docker invocation on the qualification network with the migration credential in a private env file and the backup directory mounted read-only. Docker `run --env-file` is supported; Compose `run --env-file` is not. The existing target `restore_cadrisyn` is populated and must not be reused as an empty restore target. Create another explicitly isolated destination for a repeat.

After restoration, provision constrained runtime CONNECT/schema usage/table CRUD/sequence usage-select privileges in the restored database, revoke PUBLIC TEMP/CREATE privileges, and then compare account/research fixture fields and replay both horizons under the same pinned image. [The executed probes](evidence/phase35/README.md) retain exact comparisons. Fresh sign-in and owner/outsider HTTP checks must pass before accepting recovery. The temporary restored API on 18005 was stopped after the proof; the main preview on 8085 remains available.

Whole-database backups include password, session and link state. A restore cannot recover revocations made after that backup. Production cutover must invalidate restored sessions and unused links and reconcile current access before reopening. The local proof does not certify that cutover, off-host protection, retention or RPO/RTO.

The actual workspace transfer used a read-only SQLite backup and a separate empty migrated PostgreSQL database, retaining 87 allowed fixture objects with all copied fields equal. Active sessions were excluded. Never select the original `backend/db.sqlite3` as a migration source or restore target.

## Preserve storage during host recovery

[The host repair record](PHASE35.md#docker-fault-and-targeted-repair) explains this machine's junction/bootstrap issue. Do not turn it into a generic reset procedure. A missing bootstrap directory was created through the already configured real target; no data disk or junction was moved. Docker startup then provisioned its own bootstrap distribution. If another host still cannot start, retain the failure evidence and follow Docker's [stopped-VM backup guidance](https://docs.docker.com/desktop/settings-and-maintenance/backup-and-restore/) before any separately approved storage intervention.

Use `docker compose @taskComposeArgs stop` to stop this project while retaining volumes. Do not prune/reset Docker, remove volumes or unregister distributions as a shortcut. No storage cleanup was required for Phase 3.5.
