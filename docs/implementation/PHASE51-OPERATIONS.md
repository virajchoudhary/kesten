# Reproduce the research recovery qualification

Use a fresh private run directory, a unique Compose project and unused loopback ports. Do not reuse a retained project's volumes, env file or database. The recorded Phase 5.1 project and artifacts are retained under `.local/phase51`; do not overwrite them to rerun this procedure.

## Freeze source and isolate startup

1. Record `git status --porcelain -uall`, HEAD and hashes of unrelated dirty paths. Verify the protected runtime/research manifests and original SQLite hash. Leave the index untouched until only reviewed task changes are ready.
2. Export the intended committed revision with `git archive` into a new `.local` directory. Build from this archive so unrelated working-tree edits and untracked data are excluded. The existing `.dockerignore` excludes databases, secrets, environments, model runtime output and local evidence from images.
3. Generate separate random, URL-safe secrets for Django, PostgreSQL admin, runtime and migrator. Keep the env file private. Never print `docker compose config` with expanded secrets into evidence.
4. Use the archive's `compose.yaml` and a run-local override. Set unique loopback ports for database/cache/gateway and the matching CSRF origin. Set both build arguments `CADRISYN_SOURCE_REVISION` to the frozen full commit. The recorded run used ports 15451/16391/8091.
5. Build API and web images, then start only database/cache. Wait for readiness. Do not interpret Docker being running as PostgreSQL being ready, especially after a host interruption.

The commands below assume your Compose invocation already selects that archive, unique project, private env file and override. `api` uses the constrained runtime role; `migrate` uses the migrator. Do not exchange their credentials.

## Prove the additive upgrade

Create a private `fixtures/credentials.json` under the new evidence directory with a disposable username/password. Mount the checked-in `scripts/qualify_research_postgres.py` read-only at `/qualification.py`, and that evidence directory at `/verification`. The image's backend is `/app/backend`.

Set `KERQUANT_ISOLATED_QUALIFICATION=phase51` only in these one-shot qualification containers. The helper additionally checks DEBUG, PostgreSQL and an explicit expected database. Upgrade preparation refuses a populated target.

```text
compose run --rm --no-deps <probe mounts and marker> migrate \
  python /qualification.py prepare-upgrade --expected-database cadrisyn --evidence-dir /verification

compose up -d --wait api web gateway

compose run --rm --no-deps <probe mounts and marker> api \
  python /qualification.py archive --expected-database cadrisyn --evidence-dir /verification
```

Here `compose` means your full run-specific `docker compose` command; mount placeholders must be replaced explicitly. Preparation migrates the fresh database to research.0001, creates the synthetic fixture and saves both horizon identities. Normal startup applies 0002 with the migrator. `archive` checks that migration record and the old identities, then exercises the actual CSV command. It does not acquire historical data.

Run `seed-watchlist` with the same helper/mounts/runtime role for the populated-terminal browser fixtures. It creates only the known AAPL/MSFT/NVDA instrument references for the synthetic research owner. Those references use Demo bars, not historical research observations.

Use the **committed archive's** `scripts/prepare_browser_fixture.py` with `--configured-preview --research-owner <disposable-user>`, its explicit preview marker and the new database configuration. Its `.local` belongs to the archive, not the original workspace. Retain one-use invitation/reset fixtures before regenerating them.

For the backend suite, provision a separate empty `test_cadrisyn` owned by the migrator. Migrate it with that role. Grant runtime DML, sequence use and test-only TRUNCATE there before `manage.py test workspace accounts research api.test_security --keepdb --noinput`. Do not add the cleanup grants to application databases.

## Backup, restore and compare

Finish source fixture preparation, then stop only the qualification API/web/gateway. Keep its database/cache running. This makes the source snapshot stable during comparison.

```text
compose run --rm --no-deps <probe mounts and marker> api \
  python /qualification.py snapshot --expected-database cadrisyn --evidence-dir /verification

compose run --rm --no-deps <evidence mount> api \
  python /app/scripts/ops/recovery.py backup-postgres \
  --database-url-env DATABASE_URL --output /verification/research-source.dump
```

The snapshot and dump paths must be new. The existing recovery CLI refuses overwrites. Keep the adjacent manifest with the dump; it binds checksum, size and archive listing.

As admin **on the isolated server only**, create `restore_cadrisyn OWNER cadrisyn_migrator TEMPLATE template0`. Do not migrate that target before restore. Supply its migrator URL through a private `RESTORE_DATABASE_URL` environment variable, not a command-line credential.

```text
compose run --rm --no-deps <evidence mount> -e RESTORE_DATABASE_URL migrate \
  python /app/scripts/ops/recovery.py restore-postgres \
  --manifest /verification/research-source.dump.manifest.json \
  --target-database-url-env RESTORE_DATABASE_URL
```

The restore omits source ownership/ACLs intentionally. Before serving it, revoke PUBLIC/runtime database privileges, grant runtime CONNECT, revoke PUBLIC/runtime schema privileges and grant runtime USAGE. Grant SELECT/INSERT/UPDATE/DELETE on restored application tables and USAGE/SELECT on sequences. Configure matching migrator default privileges for future tables/sequences. Do not grant CREATE, TEMP, TRUNCATE, database creation, role creation or superuser to the restored application role.

Run `verify` with `--expected-database restore_cadrisyn` and an explicit runtime DATABASE_URL for the restored target. It compares all table row hashes, intake identities/raw-byte hashes, privilege checks and every saved replay with `source-snapshot.json`. Also run `verify` against `cadrisyn` to prove the source remained unchanged. Do this full-table comparison **before** new browser writes on the restored database.

Use the same helper version for snapshot and verification. The final engineering snapshot schema is version 2. Older Phase 5.1 attempt records are retained separately and must not be silently relabeled. The read-only `privileges` command can check the role boundary without comparing a database that has intentionally received later browser writes. It rejects role memberships and ownership recorded in `pg_shdepend`, including routines and types, as well as the explicit CREATE/TEMP/schema/role flags.

To exercise the SQL negative paths, set `KERQUANT_ISOLATED_QUALIFICATION=phase51` and privately supply `KERQUANT_QUALIFICATION_ADMIN_URL` for the **new isolated `test_cadrisyn` database**, then run `python -m unittest tests.test_research_postgres_privileges -v` in the workspace environment. The tests require PostgreSQL 17, create fresh transactional roles/schemas and roll them back. Never point this opt-in test at a retained or production database.

## Restored application acceptance

Use a run-local override to point only the qualification API at the restored runtime URL. A fresh Redis logical database provides clean test throttle state without deleting old caches or changing rate limits. Start API/web/gateway with `--no-deps --wait` so no source migration service runs.

Set these host variables for the existing Chromium suite:

```text
PLAYWRIGHT_EXTERNAL_SERVER=1
PLAYWRIGHT_PRODUCTION=1
PLAYWRIGHT_BASE_URL=http://127.0.0.1:<qualification-gateway-port>
CADRISYN_E2E_FIXTURE_DIR=<absolute archive/.local path>
PLAYWRIGHT_BROWSERS_PATH=<existing compatible Chromium installation>
```

Run `npm run test:e2e -- --workers=1 --output <new absolute evidence directory>`. Keep traces off and do not reuse the default output directory containing another run's evidence. The server's throttles stay enabled; the research driver respects one bounded Retry-After. Longer or repeated throttling remains a failure to investigate.

After acceptance, verify protected-file manifests, retained SQLite hashes, retained PostgreSQL table hashes and unrelated dirty paths. Keep dumps and tokens private. Record actual image IDs and source labels, not just mutable tags. Stopping only the uniquely named qualification project is reversible; no volume deletion is required.
