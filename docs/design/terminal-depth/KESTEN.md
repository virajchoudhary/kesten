# Kesten identity and public-use gate

Decision date: 8 November 2026. The user selected **Kesten** for the platform. This supersedes the earlier shortlist and neutral display label. The selected name is being integrated locally; selection is not legal clearance or publication authority.

## Identity

Kesten is a quantitative research terminal for inspecting market observations and reproducible research. Positioning is factual: chart, compare, evaluate and inspect the evidence. No slogan is needed in the terminal. Do not imply forecast accuracy, live-market entitlement, brokerage services or an affiliation with similarly named businesses.

The mixed-case wordmark uses Inter Variable at a restrained medium weight with close optical spacing. A simple original open-stroke K provides a small navigation/favicon mark. It is a geometric initial, not a candlestick, exchange symbol or proprietary terminal logo. Dark surfaces remain ink and blue-gray, with a muted warm mark and subdued cyan interaction accent. IBM Plex Mono remains reserved for prices, dates, scales and identifiers. Light mode retains darker contrast-appropriate chart colors.

`web/src/lib/brand.ts` owns the default name and short label. `NEXT_PUBLIC_PRODUCT_NAME` and `NEXT_PUBLIC_PRODUCT_SHORT_NAME` override them at build time. The shared mark is `web/src/components/brand-mark.tsx`; the local application icon is `web/src/app/icon.svg`. Root metadata derives its title/application name from the brand configuration. Headers, public pages and authenticated routes share it.

Existing package/environment names, database roles, browser-storage keys, dataset source IDs, export schema identifiers and immutable research documents retain their previous identifiers. They are compatibility and provenance contracts, not current public branding. Display names can change without a data migration. New download filenames use the neutral `research-<run-id>` prefix; export contents and run identities are unchanged. No Git history rewrite or repository rename is performed.

## Read-only conflict screen

Checked 8 November 2026. **Public rebranding is blocked pending legal review. There is a material exact-name finance/software conflict.**

| Surface | Current evidence | Decision/limit |
| --- | --- | --- |
| Finance software | An existing [Kesten expense-tracking product](https://kesten.io/en) operates under the exact name, with a [Google Play finance app](https://play.google.com/store/apps/details?id=io.kesten). | Directly relevant naming conflict. Do not claim a unique or cleared fintech name. No assets, logo or marketing copy from that product are reused. |
| Financial services | [Kesten Financial Group](https://kestenfinancialgroup.com/home) is an existing financial-services business. | Additional financial-sector similarity risk. No affiliation is implied. |
| `kesten.com` | Authoritative COM RDAP returned 200 and a registered domain record, with registration in 2001 and recorded expiration in 2027. | Registered; no availability, transfer, purchase or acquisition entitlement. |
| `kesten.app` | Public RDAP returned 200 and a registered domain record. | Registered; no purchase authorized. |
| `kesten.io` | RDAP gateway returned 404, while the primary product site resolves and operates on this domain. | The gateway result is inconclusive and **does not mean available**. Treat the domain as in use. |
| GitHub names | Public search returned 44 name matches, including exact-name repositories `AsaoluElijah/kesten`, `karabijavad/kesten`, and `OscarUrielCZ/kesten`. The public lookup for the current owner's `/Kesten` target returned 404. | Repository names are owner-scoped. A public 404 does not exclude a private repository, reserve a name or establish rename permission. No authenticated namespace reservation or repository change was made. |
| Official trademark evidence | The [Bosnia and Herzegovina IP office's 2010 gazette](https://ipr.gov.ba/upload/documents/dokumenti_podstranice/glasnici/1_2010.pdf) contains a KESTEN word/design mark entry for KESTEN d.o.o., BAZ 069603. | Historical official record; present validity, classes relevant to this product and renewal status have not been established. Do not call it an active software registration or treat it as clearance. |
| USPTO/WIPO | [USPTO search](https://tmsearch.uspto.gov/) yielded no readable candidate result set in this workflow. [WIPO Global Brand Database](https://branddb.wipo.int/) presented an anti-automation challenge. | No bypass attempted. No completed current exact/similarity/class search. India and other target jurisdictions also remain unverified. |

Raw HTTP outcomes, timestamps and query URLs are retained in [kesten-checks.json](kesten-checks.json). The checks establish obvious conflicts and limitations, not worldwide trademark status. An attorney or qualified reviewer must assess intended markets, similarity and relevant goods/services before public use. This work does not claim that the name is available or approved for commercial release.

## Publication boundary

Local implementation may continue under the user's selected name. Do not publish a public repository/site, rename the remote repository, buy/reserve domains, claim trademark registration, deploy, or represent the identity as cleared. A legal conflict may require changing the central display configuration and mark without touching scientific records, accounts or data. The current record is deliberately sufficient to revise the name without restarting the product work.
