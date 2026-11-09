# Kerquant product-quality audit

9 November 2026. Local work on `codex/cadrisyn-foundation`, starting at `163fd042f12eb9f390dc6843474c6fc9c6e3afbf`. This is an audit and correction of the existing terminal, not a replacement architecture or a claim of commercial-terminal parity.

## Method and scope

The parent inspected the authenticated application in a real Chromium browser at desktop and phone sizes, including chart settings, instrument search, research history and account navigation. Separate read-only agents examined market and research workflows. Findings were accepted only after checking source and reproducing behavior. The production-build Playwright harness supplies repeatable acceptance and screenshot evidence. Preview accounts, invitations, synthetic evaluations and watchlists use the isolated `.local/terminal-depth/preview.sqlite3`, never the original database.

The competitive comparison uses TradingView's public Supercharts interface, including its settings panel, and official product documentation. Koyfin coverage is documentation-based; no authenticated Koyfin session or paid account was used. Comparison is qualitative and task-based. It does not assign invented usability scores, performance figures or feature completeness percentages.

### Professional reference comparison

| Workflow | Reference evidence | Kerquant observation and disposition |
| --- | --- | --- |
| Find an instrument and return to the chart | TradingView documents contextual quick search and a dedicated symbol toolbar. | The existing command dialog has keyboard navigation, but selecting a symbol bypassed its reset handler. Fixed the stale query on reopening. |
| Configure a chart while seeing the price action | Supercharts separates settings from chart navigation and supports selective chart configuration. Its public settings interaction was inspected directly. | Kerquant already has chart types, scales, overlays, crosshair readouts, measurement, comparison and saved layout settings. The settings panel unnecessarily stretched over most of a phone chart. Fixed content sizing while preserving bounded scrolling. |
| Move between chart, watchlist and research | Koyfin documents chart tools and a context-sensitive right sidebar. TradingView documents layouts and watchlist workspace organization. | Preserve the existing chart-first workspace, collapsible watchlist and research dock. Switching research tabs could discard an in-flight evaluation response. Fixed the component lifetime across dock tabs. |
| Inspect a selected saved evaluation | Both reference products emphasize preserving context while changing the object under inspection. This is a design inference from their documented navigation, not an assertion about their research models. | Standalone Open/Compare changed the exact URL but left the phone viewport below the selected result. Added native section navigation and result anchors without changing run identities. |
| Maintain a coherent application shell | Reference terminal navigation remains recognizable around auxiliary workflows. | Account had its own reduced header without Research, theme or sign-out. Reused the terminal header with an explicit current Account state and preserved guidance links. |
| Understand data and numerical meaning | Reference chart features are not evidence of Kerquant's entitlement or model validity. | Keep Demo market data and synthetic research visibly distinct. No qualified historical archive or empirical forecasting performance is established by this work. |

Sources, consulted during this audit:

- [TradingView Supercharts introduction](https://www.tradingview.com/support/solutions/43000746464-getting-started-with-supercharts/).
- [TradingView chart configuration](https://www.tradingview.com/support/solutions/43000748166-how-to-configure-your-supercharts/).
- [TradingView quick search](https://www.tradingview.com/support/solutions/43000659671-quick-search-on-tradingview-find-anything-super-fast/).
- [TradingView layouts](https://www.tradingview.com/support/solutions/43000746975-tradingview-layouts-a-quick-guide/).
- [Koyfin charts and graphs](https://www.koyfin.com/help/charts-and-graphs/).
- [Koyfin right sidebar](https://www.koyfin.com/help/right-sidebar/amp/).

No proprietary assets, icons, branding or interface layout were copied. The approved Kerquant measured-frame identity and current visual system remain.

## Accepted findings and corrections

| Priority | Reproduced problem | Correction | Regression evidence |
| --- | --- | --- | --- |
| P1 | An evaluation accepted by the API lost its completion when New evaluation was unmounted by a dock tab switch. | Keep the evaluation subtree mounted with native `hidden` across dock tabs. Existing instrument/account/unmount boundaries still apply. | Real API response delayed after server acceptance; switching to Saved runs must still select the returned exact run once. Unit coverage checks request signal, idempotency key and one submission. |
| P2 | Mobile chart settings had a large empty body that obscured the plot. | Remove forced bottom positioning, retain viewport-constrained maximum height and internal overflow. | Baseline panel was 526.16px tall; the phone regression requires a short panel below 75% of the chart height, visible price scale and restored trigger focus. This is a geometry assertion, not a performance benchmark. |
| P2 | Selecting MSFT and reopening search retained MSFT instead of resetting the search dialog. | Use the existing close/reset handler for successful selection. | New unit and real-browser scenarios failed on baseline and check empty reopened input plus available options. |
| P2 | Opening a saved result on a phone updated the route but left the result outside the viewport. | Shared section IDs, Setup/Results/Saved runs anchors and standalone result links with a native fragment. Embedded routes retain their existing scrolling behavior. | Exact saved ID and dataset identity remain; browser asserts the selected results heading enters the viewport. |
| P2 | Account navigation omitted research, theme switching and sign-out, unlike the rest of the terminal. | Use the shared terminal header; account state, pending/error sign-out handling and original security form remain. | Unit success/failure paths, account browser navigation and responsive theme checks. |

The current chart already supports candles, bars, line/area, price scales, volume, SMA/EMA/Bollinger/RSI, synchronized comparison, measurement, level tools, keyboard access and persistent settings. Those features were retained and exercised, rather than replaced by a visually simpler chart. Crosshair legend updates and Escape focus restoration were inspected and did not justify new changes. No chart library, dependency or numerical calculation was changed.

### Design choices

Reusing the terminal header was preferred over patching a second account-specific navigation tree. Native section links were preferred over turning standalone research into mutually exclusive tabs, which would hide source context and introduce more component lifetime changes. Keeping the dock form mounted was preferred over a new job queue or request manager for this bounded navigation defect. The settings fix changes actual chart visibility without adding new panels or dashboard cards.

The new research navigation follows the existing dense, restrained typography and surface tokens. It works in both themes. Keyboard focus remains visible. Result/history targets are focusable; no positive tab order, focus trap, custom scrolling framework or animation dependency was added.

## Verification and evidence

See [verification](verification.md) for final results, reproduction commands, preservation receipts, independent review and environmental limitations. The [visual review](visual-review.md) explains the before/after images in `evidence/`. Full ignored runtime evidence remains under `.local/product-audit-nov9/`.

## Remaining product and release gaps

- Data entitlement and a legally qualified historical archive remain prerequisites for real market research. Demo prices and synthetic evaluation metrics do not establish investment usefulness or empirical accuracy.
- Tab switching now preserves pending evaluations. Leaving the page or changing an instrument/model context is not a durable background-job contract. The UI must not imply server cancellation from a browser abort.
- Broad commercial-terminal functionality, exchange coverage, news/fundamental screening and intraday feeds are outside this task. Missing entitlements are not filled with simulated live data.
- Firefox access timed out before a usable audit session. Chromium is the automated and final visual acceptance engine. WebKit, physical touch devices, assistive-technology sessions and external usability testing remain unverified.
- Existing PostgreSQL, container recovery and release engineering qualifications are preserved, not rerun or newly certified by this frontend-only correction. Four PostgreSQL-only backend cases were skipped locally. Hosted CI and production deployment were not run.
- Branding/legal clearance remains separate from this local product work. No domains, repositories, public metadata services or production systems were changed.
