"""Which client sent a request.

The phone app sends `X-BottleCRM-App: <version>` from release 1.13.0 on. Builds
before it send no such header and identify themselves only as Dart's HTTP
client, which is how they are told apart from the web app and from scripts.
"""


def is_legacy_phone(request) -> bool:
    """A phone build that predates the app header (and so the editable
    lead sources), judged from the request alone."""
    meta = getattr(request, "META", None) or {}
    if meta.get("HTTP_X_BOTTLECRM_APP"):
        return False
    return str(meta.get("HTTP_USER_AGENT", "")).startswith("Dart/")
