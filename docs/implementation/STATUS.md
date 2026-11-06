# Stabilization and initial workspace

Working name: Cadrisyn. Branch: `codex/cadrisyn-foundation`. The owner's follow-up authorizes this implementation milestone. Public naming, trademark clearance, domains, repository naming, deployment, and spending remain unapproved.

Readiness on 2026-11-06: the initial local workspace milestone passes acceptance. External production release is blocked by the gates below. The canonical two-service development launcher and the production-built frontend were exercised separately; neither is evidence of a deployed service.

## Scope delivered

The supported workspace has a separate Python 3.12 environment, Django 5.2.19, DRF 3.18.3, a versioned session API, curated instrument search, daily bars with explicit provenance, calculated SMA20/SMA50/Wilder RSI14, immutable bar-content identities, and account-owned watchlists. Authentication requires CSRF for login and mutations. Market responses validate OHLC consistency, sessions, order, and finite values.

The Next.js workspace provides authenticated stock search, daily candlestick/volume/RSI panes, SMA overlays, an accessible paginated data table, private watchlists, light/dark themes, and responsive layouts. Data and Methodology pages explain the available calculations and source limitations. The initial workspace milestone is separate from the full R1 release.

Legacy imports no longer initialize remote clients or download an embedding model during URL/view startup. Legacy APIs require the explicit research profile and a staff account. Request bounds and server-generated RL identifiers protect expensive and file-backed paths. The supported router excludes those endpoints by default. Existing quant algorithms remain research code with the blueprint's verification defects still open.

## Preservation

The original `backend/db.sqlite3` remains modified exactly as it was on entry. Its SHA-256 is `93745BFC1A3149A0F77BBCDD1A50F712195750879F3FB313728AB9811F99715B`. A read-only SQLite backup passed integrity checking. New workspace data uses `.local/cadrisyn.sqlite3`; research startup uses a backup copy at `.local/legacy.sqlite3`. Neither startup path targets the original file.

The hygiene commit removed 496 generated/runtime files from the Git index only. Their files remain on disk. The [preservation manifest](evidence/preserved-untracked-runtime-files.json) records paths and hashes; the [final check](evidence/preservation-final.json) confirms all 496 are present and unchanged. Four generated reporter metadata files were also untracked and retained locally. Existing virtual environments and scientific artifacts were preserved. The local reporter wheel now contains its actual modules rather than an empty package definition.

## Verification

| Check | Result and evidence |
| --- | --- |
| Original Django baseline | 23 tests, 2 failures and 2 errors. [Original output](evidence/baseline-django-tests.txt) |
| Corrected legacy tests | 23 pass, offline, using the preserved environment. Fixture signatures now accept `target_date`; optimizer and Black-Litterman assertions remain. [Output](evidence/research-final-checks.txt) |
| Workspace and security | 29 pass under the supported environment. Includes owner isolation, CSRF, no implicit demo fallback, hand-computed Wilder smoothing, calendar/indicator fixtures, import boundaries, exact-host settings, cache outages, safe errors, and JSON size limits. [Output](evidence/backend-final-checks.txt) |
| Migrations and schema | No pending model changes. Empty local workspace database migrated. OpenAPI schema validates and matches the committed contract. Same backend output above and [migration output](evidence/local-migration.txt) |
| HTTP workspace path | 12 checks pass on loopback, including login, search, chart data, private watchlist restoration, hostile origin denial, and logout. [Receipt](evidence/http-smoke.json) |
| Research startup | Cloned database API, anonymous denial, staff input validation, and Streamlit health pass. No providers or models invoked. [Receipt](evidence/research-startup.json) |
| Python dependencies | Workspace `pip check` passes. Initial DRF audit found 5 vulnerabilities; the patched workspace and pinned Linux additions report no known vulnerabilities. [Initial](evidence/pip-audit.json), [final](evidence/pip-audit-final.json), [runtime](evidence/pip-audit-runtime.json) |
| Frontend installation and dependencies | Clean `npm ci` succeeds. Initial audit found 11 development dependency advisories. Patched Vitest/Vite and the minimatch override produce zero known npm advisories. [Install](evidence/web-clean-install.txt), [initial audit](evidence/web-audit.txt), [final audit](evidence/web-audit-final.txt) |
| Frontend unit checks | 17 tests pass, covering API contracts, chart data conversion, runtime schemas, date formatting, watchlist request ordering, retry availability, and table accessibility. [Output](evidence/web-unit.txt) |
| Frontend static checks | TypeScript and ESLint pass. [Types](evidence/web-typecheck.txt), [lint](evidence/web-lint.txt) |
| Production frontend build | Optimized Next build succeeds. This does not validate containers or a production backend. [Output](evidence/web-build.txt) |
| Browser acceptance | Real Django session/search/bars/watchlist journey passes, including range/indicator changes, table agreement, both themes, responsive widths, source-fault recovery, and logout. Development and production-built frontend runs are recorded separately. [Development](evidence/web-browser.txt), [production frontend](evidence/web-browser-production.txt) |
| Production-settings probe | No errors. Optional warning `security.W021` remains because domain-dependent HSTS preload is disabled. This is not a production acceptance claim. [Output](evidence/backend-final-checks.txt) |
| Reporter packaging | Wheel contains 12 package files, including metrics, analysis, and optimization. Financial calculations unchanged. [Receipt](evidence/reporter-wheel.json) |
| Canonical startup | The unmodified documented launcher starts both services. Sign-in returns HTTP 200, all 12 API smoke checks pass, and the launcher storage-isolation test passes. [Receipt](evidence/local-startup.json) |
| Old diagnostics | Generic discovery fails on 7 import-time diagnostic scripts. These remain preserved, outside supported unittest selection. [Disposition](evidence/legacy-diagnostics-discovery.md) |

The old research environment still contains its pre-existing FastEmbed/NumPy incompatibility and invalid `~jango` distribution. It was not repaired in place. The revised research manifest omits the unused embedding dependency, uses the repository-local reporter, and aligns Celery/beat with Django 5.2. A full scientific Linux resolver/install is still required before advancing research tools into the product. The compatible Next lint preset still requires ESLint 9; its upstream support warning is documented in the frontend README. A trial of ESLint 10 exposed plugin peer conflicts and was reverted.

## Remaining release gates

PostgreSQL/container execution, image scanning and digest locks, backup/restore and rollback rehearsals, licensed market data, provider-success verification, invitation/reset/revocation flows, centralized observability and redaction, and measured cost/load budgets remain open. Manual screen-reader, 400% zoom, and broader browser coverage also remain open. Docker is unavailable in this environment. CI configuration is provided but has not run remotely. No deployment or purchase occurred.

The full roadmap also includes saved research notes and versioned baseline runs. Those are not part of this initial workspace milestone. Portfolio, forecasting, backtesting, options, RL, and reporting remain preserved research functionality, with no new performance or production-quality claim.

Next, rehearse the Linux/PostgreSQL build on an appropriate local host. Add invitation/session lifecycle and research notes before any public release, and introduce quantitative tools only after the corresponding [model verification gates](../rebrand/08-quantitative-verification.md) pass. Complete data-rights and identity decisions before external use. The [review record](REVIEW.md) distinguishes initial findings, corrections, and acceptance limits.

## Working entry points

Run `.venv/Scripts/python.exe scripts/dev.py` from the repository root on Windows. Open `http://127.0.0.1:3000/app/markets` and use the ignored `.local/credentials.json` account. API health is `http://127.0.0.1:8000/health/`. For production-mode frontend verification, start the API with `--api-only`, then run `npm run build` and `npm start` in `web/`.

The optional research launcher is `.venv/Scripts/python.exe scripts/legacy.py`. It serves the research API on port 8001 and Streamlit on port 8501 using the cloned database. Provider-dependent research and training are not part of the verified new workspace journey.

See [operations](OPERATIONS.md) for exact startup and verification commands.
