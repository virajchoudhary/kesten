-- Run as the existing bootstrap superuser after backing up the retained volume.
-- Supply secrets in the psql process environment, never in its arguments.
-- Existing credentials are preserved. New roles use the supplied credentials.
\set ON_ERROR_STOP on
\getenv admin_password POSTGRES_ADMIN_PASSWORD
\getenv migration_password POSTGRES_MIGRATION_PASSWORD
BEGIN;
DO $preflight$
BEGIN
    IF current_database() <> 'cadrisyn' OR current_setting('is_superuser') <> 'on' THEN
        RAISE EXCEPTION 'Connect to cadrisyn as the existing bootstrap superuser';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'postgres' AND NOT (rolsuper AND rolcanlogin)) THEN
        RAISE EXCEPTION 'Existing postgres role is not a login-enabled administrator; resolve explicitly';
    END IF;
END
$preflight$;
SELECT format('CREATE ROLE postgres LOGIN SUPERUSER PASSWORD %L', :'admin_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'postgres')
\gexec
SELECT format('CREATE ROLE cadrisyn_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L', :'migration_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cadrisyn_migrator')
\gexec
COMMIT;
