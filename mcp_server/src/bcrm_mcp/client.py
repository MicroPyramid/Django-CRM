import asyncio

import httpx

# One shared connection pool per event loop.
#
# `ClientResolver` builds a fresh CrmClient per call on purpose, so a cached
# client can never serve the next caller under the previous caller's identity.
# Building a fresh *httpx* client alongside it, though, meant a brand-new TCP
# connection for every CRM call with no keep-alive reuse — and since the CRM is
# reached over loopback, each of those becomes another Django request, another
# request thread, and another Postgres connection. That amplification is what
# exhausts the database under agent load.
#
# Sharing only the transport keeps the isolation intact: no credentials are
# stored on the pool. Each CrmClient still holds its own Authorization header
# and passes it per request, exactly as before.
_LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10)
_clients: dict = {}


def _transport_client():
    """Return this event loop's shared httpx client, creating it on first use."""
    loop = asyncio.get_running_loop()
    client = _clients.get(loop)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(limits=_LIMITS)
        _clients[loop] = client
    # Test suites build a loop per test; drop clients bound to dead loops.
    for stale in [ln for ln in _clients if ln is not loop and ln.is_closed()]:
        _clients.pop(stale, None)
    return client


async def aclose_transport_clients():
    """Close pooled transports. For lifespan shutdown hooks and test teardown."""
    for loop, client in list(_clients.items()):
        if not client.is_closed:
            await client.aclose()
        _clients.pop(loop, None)


class CrmError(Exception):
    """Raised on a non-2xx CRM response; message carries the DRF error."""


class CrmClient:
    def __init__(self, base_url: str, token: str, timeout: float = 30.0):
        self._base = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}",
                         "X-Client": "mcp", "Accept": "application/json"}
        self._timeout = timeout

    async def _request(self, method, path, *, params=None, json=None):
        url = f"{self._base}{path}"
        c = _transport_client()
        resp = await c.request(method, url, headers=self._headers,
                               params=params, json=json, timeout=self._timeout)
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise CrmError(f"{resp.status_code}: {detail}")
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    async def get(self, path, params=None):
        return await self._request("GET", path, params=params)

    async def post(self, path, json):
        return await self._request("POST", path, json=json)

    async def patch(self, path, json):
        return await self._request("PATCH", path, json=json)

    async def delete(self, path):
        return await self._request("DELETE", path)
