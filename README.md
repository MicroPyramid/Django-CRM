# BottleCRM — Open Source Django CRM for Startups & Enterprises

A free, self-hosted, multi-tenant CRM built with Django REST Framework, SvelteKit and Flutter.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![Django](https://img.shields.io/badge/django-6.x-green.svg)
![SvelteKit](https://img.shields.io/badge/sveltekit-2.x-orange.svg)
![Svelte](https://img.shields.io/badge/svelte-5-orange.svg)
![Flutter](https://img.shields.io/badge/flutter-3.8+-blue.svg)
![Coverage](./coverage-badge.svg)

**BottleCRM is an open source CRM you run on your own infrastructure.** It covers the full
customer lifecycle — leads, accounts, contacts, opportunities, support tickets, tasks and
invoices — through a SvelteKit web app, a native Flutter mobile app, and a documented REST API
sharing one Django backend. PostgreSQL Row-Level Security isolates each organization's data at
the database layer, so a single deployment serves one startup or hundreds of tenants.

No per-seat pricing, no user caps, no feature paywall. MIT licensed — fork it, self-host it, own
your data.

**[Try it free →](https://bottlecrm.io/)** · [Features](https://bottlecrm.io/features) · [Docs](https://bottlecrm.io/docs) · [Pricing](https://bottlecrm.io/pricing) · [Migrate from Salesforce or HubSpot](https://bottlecrm.io/migration)

## Why BottleCRM

- **Free forever, MIT licensed** — unlimited users and records, no subscription. A genuinely
  self-hosted CRM alternative to Salesforce, HubSpot and Pipedrive.
- **Multi-tenant by design** — PostgreSQL Row-Level Security enforces tenant isolation in the
  database, not just in application code. Run it for a single company or as a SaaS for many.
- **AI agents built in (MCP)** — connect Claude, Cursor, Codex, Gemini or any MCP client and let
  it search, create and update records *as you*, inheriting your role, org and permissions.
- **Web, native mobile and API** — one Django REST backend behind a Svelte 5 web app and a
  Flutter app for iOS and Android.
- **A stack you can actually hack on** — Django 6 / DRF and Svelte 5, not a bespoke in-house
  framework. If your team writes Python, it can extend this on day one.
- **Real support tooling** — a full helpdesk with SLA timers, approvals, escalations, macros and
  a knowledge base, not a bolted-on ticket list.

## How it compares

| | BottleCRM | SaaS CRM (Salesforce, HubSpot) | Typical open source CRM |
|---|---|---|---|
| **Cost** | Free, unlimited users | Per seat, per month | Free core, often paid tiers |
| **Hosting** | Self-hosted (managed hosting available) | Vendor cloud only | Self-hosted |
| **Data ownership** | Total — it is your database | Vendor-controlled | Total |
| **Multi-tenancy** | Database-level RLS | Not applicable | Uncommon |
| **Native mobile app** | Yes — Flutter, iOS + Android | Yes | Uncommon |
| **AI agent access** | Built-in MCP server | Proprietary add-ons | Uncommon |
| **Stack** | Django REST + SvelteKit | Closed source | Varies |
| **License** | MIT | Proprietary | Varies, often GPL/AGPL |

## Features

### Core CRM Modules
- **[Leads](https://bottlecrm.io/features/lead-management)** - Capture, score and convert sales leads through your pipeline
- **[Accounts](https://bottlecrm.io/features/account-management)** - Manage company/organization records
- **[Contacts](https://bottlecrm.io/features/contact-management)** - Store and organize contact information
- **[Opportunities](https://bottlecrm.io/features/sales-pipeline)** - Visual sales pipeline for deals and forecasting
- **[Tickets & Cases](https://bottlecrm.io/features/ticket-management)** - Helpdesk with SLA tracking, approvals, escalations, macros and a knowledge base
- **[Tasks](https://bottlecrm.io/features/tasks)** - Task management with calendar and Kanban board views
- **[Invoices](https://bottlecrm.io/features/invoices)** - Estimates, recurring invoices and online payments

### AI & Integrations
- **AI Agents (MCP)** - Built-in [Model Context Protocol](https://modelcontextprotocol.io) server (`mcp_server/`) lets Claude, Cursor, Codex, Gemini and any MCP client search, create and update records via a personal access token — acting as you, with your role and permissions. See [`mcp_server/README.md`](mcp_server/README.md).
- **REST API** - Every feature is API-first and documented via OpenAPI/Swagger
- **Email Integration** - AWS SES integration for transactional emails

### Platform Features
- **[Native Mobile App](https://bottlecrm.io/features/mobile-app)** - Flutter app for iOS and Android covering leads, deals, tickets, tasks, goals and timesheets
- **Multi-Tenant Architecture** - PostgreSQL Row-Level Security keeps each organization's CRM data isolated
- **JWT Authentication** - Secure token-based authentication
- **Team Management** - Organize users into teams with role-based access
- **Activity Tracking** - Comprehensive audit logs and activity history
- **Comments & Attachments** - Collaborate with comments and file attachments on any record
- **Tags** - Flexible tagging system for organizing records
- **Background Tasks** - Celery + Redis for async task processing

### Built for your industry
Pre-configured setups for [professional services and agencies](https://bottlecrm.io/industries/professional-services-crm), [education and admissions](https://bottlecrm.io/industries/education-admissions-crm), and [real estate](https://bottlecrm.io/industries/real-estate-crm).

## Tech Stack

### Backend
- **Django 6.x** with Django REST Framework
- **PostgreSQL** for relational data storage
- **Redis** for caching and Celery broker
- **Celery** for background task processing
- **JWT** for authentication
- **AWS S3** for file storage
- **AWS SES** for email delivery

### Frontend
- **SvelteKit 2.x** with Svelte 5 (runes)
- **TailwindCSS 4** for styling
- **shadcn-svelte** UI components
- **Axios** for API communication
- **Lucide** icons

### Mobile
- **Flutter 3.8+** targeting iOS and Android
- **Material Design 3** with a flat, custom design system
- **Google Sign-In** + JWT against the same backend API

### AI
- **MCP server** (`bcrm-mcp`) built on FastMCP, stdio and HTTP transports

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 24 with pnpm 10
- PostgreSQL 14+
- Redis
- Flutter 3.8+ (only if you're building the mobile app)

### Backend Setup

The backend uses [`uv`](https://docs.astral.sh/uv/) for Python dependency management — it reads `pyproject.toml`, installs from `uv.lock`, and creates the virtual environment for you. Backend configuration starts from [`backend/.env.example`](backend/.env.example).

```bash
# Clone the repository
git clone https://github.com/Django-CRM/Django-CRM.git
cd Django-CRM/backend

# Install uv (one time, system-wide)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on macOS via Homebrew: brew install uv

# Install Python (matches the version in .python-version) and all deps into .venv/
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your database and other settings

# Run migrations
uv run python manage.py migrate

# Create a superuser
uv run python manage.py createsuperuser

# Start the development server
uv run python manage.py runserver
```

`uv run <cmd>` resolves binaries from `.venv/bin/` automatically — no need to `source .venv/bin/activate`. If you prefer the activate-then-run flow, that still works:

```bash
source .venv/bin/activate
python manage.py runserver   # equivalent to `uv run python manage.py runserver`
```

Common dev commands (from `backend/`):

```bash
uv run pytest                                # run tests
uv run python manage.py makemigrations       # create migrations
uv run celery -A crm worker --loglevel=INFO  # background worker
uv add <package>                             # add a dependency (updates pyproject.toml + uv.lock)
uv add --group dev <package>                 # add a dev-only dependency
uv lock --upgrade                            # refresh the lockfile
```

### Frontend Setup

```bash
# In a new terminal, from the project root
cd frontend

# Install dependencies
pnpm install

# Start the development server
pnpm run dev
```

### Mobile Setup (optional)

```bash
# In a new terminal, from the project root
cd mobile

flutter pub get
flutter run          # against a running backend on :8000
```

See [`mobile/README.md`](mobile/README.md) for emulator setup and release builds.

### Start Celery Worker

```bash
# In a new terminal
cd backend
uv run celery -A crm worker --loglevel=INFO
```

### Access the Application
- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/swagger-ui/
- **Admin Panel**: http://localhost:8000/admin/

### Connect your AI agent (MCP)

Let Claude, Cursor, Codex, Gemini, or any MCP client work in your CRM:

1. In the app, go to **Settings → API Tokens** and create a personal access token (shown once).
2. Register the `bcrm-mcp` server in your AI client, passing `BCRM_BASE_URL` (your API host, e.g. `http://localhost:8000`) and `BCRM_TOKEN` (the token). The token page shows ready-to-paste config for each client.
3. Restart the client and start asking.

The agent authenticates **as you** and inherits your role, org and RLS scope — it can't see or do anything you can't. Full setup, the tool list, and the security model are in [`mcp_server/README.md`](mcp_server/README.md).

## Docker Setup

Run the full stack (backend, frontend, PostgreSQL, Redis, Celery) with a single command:

```bash
# Start all services (first run will build images)
# An admin user (admin@localhost / admin) is created automatically
docker compose up --build

# (Optional) Load sample data
docker compose exec backend python manage.py seed_data --email admin@example.com
```

Once running:
- **Frontend**: http://localhost:5173
- **API / Swagger**: http://localhost:8000/swagger-ui/
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Daily workflow

```bash
docker compose up           # start all services (code changes auto-reload)
docker compose down         # stop all services
docker compose down -v      # stop and delete all data (full reset)
```

### Running commands inside containers

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python -m pytest
docker compose exec backend python manage.py manage_rls --status
```

### Custom environment overrides

The default env vars live in `.env.docker` (committed). To override locally without touching git:

1. Copy `.env.docker` to `.env.docker.local` (gitignored)
2. Edit values as needed — set your own `SECRET_KEY` here, not in `.env.docker`
3. Rebuild/restart: `docker compose up --build`

Every service loads `.env.docker` first and then `.env.docker.local` if it exists, so
your overrides win. No edits to `docker-compose.yml` are needed.

## Project Structure

```
Django-CRM/
├── backend/                 # Django REST API
│   ├── accounts/           # Accounts module
│   ├── cases/              # Cases module
│   ├── common/             # Shared models, utilities, RLS
│   ├── contacts/           # Contacts module
│   ├── invoices/           # Invoices module
│   ├── leads/              # Leads module
│   ├── opportunity/        # Opportunities module
│   ├── tasks/              # Tasks module
│   └── crm/                # Django project settings
├── frontend/               # SvelteKit frontend
│   ├── src/
│   │   ├── lib/           # Components, stores, utilities
│   │   └── routes/        # SvelteKit routes
│   │       ├── (app)/     # Authenticated app routes
│   │       └── (no-layout)/ # Auth pages (login, etc.)
│   ├── static/            # Static assets
│   └── Dockerfile         # Frontend dev container
├── mobile/                 # Flutter app (iOS + Android)
│   ├── lib/
│   │   ├── config/        # API configuration
│   │   ├── services/      # API + auth services
│   │   ├── models/        # Typed API response models
│   │   └── screens/       # Leads, deals, tickets, tasks, settings
│   ├── android/           # Android build config
│   └── ios/               # iOS build config
├── mcp_server/             # MCP server (bcrm-mcp) for AI agents
│   └── src/bcrm_mcp/      # FastMCP tools over the REST API (stdio transport)
├── docker/                 # Docker support files
│   ├── backend/
│   │   └── entrypoint.sh  # DB wait + migrate + runserver
│   └── postgres/
│       └── init-rls-user.sql # Creates non-superuser for RLS
├── Dockerfile              # Backend / Celery image
├── docker-compose.yml      # Full-stack dev environment
└── .env.docker             # Docker env vars (dev defaults)
```

## Multi-Tenancy & Security

BottleCRM isolates tenant-scoped data at both the application and the database layer. Every
org-scoped table is protected by a PostgreSQL Row-Level Security policy keyed on the
`app.current_org` session variable, which middleware sets from the authenticated user's JWT — so
a query that escapes the ORM's org filter still returns zero rows rather than another tenant's
data.

Self-hosters should follow the [Row-Level Security setup guide](RLS_SETUP.md) to configure and
verify the policies. The most important rule: **the application's database user must not be a
PostgreSQL superuser**, because superusers bypass RLS entirely. Verify with
`python manage.py manage_rls --status`.

## Development

### Testing

```bash
cd backend

# Run all tests with coverage
pytest

# Run tests without coverage (faster)
pytest --no-cov -x

# Run a specific module's tests
pytest accounts/tests/
pytest leads/tests/test_leads_kanban.py

# Run tests matching a keyword
pytest -k "test_login"

# View coverage report in browser
open htmlcov/index.html
```

### Dev login (skip the Google OAuth flow)

For local development you can mint a JWT for any user without going through Google sign-in. The command refuses to run unless `DEBUG=True`, and there's no web endpoint — it's only reachable through `manage.py`:

```bash
cd backend

# Mint tokens for an existing user (no org bound — same as the OAuth flow)
uv run python manage.py devlogin aswin.1231@gmail.com

# Bind to a specific org so you skip the orgswitch step on first load
uv run python manage.py devlogin aswin.1231@gmail.com --org "MicroPyramid"

# Create the user on the fly (random password) if they don't exist yet
uv run python manage.py devlogin newdev@example.com --create
```

The command prints the access token, the refresh token, and (with `--org`) the org's UUID, plus a
ready-to-paste `localStorage.setItem(...)` snippet.

**Note:** `localStorage` alone is not enough to sign you in. The API client reads it for direct
fetches, but SvelteKit's server-side guard (`frontend/src/hooks.server.js`) reads the
`jwt_access`, `jwt_refresh` and `org` **cookies** — without them you'll still be redirected to
`/login`. In the devtools console on `http://localhost:5173`, run the printed snippet *and*:

```js
const oneYear = 60 * 60 * 24 * 365;
document.cookie = `jwt_access=${ACCESS_TOKEN}; path=/; max-age=${oneYear}; samesite=lax`;
document.cookie = `jwt_refresh=${REFRESH_TOKEN}; path=/; max-age=${oneYear}; samesite=lax`;
document.cookie = `org=${ORG_UUID}; path=/; max-age=${oneYear}; samesite=lax`;
```

Then reload. The root route `/` is the dashboard — there is no `/dashboard` path.

### Frontend Commands

```bash
cd frontend

# Type checking
pnpm run check

# Linting
pnpm run lint

# Formatting
pnpm run format
```

### Mobile Commands

```bash
cd mobile

flutter test                      # run tests
flutter analyze --no-fatal-infos  # static analysis
dart format .                     # formatting
flutter build apk --release       # Android release build
```

## API Documentation

API routes vary by module and are documented from the generated OpenAPI schema. After starting the backend, open the [interactive Swagger UI](http://localhost:8000/swagger-ui/) to explore the available endpoints and request formats.

## FAQ

**Is BottleCRM really free?**
Yes. It's MIT licensed with unlimited users, unlimited records and no feature paywall. You only
pay if you want [managed hosting, setup or custom development](https://bottlecrm.io/pricing).

**Can I self-host it?**
That's the primary way to run it. `docker compose up --build` gives you the full stack; see
[Docker Setup](#docker-setup). Your database, your server, your data.

**Is it a good Salesforce or HubSpot alternative?**
For teams that want to own their data and avoid per-seat pricing, yes. It covers leads, pipeline,
contacts, accounts, tickets, tasks and invoicing. See the [migration guide](https://bottlecrm.io/migration)
for moving existing data across.

**Can I run it as a multi-tenant SaaS?**
Yes — multi-tenancy is built in at the database layer via PostgreSQL Row-Level Security, not
bolted on. See [Multi-Tenancy & Security](#multi-tenancy--security).

**Is there a mobile app?**
Yes, a native [Flutter app](https://bottlecrm.io/features/mobile-app) for iOS and Android sharing
the same backend API.

**Can AI agents use it?**
Yes. The bundled [MCP server](mcp_server/README.md) lets Claude, Cursor, Codex, Gemini or any MCP
client work in your CRM under your own role and permissions.

More at the [full FAQ](https://bottlecrm.io/faq).

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, development checks, and pull request guidance.

## Community

- **Issues**: [GitHub Issues](https://github.com/Django-CRM/Django-CRM/issues)
- **Twitter**: [@micropyramid](https://twitter.com/micropyramid)
- **Commercial Support**: [Contact us](https://micropyramid.com/contact/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Sponsors

We are grateful to the sponsors who support BottleCRM's continued development and maintenance.

- [MicroPyramid](https://micropyramid.com/)

We warmly welcome new sponsors. If you would like to support BottleCRM and help the project grow, please [get in touch](https://micropyramid.com/contact/).

## Contributors

This project exists thanks to all the people who contributed.

[View all BottleCRM contributors](https://github.com/Django-CRM/Django-CRM/graphs/contributors).
