import logging
import uuid

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse

logger = logging.getLogger("cadrisyn.readiness")


def release_configuration(request):
    profile = settings.CADRISYN_RELEASE_PROFILE
    response = JsonResponse({
        'profile': profile,
        'debug': settings.DEBUG,
        'private_research_enabled': profile != 'demo',
        'market_data_enabled': settings.CADRISYN_MARKET_DATA_ENABLED,
    })
    response['Cache-Control'] = 'no-store'
    return response


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
                           has_database_privilege(current_user, current_database(), 'CREATE'),
                           has_database_privilege(current_user, current_database(), 'TEMPORARY'),
                           EXISTS (
                               SELECT 1
                               FROM pg_namespace
                               WHERE nspname !~ '^pg_'
                                 AND nspname <> 'information_schema'
                                 AND has_schema_privilege(current_user, oid, 'CREATE')
                           ),
                           EXISTS (
                               SELECT 1
                               FROM pg_shdepend
                               WHERE refclassid='pg_authid'::regclass
                                 AND refobjid=r.oid AND deptype='o'
                                 AND dbid IN (0, (SELECT oid FROM pg_database WHERE datname=current_database()))
                           ),
                           EXISTS (
                               SELECT 1
                               FROM pg_auth_members
                               WHERE member=r.oid
                           )
                    FROM pg_roles r
                    WHERE rolname = current_user
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
