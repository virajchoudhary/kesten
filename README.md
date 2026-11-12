
# Kerquant

Kerquant is a local financial analysis terminal built with Next.js, Django, and Python. Its supported portfolio demonstration covers daily chart analysis, private watchlists, reproducible synthetic baseline research, and account security. Historical forecasting qualification and production release remain blocked. Original ML, portfolio, derivatives, RL, Streamlit, and reporting code is preserved separately.

The name remains configurable through `NEXT_PUBLIC_PRODUCT_NAME` and `NEXT_PUBLIC_PRODUCT_SHORT_NAME`. Existing package, environment, database, and repository identifiers remain unchanged. Public branding is not legally cleared; see [the identity record](docs/design/kerquant/IDENTITY.md).

Start with the [portfolio demonstration guide](docs/PORTFOLIO.md). The [completion record](docs/implementation/PORTFOLIO-COMPLETION.md) separates current verification from historical infrastructure evidence. Production remains **NO-GO** until security and release gates pass.

## Start the local workspace

Use Python 3.12 and Node 22.12 or later in the Node 22 LTS family. The setup creates a separate `.venv`. It does not replace `backend/venv` or the original `backend/db.sqlite3`.

On Windows, run these commands from the repository root.

```powershell
./scripts/setup.ps1
.venv/Scripts/python.exe scripts/demo.py
```

On Linux or macOS, run these commands.

```sh
sh scripts/setup.sh
.venv/bin/python scripts/demo.py
```

Run setup once to install the locked dependencies. On later starts, run only `scripts/demo.py`. Open [the workspace](http://127.0.0.1:3000/app/markets) and use the generated credentials in `.local/portfolio-demo/credentials.json`. This command explicitly creates a private synthetic account, a starter watchlist, and saved one/five-session baseline evaluations. Restarts preserve the password, saved results, and watchlist edits. The API health endpoint is [localhost:8000/health](http://127.0.0.1:8000/health/). Stop the launcher with Ctrl+C.

Demo data lives in `.local/portfolio-demo/workspace.sqlite3`. The launcher ignores inherited production storage and disables external market providers. It refuses unrelated directories and occupied ports. For an optimized local preview, add `--build`; this builds locally and does not deploy. The original `scripts/dev.py` workflow and its `.local/cadrisyn.sqlite3` database remain available for existing development work.

## Data and capabilities

The default chart is an explicitly synthetic demonstration dataset. It contains no observed stock prices or empirical performance results. Search covers 20 curated US stocks. Daily OHLCV, SMA20/50, Wilder RSI14, exact data tables and private watchlists use the versioned API. Display controls add alternate chart types/scales, configurable EMA/Bollinger studies, common-session indexed comparison, measurement, temporary price levels and browser-local display layouts. The integrated research dock preserves standalone research access and saved identities.

Set both `CADRISYN_MARKET_DATA_ENABLED=true` and `CADRISYN_YAHOO_PERSONAL_USE_ACKNOWLEDGED=true` only for permitted local personal research with Yahoo daily history through yfinance. The adapter is disabled outside development. No licensed live feed, guaranteed delay or redistribution entitlement is configured. Provider failures remain unavailable and never substitute demonstration data.

## Private forecast research

Open [research](http://127.0.0.1:3000/app/research) after starting the demo. The prepared fixture and both saved horizons are already available. The private workflow compares last-close and expanding historical-log-mean references, saves provenance and chronological evaluations, and supports exact replay.

The fixture is synthetic. No empirical forecasting performance, advanced ML model, prediction interval, or trading strategy is approved. Historical imports retain the staff, rights, and per-record availability/action gates. See [model dispositions](docs/implementation/PHASE3.md) and [the source investigation](docs/implementation/PHASE5-RESEARCH-SOURCES.md). The existing `scripts/research.py` commands target the original development workspace, not the portfolio demo.

## Run checks

```powershell
.venv/Scripts/python.exe scripts/check_backend.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_research_client.py
cd web
npm run build
npm run typecheck
npm run lint
npm test
```

For browser acceptance, use the [disposable portfolio test procedure](docs/PORTFOLIO.md#run-browser-acceptance). Do not run account-lifecycle tests against your own demo account or existing research workspace. The [frontend guide](web/README.md) covers the existing frontend commands; historical PostgreSQL/container evidence remains in the implementation records.

## Open the preserved research tools

```powershell
.venv/Scripts/python.exe scripts/legacy.py
```

This optional launcher uses the existing `backend/venv`, clones the original database to `.local/legacy.sqlite3` once, and starts the staff-protected research API on port 8001 and Streamlit on port 8501. Its separate generated credentials stay in `.local/research-credentials.json`. Provider-dependent paths require their existing environment configuration. The new frontend does not publish these unverified calculations.

The experimental FastAPI agent scaffold has its original dependency list in `agents/requirements.txt`. It is outside workspace startup. The supported workspace and optional research dependency profiles are separate under `backend/`.

The [product blueprint](docs/rebrand/README.md) records historical design and architecture decisions. Kerquant was selected for local use on 8 November 2026. The exact-name screen found no registered object for `kerquant.com`, `kerquant.app`, or `kerquant.in` in the queried RDAP registries, but domain availability and trademark clearance remain unverified. No domain purchase, repository rename, or public publication is authorized.
