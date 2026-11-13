# Kesten

A Django REST and Streamlit quantitative-research application with PyTorch LSTM,
classical forecasting, portfolio-analysis, and historical-backtesting components.
Viraj contributed research components and later continued the project as a
full-stack market workspace.

Kesten is the final project name for the historical Stock Predictor System.
The repository is now [`virajchoudhary/kesten`](https://github.com/virajchoudhary/kesten).
Earlier release records use Kerquant; older source identifiers also use
QuantVision or Cadrisyn. Existing source directories, configuration names,
branches, and Git history are unchanged. The project name does not establish
trademark or domain clearance.
The name does not imply a production release, live trading, or validated
prediction performance.

## Which implementation are you reviewing?

| Implementation | Availability | Evidence boundary |
| --- | --- | --- |
| Django and Streamlit research application | Public main | Source is available in this repository. Trading performance and production readiness are not established. |
| Next.js market workspace with Django APIs | Public draft [PR #16](https://github.com/virajchoudhary/kesten/pull/16), not public main | Independently authored continuation with recorded local checks. The release PR remains open and unmerged as of 13 November 2026. |

The newer workspace includes authenticated market APIs, owner-scoped watchlists,
and API/browser regression coverage. Its chart data includes explicitly synthetic
demonstration data. This README does not imply that cloning public main yields
the newer workspace. PR #16 contains the proposed release on
`codex/kerquant-portfolio-publication-v2`; its historical branch name is retained.
The [publication record](https://github.com/virajchoudhary/kesten/blob/a30de92eeb3755a7e1acd499e963b9c75fa4bb2a/docs/PUBLICATION.md)
documents 136 frontend tests, 169 PostgreSQL backend tests, and four CI-helper
checks run locally. These are recorded checks, not a fresh run or hosted CI pass.
Production remains NO-GO.

No verified live-trading returns, directional-accuracy gains, point-in-time
integrity, API latency, task throughput, or production deployment are claimed.

## Source map

| Area | Source |
| --- | --- |
| Django API and routes | [`backend/api/`](backend/api/) |
| Django settings and application wiring | [`backend/quantvision/`](backend/quantvision/) |
| Classical forecasting components | [`backend/api/classical_models.py`](backend/api/classical_models.py) |
| Optimization and options components | [`backend/api/bl_optimizer.py`](backend/api/bl_optimizer.py), [`backend/api/black_scholes.py`](backend/api/black_scholes.py) |
| Interactive research frontend | [`frontend/app.py`](frontend/app.py) |
| Report generation | [`quant_reporter/`](quant_reporter/) |
| Historical research examples | [`quant_testing/`](quant_testing/) |
| Existing checks | [`tests/`](tests/), [`backend/api/tests.py`](backend/api/tests.py) |

The stack uses Django REST Framework, Streamlit, PyTorch, pandas, numerical
optimization libraries, and ARIMA/GARCH components. Celery and Redis wiring is
present in the public application. A dependency or source module is not proof
that every integration runs successfully.

## Review before running

The existing checks include network/provider-dependent research scripts.
Test filenames are not passing test evidence, and public main has no captured
GitHub Actions workflow. Do not run every script as a unit-test suite.

The public dependency files are not a reproducible locked environment.
Inspect [`requirements.txt`](requirements.txt),
[`backend/requirements.txt`](backend/requirements.txt), and settings before
installing or starting services.
Provider credentials belong in an untracked local configuration, never in
source, screenshots, logs, or a public demo.

The following are source-derived local entry points, not verified turnkey setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver 127.0.0.1:8000
```

The Streamlit entry point is `streamlit run frontend/app.py`.
Some pages require the backend, external market-data services, optional
libraries, and provider configuration. Use local development only until those
dependencies and security settings have been reviewed.

## Contributions and limitations

This is an academic project with later independent continuation, not an
individually owned implementation of every model or dependency.
Viraj's reviewed work includes Django REST, Streamlit, PyTorch LSTM,
historical-backtesting, and ARIMA/GARCH components.
The Next.js continuation has separate authored source and recorded regression
evidence on the draft release branch.

Historical market-data evaluation does not by itself establish an investable
strategy. Revised data, execution costs, leakage, model selection, and
out-of-sample validation require their own assessment.
API examples, source modules, and demonstration data are not empirical
performance measurements.

No screenshot or verified production demo of the newer implementation is
attached here. The source proposed in PR #16 is public, but merging it and
deploying the application require separate approval and successful release gates.
This naming and documentation update does not authorize either action.
