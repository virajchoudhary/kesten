# Phase 5 research foundation

The source-intake foundation is implemented. Empirical forecasting qualification remains blocked. No historical archive was acquired or accepted during this work, and no historical accuracy or investment-performance claim is supported.

This work continues `2a04197` on `codex/cadrisyn-foundation`. It does not replace the unrelated Phase 5 release-engineering changes already present in this checkout.

## Implemented behavior

`backend/research/ingestion.py` converts a bounded, explicit daily CSV into the existing immutable v1 dataset. It validates source metadata, retained terms, per-observation availability evidence and their SHA-256 hashes before any database write. It never downloads prices, invents publication times, fills missing corporate actions or substitutes synthetic data.

`ResearchIntakeReceipt` stores the original CSV, terms snapshot, availability document, canonical receipt and approving staff account beside the private dataset. The additive `research.0002_researchintakereceipt` migration does not rewrite datasets or saved runs. Repeating the same import reuses its receipt. A later acquisition can create a different receipt for the same numerical dataset. Corrupt existing evidence causes rejection rather than replacement.

The shared `import_dataset` service now requires a prepared source intake for new `historical` imports. A historical JSON declaration alone is insufficient. Existing synthetic imports, saved research and deterministic replay retain their contracts. No historical rows were relabeled, and the migration does not retroactively certify existing data.

The operator commands are `import_research_csv` and `verify_research_intake`. They require local application access. Import requires an active owner and active staff approver; receipt verification is owner scoped. Raw evidence is absent from research API responses. Historical exports remain disabled under the existing synthetic-only export policy.

Every receipt says `source_attestation: operator_attested` and `independently_verified_source: false`. Hashes establish byte identity. Neither hashes nor the acknowledgement flag establish entitlement, upstream authenticity or point-in-time truth. Staff must review those matters before importing historical data. The software does not claim legal clearance.

## Scientific contract retained

The v1 protocol accepts 120 to 1,500 contiguous XNYS sessions of USD raw daily closes, complete split/dividend fields and explicit availability timestamps. Its publication window ends 60 minutes after the exchange close. It evaluates split-neutral prices in initial-share units and excludes dividends from the target. This is not a total-return protocol.

One-session and five-session targets use chronological 60/20/20 partitions and rolling forecast origins. Both reference methods use only information through the origin. Persistence and the expanding prior log-return mean remain the fixed comparisons. There is no newly fitted scaler, tuned model, confidence interval or additional configuration trial. Five-session targets overlap; ordinary independent-sample significance claims would be inappropriate.

The new future-perturbation test changes prices, dividends and splits after a cutoff. Earlier forecasts, input hashes and information cutoffs remain equal for both methods and horizons, while future outcome labels change. Frozen synthetic dataset and result hashes also remain exactly equal. These checks establish pipeline properties, not empirical predictive power.

`backend/research/quant/*.py`, the dependency lock and the replay runtime contract are unchanged. The engine still reports `empirical_performance_established: false`. Genuine historical descriptive scores, when eventually available, would not alone establish useful forecasting performance.

## Model decisions

| Candidate | Current evidence | Decision |
| --- | --- | --- |
| Persistence and expanding prior log-return mean | Deterministic synthetic checks, origin cutoffs, immutable identities and replay pass. No qualified archive exists. | Accepted as numerical reference implementations. Empirical qualification blocked. |
| Legacy mean fallback | Uses clipped simple/excess daily returns and a damped projection; it is not the v1 reference method. Missing benchmark data previously produced a nonfinite result. | Fixed only the reproduced finite-output bug. Not promoted. |
| BiLSTM and HPO | Full-series scaling precedes temporal splits in legacy prediction/backtest/HPO paths. Validation reuse, horizon/target mismatch and a zero-gradient sign penalty remain. | Reject promotion until causal preprocessing, target alignment and untouched evaluation are demonstrated. |
| ARIMA/GARCH | Fits pre-cutoff observations; it does not share the scaler issue above. Fixed-origin evaluation differs from rolling one/five-session evaluation. Capped bands lack held-out coverage evidence. Direction/sharpe calculations also need correction. | Preserve implementation. Reject promotion under the current protocol. |
| Portfolio RL | Same-index return timing, reused training/evaluation prices, unbound historical contextual requests and insufficient dataset/seed identity prevent causal out-of-sample qualification. | Preserve research. Reject promotion. |
| Standalone decision environment | Generates random returns rather than historical observations. | Synthetic software exercise only. |

Relevant legacy implementations remain in `backend/api/ai_services.py`, `backend/api/classical_models.py`, `backend/api/evolution.py` and `decision/env.py`. No model artifact was loaded, trained, overwritten or promoted. The PyTorch CPU smoke check uses synthetic tensors, performs no optimizer steps and writes no artifacts.

## Verification and operations

See [source decisions](PHASE5-RESEARCH-SOURCES.md), [operator instructions](PHASE5-RESEARCH-OPERATIONS.md) and the [verification receipt](evidence/phase5-research/verification.json). The evidence directory contains test logs and preservation receipts, not market data, credentials or database dumps.

The reusable `scripts/check_research_intake.py` proves an actual 0001-to-0002 upgrade, CSV management-command import, exact archived-byte verification, SQLite backup/restore and replay in a new Python process. Every generated input is explicitly synthetic. It creates fresh UUID-named databases under `.local/research-intake-qualification` and preserves earlier runs.

PostgreSQL qualification uses the existing Docker database and dedicated `test_cadrisyn` database. Application table inventory and row hashes are compared before and after. The application database is not migrated as part of this verification. The new migration must be applied deliberately to a chosen operational database before using intake there.

## Outstanding acceptance gates

1. Obtain an authorized archive with raw daily prices, complete action history and credible value-specific publication/vintage evidence. Preserve its actual terms and acquisition record. No archive currently meets this gate.
2. Review source authority, permitted storage/research/backup/transfer and restrictions before staff attestation. Do not infer rights from a public download link.
3. Import without manufacturing a close-time availability timestamp. Data published outside the v1 window requires a separately versioned protocol and forecast issue time, not a relaxed validator.
4. Run the fixed chronological comparisons for each asset, horizon and period. Report MAE/RMSE and justified additional metrics with coverage, benchmark differences and limitations. Do not combine synthetic checks with those results.
5. Qualify complex models independently before enabling them in the research workflow. Any uncertainty estimate needs held-out calibration evidence.

No service was deployed, no paid provider was introduced and no public Git operation was performed.
