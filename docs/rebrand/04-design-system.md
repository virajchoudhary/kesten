# Workspace design system

Status: proposed specification. Token values are design decisions. Contrast results are recorded separately when checked; no accessibility certification is asserted.

## Design intent

The work area resembles a professional market terminal in density and interaction discipline. It has its own layout, typography, colors, language, and identity. Familiar chart gestures, watchlists, and split views are conventions. Do not reproduce a competitor's exact toolbar, proprietary icons, templates, screenshots, marketing claims, or trade dress.

The application prioritizes the active instrument and chart. Evidence appears beside a result, with detailed methodology available on demand. A result must never look more certain because it is more colorful. There is no animated ticker wall, hero gradient behind data, gratuitous glass effect, neon glow, or decorative AI badge.

The Experience First principle changes the scope decision here. One coherent chart-and-research loop ships before a large menu of partially verified tools. The Prove It Works principle changes the release rule. Tokens, states, keyboard paths, and chart alternatives require actual checks before acceptance.

## Semantic tokens

Tokens below apply to the recommended Cadrisyn concept. The alternative brands may replace the identity accent after approval, but must preserve semantic meaning and pass the same checks.

| Token | Light | Dark | Usage |
| --- | --- | --- | --- |
| `canvas` | `#F5F7FA` | `#101722` | Workspace ground |
| `surface` | `#FFFFFF` | `#172131` | Panels, dialogs, chart |
| `surface-raised` | `#EEF2F7` | `#202D41` | Menus and selected table context |
| `text` | `#172338` | `#ECF1F8` | Body and key values |
| `text-secondary` | `#52627A` | `#A7B4C9` | Labels and metadata |
| `border-subtle` | `#D8DFE9` | `#344157` | Nonessential panel divisions |
| `border-control` | `#6B778C` | `#8190AA` | Essential control boundaries |
| `accent` | `#5147BF` | `#BDB5FF` | Links, selected tab text, focus context |
| `action-fill` | `#5147BF` | `#BDB5FF` | Primary action background |
| `on-action` | `#FFFFFF` | `#101722` | Primary action text |
| `positive` | `#08734B` | `#46C89A` | Gains, with a plus sign or directional label |
| `negative` | `#BA2434` | `#FF8C96` | Losses, with a minus sign or directional label |
| `warning` | `#875000` | `#F4C46C` | Stale data, partial availability |
| `focus` | `#5147BF` | `#F4C46C` | 2 px outer ring with 2 px offset |
| `observed-series` | `#304B78` | `#B0C3E7` | Historical line data |
| `forecast-series` | `#7254B5` | `#C5ACFF` | Dashed forecast line |

Use semantic classes through CSS custom properties. Do not scatter literal colors through JSX or chart configuration. Never derive meaning from a theme-specific hex value. `border-subtle` is decorative; focus, inputs, chart data, and selected states use stronger boundaries where needed.

Positive and negative candles have different fills and explicit legend labels. Offer an alternate blue/orange market palette. Comparison series use color plus dash, marker, and direct label. Do not distinguish an actual series and forecast only by opacity.

## Typography, spacing, and surfaces

Self-host Inter and IBM Plex Mono for the recommended Cadrisyn direction, with recorded font licenses. Apertane uses IBM Plex Sans in its alternative concept. Use system sans and monospace fallbacks. Font loading must not hide prices or shift table columns. Use tabular numerals and right alignment for comparable numbers. Avoid monospaced body paragraphs and tiny uppercase tracking.

| Role | Size / line height | Weight |
| --- | --- | --- |
| Marketing display | 40 / 48 px, 32 / 40 px on narrow screens | 500 |
| Page heading | 24 / 32 px | 600 |
| Section heading | 18 / 24 px | 600 |
| Body and controls | 14 / 20 px | 400 or 500 |
| Dense table data | 13 / 20 px | 400 |
| Axis and compact metadata | 12 / 16 px minimum | 400 |

Use the spacing scale 4, 8, 12, 16, 24, 32, 48 px. Compact row height is 32 px, standard is 40 px, touch is 44 px. Control height is 36 px on desktop and at least 44 px for primary touch controls. Dense icon buttons remain at least 24 by 24 px with sufficient spacing, with 32 px preferred. Corners use 4 px for controls, 8 px for dialogs, and 0 px between docked panels. Shadows distinguish overlays only. Data panels use borders and spacing.

## Component contracts

| Component | Required behavior |
| --- | --- |
| App shell | Active page, account menu, data mode, and theme control are discoverable. Page title updates on navigation |
| Instrument search | Combobox with symbol, company, exchange, and currency. Arrow keys navigate, Enter selects, Escape closes. Free text never silently resolves to the wrong exchange |
| Watchlist | Keyboard-operable rows and add/remove actions. Last selection persists per user. Empty state has a single Add instrument action |
| Chart toolbar | Range, interval, price basis, indicator, and table-view controls. No icon-only controls without names and tooltips |
| Chart | Candles or line, volume pane, time and value crosshair, zoom/reset, keyboard alternative, data table. No fabricated bars across holidays |
| Data status | Source, last bar, session state, delay or EOD status, and simulation flag remain visible at the point of use |
| Forecast panel | Origin, target session, horizon, method, artifact version, baseline, and evaluation status. A point forecast never invents an interval |
| Allocation table | Current versus scenario weights, sum, constraints, turnover, and feasibility. Expected values and realized outcomes have distinct columns |
| Run status | Stage and elapsed time with cancel/retry actions when valid. No fake percentage or estimated completion time |
| Evidence drawer | Inputs, source timestamps, versions, caveats, and downloads allowed by license. Focus returns to the trigger on close |
| Dialog | Labelled title, described consequence for destructive actions, initial focus, focus trap, Escape, and focus restoration |
| Toast | Announces saved action, never the sole place an error or stale condition appears |

Buttons have default, hover, focus, active, pending, and disabled states. Disabled controls show a concise reason when the missing prerequisite is not obvious. Forms retain user values after an error. Inline field messages identify the field, problem, and correction. Table sorting exposes direction to assistive technology. Virtualized tables keep headers and keyboard navigation valid.

## Chart language

Use Lightweight Charts for the main price surface, with required license notices and attribution. This is a library choice, not permission to clone the proprietary TradingView application. Advanced Charts is a separate product and is not assumed licensed. See [architecture](06-architecture.md).

Daily EOD is the first release's only interval. The range control changes the displayed span, not the bar frequency. Forecast overlays begin after the origin bar and use the same explicit adjustment basis and currency. A shaded band is labelled with its method and empirical coverage period. A scenario range is never labelled a confidence interval.

Show exchange-local session dates for daily bars. Offer timezone choice for future intraday data. Do not render daily session identifiers as midnight UTC and shift them to the wrong calendar date. Crosshair values show timestamp, OHLC, volume, unit, currency, and price basis. The last value does not imply a live trade.

A failed overlay does not erase a valid historical chart. Preserve chart viewport during refresh. An instrument switch clears or visibly invalidates the old instrument's overlays immediately. No green success treatment for a forecast just because its point estimate is positive.

## Layout and responsive behavior

At 1440 px and above, use a 64 px navigation rail, a 248 px watchlist, a flexible chart region with a 560 px preferred minimum, and a 320 px evidence inspector. The header is 48 px. The inspector can collapse. A lower research strip belongs to the chart context, not a second navigation system.

At 1024 to 1439 px, collapse the watchlist behind a button by default and open evidence as an overlay drawer. Preserve at least 640 px for the primary chart where available. At 768 to 1023 px, use a single content pane with chart/evidence tabs, a modal search, and touch-sized controls. Below 768 px, show one instrument, chart, and scrollable evidence sections. Watchlist and navigation use a sheet. Portfolio matrices use a contained scroll region or per-asset cards. The whole page must not acquire horizontal overflow.

Support a 320 px viewport, 200% text zoom, and 400% browser zoom. Financial tables and charts may use their own two-dimensional scrolling region when necessary, with keyboard access and a clear label. Keep essential actions outside that region. Do not remove data freshness or risk information to save space.

Three layout options were considered at specification level. A dashboard of equal cards fragments the core task. A fully configurable docking terminal costs too much for the first release. The selected fixed workspace keeps a stable chart, watchlist, and optional evidence panel. A usability prototype and visual review follow approval; no user testing or rendered prototype is claimed here.

## Accessibility and motion acceptance

Target WCAG 2.2 AA, using the [W3C recommendation](https://www.w3.org/TR/WCAG22/) as the acceptance reference. Normal text needs 4.5:1 contrast, large text 3:1, and meaningful graphical boundaries 3:1. Automated checks must include both themes and all status tokens. Manual testing covers keyboard, screen reader, zoom, focus, touch, and chart alternatives.

Provide a skip link, semantic landmarks, heading order, labelled controls, visible focus, and non-color status cues. Shortcuts are documented and can be disabled, and never fire while typing in a field. A crosshair must not announce every pointer movement. Announce deliberate selection and run completion through a restrained live region.

The chart's accessible table exposes the visible range and can paginate older rows without rendering thousands of DOM nodes. A text summary states instrument, range, price basis, latest observation, and any missing data. All financial conclusions remain available outside canvas.

Use 120 to 180 ms opacity or position transitions. `prefers-reduced-motion` removes nonessential movement. Do not animate price interpolation, flash quote cells, or use endless shimmer. Loading indicators settle into a labelled state rather than pretending to show progress.

Design approval requires both-theme screenshots at 320, 768, 1024, and 1440 px, plus the affected user journeys and failure states. These are future release gates, not completed tests.
