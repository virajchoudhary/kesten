#!/bin/sh
set -eu
: "${CADRISYN_DB_PASSWORD:?CADRISYN_DB_PASSWORD must be set}"
: "${CADRISYN_MIGRATION_PASSWORD:?CADRISYN_MIGRATION_PASSWORD must be set}"

psql --no-psqlrc --quiet --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<'SQL'
\getenv runtime_password CADRISYN_DB_PASSWORD
\getenv migration_password CADRISYN_MIGRATION_PASSWORD
CREATE ROLE cadrisyn_migrator
    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    PASSWORD :'migration_password';
CREATE ROLE cadrisyn
    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    PASSWORD :'runtime_password';
CREATE DATABASE cadrisyn OWNER cadrisyn_migrator;
REVOKE ALL ON DATABASE cadrisyn FROM PUBLIC, cadrisyn;
GRANT CONNECT ON DATABASE cadrisyn TO cadrisyn_migrator, cadrisyn;
SQL

psql --no-psqlrc --quiet --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname cadrisyn <<'SQL'
REVOKE ALL ON SCHEMA public FROM PUBLIC, cadrisyn;
ALTER SCHEMA public OWNER TO cadrisyn_migrator;
GRANT USAGE ON SCHEMA public TO cadrisyn;
ALTER DEFAULT PRIVILEGES FOR ROLE cadrisyn_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cadrisyn;
ALTER DEFAULT PRIVILEGES FOR ROLE cadrisyn_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO cadrisyn;
SQL
