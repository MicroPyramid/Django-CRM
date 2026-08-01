# Contributing to BottleCRM

Thank you for helping improve BottleCRM. Contributions of all sizes are welcome, including bug fixes, features, tests, documentation, and accessibility improvements.

## Before You Start

- Search the [existing issues](https://github.com/Django-CRM/Django-CRM/issues) before opening a new one.
- For a substantial feature or architectural change, open an issue first so the approach can be discussed before implementation begins.
- Keep pull requests focused. Unrelated changes are easier to review when submitted separately.

## Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- Node.js 24
- pnpm 10
- PostgreSQL 14+
- Redis 7+

You can also use Docker Compose, which provides the application services and development dependencies.

## Set Up the Project

Clone your fork and enter the repository:

```bash
git clone https://github.com/<your-username>/Django-CRM.git
cd Django-CRM
```

### Docker Setup

To start the full development stack:

```bash
docker compose up --build
```

The frontend is available at `http://localhost:5173`, and the backend API is available at `http://localhost:8000`.

### Backend Setup

Start PostgreSQL and Redis, create the database named in `backend/.env.example`, and ensure its credentials match your local PostgreSQL configuration. Then run:

```bash
cd backend
uv sync
cp .env.example .env
uv run python manage.py migrate
uv run python manage.py runserver
```

To process background jobs, run the Celery worker in a separate terminal:

```bash
cd backend
uv run celery -A crm worker --loglevel=INFO
```

### Frontend Setup

```bash
cd frontend
pnpm install
pnpm run dev
```

## Development Checks

Run the backend test suite from `backend/`:

```bash
uv run pytest
```

When changing Django models, generate and commit the migration, then verify that no model changes are missing migrations:

```bash
uv run python manage.py makemigrations
uv run python manage.py makemigrations --check --dry-run
```

Run the frontend checks from `frontend/`:

```bash
pnpm run lint
pnpm run check
pnpm run build
```

Use `pnpm run format` to apply the configured frontend formatting rules.

## Submitting a Pull Request

1. Create a branch from `master` with a descriptive name.
2. Make focused changes and include tests where appropriate.
3. Run the relevant development checks.
4. Update documentation when behavior, setup, or public APIs change.
5. Push your branch and open a pull request against `master`.

In the pull request description, explain what changed, why it changed, how it was tested, and include screenshots for visible UI changes.

## Pull Request Checklist

- [ ] The change is focused and does not include unrelated edits.
- [ ] Relevant backend and frontend checks pass.
- [ ] Tests cover new or changed behavior where practical.
- [ ] Required migrations are included.
- [ ] Documentation is updated.
- [ ] No credentials, tokens, or private data are committed.
