# Verify private research usability

Use an existing isolated development or test environment. Do not point tests at `backend/db.sqlite3` or a retained user database. See [research operations](RESEARCH-OPERATIONS.md) for the existing local launcher and [CSV preflight](PHASE5-RESEARCH-OPERATIONS.md#preflight-before-database-work) for source intake. These commands do not authorize historical-data admission.

## Inspect the running workflow

The task preview serves `http://127.0.0.1:3000/app/research` and proxies API requests to `http://127.0.0.1:8000`. Its new database is `.local/research-usability-20261112/preview.sqlite3`; credentials are in the private `credentials.json` beside it. This is a compiled frontend with a local development API and synthetic fixtures, not a production deployment. Availability ends when those local processes stop.

1. Sign in to the isolated account and open **Research**.
2. Search the private dataset picker. Inspect source, calendar and coverage before execution.
3. Open **Inspect selected dataset provenance**. Check the dataset SHA-256 and the receipt/component hashes, if present. **Refresh source evidence** rechecks the latest archive. Operator-declared permissions are not independent legal clearance.
4. Choose one or five sessions and run the synthetic evaluation. Confirm the synthetic label and absence of empirical forecasting claims.
5. Select **Compare baseline errors**. Switch **Test** and **Validation**, then read the units, horizon, sample count and error explanation.
6. Use saved-run history to open and compare compatible runs. Use **Verify exact replay** and the synthetic JSON export. These operate on exact saved identities.
7. Change themes and test a mobile viewport. Confirm the comparison heading clears the sticky navigation and the document does not overflow horizontally.

Historical datasets do not become qualified by passing an archive check. Missing or corrupted latest evidence blocks new historical evaluations. Existing saved-result access and deterministic replay retain their documented meaning.

## Run frontend checks

From `web/`, use the installed locked dependencies:

```powershell
npm test -- --maxWorkers=2
npm run typecheck
npm run lint
npm run build
```

Stop only the verified task-owned frontend process before rebuilding standalone output on Windows. Do not run another build against a running preview's files. From `web/`, `npm start` serves the completed standalone build on loopback by default; keep the isolated API running separately.

For the task's prepared synthetic preview, run:

```powershell
$env:CADRISYN_E2E_FIXTURE_DIR = 'C:\stock price predictor\.local\research-usability-20261112'
$env:PLAYWRIGHT_BROWSERS_PATH = 'C:\stock price predictor\.local\research-usability-20261112\browsers'
$env:PLAYWRIGHT_EXTERNAL_SERVER = '1'
npx playwright test e2e/research-usability.spec.ts e2e/research-quality.spec.ts --workers=1 --output=../.local/research-usability-recheck
```

The fixture directory must contain the task's synthetic dataset, `credentials.json` and `research-e2e-isolation.json` for two disposable accounts. The browser specs write synthetic saved runs and exports to that isolated environment. Do not substitute real-user credentials. Use an output directory separate from retained acceptance evidence.

## Run backend checks on an isolated database

With the isolated database environment already configured, run from `backend/`:

```powershell
../.venv/Scripts/python.exe -B manage.py test research.tests --verbosity 2
../.venv/Scripts/python.exe -B manage.py spectacular --format openapi-json --validate --fail-on-warn --file ../.local/openapi-recheck.json
```

For PostgreSQL, use a new disposable instance, a unique role permitted to create its test database, and an ephemeral loopback port. Confirm the database's identity before running. The concurrency test is intentionally skipped on SQLite. PostgreSQL acceptance requires its real execution, one creator, one persisted result, identical results and successful database teardown. The retained [qualification receipt](evidence/research-usability-20261112/postgres-qualification.json) identifies the exact isolated image, container, source hashes and cleanup from this task.

Do not use production roles, reset Docker, delete retained volumes or reuse application databases for this check. The task's PostgreSQL container was removed after qualification; reruns require a fresh isolated instance. Existing recovery and backup procedures remain unchanged.
