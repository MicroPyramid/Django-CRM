"""Noting what a save changed, for the rule engine.

A watched model's save is captured as a `Change` holding the old and new
value of each catalogue field it moved. Inside a request the change waits in
a per-request buffer, merged by record, until `AutomationMiddleware` hands
the buffer to the engine once the view has returned, for the reasons given
in `webhooks/emit.py`. Inside a running rule it joins that rule's chain.
Elsewhere (a Celery task, a management command) it goes to the engine when
the surrounding transaction commits.

The old row is read only when the record's org has an active rule on that
object. Without one, a save costs one rule check, cached per request.
"""

import logging
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from crum import get_current_request
from django.db import transaction
from django.db.models.signals import post_save, pre_save

logger = logging.getLogger(__name__)

CREATED = "created"
UPDATED = "updated"

_BUFFER_ATTR = "_automation_changes"
_ACTIVE_ATTR = "_automation_active"
# Set on the instance by pre_save and taken by post_save.
_PENDING_ATTR = "_automation_pending"

_watched: dict[type, Callable[[Any], str | None]] = {}
_suppressed = ContextVar("automation_suppressed", default=False)


@dataclass
class Change:
    org_id: Any
    object_key: str
    record_id: Any
    event: str
    changes: dict[str, tuple[Any, Any]]


def watch(model, key_for: Callable[[Any], str | None]) -> None:
    """Capture saves of `model`; `key_for(instance)` names its object key."""
    _watched[model] = key_for


@contextmanager
def suppress_rules():
    """Capture nothing inside the block: its writes set off no rule."""
    token = _suppressed.set(True)
    try:
        yield
    finally:
        _suppressed.reset(token)


def _active_rules(org_id):
    from automation.models import AutomationRule

    return AutomationRule.objects.filter(
        org_id=org_id, is_active=True, paused_reason=""
    )


def has_active_rules(org_id, object_key) -> bool:
    """Whether the org has a switched-on rule on `object_key` that is not paused."""
    request = get_current_request()
    if request is None:
        return _active_rules(org_id).filter(object_key=object_key).exists()
    cache = request.__dict__.setdefault(_ACTIVE_ATTR, {})
    if org_id not in cache:
        keys = _active_rules(org_id).order_by().values_list("object_key", flat=True)
        cache[org_id] = frozenset(keys)
    return object_key in cache[org_id]


def flush(request) -> list[Change]:
    """The request's captured changes, removed from it."""
    buffer = request.__dict__.pop(_BUFFER_ATTR, None)
    return list(buffer.values()) if buffer else []


def _merge(buffer, change):
    """Add `change` to `buffer`, one entry per record.

    A create absorbs the updates after it. Two updates keep the first old
    value and the last new one, and a field back where it started drops out.
    """
    key = (change.object_key, change.record_id)
    earlier = buffer.get(key)
    if earlier is None or change.event == CREATED:
        buffer[key] = change
        return
    if earlier.event == CREATED:
        return
    merged = dict(earlier.changes)
    for field, (old, new) in change.changes.items():
        first = merged[field][0] if field in merged else old
        if first == new:
            merged.pop(field, None)
        else:
            merged[field] = (first, new)
    if merged:
        earlier.changes = merged
    else:
        del buffer[key]


def _record(change):
    from automation import engine

    chain = engine.current_chain()
    if chain is not None:
        _merge(chain.changes, change)
        return
    request = get_current_request()
    if request is not None:
        _merge(request.__dict__.setdefault(_BUFFER_ATTR, {}), change)
        return
    transaction.on_commit(lambda: engine.process([change]), robust=True)


def _before_save(sender, instance, raw=False, **kwargs):
    instance.__dict__.pop(_PENDING_ATTR, None)
    key_for = _watched.get(sender)
    if key_for is None or raw or _suppressed.get() or not instance.org_id:
        return
    # A capture failure must not fail the save, so it is logged (without the
    # record's data) and its reads run in a savepoint: a database error
    # swallowed without one leaves the caller's transaction aborted, as
    # `cases.signals._maybe_route` found.
    try:
        key = key_for(instance)
        if key is None or not has_active_rules(instance.org_id, key):
            return
        from automation.objects import adapter_for

        with transaction.atomic():
            adapter = adapter_for(instance.org, key)
            if adapter is None:
                return
            before = None
            if not instance._state.adding:
                old = sender._base_manager.filter(pk=instance.pk).first()
                before = adapter.snapshot(old) if old is not None else None
        instance.__dict__[_PENDING_ATTR] = (key, adapter, before)
    except Exception:
        logger.exception(
            "Could not read %s %s before its save", sender.__name__, instance.pk
        )


def _after_save(sender, instance, created, **kwargs):
    pending = instance.__dict__.pop(_PENDING_ATTR, None)
    if pending is None:
        return
    key, adapter, before = pending
    try:
        if created:
            _record(Change(instance.org_id, key, instance.pk, CREATED, {}))
            return
        if before is None:
            return
        with transaction.atomic():
            after = adapter.snapshot(instance)
        moved = {
            field: (before.get(field), new)
            for field, new in after.items()
            if before.get(field) != new
        }
        if moved:
            _record(Change(instance.org_id, key, instance.pk, UPDATED, moved))
    except Exception:
        logger.exception(
            "Could not capture a change to %s %s", sender.__name__, instance.pk
        )


def connect():
    pre_save.connect(_before_save, dispatch_uid="automation_capture_before")
    post_save.connect(_after_save, dispatch_uid="automation_capture_after")
