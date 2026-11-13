# Portfolio publication boundary

Prepared 13 November 2026 from reviewed local source `a6eb94a4d9083cfb9785820b85ef34bfb4bb71ce`, with public main `472b87b26425b15e7cf1b7c27fafd00315c762ab` as the publication parent.

## History and protected files

The publication branch applies an exact allowlist of source/configuration files and reviewed synthetic screenshots. Local development commits are not merged or cherry-picked into its ancestry. Databases, credentials, private certificates, runtime state, model/progress archives, and local preservation metadata are excluded from each new publication commit.

**Historical databases, runtime files, and research/model artifacts already present in existing public Git history remain accessible. Their history has not been sanitized, erased, or rewritten.** A latest-tree removal does not remove earlier objects. No force-push or host-level purge occurred.

Original local databases, all 496 protected runtime files, all 17 research artifacts, and unrelated local modifications remain preserved.

## Scientific and release status

Portfolio use is limited to chart analysis and reproducible synthetic research. No historical archive has passed the point-in-time/rights gate, and no model is claimed to have validated empirical forecasting performance.

Production remains **NO-GO**. Image vulnerability gates, hosted CI, trusted production configuration, and off-host acceptance are separate outcomes. Publication is not deployment approval.

## Verification boundary

The sanitized source at `64abb1979fbb79c7f27329f519b6289f57f7c585` passed a fresh Windows checkout and pinned dependency installation. The follow-up commit restores executable file modes without changing application bytes. A browser-test correction probes external frontend readiness through the proxied session API instead of the backend-only health route.

Verified locally on 13 November 2026:

- Optimized Next.js build, generated API contract consistency, TypeScript, and lint passed.
- All 134 frontend tests passed.
- Django configuration, migrations, API schema, and 166 backend tests passed with four PostgreSQL-only skips under SQLite.
- Six isolated demo-launcher tests, 18 recovery-client tests, two research-client tests, and `pip check` passed.
- All 17 Chromium scenarios passed in one final run using new disposable accounts. They cover authentication lifecycle, private watchlists, charts, research comparisons, exact replay/export, both themes, and desktop/mobile layouts.
- The original database, 496 protected runtime files, 17 research artifacts, and 22 unrelated file hashes matched their retained preservation baseline.
- Independent review classified the 98 literal/URL scanner candidates as test fixtures, disposable CI credentials, invalid-host configuration probes, or environment references. No token, private-key, certificate, or JWT signatures matched. Every new commit tree was checked against the exact file allowlist.

Initial Windows sandbox attempts failed during temporary-directory cleanup and standalone file copying. The same checks passed with ordinary host permissions in the isolated checkout. One mobile history run timed out, then passed its focused recheck and the complete final run. No application security control or test assertion was removed.

This host also inherited an unreachable NVIDIA package index. Fresh setup passed with command-local `PIP_CONFIG_FILE=NUL`, `PIP_INDEX_URL=https://pypi.org/simple`, and an empty `PIP_EXTRA_INDEX_URL`. Package pins and TLS verification were unchanged.

These results qualify the local synthetic demonstration. They do not requalify PostgreSQL, production containers, image security, or off-host operation. Hosted GitHub CI results belong to their exact published head and must be reported separately. This record does not claim hosted checks passed.

## PR review corrections

The replacement publication is rebuilt from public main, using only final reviewed file contents. It does not include PR #15's intermediate publication commits. PR #15 and its branch are preserved, so their earlier fixture literals remain accessible there. No existing branch is rewritten or force-pushed.

Two confirmed Codex findings were corrected:

- EMA and Bollinger studies now calculate over bounded close history from the same validated market snapshot and then restrict output to visible sessions. Their values remain stable when the display range changes. The chart and selected-session legend use the same warmed calculation.
- An authenticated password change revokes that account's outstanding reset tokens inside the existing user-lock transaction. Invalid password changes leave tokens usable, and other accounts' tokens remain unchanged.

Focused tests failed before these fixes. The stale reset link returned HTTP 200 instead of 400; a 50-session EMA on 20 displayed sessions produced zero points instead of 20. The same regressions passed after correction.

GitGuardian's two PR #15 alerts were inspected as an explicit disposable CI password and a mocked Basic-auth header. Both literals were removed from the replacement source. CI now generates new passwords per run, uses restricted PostgreSQL roles, and stores its test database in an isolated temporary container. The Basic-auth test generates its header and verifies credential decoding at runtime. No scanner suppression, detector ignore, or trust-authentication bypass was added.

Local correction checks passed 136 frontend tests and 169 backend tests with four PostgreSQL-only skips under SQLite. A real PostgreSQL 17 run passed all 169 tests with no skips, including concurrency, migration, authentication, role-readiness, and research tests. The CI procedure also has three focused randomness, isolation, and ownership-bound cleanup tests.

Production remains NO-GO. These local corrections do not establish a passing hosted CI or image-security gate. Historical forecasting validity remains unestablished.

The selected screenshots contain synthetic observations and synthetic run identities, not private market data, credentials, or empirical performance. All data-provider acquisition and legal clearance requirements remain separate.
