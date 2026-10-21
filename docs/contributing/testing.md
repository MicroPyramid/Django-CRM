# Testing

## Running tests

From `backend/`:

```bash
uv run pytest
```

`backend/pytest.ini` sets `addopts` to include coverage by default,
`--cov=. --cov-config=../.coveragerc --cov-report=term-missing --cov-report=html:htmlcov
--cov-report=xml:coverage.xml`, alongside `--strict-markers --tb=short -v`. So a plain `uv run
pytest` always computes coverage and writes `backend/htmlcov/` and `backend/coverage.xml`, even for
a single test file.

Scope a run to one app, one file, or a keyword the same way you would with any pytest project:

```bash
uv run pytest accounts/tests/                    # one app's test package
uv run pytest leads/tests/test_leads_kanban.py    # one file
uv run pytest -k "test_org_isolation"             # by keyword: matches the cross-tenant
                                                   #   isolation test present in most API test
                                                   #   modules (leads, cases, contacts, ...)
```

## Fast iteration

Coverage instrumentation and the three report formats above add real overhead. For the
edit-run-edit loop, drop coverage and stop at the first failure:

```bash
uv run pytest --no-cov -x
```

`--strict-markers` (also set in `addopts`) means a typo'd **custom** marker fails the run immediately
rather than being silently ignored. Every custom marker you use has to be declared in `pytest.ini`'s
`markers` list. It doesn't touch markers a plugin registers itself, like `@pytest.mark.django_db`
(from `pytest-django`). Those work without appearing in `pytest.ini` at all, which is why every
example on this page uses `django_db` freely alongside the one marker that is declared.

## Markers

`pytest.ini` declares one custom marker:

```ini
markers =
    postgres_only: marks tests that require PostgreSQL
```

`postgres_only` marks the tests that need a real PostgreSQL: RLS policy state, isolation behaviour
under a role that RLS binds, and session-scoped connection state. List them with
`uv run pytest -m postgres_only --collect-only -q`.

## The SQLite caveat

`crm.test_settings` (`backend/crm/test_settings.py`) is the settings module `pytest.ini` points at,
and its `DATABASES` is hardcoded to an in-memory SQLite database, not read from an environment
variable, not conditional on anything. Its own module docstring states why: "RLS (Row-Level
Security) is PostgreSQL-only and is skipped on SQLite." That means **the default `uv run pytest`
run never exercises a single RLS policy**. Every test runs against a database engine that has no
concept of row security at all. Everything you'd normally rely on RLS to catch, an org-filter bug
included, is invisible to this default suite; only the explicit `Model.objects.filter(org=...)` in
application code is being tested. See [Multi-tenancy and RLS](../architecture/multi-tenancy-and-rls.md#the-two-layer-contract)
for why that ORM filter has to be correct on its own merits, independent of RLS.

The `postgres_only` tests close part of that gap. Under SQLite nearly all of them skip, so a green
default run tells you nothing about them. Run them for real with `crm.test_settings_postgres`,
which changes only the database and reads the same `DB*` variables as the application:

```bash
DJANGO_SETTINGS_MODULE=crm.test_settings_postgres DBUSER=<role> DBPASSWORD=<password> \
  uv run pytest --no-cov -m postgres_only
```

**The role must not be a superuser or have `BYPASSRLS`.** Either one bypasses every policy, so the
isolation assertions pass whether or not a policy exists. It needs `CREATEDB` so pytest-django can
build the test database. See [PostgreSQL and RLS](../self-hosting/postgresql-and-rls.md#verifying-isolation)
for setting that role up, and for `manage.py manage_rls --test`, which checks isolation on a real
database outside the suite.

## What CI runs

`.github/workflows/tests.yml` runs the backend suite three ways:

1. **SQLite**, the fast run that produces coverage, after the migration check:
   ```bash
   uv run python manage.py makemigrations --check --dry-run
   uv run pytest -m "not postgres_only" --tb=short -v
   ```
2. **PostgreSQL as the superuser**: the whole suite minus `postgres_only`, for what SQLite cannot
   see (declared string lengths, constraints, real type coercion). RLS is inert under a superuser,
   so this run proves nothing about isolation.
3. **PostgreSQL as `crm_ci`**, a `NOSUPERUSER NOBYPASSRLS` role, running only the `postgres_only`
   tests. This is the run that tests tenant isolation.

The split exists because the shared fixtures insert rows with no `app.current_org` set, which a
policy-bound role refuses. The migration check fails the build when a model change is missing its
migration; see [Pull requests](pull-requests.md#what-ci-runs) for what that means for your workflow.
