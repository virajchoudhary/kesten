# Phase three implementation record

This is the historical Phase-three record. [Phase 3.5](PHASE35.md) supersedes its Docker/PostgreSQL execution blocker; the historical-data gate remains open.

Started from `codex/cadrisyn-foundation` at `58ed0bc` on 2026-11-06. Cadrisyn remains a private working name. The original database, 496 runtime files and 17 original research artifact/progress files are preserved. There is no deployment, merge, trading execution or paid provider.

## Scope and evidence boundary

No suitable local historical dataset with usable availability, corporate-action and rights evidence was found. The initial read-only workspace audit found two synthetic demo snapshots; these are not promoted to a forecasting evaluation dataset. Ten legacy RL bundles lack the required data/split/provenance manifest and were not deserialized or modified. The first end-to-end run therefore uses an explicitly installed synthetic fixture. Numerical correctness and integration can be tested; empirical forecasting performance cannot be established from it.

## Implementation decisions

Two independent source-audit/design candidates were considered. Candidate A imports immutable point-in-time manifests and compares fixed last-close and historical-log-mean baselines. Candidate B reuses chart snapshots for small synchronous runs. The synthesis keeps A's input boundary because existing adjusted Yahoo snapshots lack per-row availability/actions, and B's synchronous bounded execution because the fixed baseline workload needs no queue or legacy scientific environment. It does not use chart demo data as observed history. The pure numerical interface can support later execution changes without altering stored result conventions.

The new `research` Django app stores immutable account-owned dataset versions and completed runs. Operator imports require active accounts, a staff operator and explicit storage/private-research/transfer-rights acknowledgement. Development fixtures require an explicit command. The authenticated session API supports private dataset/run lists, creation and owner-scoped result reads. Idempotency survives response loss and retries; conflicting reuse is rejected. Failed calculations create no partial result. PostgreSQL/SQLite migrations are additive and the legacy profile excludes this app.

The input manifest accepts 120 to 1500 contiguous XNYS daily sessions for curated XNYS instruments. Raw close and split/dividend records share an availability timestamp. Every record must be known between its exchange close and the fixed close-plus-60-minute UTC issue cutoff, before the next session opens. Retrospectively adjusted inputs, missing sessions, unknown corporate actions and late/unavailable rows are rejected rather than imputed. These checks validate the declared timestamps, not the truth of an operator's historical archive or licensing assertion.

A forward cumulative split factor expresses prices in the initial observation's share units without future rescaling. Dividends are stored but excluded from this price-only target. Horizons are one or five scheduled exchange sessions. The mean-log method projects a geometric drift reference, without claiming arithmetic expected return or a validated predictive distribution. There are no probability intervals or trading-return metrics.

Evaluation fixes target-index train/validation/test boundaries at 60/20/20 and expands only through each origin's matured observations. The two methods and their parameters are predeclared; no tuning or model selection uses the final test. Outputs retain row forecasts, actuals, origin/cutoff, input-prefix hashes, target/units, protocol hash and model versions. MAE/RMSE and simple-return errors use identical targets. Three-class direction accounting includes zero, with confusion-matrix rows predicted and columns actual. Five-session targets overlap; loss comparisons are descriptive, without a significance claim.

## Model disposition

| Implementation | Phase-three decision | Evidence/limit |
| --- | --- | --- |
| New last-close reference | Accepted as a numerical reference method | Exact origin close, next-session target, no predictive-usefulness claim |
| New expanding historical-log-mean reference | Accepted as a numerical reference method | Causal expanding returns and explicit geometric path; no expected-return or profit claim |
| Legacy historical-mean fallback | Rejected for this integration | Clipped one-period simple-return/benchmark semantics differ from the declared target/horizon |
| Legacy BiLSTM and evolutionary HPO | Experimental, rejected for promotion | Full-sample scaling before temporal split; sign penalty has no useful directional gradient; historical target and execution/evaluation mismatches |
| Legacy ARIMA plus GARCH | Experimental, rejected for promotion | Fixed-origin path is not the new walk-forward protocol; unvalidated/capped bands, first-row directional credit and inconsistent annualization |
| Portfolio RL and standalone RL | Experimental, rejected for promotion | Training-history evaluation/current features in main path; generated returns in standalone environment; saved bundles lack frozen evaluation evidence |
| Other portfolio/options/reporting methods | Preserved outside forecasting release | No new financial/scientific certification; existing verification gates remain |

Sources are `backend/api/ai_services.py`, `evolution.py`, `classical_models.py`, `tasks.py`, and `decision/env.py`; the initial independent audit records exact defect locations. Excluded scientific algorithms are not silently rewritten or used in product forecasts. No advanced ML model has demonstrated accepted out-of-sample improvement here.

## Work units

- [x] Inspect actual research and integration boundaries; record data/provenance blockers.
- [x] Baseline checks: 78 backend tests collected with three PostgreSQL-only skips, 29 frontend tests, 23 offline legacy tests; preservation hashes pass.
- [x] Implement additive models, private API, operator import, explicit fixture seed, replay CLI and safe migration-tool inclusion.
- [x] Initial new API/security selection: 14 tests pass. Workspace-transfer unit selection: seven pass.
- [x] Numerical/property checks: 24 pass; independent scientific acceptance is limited to numerical and causal mechanics.
- [x] UI, optimized production build, static checks and six browser scenarios pass against the real source API.
- [x] Independent scientific and engineering reviews; confirmed contract/concurrency/UI findings corrected and accepted.
- [x] Close final review, all preservation receipts, reproducible instructions and focused local commits.

## Current environment blocker

Docker Desktop was stopped at this phase's start. A normal start fails with a missing `docker-desktop` WSL distribution and a conflicting existing main storage path. Windows denied starting its helper service. No Docker reset, volume deletion, distro registration repair or host permission change was performed. No native/Ubuntu PostgreSQL executable was found. Phase-three PostgreSQL/container validation is currently blocked; Phase-two receipts are not reused as a new Phase-three PASS. The existing volumes and unrelated workloads remain untouched. The isolated source SQLite workspace was backed up before its additive migration.

## Scientific references

The implementation follows [rolling-origin evaluation and forecast accuracy conventions](https://otexts.com/fpp3/toolbox.html), [train-only preprocessing guidance](https://scikit-learn.org/stable/common_pitfalls.html), and the repository's [quantitative verification gates](../rebrand/08-quantitative-verification.md). The statistical methods do not require scikit-learn or PyTorch in the application environment. Django's [constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/) and [transaction/row-lock semantics](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update) support atomic owner-bound persistence. Calendar behavior uses the pinned [exchange_calendars implementation](https://github.com/gerrymanoim/exchange_calendars).

## Verification results

| Gate | Current evidence |
| --- | --- |
| Supported Django selection | 120 collected, 116 pass, four PostgreSQL-only skips; includes 24 numerical and 17 new API/replay cases. Contract matches and no missing migrations; optional `security.W021` remains |
| Numerical engine | 24 pass independently and in the backend selection; hand-calculated errors, split/dividend behavior, horizons, holidays/DST/early close, maturity, future-input invariance and deterministic replay |
| Existing research selection | 23 pass offline with the preserved research interpreter; original research algorithms remain unpromoted |
| Frontend | 44 tests pass, TypeScript/ESLint pass, optimized Next production build passes |
| Browser | Six Chromium scenarios pass on a production-built frontend and actual source API; four real API journeys and two isolated stubbed account UI scenarios. Research covers five-session creation, source/units/evidence, narrow viewport, history reload and persistent run links |
| Actual API | 19 smoke checks pass, including original market/watchlist behavior, saved research, same-key replay, metric-count reconciliation, and two synchronized sign-ins/logouts |
| Replay | Current-code result hash reproduces exactly with matching dataset, engine source, dependency lock and runtime versions |
| Recovery | SQLite backup into a new archive, restore into a separate database, current-code replay, fresh sign-in and private result read pass |
| Workspace transfer | Seven root unit tests pass, including preservation of private research rows; actual Phase-three PostgreSQL transfer remains blocked |
| PostgreSQL/container execution | Not tested for Phase three because the local Docker host cannot start; four database-only tests are explicitly skipped |

The four skipped tests comprise three existing account concurrency checks and the new same-key research concurrency check. The workflow includes the research app in the PostgreSQL job, but no hosted run is claimed. Earlier Phase-two PostgreSQL/container results remain historical, not substitutes for this phase's missing execution gate.

Browser acceptance reproduced and corrected a dependency-map mismatch and SQLite sign-in contention. The client now validates additional textual package versions while retaining its required calendar version. The source SQLite profile uses Django's documented IMMEDIATE transaction mode so concurrent read/write transactions wait instead of failing during lock upgrades; the separate legacy profile and PostgreSQL configuration retain their prior transaction mode. The exact synchronized before/after API receipts distinguish the observed failure from the correction. Browser assertions were also aligned to repeated labels and the implemented methodology. A parent UTF-8 edit error was caught by a unit test and corrected without weakening that assertion.

The API advertises only JSON for research creation and documents authorization, missing/private records, unsupported media, throttling and unavailable-data errors. Result structures are declared in OpenAPI and generated TypeScript; runtime validation checks the nested scientific result and non-empirical status. The running process captures its engine/runtime fingerprint once, so later checkout edits do not relabel already loaded numerical code. Restart the API after code or environment changes before generating new evidence. Strict replay is qualified for the current pinned Windows environment; bitwise cross-platform identity is not claimed.

## Reproduce the private workflow

Follow [research operations](RESEARCH-OPERATIONS.md). The working source entry point is `http://127.0.0.1:3000/app/research`; market and account routes remain `/app/markets` and `/app/account`. The API is on port 8000. The container entry point on 8080 is unavailable on this host until Docker recovery.

No new package was added to the workspace dependency set. The legacy FastEmbed/NumPy and invalid-distribution issues remain confined to the old environment. Non-failing calendar/pandas timezone deprecation warnings are recorded, not silenced. Advanced model promotion still requires a rights-approved historical archive, independent point-in-time evidence, a frozen multi-asset evaluation and reliable baseline-relative improvement. No uncertainty calibration or trading evaluation is established by fixture tests.

## Review and commit trail

The independent numerical reviewer returned PASS and reran all 24 pure checks. The initial engineering review returned FAIL for advertised form encodings that the strict JSON horizon rejected. A subsequent acceptance found the dependency-map mismatch, unresolved browser sign-in failure and chart/assertion mismatches. These were corrected and the final bounded engineering acceptance returned PASS for the current API, client contract and concurrency corrections. It inspected source and receipts rather than rerunning services. All review workers' latest own runtime contexts identify Azure GPT-6 Luna at Max effort. This is independent context review, not provider diversity, a penetration test or certification.

The parent subsequently corrected visually observed chart-axis label collisions and bounded the saved-run list so it does not dominate mobile layouts. Numerical/API behavior did not change. UI tests/static checks and the affected actual research browser path were rerun; light/dark/mobile screenshots were inspected locally. Earlier failing receipts remain evidence of correction, not a current PASS.

- `ff8e0a5`: pure causal daily baselines and 24 numerical tests.
- `d54dbe4`: additive private storage/API, typed result contract, import/replay tools, preservation integration and concurrency correction.
- `654e5f0`: integrated research workspace, provenance, public calculation notes and browser workflows.
- `c28e032`: explicit legacy SQLite profile isolation and its failing-then-passing regression.
- `378696c`: readable chart axes and bounded mobile history.
- `b060a21`: browser geometry acceptance without fixing an arbitrary tick count.

The visual correction and final documentation/evidence follow on the same branch. No branch merge or publication occurred. Remaining release blockers are a qualified historical dataset and source rights, new PostgreSQL/container execution, hosted CI, production security/operations qualification and empirical model evidence. The synthetic fallback workflow is complete; real market predictive performance is not established.

The final legacy-profile probe also tested direct module loading with an inherited false legacy flag. It exposed workspace transaction options being inherited before the legacy module reset that flag. An explicit copied database configuration now removes the workspace-only option. The new configuration test failed before the fix, then passed alongside all23 legacy checks. This small post-review compatibility correction has parent test acceptance rather than another independent verdict.

Additional focused commits are `c28e032` for direct legacy-profile isolation and `378696c` for chart/mobile layout. Final evidence includes two root profile-isolation tests, a real-browser label-geometry regression and local light/dark/mobile inspection. The only remaining working-tree difference after documentation closeout is the original, unchanged-hash research database.
