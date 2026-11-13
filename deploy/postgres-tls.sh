#!/bin/sh
set -eu
install -d -m 700 -o postgres -g postgres /run/postgresql-tls
install -m 600 -o postgres -g postgres /run/secrets/database_key /run/postgresql-tls/server.key
install -m 644 -o postgres -g postgres /run/secrets/database_cert /run/postgresql-tls/server.crt
CADRISYN_DB_PASSWORD=$(cat /run/secrets/runtime_password)
CADRISYN_MIGRATION_PASSWORD=$(cat /run/secrets/migration_password)
export CADRISYN_DB_PASSWORD CADRISYN_MIGRATION_PASSWORD
exec /usr/local/bin/docker-entrypoint.sh postgres -c ssl=on -c ssl_cert_file=/run/postgresql-tls/server.crt -c ssl_key_file=/run/postgresql-tls/server.key -c hba_file=/etc/postgresql/pg_hba.production.conf
