# Three brand directions

All concepts are proposals. No logo is a finished identity, and no trademark rights are asserted. The shared product promise is a market workspace where each analytical result can be traced to its inputs. Cadrisyn is the recommended concept after a preliminary software soundalike lead raised Apertane's naming risk. The order of the developed concepts below is not their final ranking.

## Apertane

### Position and story

Apertane is a market-research workspace for independent analysts and small investment research teams who move between price action, model evidence, and portfolio decisions. It competes on continuity and traceability, rather than on a claim to predict markets better.

Proposed tagline: **Markets, in perspective.** Use it on the marketing page and an occasional report cover. Omit it from the working application header.

The name suggests an aperture, a controlled field of observation. The coined ending leaves room for derivatives, risk, and research. The narrative is about making assumptions visible. Avoid camera metaphors in the interface.

### Verbal identity

Calm, literate, specific. State an observation, its time window, and its limits. Prefer `Forecast`, `Scenario`, `Observed return`, `Model evidence`, and `Data as of`. Avoid `AI predicts a winner`, `Institutional-grade returns`, `Guaranteed`, `Live` without entitlement evidence, and unexplained confidence scores.

Examples:

- Marketing headline: `A clearer view of your market research.`
- Product description: `Charts, model evidence, and portfolio scenarios in one workspace.`
- Forecast unavailable: `No approved model is available for this instrument.`
- Stale data: `Latest daily bar: 4 Nov. The next session is not yet available.`

### Visual identity

Ink, porcelain, and restrained blue. Brand ink `#152337`, porcelain `#F5F7FA`, action blue `#2454D6`, secondary steel `#61738B`. Financial positive and negative colors remain semantic, independent of the brand accent. App tokens come from the [design system](04-design-system.md).

Use IBM Plex Sans for UI and IBM Plex Mono for identifiers, code, and dense numeric comparison. Use tabular numbers in tables. Use the same family for marketing, with wider spacing and a restrained 40/48 display size. Self-host font files and keep their licenses.

Iconography uses a 20 px canvas with a consistent 1.5 px stroke. Instrument, research, layers, and portfolio icons use familiar shapes. Do not turn every navigation label into a custom symbol.

Logo direction: two offset open planes forming an abstract aperture, with a single deliberate gap. Avoid an upward arrow, candlestick, eye, shutter-wheel cliché, or TradingView cloud silhouette. Build a horizontal wordmark and a separate 16 px monogram test. Require monochrome and reverse versions before any color treatment. No gradient is needed.

## Basisfold

### Position and story

Basisfold is a research platform for analysts who compare several explanations before committing capital. Its distinction is the connection between a market observation, a reproducible experiment, and a portfolio scenario.

Proposed tagline: **Bring the evidence together.**

`Basis` has an authentic financial meaning, but the product is not limited to basis trading. `Fold` suggests views brought together and repeatable research folds. The existing origami use is a naming weakness as well as a source of visual restraint. Avoid claiming that the word was invented.

### Verbal identity

Direct, analytical, slightly warmer than Apertane. Prefer `Compare`, `Review assumptions`, `Save research`, and `Reproduce run`. Describe an optimizer's objective explicitly instead of using `Best portfolio`.

Examples:

- Marketing headline: `Build a market view you can examine.`
- Portfolio action: `Compare allocations`.
- Model result: `This run did not outperform the baseline on the locked evaluation set.`
- Error: `The optimizer could not satisfy these constraints. Review the maximum position limits.`

### Visual identity

Graphite `#182825`, warm paper `#F5F6F1`, evergreen `#17604A`, muted moss `#65756D`. Reserve the brand green for identity and selected controls. Market gains still carry a sign, label, and a separately tested semantic token. This direction needs extra care to avoid implying that every primary action means profit.

IBM Plex Sans is the application typeface. Source Serif 4 may appear in long-form research headings and report covers, never on chart axes or controls. IBM Plex Mono supports tickers and aligned scenario values. Do not introduce a third family into the application shell.

Iconography favors brackets, tables, and layered documents. Logo direction: two folded rectangular planes seen from above, with negative space forming a subtle `b`. No 3D origami illustration. Test against common folded-page software marks during legal and design review.

## Cadrisyn

### Position and story

Cadrisyn is a disciplined analytical workspace for small teams that need a shared method across market research and risk review. It has the most formal tone of the three and the least immediate pronunciation.

Proposed tagline: **A disciplined market view.**

The name draws on cadre and synthesis. Neither is used as a literal feature label. It suggests joined expertise without implying an asset manager, broker, or regulated adviser.

### Verbal identity

Precise, concise, professional. Use `Review`, `Assumptions`, `Evidence`, `Allocation`, and `Method`. Product language remains ordinary English. Avoid institutional cosplay, security badges without proof, and invented abbreviations.

Examples:

- Marketing headline: `One workspace for market analysis and model review.`
- Backtest warning: `Transaction costs are excluded from this run.`
- Research action: `Attach to notebook`.
- Job status: `Queued. Your inputs have been saved.`

### Visual identity

Midnight `#172035`, chalk `#F6F7FB`, indigo `#5147BF`, muted slate `#69748B`. Indigo distinguishes model overlays from observed price. Multi-series charts must still use the shared categorical palette.

Use Inter for UI and IBM Plex Mono for research identifiers and tabular values. Keep display type within the same sans family, with disciplined weight changes instead of decorative typography.

Iconography uses an orthogonal grid with controlled diagonals. Logo direction: two incomplete frames sharing a centerline, forming a compact abstract `c`. Avoid shields, seals, bank columns, and network-node diagrams. A one-color 16 px test decides whether the mark survives.

## Identity approval criteria

Approve one direction only after pronunciation, spelling recall, soundalikes, and legal screening are reviewed. Test the name in a spoken introduction, a browser title, a report citation, and a support email address. These tests have not yet been run with users.

For the selected direction, implementation must deliver a vector wordmark, monochrome mark, favicon, app icon, light/dark lockups, clear-space rules, font license records, and sample report cover. Those are future design deliverables. This package deliberately stops at logo direction.

Brand acceptance requires no performance promise, no false certification, no copied proprietary assets, readable contrast, and a coherent name across the public shell. Existing Python package names can remain internal until a separately tested migration warrants changing them.
