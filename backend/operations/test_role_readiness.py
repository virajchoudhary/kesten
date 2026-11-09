import json
import unittest
from unittest.mock import MagicMock, patch

from operations.health import readiness

ROLE_FLAGS = (
    "superuser",
    "create_database",
    "create_role",
    "replication",
    "bypass_rls",
    "create_schema",
    "temporary",
    "writable_schema",
    "owns_objects",
    "role_membership",
)

ROLE_FLAG_SQL = (
    "r.rolsuper",
    "r.rolcreatedb",
    "r.rolcreaterole",
    "r.rolreplication",
    "r.rolbypassrls",
    "has_database_privilege(current_user, current_database(), 'CREATE')",
    "has_database_privilege(current_user, current_database(), 'TEMPORARY')",
    (
        "nspname !~ '^pg_' AND nspname <> 'information_schema' "
        "AND has_schema_privilege(current_user, oid, 'CREATE')"
    ),
    (
        "FROM pg_shdepend WHERE refclassid='pg_authid'::regclass "
        "AND refobjid=r.oid AND deptype='o' AND dbid IN (0, "
        "(SELECT oid FROM pg_database WHERE datname=current_database()))"
    ),
    "FROM pg_auth_members WHERE member=r.oid",
)


class PostgreSQLRoleReadinessTests(unittest.TestCase):
    def readiness_for_flags(self, flags):
        database = MagicMock()
        cursor = database.cursor.return_value.__enter__.return_value
        database.vendor = "postgresql"
        row = [None]

        def execute(statement):
            query = " ".join(statement.split())
            if query == "SELECT 1":
                row[0] = (1,)
            else:
                row[0] = tuple(
                    flag if clause in query else False
                    for flag, clause in zip(flags, ROLE_FLAG_SQL, strict=True)
                )

        cursor.execute.side_effect = execute
        cursor.fetchone.side_effect = lambda: row[0]
        cache_backend = MagicMock()
        cache_backend.get.return_value = "ok"

        with (
            patch("operations.health.connection", new=database),
            patch("operations.health.MigrationExecutor") as migration_executor,
            patch("operations.health.cache", new=cache_backend),
        ):
            migration_executor.return_value.migration_plan.return_value = []
            response = readiness(None)

        query = " ".join(cursor.execute.call_args_list[1].args[0].split())
        return response, query

    def test_unprivileged_role_is_ready_and_checks_verified_catalog_logic(self):
        response, query = self.readiness_for_flags((False,) * len(ROLE_FLAGS))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {
                "status": "ready",
                "checks": {
                    "database_role": True,
                    "database": True,
                    "cache": True,
                },
            },
        )
        self.assertEqual(response["Cache-Control"], "no-store")
        for clause in ROLE_FLAG_SQL[5:]:
            self.assertIn(clause, query)

    def test_each_privileged_role_condition_blocks_readiness_without_leaking_details(self):
        for index, flag in enumerate(ROLE_FLAGS):
            flags = [False] * len(ROLE_FLAGS)
            flags[index] = True
            with self.subTest(flag=flag):
                response, _ = self.readiness_for_flags(flags)

                self.assertEqual(response.status_code, 503)
                self.assertFalse(json.loads(response.content)["checks"]["database_role"])
                self.assertNotIn("cadrisyn", response.content.decode())


if __name__ == "__main__":
    unittest.main()
