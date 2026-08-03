"""FastMCP server entry point for BottleCRM (stdio or http transport).

Wraps the plain async tool functions in ``bcrm_mcp.tools`` as FastMCP tools and
exposes a ``build_server(client=None)`` factory plus a ``main()`` console entry
point (the ``bcrm-mcp`` script points at ``bcrm_mcp.server:main``).

The transport is chosen by ``BCRM_TRANSPORT`` (default ``stdio``):

* **stdio**: the process acts as a single user; one :class:`CrmClient` is
  built lazily from ``BCRM_BASE_URL`` + ``BCRM_TOKEN`` and reused.
* **http**: a hosted, multi-user server; each request authenticates with its
  own ``Authorization: Bearer <pat>`` header and gets a *fresh* per-request
  :class:`CrmClient`, so every caller acts strictly as their own CRM identity.
  See :class:`ClientResolver` and ``bcrm_mcp.auth``.

The client is resolved lazily on first tool call so that constructing the
server (e.g. in tests, or to introspect tools) never requires env vars. Pass
``client=`` to inject one.
"""

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

from bcrm_mcp import tools
from bcrm_mcp.auth import AuthError, extract_bearer_token
from bcrm_mcp.client import CrmClient
from bcrm_mcp.config import HTTP, Settings


def _request_headers():
    """Headers of the active HTTP request (empty in stdio).

    ``get_http_headers`` strips ``authorization`` by default, so we explicitly
    opt it back in. That header is exactly what we need for per-request auth.
    """
    return get_http_headers(include={"authorization"})


class ClientResolver:
    """Resolves the :class:`CrmClient` for the current call by transport.

    * an injected client (tests) is always returned as-is;
    * **http** builds a *fresh* client per call from the request's bearer token
      and never caches it. A cached client would serve the next caller under
      the previous caller's identity (a cross-tenant leak);
    * **stdio** builds one shared client from env, lazily, and reuses it.

    ``settings_loader`` and ``headers_getter`` are injectable for tests.
    """

    def __init__(self, injected=None, settings_loader=Settings.from_env,
                 headers_getter=_request_headers):
        self._injected = injected
        self._load_settings = settings_loader
        self._headers_getter = headers_getter
        self._settings = None
        self._stdio_client = None

    def get(self):
        if self._injected is not None:
            return self._injected
        if self._settings is None:
            self._settings = self._load_settings()
        if self._settings.transport == HTTP:
            token = extract_bearer_token(self._headers_getter())
            if not token:
                raise AuthError(
                    "Missing or malformed Authorization header. Send "
                    "'Authorization: Bearer <bcrm_pat_…>' with your request."
                )
            # Fresh, uncached: scoped to this caller for this request only.
            return CrmClient(self._settings.base_url, token)
        if self._stdio_client is None:
            self._stdio_client = CrmClient(
                self._settings.base_url, self._settings.token
            )
        return self._stdio_client


# Tool annotation hints (mcp.types.ToolAnnotations fields). Passed as plain
# dicts to ``@mcp.tool(annotations=...)``. FastMCP 3.x accepts a dict and
# coerces it to a ToolAnnotations model.
_READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
_DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "openWorldHint": True}


def build_server(client=None, settings_loader=None):
    """Build and return a FastMCP server with all CRM tools registered.

    ``client`` may be injected (tests pass a stub); when ``None`` a real
    :class:`CrmClient` is resolved lazily on the first tool call.

    ``settings_loader`` overrides where :class:`Settings` come from. By default
    they are read from env (``Settings.from_env``); the in-Django mount passes a
    loader that returns explicit http-mode settings so it never depends on
    ``BCRM_TRANSPORT`` being set in the Django process env.
    """
    mcp = FastMCP("BottleCRM")
    kwargs = {} if settings_loader is None else {"settings_loader": settings_loader}
    resolver = ClientResolver(injected=client, **kwargs)

    def get_client():
        return resolver.get()

    @mcp.tool(annotations=_READ_ONLY)
    async def crm_search(
        entity: str,
        query: str = "",
        filters: dict | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        """Search/list CRM records of an entity (leads, contacts, accounts, opportunities, tasks, cases, invoices, solutions). Returns compact rows; limit is capped at 50."""
        return await tools.crm_search(
            get_client(), entity, query or None, filters, limit, offset
        )

    @mcp.tool(annotations=_READ_ONLY)
    async def crm_get(entity: str, id: str):
        """Fetch one CRM record's full detail by id."""
        return await tools.crm_get(get_client(), entity, id)

    @mcp.tool(annotations=_WRITE)
    async def crm_create(entity: str, data: dict):
        """Create a CRM record. `data` is validated server-side by the API."""
        return await tools.crm_create(get_client(), entity, data)

    @mcp.tool(annotations=_WRITE)
    async def crm_update(entity: str, id: str, data: dict):
        """Partially update a CRM record (PATCH semantics)."""
        return await tools.crm_update(get_client(), entity, id, data)

    @mcp.tool(annotations=_DESTRUCTIVE)
    async def crm_delete(entity: str, id: str, confirm: bool = False):
        """Delete a CRM record. DESTRUCTIVE and irreversible. You must pass confirm=true to proceed."""
        return await tools.crm_delete(get_client(), entity, id, confirm)

    @mcp.tool(annotations=_WRITE)
    async def crm_action(
        entity: str,
        id: str,
        action: str,
        params: dict | None = None,
        confirm: bool = False,
    ):
        """Run a non-CRUD action (e.g. convert a lead, add_comment, send an invoice). Call list_actions to see allowed actions per entity. Outward-facing actions like `send` (emails a customer) require confirm=true."""
        return await tools.crm_action(
            get_client(), entity, id, action, params, confirm
        )

    @mcp.tool(annotations=_READ_ONLY)
    async def crm_describe(entity: str):
        """Describe an entity's writable/readable fields and enums (from the live API schema)."""
        return await tools.crm_describe(get_client(), entity)

    @mcp.tool(annotations=_READ_ONLY)
    def list_actions():
        """Return the allowed non-CRUD actions for each entity."""
        return tools.list_actions()

    return mcp


def build_http_app(base_url, path="/mcp"):
    """Build the MCP server in http (per-request auth) mode and return its ASGI
    app, ready to be served standalone or composed into another ASGI app (e.g.
    Django's ``asgi.py``).

    ``base_url`` is the CRM REST root the tools call (when composed in-process,
    the same host reached over loopback). ``path`` is the route the streamable
    endpoint is served at *within* the returned app.

    The returned Starlette app carries a ``lifespan`` that MUST be run (serve it
    directly, or forward the ``lifespan`` scope to it from a parent dispatcher)
    or the MCP session manager never starts and requests fail.
    """
    settings = Settings(base_url=base_url.rstrip("/"), transport=HTTP)
    server = build_server(settings_loader=lambda: settings)
    return server.http_app(path=path)


def main():
    """Console entry point. Transport is selected by ``BCRM_TRANSPORT``.

    ``stdio`` (default) talks over stdin/stdout for a locally-launched server.
    ``http`` serves streamable-HTTP on ``BCRM_HOST``:``BCRM_PORT`` at
    ``BCRM_PATH`` and authenticates each request from its Authorization header.
    """
    settings = Settings.from_env()
    server = build_server()
    if settings.transport == HTTP:
        server.run(
            transport="http",
            host=settings.host,
            port=settings.port,
            path=settings.path,
        )
    else:
        server.run()


if __name__ == "__main__":
    main()
