# CLAUDE.md - AI Assistant Guide for BottleCRM

## Project Overview

BottleCRM (Django-CRM) is an open-source CRM system built with Django and Django REST Framework. It provides customer relationship management for startups and small businesses.

**Status**: Maintenance mode - active development has moved to [MicroPyramid/opensource-startup-crm](https://github.com/MicroPyramid/opensource-startup-crm) (SvelteKit version).

## Tech Stack

- **Backend**: Django 4.2.1, Django REST Framework 3.14.0
- **Database**: PostgreSQL
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Task Queue**: Celery 5.2.7 with Redis
- **CMS**: Wagtail 5.0.1
- **API Docs**: drf-spectacular (Swagger/OpenAPI)
- **Deployment**: Docker, Gunicorn

## Project Structure

```
crm/                    # Django project settings
common/                 # Shared models, auth, utilities
accounts/               # Account/Company management
contacts/               # Contact management
leads/                  # Lead management
opportunity/            # Sales pipeline
tasks/                  # Task management
cases/                  # Support/issue tracking
events/                 # Calendar/events
teams/                  # Team management
invoices/               # Invoice management
emails/                 # Email management
cms/                    # Wagtail CMS
templates/              # HTML templates
static/                 # Static assets
docs/                   # Sphinx documentation
scripts/                # Deployment scripts
```

## Key Files

| File | Purpose |
|------|---------|
| `manage.py` | Django CLI entry point |
| `crm/settings.py` | Main configuration |
| `crm/urls.py` | URL routing |
| `crm/celery.py` | Celery task queue setup |
| `common/models.py` | User, Org, Profile models |
| `common/utils.py` | Shared utilities and constants |
| `requirements.txt` | Python dependencies |

## Development Setup

### Prerequisites
- Python 3.x
- PostgreSQL 9.4+
- Redis server

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ENV.md .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver

# Start Celery worker (separate terminal)
celery -A crm worker --loglevel=INFO
```

### Docker Setup

```bash
docker build -t djcrm:1 -f docker/dockerfile .
docker-compose -f docker/docker-compose.yml up
```

## Common Commands

```bash
# Run development server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Run tests
pytest

# Run tests with coverage
coverage run -m pytest
coverage report

# Start Celery worker
celery -A crm worker --loglevel=INFO

# Format code
black .
```

## Testing

- **Framework**: pytest with Django plugin
- **Config**: `pytest.ini`
- **Coverage**: `.coveragerc`

### Test Locations
- `*/tests_celery_tasks.py` - Celery task tests (per app)
- `*/tests.py` - Unit tests

### Run Tests
```bash
pytest                          # All tests
pytest accounts/                # Single app
pytest -x                       # Stop on first failure
coverage run -m pytest          # With coverage
```

## API Structure

### Base URL Patterns
- `/api/` - Common endpoints
- `/api/accounts/` - Account management
- `/api/contacts/` - Contact management
- `/api/leads/` - Lead management
- `/api/opportunities/` - Sales pipeline
- `/api/teams/` - Team management
- `/api/tasks/` - Task management
- `/api/events/` - Events
- `/api/cases/` - Case management

### API Documentation
- `/swagger-ui/` - Swagger UI
- `/api/schema/redoc/` - ReDoc
- `/schema/` - OpenAPI schema

## Code Conventions

### Django App Pattern
Each app follows this structure:
- `models.py` - Database models
- `views.py` - API views (class-based)
- `serializer.py` - DRF serializers
- `tasks.py` - Celery async tasks
- `tests_celery_tasks.py` - Task tests

### Model Pattern
Models inherit from `common.base.BaseModel` for timestamp fields:
```python
from common.base import BaseModel

class MyModel(BaseModel):
    # created_at and updated_at are automatic
    name = models.CharField(max_length=255)
```

### View Pattern
Views use DRF class-based views with permissions:
```python
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class MyView(APIView):
    permission_classes = [IsAuthenticated]
```

### Serializer Naming
- Read serializers: `ModelSerializer`
- Write serializers: `CreateModelSerializer`

### Code Quality
- **Formatter**: Black (configured in `.pre-commit-config.yaml`)
- **Pre-commit**: `pre-commit install`

## Environment Variables

Key variables (see `ENV.md` for full list):

```
SECRET_KEY          # Django secret key
ENV_TYPE            # dev/stage/live
DBNAME              # PostgreSQL database name
DBUSER              # Database user
DBPASSWORD          # Database password
DBHOST              # Database host
CELERY_BROKER_URL   # Redis URL for Celery
```

## Multi-tenancy

The app supports multiple organizations via the `Org` model in `common/models.py`. Middleware in `common/middleware/get_company.py` handles organization context.

## Important Patterns

### Authentication
JWT tokens via `djangorestframework-simplejwt`. Custom auth in `common/external_auth.py`.

### Async Tasks
Celery tasks defined in `*/tasks.py` files. Example:
```python
from celery import shared_task

@shared_task
def send_email_task(email_data):
    # Task implementation
    pass
```

### Tags and Relationships
Many-to-many relationships use through models. Tags are stored in `accounts/models.py`.

## CI/CD

- **GitHub Actions**: CodeQL security scanning
- **Travis CI**: Test execution and coverage
- **Jenkins**: Docker build and deployment

## External Documentation

- ReadTheDocs: http://django-crm.readthedocs.io
- Demo: https://bottlecrm.io/
- Sphinx docs: `docs/source/`

## When Making Changes

1. **Follow existing patterns** - Check similar files in the same app
2. **Add tests** - Create tests in `tests_celery_tasks.py` or `tests.py`
3. **Run formatter** - Use `black .` before committing
4. **Update migrations** - Run `makemigrations` for model changes
5. **Check API docs** - Ensure serializers are documented with drf-spectacular

## Common Issues

- **Database connection**: Ensure PostgreSQL is running and `.env` is configured
- **Celery tasks not running**: Start Redis and Celery worker
- **Static files 404**: Run `python manage.py collectstatic`
- **Migration conflicts**: Check for unapplied migrations with `python manage.py showmigrations`
