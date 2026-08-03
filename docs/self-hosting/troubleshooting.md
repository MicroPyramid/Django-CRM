# Troubleshooting

Five symptoms that come up often enough in a multi-tenant, RLS-backed deployment to be worth their
own page, each with the specific cause and a command that confirms it rather than a guess.

## Every list is empty

Two distinct, verifiable causes, depending on where you're looking:

**Through the API**, `HasOrgContext` (`backend/common/permissions.py`) is the permission class most
list/detail views use alongside `IsAuthenticated`. It denies with a `403` and the message
`"Organization context is required. Please login again."` whenever `request.profile` or
`request.org` is unset, which happens when the JWT you're sending has no `org_id` claim (a token
minted without picking an org yet. See [First sign-in](../getting-started/first-sign-in.md#choosing-an-organization))
or belongs to a profile that's no longer active in that org. That response body is the confirmation:
if you're getting `403` with that message rather than an empty `200`, this is it, and the fix is to
obtain a token with the right org bound (via `/api/auth/switch-org/`, or `devlogin --org` in
development).

**Through Django admin** (`/admin/`), the failure looks different and is easy to miss: `/admin/` is
listed in `RequireOrgContext.EXEMPT_PATHS` (`backend/common/middleware/rls_context.py`), which
exempts it from *requiring* org context, but exemption from requiring a context is not the same as
*setting* one, and nothing else sets `app.current_org` for an admin-authenticated request either. On
a correctly configured, non-superuser database role, every RLS-protected model registered in Django
admin (`Lead`, `Task`, `Board`, `Invoice`, and others. See each app's `admin.py`) will show **zero
rows in the admin list view even though the data exists**, because the RLS policy's
`NULLIF(current_setting('app.current_org', true), '')` evaluates to `NULL` with no context set, and
`org_id::text = NULL` is never true. Confirm this by comparing counts: the same model returns real
data through `GET /api/leads/` (which does have org context) but nothing through the `Lead` admin
changelist at `/admin/leads/lead/` (`/admin/leads/` alone is the app index, listing model names, not
rows. It won't show this). This is expected behavior, not a bug to fix. Django admin was never
wired to set RLS context, and doing so would need to resolve which org an admin-site request is
"for," which the admin UI itself has no concept of.

## Tenant data is visible across organizations

This is the fail-safe design inverted, and it has one cause in this codebase: the database role
Django connects as is a PostgreSQL superuser, and superusers bypass Row-Level Security entirely,
silently, no error, no log line, every policy still exists and looks correctly configured. Confirm
it directly:

```bash
cd backend
uv run python manage.py manage_rls --verify-user
```

This prints `Is superuser: True` and explicit remediation SQL if the role is a superuser, or a
success line if it isn't. The default `DBUSER` (unset, falling back to `postgres`) is a superuser on
most PostgreSQL installations. See [PostgreSQL and RLS](postgresql-and-rls.md#creating-the-application-role)
for how to create and switch to a dedicated non-superuser role, and don't trust a green local/dev
environment as proof this is configured correctly: a superuser dev database makes every endpoint
*look* correctly isolated purely because the application's own `.filter(org=...)` calls happen to be
right, while RLS itself does nothing underneath them.

## Celery tasks see no data

A Celery worker never runs Django's request middleware, so nothing sets `app.current_org` for it the
way `RequireOrgContext` does for an HTTP request. Every task in `backend/common/tasks.py` that
queries an org-scoped table is expected to call `set_rls_context(org_id)`, also defined in that
module, as its first line before touching the ORM. A task that queries an RLS-protected model
without calling it first runs with an empty RLS context on a fresh worker connection, which. Per
the same fail-safe design as above. Means the query returns **zero rows**, not the wrong org's
rows, but it does mean the task silently does nothing useful. Confirm by reading the task itself for
a `set_rls_context(...)` call before its first org-scoped query; there's no runtime flag or log line
that surfaces this automatically. See [Email and Celery](email-and-celery.md#rls-in-background-tasks)
for the pattern and the two tasks that intentionally skip it.

## Sign-in redirects in a loop

The SvelteKit frontend stores JWT tokens in httpOnly cookies whose `secure` flag is gated on
`NODE_ENV`/`env.NODE_ENV === 'production'`: this pattern repeats across
`frontend/src/hooks.server.js` and every `+page.server.js` that sets an auth-related cookie (login,
magic-link verify, org selection). If you set `NODE_ENV=production` on the Node process serving the
frontend while the site is actually reached over plain HTTP (no TLS terminated in front of it, or a
proxy that isn't forwarding correctly), every cookie gets written with the `Secure` attribute, and
the browser silently refuses to store or send a `Secure` cookie over a non-HTTPS connection. The
result: sign-in appears to succeed (the OAuth/magic-link exchange completes and the server tries to
set the cookies), but the next request arrives with no `jwt_access` cookie, `hooks.server.js` treats
it as unauthenticated, and redirects back to `/login`, which the user completes again, with the
same outcome. Confirm it by inspecting the `Set-Cookie` response header in the browser's network
tab: a `Secure` attribute on a response served over `http://` is the signature of this exact failure.
The fix is to serve the frontend over HTTPS if `NODE_ENV=production` is set, or leave `NODE_ENV`
unset/`development` until TLS is actually in front of it.

## Migrations fail

`manage.py migrate` is also what applies and re-applies Row-Level Security policies. See
[PostgreSQL and RLS](postgresql-and-rls.md#enabling-policies). Two things about how those specific
migrations are written are worth knowing if `migrate` fails partway through: they run with
`atomic = False` (every migration that calls `get_enable_policy_sql` carries the comment "RLS policy
creation can't run inside an atomic block"), and the SQL those migrations run always
`DROP POLICY IF EXISTS` before `CREATE POLICY`, so re-running `manage.py migrate` after an
interrupted run is safe rather than something that fails on a duplicate policy.

`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`, which these migrations run, requires the connecting
role to either be the table's owner or a superuser. As long as the same non-superuser role runs
every migration for a given database from the very first one, the setup this project documents in
[PostgreSQL and RLS](postgresql-and-rls.md#creating-the-application-role). That role owns every
table it creates and this is never an issue. It becomes one if you provision the schema differently:
for example, running the first `migrate` as the `postgres` superuser and only switching `DBUSER` to
a dedicated non-superuser role afterward leaves that role without ownership of the already-created
tables, and a later migration's `ALTER TABLE` fails with a permission error naming the table. If
`migrate` fails this way, check which role owns the affected table (`\dt+ <table>` in `psql`) against
the role in `DBUSER`.

Separately, if you've forked this project and modified a model: this project's own CI runs
`manage.py makemigrations --check --dry-run` before its test suite specifically to catch a model
change that never got its migration generated. Run that same command locally after any model
change.
