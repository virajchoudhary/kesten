# Phase-two verification receipts

Recorded 2026-11-06 for the local private foundation. The parent ran these checks; independent source-review verdicts are recorded separately in [REVIEW.md](../../REVIEW.md). [PHASE2.md](../../PHASE2.md) maps each result to its gate. Secrets, tokens, credentials, database contents and backup archives are excluded.

## Reproduce supported checks

From the repository root on Windows:

```powershell
.venv/Scripts/python.exe scripts/check_backend.py
backend/venv/Scripts/python.exe scripts/check_research.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_recovery.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_workspace_migration.py
```

In `web/`, run `npm run build`, `npm run typecheck`, `npm run lint`, and `npm test`. For source-mode browser checks prepare disposable account fixtures, start the API with `scripts/dev.py --api-only`, and set `PLAYWRIGHT_PRODUCTION=1` before `npm run test:e2e`. Packaged-stack browser checks set `PLAYWRIGHT_EXTERNAL_SERVER=1` and a loopback `PLAYWRIGHT_BASE_URL` and use fresh preview-bound fixtures. See [the operating guide](../../FOUNDATION-OPERATIONS.md).

PostgreSQL tests use an isolated migrated `test_cadrisyn` database with the runtime role and `--keepdb --noinput`. The migration role creates the schema. Only that disposable test database grants TRUNCATE and sequence UPDATE to support Django fixture resets; the application database does not. The CI workflow records this setup. Run `backend/manage.py test accounts workspace api.test_security` with the explicit test PostgreSQL and Redis environment. Do not run these tests against a user-data database.

`verify_role_upgrade.py` creates a new retained legacy-configured PostgreSQL volume, tests its actual role transition and restart, and refuses existing names. `legacy-role-upgrade-v2.txt` is its final output. An initial direct demotion failed because PostgreSQL's original bootstrap role must remain superuser; that failure drove the disabled-bootstrap identity design.

## Scope and limits

- PostgreSQL: 78 pass, no skips. SQLite: 75 pass, 3 PostgreSQL-only skips. These are different database runs of the same 78-test selection.
- Browser: five Chromium scenarios. Market research, account activation/change/revocation, and password-reset invalidation use the actual packaged API/database. Two tests stub account responses for isolated UI behavior.
- Recovery: 17 tests per operating system, plus actual PostgreSQL custom archive/manifest verification, separate-target restore, 20-object fixture comparison and fresh account access. Whole-database security cutover, off-host encryption and retention remain operational gates.
- Workspace transfer: the actual source contained zero restricted snapshots and zero unused token records. Pure regression fixtures cover their exclusion; the zero counts are not evidence of a licensed-provider success test.
- Build: Windows optimized Webpack output and actual Linux API/web images. Forty-seven packaged Python source files match the reviewed tree. Python and Node base images are digest-pinned; other runtime images use explicit versions and still need production digest promotion and OS scanning.
- The cache-outage receipt predates the final database role split; cache handling did not change afterward. The final 13-check smoke and five browser scenarios exercised the separated-role stack.
- Package audits cover the supported pinned inputs at check time. Python audit used `--no-deps` on those inputs and is not a fresh full scientific resolver or OS scan.
- An earlier test run overlapped a database restart and failed. The stable final PostgreSQL receipt supersedes it. A first named-volume CREATE DATABASE crash recovered, without an established root cause; later cold-start, restore and restart checks passed. Production-host qualification remains required.
- All 496 original runtime-file hashes and the original SQLite database hash were checked again at closeout. The separate workspace database legitimately received account/schema changes.
- Hosted CI, deployment, paid services, live data rights, production performance and financial model validity are not established by these receipts.
