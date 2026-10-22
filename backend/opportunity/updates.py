"""One path for editing a deal that already exists.

The deal PATCH (`OpportunityDetailView.patch`) and automation rules both write
through `update_deal`, so a gate added here holds for both, as
`cases.updates.update_case` does for tickets.

Authorization is the caller's job and happens first: the view looks the deal
up through `opportunity.access.get_visible_deal`.
"""

import json

from django.db import transaction

from common.custom_fields import validate_payload as validate_custom_fields_payload
from common.models import Profile, Tags, Teams
from common.validators import payload_id_list
from contacts.access import replace_visible_contacts
from opportunity.serializer import OpportunityCreateSerializer
from opportunity.tasks import send_email_to_assigned_user


def update_deal(request, deal, data):
    """Apply ``data`` to ``deal`` as a partial update.

    Returns ``None`` once saved, or the error dict a 400 carries, before
    anything is written. Only the keys present in ``data`` change;
    ``assigned_to`` replaces, and the email to whoever it newly assigns is
    queued once the transaction commits, as in
    `cases.updates.notify_newly_assigned`. A save that moves the deal into a
    won or lost stage records ``request.profile`` as who closed it. A
    malformed id in ``contacts``, ``tags``, ``teams`` or ``assigned_to``
    raises DRF's ``ValidationError`` (a 400).
    """
    org = request.profile.org
    serializer = OpportunityCreateSerializer(
        deal,
        data=data,
        request_obj=request,
        partial=True,
    )
    if not serializer.is_valid():
        return serializer.errors

    save_kwargs = {
        "closed_on": data.get("closed_on") if "closed_on" in data else deal.closed_on
    }
    if "custom_fields" in data:
        cf_payload = data.get("custom_fields")
        if isinstance(cf_payload, str):
            try:
                cf_payload = json.loads(cf_payload)
            except (TypeError, ValueError):
                cf_payload = None
        cleaned_cf, cf_errors = validate_custom_fields_payload(
            "Opportunity",
            cf_payload or {},
            org,
            existing=deal.custom_fields or {},
        )
        if cf_errors:
            return {"custom_fields": cf_errors}
        save_kwargs["custom_fields"] = cleaned_cf
    # Parsed before the first write, as in PUT. An absent key parses to [].
    contact_ids = payload_id_list(data.get("contacts"), "contacts")
    tag_ids = payload_id_list(data.get("tags"), "tags")
    team_ids = payload_id_list(data.get("teams"), "teams")
    assigned_ids = payload_id_list(data.get("assigned_to"), "assigned_to")
    deal = serializer.save(**save_kwargs)

    if "contacts" in data:
        replace_visible_contacts(deal.contacts, contact_ids, request.profile)

    if "tags" in data:
        deal.tags.clear()
        if tag_ids:
            deal.tags.add(*Tags.objects.filter(id__in=tag_ids, org=org, is_active=True))

    if "teams" in data:
        deal.teams.clear()
        if team_ids:
            deal.teams.add(*Teams.objects.filter(id__in=team_ids, org=org))

    if "assigned_to" in data:
        previous = set(deal.assigned_to.values_list("id", flat=True))
        deal.assigned_to.clear()
        if assigned_ids:
            deal.assigned_to.add(
                *Profile.objects.filter(id__in=assigned_ids, org=org, is_active=True)
            )
        current = deal.assigned_to.values_list("id", flat=True)
        recipients = list(set(current) - previous)
        if recipients:
            deal_id = deal.id
            org_id = str(org.id)
            transaction.on_commit(
                lambda: send_email_to_assigned_user.delay(recipients, deal_id, org_id),
                robust=True,
            )

    if serializer.closing:
        deal.closed_by = request.profile
        deal.save()
    return None
