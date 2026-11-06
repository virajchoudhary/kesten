"""Django settings for the Cadrisyn local workspace and API."""

import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean value.")


def _env_list(name, default=()):
    value = os.environ.get(name)
    if value is None:
        return list(default)

    items = [item.strip() for item in value.split(",") if item.strip()]
    if any("*" in item or item.startswith(".") for item in items):
        raise ImproperlyConfigured(f"{name} must contain explicit values, not a wildcard.")
    return items


def _database_from_url(database_url):
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL must use the PostgreSQL scheme.")

    database_name = unquote(parsed.path.lstrip("/"))
    if not database_name or not parsed.hostname:
        raise ImproperlyConfigured("DATABASE_URL must include a database name and host.")

    query = parse_qs(parsed.query)
    options = {}
    for name in ("sslmode", "connect_timeout", "application_name"):
        if name in query:
            options[name] = query[name][-1]

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": database_name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": str(parsed.port or ""),
        "CONN_MAX_AGE": 60,
        "OPTIONS": options,
    }


DEBUG = _env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured.")

_local_hosts = ("localhost", "127.0.0.1", "[::1]") if DEBUG else ()
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", _local_hosts)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list at least one exact host.")

CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = _env_list("DJANGO_CORS_ALLOWED_ORIGINS")
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = False

CADRISYN_LEGACY_ENABLED = _env_bool("CADRISYN_LEGACY_ENABLED", False)
CADRISYN_LEGACY_SCHEDULER_ENABLED = _env_bool(
    "CADRISYN_LEGACY_SCHEDULER_ENABLED", False
)
CADRISYN_MARKET_DATA_ENABLED = _env_bool("CADRISYN_MARKET_DATA_ENABLED", False)
try:
    CADRISYN_EOD_GRACE_HOURS = int(os.environ.get("CADRISYN_EOD_GRACE_HOURS", "4"))
except ValueError as error:
    raise ImproperlyConfigured("CADRISYN_EOD_GRACE_HOURS must be an integer from 0 to 48.") from error
if not 0 <= CADRISYN_EOD_GRACE_HOURS <= 48:
    raise ImproperlyConfigured("CADRISYN_EOD_GRACE_HOURS must be an integer from 0 to 48.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "api",
    "workspace",
    "django_celery_beat",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "quantvision.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "quantvision.wsgi.application"
ASGI_APPLICATION = "quantvision.asgi.application"

database_url = os.environ.get("DATABASE_URL", "").strip()
if database_url:
    DATABASES = {"default": _database_from_url(database_url)}
else:
    configured_db_path = Path(
        os.environ.get(
            "CADRISYN_DB_PATH",
            str(REPO_ROOT / ".local" / "cadrisyn.sqlite3"),
        )
    ).expanduser()
    if not configured_db_path.is_absolute():
        configured_db_path = REPO_ROOT / configured_db_path
    configured_db_path = configured_db_path.resolve()

    legacy_db_path = (BASE_DIR / "db.sqlite3").resolve()
    if configured_db_path == legacy_db_path:
        raise ImproperlyConfigured(
            "CADRISYN_DB_PATH cannot point to the preserved legacy database."
        )

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": configured_db_path,
            "OPTIONS": {"timeout": 30},
        }
    }

cache_url = os.environ.get("DJANGO_CACHE_URL", "").strip()
if cache_url:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": cache_url,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "cadrisyn-local",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_FAILURE_VIEW = "workspace.exceptions.csrf_failure"

SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = 0 if DEBUG else 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = _env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
USE_X_FORWARDED_HOST = False
if _env_bool("DJANGO_TRUST_X_FORWARDED_PROTO", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DATA_UPLOAD_MAX_MEMORY_SIZE = 2_621_440
FILE_UPLOAD_MAX_MEMORY_SIZE = 2_621_440
DATA_UPLOAD_MAX_NUMBER_FIELDS = 200

_throttle_classes = [
    "rest_framework.throttling.ScopedRateThrottle",
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": _throttle_classes,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/hour",
        "user": "300/hour",
        "login": "30/minute",
        "market": "60/minute",
        "legacy": "5/hour",
        "legacy_read": "60/minute",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "workspace.exceptions.exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Cadrisyn API",
    "DESCRIPTION": "Private daily-market research workspace API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL",
    os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
)
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND",
    "redis://127.0.0.1:6379/1",
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

CELERY_BEAT_SCHEDULE = {}
if CADRISYN_LEGACY_ENABLED and CADRISYN_LEGACY_SCHEDULER_ENABLED:
    from celery.schedules import crontab

    CELERY_BEAT_SCHEDULE["nightly-hpo"] = {
        "task": "api.tasks.run_hpo_for_watchlist",
        "schedule": crontab(hour=1, minute=0),
    }
