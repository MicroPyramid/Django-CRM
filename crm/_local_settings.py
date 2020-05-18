from crm.settings import *

DOMAIN_NAME = "test.io"

SESSION_COOKIE_DOMAIN = ".test.io"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "dj_crm",
        "USER": "postgres",
        "PASSWORD": "root",
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5433"),
    }
}

ALLOWED_HOSTS = ["*"]
