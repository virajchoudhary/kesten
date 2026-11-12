# Kerquant public publication preflight

Assessment date: 13 November 2026. **Publication is blocked. No push, pull request, merge, deployment, purchase, or remote configuration change occurred.**

The user authorized publication to `virajchoudhary/stock-predictor-system`, conditional on stopping when sensitive material or a serious blocker is found. This report applies that condition. The application can launch from a fresh local clone, but its current publication tree/history has not passed the protected-data gate.

## Exact source and remote

| Item | Observed value |
| --- | --- |
| Public repository | <https://github.com/virajchoudhary/stock-predictor-system> |
| Local source | `codex/cadrisyn-foundation`, `16fa306fb349e2eeeaf9f3f0f2df756f0f5c1397` |
| Fetched public main | `472b87b26425b15e7cf1b7c27fafd00315c762ab` |
| Local commits not reachable from public main | 75 |
| Fresh clone | `.local/publication-20261113/fresh-checkout`, cloned locally with `--no-hardlinks --single-branch` |
| Published Kerquant commit | None |

The local and public histories have diverged. No force-push or replacement of public `main` was attempted. A full fetch encountered remote branch names differing by case on Windows; a targeted main-only fetch succeeded. No lock file or remote branch was deleted.

## Publication findings

| Finding | Evidence and disposition |
| --- | --- |
| Original database is tracked | `backend/db.sqlite3`, blob `9bfd81c14cabd4b0a909befd2c2b71772e3f1cf0`, 204,800 bytes, exists identically in source and public main. The committed copy has zero account/session rows but contains optimized-model, searched-symbol, and scheduler records. Only schema/counts were read from an isolated copy. No claim that it contains active credentials is made. It must not be included in a new portfolio source tree. |
| Seventeen protected research artifacts remain tracked | Ten RL model ZIPs and seven progress JSON files under `backend/api/rl_models/` and `backend/api/rl_progress/` exist identically in source/public main. Their bytes are not newly outgoing Git objects. The existing research record says the bundles lack frozen data/split/provenance evidence. Source-data rights and contents of serialized bundles are not cleared for republication. They must be retained locally and omitted from the portfolio tree. |
| Protected runtime payloads are excluded from the source tip | None of the 496 runtime-manifest paths appears in the source tree. Their payloads are already reachable from public main/history. No new copies were staged. |
| New preservation manifest is metadata only | `docs/implementation/evidence/preserved-untracked-runtime-files.json` contains 496 relative path/hash/size entries, no absolute paths, credentials, secret-named entries, or file contents. This is not evidence of a leaked credential. It exposes local preservation bookkeeping and is unnecessary in a public portfolio package. |
| Historical development secret | A pre-existing public Django settings blob contains a `django-insecure-` default. It is absent from current source settings and is not newly outgoing. Masked log entries are not unmasked credentials. No active production use or credential compromise is established. Removing a later file does not erase its historical copy. |
| Strong token/private-key scan | The parent scanned 1,948 unique blobs reachable from source and public main, about 70.5 MB. No matches appeared for the implemented private-key, AWS, GitHub, Slack, Google/OpenAI key, or JWT patterns. A separate reviewer inspected 1,343 newly reachable blobs, about 28.3 MB, and found no new strong credential payload. |
| Text candidates | The parent retained 325 pattern matches, including 168 outgoing candidates. They comprise test literals, URL/environment interpolation, SQL parameter references, public CA bundle certificates, and pre-existing development defaults. Counts are candidate matches, not confirmed secrets. No credential values appear in the report. |
| Scan limits | No dedicated Gitleaks/TruffleHog executable was available. Pattern checks do not prove that arbitrary or encrypted secrets are absent. Compressed/serialized models were not loaded. Historical image evidence was not exhaustively visually cleared for private content. These limits prevent a blanket "history is secret-free" claim. |
| Unrelated work | Existing uncommitted database, CI, configuration, research, and test changes were not used in the fresh clone or staged for this task. |

The independent reviewer accepted the absence of newly outgoing strong credentials/data payloads but withheld publication clearance for preservation metadata classification. The parent classified that manifest as metadata only. The parent still withholds publication because the current tree republishes explicitly protected, scientifically unqualified artifacts and a runtime database, and the preserved history cannot be described as a clean data-free portfolio history.

## Fresh-checkout verification

The source clone received its own new `.venv` and `web/node_modules`. No original environment, ignored credentials, or dirty source file was copied into it.

| Check | Result |
| --- | --- |
| Documented Windows setup | Passed with locked Python requirements and `npm ci`, 526 frontend packages installed. Initial restricted execution and repeated DNS retries failed; normal approved execution with bounded network retries completed. TLS verification and dependency pins were unchanged. |
| Backend and configuration | 166 tests ran, 162 passed, 4 PostgreSQL-only tests skipped under SQLite. No migration drift. OpenAPI matched. Existing `security.W021` HSTS-preload warning remained. |
| Frontend unit tests | 134 passed across 38 files. |
| Frontend lint and TypeScript | Passed. |
| Optimized frontend build | Passed with all 12 generated pages. |
| Startup/account-preservation regressions | 10 committed tests passed. Account/password changes, dataset/run identities, numerical results, and watchlist edits survive repeat preparation. |
| Actual Chromium journey | Passed sign-in, symbol switching, synthetic research execution, exact replay, export run identity, and desktop/mobile captures. No page errors. API health returned 200. |
| Runtime configuration | Full launcher used `--build --web-port 3012 --api-port 8012`. Only synthetic data was enabled, under the clone's `.local/portfolio-demo`. |

The earlier 168-test dirty-checkout receipt included two uncommitted local tests. The fresh committed clone has 166 tests. These counts are kept separate.

The standalone browser verifier initially used a five-second default and an exact instrument heading without its appended ticker. Both verifier defects were corrected to the repository's ten-second assertion convention and the actual accessible heading. The application source was unchanged.

The [existing portfolio guide](PORTFOLIO.md) remains the supported procedure. Linux/macOS startup, other browser engines, hosted CI, PostgreSQL, container recovery, and image-security rescans were not repeated in this publication preflight.

## Prepared documentation

The local README now leads with the actual product capabilities, desktop screenshots, synthetic-data disclosure, pinned setup commands, architecture, verification boundaries, and production restrictions. It explicitly warns that public main has not yet received this implementation. It does not claim public publication, empirical forecasting validity, or trademark clearance.

The [sanitized verification summary](implementation/evidence/publication-20261113/verification.json), [fresh desktop market capture](implementation/evidence/publication-20261113/fresh-markets-desktop.png), [fresh research capture](implementation/evidence/publication-20261113/fresh-research-desktop.png), and [fresh mobile market capture](implementation/evidence/publication-20261113/fresh-markets-mobile.png) accompany this report. Full local logs and reproducible checks remain under `.local/publication-20261113/`. Credentials, raw scan candidates, binary objects, and databases remain outside staged publication documentation.

## Safe continuation after the data decision

Publication authorization is recorded. What remains is the handling of already-public protected data/history, not a request to authorize the same push again.

1. In an isolated publication checkout based on the then-current public main, prepare an additive portfolio commit from approved source files.
2. Omit databases, runtime state, model/progress archives, private certificates, credentials, and unnecessary preservation metadata from that commit's tree. Keep every original file and the local development history intact.
3. Explicitly record that these old payloads remain reachable in the existing public history. A normal deletion commit cannot purge them. Any purge requires a separate history-rewrite/host-removal decision; this task forbids force-push.
4. Recheck all new objects and screenshots, verify the exact sanitized commit in a fresh clone, and obtain independent acceptance of the selected publication boundary.
5. Push only a new publication branch with normal Git semantics and open a reviewed pull request. Respect protected-branch/required-check controls. Do not use production NO-GO as permission to disable security checks.

Until the existing protected-history disposition is explicit, this task stops before all public writes. No active secret is asserted from a pattern match. No original database or protected artifact was deleted, rewritten, or deserialized.

The Prove It Works principle required installation and real Chromium use from a committed fresh clone. It also kept the public-tree findings distinct from newly outgoing Git objects.
