import os
import unittest
import uuid

import psycopg
from psycopg import sql

from scripts.qualify_research_postgres import read_runtime_privileges, verify_runtime_privileges


@unittest.skipUnless(
    os.environ.get("KERQUANT_ISOLATED_QUALIFICATION") == "phase51"
    and os.environ.get("KERQUANT_QUALIFICATION_ADMIN_URL"),
    "Requires the explicit isolated PostgreSQL qualification test database.",
)
class PostgresPrivilegeSqlTests(unittest.TestCase):
    def setUp(self):
        self.db = psycopg.connect(os.environ["KERQUANT_QUALIFICATION_ADMIN_URL"])
        self.addCleanup(self.db.close)
        self.addCleanup(self.db.rollback)
        self.assertEqual(self.db.info.dbname, "test_cadrisyn")
        self.assertEqual(self.db.info.server_version // 10000, 17)
        self.cursor = self.db.cursor()
        token = uuid.uuid4().hex[:12]
        self.candidate = "kq_candidate_" + token
        self.owner = "kq_owner_" + token
        self.schema = "kq_probe_" + token
        self.cursor.execute("REVOKE CREATE, TEMPORARY ON DATABASE test_cadrisyn FROM PUBLIC")
        for name in (self.candidate, self.owner):
            self.cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOINHERIT").format(sql.Identifier(name)))
        self.cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))

    def candidate_privileges(self):
        self.cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(self.candidate)))
        try:
            role, privileges = read_runtime_privileges(self.cursor)
            self.assertEqual(role, self.candidate)
            return privileges
        finally:
            self.cursor.execute("RESET ROLE")

    def test_fresh_unprivileged_role_has_no_capabilities(self):
        self.assertFalse(any(self.candidate_privileges().values()))

    def test_noinherit_set_membership_is_detected(self):
        self.cursor.execute(sql.SQL("GRANT {} TO {} WITH INHERIT FALSE, SET TRUE").format(
            sql.Identifier(self.owner), sql.Identifier(self.candidate),
        ))
        self.cursor.execute("SELECT pg_has_role(%s, %s, 'USAGE'), pg_has_role(%s, %s, 'SET')", (
            self.candidate, self.owner, self.candidate, self.owner,
        ))
        self.assertEqual(self.cursor.fetchone(), (False, True))
        privileges = self.candidate_privileges()
        self.assertTrue(privileges["role_membership"])
        with self.assertRaises(ValueError):
            verify_runtime_privileges("cadrisyn", privileges)

    def assert_owned_object_detected(self, statement):
        self.cursor.execute(sql.SQL("GRANT USAGE, CREATE ON SCHEMA {} TO {}").format(
            sql.Identifier(self.schema), sql.Identifier(self.candidate),
        ))
        self.cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(self.candidate)))
        self.cursor.execute(statement.format(sql.Identifier(self.schema)))
        self.cursor.execute("RESET ROLE")
        self.cursor.execute(sql.SQL("REVOKE CREATE ON SCHEMA {} FROM {}").format(
            sql.Identifier(self.schema), sql.Identifier(self.candidate),
        ))
        self.cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=%s))",
            (self.candidate,),
        )
        self.assertFalse(self.cursor.fetchone()[0])
        privileges = self.candidate_privileges()
        self.assertFalse(privileges["writable_schema"])
        self.assertTrue(privileges["owns_objects"])
        with self.assertRaises(ValueError):
            verify_runtime_privileges("cadrisyn", privileges)

    def test_routine_ownership_without_relations_is_detected(self):
        self.assert_owned_object_detected(sql.SQL("CREATE FUNCTION {}.probe() RETURNS integer LANGUAGE sql AS 'SELECT 1'"))

    def test_type_ownership_without_relations_is_detected(self):
        self.assert_owned_object_detected(sql.SQL("CREATE TYPE {}.probe AS ENUM ('synthetic')"))
