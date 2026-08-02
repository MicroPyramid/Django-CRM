# MCP server

`bcrm-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io) server that lets an AI
agent (Claude Desktop, Cursor, Codex CLI, Gemini CLI, or any other MCP client) read and write CRM
data. It lives in its own top-level package, `mcp_server/`, next to `backend/` and `frontend/` —
not inside the Django project — and it is a thin HTTP client of the CRM's own REST API: it has no
database connection of its own and does not import Django (`mcp_server/src/bcrm_mcp/client.py`
depends only on `httpx`). Every tool call becomes one authenticated request to `/api/...`, and the
backend enforces RLS, RBAC and field validation exactly as it would for any other caller.

Source and further detail: [`mcp_server/README.md`](https://github.com/django-crm/Django-CRM/blob/master/mcp_server/README.md)
in the repository.

## What it does

The server exposes eight tools an agent can call — search/list, get, create, update, delete, a
generic non-CRUD action runner, a schema-describe helper, and an action-discovery helper — over
eight CRM entities: leads, contacts, accounts, opportunities, tasks, cases, invoices and
solutions. It does not add any capability the REST API doesn't already have; it's a uniform,
agent-friendly surface over the same endpoints documented in [API reference](../api/conventions.md).

## Installing

There are two things you can install, depending on how you want to run it.

**The standalone package**, for running the server as a local subprocess your MCP client launches
(the `stdio` transport, the default):

```bash
cd mcp_server
uv sync
```

`uv sync` creates `mcp_server/.venv/` from `mcp_server/pyproject.toml` + `uv.lock`. The package
requires Python 3.11+ and pulls in `fastmcp`, `httpx` and `pydantic` — nothing from the Django
project.

**The `mcp` extra on the backend**, for mounting the server inside the Django app so it's reachable
over HTTP without a local install at all:

```bash
cd backend
uv sync --extra mcp
```

This is declared in `backend/pyproject.toml` as `[project.optional-dependencies] mcp =
["bcrm-mcp"]`, with `bcrm-mcp` resolved via `[tool.uv.sources]` as an editable path dependency on
`../mcp_server`. It is opt-in specifically so the core backend install stays lean — a plain `uv
sync` in `backend/` never pulls in `fastmcp` or `starlette` at all. If the extra isn't installed,
`backend/crm/asgi.py` catches the resulting `ImportError` and serves Django alone; an incomplete or
skipped MCP install never takes the rest of the site down.

## Hosted at /mcp

`backend/crm/asgi.py` optionally mounts the MCP server at exactly `/mcp` on the same process that
serves the rest of the API — no separate deployment. This only activates when three things are all
true: the `mcp` extra is installed, `BCRM_MCP_ENABLED` is not set to a falsy value (`0`, `false`,
`no` or `off` — anything else, including unset, leaves it enabled), and the app is served under
**ASGI**, not WSGI:

```bash
# from backend/
uv sync --extra mcp
BCRM_BASE_URL=http://127.0.0.1:8000 \
  uv run uvicorn crm.asgi:application --host 0.0.0.0 --port 8000
# MCP is now live at http://<host>:8000/mcp
```

`manage.py runserver` uses WSGI, so the mount is inactive under the ordinary local dev server —
this is purely an ASGI-server concern and doesn't change any other local workflow.
`BCRM_BASE_URL` is the loopback address the mounted tools call to reach the CRM API; it defaults
to `http://127.0.0.1:8000`, which is correct when MCP and Django share the same process, as they
do here.

The mount dispatches by path prefix rather than Starlette's `Mount` (which only matches
`/mcp/…` with a trailing segment and would let a bare `/mcp` fall through to Django) — both `/mcp`
and `/mcp/...` are routed to the MCP app, everything else goes to Django as before.

## Authenticating

The server has two transports, and they authenticate differently:

- **`stdio`** (default, used when your MCP client launches `bcrm-mcp` as a local subprocess) — the
  whole process acts as one user. It reads a single token from `BCRM_TOKEN` at startup and reuses
  one `CrmClient` for every call. `Settings.from_env()` refuses to start without it.
- **`http`** (the `/mcp` mount above, or a standalone server run with `BCRM_TRANSPORT=http`) — a
  long-lived, multi-user server. There is no server-side token at all; `Settings.from_env()`
  actively rejects a `BCRM_TOKEN` set alongside `BCRM_TRANSPORT=http`, because a shared token would
  collapse every caller into one identity. Instead **every request carries its own
  `Authorization: Bearer <bcrm_pat_…>` header**, and `ClientResolver.get()`
  (`mcp_server/src/bcrm_mcp/server.py`) builds a fresh, uncached `CrmClient` from that header on
  every single call — never reused across requests, so one caller's identity can never leak into
  the next caller's response.

For the `/mcp` mount specifically, `crm/asgi.py` enforces this at the edge: any request to `/mcp`
or `/mcp/...` with no well-formed bearer token gets a `401` before it reaches the MCP layer at
all — even `initialize` and tool listing are unreachable without a token, not just the tool calls
that touch data. The token's actual validity (not expired, not revoked, owning profile and org
still active) is then re-checked by the backend on every API call the tool makes, the same way any
other PAT-authenticated request is checked — see
[Tokens and API keys](../api/tokens-and-api-keys.md#personal-access-tokens) for how a PAT is
minted, validated and revoked.

In both transports, the token is a normal BottleCRM personal access token
(`bcrm_pat_…`) — there is nothing MCP-specific about it.

## Available tools

| Tool | Kind | Description |
| --- | --- | --- |
| `crm_search` | read-only | List/search records of an entity. Takes `query`, `filters`, `limit`, `offset`. `limit` is capped at **50** regardless of what's requested (`MAX_LIMIT` in `mcp_server/src/bcrm_mcp/tools.py`). |
| `crm_get` | read-only | Fetch one record's full detail by `id`. |
| `crm_create` | write | Create a record from a `data` object, validated server-side exactly as `POST` to the underlying endpoint would be. |
| `crm_update` | write | Partially update a record (PATCH semantics) from a `data` object. **Returns an error for `invoices`** — see below. |
| `crm_delete` | destructive | Delete a record. Refuses to run unless called with `confirm=true`. **Also returns an error for `invoices`** — see below. |
| `crm_action` | write | `POST` a non-CRUD action to `/api/<entity>/<id>/<action>/`. Most of the actions `entities.py` lists don't resolve to a real route today — see below before relying on this. |
| `crm_describe` | read-only | Return an entity's fields, types, enums and which are required, derived from the live OpenAPI schema at `/schema/`. |
| `list_actions` | read-only | Return the allowed non-CRUD actions for every entity, exactly as `entities.py` declares them — see below for which of those are actually reachable. |

CRUD tools take an `entity` argument. `resolve_path` (`mcp_server/src/bcrm_mcp/entities.py`) maps
each to its real API path and the non-CRUD actions `entities.py` declares as allowed for it:

| Entity | API path | Non-CRUD actions declared |
| --- | --- | --- |
| `leads` | `/api/leads/` | `convert`, `add_comment` |
| `contacts` | `/api/contacts/` | `add_comment` |
| `accounts` | `/api/accounts/` | `add_comment` |
| `opportunities` | `/api/opportunities/` | `add_comment` |
| `tasks` | `/api/tasks/` | — |
| `cases` | `/api/cases/` | `add_comment` |
| `invoices` | `/api/invoices/` | `send` |
| `solutions` | `/api/cases/solutions/` | — |

Solutions are served under the cases app, not at a top-level `/api/solutions/` — `crm_search(entity="solutions", ...)` resolves to `/api/cases/solutions/` correctly, but it's worth knowing if you're
cross-referencing the [Endpoint index](../api/endpoint-index.md).

**Most of the actions in that table don't work, and neither does `crm_update`/`crm_delete` on
invoices — this is a real bug in `entities.py`, not a doc gap, and it isn't fixed here.**
`crm_action` builds `POST /api/<entity>/<id>/<action>/` (`tools.py`). Checked against the real
Django URLconfs (`leads/urls.py`, `contacts/urls.py`, `accounts/urls.py`, `opportunity/urls.py`,
`cases/urls.py`, `invoices/api_urls.py`):

- **`convert` on `leads`** — no such route exists anywhere in `leads/urls.py`. Converting a lead
  is done by setting its status, not by calling an action:
  `crm_update(entity="leads", id=..., data={"status": "converted"})`.
- **`add_comment`** on `leads`, `contacts`, `accounts`, `opportunities` and `cases` — none of these
  resolve either. Every one of those apps routes comments at `comment/<id>/`
  (e.g. `POST /api/leads/comment/<id>/`), not `<id>/add_comment/`, and Django's `<str:pk>` URL
  converter doesn't match a `/` inside the segment, so `<id>/add_comment/` matches nothing. No tool
  in this MCP server currently reaches the `comment/<id>/` routes at all.
- **`send` on `invoices`** is the only one that actually resolves —
  `POST /api/invoices/<id>/send/` is a real route (`invoices/api_urls.py`).

Calling `crm_action` with any of the non-working entries returns a `CrmError` carrying the
backend's `404` — the MCP layer doesn't pre-validate that the action exists before posting.

Separately, `InvoiceDetailView` (`backend/invoices/api_views.py`) implements only `get` and `put`
— no `patch`, no `delete` — so `crm_update` (which sends `PATCH`) and `crm_delete` (which sends
`DELETE`) both come back as a `CrmError` carrying a `405` for `invoices`, regardless of the
`data`/`confirm` you pass. To change an invoice, use `crm_action(entity="invoices",
action="send", confirm=true)` for sending it, or a full `PUT` via the REST API directly (see
[Invoices and estimates](../api/invoices.md)) for anything else — there is no MCP tool that
partially updates or deletes an invoice today.

## Permissions

**The agent is exactly as privileged as the PAT it's given, no more and no less.** `PATAuthentication`
resolves the token to the owning `Profile` and sets `request.profile`/`request.org` from it
(`backend/common/pat_auth.py`) — the same code path any other PAT-authenticated request goes
through. There is no separate MCP identity, no elevated service account, and no way for the MCP
layer itself to grant a permission the token's owner doesn't already have. A PAT does carry a
`scopes` field, but nothing in the request-handling code enforces it yet (see
[Tokens and API keys](../api/tokens-and-api-keys.md#personal-access-tokens)) — so today there is no
way to hand an agent a narrower token than its owner's own full role and org access. Treat every
PAT you configure into an MCP client as equivalent to handing that agent your own login for as
long as the token is valid.

A few narrower guards live in the MCP layer itself, on top of (not instead of) backend
enforcement:

- `crm_search` caps `limit` at 50 no matter what the agent asks for, so a single call can't pull an
  unbounded result set.
- `crm_delete` refuses to run without `confirm=true`.
- `crm_action` refuses an outward-facing action — currently just `send` (emailing a customer an
  invoice) — without `confirm=true` too, mirroring the delete guard so a model can't trigger a
  real-world side effect off a misread instruction.

Beyond that, the MCP server does no authorization of its own: it forwards each tool call to the
CRM API verbatim and surfaces whatever the API returns, success or error (`CrmClient._request`
raises `CrmError` whenever `resp.status_code >= 400`, carrying the DRF error body — a `3xx`
response isn't treated as an error by this check and instead falls through to `resp.json()`,
which would raise its own decode error if that response body isn't JSON).
RLS, role checks and per-object ownership rules are all enforced exactly once, in the backend, the
same as for the web app or the mobile app.

To cut off an agent immediately, revoke its PAT. There are two ways to do that, and which one
applies depends on your role. An admin can revoke any token in the org from the CRM at
**Settings → API tokens** (`/settings/api-tokens`); that page's revoke action calls the
admin-only `DELETE /api/org/tokens/{id}/`, and the whole page is gated on that same admin-only
oversight list (`GET /api/org/tokens/`) — a non-admin who opens it sees "Admins only", not a token
list, and can't reach any revoke control there at all. Any role can instead call
`DELETE /api/profile/tokens/{id}/` directly against their **own** token — a separate, self-service
endpoint that no UI on this settings page currently calls — which is the option to use if the PAT
you need to revoke is yours and you aren't an admin.
