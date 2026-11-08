# Analysis terminal design

The design serves three tasks: inspect an instrument, change the analytical lens, and inspect the record behind an evaluation. It uses continuous work surfaces rather than a dashboard of cards.

## Structure

The global header owns route navigation, account and theme. The command row owns instrument, daily interval, chart type, studies, comparison, lookback and data mode. A narrow tool rail owns measurement, price levels, display layouts and chart settings. The right sidebar owns the private watchlist, list filtering and the selected snapshot. The plot receives remaining viewport space. All controls are functional with current daily contracts.

Research opens below the plot as an account-private inspector with Selected, Saved runs and New evaluation tabs. The separator supports pointer drag and keyboard arrows/Home/End. Maximize is explicit; standalone research remains the full review surface. Mobile uses focused research content rather than compressed desktop panes. A saved result does not inherit the chart's snapshot or Demo label.

## Tokens and typography

Dark is primary: ink canvas `#0D1116`, panel `#11171E`, raised surface `#1A242E`, rules `#27313D`, primary text `#E3E8EC`, secondary `#9BA7B0`. Cyan accents denote selection/actions, amber denotes provenance/attention. Green and red describe signed observations only. They never imply buy/sell recommendations.

Light uses white work surfaces, cool gray canvas, dark graphite type and darker chart colors. Chart tokens are theme-aware. Inter Variable is the interface face. IBM Plex Mono is reserved for numeric inspection, scales and identifiers. Compact desktop labels are 10–12 px with sufficient line spacing; mobile controls keep usable hit areas. The Kesten wordmark uses restrained mixed-case type and an original open-stroke K mark. It is the selected local identity, not trademark clearance; names remain centralized and revisable.

Price, percentage and index scales normalize all price overlays using one first-returned-session anchor. Log mode changes the primary price pane only; RSI, volume and indexed comparison keep their own units. Bollinger bands are rolling descriptive dispersion, not forecast uncertainty. EMA is seeded with an SMA. Study parameters have validated bounds. Numeric implementation and tests are in the display layer and do not change stored research.

## Interaction and state

- Ctrl/Cmd+K opens instrument search; its existing arrow/Enter/Escape behavior remains. Chart arrow keys inspect exact observations; Enter selects measurement endpoints when the ruler is active; Escape clears the measurement.
- The chart legend always reports raw OHLCV, with currency and session, even when the visible axis is normalized. Scale basis and studies are identified separately.
- Browser-local layouts store display settings and names only. Unsupported/malformed versions fall back safely. Prices, research data, credentials and instrument identities are excluded. Horizontal levels and ruler endpoints are session-local and scoped to the instrument/data mode.
- Comparisons fail visibly on incompatible provenance, currency or insufficient overlap. Requests are aborted when context changes. No hidden fallback to synthetic data.
- Loading, empty, unavailable and authentication states reuse the existing contracts. A chart-render failure leaves the exact daily data table available.
- Research views retain target dates, origins, information cutoffs, model/run/dataset identities and synthetic disclosures. CSV export is exact and formula-escaped, and restricted to synthetic fixtures until historical redistribution permissions are represented by the contract.

## Accessibility and visual acceptance

Use semantic navigation, labeled controls, selected/expanded state, focus-visible rings, proper table headers and a keyboard-operable resize separator. Color is accompanied by numbers/text. Canvas content has keyboard inspection and exact tabular alternatives. Research chart inspection has a keyboard slider, window controls and pinning. Respect reduced motion; no decorative animations.

Acceptance requires rendered Chromium checks at 1440×900, 1920×1080, tablet and mobile, in both themes. Inspect plot visibility, scales, pane labels, long identities, sidebar/dock scrolling, dialog focus, overflow and actual interaction. Automated tests and an accessibility scan supplement this review; they do not establish screen-reader certification or professional-platform parity.
