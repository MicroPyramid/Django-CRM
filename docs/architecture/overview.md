# Architecture overview

This section is for developers extending or auditing BottleCRM, not for operators deploying it.
See Self-hosting for that. It explains how the backend is put together: what runs before a view
ever sees a request, what each Django app owns, and where to go for the detail on tenancy,
authentication, permissions, the data model, and background jobs.

## The three clients

A SvelteKit web app (`frontend/`), a Flutter mobile app (`mobile/`), and any third-party
integration all talk to the same Django REST Framework backend (`backend/`) over the same JSON
API: there is no separate mobile API or web-only endpoint set. `crm/urls.py` mounts the entire
API under `/api/`, split into `common.app_urls` (auth, org/profile management, teams, tags,
notifications, documents, custom fields, and one route each into `accounts`, `contacts`, `leads`,
`opportunity`, `tasks`, `cases`, `invoices`, boards, business hours, and macros) plus
`invoices.public_urls` for the anonymous client-portal endpoints. Because every client shares one
API, an authorization rule enforced in a view protects all three clients at once, and,
conversely, a rule enforced only in the SvelteKit UI protects none of them, since a script or a
modified mobile build reaches the API directly.

## Request lifecycle

Tenancy is established in middleware, before any view code runs, in a fixed order defined in
`MIDDLEWARE` in `backend/crm/settings.py`:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "crum.CurrentRequestUserMiddleware",
    "common.middleware.get_company.GetProfileAndOrg",
    "common.middleware.rls_context.RequireOrgContext",
]
```

The two that matter for multi-tenancy run last, in this order:

1. **`GetProfileAndOrg`** (`backend/common/middleware/get_company.py`) resolves who the caller is
   and which org they're acting in. For a request bearing a personal access token it resolves the
   token first, deliberately before the JWT branch, so a PAT is never handed to the JWT decoder.
   For a JWT-bearing request it decodes the access token, reads the `org_id` claim out of the
   signed payload (never out of a header or body. See
   [Authentication](authentication.md#claims)), and looks up an active `Profile` for that
   `user_id`/`org_id` pair; only if that profile exists does it set `request.profile` and
   `request.org`. For an org-API-key request it resolves the key to the org's first active
   `ADMIN` profile. In every path, the org on the request is a fact the server derived and
   verified, never a value taken as-is from the client.
2. **`RequireOrgContext`** (`backend/common/middleware/rls_context.py`) runs next and does two
   things: it rejects any request to a non-exempt path with a 403 if `request.org` was never set
   by the step above, and, this is the step that actually enables tenant isolation, it sets the
   PostgreSQL session variable `app.current_org` to that org's id with
   `SELECT set_config('app.current_org', %s, false)`, and resets it to an empty string after the
   response. Every Row-Level Security policy in the schema keys off this one session variable; see
   [Multi-tenancy and RLS](multi-tenancy-and-rls.md) for how.

So the order is: identity and org are established and validated from the JWT first, and only once
that has succeeded is the database told which org's rows the rest of this request may see. A view
never runs before both steps have completed; `RequireOrgContext` sits after `GetProfileAndOrg` in
the list above and returns a response itself (the 403) rather than calling `get_response` when the
context is missing, so a request that fails tenancy resolution never reaches URL dispatch.

This file also defines an older class, `SetOrgContext`, whose own docstring describes it as the
one wired into `MIDDLEWARE`. That docstring is stale. `SetOrgContext` sets the session variable
but never rejects a context-less request; `RequireOrgContext` is what `settings.py` actually
lists, and it is the one enforced.

One layer above middleware, DRF's own authentication runs at view dispatch time
(`DEFAULT_AUTHENTICATION_CLASSES` in `REST_FRAMEWORK`: `PATAuthentication`, then simplejwt's
`JWTAuthentication`, then `APIKeyAuthentication`) to populate `request.user` for `IsAuthenticated`
and similar permission classes. This is a second, independent pass over the same credential,
`PATAuthentication` reuses the PAT the middleware already resolved (stashed as `request._pat`) to
avoid a second lookup, but a JWT is decoded once by the middleware for org context and again by
`JWTAuthentication` for `request.user`. Every view still needs `permission_classes` set correctly;
authentication alone only establishes identity, not what that identity may do. See
[Permissions and roles](permissions-and-roles.md).

## Backend layout

```
backend/
├── crm/            # Project config: settings.py, urls.py, celery.py
├── common/         # Cross-cutting: User/Org/Profile, middleware, RLS config, permissions,
│                   # auth views, personal access tokens, notifications, tags, teams, custom
│                   # fields, documents, packs, security audit log
├── accounts/       # Account (company/customer) records
├── contacts/       # Contact (person) records
├── leads/          # Leads, lead pipelines/stages, lead-to-account conversion
├── opportunity/     # Sales pipeline: Opportunity, line items, stage aging, sales goals
├── cases/          # Support tickets: Case, SLAs, CSAT, escalation/routing, inbound email
├── tasks/          # Task management and Kanban boards (Board/BoardColumn/BoardTask)
├── invoices/        # Billing: invoices, estimates, recurring invoices, products, payments,
│                    # and the anonymous client-portal views (invoices.public_urls)
├── orders/          # Sales orders and order line items
├── business_hours/  # Per-org working-hours calendars that SLA timers honor
└── macros/          # Canned responses / saved replies
```

`common` is the one app every other app depends on for tenancy itself: it owns the
`User`/`Org`/`Profile` models, the RLS configuration (`common/rls/`), the permission classes
(`common/permissions.py`), and every authentication path (`common/views/auth_views.py`,
`common/pat_auth.py`, `common/external_auth.py`). Every domain app's *models* build on `common`
(`BaseModel`/`BaseOrgModel` from `common.base`, `Org`/`Profile` from `common.models`) and never the
other way around. That one-directional rule doesn't extend to `common`'s own *views*, though:
several of them are cross-cutting by nature and import domain-app models directly, the dashboard
(`common/views/dashboard_views.py`), global search (`common/search_views.py`), tag usage counts
(`common/views/tags_views.py`), and vertical-pack application (`common/packs/applier.py`) all pull
in `Lead`, `Opportunity`, `Case`, and others, because aggregating across every domain app is
exactly what those views are for. Only the model layer is strictly one-directional.

The `teams` Django app referenced in some older documentation and comments no longer exists as a
separate app; `Teams` is a model in `common/models.py`, and `INSTALLED_APPS` in
`backend/crm/settings.py` has a commented-out `# "teams",  # Merged into common app` line marking
where it used to be.
