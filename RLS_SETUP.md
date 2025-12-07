# PostgreSQL Row-Level Security (RLS) Setup Guide

This guide explains how to set up PostgreSQL with Row-Level Security for BottleCRM multi-tenancy.

## Overview

RLS provides database-level tenant isolation. Every query automatically filters by organization, ensuring data protection even if application code misses a filter.

**Key Points:**
- RLS uses PostgreSQL session variable `app.current_org` to identify the current tenant
- **Superusers bypass RLS** - the application must use a non-superuser database account
- 24 tables are RLS-protected (see list below)

---

## 1. Create PostgreSQL Database

```sql
-- Connect as postgres superuser
sudo -u postgres psql

-- Create the database
CREATE DATABASE bottlecrm;
```

---

## 2. Create Application User (Non-Superuser)

**CRITICAL:** The application user must NOT be a superuser, otherwise RLS is completely bypassed.

```sql
-- Connect as postgres superuser
sudo -u postgres psql

-- Create non-superuser for the application
CREATE USER crm_user WITH PASSWORD 'crm_password';

-- Verify user is NOT a superuser
SELECT usename, usesuper FROM pg_user WHERE usename = 'crm_user';
-- Should show: crm_user | f
```

---

## 3. Grant Database Permissions

```sql
-- Connect to bottlecrm database
\c bottlecrm

-- Grant connection rights
GRANT CONNECT ON DATABASE bottlecrm TO crm_user;

-- Grant schema privileges (required for migrations to create/alter tables)
GRANT ALL ON SCHEMA public TO crm_user;

-- Grant table permissions (SELECT, INSERT, UPDATE, DELETE)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO crm_user;

-- Grant sequence permissions (for auto-increment fields)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO crm_user;

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO crm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO crm_user;
```

> **Note:** Granting schema/table privileges does NOT weaken RLS. These control DDL operations (CREATE/ALTER/DROP), while RLS controls row-level access. Only `BYPASSRLS` attribute or superuser status bypasses RLS.

---

## 4. Configure Django Environment

Set these environment variables for Django:

```bash
export DBNAME=bottlecrm
export DBUSER=crm_user
export DBPASSWORD=crm_password
export DBHOST=localhost
export DBPORT=5432
```

Or in your `.env` file:

```env
DBNAME=bottlecrm
DBUSER=crm_user
DBPASSWORD=crm_password
DBHOST=localhost
DBPORT=5432
```

---

## 5. Run Migrations

Migrations automatically enable RLS on all protected tables:

```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

---

## 6. Verify RLS Setup

### Check RLS Status

```bash
python manage.py manage_rls --status
```

Expected output:
```
RLS Status:

  Database user "crm_user" is not a superuser - RLS will be enforced

  lead: ENABLED (forced)
  accounts: ENABLED (forced)
  contacts: ENABLED (forced)
  ...

  Enabled: 24, Disabled: 0
```

### Verify User is Not Superuser

```bash
python manage.py manage_rls --verify-user
```

Expected output:
```
Verifying database user...
  Current user: crm_user
  Is superuser: False
  Can create DB: False
Database user is properly configured for RLS
```

### Test RLS Isolation

```bash
python manage.py manage_rls --test
```

This tests that:
- Data is visible with correct org context
- Data is isolated between organizations
- No data is returned without context (fail-safe)

---

## 7. RLS-Protected Tables (24)

| Category | Tables |
|----------|--------|
| Core Business | `lead`, `accounts`, `contacts`, `opportunity`, `case`, `task`, `invoice` |
| Supporting | `comment`, `commentFiles`, `attachments`, `document`, `teams`, `activity`, `tags`, `address`, `solution` |
| Boards (Kanban) | `board`, `board_column`, `board_task`, `board_member` |
| Settings/Email | `apiSettings`, `account_email`, `emailLogs`, `invoice_history` |
| Security | `security_audit_log` |

---

## 8. Production Checklist

- [ ] Application database user is NOT a superuser
- [ ] All 24 tables show RLS ENABLED (forced)
- [ ] `manage_rls --test` passes
- [ ] `manage_rls --verify-user` confirms non-superuser
- [ ] Environment variables are securely stored (not in version control)

---

## Troubleshooting

### "RLS will be bypassed" Warning

The database user is a superuser. Create a non-superuser as shown in Step 2.

### Tables Show "disabled"

Run migrations again or check if the table has an `org_id` column:

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'your_table' AND column_name = 'org_id';
```

### Data Visible Without Context

If `manage_rls --test` shows data without context, the RLS policies may need updating:

```bash
python manage.py migrate common
```

### Permission Denied Errors

Grant permissions again (Step 3), especially after creating new tables:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO crm_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO crm_user;
```

---

## How RLS Works

### Session Context

Each request sets the org context via middleware:

```sql
SELECT set_config('app.current_org', '<org_uuid>', true);
```

### Policy Definition

Each table has two policies:

1. **Isolation Policy** (SELECT/UPDATE/DELETE):
   ```sql
   CREATE POLICY org_isolation ON "lead"
       FOR ALL
       USING (org_id::text = NULLIF(current_setting('app.current_org', true), ''));
   ```

2. **Insert Check Policy**:
   ```sql
   CREATE POLICY org_insert_check ON "lead"
       FOR INSERT
       WITH CHECK (org_id::text = NULLIF(current_setting('app.current_org', true), ''));
   ```

The `NULLIF(..., '')` ensures **no rows are returned** when context is not set (fail-safe).

### Force RLS

```sql
ALTER TABLE "lead" FORCE ROW LEVEL SECURITY;
```

This ensures RLS applies even to the table owner.

---

## Adding RLS to New Tables

1. Inherit from `BaseOrgModel` in your model
2. Add table name to `ORG_SCOPED_TABLES` in `common/rls/__init__.py`
3. Create migration:

```python
from django.db import migrations
from common.rls import get_enable_policy_sql

def enable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(get_enable_policy_sql('your_table_name'))

class Migration(migrations.Migration):
    dependencies = [...]
    operations = [
        migrations.RunPython(enable_rls, migrations.RunPython.noop),
    ]
```

---

## Celery Tasks

Background tasks don't go through middleware, so you must set context manually:

```python
from common.tasks import set_rls_context

@app.task
def my_task(data_id, org_id):
    set_rls_context(org_id)  # REQUIRED before any query
    obj = MyModel.objects.get(id=data_id)
```

---

## Quick Reference

```bash
# Check RLS status
python manage.py manage_rls --status

# Verify non-superuser
python manage.py manage_rls --verify-user

# Test isolation
python manage.py manage_rls --test
```
