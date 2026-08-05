"""Test settings that run the suite against a real PostgreSQL.

`crm.test_settings` uses in-memory SQLite, which is fast and is what CI has
always run. It also cannot see an entire class of defect, and that class keeps
producing real bugs:

* an org name longer than `varchar(100)` raised `DataError` and an uncaught
  500 in production, while all 3113 SQLite tests passed (SQLite ignores
  declared string lengths entirely)
* six pipeline tables shipped with no RLS policy, invisible because RLS is a
  PostgreSQL feature and every test skipped it
* the `postgres_only` marker exists precisely for tests that need the real
  database, and CI ran with `-m "not postgres_only"`, so none of them had ever
  executed there

This module changes only the database. Everything else, the eager-broker
Celery config and the cheap password hasher, is inherited from
`crm.test_settings` so the two runs differ in exactly one variable.

Connection details come from the same `DBNAME`/`DBUSER`/`DBHOST`/`DBPORT`
environment variables the application settings read, so this needs no
CI-specific values baked in.

**The role must not be a superuser.** A PostgreSQL superuser bypasses RLS
outright, and `get_enable_policy_sql` sets `FORCE ROW LEVEL SECURITY` so even
the table owner is subject to its policies. Running these tests as `postgres`
would leave every isolation assertion vacuously true, which is the failure mode
described in `RLS_SETUP.md`.
"""

import os

from crm.test_settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DBNAME", "crm_db"),
        "USER": os.environ.get("DBUSER", "postgres"),
        "PASSWORD": os.environ.get("DBPASSWORD", "postgres"),
        "HOST": os.environ.get("DBHOST", "localhost"),
        "PORT": os.environ.get("DBPORT", "5432"),
        "CONN_MAX_AGE": 0,
    }
}
