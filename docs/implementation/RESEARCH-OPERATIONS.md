# Run private forecast research

This phase supports fixed reference methods over frozen datasets. The supplied 180-session fixture is synthetic and establishes no empirical forecasting performance. No advanced ML model, interval, strategy or paid provider is enabled.

## Start and seed the local workspace

Use the existing Python 3.12 workspace environment and Node 22 setup. From the repository root:

```powershell
.venv/Scripts/python.exe scripts/dev.py
```

The launcher migrates `.local/cadrisyn.sqlite3`, preserves an existing analyst password, and starts API 8000 and frontend 3000. In another shell, explicitly seed the test fixture:

```powershell
.venv/Scripts/python.exe scripts/research.py seed --owner analyst
```

Open `http://127.0.0.1:3000/app/research`. Sign in using ignored `.local/credentials.json`, select `Synthetic pipeline fixture`, choose one or five exchange sessions, and run the evaluation. The result is saved privately. Its link and recent-run history survive reload. Existing chart data and watchlists are separate.

To reproduce the production-built source preview, start `scripts/dev.py --api-only` in one shell, then run `npm run build` and `npm start` in `web/`. The start wrapper defaults to loopback. Stop an existing preview before rebuilding its standalone files on Windows. Restart the API after scientific code or environment changes. Source-mode startup does not start training, Celery or cloud services.

## Import historical data

The developer wrapper always targets the isolated local workspace. A separately configured database/container uses the same Django management commands directly with its actual environment. It cannot currently be exercised here because Docker's host startup is blocked.

```powershell
.venv/Scripts/python.exe scripts/research.py import --file .local/approved-history.json --owner analyst --approved-by OPERATOR --acknowledge-terms
```

`OPERATOR` must be an existing active staff account. The acknowledgement covers reviewed storage, private-research and transfer rights. The system records the approving account and import time. Neither the flag nor a source label proves licensing or historical truth; retain the supporting archive and terms. No fetcher downloads data automatically. Importing identical normalized content for the same owner returns the existing version instead of overwriting it. A change creates another version.

The UTF-8 JSON manifest has these exact fields:

| Field | Required meaning |
| --- | --- |
| `schema_version` | Integer 1 |
| `name`, `instrument_id` | Bounded display name and a supported curated XNYS/USD instrument ID |
| `data_kind` | `historical` or `synthetic_fixture`; known synthetic markers cannot be labelled historical |
| `source_id`, `license_reference`, `availability_evidence` | Source identity, usage terms/reference, and archived evidence supporting the supplied availability timestamps |
| `adjustment_basis` | `raw_with_causal_splits`; retrospectively adjusted closes are not accepted |
| `calendar` | `XNYS` in this initial engine |
| `corporate_actions_complete` | Boolean true; unknown actions are rejected |
| `issue_lag_minutes` | Integer 60, the fixed close-origin issue cutoff |
| `observations` | 120 to 1500 ordered contiguous exchange sessions with no imputation |

Every observation has exactly `session`, `close`, `available_at`, `split_ratio`, and `cash_dividend`. `session` is an ISO session date. Close is finite and positive. Availability is an aware timestamp for the complete price/action record, at or after its exchange close and no later than close plus 60 minutes, before the next session opens. The issue cutoff itself must already have elapsed at import. Availability must increase strictly. A retrieval timestamp alone is insufficient evidence of historical availability.

The split ratio is new shares per old share, positive and finite; it is 1 at the first observation because the initial unit is defined after that close. Later splits enter only from their effective session onward. Cash dividends are finite/nonnegative metadata and are excluded from the price-only target and simple return. Values are USD per initial share, not necessarily current quoted-share prices or total returns. Gaps, duplicates, non-session dates, late publications, non-finite values, unknown fields and incompatible bases are rejected. The input file is capped at 2 MB.

## Replay and verify

Copy the saved run UUID from the result header or private run URL:

```powershell
.venv/Scripts/python.exe scripts/research.py replay --run RUN_UUID --owner analyst
.venv/Scripts/python.exe scripts/smoke_api.py --include-research --concurrent-sign-in
```

Replay recomputes without overwriting stored results and checks the dataset, engine source, dependency lock, runtime versions and exact result hash. A mismatch exits unsuccessfully and retains the original evidence. Earlier development fixture runs remain saved under their original source hashes; use their matching code/environment for exact replay. The smoke command intentionally saves a new synthetic run, preserves the existing watchlist, and checks two synchronized sign-ins plus private-data behavior. It accepts only explicit loopback origins.

Run `.venv/Scripts/python.exe scripts/check_backend.py` and `backend/venv/Scripts/python.exe scripts/check_research.py`. In `web/`, run `npm run build`, `npm run typecheck`, `npm run lint`, and `npm test`. For the browser gate, prepare fresh disposable fixtures with `scripts/prepare_browser_fixture.py`, start the API separately, set `PLAYWRIGHT_PRODUCTION=1`, and run `npm run test:e2e`. Set `PLAYWRIGHT_BROWSERS_PATH` to the existing installation or install Chromium with Playwright first. One-use lifecycle fixture files must be refreshed for each full browser run.

Research creation accepts JSON numeric horizons 1 or 5, not arbitrary models or client bars. The request key is a UUID and is unique per owner. Reuse with identical inputs returns the stored result; different inputs return 409. Computation is synchronous and bounded. Failure creates no partial saved result, so retry with the same key. Completed results and input versions are durable; private list/detail endpoints never return another user's records. There is no upload, sharing, deletion, training or execution endpoint in this slice.

## Recovery and remaining gates

Use [foundation recovery](FOUNDATION-OPERATIONS.md) and [the backup CLI](../../scripts/ops/README.md). Never target the original `backend/db.sqlite3`. New research datasets and completed results are included in workspace transfer; the source must be schema-migrated and the PostgreSQL destination empty. Imported rights acknowledgement includes transfer; review the destination purpose before any cutover. No active account links or sessions cross that transfer. Actual Phase-three PostgreSQL transfer/concurrency/container checks remain blocked on this host and must run before release.

The phase restored the current SQLite research store into a new database, reproduced a current-code result, and verified fresh sign-in and private access. This does not establish PostgreSQL behavior, off-host backup protection, security-state cutover, RPO/RTO, or cross-platform numerical tolerance. Retain original databases, manifests and artifacts. Docker recovery must preserve its existing volumes; do not reset or delete storage to force this gate green.
