# Terminal overhaul evidence

These are local software and visual checks from 2026-11-07. All plotted prices and research results in the screenshots are explicitly synthetic. No historical archive, investment performance, live feed, hosted CI result or production deployment is qualified here.

## Rendered comparison

| Viewport | Before, isolated `f50be38` source snapshot | After, production-mode frontend |
| --- | --- | --- |
| 1440x900 | [Markets](before/markets-1440.png), [research](before/research-1440.png) | [Markets](after/markets-1440.png), [research](after/research-1440.png) |
| 1920x1080 | [Markets](before/markets-1920.png) | [Markets](after/markets-1920.png) |
| 820x1180 | [Markets](before/markets-820.png) | [Markets](after/markets-820.png) |
| 390x844 | [Markets](before/markets-390.png), [research](before/research-390.png) | [Markets](after/markets-390.png), [research](after/research-390.png) |

Both folders contain account, data and methodology captures at the same four browser viewport sizes. The after folder also contains desktop/phone sign-in captures. These are full-page screenshots, so an image's total height may exceed its browser viewport height. Review accounts and saved identities are disposable, account-private synthetic fixtures, not original user records. Each final viewport uses a fresh browser context with the dedicated review session.

[Graphite terminal](direction-a-graphite.png) and [research folio](direction-b-folio.png) are rendered direction studies. Folio is a temporary browser style/layout study applied to the working chart. It is not an extra shipped theme or an unfinished feature shown as complete.

## Verification receipts

- `build-qualified.txt` records the final optimized build and its TypeScript pass.
- `unit-delivery.txt` records all 77 frontend unit tests.
- `lint-delivery.txt` records the final lint gate.
- `browser-paced-final.txt` records the rate-respecting runner. The constituent suites must all pass; no retries or security-limit changes are added.
- `backend-summary.json` is a parent-authored summary of observed backend execution, explicitly not a raw backend log. It records 132 passed and four PostgreSQL-only skips, schema equality, migration checks and 18 recovery unit passes.
- `navigation-before.txt` records the failing browser reproduction before URL selection became authoritative.
- `preservation.json` records the original database hash, all 496 runtime files, all 17 research artifacts and the retained shared-credential comparison.
- [Independent reviews](REVIEW.md) distinguish source findings, visual scope, corrections and parent-owned runtime acceptance.

The optimized frontend runs locally against an isolated development API and new SQLite review store. This is production-mode frontend validation, not a full production infrastructure qualification. Existing PostgreSQL/container recovery evidence is retained; these infrastructure workflows were not rerun during the UI priority change. Four PostgreSQL-only tests are reported as skipped, not PASS.

The current browser suite covers actual API authentication, watchlist changes, source failure/retry, symbol/range switching, indicators, themes, narrow widths, accessibility scans, private research execution, comparison compatibility, replay and exact export, account activation/reset/revocation and cross-tab account isolation. The terminal scenario adds exact crosshair OHLC checks, chart settings/reset, a collapsible watchlist, integrated run identity, Back navigation and mobile focus return.

`inventory.json` records collected file hashes and sizes. Collected text receipts normalize line endings and trailing whitespace; private original outputs remain in ignored `.local/ui-overhaul/`. The inventory uses canonical LF line endings so Git's Windows conversion does not invalidate it. PNG bytes remain unchanged. Run `python docs/implementation/evidence/ui-overhaul/verify_inventory.py` to check it. No credential file, cookie, token, database, private API log, model artifact or original research record is included.
