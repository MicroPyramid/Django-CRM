"""What an org's creation records about where it came from.

The web app keeps the first visit's campaign tags and referring host in a
cookie and sends them with the create; the API cleans them here and adds which
client created the org. A bad value is dropped rather than refused: this is
analytics, and it must never stop an org from being created.
"""

import re

TAG_KEYS = ("utm_source", "utm_medium", "utm_campaign")
MAX_TAG_LENGTH = 100
_HOST = re.compile(
    r"^(?=.{1,253}$)[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$"
)

# The Flutter app's user agent. Web creates go through the SvelteKit server.
PHONE_USER_AGENT_PREFIX = "Dart/"


def clean_signup_source(raw, user_agent):
    """Return the dict to store on `Org.signup_source`.

    Always has `client` ("phone" or "web"); adds each `utm_*` tag that is a
    non-blank string (printable characters only, at most MAX_TAG_LENGTH) and
    `referrer` when it is a bare host name. Anything else in `raw` is ignored.
    """
    phone = (user_agent or "").startswith(PHONE_USER_AGENT_PREFIX)
    source = {"client": "phone" if phone else "web"}
    if not isinstance(raw, dict):
        return source
    for key in TAG_KEYS:
        value = raw.get(key)
        if isinstance(value, str):
            value = "".join(ch for ch in value if ch.isprintable()).strip()
            if value:
                source[key] = value[:MAX_TAG_LENGTH]
    referrer = raw.get("referrer")
    if isinstance(referrer, str) and _HOST.match(referrer.strip().lower()):
        source["referrer"] = referrer.strip().lower()
    return source
