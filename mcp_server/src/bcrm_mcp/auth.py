"""Per-request authentication for the http transport.

In http mode every MCP request carries the caller's own Personal Access Token
in the ``Authorization`` header. The server builds a fresh CrmClient from THAT
token for each call, so every caller acts strictly as their own CRM identity
(their role, their org). The server holds no shared token in http mode,
caching or reusing a client across requests would collapse all callers into a
single identity and break tenant isolation, so we deliberately never do it.
"""


class AuthError(Exception):
    """Raised when an http-mode request carries no usable bearer token."""


_BEARER = "bearer "  # scheme prefix, compared case-insensitively


def extract_bearer_token(headers):
    """Return the PAT from an ``Authorization: Bearer <token>`` header.

    ``headers`` is the mapping returned by FastMCP's ``get_http_headers`` (keys
    already lowercased). Returns the token string, or ``None`` when the header
    is absent, not a Bearer scheme, or empty. Never raises, callers decide how
    to handle a missing token.
    """
    if not headers:
        return None
    raw = headers.get("authorization") or headers.get("Authorization")
    if not raw:
        return None
    value = raw.strip()
    if value[: len(_BEARER)].lower() != _BEARER:
        return None
    token = value[len(_BEARER) :].strip()
    return token or None
