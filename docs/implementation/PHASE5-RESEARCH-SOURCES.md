# Historical source qualification decisions

Reviewed on 2026-11-09. No historical dataset was accepted, downloaded or evaluated in this phase. Accordingly there are no genuine raw-market-data hashes or acquisition dates to report. Synthetic fixture hashes in the verification evidence are not market-data provenance.

## Existing local holdings

Read-only inspection of `.local/cadrisyn.sqlite3` found one synthetic research dataset and no historical datasets. The retained `.local/terminal-depth/preview.sqlite3` contained 17 synthetic datasets and no historical datasets. These counts describe those inspected stores, not every possible file on the computer.

The original database and protected runtime/research artifacts were hash checked. Unknown pickles and model artifacts were not deserialized to search for prices. Existing CSV fixtures, demo data and generated prices do not become historical evidence through relabeling.

## Candidate assessment

| Candidate and primary reference | Evidence and suitability | Disposition |
| --- | --- | --- |
| [UCI Dow Jones Index](https://archive.ics.uci.edu/dataset/312/dow%2Bjones%2Bindex), DOI `10.24432/C5788V` | Official page describes 750 weekly observations covering the first two quarters of 2011 and lists a CC BY 4.0 license. The records include next-week prices and a future-return label. It does not establish the raw-price/action/vintage evidence required by this daily protocol. | Reject for daily evaluation. Do not interpolate weekly observations or admit future labels as inputs. The repository's license notice does not independently establish underlying exchange-data authority. |
| [Nasdaq WIKI product reference](https://data.nasdaq.com/databases/WIKIP) | Independent source research found indexed first-party product metadata describing community-curated historical prices, a public-domain claim, discontinued support in 2018 and a 9:15 p.m. Eastern update schedule. Direct retrieval during final verification returned HTTP 404. No archive, terms snapshot, action history or value-specific vintage record was verified. | Unqualified. Indexed metadata is a research lead, not current access or rights proof. The described publication schedule also falls outside the v1 close-plus-60-minute window. |
| [UCI Istanbul Stock Exchange](https://archive.ics.uci.edu/dataset/247/istanbul+stock+exchange) | Independent primary-source review identified daily index returns rather than raw individual-equity closes on XNYS. Source and underlying redistribution authority were not established for this application. | Unqualified and outside the current protocol. |
| [UCI CNNpred](https://archive.ics.uci.edu/dataset/554/cnnpred+cnn+based+stock+market+prediction+using+a+diverse+set+of+variables) | Independent primary-source review identified mixed daily index features, not an individual-equity raw-price and publication-vintage archive. | Unqualified and outside the current protocol. |

The latter entries were cross-checked against official UCI metadata during final verification; no market-data bytes were acquired or licensed. Earlier Phase 3.5 provider investigations remain historical evidence. This phase does not assert that their access, prices or terms are unchanged.

## Required source package

Before a historical import, the reviewing operator must establish and retain:

- Provider identity, exact instrument identity and attribution, acquisition timestamp and SHA-256 of the bytes actually received.
- Terms snapshot, source authority and permitted storage, private research, backup and internal transfer. Record whether redistribution is permitted. A restriction on public redistribution must survive research exports and recovery operations.
- Actual observation dates, calendar, gaps, coverage, price basis and complete split/dividend records. Retrospectively adjusted closes cannot be passed off as raw closes.
- Value-specific publication or vintage evidence. A timestamp generated from an exchange calendar is an assumption, not evidence that a price or action was then available.
- Source review reference and limitations, including revisions, survivorship and instrument-selection bias.

The intake format requires one digest per normalized observation as well as a digest of the entire availability document. This binds the supplied value/action record to its claimed availability evidence. It cannot prevent a dishonest or mistaken operator from creating a false claim. `independently_verified_source` therefore remains false.

The importer fetches no URLs. Do not put credentials or signed download parameters in its source records. Do not add a scraper, bypass access controls or purchase a subscription to remove this blocker.
