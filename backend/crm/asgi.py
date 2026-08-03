"""ASGI entrypoint for Django-CRM.

Mirror of `wsgi.py` for ASGI servers (uvicorn, hypercorn, daphne). Required
for the in-app notifications SSE stream. Async views serving long-lived
connections will hold a worker hostage when run under WSGI.

It also optionally mounts the BottleCRM **MCP server** at ``/mcp`` so AI agents
can connect over HTTP with no local install (each request authenticates with
its own ``Authorization: Bearer <pat>`` header). The mount is best-effort: if
the optional ``bcrm-mcp`` dependency is not installed, or ``BCRM_MCP_ENABLED``
is false, this module serves Django alone. Exactly as before.

Production deploy must run an ASGI server pointing at this module:

    uvicorn crm.asgi:application --host 0.0.0.0 --port 8000

`runserver` uses WSGI, so the MCP mount is only active under a real ASGI
server; dev workflows for the Django app itself are unchanged.
"""

import os
import sys

from django.core.asgi import get_asgi_application

PROJECT_DIR = os.path.abspath(__file__)
sys.path.append(PROJECT_DIR)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")

django_application = get_asgi_application()


def _mcp_disabled():
    return os.environ.get("BCRM_MCP_ENABLED", "true").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    )


def _build_application():
    """Return the ASGI app: Django alone, or Django with the MCP server at /mcp.

    Falls back to the plain Django app whenever the MCP server can't or
    shouldn't be mounted, so an incomplete install never takes the site down.
    """
    if _mcp_disabled():
        return django_application

    try:
        from bcrm_mcp.auth import extract_bearer_token
        from bcrm_mcp.server import build_http_app
    except ImportError:
        # Optional `mcp` extra not installed: serve Django only.
        return django_application

    # The CRM REST root the MCP tools call. Mounted in-process, so this is a
    # loopback to this very server; override via env for a different internal
    # address.
    base_url = os.environ.get("BCRM_BASE_URL", "http://127.0.0.1:8000")

    # MCP streamable endpoint lives at exactly "/mcp". We dispatch by prefix
    # ourselves rather than using Starlette's Mount, which (in the vendored
    # starlette) only matches "/mcp/…" and lets a slashless "/mcp" fall through
    # to Django, users configure ".../mcp" without a trailing slash.
    mcp_app = build_http_app(base_url, path="/mcp")

    def _bearer_token(scope):
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                return extract_bearer_token(
                    {"authorization": value.decode("latin-1")}
                )
        return None

    async def application(scope, receive, send):
        kind = scope.get("type")
        # Drive ONLY the MCP app's lifespan (it starts the MCP session
        # manager). Django needs no lifespan, so it never sees this scope.
        if kind == "lifespan":
            await mcp_app(scope, receive, send)
            return
        if kind in ("http", "websocket"):
            path = scope.get("path", "")
            if path == "/mcp" or path.startswith("/mcp/"):
                # Edge auth: reject anything without a well-formed bearer token
                # BEFORE it reaches the MCP layer, so initialize/list-tools are
                # unreachable unauthenticated, not just tool calls. (The token's
                # validity is still checked by the backend on each API call.)
                if _bearer_token(scope) is None:
                    await _unauthorized(scope, send)
                    return
                await mcp_app(scope, receive, send)
                return
        await django_application(scope, receive, send)

    return application


async def _unauthorized(scope, send):
    """Send a 401 (http) or reject the connection (websocket) for /mcp requests
    that carry no usable bearer token."""
    if scope.get("type") == "websocket":
        await send({"type": "websocket.close", "code": 1008})
        return
    body = (
        b'{"error":"unauthorized","detail":"Missing or malformed Authorization '
        b'header. Send: Authorization: Bearer <bcrm_pat_...>"}'
    )
    await send(
        {
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", b"Bearer"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


application = _build_application()
