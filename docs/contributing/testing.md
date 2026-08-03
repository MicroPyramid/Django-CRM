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
example on this page uses `django_db` freely alongside the two markers that actually are declared.

## Markers

`pytest.ini` declares exactly two custom markers:

```ini
markers =
    slow: marks tests as slow
    postgres_only: marks tests that require PostgreSQL
```

`postgres_only` is in active use. Exactly six tests carry it, confirmed by collecting the marker
directly (`uv run pytest -m postgres_only --collect-only` → `6/2776 tests collected`), across four
files: `common/tests/test_pat_auth.py` (one test), `common/tests/test_pat_model.py` (one),
`common/tests/test_rls_pipeline_tables.py` (two), and `invoices/tests/test_portal_rls.py` (two).
(`common/tests/test_pat_integration.py` mentions `postgres_only` only in a comment explaining that
its own tests deliberately *don't* carry the marker and run on SQLite instead. It contributes zero
of the six.) Four of the six assert RLS policy state directly (`pg_policies`,
`pg_class.relrowsecurity`): the two in `test_rls_pipeline_tables.py`, plus one each in
`test_pat_model.py` and `test_portal_rls.py` confirming `personal_access_token` and
`portal_access_token` deliberately carry *no* policy. The other two assert isolation *behaviour*
under a real, RLS-enforcing role instead of reading policy metadata:
`test_pat_auth.py::test_cross_org_pat_cannot_read_other_orgs_leads` calls the real `/api/leads/`
endpoint and checks a foreign org's lead never appears, and
`test_portal_rls.py::test_resolution_reads_estimate_that_empty_context_hides` exercises the full
portal-token resolution path. `slow` is declared but,
as of this writing, applied to nothing (`grep -rn "pytest.mark.slow" --include='*.py' .`, excluding
`venv/`, returns no matches in application code). It's reserved for future use, not a marker you'll
see filtering anything today.

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

The `postgres_only`-marked tests exist to close part of that gap, and they self-skip safely rather
than fail when there's no PostgreSQL connection: each one checks `connection.vendor != "postgresql"`
and calls `pytest.skip(...)` if so. Under the SQLite settings this repository ships, that check is
always true, so these six tests always skip. They don't fail, and a green `uv run pytest` run tells
you nothing about whether they'd pass. One of them, `test_portal_rls.py`'s module docstring,
describes an intended way to actually run them for real, against a non-superuser PostgreSQL role:
`RLS_ENFORCE=1`, pointed at a `crm.test_settings_postgres` module. A comment in `backend/.env`
(gitignored, `.gitignore:20`, and absent from `.env.example`, so a fresh clone has neither the
file nor the reference) names the same two pieces. Neither source is authoritative, because that
settings module does not exist anywhere in this checkout as of this writing, so this documented path
does not currently work. If you need to prove RLS isolation holds against real data rather than
just reading the policy SQL, use `manage.py manage_rls --test` against a real, non-superuser-configured PostgreSQL
database instead. See [PostgreSQL and RLS](../self-hosting/postgresql-and-rls.md#verifying-isolation)
for exactly what it proves and how to set up that role.

## What CI runs

`.github/workflows/tests.yml`'s `backend-tests` job runs on the same SQLite settings described
above, there's no PostgreSQL service in that job, so `postgres_only` tests skip there too, and
CI itself has no path that runs them for real. Two steps matter, in this order:

```bash
uv run python manage.py makemigrations --check --dry-run
uv run pytest -m "not postgres_only" --tb=short -v
```

The migration check runs first and fails the build if any model change is missing its migration.
See [Pull requests](pull-requests.md#what-ci-runs) for what that means for your workflow. The
`-m "not postgres_only"` filter on the test step is redundant with the tests self-skipping, but
makes the exclusion explicit in the command itself rather than relying on every future
`postgres_only` test remembering its own skip guard.
