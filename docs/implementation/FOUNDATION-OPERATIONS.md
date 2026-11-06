# Operate the hardened foundation

For current Phase 3.5 container/PostgreSQL qualification and the isolated 8085 preview, use [qualification operations](PHASE35-OPERATIONS.md) and [results](PHASE35.md). The earlier Docker startup blocker is resolved; historical-data qualification remains blocked.

This is a local, private preview. Cadrisyn remains a working name. It does not authorize public deployment or provider purchases.

## Start an isolated container preview

Use a new Compose project name when testing this revision. PostgreSQL initialization runs only on an empty volume; changing environment variables does not update roles in an existing database. Keep older volumes and their data.

Copy `config/.env.example` to an ignored local environment file. Set four different generated values: `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` (URL-safe runtime password), `POSTGRES_MIGRATION_PASSWORD` (URL-safe schema-owner password), and `POSTGRES_ADMIN_PASSWORD` (bootstrap password). Do not use the example strings.

```powershell
docker compose --project-name cadrisyn-preview --env-file .local/preview.env build api web
docker compose --project-name cadrisyn-preview --env-file .local/preview.env up --detach --wait --wait-timeout 360
```

Open `http://127.0.0.1:8080`. PostgreSQL and Redis have no host ports. The gateway binds only to loopback. This HTTP profile deliberately uses development cookies; do not expose it publicly. The migration service completes before API readiness, then the frontend and gateway start. The API and migration service use the same built image.

The database container bootstraps with `postgres`. Only `cadrisyn_migrator` owns the database/schema and runs migrations. The application connects as `cadrisyn`, with table CRUD and sequence usage/read privileges. It cannot create permanent or temporary tables, own public relations, create databases/roles, replicate, or bypass row security. New migration objects receive runtime DML grants through default privileges. Readiness rejects privileged or schema-owning application roles and pending migrations.

For a previously initialized preview, back up first and stop every application/worker connection using its database credentials. Initialization variables do not change an existing cluster. The baseline Compose profile created `cadrisyn` as PostgreSQL's original bootstrap superuser. PostgreSQL requires that original identity to remain a superuser, so a simple demotion cannot work.

Prepare four separate secrets as above, retaining the existing runtime `POSTGRES_PASSWORD`. In PowerShell, substitute the actual retained database container name below. The preparation script creates a separately credentialed `postgres` administrator and constrained migrator only when absent. It preserves existing passwords; if those roles already exist, use their actual credentials. Never print the environment file.

```powershell
Get-Content deploy/prepare-preview-role-upgrade.sql -Raw | docker exec --interactive --env-file .local/preview.env DATABASE_CONTAINER psql -X --set ON_ERROR_STOP=1 -U cadrisyn -d cadrisyn
Get-Content deploy/upgrade-preview-roles.sql -Raw | docker exec --interactive DATABASE_CONTAINER psql -X --set ON_ERROR_STOP=1 -U postgres -d cadrisyn
```

The first command uses the old bootstrap login over the container's local socket. If the existing runtime is already constrained, run preparation as its existing bootstrap administrator instead. The second command must use the separate administrator. It transactionally renames the original bootstrap identity to `cadrisyn_legacy_bootstrap`, disables its login and removes its password, and creates a constrained `cadrisyn` login with the existing SCRAM credential. Non-bootstrap runtime roles are demoted directly. It transfers the database, public schema and public relations to the migrator, preserving rows. It refuses a conflicting retained-bootstrap name or non-SCRAM bootstrap credential, rather than guessing how to change it. Other databases and their objects remain present. Review any applications sharing this cluster before the cluster-wide role change.

Restart the preview with the updated Compose configuration and verify readiness and account access. Do not erase an existing volume to make readiness green. Production migration credentials belong in the deployment/migration control plane, outside the API process. The [official image documentation](https://github.com/docker-library/docs/blob/master/postgres/README.md#environment-variables) describes the initialization-only variables and superuser bootstrap behavior.

To create the first operator, use `docker compose ... exec api python manage.py createsuperuser`. Then issue closed-registration invitations from the container. Keep terminal output private because invitation and reset commands print one-use URLs.

## Manage accounts

Run commands with the same database environment as the account store. For the local SQLite workspace, enter the environment used by `scripts/dev.py`. For the container preview, use `docker compose ... exec api` before `python manage.py`.

```sh
python manage.py issue_invitation --username analyst2 --issued-by OPERATOR --base-url https://APPROVED_HOST
python manage.py revoke_invitation INVITATION_ID --revoked-by OPERATOR
python manage.py issue_password_reset --username analyst2 --issued-by OPERATOR --base-url https://APPROVED_HOST
python manage.py prune_account_security
python manage.py clearsessions
```

Debug loopback origins may use HTTP. Production origins must use HTTPS. Invitations reserve a username, expire within seven days, and can be revoked by the printed ID. Resets expire within 24 hours, invalidate earlier unused reset tokens, and revoke workspace sessions when consumed. The database stores token digests, not the bearer secrets. No email delivery is implemented or claimed.

Users manage passwords and revoke other workspace sessions at `/app/account`. Passwords require at least 12 characters and Django's other validators. Sessions expire after 12 hours and use secure cookies outside development. Password changes retain the current session and invalidate others; resets invalidate all workspace sessions. The separate research profile has its own users, cookies and database and is outside this revocation scope.

Login failures share a bounded cooldown per normalized account and client address. Different clients do not lock out the whole account. A shared NAT also shares that account's bucket; distributed credential-stuffing defenses and MFA/SSO remain further release work. DRF ignores arbitrary `X-Forwarded-For`. Only enable `CADRISYN_TRUST_CLIENT_IP` or `CADRISYN_TRUST_REQUEST_ID` behind an ingress that overwrites the corresponding headers, with the API inaccessible directly. The supplied gateway does this.

Schedule `prune_account_security` and `clearsessions` externally. No scheduler or background training starts automatically. Operator deactivation uses Django's account administration/management interfaces and invalidates authentication on the next request; do not delete user data to disable access.

## Transfer workspace data

Back up first. Migrate the source workspace schema locally and the destination PostgreSQL schema separately. Set `DATABASE_URL` to the explicit destination in the command's environment; do not place credentials in command-line arguments.

```sh
python scripts/migrate_workspace.py --source-sqlite /absolute/path/to/.local/cadrisyn.sqlite3
```

Use the migration credential for the destination. The tool snapshots the source read-only, refuses the original research database, and requires a migrated destination with no users, groups, workspace/account records, admin log entries or sessions. It loads data in a transaction and compares every copied fixture field before committing. Users, password hashes, groups, watchlists, account state, terminal token history and demo snapshots transfer. Restricted non-demo observations and unused invitation/reset tokens remain at the source and are counted in the result. Issue new links in the destination. The source is never deleted. Session cookies do not transfer; sign in again after cutover.

The CLI is for an isolated destination, not an online bidirectional synchronization system. Complete a cutover rehearsal before selecting a production migration window. Retain the source and backups for rollback.

## Back up and restore

Use [the recovery CLI](../../scripts/ops/README.md). PostgreSQL backups use custom-format `pg_dump`, a verified archive listing, and a checksummed manifest. Restore requires a different empty database and runs in one transaction without `--clean`, `--create` or owner/ACL replacement. Create the destination explicitly using a database operator, restore with the migration credential, and provision the runtime DML/sequence grants in the restored database before application verification. The runtime credential intentionally cannot restore schema objects. Clients must support the server/archive version.

SQLite backups use a read-only source and SQLite's backup API. Restore validates a temporary sibling file, syncs it, and publishes it atomically without overwriting a destination. A crash may leave a `.partial` sibling; it cannot expose a partially copied final target. Verify ownership and the intended target before removing any abandoned temporary file.

Files are not encrypted by this tool. POSIX permissions are restricted; on Windows, `chmod` does not establish an owner-only ACL. Use a directory with an independently verified operator/service-account ACL and encrypted backup storage. Do not commit dumps or secrets. Set retention and off-host backup policy before external use. No RPO or RTO is claimed.

A whole-database recovery also restores the backup's password, session and token state. An older backup can therefore predate later revocations. Before reopening a recovered service, invalidate its sessions and unused invitation/reset credentials, reissue necessary links, and verify current account access. This operator cutover procedure and production retention policy remain to be rehearsed; the local restore proof verifies database fidelity and a fresh sign-in, not recovery of post-backup security decisions.

## Observe and recover services

`/health/` is process liveness. `/health/ready/` checks database access, schema migration state, application role privilege and cache read/write. It returns 503 for a failed dependency; process liveness remains separate. Cache/provider failures do not substitute demo observations.

Application JSON logs omit request bodies, raw exception messages, query strings, credential headers and token URLs. API error bodies and response headers carry the application request ID. The trusted gateway ID is preserved on API requests. Gateway and Gunicorn access formats omit URLs and headers. Central collection, alert routing and retention still require an operational owner.

If readiness fails, inspect `docker compose ... ps`, safe logs, migration status and the dependency check. Restore dependencies before restarting the application. Retain database volumes; `stop` preserves them. For a failed migration, retain the source database and restore a verified backup into a separate target before switching configuration. Do not run destructive `down --volumes` as a repair step.

Production configuration fails closed without a long secret, explicit PostgreSQL URL and shared Redis URL. PostgreSQL connections default to requiring TLS outside development. Supply exact HTTPS hosts/origins, trusted TLS ingress, externally managed secrets and backup storage before deployment. HSTS preload stays disabled pending the domain decision. Image scanning, hosted CI and production-host recovery remain separate acceptance gates.

## Repeat local verification

```powershell
.venv/Scripts/python.exe scripts/check_backend.py
backend/venv/Scripts/python.exe scripts/check_research.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_recovery.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_workspace_migration.py
.venv/Scripts/python.exe scripts/prepare_browser_fixture.py
.venv/Scripts/python.exe scripts/dev.py --api-only
```

In a second shell, run `npm run build`, `npm run typecheck`, `npm run lint`, `npm test`, then `npm run test:e2e` in `web/` with `PLAYWRIGHT_PRODUCTION=1`. Set `PLAYWRIGHT_BROWSERS_PATH` to an existing installation or run `npx playwright install chromium` first. Preparing fixtures creates new disposable accounts and one-use ignored files; it does not change the existing analyst's password.

The build and development commands explicitly select Next's bundled Webpack after two observed Turbopack CSS-worker startup failures on this Windows host. This option is documented in the [Next CLI reference](https://nextjs.org/docs/app/api-reference/cli/next). Docker builds mount the dependency stage read-only during compilation and ship the standalone output, local fonts and license notices.

The workflow defines separate SQLite/browser, PostgreSQL/Redis and container jobs. CI database credentials are ephemeral test fixtures. No hosted green run is implied by adding the jobs. Preserve the existing research environment; the core workspace environment intentionally does not install PyTorch.

To test a retained-volume upgrade independently, run `python scripts/verify_role_upgrade.py --name cadrisyn-upgrade-check --env-file .local/preview.env`. It refuses existing container/volume names, creates a fresh legacy-configured PostgreSQL volume without host ports, tests role transition, preserved rows, default grants, DDL denial, idempotence and restart, and retains the container/volume. Stop the named test container after inspection. This verifier never targets the working preview database.

For packaged-stack browser verification, prepare disposable account fixtures with the helper bound into the API image, the existing preview environment and `.local` fixture output directory, and `CADRISYN_PREVIEW_PROFILE=true`. Run it with `--configured-preview`; it rejects non-preview destinations. Then set `PLAYWRIGHT_EXTERNAL_SERVER=1` and `PLAYWRIGHT_BASE_URL=http://127.0.0.1:8080` before `npm run test:e2e` in `web/`. Use fresh invitation/reset fixture files for each run. Two tests stub account responses to check UI states; three journeys use the actual API and database.
