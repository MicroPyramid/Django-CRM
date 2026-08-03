# Production deployment

Neither `docker-compose.yml` nor the repo-root `Dockerfile` builds a production-hardened
deployment out of the box. See the warning in [Docker](docker.md). This page covers what
changes: the process that serves requests, how static files are handled, what sits in front of
Django, and which environment variables the codebase itself treats as security-relevant. It
assumes you already have a working install per [Manual setup](../getting-started/manual-setup.md)
or [Docker](docker.md) and a PostgreSQL role configured per
[PostgreSQL and RLS](postgresql-and-rls.md).

## Before you start

There is no bundled production `docker-compose` file, systemd unit, or process manager
configuration in this repository, the `Dockerfile` builds an image (`backend/Dockerfile` puts
`uv`-managed dependencies and the venv's `bin/` on `PATH`, so `gunicorn`, `celery`, and `python`
all resolve inside it), but what command that image *runs* is up to you: `docker-compose.yml`'s
`backend` service overrides it with `/entrypoint.sh`, which calls `manage.py runserver`, the
Django development server. For a production container or host process you supply your own start
command (see [Application server](#application-server) below) instead of that entrypoint script.

Whatever you run it as, apply migrations and collect static files before serving traffic:

```bash
cd backend
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
```

## Application server

`backend/pyproject.toml` lists `gunicorn>=26.0.0` under its dependencies, commented "Production
WSGI server". Gunicorn is the WSGI server this project ships as a dependency for serving the
Django app itself. `backend/crm/wsgi.py` exposes the standard `application` callable, so from
`backend/`:

```bash
cd backend
uv run gunicorn crm.wsgi:application --bind 0.0.0.0:8000
```

There is one documented exception to WSGI, in the codebase's own words. `backend/crm/asgi.py`
carries this docstring:

> Production deploy must run an ASGI server pointing at this module:
> `uvicorn crm.asgi:application --host 0.0.0.0 --port 8000`

The reason given is the in-app notifications SSE (server-sent events) stream: it's an async view
serving a long-lived connection, and running it under WSGI (Gunicorn) "will hold a worker
hostage" for the life of each connection. `uvicorn[standard]>=0.51.0` is a listed dependency
alongside Gunicorn for exactly this path. In short: if you need the SSE notification stream to
work correctly under concurrent load, serve via `uvicorn crm.asgi:application`, not
Gunicorn/WSGI; if you don't,
Gunicorn against `crm.wsgi:application` is what this project bundles as its production WSGI
dependency.

## Static files

`whitenoise.middleware.WhiteNoiseMiddleware` is in `MIDDLEWARE` (immediately after
`SecurityMiddleware`), and `STATICFILES_STORAGE` is set to
`whitenoise.storage.CompressedManifestStaticFilesStorage`. This means Django itself serves static
assets, compressed and content-hashed, directly from the WSGI/ASGI process; you do not need a
separate static file server or a reverse-proxy `location /static/` block for correctness. Static
files are collected to `STATIC_ROOT` (`backend/staticfiles/`, i.e. `BASE_DIR/staticfiles`) under
`STATIC_URL = "/static/"` by `manage.py collectstatic`, which you must run yourself. Gunicorn
does not run it for you (the Docker Compose entrypoint does, but only because
`docker/backend/entrypoint.sh` calls it explicitly on every start).

Media (user-uploaded files: invoice attachments, case attachments, and similar) is separate from
static files and is not covered by WhiteNoise. With `ENV_TYPE=dev` (the default),
`MEDIA_ROOT`/`MEDIA_URL` are a local `media/` directory served through Django itself; with
`ENV_TYPE=prod`, `backend/crm/server_settings.py` is imported instead and switches
`DEFAULT_FILE_STORAGE` to `storages.backends.s3boto3.S3Boto3Storage`, reading `AWS_BUCKET_NAME`,
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SES_REGION_NAME`, `AWS_SES_REGION_ENDPOINT` and
`SENTRY_DSN` from the environment with `os.environ[...]`: a plain `KeyError` at import time, and
the process refusing to start, if any of them are unset. It also switches `EMAIL_BACKEND` to
`django_ses.SESBackend` and hardcodes `SESSION_COOKIE_DOMAIN = ".bottlecrm.io"`. That domain is
specific to the project's own SaaS hosting, not to your deployment. Setting `ENV_TYPE=prod`
without also being ready to supply AWS S3, SES and Sentry credentials, and without meaning to
scope session cookies to `bottlecrm.io`, will not do what you want. See
[Required settings](#required-settings) below for the practical consequence.

## Reverse proxy

Nothing in `backend/crm/settings.py` terminates TLS, and `SECURE_PROXY_SSL_HEADER` is not set
anywhere in this codebase's settings modules. Concretely: if you terminate TLS at a reverse proxy
(nginx, Caddy, or similar) and forward plain HTTP to Gunicorn/Uvicorn, Django's
`request.is_secure()` will report `False` for every request unless you add
`SECURE_PROXY_SSL_HEADER` yourself (typically pointing at the `X-Forwarded-Proto` header your
proxy sets). This project does not configure that for you. `SECURE_HSTS_SECONDS = 31536000`
(one year), `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`, `SECURE_HSTS_PRELOAD = True` and
`SECURE_CONTENT_TYPE_NOSNIFF = True` are all set unconditionally in `backend/crm/settings.py`, but
Django's `SecurityMiddleware` only emits the `Strict-Transport-Security` header on requests it
considers secure, so without `SECURE_PROXY_SSL_HEADER` configured correctly for your proxy, that
HSTS configuration silently never takes effect.

Point your proxy at whichever port your application server binds (`8000` in the examples above),
and route `/` there. There's no repo-provided proxy config (nginx site file, Caddyfile, or
similar) to point to. The specifics are yours to write.

## Required settings

`backend/crm/settings.py` reads these from the environment at import time (i.e. at process
startup, not per-request):

| Variable | Behavior |
|---|---|
| `SECRET_KEY` | Defaults to the literal string `"django-insecure-dev-key-please-change-in-production"` if unset. The module itself checks this: if `SECRET_KEY` is empty or starts with `"django-insecure"` **and** `ENV_TYPE != "dev"`, it raises `ValueError("SECRET_KEY must be set to a secure value in non-dev environments")` at import time, a hard startup failure, not a warning. This guard only fires when `ENV_TYPE` is set to something other than `dev`; given the `ENV_TYPE=prod` consequences described above (S3/SES/Sentry env vars becoming mandatory, the hardcoded `.bottlecrm.io` cookie domain), don't rely on that check alone. Set a real, unique `SECRET_KEY` regardless of `ENV_TYPE`. |
| `DEBUG` | Must be `False` in production. Read as `os.environ.get("DEBUG", "False").lower() == "true"`, defaults to `False` already, so the failure mode to avoid is *explicitly* setting `DEBUG=True` (as `.env.docker` does for local development) and carrying that into production. |
| `ALLOWED_HOSTS` | A comma-separated environment variable: `os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")`. Set it to the hostname(s) you'll actually be served on, e.g. `ALLOWED_HOSTS=crm.example.com`. |
| `CSRF_TRUSTED_ORIGINS` | Also comma-separated: `os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")`, empty by default. Django requires each entry to include a scheme (e.g. `https://crm.example.com`), not a bare hostname. |

A few more the same module reads, worth setting deliberately rather than leaving at their
defaults: `CORS_ALLOWED_ORIGINS` (comma-separated, defaults to the two local dev frontend
origins) and `CORS_ALLOW_ALL` (`CORS_ORIGIN_ALLOW_ALL`, `.env.docker` sets this `True` for local
development. Leave it `False` in production and rely on `CORS_ALLOWED_ORIGINS` instead), and
`DOMAIN_NAME`/`FRONTEND_URL`, which are interpolated into emails (magic links, notifications) and
so need to point at your real, public hostnames.
