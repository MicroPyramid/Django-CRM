"""In-app notification dispatcher.

Single call site used by every producer (watchers, mentions, escalations,
future apps). Writes a `Notification` row, then best-effort publishes the
new row's id on a Redis pub/sub channel so the SSE consumer can fan it out
to any open browser tabs for that recipient.

Channel naming: ``notif:<org_id>:<profile_id>`` — see
``docs/cases/tier2/in-app-notifications.md`` "Cross-org leak".
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Optional

from django.conf import settings

from common.models import Notification, Profile

logger = logging.getLogger(__name__)


_redis_client = None
_redis_lock = threading.Lock()


def _get_redis():
    """Lazy redis-py client keyed off CELERY_BROKER_URL.

    Returns None if redis is unavailable (e.g. test environments) — callers
    must treat publish as best-effort.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    with _redis_lock:
        if _redis_client is not None:
            return _redis_client
        try:
            import redis  # type: ignore
        except ImportError:  # pragma: no cover
            logger.warning("redis-py not installed; notification fan-out disabled")
            return None
        url = getattr(settings, "CELERY_BROKER_URL", None) or "redis://localhost:6379/0"
        try:
            client = redis.Redis.from_url(url, socket_timeout=1, socket_connect_timeout=1)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not build redis client for notifications: %s", exc)
            return None
        _redis_client = client
        return client


def channel_for(org_id, profile_id) -> str:
    return f"notif:{org_id}:{profile_id}"


def _publish(channel: str, payload: str) -> None:
    client = _get_redis()
    if client is None:
        return
    try:
        client.publish(channel, payload)
    except Exception as exc:
        # Publish failure must never break the originating request — the
        # row is already persisted and the user sees it on next poll/load.
        logger.warning("notifications publish failed on %s: %s", channel, exc)


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
    """Write a Notification row and publish it on the recipient's channel.

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
    _publish(channel_for(recipient.org_id, recipient.id), str(notif.id))
    return notif
