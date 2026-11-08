# Terminal implementation and verification

This work continues `codex/cadrisyn-foundation` from `2cf72c2`. It addresses the rejection of the previous UI. Phase 5 release engineering remains paused. Kesten is the user-selected local identity. Public clearance is unresolved; see [the identity and conflict record](KESTEN.md).

Read the [product comparison](PRODUCT-COMPARISON.md), [design system](DESIGN-SYSTEM.md), and [brand screen](BRAND-SHORTLIST.md). The comparison explains which professional-terminal patterns were adopted and which capabilities remain absent. No parity claim is made.

## Delivered behavior

- Four daily chart types, four price-scale modes, free/magnet crosshair, grid/volume/RSI/SMA switches, validated configurable EMA and Bollinger studies.
- Common-session indexed comparison with provenance/currency checks, exclusion counts and per-instrument as-of/freshness disclosure. Comparison remains Demo when its inputs are synthetic.
- Keyboard and pointer close-to-close measurement, instrument/data-mode-scoped horizontal levels, time navigation and a reset that restores price autoscaling as well as time extent.
- Browser-local versioned display settings and eight named layouts. These contain no prices, account credentials, dataset or run identities. Annotations stay in memory for the current session.
- A persistent chart with a pointer/keyboard-resizable research dock, explicit maximize/restore, account-private saved-run selection and evaluation setup. The inspector uses a compact context column beside research analytics; full research remains available. Dataset/run/model identities, source evidence and replay are retained.
- A dense saved-run table on desktop, stacked records with accessible actions on phones, exact evaluation-window CSV for synthetic fixtures, and target-window/pinning controls. Historical CSV and JSON redistribution remain blocked.
- Searchable private watchlist and a selected snapshot sourced only from fetched OHLCV. No unloaded watchlist quote is fabricated.

## Run locally

Use the existing environment and launchers. No database conversion or container change is needed for these frontend changes.

```powershell
# Repository root; creates/uses the separate development store, never backend/db.sqlite3.
.venv/Scripts/python.exe scripts/dev.py
```

Open [markets](http://127.0.0.1:3000/app/markets), [research](http://127.0.0.1:3000/app/research), [account security](http://127.0.0.1:3000/app/account), [methodology](http://127.0.0.1:3000/methodology), or [data policy](http://127.0.0.1:3000/data). Read existing local credentials from the ignored credential file; never commit or print them. Do not seed, migrate or test against the original database.

The review preview uses a further isolated `.local/terminal-depth/preview.sqlite3`, not the normal development store. Its ignored `serve-api.py` and fixture helpers create synthetic data and disposable review accounts. Its credentials are in `.local/terminal-depth/credentials.json`. No preview credential or database belongs in Git. Existing PostgreSQL roles, volumes, backup archives and recovery commands are unchanged; their prior qualification is not a new test result from this UI task.

The review research fixture belongs to `xnys-jpm`. Search for **JPM**, open **Research**, choose **New eval**, then select a one- or five-session horizon and run the evaluation. Other instruments correctly show no matching private dataset until one is imported or explicitly seeded. Chart Demo snapshots and immutable research fixtures remain separate datasets even for the same instrument.

For a production-mode local frontend, stop the existing frontend first, then run:

```powershell
cd web
$env:DJANGO_API_URL='http://127.0.0.1:8000'
npm run build
npm start -- --hostname 127.0.0.1
```

For independent verification:

```powershell
# Repository root.
.venv/Scripts/python.exe scripts/check_backend.py
# Frontend directory.
npm test
npm run typecheck
npm run lint
npm run build
# Set CADRISYN_E2E_FIXTURE_DIR to a prepared disposable fixture directory.
# Use the existing operations guide to prepare source or PostgreSQL fixtures safely.
$env:PLAYWRIGHT_EXTERNAL_SERVER='0'
$env:TERMINAL_EVIDENCE_DIR='C:\stock price predictor\.local\terminal-depth\browser'
npm run test:e2e:terminal
```

Source-profile browser checks use the API health endpoint on port 8000; the existing frontend is reused. `PLAYWRIGHT_EXTERNAL_SERVER=1` instead selects the container-profile health default on port 8080 and must not be used for this source preview.

The browser runner paces suites by 60 seconds to preserve API throttles. It now includes `terminal-depth.spec.ts` and optionally copies each suite's screenshots before Playwright replaces its output directory. The depth scenario expects the preceding terminal scenario to have created a synthetic saved run in the same disposable account. Do not disable security limits to accelerate acceptance.

## Evidence and limitations

The current verification ledger and review dispositions are in [VERIFICATION.md](VERIFICATION.md). Raw local logs and full route captures are retained under `.local/terminal-depth/`; selected screenshots are included with this documentation after validation. Before images deliberately show the rejected historical interface and its former wordmark.

The work does not qualify historical data, establish empirical prediction accuracy, approve legacy models, create confidence intervals or add trading. It does not renew PostgreSQL/container/recovery certification, hosted CI, deployment or paid-provider approval. Production data rights, operational/security release gates, non-Chromium browsers and assistive-technology testing remain separate requirements. Only the listed local checks were executed.
