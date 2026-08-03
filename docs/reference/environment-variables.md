# Environment variables

This page is the exhaustive table: every environment variable `backend/crm/settings.py` reads,
its real default, and what it's for. [Self-hosting: Environment variables](../self-hosting/environment-variables.md)
is the narrative companion. How configuration loading actually works (`load_dotenv()`, the
`.env.docker` / `.env.docker.local` layering), and the smaller, curated list of variables an
operator actually has to touch to run a working, non-default install. Read that page first if
you're setting up a deployment; come back here when you need the complete list or an exact default.

## How to set them

Every variable in the table below is read with `os.environ.get("NAME", <default>)` (or the
equivalent `os.getenv`) directly in `crm/settings.py`, at process import time: `manage.py
runserver`, `migrate`, a Gunicorn/Uvicorn worker, a Celery worker, and every management command all
read the same values the same way. A `.env` file next to `manage.py` (for a manual install) or
`.env.docker`/`.env.docker.local` (for the Docker Compose stack) is loaded into the process
environment before any of these calls run, so an unset variable falls back to the default in the
**Default** column rather than crashing immediately. That's true even for `SECRET_KEY`: its own
`os.environ.get` call always succeeds, but the value it produces then feeds a separate check a few
lines later that raises `ValueError` once `ENV_TYPE` is anything other than `dev` (see the
`SECRET_KEY` row below): a default that satisfies `os.environ.get` doesn't necessarily satisfy
everything downstream of it. The variables with genuinely no default in code. Read with plain
`os.environ[...]`, so a missing one is an immediate `KeyError` rather than a fallback. Live outside
`crm/settings.py` entirely and are covered in the list below instead of the table.

Three groups of real, project-read environment variables are **not** read by `crm/settings.py`
itself, so they aren't in the table below:

- **`ADMIN_PASSWORD`** is read directly by the `create_default_admin` management command (see
  [Management commands](management-commands.md#create_default_admin)). It still gets its own row
  below because it's part of the same Docker bootstrap flow as `ADMIN_EMAIL`, which *is* read in
  `settings.py`.
- **`AWS_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `SENTRY_DSN`** are read with
  plain `os.environ[...]` (no default) inside `backend/crm/server_settings.py`, which
  `crm/settings.py` only imports when `ENV_TYPE=prod`. A missing one is a `KeyError` at import
  time. The process refuses to start rather than starting half-configured. `ENV_TYPE` itself
  follows the same rule: it's read in `settings.py`, but it's the internal dev/prod switch this
  project's own tests exclude from the table by design, not a self-hoster-facing setting on its
  own. See [Production deployment](../self-hosting/production-deploy.md#required-settings) and
  [Security hardening](../self-hosting/security-hardening.md#secrets) for what `ENV_TYPE=prod`
  actually requires and why it shouldn't be set casually.
- **`BCRM_MCP_ENABLED`** and **`BCRM_BASE_URL`** are two different knobs, both read in
  `backend/crm/asgi.py`, not `crm/settings.py`. Only `BCRM_MCP_ENABLED` (default `"true"`) gates
  whether the optional MCP server is mounted at `/mcp` at all, anything in `0`/`false`/`no`/`off`
  disables it, anything else (including unset) leaves it enabled. `BCRM_BASE_URL` (default
  `http://127.0.0.1:8000`) has no bearing on whether the mount happens; it's the REST API root the
  mounted MCP tools call once it's live. See [MCP server](../integrations/mcp-server.md) for both.

## Reference

### Django core

| Variable | Default | Required | Purpose |
| --- | --- | --- | --- |
| `SECRET_KEY` | `django-insecure-dev-key-please-change-in-production` | Yes, once `ENV_TYPE` is anything other than `dev` (see above) | Django's cryptographic signing key. It also *is* the JWT `SIGNING_KEY`: `SIMPLE_JWT["SIGNING_KEY"]` is set to `SECRET_KEY` directly, so there is no separate JWT signing key setting anywhere in this codebase, and rotating `SECRET_KEY` invalidates every outstanding access and refresh token. See [Architecture: Authentication](../architecture/authentication.md#token-model) and [Security hardening](../self-hosting/security-hardening.md#secrets). |
| `DEBUG` | `False` | No | Django debug mode. Also the sole gate on the `devlogin` management command. See [Management commands](management-commands.md#devlogin). |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Yes, once serving traffic under a real hostname | Comma-separated list, split on `,` into Django's `ALLOWED_HOSTS`. |

### Database

| Variable | Default | Required | Purpose |
| --- | --- | --- | --- |
| `DBNAME` | `crm_db` | No | PostgreSQL database name. |
| `DBUSER` | `postgres` | Yes, before anyone but you can reach the instance | PostgreSQL role. The default is the PostgreSQL superuser account on most installations, and a superuser silently bypasses every RLS policy this project relies on for tenant isolation. See [PostgreSQL and RLS: Creating the application role](../self-hosting/postgresql-and-rls.md#creating-the-application-role). |
| `DBPASSWORD` | `postgres` | Yes, alongside `DBUSER` | PostgreSQL password. |
| `DBHOST` | `localhost` | No | PostgreSQL host. |
| `DBPORT` | `5432` | No | PostgreSQL port. |

### Email

| Variable | Default | Required | Purpose |
| --- | --- | --- | --- |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | No | Django email backend. The default prints outbound mail to stdout instead of sending it. Setting `ENV_TYPE=prod` overrides this unconditionally to `django_ses.SESBackend`, regardless of what this variable is set to. See [Email and Celery](../self-hosting/email-and-celery.md#amazon-ses). |
| `DEFAULT_FROM_EMAIL` | `noreply@localhost` | No | `From` address on outbound mail. |
| `ADMIN_EMAIL` | `admin@localhost` | No | Assigned to `settings.ADMIN_EMAIL` but not consumed anywhere else in `settings.py` itself. The one place it's read outside this module and `create_default_admin` (see below) is `common/views/user_views.py`, which returns it as `admin_email` in the user-list API response context. `create_default_admin` also reads `ADMIN_EMAIL` a second time, independently and with the same default, to name the bootstrap Django superuser account. |
| `AWS_SES_REGION_NAME` | `ap-south-1` | No, unless `ENV_TYPE=prod` | Only read when `"django_ses"` appears in `EMAIL_BACKEND`. True if you set `EMAIL_BACKEND=django_ses.SESBackend` directly, or unconditionally true once `ENV_TYPE=prod` forces that backend. Under `ENV_TYPE=prod`, `server_settings.py` requires this variable outright (`os.environ[...]`, no default) before `settings.py`'s own conditional read ever runs, so the default above is effectively unreachable in that mode. |
| `AWS_SES_REGION_ENDPOINT` | `email.<AWS_SES_REGION_NAME>.amazonaws.com` | No, unless `ENV_TYPE=prod` | Same condition and the same `ENV_TYPE=prod`-makes-it-required caveat as `AWS_SES_REGION_NAME` above. |

### Celery and Redis

| Variable | Default | Required | Purpose |
| --- | --- | --- | --- |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Yes, before anyone but you can reach the instance | Redis URL Celery uses as its message broker. |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Yes, alongside `CELERY_BROKER_URL` | Redis URL Celery uses to store task results. |

### CORS and CSRF

| Variable | Default | Required | Purpose |
| --- | --- | --- | --- |
| `CORS_ALLOW_ALL` | `False` | No | Sets Django's `CORS_ORIGIN_ALLOW_ALL`. Note the name doesn't match the Django setting it controls. `"true"` (case-insensitive) allows every origin; anything else leaves it off. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Yes, once the frontend is served from a real domain | Comma-separated list of allowed CORS origins; each entry is stripped of surrounding whitespace and empty entries are dropped. |
| `CSRF_TRUSTED_ORIGINS` | *(empty, no trusted origins)* | Yes, before anyone but you can reach the instance | Comma-separated list, same stripping rule as `CORS_ALLOWED_ORIGINS`. Each entry needs a scheme, e.g. `https://crm.example.com`. A bare hostname is silently useless to Django's CSRF check. |

### URLs

| Variable | Default | Required | Purpose |
| --- | --- | --- | --- |
| `DOMAIN_NAME` | `http://localhost:8000` | Yes, once self-hosted under a real domain | Base URL embedded in outbound emails' links back to the CRM. This is the **backend's** URL, not necessarily the frontend's. Two uses matter more than the rest: it builds the link an **anonymous client** gets in an emailed invoice/estimate (`invoices/api_views.py`, `invoices/tasks.py`, via `send_invoice_to_client(..., domain=...)`) and the link in a **CSAT survey** email (`cases/tasks.py`, `link = f"{domain}/csat/{raw_token}"`). Both go to people outside the organization, so leaving the `localhost` default in a real deployment doesn't just look wrong internally, it emails dead links to customers. The remaining, lower-stakes uses are internal notification emails (comment-mention, account activation/deactivation, and the per-record "assigned to you" emails in `leads/tasks.py`, `cases/tasks.py`, `opportunity/tasks.py`, `contacts/tasks.py`, `accounts/tasks.py`), which only reach people who already have accounts in the org. |
| `FRONTEND_URL` | `http://localhost:5173` | Yes, once self-hosted under a real domain | Base URL of the SvelteKit frontend. Used to build the welcome email's link and the magic-link sign-in URL (`common/tasks.py`). The links a recipient is actually meant to click into the app. |
| `SWAGGER_ROOT_URL` | `http://localhost:8000` | No | Read into a Django setting in `crm/settings.py`, but not referenced anywhere else in this codebase (backend, frontend, or mobile) as of this writing. Setting it currently has no observable effect. |

### Google OAuth

| Variable | Default | Required | Purpose |
| --- | --- | --- | --- |
| `GOOGLE_CLIENT_ID` | *(empty)* | No, leaving it blank disables Google sign-in | OAuth client ID sent to Google's token endpoint and used as the expected audience when verifying a mobile ID token. See [Google OAuth](../self-hosting/google-oauth.md#backend-configuration). |
| `GOOGLE_CLIENT_SECRET` | *(empty)* | No, leaving it blank disables Google sign-in | OAuth client secret, alongside `GOOGLE_CLIENT_ID` above. |
| `GOOGLE_REDIRECT_URI` | *(empty)* | No | Defined in `settings.py` but not read anywhere else in the backend, the redirect URI actually used in the token exchange is the one the frontend sends in the request body on each call, not this setting. Safe to leave unset even in production; see [Google OAuth](../self-hosting/google-oauth.md#backend-configuration) for why. |

### Docker bootstrap (not read by `crm/settings.py`)

| Variable | Default | Required | Purpose |
| --- | --- | --- | --- |
| `ADMIN_PASSWORD` | *(empty string)* | No, but leaving it unset is a real security gap | Read directly by the `create_default_admin` management command. An empty value doesn't mean "no password", the command falls back to the literal password `admin` and prints a warning. `create_default_admin` runs automatically on every Docker container start (`docker/backend/entrypoint.sh`, right after `migrate`), so an unset `ADMIN_PASSWORD` in a real deployment means the bootstrap Django superuser's password is the literal string `admin` until someone changes it. See [Management commands](management-commands.md#create_default_admin). |
