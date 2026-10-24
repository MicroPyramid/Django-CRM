"""Keep uploaded spreadsheets out of Sentry.

An import upload is a whole customer list. With `send_default_pii` on, a failed
import request would attach its body, and a frame's local variables hold the
rows being parsed. `scrub_import_data` drops both. On an import URL every
frame loses its locals (stdlib `csv` and `openpyxl` frames hold rows and cells)
and breadcrumbs and extra are cleared; elsewhere, for example a Celery task that
runs import code, only frames in `IMPORT_MODULES` lose them. It never raises: a scrubber
that throws makes Sentry drop the event, so a malformed event passes through.
"""

import re
from urllib.parse import urlsplit

from common.public_tokens import scrub_public_tokens

IMPORT_MODULES: tuple[str, ...] = (
    "common.spreadsheet",
    "common.import_mapping",
    "contacts.services.csv_import",
    "contacts.import_views",
    "leads.csv_import",
    "leads.views.import_views",
)

# A lead webhook post is treated the same way: its body is a stranger's
# personal data and, for some senders, carries the webhook's key.
_IMPORT_PATH = re.compile(r"/api/(contacts|leads)/import/|/api/public/leads/")


def _scrub_frames(container, every_frame):
    stacktrace = container.get("stacktrace") if isinstance(container, dict) else None
    frames = stacktrace.get("frames") if isinstance(stacktrace, dict) else None
    if not isinstance(frames, list):
        return
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        module = frame.get("module")
        if every_frame or (
            isinstance(module, str) and module.startswith(IMPORT_MODULES)
        ):
            frame.pop("vars", None)


def scrub_import_data(event):
    try:
        request = event.get("request")
        on_import_path = False
        if isinstance(request, dict):
            url = request.get("url")
            if isinstance(url, str) and _IMPORT_PATH.search(urlsplit(url).path):
                on_import_path = True
                request.pop("data", None)
        if on_import_path:
            event.pop("breadcrumbs", None)
            event.pop("extra", None)
        for key in ("exception", "threads"):
            section = event.get(key)
            values = section.get("values") if isinstance(section, dict) else None
            if isinstance(values, list):
                for value in values:
                    _scrub_frames(value, on_import_path)
    except Exception:
        return event
    return event


def before_send(event, hint):
    return scrub_import_data(scrub_public_tokens(event, hint))
