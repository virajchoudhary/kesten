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


def _env_secret(name):
    value = os.environ.get(name, "").strip()
    filename = os.environ.get(name + "_FILE", "").strip()
    if value and filename:
        raise ImproperlyConfigured(f"Configure either {name} or {name}_FILE, not both.")
    if filename:
        try:
            raw = Path(filename).read_bytes()
            if not 1 <= len(raw) <= 65536:
                raise ValueError
            value = raw.decode("utf-8").rstrip("\r\n")
        except (OSError, UnicodeDecodeError, ValueError) as error:
            raise ImproperlyConfigured(f"{name}_FILE must contain a readable non-empty UTF-8 secret.") from error
    return value


def _database_from_url(database_url):
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL must use the PostgreSQL scheme.")

    database_name = unquote(parsed.path.lstrip("/"))
    if not database_name or not parsed.hostname:
        raise ImproperlyConfigured("DATABASE_URL must include a database name and host.")

    query = parse_qs(parsed.query)
    options = {"connect_timeout": 5}
    for name in ("sslmode", "sslrootcert", "connect_timeout", "application_name"):
        if name in query:
            options[name] = query[name][-1]
    if not DEBUG:
        if options.get("sslmode") != "verify-full" or not Path(options.get("sslrootcert", "")).is_file() or not parsed.password:
            raise ImproperlyConfigured("Production PostgreSQL requires password authentication and verify-full TLS with an explicit CA file.")

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": database_name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": str(parsed.port or ""),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": options,
    }


DEBUG = _env_bool("DJANGO_DEBUG", False)
SECRET_KEY = _env_secret("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured.")
if not DEBUG and len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must contain at least 50 characters outside development.")

CADRISYN_RELEASE_PROFILE = os.environ.get("CADRISYN_RELEASE_PROFILE", "development" if DEBUG else "demo")
if CADRISYN_RELEASE_PROFILE not in {"development", "demo", "historical_research"}:
    raise ImproperlyConfigured("CADRISYN_RELEASE_PROFILE must name a supported release profile.")
if not DEBUG and CADRISYN_RELEASE_PROFILE == "development":
    raise ImproperlyConfigured("The development release profile requires DJANGO_DEBUG=true.")

_local_hosts = ("localhost", "127.0.0.1", "[::1]") if DEBUG else ()
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", _local_hosts)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list at least one exact host.")

CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = _env_list("DJANGO_CORS_ALLOWED_ORIGINS")
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = False
if not DEBUG:
    for origin in [*CSRF_TRUSTED_ORIGINS, *CORS_ALLOWED_ORIGINS]:
        parsed_origin = urlparse(origin)
        if parsed_origin.scheme != "https" or parsed_origin.username or parsed_origin.password or parsed_origin.path or parsed_origin.query or parsed_origin.fragment or parsed_origin.hostname not in ALLOWED_HOSTS:
            raise ImproperlyConfigured("Production origins must be exact HTTPS origins on an allowed host.")

CADRISYN_LEGACY_ENABLED = _env_bool("CADRISYN_LEGACY_ENABLED", False)
CADRISYN_ADMIN_ENABLED = _env_bool("CADRISYN_ADMIN_ENABLED", DEBUG)
CADRISYN_TRUST_REQUEST_ID = _env_bool("CADRISYN_TRUST_REQUEST_ID", False)
CADRISYN_TRUST_CLIENT_IP = _env_bool("CADRISYN_TRUST_CLIENT_IP", False)
CADRISYN_LEGACY_SCHEDULER_ENABLED = _env_bool(
    "CADRISYN_LEGACY_SCHEDULER_ENABLED", False
)
CADRISYN_MARKET_DATA_ENABLED = _env_bool("CADRISYN_MARKET_DATA_ENABLED", False)
CADRISYN_YAHOO_PERSONAL_USE_ACKNOWLEDGED = _env_bool("CADRISYN_YAHOO_PERSONAL_USE_ACKNOWLEDGED", False)
if not DEBUG and (CADRISYN_LEGACY_ENABLED or CADRISYN_MARKET_DATA_ENABLED or CADRISYN_ADMIN_ENABLED or CADRISYN_LEGACY_SCHEDULER_ENABLED):
    raise ImproperlyConfigured("Unqualified providers, legacy scheduling and admin routes are disabled in production profiles.")
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
    "accounts",
    "research",
    "django_celery_beat",
    "corsheaders",
]

MIDDLEWARE = [
    "operations.logging.RequestLoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "operations.client.ClientAddressMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.SessionEpochMiddleware",
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

database_url = _env_secret("DATABASE_URL")
if not DEBUG and not database_url:
    raise ImproperlyConfigured("Production requires an explicit PostgreSQL DATABASE_URL.")
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
            "OPTIONS": {
                "timeout": 30,
                **({"transaction_mode": "IMMEDIATE"} if not CADRISYN_LEGACY_ENABLED else {}),
            },
        }
    }

cache_url = _env_secret("DJANGO_CACHE_URL")
if not DEBUG and not cache_url:
    raise ImproperlyConfigured("Production requires an explicit shared Redis DJANGO_CACHE_URL.")
if cache_url:
    if urlparse(cache_url).scheme not in {"redis", "rediss"} or not urlparse(cache_url).hostname:
        raise ImproperlyConfigured("DJANGO_CACHE_URL must be a Redis URL with a host.")
    if not DEBUG:
        parsed_cache = urlparse(cache_url)
        cache_options = parse_qs(parsed_cache.query)
        if parsed_cache.scheme != "rediss" or not parsed_cache.password or not Path(cache_options.get("ssl_ca_certs", [""])[-1]).is_file() or cache_options.get("ssl_cert_reqs", ["required"]) != ["required"] or cache_options.get("ssl_check_hostname", ["true"]) != ["true"]:
            raise ImproperlyConfigured("Production Redis requires password authentication and hostname-verified TLS with an explicit CA file.")
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": cache_url,
            "OPTIONS": {"socket_connect_timeout": 3, "socket_timeout": 3, **({"ssl_check_hostname": True} if not DEBUG else {})},
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
        "OPTIONS": {"min_length": 12},
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
STATIC_ROOT = Path(os.environ.get("DJANGO_STATIC_ROOT", str(REPO_ROOT / ".local" / "static")))
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = "cadrisyn_session"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 60 * 60 * 12
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_NAME = "cadrisyn_csrf"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_FAILURE_VIEW = "workspace.exceptions.csrf_failure"

SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
if not DEBUG and not SECURE_SSL_REDIRECT:
    raise ImproperlyConfigured("Production profiles require HTTPS redirection.")
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
    "NUM_PROXIES": 0,
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
        "research": "6/minute",
        "legacy": "5/hour",
        "legacy_read": "60/minute",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "workspace.exceptions.exception_handler",
}

SPECTACULAR_SETTINGS = {
    "ENUM_NAME_OVERRIDES": {"ResearchModelEnum": ["last_close", "historical_log_mean"]},
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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "operations.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.server": {"handlers": [], "propagate": False},
    },
}

CELERY_BEAT_SCHEDULE = {}
if CADRISYN_LEGACY_ENABLED and CADRISYN_LEGACY_SCHEDULER_ENABLED:
    from celery.schedules import crontab

    CELERY_BEAT_SCHEDULE["nightly-hpo"] = {
        "task": "api.tasks.run_hpo_for_watchlist",
        "schedule": crontab(hour=1, minute=0),
    }
