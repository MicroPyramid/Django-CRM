# BottleCRM

BottleCRM is a multi-tenant CRM covering leads, accounts, contacts, opportunities, support
tickets (cases), tasks and invoices.

## What BottleCRM is

BottleCRM is MIT licensed and self-hosted: you run it on your own infrastructure, there are no
per-seat limits, and there is no feature paywall.

## How it fits together

Three clients (a SvelteKit web app, a Flutter mobile app, and the REST API) share one Django
REST Framework backend. Tenant isolation is enforced by PostgreSQL Row-Level Security keyed on
the `app.current_org` session variable, not by application code alone: application middleware
sets that variable from the authenticated user's JWT on every request, and the database enforces
it independently of the ORM's own org filters.

## Where to start

- **Operators**, deploying and running BottleCRM: [Docker quick start](getting-started/docker-quick-start.md)
- **Integrators**, building against the REST API: [Conventions](api/conventions.md)
- **Contributors**, working on the BottleCRM codebase: [Development setup](contributing/development-setup.md)
