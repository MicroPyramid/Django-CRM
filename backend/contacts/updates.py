"""One path for editing a contact that already exists.

The contact PATCH (`ContactDetailView.patch`) and automation rules both write
through `update_contact`, so a gate added here holds for both, as
`cases.updates.update_case` does for tickets.

Authorization is the caller's job and happens first: the view looks the
contact up through `contacts.access.visible_contacts_qs`.
"""

import json

from django.db import transaction

from common.custom_fields import validate_payload as validate_custom_fields_payload
from common.models import Profile, Tags, Teams
from common.validators import payload_id_list
from contacts.serializer import CreateContactSerializer
from contacts.services.account_link import link_primary_account
from contacts.tasks import send_email_to_assigned_user


def notify_newly_assigned(request, contact, previous_assignee_ids):
    """Email whoever the edit just put on this contact, and nobody else.

    Shared by PUT and `update_contact`, as in cases. PUT used to read the
    "previous" assignees after it had replaced them, so it never told anybody;
    PATCH, which the web app edits with, never tried. Queued once the
    surrounding transaction commits, as `cases.updates.notify_newly_assigned`
    explains.
    """
    current = set(contact.assigned_to.all().values_list("id", flat=True))
    recipients = list(current - set(previous_assignee_ids))
    if not recipients:
        return
    contact_id = contact.id
    org_id = str(request.profile.org.id)
    transaction.on_commit(
        lambda: send_email_to_assigned_user.delay(recipients, contact_id, org_id),
        robust=True,
    )


def update_contact(request, contact, data):
    """Apply ``data`` to ``contact`` as a partial update.

    Returns ``None`` once saved, or the error dict a 400 carries, before
    anything is written. Only the keys present in ``data`` change;
    ``assigned_to`` replaces. A malformed id in ``teams``, ``assigned_to`` or
    ``tags`` raises DRF's ``ValidationError`` (a 400).
    """
    org = request.profile.org
    serializer = CreateContactSerializer(
        data=data, instance=contact, request_obj=request, partial=True
    )
    if not serializer.is_valid():
        return serializer.errors

    save_kwargs = {}
    if "custom_fields" in data:
        cf_payload = data.get("custom_fields")
        if isinstance(cf_payload, str):
            try:
                cf_payload = json.loads(cf_payload)
            except (TypeError, ValueError):
                cf_payload = None
        cleaned_cf, cf_errors = validate_custom_fields_payload(
            "Contact",
            cf_payload or {},
            org,
            existing=contact.custom_fields or {},
        )
        if cf_errors:
            return {"custom_fields": cf_errors}
        save_kwargs["custom_fields"] = cleaned_cf

    # Parsed before the first write, as in PUT. An absent key parses to [].
    team_ids = payload_id_list(data.get("teams"), "teams")
    assigned_ids = payload_id_list(data.get("assigned_to"), "assigned_to")
    tag_ids = payload_id_list(data.get("tags"), "tags")

    contact = serializer.save(**save_kwargs)
    link_primary_account(contact)

    if "teams" in data:
        contact.teams.clear()
        if team_ids:
            contact.teams.add(*Teams.objects.filter(id__in=team_ids, org=org))

    if "assigned_to" in data:
        previous_assigned_to_users = list(
            contact.assigned_to.all().values_list("id", flat=True)
        )
        contact.assigned_to.clear()
        if assigned_ids:
            contact.assigned_to.add(
                *Profile.objects.filter(id__in=assigned_ids, org=org, is_active=True)
            )
        notify_newly_assigned(request, contact, previous_assigned_to_users)

    if "tags" in data:
        contact.tags.clear()
        if tag_ids:
            contact.tags.add(
                *Tags.objects.filter(id__in=tag_ids, org=org, is_active=True)
            )
    return None
