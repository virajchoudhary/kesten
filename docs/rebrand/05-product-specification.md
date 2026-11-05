# Product scope and interaction specification

Status: proposed product behavior. Existing feature status is recorded in [the repository audit](01-repository-audit.md). A route in this specification is not a claim that the route exists today.

## Product thesis and audience

Give an analyst one continuous path from an instrument's observed history to a tested hypothesis and a saved research decision. The product combines charting, forecasts, allocation scenarios, research, backtests, and derivatives through shared instruments, dated data, and reproducible runs.

The initial audience is a technically literate independent analyst or a small research team. They need fewer context switches between a chart, a Python experiment, and a report. Large trading desks, advisers managing client suitability, high-frequency traders, and brokerage execution are outside the first release. Institutional software quality is the benchmark, not a certification or a claim of institutional adoption.

The primary task is `Select an instrument, inspect the evidence, save a view`. Secondary tasks are `Compare a hypothesis against a baseline` and `Compare allocations under explicit constraints`. Session time, clicks, and output counts are poor substitutes for a correct, understandable result.

The owner has not set a jurisdiction, commercial model, data budget, or legal entity. Working assumptions are an invite-only research preview, English UI, US-listed USD equities with daily bars, no order execution, and no paid subscriptions in release one. India and INR are a planned expansion because the existing code supports Indian symbols. Mixed-currency optimization is not silently enabled.

## Product boundaries and first release

R1 contains sign-in, instrument search over a small curated universe, daily historical charting, a persistent watchlist, a source/freshness inspector, saved private research notes, and one saved next-session last-close baseline with its explicit horizon and methodology. A verified model artifact may accompany the baseline in P1 only after the quantitative gate passes. The UI calls the baseline by its method and does not claim an ML forecast.

The deployable demo variant uses deterministic synthetic fixtures with an unmistakable Demo data label on every output and export. The market-data variant requires an approved EOD display and storage license. A private preview is not an exemption from licensing. No public deployment is authorized by this package.

Portfolios, research assistance, full backtesting, derivatives, live feeds, alerting, and team collaboration are staged releases. Do not show disabled navigation tabs for them in R1. A public roadmap may describe proposed capabilities with clear status. Avoid marketing a future tool as an available feature.

## Information architecture

Public navigation is Product, Methodology, and Data. Pricing waits for validated entitlements and an approved business model. The app navigation grows from Markets and Research to Portfolios, Backtests, and Derivatives as each is released. Runs are a shared object reachable from any module.

| Route | User goal | Primary content and actions | Key states and release |
| --- | --- | --- | --- |
| `/` | Understand the product and enter | Selected brand, honest product image, short capability statement, Open workspace or Sign in | Demo preview labels; no fabricated customer logos or return metrics. R1 |
| `/methodology` | Understand how a result is produced | Data basis, horizons, baseline, validation policy, model release status | Explicit unknowns and version history. R1 |
| `/data` | Understand coverage and freshness | Instrument universe, exchanges, provider, EOD/delay labels, outage status, license-limited uses | Provider degraded, coverage absent, demo. R1 |
| `/sign-in` | Access private work | Email/password for invited users, reset flow, session status | Invalid credentials, throttled, expired reset, MFA if enabled. R1 |
| `/app/markets` | Resume research | Last selected instrument or search, watchlist, chart, evidence inspector | First visit, no selection, stale bars, entitlement denied, API unavailable. R1 |
| `/app/markets/[instrumentId]` | Inspect one instrument | Exchange-qualified identity, OHLCV, range, price basis, forecast/baseline panel, Save note | Symbol change, no history, gaps, model not approved. R1 |
| `/app/research` | Find saved work | Private notes and saved instrument views, search and sort | Empty, save failure, no access. R1 |
| `/app/research/[noteId]` | Record a view and its evidence | Title, plain text or sanitized Markdown, linked instrument and immutable run, saved timestamp | Dirty, saving, saved, conflict, read-only. R1 |
| `/app/runs/[runId]` | Inspect or reproduce an analysis | Stage, input snapshot, assumptions, artifact IDs, outputs, limitations | Queued, running, cancellation, failed, expired artifact. R1 baseline; P1 other job types |
| `/app/forecasts` | Compare model evidence | Instrument/horizon selector, model and baseline comparison, evaluation card, archived runs | Insufficient data, unapproved artifact, no evaluation. P1 |
| `/app/portfolios` | Find saved scenario portfolios | Name, base currency, asset count, last run, Create scenario | No portfolios, stale run, ownership denied. P1 |
| `/app/portfolios/[id]` | Compare allocations | Weights, expected/realized fields, objective and constraints, exposure, baseline allocation, run history | Infeasible, excluded instrument, FX unavailable, solver failure. P1 |
| `/app/backtests` | Run a reproducible experiment | Strategy, universe, train/validation/test ranges, costs, benchmark, job submission | Invalid chronology, insufficient history, too large, cancellation. P1 |
| `/app/derivatives` | Explore theoretical option scenarios | European option calculator, explicit units, dividends, expiry, price/Greeks/payoff; licensed chain later | Invalid finite inputs, expiry, no IV solution, simulated chain. P1 calculator; P2 chain/SABR |
| `/app/settings` | Manage account and workspace | Theme, timezone, session revocation, data permissions, export/delete request | Unsaved, permission change, session expiry. R1 minimal |
| `/privacy`, `/terms`, `/risk` | Understand use and limits | Owner-approved policies, retention, data rights, research scope | Effective date and policy version. Required before external access |

Use stable instrument IDs in links, not a bare ticker that can be reused after a corporate event. Search aliases include provider symbols, but the selected result exposes venue and currency. The same instrument, data cutoff, and run identity carry between pages.

## Core journeys and objective outcomes

### Inspect and save an instrument

1. Sign in, then search by company or symbol.
2. Select the exchange-qualified result. The chart and header show the same instrument and currency.
3. Change the visible range, inspect a bar, and open the data table.
4. Open evidence. Read source, last bar, adjustment basis, and EOD or demo status.
5. Save a note linked to that instrument and, if present, the exact forecast run.
6. Reload and reopen the saved view. The note remains private and the linked historical run has not changed.

Acceptance includes keyboard-only completion, an expired-session interruption that preserves the draft, a failed save that remains recoverable, and no old overlay flashing under a new symbol. A five-person usability study is proposed after prototype approval. The target is at least four participants completing this task without moderator intervention; no result is claimed today.

### Review a forecast

Select a horizon expressed in exchange sessions. Show origin close, target session, adjusted/unadjusted basis, method, model version if any, and data snapshot. Compare the estimate with a naive last-close or historical-mean baseline. Open the evaluation card to see locked dates, sample count, error measures, baseline differences, and limitations.

An unapproved model produces `No approved model`, not a fallback labelled as an LSTM. Intervals appear only if their construction and empirical coverage are verified. A historical forecast cannot consume news or model tuning from after its origin. No Buy/Sell action is derived from a point estimate in R1.

### Compare portfolio scenarios

Create a same-currency hypothetical allocation. Choose objective, asset bounds, cash allowance, rebalance schedule, costs, and data period. Review excluded instruments before submitting. Compare results with equal-weight and the starting allocation. Inspect feasibility, concentration, turnover, and expected versus realized values. Save the run without modifying a real account.

A risk slider, if retained, displays its actual mapping between objectives and constraints. It is not an assessment of personal suitability. No invisible optimizer substitution is allowed. A fallback result has a distinct method and reason.

### Test a hypothesis

Choose a versioned strategy from a fixed catalog, not arbitrary executable code. Lock the training, validation, and test windows. Show signal time, execution time, fees, slippage, dividend handling, and benchmark. Submit a bounded job and continue working. The run survives refresh, supports cancellation, and exposes an immutable trade ledger and reproducibility manifest.

Changing inputs creates a new run. The old result never updates under the same ID. Runs with data leakage, mismatched horizons, or incomplete costs cannot present a Verified badge.

### Explore derivatives

Start with a theoretical European option scenario. Enter spot, strike, expiry, continuously compounded annual rate, dividend yield, and annualized volatility. Show model price, Greeks with units, and payoff distinct from price. A manually entered volatility is an assumption. A derived historical volatility is an estimate, not a market IV.

For future chains, show source and quote time per contract, exercise style, multiplier, expiry convention, and licensing. Simulated chains occupy an explicit Demo context and never replace unavailable market quotes automatically. American options must not be priced or described as exactly valued by a European BSM engine.

## State model shared across modules

| State | Required behavior |
| --- | --- |
| Initial / empty | Explain the missing object through one action, such as Add instrument. Do not fill the screen with invented values |
| Loading | Keep stable panel geometry. Announce loading once. Do not display old instrument data as current |
| Ready | Show units, source, as-of time, and method where they affect interpretation |
| Partial | Render valid panels, name missing fields, and expose retry for the failed portion |
| Stale | Preserve usable data with timestamp and stale label; invalidate calculations that require a newer snapshot |
| Market closed | Distinguish a scheduled closed session from an unexpected missing daily bar |
| Unavailable | State whether coverage, license, insufficient history, provider, or model approval is missing |
| Offline | Preserve unsaved text locally for the session; do not queue financial jobs silently |
| Validation error | Mark fields, keep values, focus an error summary, and provide a correction |
| Unauthorized / forbidden | Reauthenticate or explain access. Never reveal another user's object through error details |
| Job failed | Show safe error code, stage, run ID, and retry availability. Never include provider tokens or a stack trace |
| Cancelled | Keep manifest and partial diagnostic status. Do not call a partial output successful |
| Unsaved / saving / conflict | Keep the user's draft; prevent last-write-wins loss using a revision precondition |

Freshness and job status are independent. A successful run can use stale data. A model can be technically available but unapproved. These distinctions must survive the API and UI rather than collapsing into one green dot.

## Responsive, accessibility, and content rules

The [design system](04-design-system.md) owns exact dimensions, theme tokens, and accessibility criteria. The app defaults to the user's system theme, persists an explicit choice, and avoids a flash of the opposite theme. Mobile uses a single pane, with chart/table and evidence reachable without drag gestures.

Money is formatted from instrument currency metadata, not ticker suffix guesses. Show percentage points, returns, decimal rates, annualization basis, and sample units consistently. Round for display only. Missing values render as `Unavailable` with a reason, never zero. Distinguish expected, simulated, observed, and backtested results in labels and exports.

Use content that explains the decision at hand. Keep marketing taglines out of working panels. Methodology details belong in evidence drawers. Essential simulation, staleness, licensing, and model-risk information stays adjacent to the result.

## Product evidence after launch

Proposed measures are successful completion of the inspect/save journey, saved research reopened, forecast-evidence views, failed-job rate, stale-data exposure, and support cases caused by ambiguity. Collect aggregate event counts without note contents or portfolio values. Establish a baseline during the preview before setting growth targets. Do not invent retention, accuracy, assets-under-analysis, or customer adoption figures.
