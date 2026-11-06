# Historical data qualification

Reviewed on 2026-11-07 for Phase 3.5 at `8817617`. No candidate in this bounded review qualifies for the existing forecasting protocol. This is a source assessment, not trademark clearance, legal advice or a claim that all historical datasets are unusable. No market observations were acquired, no account was created, and no subscription was purchased.

## Acceptance boundary

The unchanged engine requires 120 to 1500 contiguous XNYS sessions for a supported USD stock, raw closes and complete effective split/dividend records. Each complete price/action row must have source-supported point-in-time availability between its exchange close and close plus 60 minutes, before the next open. A download date does not establish when a historical value was first known. A final corrected archive can differ from what was available at the forecast origin. Retrospectively adjusted closes and invented publication times are not acceptable substitutes.

Rights must cover the intended user and purpose, local storage, private research, backups and database transfer. Public download access, an uploader's license, or a non-commercial personal plan does not automatically authorize an enterprise service or redistribution. No provider rights are certified here.

## Sources assessed

| Candidate | Source facts and qualification decision |
| --- | --- |
| Alpha Vantage | [Daily API documentation](https://www.alphavantage.co/documentation/) distinguishes raw daily prices from adjusted/corporate-action data. Its free compact daily response has 100 rows; full daily history and the daily-adjusted endpoint require premium access. The [terms](https://www.alphavantage.co/terms_of_service/) default to individual personal non-commercial use and distinguish use for a firm. No reviewed endpoint supplies the required original per-row price/action availability archive. Not accepted for this contract; no API key requested. |
| Tiingo EOD | [Documentation](https://www.tiingo.com/documentation/end-of-day) provides raw/adjusted prices and split/dividend fields, describes most US prices arriving at 5:30 PM EST and corrections through 8 PM. This does not support the close-plus-60-minute complete-record deadline. [Terms](https://app.tiingo.com/tos/) sections 1.7(c) and 7.3 restrict predictive-model use to qualifying paid plans and distinguish commercial use and redistribution permissions. Not accepted; no account or data requested. |
| Nasdaq Data Link WIKI | The [official product URL](https://data.nasdaq.com/databases/WIKIP) returned 404 in this review. Search-indexed first-party metadata describes historical US daily prices/actions, public-domain status, discontinued support in 2018 and a late-evening update cadence. These incomplete metadata are not verified current access/rights or point-in-time evidence. Raw methodology, action completeness and an accessible original archive were not qualified. No download or empirical evaluation. |
| NYSE | [TAQ Closing Prices](https://www.nyse.com/data-products/catalog/taq-nyse-closing-prices) describes closing-price history. Corporate actions are offered separately through the [Market Event Feed](https://www.nyse.com/market-data/corporate-actions/market-event-feed). Product access/entitlements and source-authenticated publication records for both would need qualification; the reviewed pages do not establish a free permitted complete input archive. Not acquired under the no-purchase constraint. |
| CRSP | [Research product information](https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/) describes daily research data/actions and licensed access. The independent reviewer found subscription access, with no qualifying close-plus-60-minute publication archive. The parent's direct fetch timed out, so current detailed terms/coverage were not independently read back. No institutional entitlement was established and no data was acquired. |
| Stooq | [Terms](https://stooq.com/t/?i=1) and [historical download page](https://stooq.com/db/h/) presented browser verification. It was not bypassed. Rights, adjustment basis, action completeness, coverage and availability evidence therefore remain unverified. Download availability alone is insufficient. |

The parent verified Alpha Vantage and Tiingo documentation/terms and the NYSE product pages directly, and reproduced the Nasdaq 404 and Stooq challenge. The independent read-only review also assessed CRSP and the indexed Nasdaq metadata. No exact coverage/completeness assertion from an unacquired archive is treated as verified. Provider documentation is mutable; repeat this assessment before an actual acquisition.

## Existing local data

A read-only inventory of the isolated workspace found one `synthetic_fixture` dataset version and two `demo` chart snapshots, with no historical research dataset. The earlier frozen research/model artifacts are not a rights- and availability-documented price archive. They remain untouched and were not deserialized.

Qualified market datasets: none. Raw market-data SHA-256 values and acquisition dates: none, because no market data was acquired. There are no empirical MAE/RMSE tables, asset/horizon rankings, calibrated intervals or out-of-sample improvement claims from this phase. Container smoke, replay and browser tests use explicit synthetic fixtures only.

## Reopening the gate

Retain the original source bytes, SHA-256, acquisition timestamp, provider attribution, terms/version and permitted-use evidence with any future candidate. Independently verify exchange mapping, calendar coverage, missing sessions, raw-price basis, actions and historical publication/correction evidence before operator import. The current normalized-content version hash and import timestamp do not replace an original-file hash or an acquisition receipt. The parser validates declarations; it cannot authenticate an operator's external evidence.

Use the existing staff-approved [import/replay workflow](RESEARCH-OPERATIONS.md) only after those checks. Do not synthesize availability times, relabel fixtures, assume absent corporate actions mean none, tune on the final test set, or relax the protocol silently to make a provider fit. A later issue cutoff or retrospective-only study would be a separately specified scientific protocol, not this qualification.

## Model decisions

The last-close and expanding historical-log-mean methods remain accepted as numerical reference methods for one- and five-session targets, without empirical usefulness established. No additional method is needed before qualified observations exist. The preserved mean fallback, ARIMA/GARCH, BiLSTM/HPO and RL remain rejected for product promotion for the source-level reasons in the [Phase-three disposition table](PHASE3.md#model-disposition). No algorithm was trained, rewritten or certified in this qualification.
