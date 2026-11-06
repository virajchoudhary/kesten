# Database recovery utility

`recovery.py` creates explicit logical backups and restores only to an isolated,
empty target. It uses only the Python standard library. PostgreSQL operations
also require matching `pg_dump`, `pg_restore`, and `psql` client programs on
`PATH`; use the PostgreSQL 17 client with the repository's PostgreSQL 17
Compose service. The current API image must include this directory and
`postgresql-client` before the container examples below can run.

The utility has no implicit database or file paths. Supply a database URL
through a named environment variable, not as a command-line value. URL
usernames, passwords, and database names must use valid percent encoding.
`sslmode`, `connect_timeout`, and `application_name` are preserved. Passwords
are not passed in process arguments or printed; PostgreSQL clients receive
them through a temporary `PGPASSFILE`, which is removed when the command exits.
Client errors omit PostgreSQL stderr, and invalid CLI arguments do not echo
their values.

## PostgreSQL backup

Create the output directory first. The dump and adjacent
`<dump-name>.manifest.json` are new files and are never overwritten.

On a host with the PostgreSQL client tools:

```powershell
$env:CADRISYN_SOURCE_DATABASE_URL = $env:DATABASE_URL
& .\.venv\Scripts\python.exe scripts\ops\recovery.py backup-postgres `
  --database-url-env CADRISYN_SOURCE_DATABASE_URL `
  --output .local\backups\cadrisyn.dump
```

```sh
export CADRISYN_SOURCE_DATABASE_URL="$DATABASE_URL"
python scripts/ops/recovery.py backup-postgres \
  --database-url-env CADRISYN_SOURCE_DATABASE_URL \
  --output .local/backups/cadrisyn.dump
```

The source URL must be present in the environment before running the command.
Do not replace `--database-url-env` with a URL literal. In the local Compose
profile, PostgreSQL is private to the Compose network, so run the command from
the API container after its image includes this utility and the PostgreSQL
client tools:

```sh
docker compose exec -T api python /app/scripts/ops/recovery.py backup-postgres \
  --database-url-env DATABASE_URL \
  --output /tmp/cadrisyn.dump
docker compose cp api:/tmp/cadrisyn.dump .local/backups/cadrisyn.dump
docker compose cp api:/tmp/cadrisyn.dump.manifest.json \
  .local/backups/cadrisyn.dump.manifest.json
```

Copy the dump and manifest together. The manifest contains a SHA-256 digest,
size, PostgreSQL schema/object counts, whether Django migrations are present,
server version, a schema-list digest, and a non-secret source fingerprint.
It does not contain the connection URL or password. A checksum detects
accidental corruption; it does not authenticate who created a manifest.

## PostgreSQL restore

Have an administrator create a separate, isolated, empty target database
first. Do not use the source database URL. This command does not create,
clean, drop, or rename databases. It rejects a matching source endpoint,
rejects a matching cluster/database identity when available, and refuses a
target with user schemas or objects. Restore runs with
`pg_restore --single-transaction --exit-on-error`, without clean or create
flags, so a restore error rolls back its writes.

The restore validates the manifest, artifact size and SHA-256, then confirms
the custom-format dump can be listed and that its schema listing matches the
manifest before connecting to the destination.

```powershell
$env:CADRISYN_RESTORE_TARGET_DATABASE_URL = '<percent-encoded URL to the separate empty database>'
& .\.venv\Scripts\python.exe scripts\ops\recovery.py restore-postgres `
  --manifest .local\backups\cadrisyn.dump.manifest.json `
  --target-database-url-env CADRISYN_RESTORE_TARGET_DATABASE_URL
```

```sh
export CADRISYN_RESTORE_TARGET_DATABASE_URL='<percent-encoded URL to the separate empty database>'
python scripts/ops/recovery.py restore-postgres \
  --manifest .local/backups/cadrisyn.dump.manifest.json \
  --target-database-url-env CADRISYN_RESTORE_TARGET_DATABASE_URL
```

For a container restore, copy the dump and manifest to the API container first,
then set `CADRISYN_RESTORE_TARGET_DATABASE_URL` in that container's execution
environment and run the same command. The recovery tool restores database
objects as the target connection user and omits source ownership and ACLs.
PostgreSQL cluster roles, server configuration, and external extension
binaries are outside a `pg_dump` archive and need their own approved recovery
procedure.

## SQLite development backup and restore

SQLite backup opens the explicit source with `mode=ro` and `PRAGMA query_only`,
then copies it through Python's SQLite backup API. It never runs migrations on
the source. The backup file and manifest are created exclusively with
owner-only permissions where supported.

```powershell
& .\.venv\Scripts\python.exe scripts\ops\recovery.py backup-sqlite `
  --source-path .local\cadrisyn.sqlite3 `
  --output .local\backups\cadrisyn-dev.sqlite3
```

```sh
python scripts/ops/recovery.py backup-sqlite \
  --source-path .local/cadrisyn.sqlite3 \
  --output .local/backups/cadrisyn-dev.sqlite3
```

SQLite restore requires a new target path. It validates the manifest and
checksum, checks database integrity and schema metadata, and copies to the new
file with the SQLite backup API. It refuses the preserved
`backend/db.sqlite3`, an existing target, and the backup artifact/manifest
itself.

```powershell
& .\.venv\Scripts\python.exe scripts\ops\recovery.py restore-sqlite `
  --manifest .local\backups\cadrisyn-dev.sqlite3.manifest.json `
  --target-path .local\cadrisyn-restore-test.sqlite3
```

## Recovery policy

A logical custom-format dump restored into a separately named empty database
keeps the original database available for comparison and rollback. A
destructive in-place restore can remove or replace existing objects before an
operator has proven the backup, migrations, ownership, or application behavior.
The separate-target model avoids that failure mode; it is the only restore
mode implemented here.

The tool does not encrypt files or select retention. Store backups and
manifests in an access-controlled location, encrypt them before off-host
transfer, and verify a restore and an application sign-in journey before
making recovery-time claims. Do not run migrations against the original
`backend/db.sqlite3`.
