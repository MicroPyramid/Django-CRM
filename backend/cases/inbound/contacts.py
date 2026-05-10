"""Resolve the From: address of an inbound email to a Contact, auto-creating
when no match exists for this org.
"""

from __future__ import annotations

import logging
from typing import Optional

from contacts.models import Contact
from .parser import ParsedEmail

logger = logging.getLogger(__name__)


def _split_display_name(display: str, fallback_email: str) -> tuple[str, str]:
    """Split a "First Last" display name into (first, last). Falls back to the
    local part of the email when the display name is missing or empty."""
    name = (display or "").strip()
    if not name:
        local = (fallback_email or "").split("@", 1)[0]
        return (local or "Unknown", "")
    parts = name.split(maxsplit=1)
    if len(parts) == 1:
        return (parts[0], "")
    return (parts[0], parts[1])


def resolve_contact(parsed: ParsedEmail, org) -> Optional[Contact]:
    """Find or auto-create a Contact for the From: address.

    Returns None if the email has no usable From address (already filtered as
    spam upstream usually, but defensively None-safe).
    """
    if not parsed.from_address:
        return None

    existing = (
        Contact.objects.filter(org=org, email__iexact=parsed.from_address)
        .order_by("-created_at")
        .first()
    )
    if existing:
        return existing

    first, last = _split_display_name(parsed.from_display_name, parsed.from_address)
    return Contact.objects.create(
        org=org,
        email=parsed.from_address,
        first_name=first[:255] or "Unknown",
        last_name=last[:255],
        auto_created=True,
        is_active=True,
    )


__all__ = ["resolve_contact"]
