"""
Test settings for Django CRM backend.

Uses SQLite in-memory database instead of PostgreSQL for fast, isolated tests.
RLS (Row-Level Security) is PostgreSQL-only and is skipped on SQLite.
"""

from crm.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
