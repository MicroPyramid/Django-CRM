# Repository layout

This page is a map, not a tutorial. It tells you where to look, and links to the pages that explain
*why* each part is shaped the way it is.

## Top level

```
Django-CRM/
├── backend/             # Django REST Framework API. See Backend apps below
├── frontend/            # SvelteKit web app. See Frontend below
├── mobile/              # Flutter app. See Mobile below
├── docs/                # This documentation site (MkDocs Material)
├── docker/              # Docker-specific config: docker/postgres/init-rls-user.sql (creates the
│                        #   non-superuser RLS role) and docker/backend/entrypoint.sh. That's the
│                        #   whole directory, no Redis config lives here
├── mkdocs.yml           # Docs site config and nav
├── docker-compose.yml   # Full local stack. See Self-hosting → Docker
├── CONTRIBUTING.md      # The short version of this Contributing section
├── RLS_SETUP.md         # Stubbed pointer to PostgreSQL and RLS, kept only so links made before
│                        #   this documentation site existed still resolve; not a setup guide
│                        #   itself anymore
└── schema.yml           # Generated OpenAPI schema (drf-spectacular), not hand-maintained
```

`docs/` also holds internal specs and plans under `docs/superpowers/` and `docs/design/`. These are
excluded from the built site (`exclude_docs` in `mkdocs.yml`) and are not part of the published
documentation.

## Backend apps

`backend/crm/settings.py`'s `INSTALLED_APPS` lists the project's Django apps in this order (minus
Django/DRF/third-party entries):

| App | Owns |
|---|---|
| `common` | `User`/`Org`/`Profile` models, the RLS configuration, permission classes, every authentication path (JWT, personal access tokens, org API keys), notifications, tags, teams, custom fields, documents, and vertical packs |
| `accounts` | Account (company/customer) records |
| `cases` | Support tickets: `Case`, SLAs, CSAT, escalation/routing, inbound email |
| `contacts` | Contact (person) records |
| `leads` | Leads, lead pipelines/stages, lead-to-account conversion |
| `opportunity` | The sales pipeline: `Opportunity`, line items, stage aging, sales goals/quotas |
| `tasks` | Task management and Kanban boards (`Board`/`BoardColumn`/`BoardTask`) |
| `invoices` | Billing (invoices, estimates, recurring invoices, products, payments), and the anonymous client-portal views |
| `orders` | Sales orders and order line items |
| `business_hours` | Per-org working-hours calendars that SLA timers honor |
| `macros` | Canned responses / saved replies |

`common` is the one app every other app depends on for tenancy: it owns `BaseModel` and
`BaseOrgModel` (`common/base.py`: the abstract base classes every org-scoped model builds on, see
[Adding an org-scoped model](adding-an-org-scoped-model.md)), the tenancy middleware
(`common/middleware/get_company.py`'s `GetProfileAndOrg` and
`common/middleware/rls_context.py`'s `RequireOrgContext`), and the RLS utilities
(`common/rls/__init__.py`; `ORG_SCOPED_TABLES`, `get_enable_policy_sql`, and the rest of the SQL
generators). See [Architecture overview](../architecture/overview.md#backend-layout) for how these
pieces run together on a request, and [Multi-tenancy and RLS](../architecture/multi-tenancy-and-rls.md)
for the tenancy model itself.

Each domain app follows a similar internal shape: `models.py` (or a `models/` package for larger
apps), `serializer.py`, one or more view modules, `migrations/`, and `tests/`. `common` is larger and
less uniform than the others because it also holds cross-cutting views. The dashboard, global
search, tag usage counts. That pull in models from every domain app; see
[Architecture overview](../architecture/overview.md#backend-layout) for why that one-directional
model-layer rule doesn't extend to views.

## Frontend

```
frontend/src/
├── lib/
│   ├── api.js, api-helpers.js   # API client (fetch/axios wrappers)
│   ├── components/              # Shared UI components (shadcn-svelte based)
│   ├── server/                  # Server-side load-function helpers
│   ├── shell/                   # App shell (nav, layout chrome)
│   ├── stores/                  # Svelte stores
│   └── v2/                      # Shared v2 design-system pieces (components, styles, formatters)
└── routes/
    ├── (app)/         # Authenticated routes, leads, accounts, contacts, opportunities
    │                  #   (as "pipeline"), tasks, tickets ("support"), invoices, and more
    ├── (no-layout)/   # Public routes, login and the rest of the pre-auth flow
    └── api/           # SvelteKit server routes (not the Django API)
```

Every page under `routes/(app)/` reads and writes the Django API described in the rest of this
site. There is no separate frontend-only data model.

## Mobile

```
mobile/lib/
├── config/     # API base URL and other compile-time configuration
├── core/       # Cross-cutting utilities
├── data/       # Data layer
├── providers/  # State management
├── routes/     # App routing
├── screens/    # UI screens
├── services/   # API and auth service classes
├── widgets/    # Shared widgets
└── main.dart   # Entry point
```

See [Build and configure](../mobile/build-and-configure.md) for how this connects to a backend, and
[Release builds](../mobile/release-builds.md) for producing a signed build.
