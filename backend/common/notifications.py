"""In-app notification dispatcher.

Single call site used by every producer (watchers, mentions, escalations,
future apps). Writes a `Notification` row. That row is the whole delivery
mechanism: clients poll ``GET /api/notifications/?since=<iso>`` and pick it up
on their next tick.

This module used to also publish each new row's id on a Redis pub/sub channel
(``notif:<org_id>:<profile_id>``) to fan out to an SSE consumer. The SSE
stream was removed on 2026-08-03, which left the publish with no subscriber:
it opened a Redis connection per notification for nobody. Removed with it. If
a live transport ever comes back, it should be websockets via Channels rather
than the hand-rolled stream that was here, and it can reintroduce a fan-out
then.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from common.models import Notification, Profile

logger = logging.getLogger(__name__)


def create(
    recipient: Profile,
    verb: str,
    *,
    actor: Optional[Profile] = None,
    entity: Any = None,
    entity_name: str = "",
    link: str = "",
    data: Optional[dict] = None,
) -> Optional[Notification]:
    """Write a Notification row for the recipient.

    Returns the Notification, or ``None`` when delivery was skipped because
    the recipient is inactive.

    ``entity``: pass any model instance; ``entity_type`` is set to its class
    name and ``entity_id`` to its primary key. Pass ``entity_name`` to
    override the denormalized label.
    """
    if recipient is None or not getattr(recipient, "is_active", True):
        return None

    entity_type = ""
    entity_id = None
    if entity is not None:
        entity_type = entity.__class__.__name__
        entity_id = getattr(entity, "pk", None)
        if not entity_name:
            entity_name = str(getattr(entity, "name", "") or "")[:255]

    notif = Notification.objects.create(
        org=recipient.org,
        recipient=recipient,
        verb=verb,
        actor=actor,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        link=link,
        data=data or {},
    )
    return notif
