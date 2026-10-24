"""Addresses made under `INBOUND_EMAIL_DOMAIN`, and how the catch-all webhook
finds a recipient's org.

A generated address is `<org slug>-<6 random characters>@<domain>`, unique
across every org (`uniq_generated_inbound_address`). Its org is looked up in
the unscoped `PortalAccessToken` table, keyed on the SHA-256 of
`LOOKUP_PREFIX + address`, because RLS hides every org's mailbox from the
anonymous catch-all until it knows which org to read as.
"""

from __future__ import annotations

import re
import secrets
import string

from django.conf import settings
from django.utils.text import slugify

LOOKUP_PREFIX = "inbound-address:"
SLUG_MAX = 30
SUFFIX_LENGTH = 6
_ALPHABET = string.ascii_lowercase + string.digits


def generated_domain() -> str:
    """The domain addresses are made under, or "" when this server makes none."""
    value = getattr(settings, "INBOUND_EMAIL_DOMAIN", "") or ""
    return value.strip().lower().lstrip("@").rstrip(".")


def catch_all_topic() -> str:
    return (getattr(settings, "INBOUND_EMAIL_TOPIC_ARN", "") or "").strip()


def address_domain(address: str) -> str:
    return (address or "").rsplit("@", 1)[-1].strip().lower().rstrip(".")


def on_generated_domain(address: str) -> bool:
    """Whether `address` is at the inbound domain or one of its subdomains."""
    domain = generated_domain()
    if not domain or "@" not in (address or ""):
        return False
    host = address_domain(address)
    return host == domain or host.endswith("." + domain)


def _random_suffix() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(SUFFIX_LENGTH))


def new_address(org) -> str:
    slug = re.sub(r"[-_]+", "-", slugify(org.name or ""))[:SLUG_MAX].strip("-")
    return f"{slug or 'org'}-{_random_suffix()}@{generated_domain()}"


def lookup_token(address: str) -> str:
    return LOOKUP_PREFIX + (address or "").strip().lower()
