"""Explicit loopback research profile for the preserved quantitative environment."""

from . import settings as base


for name in dir(base):
    if name.isupper():
        globals()[name] = getattr(base, name)

ROOT_URLCONF = "quantvision.legacy_urls"
INSTALLED_APPS = [app for app in base.INSTALLED_APPS if app not in {"workspace", "accounts", "drf_spectacular"}]
MIDDLEWARE = [item for item in base.MIDDLEWARE if item != "accounts.middleware.SessionEpochMiddleware"]
CADRISYN_LEGACY_ENABLED = True
SESSION_COOKIE_NAME = "cadrisyn_research_session"
CSRF_COOKIE_NAME = "cadrisyn_research_csrf"
REST_FRAMEWORK = {
    **base.REST_FRAMEWORK,
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}
CSRF_FAILURE_VIEW = "django.views.csrf.csrf_failure"
