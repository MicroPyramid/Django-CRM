import os
from datetime import timedelta

from corsheaders.defaults import default_headers
from dotenv import load_dotenv

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-dev-key-please-change-in-production"
)

if not SECRET_KEY or SECRET_KEY.startswith("django-insecure"):
    if os.environ.get("ENV_TYPE", "dev") != "dev":
        raise ValueError(
            "SECRET_KEY must be set to a secure value in non-dev environments"
        )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Security: Restrict allowed hosts - set ALLOWED_HOSTS env var in production
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_ses",
    "drf_spectacular",
    "common",
    "accounts",
    "cases",
    "contacts",
    "leads",
    "opportunity",
    "tasks",
    "invoices",
    "orders",
    "business_hours",
    "macros",
    # "teams",  # Merged into common app
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  # CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "crum.CurrentRequestUserMiddleware",
    "common.middleware.get_company.GetProfileAndOrg",
    "common.middleware.rls_context.RequireOrgContext",  # RLS: Enforce org context + set PostgreSQL session variable
]

ROOT_URLCONF = "crm.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.common.app_name",
                # "django_settings_export.settings_export",
            ],
        },
    },
]

WSGI_APPLICATION = "crm.wsgi.application"

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DBNAME", "crm_db"),
        "USER": os.environ.get("DBUSER", "postgres"),
        "PASSWORD": os.environ.get("DBPASSWORD", "postgres"),
        "HOST": os.environ.get("DBHOST", "localhost"),
        "PORT": os.environ.get("DBPORT", "5432"),
        # Verify a pooled connection is alive before handing it to a request,
        # so a Postgres restart or dropped connection retries transparently
        # instead of surfacing as a request error.
        "CONN_HEALTH_CHECKS": True,
    }
}


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _reset_rls_context(conn):
    """Clear the tenant RLS context before a connection re-enters the pool.

    `RequireOrgContext` sets `app.current_org` transaction-locally, so it
    reverts on its own. But several call sites legitimately run OUTSIDE that
    request transaction and still set the GUC with SESSION scope
    (is_local=False): every Celery task via `common.tasks.set_rls_context`, the
    anonymous CSAT view, and the SES inbound webhook. psycopg_pool does not
    reset session state on putconn — it only rolls back an open transaction —
    so without this hook a pooled backend carries one tenant's org id to
    whichever request or task borrows it next.

    Setting the GUC to '' is equivalent to never setting it: the policies use
    `NULLIF(current_setting(...), '')`, so both fail closed to zero rows.

    Must leave the connection IDLE — psycopg_pool discards any connection its
    reset function leaves inside a transaction.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.current_org', '', false)")
    if not conn.autocommit:
        conn.commit()


# Bounded connection pool (psycopg3). Without it Django opens one Postgres
# connection per request with no ceiling, so a traffic spike — or a leaked
# long-lived connection (e.g. an SSE stream) — can exhaust a shared cluster.
#
# The pool is PER PROCESS, so the real server-side total is roughly
# (max_size x web worker processes) + (max_size x celery worker processes).
# Keep max_size small and size the sum against the DB role's CONNECTION LIMIT.
# `timeout` is the backpressure valve: once max_size connections are checked
# out, further checkouts wait up to this many seconds and then raise, instead
# of opening an unbounded number of connections.
#
# Disable (DB_POOL_ENABLED=false) when fronting Postgres with an external
# pooler such as PgBouncer that owns pooling instead. Note: CONN_MAX_AGE must
# stay 0 (the default) — Django forbids persistent connections with pooling.
#
# WARNING: if you disable this in favour of PgBouncer, `reset` below stops
# running, and PgBouncer does NOT clear `app.current_org` between clients in
# transaction-pooling mode. Configure `server_reset_query` accordingly, or the
# session-scoped call sites named in _reset_rls_context() will leak across
# tenants.
if os.environ.get("DB_POOL_ENABLED", "true").lower() not in ("false", "0", "no"):
    DATABASES["default"]["OPTIONS"] = {
        "pool": {
            "min_size": _env_int("DB_POOL_MIN_SIZE", 2),
            "max_size": _env_int("DB_POOL_MAX_SIZE", 10),
            "timeout": _env_int("DB_POOL_TIMEOUT", 10),
            # Security: never hand a connection to the next borrower carrying
            # the previous tenant's RLS context. See _reset_rls_context().
            "reset": _reset_rls_context,
        }
    }


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/


TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

AUTH_USER_MODEL = "common.User"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

ENV_TYPE = os.environ.get("ENV_TYPE", "dev")
if ENV_TYPE == "dev":
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    MEDIA_URL = "/media/"
elif ENV_TYPE == "prod":
    from .server_settings import *  # noqa: F401

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@localhost")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@localhost")

# AWS SES settings (loaded when EMAIL_BACKEND is django_ses.SESBackend)
if "django_ses" in EMAIL_BACKEND:
    AWS_SES_REGION_NAME = os.environ.get("AWS_SES_REGION_NAME", "ap-south-1")
    AWS_SES_REGION_ENDPOINT = os.environ.get(
        "AWS_SES_REGION_ENDPOINT", f"email.{AWS_SES_REGION_NAME}.amazonaws.com"
    )
    # Uses AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY from env if set;
    # otherwise falls back to IAM role credentials.


# celery Tasks
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[%(server_time)s] %(message)s",
        },
        "security": {
            "format": "%(asctime)s | %(levelname)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        },
        "console_debug_false": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "logging.StreamHandler",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "filename": "server.log",
        },
        "security_audit": {
            "class": "logging.FileHandler",
            "filename": "security_audit.log",
            "formatter": "security",
        },
    },
    "loggers": {
        "django": {
            "handlers": [
                "console",
                "console_debug_false",
                "logfile",
            ],
            "level": "INFO",
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "security.audit": {
            "handlers": ["security_audit", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

APPLICATION_NAME = "bottlecrm"

SETTINGS_EXPORT = ["APPLICATION_NAME"]

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "common.pat_auth.PATAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "common.external_auth.APIKeyAuthentication",
        # "rest_framework.authentication.SessionAuthentication",
        # "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SPECTACULAR_SETTINGS = {
    "TITLE": "BottleCRM API",
    "DESCRIPTION": "Open source CRM application",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "PREPROCESSING_HOOKS": ["common.custom_openapi.preprocessing_filter_spec"],
    "ENUM_NAME_OVERRIDES": {
        # Role enums
        "ProfileRoleEnum": "common.utils.ROLES",
        "BoardMemberRoleEnum": "tasks.models.BoardMember.ROLE_CHOICES",
        # Priority enums
        "TaskPriorityEnum": "tasks.models.Task.PRIORITY_CHOICES",
        "CasePriorityEnum": "common.utils.PRIORITY_CHOICE",
        "BoardTaskPriorityEnum": "tasks.models.BoardTask.PRIORITY_CHOICES",
        # Status enums
        "TaskStatusEnum": "tasks.models.Task.STATUS_CHOICES",
        "CaseStatusEnum": "common.utils.STATUS_CHOICE",
        "SolutionStatusEnum": "cases.models.Solution.STATUS_CHOICES",
        "DocumentStatusEnum": "common.models.Document.DOCUMENT_STATUS_CHOICE",
        "InvoiceStatusEnum": "invoices.models.Invoice.INVOICE_STATUS",
        "ContactFormStatusEnum": "common.models.ContactFormSubmission.STATUS_CHOICES",
        "LeadStatusEnum": "common.utils.LEAD_STATUS",
    },
}

# JWT_SETTINGS = {
#     'bearerFormat': ('Bearer', 'jwt', 'Jwt')
# }

SWAGGER_SETTINGS = {
    "DEFAULT_INFO": "crm.urls.info",
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter 'Bearer <token>'",
        },
    },
}

CORS_ALLOW_HEADERS = default_headers + ("org",)
# Security: CORS configuration via environment variables
CORS_ORIGIN_ALLOW_ALL = os.environ.get("CORS_ALLOW_ALL", "False").lower() == "true"
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
# Security: CSRF trusted origins via environment variable
_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]

# Security: HSTS with 1 year duration (recommended minimum)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

SIMPLE_JWT = {
    # Security: Reduced token lifetimes
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    # Security: Enable token rotation to invalidate old refresh tokens
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
# it is needed in custome middlewere to get the user from the token
JWT_ALGO = "HS256"


DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "http://localhost:8000")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
SWAGGER_ROOT_URL = os.environ.get("SWAGGER_ROOT_URL", "http://localhost:8000")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "")
