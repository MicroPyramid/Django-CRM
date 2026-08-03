import os
from dataclasses import dataclass

STDIO = "stdio"
HTTP = "http"
_VALID_TRANSPORTS = (STDIO, HTTP)


@dataclass
class Settings:
    base_url: str
    token: str | None = None
    transport: str = STDIO
    host: str = "127.0.0.1"
    port: int = 8900
    path: str = "/mcp"

    @classmethod
    def from_env(cls):
        base = os.environ.get("BCRM_BASE_URL", "").rstrip("/")
        if not base:
            raise SystemExit("BCRM_BASE_URL env var is required")

        transport = os.environ.get("BCRM_TRANSPORT", STDIO).strip().lower()
        if transport not in _VALID_TRANSPORTS:
            raise SystemExit(
                f"BCRM_TRANSPORT must be one of {_VALID_TRANSPORTS}, got '{transport}'"
            )

        token = os.environ.get("BCRM_TOKEN") or None
        # stdio: the whole process acts as ONE user, so a server-side token is
        # required. http: the token arrives per-request in each caller's
        # Authorization header, so a server-side BCRM_TOKEN is not only
        # unnecessary but a footgun (it would make every caller share one
        # identity and bypass tenant isolation). Reject it outright.
        if transport == STDIO and not token:
            raise SystemExit("BCRM_TOKEN env var is required for stdio transport")
        if transport == HTTP and token:
            raise SystemExit(
                "BCRM_TOKEN must NOT be set with http transport: each request "
                "authenticates with its own Authorization header. Unset BCRM_TOKEN."
            )

        host = os.environ.get("BCRM_HOST", "127.0.0.1")
        raw_port = os.environ.get("BCRM_PORT", "8900")
        try:
            port = int(raw_port)
        except ValueError:
            raise SystemExit(f"BCRM_PORT must be an integer, got '{raw_port}'")
        path = os.environ.get("BCRM_PATH", "/mcp")

        return cls(
            base_url=base,
            token=token,
            transport=transport,
            host=host,
            port=port,
            path=path,
        )
