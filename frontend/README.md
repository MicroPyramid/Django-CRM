# BottleCRM web app

The SvelteKit (Svelte 5) web client for BottleCRM. It has no database of its own: every page reads
and writes through the Django REST API in [`../backend`](../backend), the same API the Flutter app
in [`../mobile`](../mobile) uses. For what BottleCRM is, see the [project README](../README.md).

## Run it locally

Start the backend first (see [Development setup](../docs/contributing/development-setup.md)), then:

```bash
cd frontend
cp .env.example .env    # PUBLIC_DJANGO_API_URL points at the backend, http://localhost:8000 by default
pnpm install
pnpm run dev            # http://localhost:5181
```

The browser calls the API cross-origin, so the backend's `CORS_ALLOWED_ORIGINS` must include
`http://localhost:5181`. A missing entry shows up as a CORS error, not a 404.

## Checks

```bash
pnpm run check    # svelte-check type checking
pnpm run lint     # prettier + eslint
pnpm run test     # vitest
pnpm run build    # production build (adapter-node)
```

## Access control

Org membership and role (`USER` or `ADMIN`) come from the server, and the backend is the only place
they are enforced; anything the UI hides is a convenience, not a control. Platform super admin is
the `is_superuser` flag on the user record, granted explicitly and never derived from an email
address.

## More

- [Manual setup](../docs/getting-started/manual-setup.md) and [Docker quick start](../docs/getting-started/docker-quick-start.md)
- [Contributing](../CONTRIBUTING.md)
- License: [MIT](../LICENSE)
