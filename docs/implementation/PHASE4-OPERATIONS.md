# Run and verify the Phase 4 workspace

Use isolated preview data and loopback interfaces. Keep the existing database, volumes, private environment files, and earlier backup archives.

## Resume this machine's packaged preview

From `C:\stock price predictor` in PowerShell:

```powershell
docker start cadrisyn-phase35-database-1 cadrisyn-phase35-cache-1
docker start cadrisyn-phase4-api cadrisyn-phase4-web
docker start cadrisyn-phase4-gateway
curl.exe --fail http://127.0.0.1:8086/health/ready/
```

Open [research](http://127.0.0.1:8086/app/research), [markets](http://127.0.0.1:8086/app/markets), or [account security](http://127.0.0.1:8086/app/account). Existing analyst credentials remain in ignored `.local/credentials.json`. These are local preview credentials, not a production account setup.

The Phase 4 API and web run non-root with dropped capabilities and no-new-privileges. Its gateway binds only `127.0.0.1:8086`. PostgreSQL roles and the Phase 3.5 containers are retained. The Phase 4 API uses Redis database 3, separate from the old application. The gateway's read-only configuration and the API's private environment remain in `.local/phase4/`. Do not print those environments or put database URLs in process arguments.

The temporary `*-before-lineage`, `*-before-theme`, and `*-before-review` Phase 4 containers are stopped and retained. The source development frontend on 3100 was stopped before packaged acceptance. Port 8085 serves the retained Phase 3.5 application, not the new UI. Read-only gateway probes are recorded separately from Docker healthchecks; manually started Phase 4 containers have no claimed Docker health status.

For a fresh clone, follow [foundation setup](FOUNDATION-OPERATIONS.md) with new private secrets and an explicitly isolated Compose project. The standard `compose.yaml` and Dockerfiles build the current code. Do not initialize an older user volume or copy this machine's credentials. The [Phase 3.5 operations guide](PHASE35-OPERATIONS.md) explains constrained role/test-database provisioning and host-runtime environment setup.

## Exercise research

1. Sign in and open **Research**.
2. Select an imported private dataset and a supported horizon. A synthetic fixture remains labeled throughout the workflow.
3. Run an evaluation. Copy the URL to retain the exact run identity.
4. Inspect **Forecast**, **Walk-forward**, and **Errors**. Use the session slider with arrow keys or open exact values.
5. Filter **Saved evaluations** and choose **Compare with open run**. Preserve both UUIDs in the URL. Incompatible protocols or horizons hide metric changes.
6. Choose **Verify exact replay**. Inspect each check; a runtime mismatch is not a numerical PASS.
7. Download synthetic JSON. Preserve the file unchanged. Its `result_sha256` hashes Python's sorted compact JSON representation of the stored result, not the whole envelope or arbitrary reserialized browser JSON.

Both references are always evaluated. **Reference focus** changes the display only. Missing licensed data does not enable uploads, live-data substitution, legacy model training, or historical export.

## Repeat source and container checks

```powershell
.venv/Scripts/python.exe scripts/check_backend.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_recovery.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_workspace_migration.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_research_client.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_dev_environment.py
docker exec cadrisyn-phase4-api python -m pip check
docker exec cadrisyn-phase4-api python manage.py makemigrations --check --dry-run
docker exec cadrisyn-phase4-api python manage.py test workspace accounts research api.test_security --keepdb --noinput
Push-Location web
npm run typegen
npm run typecheck
npm run lint
npm test -- --maxWorkers=2
Pop-Location
```

The container test command requires the existing separate `test_cadrisyn` database and its test-only grants described in the Phase 3.5 guide. Never grant runtime DDL or test TRUNCATE privileges in the application database. Source checks use isolated SQLite and skip PostgreSQL-only cases. This phase introduces no database migration.

Before browser acceptance, run the documented fixture-preparation command in [Phase 3.5 operations](PHASE35-OPERATIONS.md#repeat-browser-and-http-gates). It supplies an explicit child environment from the retained secrets and creates fresh disposable invitation/reset tokens. Preserve earlier one-use token files privately before replacing them. The same isolated PostgreSQL store serves both previews; use the existing `analyst` research owner.

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) '.local/phase35/browsers'
$env:PLAYWRIGHT_EXTERNAL_SERVER = '1'
$env:PLAYWRIGHT_PRODUCTION = '1'
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:8086'
Push-Location web
npx playwright install chromium
npm run test:e2e -- --workers=1
Pop-Location
.venv/Scripts/python.exe scripts/smoke_api.py --origin http://127.0.0.1:8086 --include-research --concurrent-sign-in
```

The browser suite contains nine scenarios. Fixture preparation also writes private `research-e2e-isolation.json` for the two-tab account-switch test. Run writing acceptance commands sequentially; the research throttle is shared by evaluation and replay. Allow rate-limit windows to expire between browser and smoke batches if necessary. Do not disable or clear application rate limits to make acceptance pass. Screenshots appear under ignored `web/test-results/`. These tests save labeled synthetic evaluations and use disposable lifecycle accounts.

Successful login/logout broadcasts a credential-free invalidation message to other tabs. Focus and visible-tab transitions also recheck the session. During recheck the private workspace is unmounted, and another username creates a fresh workspace. Navigating away aborts the client evaluation request and prevents late navigation; a server evaluation already in progress can still finish and remain in private history.

## Repeat recovery without replacing data

Follow [recovery operations](../../scripts/ops/README.md). The API image contains the required PostgreSQL clients. Use a new archive filename and a newly created empty target database on every qualification attempt:

```powershell
docker exec cadrisyn-phase4-api python /app/scripts/ops/recovery.py backup-postgres --database-url-env DATABASE_URL --output /tmp/another-preview.dump
```

Copy the dump and adjacent manifest together into private storage. Supply restoration credentials through a private env file to a separate invocation of the API image. Mount only the backup/probe directory read-only. A Python probe outside `/app/backend` needs `PYTHONPATH=/app/backend` or an explicit equivalent import path.

`restore_cadrisyn_phase4` is now populated. Do not reuse it as an empty target. The Phase 4 recovery proof compared all selected fixture fields and replayed both horizons under the pinned numerical runtime; it did not reopen the restored store to users. Existing backup/restore tools reject overwrites and populated targets. Restored sessions and unused links still require production cutover invalidation and access reconciliation.

## Check security and stop safely

Run [the scoped dependency and image scans](PHASE4-SCANNING.md). Their current Medium-or-higher image gate is **FAIL**, despite passing application tests and clean application dependency audits. Retain scanner output and compare vendor package revisions before accepting a finding or a false-positive disposition.

```powershell
docker stop cadrisyn-phase4-gateway cadrisyn-phase4-web cadrisyn-phase4-api
```

This stops only the Phase 4 application. Retain the database/cache and all volumes. No prune, reset, volume removal, WSL relocation, merge, or deployment is part of these instructions.
