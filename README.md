
# Cadrisyn

Cadrisyn is the temporary working name for a private daily-market research workspace. The new Next.js interface uses a Django session API. Existing Streamlit, forecasting, portfolio, derivatives, RL, and reporting code remains in the repository as research functionality.

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

Set `CADRISYN_MARKET_DATA_ENABLED=true` in the launching shell only for permitted personal research with Yahoo daily history through yfinance. This optional mode has no guaranteed delay or redistribution entitlement. Provider failures remain unavailable. They never substitute demonstration data. No paid service or external deployment is configured.

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

Browser acceptance uses the running local API. Start it separately with `scripts/dev.py --api-only`. See [the frontend guide](web/README.md), [implementation status](docs/implementation/STATUS.md), and [operations instructions](docs/implementation/OPERATIONS.md) for results, remaining gates, and container configuration.

## Open the preserved research tools

```powershell
.venv/Scripts/python.exe scripts/legacy.py
```

This optional launcher uses the existing `backend/venv`, clones the original database to `.local/legacy.sqlite3` once, and starts the staff-protected research API on port 8001 and Streamlit on port 8501. Its separate generated credentials stay in `.local/research-credentials.json`. Provider-dependent paths require their existing environment configuration. The new frontend does not publish these unverified calculations.

The experimental FastAPI agent scaffold has its original dependency list in `agents/requirements.txt`. It is outside workspace startup. The supported workspace and optional research dependency profiles are separate under `backend/`.

The [product blueprint](docs/rebrand/README.md) records design and architecture decisions. Cadrisyn has no trademark clearance, registered domain, certification, or finalized public identity.
