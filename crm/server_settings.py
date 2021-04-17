import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False

DOMAIN_NAME = "bottlecrm.com"

AWS_STORAGE_BUCKET_NAME = AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
S3_DOMAIN = AWS_S3_CUSTOM_DOMAIN = str(AWS_BUCKET_NAME) + ".s3.amazonaws.com"
AWS_SES_REGION_NAME = os.getenv("AWS_SES_REGION_NAME", "")
AWS_SES_REGION_ENDPOINT = os.getenv("AWS_SES_REGION_ENDPOINT", "")

AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
DEFAULT_S3_PATH = "media"

MEDIA_ROOT = "/%s/" % DEFAULT_S3_PATH
MEDIA_URL = "//%s/%s/" % (S3_DOMAIN, DEFAULT_S3_PATH)
STATIC_URL = "https://%s/" % (S3_DOMAIN)
ADMIN_MEDIA_PREFIX = STATIC_URL + "admin/"

CORS_ORIGIN_ALLOW_ALL = True

AWS_IS_GZIPPED = True
AWS_ENABLED = True
AWS_S3_SECURE_URLS = True

EMAIL_BACKEND = "django_ses.SESBackend"

SESSION_COOKIE_DOMAIN = ".bottlecrm.com"

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)


SENTRY_ENABLED = os.getenv("SENTRY_ENABLED", False)

if SENTRY_ENABLED and not DEBUG:
    if os.getenv("SENTRY_DSN") is not None:
        RAVEN_CONFIG = {
            "dsn": os.getenv("SENTRY_DSN", ""),
        }
        INSTALLED_APPS = INSTALLED_APPS + [
            "raven.contrib.django.raven_compat",
        ]
        MIDDLEWARE = [
            "raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware",
            "raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware",
        ] + MIDDLEWARE
