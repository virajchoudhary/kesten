import logging
import uuid

from django.core.cache import cache
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse

logger = logging.getLogger("cadrisyn.readiness")


def readiness(request):
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            if connection.vendor == "postgresql":
                cursor.execute(
                    """
                    SELECT r.rolsuper, r.rolcreatedb, r.rolcreaterole, r.rolreplication, r.rolbypassrls,
                           pg_get_userbyid(d.datdba) = current_user,
                           has_schema_privilege(current_user, 'public', 'CREATE'),
                           EXISTS (
                               SELECT 1
                               FROM pg_class c
                               JOIN pg_namespace n ON n.oid = c.relnamespace
                               WHERE n.nspname = 'public'
                                 AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
                                 AND pg_get_userbyid(c.relowner) = current_user
                           )
                    FROM pg_roles r
                    JOIN pg_database d ON d.datname = current_database()
                    WHERE r.rolname = current_user
                    """
                )
                privileges = cursor.fetchone()
                checks["database_role"] = privileges is not None and not any(privileges)
        executor = MigrationExecutor(connection)
        checks["database"] = not bool(executor.migration_plan(executor.loader.graph.leaf_nodes()))
    except Exception:
        checks["database"] = False
    probe = "cadrisyn:ready:" + uuid.uuid4().hex
    try:
        cache.set(probe, "ok", timeout=10)
        checks["cache"] = cache.get(probe) == "ok"
        cache.delete(probe)
    except Exception:
        checks["cache"] = False
    ready = all(checks.values())
    if not ready:
        for name, ok in checks.items():
            if not ok:
                logger.warning("dependency_unavailable", extra={"event": "dependency_unavailable", "component": name})
    response = JsonResponse({"status": "ready" if ready else "unavailable", "checks": checks}, status=200 if ready else 503)
    response["Cache-Control"] = "no-store"
    return response
