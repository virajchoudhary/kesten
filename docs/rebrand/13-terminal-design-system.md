# Terminal design revision

This revision implements the later request for a chart-first interface. Cadrisyn remains a configurable working name. It does not approve a trademark, domain, company name or repository rename.

## Two directions and the choice

| Direction | Composition | Strength | Cost |
| --- | --- | --- | --- |
| Graphite terminal | Charcoal canvas, compact horizontal commands, edge-to-edge chart, collapsible right watchlist, switchable research view | Makes daily observations the primary working surface. Research results retain enough width for comparison tables and exact values. | Requires a deliberate switch between chart and detailed research. |
| Research folio | Warm paper, serif wordmark and instrument headings, inset chart, left instrument index | Reads well as an analyst's notebook and suits occasional research sessions. | Inset margins and a permanent index consume chart space. The serif hierarchy adds visual emphasis to labels that analysts repeatedly scan. |

Both studies were rendered with the existing working demo chart, rather than invented market values. The folio study applies temporary browser-session styles and is not a shipped interface. See the implementation evidence for both images.

Choose Graphite terminal. A bottom research dock was also considered in independent review. The current result view contains exact-row tables, comparison evidence, replay and provenance; compressing it beneath a useful chart would require two competing scroll regions. A full research view preserves those controls without creating a second implementation of the research API. The chart stays mounted while the analyst switches views.

## Sources and original interpretation

[TradingView's Supercharts guide](https://www.tradingview.com/support/solutions/43000746464-getting-started-with-supercharts/) describes the central chart and surrounding toolbars. Its [configuration guide](https://www.tradingview.com/support/solutions/43000748166-how-to-configure-your-supercharts/) and [watchlist guide](https://www.tradingview.com/support/solutions/43000745825-mastering-the-tradingview-watchlists/) support compact chart controls and a right-side instrument list. [Koyfin's watchlist documentation](https://www.koyfin.com/features/watchlists/) describes reusable instrument lists as inputs to a research workspace. These sources inform the task hierarchy. Their branding, icon artwork and exact layouts are not copied.

Lightweight Charts remains the existing rendering library. The installed package is 5.2.1 under Apache 2.0. The [official project](https://www.tradingview.com/lightweight-charts/) requires creator attribution and a TradingView link. `attributionLogo: true`, the public license files, the methodology attribution and `web/THIRD_PARTY_NOTICES.md` remain intact. This revision does not add a proprietary charting library or market-data entitlement.

The implementation follows the installed Next.js documentation for asynchronous page search parameters and `next/navigation` navigation. It uses the existing schema parser before passing run, comparison, instrument and method identities to the client.

## Working surfaces

- A 54px application header contains the wordmark, Markets/Research navigation, account access, theme and sign-out controls.
- The market command bar contains symbol search, the fixed daily resolution, available history ranges, indicators, data mode and watchlist toggle. Range buttons change the observation window, not the candle interval. No intraday option is offered.
- A 40px view bar switches Chart/Research. Chart reset and settings use actual chart APIs and state.
- The right watchlist is 282px wide, increasing to 310px on large screens. Closing it returns that space to analysis. Rows show instrument metadata, not invented prices for symbols that have not been fetched.
- The chart height follows the viewport with a desktop minimum. Price uses 72% of pane stretch, volume 10%, RSI 18%. Turning RSI off redistributes space while retaining the logical time window.
- A crosshair legend shows the exact observation date, open, high, low, close and volume. Leaving the chart returns the legend to the latest bar. Exact values remain available through the accessible data table.
- Source evidence opens as a dialog. The chart always retains its compact Demo/Delayed label and an explicit synthetic-data statement when appropriate.
- Integrated research reuses setup, history, results, benchmark comparison, export and replay components. URLs preserve exact immutable identities. Standalone research remains available.

## Tokens and typography

| Role | Dark | Light |
| --- | --- | --- |
| Canvas | `#101214` | `#f2f4f5` |
| Surface/chart | `#15191c` | `#ffffff` |
| Raised control | `#20262b` | `#edf0f2` |
| Primary text | `#e3e8ec` | `#20282e` |
| Secondary text | `#9ba7b0` | `#52616c` |
| Border | `#2b333a` | `#dde2e6` |
| Accent/action | `#8cbacb` | `#17657a` |
| Positive | `#51b59a` | `#08734b` |
| Negative | `#e58b90` | `#ba2434` |

Dark is the default for a new browser. A stored preference remains authoritative. Both themes use the same layout and hierarchy. Inter remains the self-hosted interface face. IBM Plex Mono serves prices, identifiers and chart values. Body text and prices use tabular numbers. Numeric letter spacing remains normal. Tightened wordmark and heading spacing is intentional; it is not applied to financial tables.

Use 1px borders between adjacent working surfaces, square docked regions, 4px controls and 8px dialogs. Shadows belong to overlays. Lucide icons retain a consistent stroke and accessible text names. Icons do not imply unsupported drawing tools, trading, orders or data feeds.

## Responsive and accessible behavior

Below 1100px the watchlist becomes a right-side dialog. Its button reports the dialog's actual expanded state, independently of the desktop panel. Dialog close and Escape return keyboard focus to the trigger. Below 768px history ranges move into a second command row; the chart and research remain full-width. Research setup and results stack rather than compressing a desktop sidebar into a phone.

Preserve native search arrows/Enter/Escape, visible focus, named controls, skip links, chart summaries, exact tables, error announcements and reduced-motion behavior. Loading and failure states never show a previous symbol's data as the newly selected symbol. A failed provider request never becomes demo history. Automated axe checks supplement visual and keyboard review; they are not an accessibility certification.

## Brand recommendation

| Candidate | Product fit | Remaining concern | Recommendation |
| --- | --- | --- | --- |
| Cadrisyn | Formal and broad enough for market analysis and reproducible quant research. Works as a compact terminal wordmark. | Pronunciation and spelling recall need user testing; no clearance. | Retain as the working candidate. |
| Basisfold | Most concrete and memorable; suggests financial basis and repeated research folds. | Existing origami usage and `basisFold` code identifiers weaken lexical exclusivity. | Strong alternative for a research-led identity. |
| Apertane | Suggests a field of observation and supports an open, restrained visual identity. | The earlier blueprint records an unresolved A(P)ERTAIN software soundalike lead. | Keep behind the other two pending specialist screening. |

The 2026-11-07 exact-string search refresh returned unrelated language/OCR matches for Apertane, origami and code/patent references for Basisfold, and no obvious returned exact-name financial/software company for Cadrisyn. Search absence is not availability. [The origami dictionary](https://papirfoldning.dk/da/ordbog/ordbog.html) supports the Basisfold lexical concern. Domain, GitHub and registry observations in the original brand research are dated evidence, not reverified availability. No new trademark-register or domain-clearance claim is made in this UI phase. No stronger new candidate justified interrupting the established product identity.

Cadrisyn's proposed positioning is "Market analysis with reproducible research." Keep it out of the terminal header. The wordmark uses a restrained Inter treatment and three offset planes as a working geometric mark. It carries no growth arrow or promise of returns. `NEXT_PUBLIC_PRODUCT_NAME` configures the display name at build time. Package identifiers, API namespaces, database components and repository naming remain unchanged.
