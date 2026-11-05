# Financial-model and research acceptance policy

Status: proposed mandatory gates for affected releases. No model or strategy is certified, profitable, or validated by this document.

## Definitions and result classes

An observed value comes from a dated market-data snapshot. An expected value is a model or statistical estimate. A scenario uses user-selected assumptions. A backtest applies a locked strategy to historical observations with an execution model. A simulation samples a defined stochastic process. These terms are never interchangeable in API fields, charts, reports, or marketing.

Each result includes instrument identity, currency, units, adjustment basis, calendar, source/snapshot, observation cutoff, origin/target horizon, method/code version, and conventions. Model runs additionally include artifact, features, scaler, split/tuning IDs, seed, runtime, and evaluation approval. A numerical output without those fields remains experimental.

R1 uses a naive last-close baseline for the next completed exchange session. Its value equals the origin close, its target is explicit, and it is labelled `Last-close baseline`. It is a reference forecast, not ML or a trading recommendation. The historical-mean fallback is not accepted unchanged because of current horizon and provider semantics.

## Shared numerical conventions

Use one return convention per calculation and name conversions. Simple return is `P_t / P_(t-1) - 1`. Log return is `log(P_t / P_(t-1))`. Compounded strategy return is the product of one plus each net period return, minus one. A sum is not the same statistic.

Include initial equity in drawdown. Define whether drawdown is a negative signed value or a positive loss magnitude and keep the API consistent. R1/P1 proposed convention is a nonnegative loss magnitude in structured metrics, with the UI label `Maximum drawdown`. Do not reuse existing signed strings without conversion.

Annualization uses the actual return frequency and declared session calendar. A default 252 sessions for US daily equities and 52 for weekly data are explicit approximations, not universal constants. Use an effective per-period risk-free conversion when computing excess returns. Short samples show total period return and duration. If an annualized value is offered, use the declared elapsed-time formula and explain instability; do not label unannualized period return as CAGR.

Proposed Sortino uses the square root of the mean squared negative shortfall from the declared minimum acceptable return over all periods, not the standard deviation conditional on negative observations. Historical VaR/CVaR states loss-versus-return sign convention, quantile interpolation, confidence level, horizon, sample count, and tail rule. Nonfinite or undefined statistics return null with a reason.

Currency conversions use dated FX and keep source currency. Adjusted prices, dividends, split events, delistings, ticker changes, and survivorship are explicit. Never backfill prices before listing or substitute an unobserved quote with a synthetic number in a market result.

## Gate matrix

| Gate | Objective acceptance tests | Blocks |
| --- | --- | --- |
| Q01 Data integrity | Fixtures for splits, dividends, missing sessions, first listing, delisting, duplicate bars, timezone/DST, and provider period ranges. No invented pre-inception prices. Requested `5y` either returns the correct range or explicit insufficient coverage | All market/quant releases |
| Q02 Point-in-time isolation | Modify every observation after an origin and show that its features, scaler, tuned configuration, and original forecast remain unchanged. Assert maximum input publication/availability time is at or before origin | Forecasts and historical scenarios |
| Q03 Transform discipline | Fit scaler/imputation/feature selection on training only. Validation/test extrema cannot alter training transforms. Feature names/order/dtypes are serialized and checked at inference | ML release |
| Q04 Horizon alignment | Hand-worked bars prove origin, available completed bar, target close, and execution entry/exit. Error metrics and per-row errors use the same target. Daily/weekly labels match actual sampling | Forecast/backtest release |
| Q05 Ledger and metrics | On a known trade sequence, fees and slippage reconcile each fill to cash, holdings, equity, compounded return, drawdown, and final wealth. Directional accuracy and profitable-trade rate are distinct | Backtests/reports |
| Q06 Forecast evaluation | Freeze train/validation/test by time, tune only within training/validation, and compare against last-close, historical mean, and a declared classical baseline. Report MAE/RMSE, direction policy including ties, sample size, confidence/uncertainty, and per-horizon differences | Any public model-performance claim |
| Q07 Portfolio feasibility | Weight sum and asset/group bounds meet declared tolerances; infeasible constraints return infeasible. Single-asset versus 60% cap is rejected. No solver fallback keeps the original method label. Compare equal-weight/current allocation | Optimizer release |
| Q08 BL math and data | Known posterior fixtures, no-view prior recovery, confidence sensitivity, positive-semidefinite covariance checks, explicit risk-free excess-return prior, and historical market-cap availability | BL release |
| Q09 Derivatives | Dividend-adjusted put-call parity, price bounds/monotonicity, IV round trip, finite-difference Greeks with unit checks, expiry and zero-vol limits, negative rates, nonfinite input rejection, and impossible market-price cases | BSM release |
| Q10 Simulation | Seeded runs, t=0 equity, declared drift convention, dimensions, deterministic zero-vol case, and sampled moments within statistical tolerances. Annual log drift is not reduced by half variance twice | Monte Carlo release |
| Q11 RL chronology | Observation ends before the return earned by the action. Train/tune/evaluate on disjoint periods; fundamentals/news are point-in-time. Ensemble allocation and reported equity describe the same strategy | RL release |
| Q12 Interval validity | State predictive/confidence/scenario meaning, construction, horizon, and coverage. Evaluate empirical coverage and width by horizon and regime on held-out data | Any probability/band claim |
| Q13 Reproduction | Frozen licensed dataset hash, code SHA, dependency lock, artifacts/scalers, seeds, hardware/runtime, config, and output manifest reproduce within justified tolerances | Promoted model/artifact |

Initial float64 accounting tolerance is `1e-8` for normalized weights and deterministic fixture comparisons where appropriate. Price/Greek tolerances depend on scale, finite-difference step, and display rounding. Define solver feasibility tolerances separately from display precision. Statistical tolerances come from the sample/process, not arbitrary exact equality.

## Forecast and backtest protocol

Start with a frozen dataset and a dated research question. Lock the instrument universe and benchmark before evaluating. Split chronologically, with a gap or purging where overlapping labels create leakage. A bidirectional LSTM over already observed historical windows is not itself future leakage; window construction and data availability decide that question.

Fix the scaler leak, historical HPO selection, differentiability of the directional objective, target/execution mismatch, and reporting reconciliation identified in the audit. For a directional loss, verify that a representative wrong-sign prediction changes the gradient as intended. Do not treat a larger numeric loss with unchanged gradient as proof of learning direction.

Select models using training/validation only. Keep the final test untouched until the candidate and protocol are locked. Record the number of configurations tried. Report failures, per-instrument dispersion, and sensitivity to costs and dates. A selected historical example cannot substantiate broad accuracy. No pre-specified minimum accuracy or Sharpe is invented here. A reviewer approves the evaluation protocol and economically relevant comparison before model promotion.

A result may pass numerical correctness and still fail predictive usefulness. Publish the actual comparison, including negative or inconclusive results. R1 remains baseline-only if a model does not pass. No neural model is required to justify a professional chart workspace.

Execution must use a price available after the signal. Include spread, commission, slippage, borrowing/financing where applicable, turnover, capacity assumptions, and cash constraints. Do not imply that a long/short sign strategy is executable without short availability. Benchmark equity uses the same date range, adjustment basis, and cost policy. Optimization/evaluation on the same sample is labelled in-sample analysis, never validation.

## Options and volatility models

Retain the core European BSM formulas after broader Q09 tests. The narrow discovery probe supports parity, one IV round trip, and one delta finite difference only. It does not test every boundary or contract style. Zero volatility with positive time requires discounted deterministic payoffs and consistent sensitivities, not a universal intrinsic-value shortcut. Inputs must be finite, and impossible IV cases produce an unavailable result.

Replace the existing heuristic `confidence` presentation with a clearly named diagnostic or remove it from the product. Large theoretical/market divergence is not a probability of profit. Rate/volatility defaults are dated assumptions. Greeks specify theta per calendar day, vega per one percentage point volatility, and rho per one percentage point rate, matching the engine's chosen units.

SABR needs a documented Hagan approximation variant, forward/spot convention, beta treatment, calibration objective/weights, bounds, residuals, expiry units, and extrapolation policy. Test ATM behavior and low-vol/near-zero-parameter limits, then compare known fixtures or an independent vetted implementation. Check surface arbitrage conditions where the product implies a coherent surface. A fitted smile is not a forecast and does not validate the simulated chain's economics.

American exercise, discrete dividends, contract multipliers, calendars, settlement, and exercise-specific models are separate future scope. The UI must not imply that a European BSM formula values every chain contract exactly.

## Model artifact and approval lifecycle

Use `experimental`, `evaluated`, `approved`, `deprecated`, and `revoked` states. Training never automatically grants approval. Approval records protocol, data rights, evidence, limitations, and reviewer. Serve only approved artifacts in product forecasts. Revocation stops new inference while retaining historical run evidence and a clear status.

Monitor data drift, feature availability, forecast errors after outcomes become observable, interval coverage if offered, and baseline-relative performance. Labels mature only after the target session. Do not tune against not-yet-realized outcomes or silently overwrite a historical forecast. Retraining is a versioned operator action with budget and evaluation gates.

[PyTorch 2.10's reproducibility guidance](https://docs.pytorch.org/docs/2.10/notes/randomness.html) explains why seeds alone do not guarantee identical behavior across versions/platforms. Record the environment and tolerance. The [2.10 serialization guidance](https://docs.pytorch.org/docs/2.10/notes/serialization.html) supports state-dict-oriented loading and cautions about untrusted serialization. These pages were read on the research date and match the inspected runtime series. Use only trusted, hashed artifacts and explicit safe loading options supported by the locked runtime. No arbitrary uploaded model files in the product.

## Current verdict

The repository contains useful research and numerical code. Its current forecast/backtest/RL outputs are not accepted evidence for production quantitative claims. The [audit](01-repository-audit.md) identifies the source defects and [probe receipt](audit-probe-results.json) records narrow current observations. Every gate above is future work unless explicitly marked as exercised in that receipt.
