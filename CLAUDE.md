# CLAUDE.md

BottleCRM community edition, a multi-tenant CRM. `backend/` is a Django 6.1 + DRF API managed with uv and published to PyPI as `django-crm`. `frontend/` is SvelteKit 3 with Svelte 5 runes, Tailwind 4, shadcn-svelte and pnpm. `mobile/` is a Flutter app with its own `mobile/CLAUDE.md`. Both clients use the same API. Tenants are isolated by PostgreSQL row-level security underneath explicit ORM filters.

## Security first

This is a production multi-tenant app under active attack. The two targets are account takeover and superadmin escalation: assume every change is probed for a way to act as another user, read another org's data, or reach `is_superuser`. Full rules: `docs/contributing/security-rules.md`.

- **The backend is the only trust boundary.** Web and mobile validation are UX; every rule must also live in the DRF serializer or view.
- **Identity, org and role are server-derived** from `request.profile` and the JWT, never the request body. Login, OAuth, JWT claims, token refresh and rotation, email or password change, invitations, membership and role assignment are high-risk by default.
- **Every view gets `permission_classes = (IsAuthenticated, HasOrgContext)`** plus its object or role check. When you touch a check, prove it can return both true and false, with a test for each: comparing mismatched types makes a check silently always-false.
- **Scope every query by org**, then check visibility (see Reuse below), and pass `org=` on `create()` and `serializer.save()`. RLS is the safety net, not the contract.
- **Server-owned fields** (`org`, `created_by`, `profile`, publish flags) are `read_only=True` or popped before save. State transitions validate the source state, not just the target.
- Check by name for: org auto-join by email domain, IDOR on detail and nested routes, mass assignment, refresh tokens surviving a privilege change, SSRF, path traversal, stored-markdown XSS, and secrets or another tenant's data in responses and logs.
- **Never weaken a protection** (RLS policy, permission class, org filter, validator, CSRF or auth check) to make something work: surface it and ask. Flag vulnerabilities you notice, but never in a public issue, PR or commit message: they are reported as `SECURITY.md` describes.

## House rules

- **Web and mobile ship together.** A user-facing change reaches `frontend/src/` and `mobile/lib/` in the same pass, whichever side it starts on. If one half genuinely cannot ship, add a row to the Backlog in `mobile/docs/PARITY.md` and say so. Parity covers behaviour too: validators, status sets, role gates, filter params, currency and timezone rules. Change one client, grep the other.
- **Mobile first.** A web page is done when it works at 390px: no horizontal scroll, no stranded action, tap targets about 44px. `frontend/src/lib/v2/styles/v2.css` turns `.v2-table` rows into cards below 768px (refined per cell with `data-m`: `title`, `meta`, `lead`, `tag`, `bar`, `hide`) and supplies `.v2-tabbar` and `.v2-fab`. Bespoke markup opts out of all of it. 768px is the phone breakpoint; other one-off values in route files are drift.
- **Bump the version with the change.** `version` in `backend/pyproject.toml` is the only version, and `backend/uv.lock` repeats it on its `django-crm` line. Feature or endpoint: minor. Fix, docs or packaging: patch. Major only for a REST break or a migration that cannot be applied forward. A frontend change bumps too, since every release publishes `ghcr.io/django-crm/bottlecrm-frontend:<version>`; a mobile-only change does not. See `docs/contributing/releasing.md`.
- **A new Django app is two edits**: `INSTALLED_APPS` and the hatch `packages`/`include` lists in `backend/pyproject.toml`. A missing entry imports fine from a checkout and fails after `pip install`; `common/tests/test_packaging.py` catches the drift.
- **Build what was asked, and reuse before adding.** No config knob or abstraction without a second real caller. A feature is done when its failure paths, malformed input and wrong-role caller are tested. When you fix a block, check its other branches; no dead code, and no docstring describing behaviour the code lacks.
- **Comment sparingly.** Comment only what the code cannot say: a non-obvious reason, a workaround, a subtle invariant, a deliberate departure from the obvious approach. Never narrate what it does. Two or three lines, five at most; a longer reason belongs in a docstring or `docs/`, with a one-line pointer. State a fact once, where a reader meets it first. Much of this code predates the rule, so the file you are editing is not the standard. This overrides matching the surrounding comment density.
- **No em dashes** in anything: code, comments, docstrings, UI copy, DRF error strings, docs, test names, seed data. Rewrite with a comma, colon, parentheses or two sentences; an en dash or spaced hyphen in the same role is not a fix. A bare `'—'` rendered as an empty-value placeholder is a glyph and stays.
- **Agents do not commit, stage or push.** Leave changes unstaged for a human to review.

## Reuse before writing

Backend:

- Admin: `common.permissions.is_org_admin(profile)`. Never compare `role` yourself. Permission classes `HasOrgContext`, `IsOrgAdmin` and `IsSuperAdmin` live in the same module.
- One record: `common.lookups.get_scoped_or_404(model, pk, org)` (404 for missing, cross-tenant and malformed ids); a comment or attachment on a visible parent: `get_on_visible_record_or_404`. Visibility rules live in each module's `access.py` (`visible_leads_qs`, `visible_cases_qs`, `has_*_access`, `may_delete_*`).
- Routes use `<uid:pk>` (`common.converters.UUIDLikeConverter`), never `<uuid:pk>` or `<str:pk>`. Query params and payload ids go through `common.validators` (`uuid_param`, `uuid_list_param`, `payload_id_list`, `date_param`, `decimal_param`, `choice_list_param`).
- RLS: `common.tasks.set_rls_context` and `clear_rls_context` (pair them in `finally`); `get_enable_policy_sql` and `ORG_SCOPED_TABLES` in `common/rls/__init__.py`.
- Uploads: `common.utils.validate_attachment` before the first write, then `create_attachment`.
- Money: `common.money` (`org_currency`, `currency_block`, which never adds two currencies). Time: `common.org_time` (`org_timezone`, `activate_org_timezone`). Links in emails: `common.links.frontend_url` and `api_url`. Audit: `common.audit_log.audit_log`. Custom fields: `common.custom_fields.validate_payload`.
- Test fixtures: `common.testing` (`org_a`, `org_b`, `admin_client`, `user_client`, `set_rls_context`, ...), re-exported by `conftest.py`.

Frontend:

- Formatting: `#lib/v2/format.js` (`money(n, currency)`, which defaults to USD, so pass `data.org.currency`; `shortDate`, `longDate`, `relativeTime`). The org's "today": `todayIn(tz)` from `#lib/v2/dates.js` with `data.org.timezone`.
- Admin: `isOrgAdmin` from `#lib/admin.js`. Labels and tones: `#lib/v2/enums.js`. Classes: `cn` from `#lib/utils.js`. DRF errors to a sentence: `readableError` from `#lib/server/v2/form-errors.js`.
- Lists and filters: `#lib/v2/filters.js`, `#lib/server/v2/filter-params.js`, `#lib/server/v2/list-queries.js`, `#lib/server/v2/saved-views.js`. Custom fields: `#lib/server/v2/custom-fields.js`. @mentions: `MentionTextarea` and `MentionBody` in `#lib/v2/components/`, fed by `mentionPeople()` from `#lib/v2/mentions.js`.
- Components: `#lib/v2/components/<Name>.svelte` (`PageHeader`, `Pill`, `EmptyState`, `StatCard`, `ConfirmAction`, `FilterBar`, ...). Many shadcn components in `components/ui/` and everything in `components/layout`, `components/dashboard` and `components/users` have no importers. Find a live caller before building on any of them.

## Commands

```bash
# backend/
uv sync
uv run python manage.py migrate
uv run python manage.py runserver                           # :8000
uv run celery -A crm worker --loglevel=INFO
uv run pytest leads/tests/test_leads_kanban.py --no-cov     # one file (preferred)
uv run pytest --no-cov -x                                   # whole suite, in-memory SQLite
DJANGO_SETTINGS_MODULE=crm.test_settings_postgres DBUSER=<non-superuser role> \
  uv run pytest --no-cov -m postgres_only                   # RLS tests; DB* env vars as in CI
uv run ruff check . && uv run ruff format .                 # ruff only: no black, no isort
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py manage_rls --status                 # also --verify-user, --test

# frontend/
pnpm install
pnpm run dev                                                # :5181
pnpm test                                                   # vitest
pnpm run check                                              # svelte-kit sync + svelte-check
pnpm run lint                                               # prettier --check + eslint
pnpm run format

docker compose up --build                                   # full stack, from the repo root
```

CI (`.github/workflows/tests.yml`) blocks on `makemigrations --check`, `ruff check`, `ruff format --check`, pytest on SQLite and on Postgres, the `postgres_only` tests as a non-superuser role, a wheel install check, `eslint`, `pnpm check`, `pnpm test`, `pnpm build` and `mkdocs --strict`. Prettier only warns. Nothing runs for mobile. Markers, the Postgres role and the three CI runs: `docs/contributing/testing.md`.

## Gotchas

Backend:

- **`created_by` is a `User` FK; `assigned_to` holds `Profile`s.** Compare `profile.user_id == obj.created_by_id`. Mixing the two is how permission checks went silently dead.
- **`BaseModel.save` stamps `created_by`/`updated_by`** from the request user inside a request and keeps caller values outside one.
- **`ATOMIC_REQUESTS` is off**: validate everything, uploads included, before the first write.
- **`Task`, `Comment` and `Attachments` call `full_clean()` in `save()`**, so a model `ValidationError` arrives as a 500 unless the serializer checks first. `Case.clean()` never runs on save.
- **`Meta.ordering` leaks into `DISTINCT` and `GROUP BY`**: call `.order_by()` before `.distinct()` or `.values().annotate()`.
- **A `read_only` field is dropped silently**: the write returns 200 and nothing changes. Privilege fields turn read-only for callers who may not grant them.
- **The detail route carries comments and attachments.** `/api/<module>/<uid:pk>/` takes GET (record plus comments and attachments), POST (adds a comment or attachment), PUT, PATCH and DELETE. `/comment/<uid:pk>/` is PUT, PATCH, DELETE by comment id; `/attachment/<uid:pk>/` is DELETE only. Deals are `/api/opportunities/`. Swagger: `/swagger-ui/`.
- **SQLite tests cannot see RLS**: `crm.test_settings` is in-memory SQLite, where the RLS helpers do nothing. Tenant isolation needs a `postgres_only` test.
- **Most core models predate `BaseOrgModel`** and declare their own `org` FK. A new org-scoped model inherits `BaseOrgModel`, joins `ORG_SCOPED_TABLES` and gets an RLS migration; follow `docs/contributing/adding-an-org-scoped-model.md`.
- Celery workers have no middleware: call `set_rls_context(org_id)` before any query.

Frontend:

- **JavaScript with JSDoc, not TypeScript.** Imports use the `#lib/...` subpath with the full file (`#lib/components/ui/button/index.js`), never `$lib`. Runes only: no `export let`, `on:click`, `<slot>`, `createEventDispatcher` or `$app/stores`. There is no Zod.
- **Data loads on the server.** A route's `+page.server.js` calls `#lib/server/v2/<entity>.js`, which calls `apiRequest` from `#lib/api-helpers.js` with the cookies; writes are form actions with `use:enhance` and `fail()`. There are no `+page.js` files, because the JWT is an httpOnly cookie the browser cannot read. Browser code talks to `src/routes/api/*/+server.js` proxies or `?/action`, never to Django, and cannot import `#lib/server/*`.
- **A load's returned names are the page's contract.** `server/v2` returns `{ results, totals }` and each load renames them; a mismatch is an SSR 500 while the API answers 200, and `pnpm check` does not catch it. Load the page.
- **Forms drop values silently.** A `<select>` with no option matching the stored value submits nothing and clears it on save (use `missingOptions` from `#lib/v2/pickers.js`); an unchecked checkbox submits nothing, so send an explicit `false`.
- **There are no toasts and no toast library.** Feedback is `fail()` plus `form?.error` or `form?.message`.
- Env vars are declared in `src/env.js` and read through `$app/env/public` or `$app/env/private`. In SvelteKit 3 a string starting with `/` is a route ID: link with `resolve()` from `$app/paths`, or `asInternalPath` for a built string.
- Vitest runs in Node: it cannot compile `.svelte` or resolve `$app/*` beyond the env stubs, so a testable module imports neither. Tests sit beside the code as `*.test.js`; run them from `frontend/`.
- Never log a raw axios error in `hooks.server.js`, since it carries the tokens: use `describeError`. `/help` (the signed-in user's tickets) is not `/help-center` (public) and stays out of `PUBLIC_ROUTES`.

## Checking a page in the browser

1. `cd backend && uv run python manage.py devlogin <email> --org MicroPyramid`. It only runs with `DEBUG=True`. With seeded data, `<email>` is `seed_data`'s default `--email`. It prints both tokens and a devtools snippet.
2. Open the app and run the snippet in the console (or `evaluate_script`). It sets the `jwt_access`, `jwt_refresh` and `org` cookies that `hooks.server.js` reads, then reloads. Tokens in `localStorage` alone still redirect to `/login`.
3. `/` is the dashboard; there is no `/dashboard` route. Check narrow layouts with device emulation at 390px, since a resized window may not go below about 500px.

`--org` takes an id or a name, and the user needs an active profile in that org (`seed_data` creates one).
