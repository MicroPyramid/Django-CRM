# Backups and upgrades

This page covers what actually needs backing up in a self-hosted BottleCRM instance, and what
"upgrading" means for the Docker Compose setup versus a manual install.

## What to back up

Two things hold state that nothing else can regenerate: **the PostgreSQL database** and **the media
directory**. Everything else: the application code, static assets (`collectstatic` output),
installed dependencies, the Redis broker/result store, is either checked into version control,
rebuilt from it, or disposable. Redis in particular is not a backup concern: it's the Celery broker
and result backend (`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`), not a store of business data: an
in-flight task queue lost on restart means a retry, not lost records, since the records themselves
live in PostgreSQL.

## Backing up PostgreSQL

Every org, every record, every RLS-protected row lives in the database configured by `DBNAME`/
`DBUSER`/`DBHOST`/`DBPORT` (see [Environment variables](environment-variables.md#database)). A plain
`pg_dump` is enough for a logical backup:

```bash
pg_dump -h <DBHOST> -p <DBPORT> -U <DBUSER> -d <DBNAME> -F c -f backup.dump
```

Under Docker Compose, run it against the `db` service:

```bash
docker compose exec db pg_dump -U postgres -d crm_db -F c -f /tmp/backup.dump
docker compose cp db:/tmp/backup.dump ./backup.dump
```

`docker-compose.yml` also declares `postgres_data` as a named volume mounted at
`/var/lib/postgresql/data` on the `db` service. This is the actual on-disk database, and is what
must survive a `docker compose down` (which removes containers but leaves named volumes intact) or a
rebuild. Only `docker compose down -v`, or removing the volume explicitly, deletes it. See
[Docker](docker.md#persisting-data).

## Media files

`MEDIA_ROOT` depends on which settings module is active. With `ENV_TYPE=dev` (the default),
`crm/settings.py` sets `MEDIA_ROOT` to a local `media/` directory under `BASE_DIR`, and uploaded
files (invoice attachments, case attachments, and similar) land on local disk. Under Docker Compose
this resolves to `/app/media` inside the `backend` container, which, because `/app` is the
bind-mounted `./backend` directory, not a named volume. Means uploads land in `backend/media/` on
the host automatically, but are **not** covered by the `postgres_data` volume's guarantees. Back up
`backend/media/` (or your equivalent local media path in a manual install) alongside the database.

With `ENV_TYPE=prod`, `backend/crm/server_settings.py` switches `DEFAULT_FILE_STORAGE` to
`storages.backends.s3boto3.S3Boto3Storage` and media is written to the S3 bucket named by
`AWS_BUCKET_NAME` instead of local disk: in that configuration, back up the bucket using your normal
AWS backup practice (versioning, replication, or a separate backup job) rather than a filesystem
backup.

## Upgrading

Under Docker Compose, `docker/backend/entrypoint.sh` runs `manage.py migrate --noinput`,
`manage.py create_default_admin` and `manage.py collectstatic --noinput` on **every** container
start, not only the first, so pulling new source and rebuilding is the entire upgrade procedure:

```bash
git pull
docker compose up --build
```

There is no separate migration step to remember; the schema and static assets are brought up to
date automatically on restart. Back up `postgres_data` and `backend/media/`, per the sections above,
before upgrading across any change you're not confident is backward compatible with your existing
data, nothing in this compose setup takes an automatic backup for you.

For a manual install (no Docker), the equivalent is: pull the new source, `uv sync` to update
dependencies, then run migrations and `collectstatic` yourself before restarting the process (see
[Migrations](#migrations) below and [Production deployment](production-deploy.md#before-you-start)).

## Migrations

`manage.py migrate` applies schema changes and, for the RLS-related migrations specifically,
re-applies the Row-Level Security policies described in
[PostgreSQL and RLS](postgresql-and-rls.md#enabling-policies). RLS is enabled and disabled by
migrations, not by any separate command. Those migrations run with `atomic = False` (the comment
next to it, repeated across every migration that calls `get_enable_policy_sql`, is explicit: "RLS
policy creation can't run inside an atomic block"), and `get_enable_policy_sql()` itself issues
`DROP POLICY IF EXISTS` before each `CREATE POLICY`, so re-running `migrate` after an interrupted run
is safe rather than something that fails on a duplicate policy.

This project's own CI enforces that no model change ships without a matching migration:
`.github/workflows/tests.yml` runs

```bash
uv run python manage.py makemigrations --check --dry-run
```

as a dedicated step before the test suite. If you fork this project and add or change a model, run
`manage.py makemigrations` yourself and commit the result. The check names the problem directly;
without it you would find out indirectly, from a test or a request failing against a column the
database does not have.
