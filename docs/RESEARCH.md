# Research methods and limitations

The public portfolio demo contains synthetic fixtures. No empirical prediction performance, investment recommendation, uncertainty interval, or live-trading capability is qualified.

## Baseline protocol

The supported engine compares last-close persistence with an expanding historical-log-mean reference. Every evaluation reports both baselines. Selecting a reference changes the visual focus, not which benchmark was evaluated.

Horizons are one or five exchange sessions. The chronological protocol partitions forecast targets into training, validation, and test periods. Each origin uses only the information available in its prefix. Target alignment follows the exchange calendar, including holidays, daylight-saving changes, and early closes.

MAE and RMSE are reported in the result's declared units and period. A lower error in a synthetic fixture is a numerical illustration, not evidence of market usefulness. Five-session targets overlap, so their errors are not independent observations. No statistical significance or predictive advantage is claimed.

Dataset, protocol, model, engine, run, and result identities remain explicit. Saved-result comparison checks compatibility. Export is restricted to consistent synthetic pipeline results. Replay verifies the exact saved result with matching source and runtime bindings.

## Historical admission

The existing daily contract accepts 120–1,500 contiguous XNYS sessions for supported instruments, USD raw closes, complete split/dividend semantics, and supported availability evidence. Each complete record must be available within the protocol's close-to-close-plus-60-minute window, before the next open.

A historical candidate requires permission for the actual user, local storage, private research, backup, and applicable transfer. A free endpoint, downloaded file hash, or adjusted-close series alone does not establish those rights.

Historical dates and current corrected values do not prove what was known at a past origin. Original/corrected vintages, corporate-action knowledge, calendars, completeness, provider attribution, and acquisition evidence must be reviewed separately. Exploratory analysis remains distinct from point-in-time-qualified forecasting.

No historical archive has passed these gates. CRSP through a legitimate institutional entitlement, EODHD under its applicable personal/commercial terms, and Massive under a source-specific agreement were investigated as potential acquisition routes. None has been acquired or approved for this demonstration. Free corrected-history access must not be presented as historical-vintage qualification.

## Preserved legacy research

ARIMA/GARCH, BiLSTM/HPO, mean fallback, RL, portfolio optimization, options, and reporting code remain research candidates. They are excluded from qualified forecasting claims.

Identified promotion blockers include full-sample preprocessing in legacy model paths, inconsistent horizon/benchmark semantics, training-history evaluation, and missing frozen dataset/split/provenance manifests for old serialized bundles. Those bundles and private runtime artifacts are excluded from the current public tree. Original local copies remain preserved.

## References

- [Forecasting principles, rolling origins and forecast accuracy](https://otexts.com/fpp3/toolbox.html).
- [Train-only preprocessing and leakage prevention](https://scikit-learn.org/stable/common_pitfalls.html).
- [Exchange calendars](https://github.com/gerrymanoim/exchange_calendars).

These references guide methodology; they do not certify Kerquant, approve data licenses, or validate predictive performance.
