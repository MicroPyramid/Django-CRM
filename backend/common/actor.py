"""Who the activity feed credits when the request is not the one acting.

A running automation rule acts as its owner, inside a request someone else
made or outside any request. Its writes are credited with `acting_for(owner,
rule.name)`, which the feed's receivers read before the request's profile.
"""

from contextlib import contextmanager
from contextvars import ContextVar

_actor = ContextVar("acting_for", default=None)


@contextmanager
def acting_for(profile, note: str):
    """Credit the block's activity to `profile`, noting `note` (a rule's name)."""
    token = _actor.set((profile, note))
    try:
        yield
    finally:
        _actor.reset(token)


def current_actor():
    """`(profile, note)` inside `acting_for`, else None."""
    return _actor.get()
