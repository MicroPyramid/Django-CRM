"""Recomputing a lead when a record's delete takes its interactions with it.

Deleting a contact, account, deal or ticket deletes the interactions it is
home to (`interactions.models.delete_or_unlink`), and one of those can be a
lead's response: a converted lead's calls live on its contact. Each lead
they linked is recomputed once, after the delete commits.
"""

from django.db import transaction
from django.db.models.signals import post_delete

from interactions.service import refresh_lead_response
from leads.models import Lead

_PENDING = "_interaction_leads_to_refresh"


def interaction_deleted(sender, instance, origin=None, **kwargs):
    # One interaction deleted on its own came through
    # `service.delete_interaction`, which recomputes in its own transaction.
    if instance.lead_id is None or origin is instance:
        return
    # Every row one delete takes shares its origin, so the leads are gathered
    # there and refreshed by a single callback.
    holder = origin if origin is not None else instance
    pending = getattr(holder, _PENDING, None)
    if pending is None:
        pending = set()
        setattr(holder, _PENDING, pending)
        transaction.on_commit(lambda: _refresh(pending), robust=True)
    pending.add(instance.lead_id)


def _refresh(lead_ids):
    for lead in Lead.objects.filter(pk__in=lead_ids).select_related("org"):
        refresh_lead_response(lead)


def connect():
    post_delete.connect(
        interaction_deleted,
        sender="interactions.Interaction",
        dispatch_uid="interactions_recompute_on_delete",
    )
