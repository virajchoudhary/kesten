# Name screening and recommendation

Decision status: five proposals, three recommended for consideration. No name is approved or legally cleared. Screening date: 5 November 2026.

## Naming brief

The brand must accommodate market analysis, forecasts, portfolios, research, backtests, and derivatives without implying profitable predictions. It must sound credible when an analyst cites a report. Avoid `AI`, `alpha`, `quant`, `predict`, exchange names, and superlatives as the main identity. The retired names remain only in historical source references.

The five candidates are Apertane, Basisfold, Cadrisyn, Lattivor, and Tessivane. These are proposed product names, not claims that a company with that name exists. Ranking is editorial judgment, not a measured customer preference.

| Rank | Name and pronunciation | Rationale | Strength | Naming risk |
| --- | --- | --- | --- | --- |
| 1 | Cadrisyn, KAD-ri-sin | Cadre plus synthesis, a disciplined analyst's workspace | Compact, distinctive spelling, institutional tone | Pronunciation and spelling recall are less obvious; `cadri` and `syn` families need deeper similarity screening |
| 2 | Basisfold, BAY-sis-fohld | Financial basis plus bringing several analytical views together | Memorable, concrete, naturally suited to quantitative research | Origami/code use and separate Basis/Fold financial-software brands reduce lexical exclusivity |
| 3 | Apertane, AP-er-tayn | A coined name drawing on aperture and a plane of observation | Open, precise, broad enough for a research platform | Preliminary A(P)ERTAIN software-mark lead raises phonetic risk; official status and similarity remain unresolved |
| 4 | Lattivor, LAT-ih-vor | Lattice-inspired invented word for connected market structure | Has room for several product modules | Exact-string surname/OCR-like occurrence surfaced; lattice-derived software names are crowded; `vor` can sound aggressive |
| 5 | Tessivane, TESS-ih-vayn | Tessellation plus a directional instrument | Analytical but approachable | Existing fictional uses and a fictional cosmetics sample dilute distinctiveness; overlaps the crowded vane naming family |

Recommend Cadrisyn for concept approval, with Basisfold as the strongest plain-English alternative. Apertane remains a developed concept but now carries a specific soundalike review dependency. A concept approval is permission to explore an identity. It is not permission to register, purchase, rename, or launch.

## What the screening actually established

The general web-search tool returned no obvious exact-name financial or software company for these five candidates in the queries below. That is a limited observation, not proof of absence. [general-name-searches.json](general-name-searches.json) preserves the final per-name queries and returned source references. All negative collision conclusions remain inconclusive. Search results can omit small, recent, private, non-English, or unindexed businesses.

| Candidate | General search findings | Public GitHub repositories | Domain registry response | Trademark result |
| --- | --- | --- | --- | --- |
| Apertane | Unrelated archival/OCR and language occurrences surfaced; no obvious exact-name financial/software company in returned results | API returned 0 matching repositories by name or description | `.com`, `.app`, and `.in` returned HTTP 404 from their registry RDAP endpoints | Not verified |
| Basisfold | Origami term and `basisFold` code identifiers surfaced | API returned 0 matching repositories by name or description | Same three registry responses | Not verified |
| Cadrisyn | Exact-string web query returned no results | API returned 0 matching repositories by name or description | Same three registry responses | Not verified |
| Lattivor | An unrelated document includes `Lattivor`; no obvious financial/software company in returned results | API returned 0 matching repositories by name or description | Same three registry responses | Not verified |
| Tessivane | Fictional characters and an explicitly fictional serum sample surfaced | API returned 0 matching repositories by name or description | Same three registry responses | Not verified |

The connected GitHub repository search returned no repositories for the five names joined with `OR`. Separate public GitHub repository-search API requests supplied per-name receipts without credentials. The query was `<name> in:name,description`, with five returned items requested. These checks did not establish availability of private repositories, every code identifier, packages, organizations, or handles. The exact request URLs, counts, HTTP statuses, and UTC timestamps are in [public-name-checks.json](public-name-checks.json). The connected search is recorded in [connected-github-check.json](connected-github-check.json).

The `.com` RDAP requests used Verisign. Follow-up requests used IANA's published endpoints for Google Registry `.app` and NIXI `.in`. HTTP 404 means no registration record was returned at that time. It does not establish registrability, price, absence of a reserved name, future availability, or rights to use the word. The `.in` response additionally says registration is available, but no registrar checkout was performed. No `.io`, `.ai`, country-market alternatives, premium pricing, social handles, or defensive registrations were verified. See [domain-checks-followup.json](domain-checks-followup.json). The initial `.app` hostname was incorrect and failed DNS; the follow-up supersedes that attempt.

## Search engines and reproducible queries

The shared web-search tool was used for exact names and combinations with finance, software, trading, company, GitHub, and trademark. Its underlying engine coverage is not exposed. Direct Google and Bing requests were also made for all five names with `finance software`.

Google returned a redirect/script shell with no usable result listings. Bing RSS returned unrelated fallback items without the candidate strings. These are **inconclusive second-engine checks**, despite HTTP 200. They are not negative collision results. [search-engine-checks.json](search-engine-checks.json) retains visible Google text, request URLs/status/times, and counts of returned versus candidate-matching Bing items. Irrelevant RSS article text was omitted. A human browser check on both engines remains required before a public naming commitment.

Repeat each of the following for every candidate, with and without quotation marks:

```text
"Apertane"
"Apertane" finance software trading company
"Apertane" site:github.com
"Apertane" trademark
"Apertane" site:uspto.gov
```

An additional preliminary search covered `Apertaine`, `Apertain`, `Apertana`, `Cadri Syn`, `Cadresyn`, `Cadrisin`, and `Basis Fold` with financial/software terms. It surfaced an [IndiaFilings listing for A(P)ERTAIN](https://www.indiafilings.com/search/apertain-tm-2966343), application 2966343, describing class 9 software. This is a third-party lead. Its displayed status is not an authoritative current registry result, and no legal similarity conclusion is made. The primary Apertain site could not be read. The lead is enough to lower Apertane's recommendation rank pending counsel's review.

The same pass surfaced [Basis accounting software](https://www.getbasis.ai/) and [Fold personal-finance software](https://fold.money/faq). Neither is an exact Basisfold match. Their use of the component words increases the need to assess overall similarity and distinctiveness. Cadrisyn's queried variants returned no obvious matching company in the returned results; that remains incomplete screening, not clearance.

Search alternate stress, plurals, spacing, translations, `Lattivore`, and `Tessi Vane` in intended markets before commitment. Comprehensive phonetic, figurative, and legal similarity searches remain uncompleted. Do not treat exact-string screening as a substitute.

## Trademark access and remaining work

| Registry | Access observed | Verification limit |
| --- | --- | --- |
| [USPTO trademark search](https://trademarksearch.uspto.gov/) | Web tool could not access the search application | No database search completed and no negative result established |
| [WIPO Global Brand Database](https://branddb.wipo.int/) | CAPTCHA challenge page | No marks searched; challenge was not bypassed |
| [IP India public search](https://tmrsearch.ipindia.gov.in/tmrpublicsearch/) | OTP and CAPTCHA login interface | No account, OTP request, or marks search performed |
| [TMview](https://www.tmdn.org/tmview/) | Application returned no readable records | No marks searched and no clearance conclusion |

Indexed trademark searches also returned no relevant official records for the first group of exact names. Registry indexing is incomplete. Record-level statuses, owners, goods, classes, phonetic similarity, common-law use, and pending applications remain unverified for all five.

Before approving public use, establish the legal entity and intended markets. Commission a professional exact and similarity search covering at least software and SaaS, financial analytics, and any actual financial services. Nice classes 9, 42, and potentially 36 are a starting scope for counsel, not a legal classification decision. Check India, the US, and any intended EU/UK distribution separately. Company-name and domain availability are separate questions.

## Candidates excluded during discovery

| Name | Evidence that changed the decision |
| --- | --- |
| Orivect | An [existing trading platform](https://orivect.com/platform) uses the exact name. Excluded for direct category overlap |
| StrataVane | An [existing market-intelligence product](https://stratavane.com/about) uses the exact name. Excluded for direct category overlap |
| Northlattice | [NorthLattice Systems](https://northlattice.com/) uses the exact name in technology services. Excluded for software/analytics adjacency |
| Veltrane | [Veltrane's financial disclosure](https://www.veltrane.com/financial-disclosure) describes a financial-adjacent service. Excluded |
| Veldrith | A [public graphics library](https://github.com/Stellution-Studios/Veldrith) uses the exact software name. Excluded |

Other exploratory words were dropped when company or product results appeared. They are not alternatives awaiting approval. Screening a name does not endorse any site encountered.

## Sources and evidence limits

The [origami dictionary](https://papirfoldning.dk/ordbog/ordbog_en.html) supports the lexical collision for Basisfold. The [Capafy product sample](https://capafy.ai/ar/agent/product-video-ads-exact-price-tiktok-reels/1985006723) explicitly describes the Tessivane example as fictional. [Echoveil's fiction](https://echoveil.gg/universe/factions) supplies another exact-name use. None of those sources establishes trademark ownership or the absence of competing rights.

The public JSON receipts support transport, repository counts, and registry status only. They are time-stamped discovery evidence. Recheck before any registration or launch.
