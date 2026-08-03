# Requirements

What has to be true about your environment before you follow [Docker](docker.md) or
[Production deployment](production-deploy.md). This page only covers versions, hardware shape and
services. See [Manual setup](../getting-started/manual-setup.md) for the commands that install
them.

## Supported versions

| Component | Version | Source |
|---|---|---|
| Python | 3.12 or later | `backend/pyproject.toml` sets `requires-python = ">=3.12"`; `backend/.python-version` pins `3.12` exactly. |
| Django | 6.0.7 or later | `backend/pyproject.toml` dependency `django>=6.0.7`. |
| PostgreSQL | 16 | `docker-compose.yml`'s `db` service uses image `postgres:16-alpine`. This is also the only version this project's own CI ever runs against. See the note below. |
| Redis | 7 | `docker-compose.yml`'s `redis` service uses image `redis:7-alpine`. |
| Node.js | 24 | `.github/workflows/tests.yml`'s `frontend-checks` job sets up `node-version: '24'`. |
| pnpm | 10 | Same job pins the pnpm action to `version: 10`. |

Backend dependencies (`djangorestframework`, `djangorestframework-simplejwt`, `celery`,
`weasyprint`, `gunicorn`, and the rest) are locked in `backend/uv.lock`; `uv sync` from
`backend/` installs the exact versions CI and this documentation were checked against.

**PostgreSQL is not optional.** BottleCRM's multi-tenancy is enforced by PostgreSQL Row-Level
Security (RLS), keyed on the `app.current_org` session variable. See
[PostgreSQL and RLS](postgresql-and-rls.md) for how that works and why it matters. RLS is a
PostgreSQL feature with no SQLite equivalent. The only place SQLite appears in this codebase is
`backend/crm/test_settings.py`, which swaps in an in-memory SQLite database for the test suite
specifically because "RLS ... is PostgreSQL-only and is skipped on SQLite" (its own docstring).
Running the application itself against SQLite is not supported by any settings module in this
repository.

That gap is also why `.github/workflows/tests.yml`'s `backend-tests` job runs
`pytest -m "not postgres_only"` against SQLite and explicitly excludes every test marked
`postgres_only`: those tests need a real PostgreSQL connection to exercise RLS and don't run in
that job at all. Treat PostgreSQL 16, as pinned in `docker-compose.yml`, as the version this
project actually exercises; nothing in this repository documents support for, or testing against,
any other major version.

## Hardware

There is no benchmarked sizing guide in this repository, and this page won't invent one. What you
do need to plan capacity for is the process list a full self-hosted stack runs concurrently:
`docker-compose.yml` defines six long-running services: `db` (PostgreSQL), `redis`, `backend`
(the Django API), `celery-worker`, `celery-beat`, and `frontend`. All but `frontend` (only needed
if you're serving the SvelteKit dev server rather than a built static bundle) are required for the
API and background jobs to function; running them all on one host means sizing for a database, a
key-value store, an application server and a task worker at once, not just the Django process.
`backend/Dockerfile` also installs Cairo/Pango/gdk-pixbuf (WeasyPrint's PDF-rendering
dependencies). PDF generation for invoices and estimates runs synchronously in the request or
task that triggers it, so factor that into whatever process handles it.

## Required services

- **PostgreSQL 16**: the only supported database backend (`django.db.backends.postgresql` is the
  sole `ENGINE` any non-test settings module in this repository sets). Required for RLS-based
  tenant isolation; see [PostgreSQL and RLS](postgresql-and-rls.md).
- **Redis**: `backend/crm/settings.py` reads `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`,
  both defaulting to `redis://localhost:6379/0`. Redis backs both the Celery message broker and
  the result backend; without it, `celery -A crm worker` and `celery -A crm beat` have nothing to
  connect to.

Nothing else is required to run the API itself. Email delivery (console backend by default, SES
optionally), Google OAuth, and Sentry are all read from environment variables with working
defaults or an explicit off-state. See [Production deployment](production-deploy.md) for what
each of those needs when you turn it on.
