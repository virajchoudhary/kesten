# Kerquant identity

Decision date: 8 November 2026. The user selected Kerquant as the platform's local product identity. The application uses this name in its default display configuration. This selection does not establish trademark clearance, domain availability, or permission for public release.

## Product identity

Kerquant is a market analysis and quantitative research terminal built around inspectable data and repeatable methods. The product helps a researcher inspect an instrument, configure a baseline evaluation, compare results, and replay a saved run. Its current data and model limits remain visible in the interface.

The `quant` ending signals quantitative research, while the `Ker-` lead distinguishes the spoken form. Exact-name web results also include local-history references to Kerquant as a place or family name, so do not describe the whole string as unique. Confirm pronunciation with intended users before external launch. Use mixed case as `Kerquant`.

The terminal does not need a tagline. Keep interface language concise and specific to the selected instrument, dataset, method, horizon, evaluation period, and data provenance. Do not claim returns, prediction accuracy, live data, trading access, or institutional adoption.

## Visual identity

Use the existing self-hosted Inter Variable family for the interface and wordmark. Use IBM Plex Mono for prices, dates, chart scales, symbols, and run identifiers. Keep the wordmark at a restrained medium weight. The interface remains readable when the wordmark falls back to its full name on narrow screens.

The measured-frame symbol uses two offset right-angle reference frames around a central plane. It represents the relationship between observations and an analytical reference without drawing a rising price, order, or performance promise. The symbol is a compact original vector construction, not a K monogram. Its monochrome treatment keeps the terminal restrained. The application icon uses the same geometry on an ink tile. Do not trace another financial product's icon or use a third-party logo.

The user rejected both the thin K and the later solid split K. The next R&D pass explored four substantially different directions: an aperture, measured frames, a custom wordmark, and interlocking planes. The user selected **02, Measured frame**, from the [exploration board](assets/logo-rnd-directions.png). The selected direction is reconstructed as production SVG and tested in actual headers and the favicon. The [R&D record](LOGO-RND.md) separates research, design judgments, rejected directions, selection, and rendering evidence.

| Role | Color |
| --- | --- |
| Dark terminal canvas | `#0d1116` |
| Dark terminal panel | `#11171e` |
| Dark terminal raised surface | `#1a242e` |
| Light canvas | `#f2f4f5` |
| Light panel | `#ffffff` |
| Main text | `#e3e8ec` dark, `#20282e` light |
| Dark interaction accent | `#8cbacb` |
| Light interaction accent | `#17657a` |
| Brand symbol | `#e3e8ec` dark, `#20282e` light |
| Positive market move | `#51b59a` dark, `#08734b` light |
| Negative market move | `#e58b90` dark, `#ba2434` light |

Use the accent for focus, selected controls, and chart references. Reserve green and red for market direction, with labels or signs as well as color. Keep the mark small and avoid decorative gradients, glow, or finance clichés.

Use the installed Lucide icons for common interface actions. Keep the K as the only custom brand glyph.

## Configuration and compatibility

`web/src/lib/brand.ts` owns the default display name and short name. `NEXT_PUBLIC_PRODUCT_NAME` can override the default. `NEXT_PUBLIC_PRODUCT_SHORT_NAME` can override the short label. When that setting is empty or unset, the short label uses the resolved full name.

Public frontend environment variables are resolved at build time. Rebuild the production frontend after changing these values; restart a development server after configuration changes. The preserved Python display labels resolve their environment at process startup.

The brand mark lives in `web/src/components/brand-mark.tsx`. Next.js serves `web/src/app/icon.svg` through its App Router icon file convention. Page titles and application metadata use the shared brand configuration.

Keep database names, environment variable prefixes, package identifiers, repository names, branch names, protocol fields, storage keys, dataset source IDs, and saved research identities unchanged. These names protect compatibility and historical provenance. A later brand change should update the central display configuration, mark, icon, and user-facing documentation without renaming those identifiers.

When a preserved Streamlit title, API schema title, or local-console label uses Kerquant, that change is display text only. It does not qualify the legacy numerical or ML runtime, establish empirical performance, or promote an experimental model.

## Bounded exact-name screen

Checked 8 November 2026. The screen covers the exact spelling `Kerquant` in accessible general and finance-software search results, the connected GitHub repository search, and registry RDAP for three common domains. It is a preliminary conflict screen, not a legal search.

| Area | Observation | Limit |
| --- | --- | --- |
| Web and finance software | Exact-name web searches for `Kerquant`, finance software, financial services, and trading software returned local-history and genealogy references among the visible results, including a [Pas-de-Calais archive result](https://www.archivespasdecalais.fr/content/download/82832/2273156/file/revuePicardie%2B%2814%29.pdf) that lists Kerquant as a locality. No obvious exact-name financial software product appeared in those results. | Search indexing is incomplete. Similar spellings, unindexed products, private companies, trade names, and other countries were not comprehensively searched. |
| GitHub | The connected GitHub repository search for `Kerquant` returned no matching repositories. | This does not reserve a repository name or check private repositories, every owner namespace, organizations, package registries, or future registrations. No repository was renamed. |
| `kerquant.com` | Verisign's authoritative `.com` RDAP endpoint returned HTTP 404 on 8 November 2026. | No domain object was returned by that query. This does not guarantee that the name is registrable, unreserved, or available for purchase. |
| `kerquant.app` | Google's authoritative `.app` RDAP endpoint returned HTTP 404 on 8 November 2026. The IANA RDAP bootstrap registry maps `.app` to Google Registry. | No domain object was returned by that query. This does not guarantee that the name is registrable, unreserved, or available for purchase. |
| `kerquant.in` | NIXI's authoritative `.in` RDAP endpoint returned HTTP 404 on 8 November 2026. The IANA RDAP bootstrap registry maps `.in` to that endpoint. | No domain object was returned by that query. This does not guarantee that the name is registrable, unreserved, or available for purchase. |
| USPTO trademark search | The official Trademark Search entry point and help page were accessible. The help page documents wordmark searching, including exact-term searches. The search-result query for `Kerquant` did not return a readable result set through this workflow. | No USPTO result was verified. The official search must be completed directly, including related goods and services and similar spellings. |
| WIPO Global Brand Database | The official database presented an anti-automation challenge. No attempt was made to bypass it. | No WIPO result was verified. |
| EUIPO and TMview | The official search portal was reachable, but its interactive result page did not provide a readable `Kerquant` result set in this workflow. | No EU or participating-office result was verified. |
| India Trade Marks Registry | The official IP India search entry point was identified, but an exact-name registry query was not completed. | No India result was verified. |

The domain checks used these registry endpoints:

- [Verisign RDAP for `kerquant.com`](https://rdap.verisign.com/com/v1/domain/kerquant.com)
- [Google Registry RDAP for `kerquant.app`](https://pubapi.registry.google/rdap/domain/kerquant.app)
- [NIXI RDAP for `kerquant.in`](https://rdap.nixiregistry.in/rdap/domain/kerquant.in)
- [IANA RDAP bootstrap registry](https://data.iana.org/rdap/dns.json)

The trademark portals were:

- [USPTO Trademark Search](https://tmsearch.uspto.gov/)
- [USPTO search guidance](https://www.uspto.gov/trademarks/search/federal-trademark-searching)
- [WIPO Global Brand Database](https://branddb.wipo.int/)
- [EUIPO search and TMview information](https://www.euipo.europa.eu/en/search-ip)
- [IP India trademark search guidance](https://ipindia.gov.in/trade-marks-before-you-apply-search-existing-trademarks)

No completed trademark-entry search or legal opinion is recorded. No trademark clearance is claimed. Before external launch, search exact, phonetic, and visually similar marks in the intended markets and relevant software and financial-service classes, then obtain qualified legal review. The local selection does not authorize public branding, a domain purchase, or a repository rename.

## Historical name records

Earlier blueprint and terminal records refer to Cadrisyn or Kesten as names used in their respective phases. Those references are historical, not current naming guidance. Read the [archived product blueprint](../../rebrand/README.md), the [superseded Kesten conflict screen](../terminal-depth/KESTEN.md), and the [earlier terminal delivery record](../terminal-depth/README.md) for their original evidence.
