# Run a Kerquant portfolio demonstration

Use this guide for a local demonstration with synthetic charts and research. It does not authorize publication, deployment, real trading, or historical-data acquisition.

## Start the demonstration

Use Python 3.12 and Node 22 LTS, version 22.12 or later. Run setup once from the repository root.

```powershell
./scripts/setup.ps1
.venv/Scripts/python.exe scripts/demo.py
```

On Linux or macOS:

```sh
sh scripts/setup.sh
.venv/bin/python scripts/demo.py
```

Open `http://127.0.0.1:3000/app/markets`. Read the generated credentials from `.local/portfolio-demo/credentials.json`. Do not publish this file or put its contents in a screenshot.

The demo command explicitly prepares a synthetic account, three watchlist instruments, a synthetic research dataset, and saved baseline evaluations for both horizons. It uses the existing numerical engine and admission rules. All visible prices and errors are synthetic, not measured forecasting performance.

For an optimized local frontend, run:

```powershell
.venv/Scripts/python.exe scripts/demo.py --build
```

Stop a running preview before building against its `.next` output. `--build` compiles and starts local services; it does not use the production release profile or deploy anything. The API remains a loopback development server.

Stop the launcher with Ctrl+C. Restarting retains the account password, numerical run identities, and watchlist changes. The database is `.local/portfolio-demo/workspace.sqlite3`; existing application/research databases are separate.

If ports 3000 or 8000 are busy, choose distinct free ports:

```powershell
.venv/Scripts/python.exe scripts/demo.py --web-port 3001 --api-port 8002
```

The launcher fails before preparation if a required port is occupied. It never stops another application. `--directory .local/another-demo` selects another isolated demo folder. An existing folder without the demo marker is rejected.

## Present the core workflows

1. Sign in and open **Markets**. Search by symbol/company, switch instruments, and add/remove a private watchlist entry.
2. Inspect daily candlesticks, OHLC values, price/volume scales, SMA and RSI. Change the displayed history range and chart settings. Use EMA/Bollinger studies, comparison, measurement, or price levels as display tools.
3. Open research for JPM from the watchlist, or use the **Research** navigation link. Choose the synthetic dataset and one- or five-session horizon.
4. Inspect dataset coverage/provenance, run an evaluation, and open the saved result. Compare persistence and historical-log-mean errors with their units, target dates, and validation/test periods.
5. Inspect forecast/walk-forward/error charts and exact values. Open compatible saved-run comparisons, download a synthetic result, and verify exact replay.
6. Open **Account** to change your password or revoke other sessions. Sign out and confirm that private routes require authentication.
7. Show narrow-screen navigation and both themes. **Data** and **Methodology** document the observations, calculation methods, and research limitations.

A watchlist instrument without a private research dataset displays an empty state. It does not automatically create, license, or qualify observations for that instrument.

## Run browser acceptance

Use a new directory for each complete account-lifecycle run. These tests consume invitation/reset tokens and mutate their disposable accounts. Do not point them at a retained personal workspace.

The following Windows procedure uses ports 8000 and 3000. Stop any task-owned preview on those ports first.

```powershell
.venv/Scripts/python.exe scripts/demo.py --directory .local/portfolio-e2e-example --prepare-only --browser-fixtures
.venv/Scripts/python.exe scripts/demo.py --directory .local/portfolio-e2e-example --api-only
```

Keep the API terminal running. In a second terminal, from `web/`:

```powershell
$env:CADRISYN_E2E_FIXTURE_DIR = (Resolve-Path ../.local/portfolio-e2e-example).Path
$env:PLAYWRIGHT_BROWSERS_PATH = (Join-Path $env:CADRISYN_E2E_FIXTURE_DIR 'browsers')
$env:DJANGO_API_URL = 'http://127.0.0.1:8000'
$env:CADRISYN_WEB_RELEASE_PROFILE = 'development'
$env:PLAYWRIGHT_PRODUCTION = '1'
npx playwright install chromium
npm run build
npx playwright test --workers=1 --output=../.local/portfolio-e2e-example/browser-output
```

If inherited `PLAYWRIGHT_EXTERNAL_SERVER` or `PLAYWRIGHT_BASE_URL` values select another server, clear them for this procedure. The Playwright configuration starts and stops the optimized frontend itself and refuses to reuse a running server. The existing suites cover real API journeys plus explicit browser fault injection; mocked cases alone are not runtime acceptance.

Browser fixtures are created only with `--browser-fixtures --prepare-only`. Each spec receives its own private account, so rate limits and saved state do not leak between suites. A rerun refuses to overwrite one-use secrets. Choose a different folder instead. The original `prepare_browser_fixture.py` remains for its documented development/preview database targets; it is not the portfolio setup command.

## Preserve and recover local work

Keep each demo directory private. Copying source code is different from sharing credentials, datasets, or database files. After changing your password in **Account**, use that password on later starts. The launcher retains the original credentials file for reference and prints a reminder when its initial password is stale. It never resets your password. An absent or inactive account stops preparation; inspect the dedicated demo database before choosing an explicit recovery action. Do not delete a database to repair login.

The existing [backup and recovery instructions](implementation/OPERATIONS.md) remain applicable to their stated environments. This guide creates no new production database, PostgreSQL role, volume, or recovery policy.

## Describe the limits accurately

The supported demonstration is a charting and reproducible research application. Its default dataset is synthetic. The optional Yahoo adapter remains disabled by this launcher; a settings acknowledgement alone does not establish storage or redistribution rights.

No historical archive passed the existing point-in-time gate. Empirical forecasting accuracy, advanced models, confidence intervals, investment recommendations, and live trading remain unavailable. Original ARIMA/GARCH, BiLSTM/HPO, optimization, options, RL, and reporting implementations remain preserved research code outside the qualified terminal demonstration.

Portfolio demonstration readiness is separate from production readiness. Image-security, hosted CI, off-host acceptance, licensed data, and public-brand clearance retain their existing requirements. Production remains NO-GO.
