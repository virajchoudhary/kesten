-- Run only after cadrisyn_migrator has been created with its private credential.
-- Back up the database, then execute as a PostgreSQL bootstrap administrator
-- connected to the cadrisyn database. See prepare-preview-role-upgrade.sql
-- when the old runtime role is also the cluster's bootstrap administrator.
BEGIN;

DO $preflight$
BEGIN
    IF current_database() <> 'cadrisyn' THEN
        RAISE EXCEPTION 'Connect to the cadrisyn database before applying this upgrade';
    END IF;

    IF current_setting('is_superuser') <> 'on' THEN
        RAISE EXCEPTION 'Run this ownership upgrade as a PostgreSQL bootstrap administrator';
    END IF;

    IF current_user = 'cadrisyn' THEN
        RAISE EXCEPTION 'Reconnect as a separate bootstrap administrator before demoting cadrisyn';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'cadrisyn_migrator'
          AND rolcanlogin
          AND NOT rolsuper
          AND NOT rolcreatedb
          AND NOT rolcreaterole
          AND NOT rolreplication
          AND NOT rolbypassrls
    ) THEN
        RAISE EXCEPTION 'Create the constrained cadrisyn_migrator role before applying this upgrade';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'cadrisyn'
          AND rolcanlogin
    ) THEN
        RAISE EXCEPTION 'The cadrisyn runtime role must exist and be login-enabled';
    END IF;
END
$preflight$;

DO $runtime_role$
DECLARE
    password_verifier text;
BEGIN
    -- PostgreSQL's original bootstrap role (OID 10) must remain a superuser.
    -- Retain that identity without login and give the application a new role.
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cadrisyn' AND oid = 10) THEN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cadrisyn_legacy_bootstrap') THEN
            RAISE EXCEPTION 'Legacy bootstrap role name already exists; resolve explicitly';
        END IF;
        SELECT rolpassword INTO password_verifier FROM pg_authid WHERE rolname = 'cadrisyn';
        IF password_verifier IS NULL OR password_verifier NOT LIKE 'SCRAM-SHA-256$%' THEN
            RAISE EXCEPTION 'Legacy runtime credential must use SCRAM before upgrading';
        END IF;
        ALTER ROLE cadrisyn RENAME TO cadrisyn_legacy_bootstrap;
        ALTER ROLE cadrisyn_legacy_bootstrap NOLOGIN PASSWORD NULL;
        EXECUTE format(
            'CREATE ROLE cadrisyn LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L',
            password_verifier
        );
    ELSE
        ALTER ROLE cadrisyn NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
    END IF;
END
$runtime_role$;
ALTER DATABASE cadrisyn OWNER TO cadrisyn_migrator;
ALTER SCHEMA public OWNER TO cadrisyn_migrator;

REVOKE ALL ON DATABASE cadrisyn FROM PUBLIC, cadrisyn;
GRANT CONNECT ON DATABASE cadrisyn TO cadrisyn_migrator, cadrisyn;
REVOKE ALL ON SCHEMA public FROM PUBLIC, cadrisyn;
GRANT USAGE ON SCHEMA public TO cadrisyn;

DO $ownership$
DECLARE
    relation record;
BEGIN
    FOR relation IN
        SELECT c.relname, c.relkind
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
        ORDER BY CASE WHEN c.relkind = 'S' THEN 1 ELSE 0 END, c.relname
    LOOP
        CASE relation.relkind
            WHEN 'S' THEN
                EXECUTE format('ALTER SEQUENCE public.%I OWNER TO cadrisyn_migrator', relation.relname);
            WHEN 'v' THEN
                EXECUTE format('ALTER VIEW public.%I OWNER TO cadrisyn_migrator', relation.relname);
            WHEN 'm' THEN
                EXECUTE format('ALTER MATERIALIZED VIEW public.%I OWNER TO cadrisyn_migrator', relation.relname);
            WHEN 'f' THEN
                EXECUTE format('ALTER FOREIGN TABLE public.%I OWNER TO cadrisyn_migrator', relation.relname);
            ELSE
                EXECUTE format('ALTER TABLE public.%I OWNER TO cadrisyn_migrator', relation.relname);
        END CASE;
    END LOOP;
END
$ownership$;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cadrisyn;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cadrisyn;
ALTER DEFAULT PRIVILEGES FOR ROLE cadrisyn_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cadrisyn;
ALTER DEFAULT PRIVILEGES FOR ROLE cadrisyn_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO cadrisyn;

COMMIT;
