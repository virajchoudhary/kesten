# Terminal depth review

Review dates: 7–8 November 2026. This replaces acceptance claims about the Phase 4.5 interface. The previous interface was rejected by the product owner. The existing backend remains the authority for accounts, provenance and research results.

## Evidence and method

The starting application was captured in Chromium on every primary route at 1440×900, 1920×1080, 820×1180 and 390×844. Local originals are in `.local/terminal-depth/before/`. These screenshots use a separate preview database and synthetic fixtures, not the original database. Official product documentation was reviewed independently of the implementation lane. This is a capability and workflow comparison, not a paid-account usability study or a claim of feature parity.

| Workflow | Professional reference | Starting implementation | Decision |
| --- | --- | --- | --- |
| Change the analysis lens | Supercharts has chart configuration, indicators and alternate chart presentations. | Candles and three fixed studies; visibility switches only. | Add OHLC bars, line and area; explicit price/log/percentage/index scales; configurable EMA and Bollinger bands. Keep daily resolution honest. |
| Compare instruments | TradingView supports shared percentage scale, separate scale and separate pane. | No comparison. | Use a dedicated indexed pane with one common session anchor and common-date intersection. Require matching currency, category, provider and price basis. Disclose exclusions. No FX inference or forward filling. |
| Retain analytical context | IBKR Mosaic links symbol context across windows. Koyfin makes sidebar context available beside the active analysis. | Selecting research replaces the chart, yet chart controls remain visible. | Persistent chart with a resizable research inspector. Explicit maximize/restore, standalone full research, and focused mobile research view. Chart controls are hidden when the mobile chart is hidden. |
| Revisit a setup | TradingView distinguishes layouts from indicator templates. | No saved display setup. | Browser-local versioned display settings and eight named templates. Do not imply server sync, drawings persistence or research storage. |
| Inspect a price move | Professional charts expose crosshairs, study settings, navigation and drawings. | Crosshair and basic pan/zoom, no keyboard measurement or annotations. | Exact OHLCV legend, keyboard inspection, two-session close measurement, horizontal price levels and explicit navigation controls. Levels are annotations, never orders. |
| Find saved research | Financial workspaces put comparable records in compact tables. | A long stacked history list in a narrow column. | Search/filter/paginate the private run registry in a semantic full-width table. Keep compact history in the dock. Preserve full identities in links and exports. |
| Inspect an evaluation | Research must show targets, origin, cutoff, benchmark and evidence category. | Existing forecasts, walk-forward/errors, replay and comparison are real, but poorly integrated. | Reuse those contracts. Add target windows, pinned observations, exact CSV for synthetic fixtures, and a compact inspector. Do not invent metrics or uncertainty. |
| Watch and switch | Professional watchlists combine a symbol list with contextual data. | Metadata-only rows and substantial empty space. | Add local list filtering and a selected instrument snapshot drawn only from fetched bars, with session and Demo/Delayed disclosure. Do not fill unloaded rows with invented quotes. |

## Actual visual weaknesses

- The top rows spend space without offering enough analytical control. The toolbar conflates a daily interval with lookback windows.
- The chart dominates the initial screen but is a fixed presentation. Useful research requires abandoning it.
- The watchlist has no filtering and little context beyond company/exchange. Its unused area does not help the selected instrument.
- Research setup and record history compete in a narrow column. Long identifiers and record actions are difficult to scan.
- The same footer can visually imply that a saved synthetic research result belongs to the chart's Demo snapshot. These are separate datasets and must stay separate.
- The previous public wordmark implies a name decision that has not been approved.

## Two evaluated directions

**Instrument console, selected.** A restrained ink surface, compact command row, distinct chart tool rail, watchlist/context sidebar and research inspector dock. Display controls live beside the chart; research records use tables rather than cards. This gives customization and linked context without rewriting API ownership.

**Research folio, retained for standalone research.** A wider document-led layout with prominent methodology, dataset inspection and a full-page run registry. Better for reviewing a complete saved experiment, weaker for comparing an active chart and research at once. The standalone route remains available rather than forcing every workflow into a small pane.

The selection follows the Experience First principle: the chart remains usable during research. Model the Domain shapes versioned display preferences, explicit comparison states and snapshot-scoped measurements. Neither principle authorizes new financial calculations in the backend.

## Sources and boundaries

- [Supercharts configuration](https://www.tradingview.com/support/solutions/43000748166-how-to-configure-your-supercharts/).
- [TradingView comparison and normalization](https://www.tradingview.com/support/solutions/43000543053-compare-see-how-symbols-perform-side-by-side/). This implementation anchors the first **returned common session**, deliberately independent of viewport zoom. The anchor is displayed.
- [TradingView layouts](https://www.tradingview.com/support/solutions/43000746975-tradingview-layouts-a-quick-guide/).
- [TradingView watchlists](https://www.tradingview.com/support/solutions/43000745825-mastering-the-tradingview-watchlists/).
- [Koyfin graphing](https://www.koyfin.com/help/charts-and-graphs/) and [right sidebar](https://www.koyfin.com/help/right-sidebar/).
- [IBKR Mosaic](https://www.ibkrguides.com/traderworkstation/mosaic-layout.htm) and [advanced charts](https://www.ibkrguides.com/traderworkstation/advanced-chart.htm).
- [Lightweight Charts project and license](https://github.com/tradingview/lightweight-charts). Keep the existing Apache 2.0 notices, required attribution link and on-chart attribution logo. This is the open-source library, not Supercharts or the proprietary Charting Library.

Remaining product gaps are material: no multi-chart synchronized layout, general drawing editor, multi-list management, fundamentals/news/events, intraday feed, order entry, qualified historical archive or empirical forecasting evidence. No inactive control is added to imply those capabilities exist. TradingView, Koyfin and IBKR branding, proprietary icons and exact layouts are not copied.
