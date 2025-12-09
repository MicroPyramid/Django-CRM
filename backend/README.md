# BottleCRM Backend - Django REST API

The backend for BottleCRM, a multi-tenant CRM platform built with Django REST Framework.

## Tech Stack

- **Django 4.2.1** - Web framework
- **Django REST Framework 3.14.0** - API toolkit
- **PostgreSQL** - Database (psycopg2-binary 2.9.11)
- **Celery 5.5.3** - Async task queue
- **Redis 4.6.0** - Message broker for Celery
- **djangorestframework-simplejwt 5.2.2** - JWT authentication
- **drf-spectacular 0.26.2** - OpenAPI/Swagger documentation
- **django-ses 3.5.0** - AWS SES email backend
- **Sentry SDK 1.24.0** - Error tracking

## Django Apps

| App | Description |
|-----|-------------|
| `common` | User, Organization, Profile, Comments, Attachments, Document models |
| `accounts` | Customer account management |
| `leads` | Lead tracking and conversion |
| `contacts` | Contact management |
| `opportunity` | Sales pipeline and deal tracking |
| `cases` | Customer support tickets |
| `tasks` | Task management |
| `invoices` | Invoicing system |
| `events` | Calendar events |
| `teams` | Team management |
| `emails` | Email handling |
| `planner` | Planner events |
| `boards` | Kanban board system |
| `marketing` | Newsletter and contact forms |

## Prerequisites

- **Python 3.8+**
- **PostgreSQL**
- **Redis** (for Celery)
- **virtualenv**

## Installation

### 1. Create and activate virtual environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install PDF generation system dependencies

Invoice PDF generation uses WeasyPrint (already included in requirements.txt). However, WeasyPrint requires system libraries that must be installed separately:

**Ubuntu/Debian:**
```bash
sudo apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info
```

**macOS:**
```bash
brew install pango cairo libffi gdk-pixbuf
```

**Fedora/CentOS:**
```bash
sudo dnf install -y \
    pango \
    cairo \
    gdk-pixbuf2 \
    libffi-devel
```

**Windows:**
Follow the [WeasyPrint Windows installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).

> **Note**: If you skip this step, the CRM will work but PDF download for invoices will show "PDF generation unavailable".

### 4. Configure environment variables

Create a `.env` file in the `backend/` directory:

```env
# Django
SECRET_KEY=your-secret-key-here
ENV_TYPE=dev

# Database
DBNAME=bottlecrm
DBUSER=postgres
DBPASSWORD=root
DBHOST=localhost
DBPORT=5432

# Email
DEFAULT_FROM_EMAIL=noreply@bottlecrm.com
ADMIN_EMAIL=admin@bottlecrm.com

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Domain
DOMAIN_NAME=http://localhost:8000
SWAGGER_ROOT_URL=http://localhost:8000
```

### 5. Set up database

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE bottlecrm WITH OWNER = postgres;
ALTER USER postgres WITH PASSWORD 'root';
\q

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## Running Celery

For background tasks (emails, notifications), run the Celery worker:

```bash
celery -A crm worker --loglevel=INFO
```

## API Documentation

- **Swagger UI**: http://localhost:8000/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **Django Admin**: http://localhost:8000/admin/

### Generating Schema

To generate the OpenAPI schema file:

```bash
python manage.py spectacular --file openapi.yml
```

## Architecture

### Multi-Tenancy

Every request operates within an organization context:

- **Organization (Org)**: Top-level tenant container
- **Users**: Regular members with USER role
- **Admins**: Organization administrators with ADMIN role
- **Super Admin**: Users with @micropyramid.com email domain have platform-wide access

### Authentication

JWT-based authentication:

```
Authorization: Bearer <token>
```

- Organization ID is embedded in the JWT token (not sent as header)
- Access token lifetime: 1 day
- Refresh token lifetime: 365 days

### Middleware

The middleware chain provides security:

1. **`GetProfileAndOrg`** (`common.middleware.get_company`):
   - Extracts org_id from JWT token claims (not headers - prevents spoofing)
   - Validates user has active membership in the organization
   - Sets `request.profile` and `request.org`

2. **`RequireOrgContext`** (`common.middleware.rls_context`):
   - Sets PostgreSQL session variable `app.current_org` for RLS
   - Resets context after each request

### Row-Level Security (RLS)

PostgreSQL RLS provides database-level tenant isolation as defense-in-depth.

#### How It Works

1. **Middleware sets context**: `SET app.current_org = '<org_id>'`
2. **RLS policies filter queries**: Only rows matching `org_id` are visible
3. **Fail-safe design**: Empty context returns zero rows (NULLIF pattern)

#### Protected Tables (24 total)

| Category | Tables |
|----------|--------|
| Core Business | `lead`, `accounts`, `contacts`, `opportunity`, `case`, `task`, `invoice` |
| Supporting | `comment`, `attachments`, `document`, `teams`, `activity`, `tags`, `address`, `solution` |
| Boards | `board`, `board_column`, `board_task`, `board_member` |
| Other | `apiSettings`, `account_email`, `emailLogs`, `invoice_history`, `security_audit_log` |

#### Configuration

RLS is configured in `common/rls/__init__.py`:

```python
from common.rls import RLS_CONFIG, get_enable_policy_sql

# List of protected tables
tables = RLS_CONFIG['tables']

# Enable RLS on a table
cursor.execute(get_enable_policy_sql('my_table'))
```

#### Management Commands

```bash
# Check RLS status on all tables
python manage.py manage_rls --status

# Verify database user is non-superuser (required for RLS)
python manage.py manage_rls --verify-user

# Test RLS isolation between organizations
python manage.py manage_rls --test

# Enable RLS on all configured tables
python manage.py manage_rls --enable

# Disable RLS (for debugging only)
python manage.py manage_rls --disable
```

#### Critical: Database User Setup

**PostgreSQL superusers bypass ALL RLS policies.** You must use a non-superuser:

```sql
-- Create application user
CREATE USER crm_app WITH PASSWORD 'your_secure_password';

-- Grant permissions
GRANT CONNECT ON DATABASE bottlecrm TO crm_app;
GRANT USAGE ON SCHEMA public TO crm_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO crm_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO crm_app;

-- Future tables inherit permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO crm_app;
```

Update `.env`:
```env
DBUSER=crm_app
DBPASSWORD=your_secure_password
```

#### Celery Tasks & RLS

Background tasks don't go through middleware, so set RLS context manually:

```python
from common.tasks import set_rls_context

@app.task
def my_background_task(data_id, org_id):
    set_rls_context(org_id)  # Required!
    obj = MyModel.objects.get(id=data_id)
    # ... process
```

#### Adding RLS to New Tables

1. Add table name to `ORG_SCOPED_TABLES` in `common/rls/__init__.py`
2. Create migration using `get_enable_policy_sql()`
3. Ensure model has `org = models.ForeignKey(Org, ...)`

### BaseModel Pattern

All models inherit from `BaseModel` (`common.base.BaseModel`):

- UUID primary keys (not integer IDs)
- Automatic timestamps: `created_at`, `updated_at`
- Audit trail: `created_by`, `updated_by`
- Organization isolation: `org = models.ForeignKey(Org)`

### API Endpoint Pattern

```
GET/POST       /api/<module>/              # List/Create
GET/PUT/DELETE /api/<module>/<pk>/         # Detail/Update/Delete
GET/POST       /api/<module>/comment/<pk>/ # Comments
GET/POST       /api/<module>/attachment/<pk>/ # Attachments
```

## Project Structure

```
backend/
├── manage.py
├── requirements.txt
├── crm/                    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── common/                 # Core models and utilities
│   ├── models.py           # User, Org, Profile, etc.
│   ├── base.py             # BaseModel
│   ├── middleware/
│   └── tasks.py            # Celery tasks
├── accounts/
├── leads/
├── contacts/
├── opportunity/
├── cases/
├── tasks/
├── invoices/
├── events/
├── teams/
├── emails/
├── planner/
├── boards/
├── marketing/
├── templates/
└── static/
```

## Development

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Run tests
pytest
```

### Creating a New App

1. Create the app:
   ```bash
   python manage.py startapp myapp
   ```

2. Add to `INSTALLED_APPS` in `crm/settings.py`

3. Create models inheriting from `BaseModel`:
   ```python
   from common.base import BaseModel
   from common.models import Org

   class MyModel(BaseModel):
       org = models.ForeignKey(Org, on_delete=models.CASCADE)
       # ... other fields
   ```

4. Always filter queries by organization:
   ```python
   queryset = MyModel.objects.filter(org=request.profile.org)
   ```

5. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Environment Variables Reference

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `ENV_TYPE` | Environment type (`dev` or `prod`) |
| `DBNAME` | PostgreSQL database name |
| `DBUSER` | PostgreSQL username |
| `DBPASSWORD` | PostgreSQL password |
| `DBHOST` | PostgreSQL host |
| `DBPORT` | PostgreSQL port |
| `DEFAULT_FROM_EMAIL` | Default sender email |
| `ADMIN_EMAIL` | Admin notification email |
| `CELERY_BROKER_URL` | Redis URL for Celery broker |
| `CELERY_RESULT_BACKEND` | Redis URL for Celery results |
| `DOMAIN_NAME` | Application domain |
| `SWAGGER_ROOT_URL` | Swagger documentation root URL |

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify database exists
sudo -u postgres psql -l
```

### Migration Issues

```bash
# Show migration status
python manage.py showmigrations

# Reset migrations (development only)
python manage.py migrate --fake <app> zero
```

### Celery Not Processing Tasks

```bash
# Check Redis is running
redis-cli ping

# Check Celery worker logs
celery -A crm worker --loglevel=DEBUG
```

## License

MIT License - see [LICENSE](../LICENSE) for details.
