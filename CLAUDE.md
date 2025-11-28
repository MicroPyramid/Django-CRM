# CLAUDE.md

BottleCRM is a SaaS CRM platform: Django REST API backend (`backend/`) + SvelteKit frontend (`frontend/`).

## Quick Reference

```bash
# Backend
cd backend && source venv/bin/activate && python manage.py runserver
cd backend && source venv/bin/activate && celery -A crm worker --loglevel=INFO

# Frontend
cd frontend && pnpm run dev
```

**API Docs**: http://localhost:8000/swagger-ui/

## Tech Stack

**Backend**: Django 5.x, DRF, PostgreSQL, Redis/Celery, JWT auth, AWS S3/SES
**Frontend**: SvelteKit, Svelte 5 (runes), TailwindCSS, shadcn-svelte, Zod, Axios, Lucide icons

## Multi-Tenancy & RLS (CRITICAL)

Every request operates within an organization context. RLS provides database-level isolation, but **always filter at ORM level too** (defense-in-depth).

### Required Patterns

```python
# ALWAYS filter by org - never use .all() on org-scoped models
queryset = Model.objects.filter(org=request.profile.org)

# ALWAYS include org in get_object
def get_object(self, pk):
    return get_object_or_404(Lead, id=pk, org=self.request.profile.org)

# ALWAYS set org when creating
obj = Model.objects.create(name="Example", org=request.profile.org)
serializer.save(org=request.profile.org)
```

### RLS-Protected Tables (24)

`lead`, `accounts`, `contacts`, `opportunity`, `case`, `task`, `invoice`, `comment`, `attachments`, `document`, `teams`, `activity`, `tags`, `address`, `solution`, `board`, `board_column`, `board_task`, `board_member`, `apiSettings`, `account_email`, `emailLogs`, `invoice_history`, `security_audit_log`

### Adding New Org-Scoped Models

1. Inherit from `BaseOrgModel` (includes org field automatically)
2. Add table to `ORG_SCOPED_TABLES` in `common/rls/__init__.py`
3. Create RLS migration using `get_enable_policy_sql('table_name')`
4. Always filter by org in views

### Celery Tasks

```python
from common.tasks import set_rls_context

@app.task
def my_task(data_id, org_id):
    set_rls_context(org_id)  # REQUIRED before any query
    obj = MyModel.objects.get(id=data_id)
```

### RLS Commands

```bash
python manage.py manage_rls --status      # Check status
python manage.py manage_rls --verify-user # Verify non-superuser (superusers bypass RLS!)
python manage.py manage_rls --test        # Test isolation
```

## Architecture

### User Model

User → Profile → Org (one user can have profiles in multiple orgs)
- Profile includes: role (ADMIN/USER), sales/marketing access flags
- Super Admin: @micropyramid.com email domain

### BaseModel (`common/base.py`)

All models inherit from `BaseModel`: UUID PKs, timestamps (`created_at`, `updated_at`), audit (`created_by`, `updated_by`)

### AssignableMixin

For models with team/user assignment: Account, Lead, Contact, Opportunity, Case, Task

### Django Apps

- `common` - User, Profile, Org, Teams, Tags, Comment, Attachments, Document, Activity
- `accounts`, `leads`, `contacts`, `opportunity`, `cases`, `tasks`, `invoices`, `marketing`

### API Pattern

```
GET/POST       /api/<module>/                 # List/Create
GET/PUT/DELETE /api/<module>/<pk>/            # Detail/Update/Delete
GET/POST       /api/<module>/comment/<pk>/    # Comments
GET/POST       /api/<module>/attachment/<pk>/ # Attachments
```

### Celery Tasks (`common/tasks.py`)

Email tasks: `send_email_to_new_user`, `send_email_user_mentions`, `send_email_user_status`, `send_email_user_delete`, `send_email_to_reset_password`
Team tasks: `remove_users`, `update_team_users`

## Frontend

### Structure

- `src/routes/(app)/` - Main CRM (authenticated)
- `src/routes/(admin)/` - Super admin panel
- `src/routes/(site)/` - Public marketing site
- `src/routes/(no-layout)/` - Auth pages
- `src/lib/` - Components and utilities

### Key Files

- `src/hooks.server.js` - Auth, org validation, route protection
- `src/lib/stores/auth.js` - Auth state

### Standards

- **Svelte 5**: Use runes (`$state`, `$derived`, `$effect`)
- **NO TypeScript**: JavaScript with JSDoc annotations only
- **Validation**: Zod for forms
- **Icons**: Lucide Svelte

```bash
pnpm run check   # Type check via JSDoc
pnpm run lint    # Lint
pnpm run format  # Format
```

## Testing

```bash
# Backend
cd backend && pytest && black . && isort .

# Frontend
cd frontend && pnpm run check && pnpm run lint
```

## Related Docs

- `QUICKSTART.md` - Setup guide
