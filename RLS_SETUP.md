# PostgreSQL Row-Level Security (RLS) Setup Guide

This file has moved into the documentation site. See
[PostgreSQL and RLS](docs/self-hosting/postgresql-and-rls.md) for the full guide: creating the
non-superuser application role, how RLS policies are enabled by migrations, verifying isolation
with `manage_rls`, Celery's `set_rls_context`, and the mistakes that most often leave a deployment
unprotected.

Two related pages worth knowing about too: [Security hardening](docs/self-hosting/security-hardening.md#database-role)
covers the database role as part of a production checklist, and
[Troubleshooting](docs/self-hosting/troubleshooting.md) covers the specific symptoms of a
misconfigured role (empty admin lists, data visible across organizations, and more).

This file is kept only so existing links to `RLS_SETUP.md` keep resolving; it is not maintained
as a setup guide in its own right. Notably, the number of RLS-protected tables cited in earlier
versions of this file (24) was out of date. The current, verified count is documented on the
linked page rather than repeated here, precisely so this file can't drift out of sync again.
