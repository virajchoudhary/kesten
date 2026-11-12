# Kerquant portfolio completion

Assessment date: 13 November 2026. Base commit: `08a7dfa660e993ba39edbcfd036572f3c383c96f`, branch `codex/cadrisyn-foundation`.

Implementation commit: `97771fbc18d0b7822183b21f6ed30ac2cb4aa706`. The subsequent documentation commit contains this report, the portfolio guide, and sanitized evidence.

**Portfolio demonstration: GO for the frozen local synthetic scope below. Production: NO-GO.** This record does not establish empirical prediction performance, market-data rights, public-brand clearance, or deployment approval.

## Frozen supported scope

The finished demonstration is the existing Next.js terminal, Django API, daily chart analysis, private watchlists, synthetic baseline research, and account security. Original research tools remain preserved separately. No advanced model or new investment feature was added.

| User workflow | Verified behavior | Boundary |
| --- | --- | --- |
| Start and sign in | One launcher prepares a private marked workspace, applies migrations, creates an account, and starts both services. The complete launcher returned HTTP 200 for API health, sign-in, authenticated session, and private watchlist. Chromium opened Markets and Research with no page errors. | Loopback development configuration. No production server claim. |
| Market analysis | Search, symbol switching, daily candlesticks, OHLCV, SMA, RSI, EMA/Bollinger display studies, comparison, measurement, price levels, chart settings, exact tables, and local layouts. | Twenty curated instruments with synthetic prices by default. No intraday or trading functionality. |
| Watchlists | Private additions/removals, filtering, ordering, fast symbol changes, and instrument-to-research navigation. | An instrument without a private dataset shows an empty state. |
| Research | Private dataset selection, provenance inspection, one/five-session configuration, execution, chronological result inspection, baseline comparison, history, exact saved-run selection, JSON export, and deterministic replay. | Synthetic pipeline checks only. Exploratory rights evidence does not admit a dataset to point-in-time forecasting. |
| Account security | Sign-in/out, password change, session revocation, private-state clearing on account changes, operator-issued invitation, and password reset. | Invitation/reset tests use disposable accounts. No email delivery or public self-registration claim. |
| Responsive use | Desktop 1440×900 and 1920×1080, tablet 820 pixels, mobile 320–390 pixels, theme changes, mobile settings/history, and navigation. | Chromium verification. Other browser engines and physical touch devices were not tested here. |

## What changed in this closeout

- Added `scripts/demo.py` with dedicated `.local` storage, directory markers, private credentials, explicit synthetic seeding, repeatable saved baseline identities, free-port checks, and combined startup.
- Added disposable browser-fixture preparation with separate accounts per spec. This fixes shared-account rate-limit/state interference without changing application security limits. The terminal-depth test now adds NVDA explicitly before filtering for it.
- Fixed restart after an Account password change. The launcher reports that its initial password is stale and keeps the current password. It still refuses an absent/inactive account and never resets credentials.
- Updated the README, setup-command output, and [portfolio instructions](../PORTFOLIO.md). Existing development, legacy, and research commands retain their own stated database targets.
- Preserved all pre-existing dirty source/configuration files. No backend calculation, database schema, admission rule, security policy, or numerical engine changed.

## Current verification

Evidence is retained under [portfolio-completion-20261113](evidence/portfolio-completion-20261113/). Counts below describe executed checks, not production certification.

| Check | Result | Evidence |
| --- | --- | --- |
| Backend, migrations, API contract, configuration checks | 168 tests ran, 164 passed and 4 PostgreSQL-only concurrency tests skipped under SQLite. Migrations had no drift; OpenAPI matched. Deploy configuration check emitted the existing HSTS-preload warning and no errors. | [Backend summary](evidence/portfolio-completion-20261113/backend-summary.txt). Full local log remains in `.local/portfolio-completion-20261113-27b4e4ed/backend.txt`. |
| Frontend unit/component checks | 134 tests across 38 files passed. | [Frontend unit log](evidence/portfolio-completion-20261113/frontend-unit.txt). |
| TypeScript and ESLint | Passed. Independent reviewer also ran fresh non-incremental TypeScript, scoped ESLint, Python AST parsing, and diff checks. | [TypeScript](evidence/portfolio-completion-20261113/typecheck.txt), [lint](evidence/portfolio-completion-20261113/lint.txt), and [review](evidence/portfolio-completion-20261113/independent-review.md). |
| Optimized frontend build | Passed, including all 12 generated pages. | [Build log](evidence/portfolio-completion-20261113/build.txt). |
| Complete browser suite | 17 passed with one Chromium worker, zero retries, against the real isolated API and optimized frontend. Suites also contain explicit fault-injection cases. | [Browser log](evidence/portfolio-completion-20261113/browser-final.txt). |
| Demo/fixture/preservation regressions | 14 passed after the password-restart and clean-checkout test-setup fixes. Accounts, dataset/run identities, numerical results, and watchlist edits survive repeat preparation and password-change restart. | [Workflow log](evidence/portfolio-completion-20261113/workflow-tests.txt). |
| Password-restart regression | Failed before the fix because the changed password caused launcher exit 2. Passed after the fix; the database retains the changed password and the credentials file remains byte-identical. | [Failing-before log](evidence/portfolio-completion-20261113/password-restart-before.txt) and `tests/test_portfolio_demo.py`. |
| Full launcher integration | Both services served HTTP 200. Targeted Chromium sign-in, private watchlist, Markets, and Research checks passed with no page errors. | [HTTP receipt](evidence/portfolio-completion-20261113/launcher-http.json), [browser receipt](evidence/portfolio-completion-20261113/launcher-browser.txt), and [rerunnable check](evidence/portfolio-completion-20261113/verify-launcher.cjs). |
| Preservation | All 496 protected runtime files and 17 recorded research artifacts match original hashes. Original database and every pre-existing dirty file match this task's starting hashes. | [Preservation receipt](evidence/portfolio-completion-20261113/preservation.json). |

Initial browser acceptance exposed shared-fixture throttling and a watchlist setup assumption; isolated per-spec accounts and explicit setup resolved those failures. Restricted Windows execution also caused build-directory/temporary-directory permission errors and child-server/console startup failures. Normal approved local execution passed the affected checks. No application security gate was weakened.

The additional combined-launcher run could not use `markets.spec.ts` unchanged: its external-server mode checks `/health/` on a combined proxy, while the documented launcher uses separate API/frontend ports. The retained targeted check verifies those actual ports instead. This was a test-configuration mismatch; the full 17-scenario acceptance remains valid for its optimized-frontend configuration.

The Prove It Works principle led to both real Chromium acceptance and a separate full-launcher check. Model the Domain kept workspace identity and account state explicit; password changes do not trigger recovery or reset.

## Visual acceptance

The parent inspected actual Chromium captures, including chart scale/viewport use, toolbar grouping, watchlist density, responsive chart panes, research identity/provenance, baseline units, and light/dark contrast. These are rendered product captures, not design mockups.

| Capture | Review |
| --- | --- |
| [Markets, 1440×900 dark](evidence/portfolio-completion-20261113/markets-1440-dark.png) | Dominant chart, compact controls, visible scales/volume/RSI, and persistent demo attribution. |
| [Markets, 1920×1080 light](evidence/portfolio-completion-20261113/markets-1920-light.png) | Chart fills available space; right watchlist and detail panel remain aligned. |
| [Markets, 390-pixel dark](evidence/portfolio-completion-20261113/markets-390-dark.png) | Stacked controls and usable chart panes; desktop watchlist collapses. Study readout is clipped to its chart viewport on narrow screens, while full values remain available through data/indicator controls. |
| [Research, desktop](evidence/portfolio-completion-20261113/research-desktop.png) | Saved identities, replay status, target dates, partitions, charts, and benchmark units are visible with explicit synthetic limitations. |
| [Research baseline comparison, mobile light](evidence/portfolio-completion-20261113/research-mobile-light.png) | Legible comparative table, test/validation controls, and stacked private-history filters. |

The interface is accepted for this portfolio scope. It is not claimed to match the feature breadth of TradingView or Koyfin.

## Retained infrastructure evidence

This closeout did not rebuild images, repeat recovery audits, or reconfigure PostgreSQL. No relevant infrastructure or backend numerical code changed.

The preceding [research-usability PostgreSQL receipt](evidence/research-usability-20261112/postgres-qualification.json) records 85 research tests, zero skips, and 46 migration steps on an isolated PostgreSQL 17.11 instance. The [selected qualification](evidence/research-usability-20261112/postgres-selected-qualification.txt) records 12 PostgreSQL/intake checks. These are dated prior receipts, not fresh results from this closeout. Earlier container, backup/restore, and production-profile records retain their own exact source/image boundaries.

## Restricted capabilities and release blockers

1. **Image security remains failed.** The [recorded five-image investigation](IMAGE-SECURITY-ROOTCAUSE.md) retains all 431 raw matches and the unchanged medium-severity policy. No fresh scan, upstream-fix verification, or security PASS occurred here.
2. **Hosted CI and off-host production acceptance remain unverified.** Local tests and a successful build do not establish either requirement. No push or deployment occurred.
3. **No qualified historical archive or empirical model result.** The [source investigation](PHASE5-RESEARCH-SOURCES.md) and [market-data access record](PHASE51-MARKET-DATA.md) retain their dated findings. The pre-existing local acquisition drafts under `docs/implementation/acquisition-20261112/` remain untouched and uncommitted. The free-source paths do not establish complete historical price/action availability and the required storage/display rights for this demonstration. No acquisition or import was attempted.
4. **No model promotion.** ARIMA/GARCH, BiLSTM/HPO, mean fallback, RL, portfolio optimization, options, and legacy reporting remain preserved research candidates/tools. Their presence is not an out-of-sample validation claim.
5. **Public branding and publication need separate clearance/approval.** Source, credentials, licensed datasets, and private research must not be published together.
6. **Setup portability is bounded.** Windows launcher execution was verified with existing locked dependencies. Setup scripts use the locked requirements, but no clean-machine installation or macOS/Linux startup was rerun.

## Demonstrate and maintain

Follow [the portfolio guide](../PORTFOLIO.md) for the single-command start, optimized local preview, disposable browser acceptance, credentials, and preservation rules. Present the project as a financial-analysis terminal with reproducible synthetic research. Do not describe fixture metrics as market prediction accuracy.

The default entry points are `http://127.0.0.1:3000/app/markets`, `/app/research`, and `/app/account`, with API health at `http://127.0.0.1:8000/health/`. The closeout's separate presentation run used web port 3001 and API port 8002.

No push, merge, deployment, purchase, database replacement, protected-artifact deletion, or scientific promotion occurred.
