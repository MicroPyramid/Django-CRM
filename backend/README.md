# BottleCRM Backend - Django REST API

The backend for BottleCRM, a multi-tenant CRM platform built with Django REST Framework.

## Tech Stack

- **Django 4.2.1** - Web framework
- **Django REST Framework 3.14.0** - API toolkit
- **PostgreSQL** - Database (psycopg2-binary 2.9.11)
- **Celery 5.5.3** - Async task queue
- **Redis 4.6.0** - Message broker for Celery
- **Wagtail 5.0.1** - CMS integration
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
| `blog` | Blog system |
| `cms` | Wagtail CMS integration |

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

### 3. Configure environment variables

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

### 4. Set up database

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

### 5. Run the development server

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

## Architecture

### Multi-Tenancy

Every request operates within an organization context:

- **Organization (Org)**: Top-level tenant container
- **Users**: Regular members with USER role
- **Admins**: Organization administrators with ADMIN role
- **Super Admin**: Users with @micropyramid.com email domain have platform-wide access

### Authentication

JWT-based authentication with required headers:

```
Authorization: Bearer <token>
org: <organization_uuid>
```

- Access token lifetime: 1 day
- Refresh token lifetime: 365 days

### Middleware

The `common.middleware.get_company.GetProfileAndOrg` middleware:
- Extracts JWT token from `Authorization` header
- Extracts org UUID from `org` header
- Sets `request.profile` (current user's Profile)
- Sets `request.profile.org` (current Organization)

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
├── blog/
├── cms/
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
