# Run the portfolio demonstration

Use Python 3.12 and Node 22 LTS version 22.12 or later. From the repository root, run `scripts/setup.ps1` on Windows or `sh scripts/setup.sh` on Linux/macOS. Setup installs the pinned backend requirements and frontend lock.

## Start

```powershell
.venv/Scripts/python.exe scripts/demo.py
```

Use `.venv/bin/python` on Linux/macOS. Open `http://127.0.0.1:3000/app/markets`. Read the initial credentials from `.local/portfolio-demo/credentials.json`; never publish or screenshot them. API health is `http://127.0.0.1:8000/health/`.

The launcher creates a private marked directory, applies migrations, prepares a synthetic account/watchlist/dataset, and saves both baseline horizons. It disables external market providers and legacy scheduling. Existing personal databases are not targets.

Stop with Ctrl+C. Restart preserves your current password, saved identities, results, and watchlist edits. If you change your password in Account, use that password thereafter. The initial credentials file stays unchanged, and the launcher reports that it is stale.

For an optimized local frontend, stop the preview and run `scripts/demo.py --build`. This builds locally and starts a loopback development API. It does not deploy.

If ports are occupied, use `--web-port 3001 --api-port 8002`. An occupied port or an unmarked existing directory is refused. `--directory .local/another-demo` creates a separate workspace.

## Present the product

1. Sign in, search instruments, and switch symbols using the private watchlist.
2. Inspect daily candles, exact OHLCV, volume, SMA, RSI, chart studies/settings, and comparison/measurement tools.
3. Open JPM research from its watchlist link, or open the standalone Research route. An instrument without a private dataset has an empty state.
4. Inspect provenance, choose a one/five-session horizon, and run the synthetic evaluation.
5. Compare baselines, inspect forecast/walk-forward/error paths and chronological periods, reopen saved results, export exact synthetic JSON, and verify replay.
6. Open Account to change a password or revoke other sessions. Demonstrate sign-out and private-route authentication.
7. Show mobile navigation and both themes. Data and Methodology state the calculation and data limits.

Describe errors as synthetic pipeline results. Do not describe them as market accuracy, returns, confidence intervals, or financial advice.

## Run disposable Chromium acceptance

Use a new directory for every full lifecycle run. Invitation/reset tests consume one-use tokens and mutate disposable accounts.

```powershell
.venv/Scripts/python.exe scripts/demo.py --directory .local/browser-acceptance --prepare-only --browser-fixtures
.venv/Scripts/python.exe scripts/demo.py --directory .local/browser-acceptance --api-only
```

Keep the API running. In another terminal from `web/`:

```powershell
$env:CADRISYN_E2E_FIXTURE_DIR = (Resolve-Path ../.local/browser-acceptance).Path
$env:DJANGO_API_URL = 'http://127.0.0.1:8000'
$env:CADRISYN_WEB_RELEASE_PROFILE = 'development'
$env:PLAYWRIGHT_PRODUCTION = '1'
npx playwright install chromium
npm run build
npx playwright test --workers=1
```

Clear inherited `PLAYWRIGHT_EXTERNAL_SERVER` and `PLAYWRIGHT_BASE_URL` settings that select another server. Tests use separate accounts per spec; security rate limits remain enabled. Do not target retained research or personal demo accounts.

On Linux/macOS, use the same preparation/start commands with `.venv/bin/python`, and export these environment variables with your shell's syntax. Hosted CI uses Linux with browser dependencies installed through Playwright.

## Preserve and recover

Keep `.local` private. Do not commit databases, credentials, certificates, or downloaded market data. A disabled or absent demo account stops preparation; the launcher never resets it.

Operational scripts under `scripts/ops/` retain backup/restore and release checks for their stated environments. Restoring a production database or deploying requires separately authorized infrastructure and verification. See [architecture](ARCHITECTURE.md) and [publication limits](PUBLICATION.md).
