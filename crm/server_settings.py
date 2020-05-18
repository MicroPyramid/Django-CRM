import os

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.middleware.get_company.GetCompany",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "dj_crm",
        "USER": "admin",
        "PASSWORD": "U988fQkB5sW7eprr",
        "HOST": "88.99.114.133",
        "PORT": "5432",
    }
}

# celery Tasks
CELERY_BROKER_URL = "redis://88.99.114.133:6379"
CELERY_RESULT_BACKEND = "redis://88.99.114.133:6379"

# Load the local settings file if it exists
if os.path.isfile("crm/local_settings.py"):
    from .local_settings import *
elif os.path.isfile("crm/server_settings.py"):
    from .server_settings import *

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "88.99.114.133:11211",
    }
}
