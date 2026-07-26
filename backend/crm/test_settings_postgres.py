"""Test settings that run the suite against real PostgreSQL.

`crm.test_settings` swaps in SQLite for speed, which is the right default — but
SQLite has no `set_config()` and no row-level security, so every RLS, pooling
and `postgres_only` test short-circuits on `connection.vendor != "postgresql"`.
A green run under those settings says nothing about tenant isolation.

Use this module to exercise them for real:

    DJANGO_SETTINGS_MODULE=crm.test_settings_postgres uv run pytest
    # or, without touching the env:
    uv run pytest --ds=crm.test_settings_postgres -m postgres_only

Database connection details come from the same DB* environment variables as
production (see `crm.settings`); Django creates and drops a `test_`-prefixed
database, so it never touches your development data.

By default this connects as the normal `DBUSER`. If that account is a superuser
(or has BYPASSRLS) then RLS is inert, and the tenant-isolation tests skip
loudly rather than passing for the wrong reason.

To actually exercise row-level security, opt in explicitly:

    RLS_ENFORCE=1 uv run pytest --ds=crm.test_settings_postgres -m postgres_only

That connects as `RLS_TEST_DBUSER` / `RLS_TEST_DBPASSWORD` (RLS_SETUP.md creates
`crm_user` for this; it needs CREATEDB so the test database can be built).

This is opt-in rather than the default on purpose: most of the suite's fixtures
insert rows without first setting `app.current_org`, so under an RLS-enforcing
role their INSERTs are rejected outright ("new row violates row-level security
policy"). Making the whole suite RLS-clean is a separate piece of work; until
then, run the `postgres_only` subset with RLS_ENFORCE=1 and the rest without.
"""

import os

from crm.settings import *  # noqa: F401, F403

if os.environ.get("RLS_ENFORCE") == "1":
    # Connect as a non-superuser so row-level security is actually enforced.
    # Only the credentials are overridden — host/port/name and the psycopg3 pool
    # block (including its RLS reset hook) are inherited unchanged, so the tests
    # exercise the same connection setup production uses.
    DATABASES["default"] = {  # noqa: F405
        **DATABASES["default"],  # noqa: F405
        "USER": os.environ["RLS_TEST_DBUSER"],
        "PASSWORD": os.environ["RLS_TEST_DBPASSWORD"],
    }

# No broker in test runs. Views dispatch tasks through `transaction.on_commit`,
# which conftest patches to fire synchronously, so nothing needs Redis.
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
