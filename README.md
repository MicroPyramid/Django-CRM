# BottleCRM

A modern, open-source CRM platform built with Django REST Framework and SvelteKit.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Django](https://img.shields.io/badge/django-5.x-green.svg)
![SvelteKit](https://img.shields.io/badge/sveltekit-2.x-orange.svg)
![Svelte](https://img.shields.io/badge/svelte-5-orange.svg)

## Overview

BottleCRM is a full-featured Customer Relationship Management system designed for startups and small businesses. It combines a powerful Django REST API backend with a modern SvelteKit frontend, featuring multi-tenant architecture with PostgreSQL Row-Level Security (RLS) for enterprise-grade data isolation.

**Try it free**: [bottlecrm.io](https://bottlecrm.io/)

## Features

### Core CRM Modules
- **Leads** - Track and manage sales leads through your pipeline
- **Accounts** - Manage company/organization records
- **Contacts** - Store and organize contact information
- **Opportunities** - Track deals and sales opportunities
- **Cases** - Customer support case management
- **Tasks** - Task management with calendar and Kanban board views
- **Invoices** - Create and manage invoices

### Platform Features
- **Multi-Tenant Architecture** - PostgreSQL RLS for secure data isolation between organizations
- **JWT Authentication** - Secure token-based authentication
- **Team Management** - Organize users into teams with role-based access
- **Activity Tracking** - Comprehensive audit logs and activity history
- **Comments & Attachments** - Collaborate with comments and file attachments on any record
- **Tags** - Flexible tagging system for organizing records
- **Email Integration** - AWS SES integration for transactional emails
- **Background Tasks** - Celery + Redis for async task processing

## Tech Stack

### Backend
- **Django 5.x** with Django REST Framework
- **PostgreSQL** with Row-Level Security (RLS)
- **Redis** for caching and Celery broker
- **Celery** for background task processing
- **JWT** for authentication
- **AWS S3** for file storage
- **AWS SES** for email delivery

### Frontend
- **SvelteKit 2.x** with Svelte 5 (runes)
- **TailwindCSS 4** for styling
- **shadcn-svelte** UI components
- **Zod** for schema validation
- **Axios** for API communication
- **Lucide** icons

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ with pnpm
- PostgreSQL 14+
- Redis

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/MicroPyramid/Django-CRM.git
cd Django-CRM

# Create and activate virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (see env.md for details)
cp .env.example .env
# Edit .env with your database and other settings

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Start the development server
python manage.py runserver
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

### Start Celery Worker

```bash
# In a new terminal
cd backend
source venv/bin/activate
celery -A crm worker --loglevel=INFO
```

### Access the Application
- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/swagger-ui/
- **Admin Panel**: http://localhost:8000/admin/

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

1. Copy `.env.docker` to `.env.docker.local`
2. Edit values as needed
3. Update `env_file` in `docker-compose.yml` to point to `.env.docker.local`

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

BottleCRM uses PostgreSQL Row-Level Security (RLS) to ensure complete data isolation between organizations. Every database query is automatically filtered by organization context, providing enterprise-grade security.

```bash
# Check RLS status
python manage.py manage_rls --status

# Verify RLS user configuration
python manage.py manage_rls --verify-user

# Test data isolation
python manage.py manage_rls --test
```

## Development

### Backend Commands

```bash
# Run tests
cd backend && pytest

# Format code
black . && isort .

# Check dependencies
pipdeptree
pip-check -H
```

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

## API Documentation

The API follows RESTful conventions:

```
GET/POST       /api/<module>/                 # List/Create
GET/PUT/DELETE /api/<module>/<pk>/            # Detail/Update/Delete
GET/POST       /api/<module>/comment/<pk>/    # Comments
GET/POST       /api/<module>/attachment/<pk>/ # Attachments
```

Interactive API documentation is available at `/swagger-ui/` when running the backend.

## Contributing

We welcome contributions! Please see our contributing guidelines for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Community

- **Issues**: [GitHub Issues](https://github.com/MicroPyramid/Django-CRM/issues)
- **Twitter**: [@micropyramid](https://twitter.com/micropyramid)
- **Commercial Support**: [Contact us](https://micropyramid.com/contact-us/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributors

This project exists thanks to all the people who contributed.

![Contributors](https://opencollective.com/django-crm/contributors.svg?width=890&button=false)

