# Existing system audit

Discovery baseline: commit `af511b082814a19964bfeb60dbcdc7a0a93c1b00`, 5 November 2026. [baseline.json](baseline.json) records the initial inventory and database hash. `backend/db.sqlite3` was already modified. It is not a change made by this task.

This audit combines owning-source inspection, independent application and quant reviews, and bounded offline probes. It is not a penetration test, dependency vulnerability scan, full UI exercise, deployment rehearsal, or scientific model certification. Source references use repository-relative paths and one-based line numbers at this baseline.

## What exists

| Area | Actual implementation | Reuse decision |
| --- | --- | --- |
| Frontend | Streamlit, Plotly, page-specific HTML/CSS. Visible dashboard, portfolio, options, SWOT, and chat pages. Portfolio embeds allocator, BL, report, and backtest tabs | Preserve as a behavioral reference and research UI until accepted Next routes replace it |
| API | Django/DRF endpoints for forecasts, allocations, two BL workflows, SWOT, chat, HPO, RL, evolution, and two backtests | Retain Django; add validated versioned endpoints rather than rewriting all services |
| Forecasting | PyTorch bidirectional LSTM with technical indicators and log-return target, early stopping, historical-mean fallback, GA/HPO code | Retain as experimental research; repair leakage, horizons, evaluation, and artifact provenance before product claims |
| Classical baseline | ARIMA plus GARCH path, separate backtest endpoint | Preserve as a candidate baseline after conventions/coverage checks |
| Portfolios | PyPortfolioOpt-based inverse-volatility, min-variance, max-Sharpe blending; BL implementations; RL A2C/SAC/TD3 | Retain pure math and useful constraints. Reconcile method labels and BL paths. RL remains research-only |
| Derivatives | Local BSM/Greeks/IV functions, Streamlit SABR and volatility-surface analysis, simulated-chain fallback | Preserve BSM core with boundary/property tests. Gate SABR and market-chain claims separately |
| Reports | Local `quant_reporter` package, metrics, optimization, validation, Monte Carlo, Plotly and HTML reports | Preserve useful report structure and plots; correct metrics, data alignment, and unsupported fixed narrative |
| Jobs | Celery GA tasks/nightly schedule, plus request-time training and in-process RL daemon threads | Standardize on persistent Celery jobs after tests |
| Agent scaffold | FastAPI scheduler pushes Redis-list payloads, separate consumer prints a placeholder; Mongo memory helper | Preserve source but exclude from target deployment. Not a completed prediction service |
| Standalone RL | `decision/` PPO environments use generated random returns | Keep as explicitly synthetic experimentation; not historical performance evidence |

Owning sources include `backend/api/urls.py:8-23`, `frontend/pages/2_Portfolio.py:1742-1748`, `frontend/pages/3_Options_Analysis.py:181-186`, `agents/predictor/consumer.py:7-17`, and `decision/env.py:5-47`. Hidden backtest/evolution pages also exist under `frontend/pages/_hidden`; their files are not evidence that every path is exposed and working.

## Architecture and dependency findings

The active path is Streamlit calling Django through hardcoded localhost URLs, with Django importing a large mixed-service module. Data retrieval, model training, allocations, LLM calls, embeddings, and RL live together in `backend/api/ai_services.py`. The root requirements instead list FastAPI, Uvicorn, Redis, Motor, and Streamlit, so installing the root file does not install the main Django/quant application. `backend/requirements.txt` has many unbounded dependencies plus a few older exact pins. No tracked lockfile or Node frontend exists in the inspected inventory.

The Django application's custom models are `OptimizedHyperparams` and a shared `SearchedTicker` cache, not user-owned portfolios or watchlists. Django's built-in auth app is installed; this does not establish API access control or product account flows. See `backend/api/models.py:7-67` and `backend/quantvision/settings.py`.

The local `quant_reporter/setup.py` declares a package without dependencies, while backend requirements reference `quant-reporter`. A fresh build must explicitly select the local package rather than silently importing a different PyPI distribution or incidental current-directory module. The setup location/package discovery must be checked in a clean installation.

There are 628 tracked paths, of which 449 are under `frontend/venv`, and the README is two bytes. Tracked environment binaries, model ZIPs, progress files, scheduler state, log/debug pages, and Apple metadata add noise and portability risks. These counts come from `git ls-files`, not a measurement of active code. No cleanup was performed. Inventory rights, retention, reproducibility, and callers before removing anything.

The inspected host has a working backend virtual environment on Python 3.13.9. A separate base Python 3.12.5 has numerical packages but lacks Django/Streamlit. Neither environment proves that the requirements can reproduce a clean install. The frontend venv metadata references a different original path. Locking and validating a clean Linux environment is a deployment blocker.

Read-only package metadata found Django **5.0.14**, Celery 5.3.6, django-celery-beat 2.6.0, redis-py 5.0.1, PyTorch 2.10.0, PyPortfolioOpt 1.5.5, Riskfolio-Lib 7.2.1, and Streamlit 1.55.0 in that backend environment. The complete selected inventory is in [installed-package-versions.json](installed-package-versions.json). Django 5.0 is in the official [unsupported-release table](https://www.djangoproject.com/download/), so moving to a supported patched line is a release blocker. The metadata is an environment snapshot, not a lockfile, vulnerability scan, or proof that all installed packages are used.

## Findings that block external release

Severity is a product-release priority, not a CVSS score. `Source confirmed` means the behavior is visible in owning code. `Probe` means a bounded offline reproduction exists. Security exploitability and model performance were not tested against a running service.

| ID | Priority | Finding and consequence | Evidence / status |
| --- | --- | --- | --- |
| F01 | P0 | Development secret in tracked settings, DEBUG enabled, wildcard hosts, and allow-all CORS. Unsafe external configuration | `backend/quantvision/settings.py:22-32`; source confirmed; secret value omitted |
| F02 | P0 | No explicit application-wide DRF permission/throttle policy or per-view ownership for expensive endpoints. Authentication middleware is not sufficient | `backend/api/views.py:28-62,242-266`, settings and routes; source confirmed absence in inspected path |
| F03 | P0 | Caller-selected `session_id` enters progress/model filenames. A traversal write/read is a credible risk, not exploit-tested | `backend/api/views.py:247-260`; `backend/api/ai_services.py:1845-1849,1891-1892,1970-1974` |
| F04 | P0 | Forecasting and other expensive work execute inline; RL uses daemon threads. Timeouts do not stop running futures | `backend/api/views.py:14-25,37-62,242-266`; source confirmed |
| F05 | P0 | LSTM backtest scaler fits the entire history before the historical split. Production LSTM and GA preparation also fit before their validation split. Held-out observations influence preprocessing | `backend/api/ai_services.py:515-538,937-966`; `backend/api/evolution.py:45-66`; source confirmed |
| F06 | P0 | Historical backtest can use a current three-day HPO cache independent of historical origin. Tuning may contain future information | `backend/api/ai_services.py:920-935`; `backend/api/models.py:23-26`; source confirmed cache selection, downstream bias inferred |
| F07 | P0 | Forecast/error target mismatch. Predictions reconstruct target closes, RMSE/MAE compare later opens, row errors compare closes | `backend/api/ai_services.py:1040-1068,1104-1113`; source confirmed |
| F08 | P0 | Summed trade returns and compounded equity produce different headline returns. `win_rate` counts directional matches | `backend/api/ai_services.py:1076-1091,1116-1136`; source confirmed |
| F09 | P0 | RL evaluates the same prices used for training. Observation/reward indices need correction to avoid acting on already observed returns | `backend/api/ai_services.py:1670-1717,1845-1852,1883-1901`; source confirmed indexing and data reuse |
| F10 | P0 | Historical RL fetches current fundamentals/news; ensemble weights are paired with A2C-only headline history/return | `backend/api/ai_services.py:1510-1540,1850-1852,1906-1943`; source confirmed |
| F11 | P0 | Shared report fetcher backfills before an asset's first observation, inventing pre-inception history | `quant_reporter/data.py:41-45`; source confirmed |
| F12 | P0 | Report max drawdown can omit an initial loss; subyear CAGR is labelled annualized while clamped to a one-year denominator | `quant_reporter/metrics.py:5-22,75-90`; offline defect probes |
| F13 | P0 | Displayed optimizer methods say HRP/Min CVaR while code builds inverse volatility/min variance. Fallback can contradict the stated 60% concentration cap | `backend/api/ai_services.py:1335-1346,1373-1436`; `backend/api/views.py:64-84`; source confirmed |
| F14 | P0 | Horizon labels disagree. Dashboard says 30-day, service label says next-day, LSTM aggregates weekly bars | `frontend/pages/1_Dashboard.py:50-56`; `backend/api/ai_services.py:457,483-486`; source confirmed |
| F15 | P0 | Silent provider fallback lacks source/as-of provenance; Polygon's period map omits `5y`; adjusted and raw closes differ across workflows | `backend/api/ai_services.py:142-203,1810-1834`; source confirmed |
| F16 | P1, before ML release | Directional penalty uses `torch.sign`, adding no directional gradient to the training loss | `backend/api/ai_services.py:61-72`; offline gradient probe |
| F17 | P1, before classical release | Daily classical backtest uses weekly Sharpe annualization; interval coverage is not established | `backend/api/classical_models.py:23-76,83-122,215-219`; source confirmed |
| F18 | P1, before RL release | RL HPO imports a function with no definition found in the repository, then catches failure and uses defaults | `backend/api/ai_services.py:1862-1871`; `backend/api/evolution.py`; source/search confirmed, not trained |
| F19 | P1, before BL release | Two BL methods need reconciliation; NumPy delta omits its documented risk-free subtraction; other path uses current caps | `backend/api/bl_numpy.py:177-195`; `backend/api/bl_optimizer.py:15-40,145-195`; `backend/api/views.py:117-205` |
| F20 | P1, before simulation release | Annual mean log-return inputs feed a GBM step that subtracts half variance again; fixed training/OOS narratives do not describe arbitrary runs | `quant_reporter/opt_core.py:31-39`; `quant_reporter/monte_carlo.py:27-61,143-150,221-225`; source confirmed |
| F21 | P1, before derivatives release | BSM confidence score is heuristic, not a probability; rates/default volatility are dated assumptions | `backend/api/black_scholes.py:34-44,244-284,341-355`; source confirmed |

P0 means the affected behavior must be corrected or excluded before any external release. It does not require repairing an excluded RL or report module to ship a narrow chart workspace. Preserve experimental code privately and keep its results out of public claims until its gate passes.

Weekly aggregation also requires an availability-time review. A resample label is not the moment the full weekly bar became available. The known scaler leak does not prove that every weekly window leaks; fixtures must establish the exact origin, completed bars, and inference horizon.

## User experience and product-trust debt

The dashboard hardcodes price currency from ticker suffixes and labels current/forecast values without a full data envelope. Pages hardcode localhost endpoints, use inconsistent styles, and some network calls have no timeout. SWOT can import backend services directly as a fallback. The PowerShell launcher opens `Home.py`, while Unix starts `app.py`. These paths need a single accepted entry point and service contract.

Sources include `frontend/pages/1_Dashboard.py:10,28,45-56,122-135`, `frontend/pages/6_Chat.py:5,29`, `frontend/pages/4_SWOT_Analysis.py:313-340`, `scripts/start_streamlit.ps1:1-2`, and `scripts/start_streamlit.sh:4-23`.

The options page explicitly labels simulated NIFTY-style chain mode, which is a worthwhile honesty convention to retain. It still needs source/time/convention handling and no automatic mixing with market quotes. See `frontend/pages/3_Options_Analysis.py:28-30,58-114,205-215`. No live-data access was tested.

## Tests and current evidence

`backend/api/tests.py` contains useful `SimpleTestCase` checks for BSM properties, BL sensitivity, portfolio risk-profile changes, queue helpers, and frontend naming/launcher behavior. Preserve behavioral and numerical checks during migration. Some tests encode old method labels and require review against corrected semantics rather than mechanical preservation.

Loose root `tests/` scripts call a running localhost API and some write dumps. They are not a self-contained CI suite. `quant_testing/` contains examples, not a substitute for contract tests. The audit found no tracked CI/deployment/container configuration in the targeted inventory.

The Django suite and `check --deploy` were not run in this task. Importing the test module imports production services. `backend/api/ai_services.py:9-26` creates cache state and initializes FastEmbed, which may acquire model files. Later module initialization creates RL directories. This prevents a clean claim of network-free/import-safe test execution. No dependency installation, training, provider, LLM, or active API calls were made.

The [offline probe](audit_probe.py) attempts a syntax parse of 88 Python files without importing the application. It found one existing syntax error at `quant_testing/example_combined.py:1`, whose first line begins `the import`. It loads only two local numerical files, compiles the exact directional-loss function in isolation, and checks proposed color tokens. [audit-probe-results.json](audit-probe-results.json) is the execution receipt. BSM properties passing on these fixtures do not validate SABR, American exercise, model probabilities, live quotes, or the whole product. Reproduced defects are findings, not passing financial acceptance tests.

## Deployment blockers and preservation

Current scripts use local absolute paths, a development Django server listening on all interfaces, and differing Streamlit entry points. SQLite, local progress files, tracked environments, unpinned dependencies, heavy import effects, no explicit production auth/quotas, and unresolved data redistribution prevent a production-readiness claim. The `gunicorn` requirement alone is not a deployment configuration.

Preserve all existing modules in this run. Later migrations retain BSM/BL math, indicator/forecast research, portfolio/report structure, and useful tests behind explicit contracts. Quarantine misleading results through routing and release policy before undertaking broad rewrites. Security and financial correctness fixes should be small, separately reviewable changes with representative failing fixtures.
