
# Cadrisyn

Cadrisyn is the temporary working name for a private daily-market research workspace. The new Next.js interface uses a Django session API. Existing Streamlit, forecasting, portfolio, derivatives, RL, and reporting code remains in the repository as research functionality.

The foundation includes closed-registration account lifecycle, revocable sessions, restricted PostgreSQL roles, local containers, source-policy safeguards, and backup/restore tooling. See [current implementation status](docs/implementation/STATUS.md) and [Phase 4 operations](docs/implementation/PHASE4-OPERATIONS.md) for executed checks, working entry points, and remaining release gates.

## Start the local workspace

Use Python 3.12 and Node 22.12 or later in the Node 22 LTS family. The setup creates a separate `.venv`. It does not replace `backend/venv` or the original `backend/db.sqlite3`.

On Windows, run these commands from the repository root.

```powershell
./scripts/setup.ps1
.venv/Scripts/python.exe scripts/dev.py
```

On Linux or macOS, run these commands.

```sh
sh scripts/setup.sh
.venv/bin/python scripts/dev.py
```

Open [the workspace](http://127.0.0.1:3000/app/markets). Read the generated username and password from the ignored `.local/credentials.json`. The launcher creates the user only if absent and preserves its password on later starts. The API health endpoint is [localhost:8000/health](http://127.0.0.1:8000/health/). Stop the launcher with Ctrl+C to stop its owned services.

Development data lives in `.local/cadrisyn.sqlite3`. Development startup explicitly overrides inherited database and cache URLs. If the local credential file is lost, use Django's `changepassword analyst` with the same development environment rather than deleting the database.

## Data and capabilities

The default chart is an explicitly synthetic demonstration dataset. It contains no observed stock prices or performance results. Search covers 20 curated US stocks. Daily candles, SMA20, SMA50, Wilder RSI14, an accessible price table, and private watchlists use the versioned API.

Set both `CADRISYN_MARKET_DATA_ENABLED=true` and `CADRISYN_YAHOO_PERSONAL_USE_ACKNOWLEDGED=true` only for permitted local personal research with Yahoo daily history through yfinance. The adapter is disabled outside development. No licensed live feed, guaranteed delay or redistribution entitlement is configured. Provider failures remain unavailable and never substitute demonstration data.

## Private forecast research

Open [forecast research](http://127.0.0.1:3000/app/research) after starting the workspace. Explicitly install the reproducible development fixture with `.venv/Scripts/python.exe scripts/research.py seed --owner analyst`. The private workflow compares last-close and expanding historical-log-mean references at one or five exchange sessions, saves provenance and chronological evaluations, and supports exact replay.

The fixture is synthetic. No empirical forecasting performance, advanced ML model, prediction interval or trading strategy is approved. Historical imports require a staff operator, reviewed data rights and per-record availability/action evidence. See [research operations](docs/implementation/RESEARCH-OPERATIONS.md) and [model dispositions](docs/implementation/PHASE3.md). Phase 4 adds interactive analytics, filtered private history, guarded comparisons, exact replay, and synthetic exports. The retained packaged preview is [research on port 8086](http://127.0.0.1:8086/app/research). See [Phase 4 results](docs/implementation/PHASE4.md) and [container operations](docs/implementation/PHASE4-OPERATIONS.md). Historical-data qualification and the image-security release gate remain blocked.

## Run checks

```powershell
.venv/Scripts/python.exe scripts/check_backend.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_research_client.py
cd web
npm run build
npm run typecheck
npm run lint
npm test
npx playwright install chromium
npm run test:e2e
```

Browser acceptance uses the running local API. Prepare disposable source fixtures with `.venv/Scripts/python.exe scripts/prepare_browser_fixture.py`, then start the API separately with `scripts/dev.py --api-only`. For the PostgreSQL-backed preview, use the explicit fixture environment and browser commands in [Phase 4 operations](docs/implementation/PHASE4-OPERATIONS.md). See [the frontend guide](web/README.md) and [implementation status](docs/implementation/STATUS.md) for results and remaining gates.

## Open the preserved research tools

```powershell
.venv/Scripts/python.exe scripts/legacy.py
```

This optional launcher uses the existing `backend/venv`, clones the original database to `.local/legacy.sqlite3` once, and starts the staff-protected research API on port 8001 and Streamlit on port 8501. Its separate generated credentials stay in `.local/research-credentials.json`. Provider-dependent paths require their existing environment configuration. The new frontend does not publish these unverified calculations.

The experimental FastAPI agent scaffold has its original dependency list in `agents/requirements.txt`. It is outside workspace startup. The supported workspace and optional research dependency profiles are separate under `backend/`.

The [product blueprint](docs/rebrand/README.md) records design and architecture decisions. Cadrisyn has no trademark clearance, registered domain, certification, or finalized public identity.
