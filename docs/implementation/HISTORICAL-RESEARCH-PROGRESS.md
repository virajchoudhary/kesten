# Historical research qualification, 12 November 2026

Production remains **NO-GO**. No reviewed archive qualifies for the frozen v1 protocol, so no real-data ingestion, training, empirical scores or model promotion occurred. This work adds executable intake preflight and fixes a reproduced historical-run admission defect. It does not repeat the completed image-security investigation.

Starting commit is `b34eebe65f7808685a7716a3df9665f701a48d55` on `codex/cadrisyn-foundation`. The numerical engine, dataset format, dependency lock, migrations and replay implementation are unchanged.

## Source decision

**EODHD is the closest free candidate for one person's private, noncommercial research, but is not qualified for Kerquant's present workflow.** Its free endpoint supplies a year of history with 20 daily requests. Raw close is separate from the split/dividend-adjusted close. A calendar year could satisfy the 120-observation minimum, but actual completeness and corporate-action coverage have not been tested. No account or price request was made. [EOD API specification](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes).

There is now stronger rights evidence than a generic free-plan advertisement. EODHD expressly permits personal local storage, encrypted backups, provenance records and indefinite retention of private research outputs after cancellation. It prohibits sharing and use for a business or group; this does not establish the internal-transfer entitlement required by Kerquant's intake. No institutional or multi-user permission is inferred. [Storage and retention](https://eodhd.com/help/storage), [personal/commercial terms](https://eodhd.com/financial-apis/terms-conditions).

More decisively, EODHD states that corrections overwrite bars and actions, have no fixed correction window, and retain neither past vintages nor change timestamps. Its advertised US delivery schedule is not proof that today's exact record was available at an old forecast origin. Its source page describes exchange contracts, while the API footer describes OTC/market-maker aggregation without exchange feeds. The exact US feed needs clarification. These are source facts to resolve, not gaps to fill with generated timestamps. [Correction and vintage methodology](https://eodhd.com/help/methodology), [source description](https://eodhd.com/financial-apis/our-data-sources-and-data-partners), [API footer](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes).

| Alternative | Verified evidence | Current decision |
| --- | --- | --- |
| Twelve Data | Official guidance places historical US EOD availability after midnight ET on the next trading day. Terms restrict free-tier commercial use and require deletion following termination. | Outside close-plus-60-minute v1 timing; durable retention and application entitlements are not established. [US equities guide](https://support.twelvedata.com/en/articles/9935903-us-equities-market-data), [terms sections 2, 12 and 16](https://twelvedata.com/terms). |
| SimFin | The pricing FAQ says downloaded data and backups must be deleted after cancellation. | Unsuitable for this durable archive/recovery workflow without a different written grant. [Current pricing FAQ](https://www.simfin.com/en/prices/). |
| Nasdaq WIKI | Official WIKIP URL and direct terms retrieval returned 404. Search-indexed generic Nasdaq terms require an order form and do not establish WIKI-specific rights. | No verified current acquisition route or archive entitlement. Legacy public-domain metadata is not current clearance. [Product URL](https://data.nasdaq.com/databases/WIKIP), [indexed terms URL](https://data.nasdaq.com/terms). |
| CRSP | Official product documentation describes daily prices, corporate actions, permanent identifiers and active/inactive securities; access requires a data license/subscription. | Strong institutional source to consider only if a lawful existing entitlement is supplied. No entitlement, price or v1 publication-vintage proof was established. Nothing purchased. [Product](https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/), [access information](https://indexes.morningstar.com/research-data-products). |

The independent source reviewer reached the same no-qualified-source decision. This is a research assessment, not legal clearance. Raw documentation snapshots remain private; their acquisition timestamps, HTTP outcomes and SHA-256 hashes are in the [source receipt](evidence/historical-research-20261112/source-snapshots.json). These hashes identify documentation, **not market datasets**. No historical raw-data hash, measured date coverage or completeness result is fabricated.

The earlier [UCI and WIKI findings](PHASE5-RESEARCH-SOURCES.md) remain valid limitations. Weekly returns, demo prices, synthetic fixtures and third-party mirror licenses cannot substitute for a qualified daily archive.

## Working research improvements

Before this fix, an authenticated owner could start a new historical run from a directly created or legacy dataset without any `ResearchIntakeReceipt`. The regression reached HTTP 201 and persisted a run before the guard. Source evidence was checked at import, but not at execution.

`run_evaluation` now verifies the newest archived receipt for a historical dataset after checking its numerical identity and before evaluation. Missing evidence, tampered terms/CSV/availability, or a corrupt latest acquisition blocks the new run. It does not silently fall back to an older receipt. The existing API returns `dataset_unavailable` with HTTP 503 and stores no new result. Verification still says `independently_verified_source: false`; an intact operator attestation does not authenticate a provider or grant rights.

Existing saved-result reads and idempotent responses remain available. Numerical replay retains its prior meaning: equality of dataset, engine, environment and numerical result. Replay is not renewed source qualification. No saved result or corrupted receipt is edited to make a check pass. Synthetic workflows continue without requiring optional source receipts.

`import_research_csv --dry-run` uses the exact existing bounded parser and `PreparedIntake` path before any actor query or import. It reports dataset/receipt identities, source ID, acquisition time, component hashes, coverage, declared permissions and the attestation limitation. It does not need account names, acknowledgement or a usable database. Write mode still requires both active actors, a staff approver and the acknowledgement. See [operator commands](PHASE5-RESEARCH-OPERATIONS.md#preflight-before-database-work).

## Evaluation scope

The fixed one/five-session persistence and expanding log-mean implementations remain the first comparisons. Their existing chronological target partitions, origin-specific prefix hashes, expanding information sets and frozen outputs were retained. No fitted preprocessing, configuration search, uncertainty band, statistical significance or trading claim was introduced.

No qualified data means **empirical MAE, RMSE and benchmark differences are unavailable**. Passing synthetic future-perturbation and replay tests establish software properties only. Five-session overlapping targets still preclude independent-sample inference. The prior [legacy-model promotion rejections](PHASE5-RESEARCH.md#model-decisions) remain; no BiLSTM/HPO, ARIMA/GARCH or RL model was trained or promoted.

## Verification and remaining gates

The [verification receipt](evidence/historical-research-20261112/verification.json) records exact checks and limitations. A real subprocess preflight accepted a synthetic package and rejected altered terms with exit code 1 while the configured SQLite directory did not exist. No database directory was created. Tests use synthetic/schema-only inputs and disposable in-memory databases, never empirical observations. The missing-receipt regression has a failing-before record.

The complete research suite ran 79 tests: 78 passed and the PostgreSQL-specific concurrent-transaction test was skipped on SQLite. This includes the six new admission/preflight tests, frozen one/five-session hashes, future perturbations, input bounds, privacy, exports and deterministic replay. Ruff 0.15.17 passed E4/E7/E9/F checks on the three changed Python files. A first expanded run exposed two serialization errors in the new test fixture, which were corrected before the complete suite passed; production parsers were not loosened.

Current hash checks match the original database, all 496 protected runtime files, 17 research artifacts and 22 unrelated starting paths. The numerical source, schema migrations and dependency lock match the starting commit. [Preservation receipt](evidence/historical-research-20261112/preservation.json).

Independent implementation acceptance is recorded separately from source qualification in the [review receipt](evidence/historical-research-20261112/independent-review.md). A code PASS cannot turn a rejected source into market evidence. Existing container, PostgreSQL, browser and security receipts were not rerun or relabeled as fresh passes for this change.

The next empirical gate requires an authorized archive with complete actions, sufficient contiguous XNYS sessions and evidence for the actual values available at each close-plus-60-minute origin. Moving the issue time alone cannot recover overwritten vintages. A different owner-only retrospective protocol would need its own limitations, scientific review and version; it was not slipped into v1. A lawful forward snapshot collection could eventually establish observed vintages, but no capture job or account was created here.

No push, merge, deployment, purchase or production acceptance occurred.
