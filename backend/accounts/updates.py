"""One path for editing an account that already exists.

The account PATCH (`AccountDetailView.patch`) and automation rules both write
through `update_account`, so a gate added here holds for both, as
`cases.updates.update_case` does for tickets.

Authorization is the caller's job and happens first: the view looks the
account up through `accounts.access.visible_accounts_qs`.
"""

import json

from django.db import transaction

from accounts.serializer import AccountCreateSerializer
from accounts.tasks import send_email_to_assigned_user
from common.custom_fields import validate_payload as validate_custom_fields_payload
from common.models import Profile, Tags, Teams
from common.validators import payload_id_list
from contacts.access import replace_visible_contacts


def update_account(request, account, data):
    """Apply ``data`` to ``account`` as a partial update.

    Returns ``None`` once saved, or the error dict a 400 carries, before
    anything is written. Only the keys present in ``data`` change;
    ``assigned_to`` replaces, and the email to whoever it newly assigns is
    queued once the transaction commits, as in
    `cases.updates.notify_newly_assigned`. A malformed id in ``contacts``,
    ``tags``, ``teams`` or ``assigned_to`` raises DRF's ``ValidationError``
    (a 400), before the serializer runs.
    """
    org = request.profile.org
    # Parsed before the first write, as in PUT. An absent key parses to [].
    contact_ids = payload_id_list(data.get("contacts"), "contacts")
    tag_ids = payload_id_list(data.get("tags"), "tags")
    team_ids = payload_id_list(data.get("teams"), "teams")
    assigned_ids = payload_id_list(data.get("assigned_to"), "assigned_to")

    serializer = AccountCreateSerializer(
        account,
        data=data,
        request_obj=request,
        account=True,
        partial=True,
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
            "Account",
            cf_payload or {},
            org,
            existing=account.custom_fields or {},
        )
        if cf_errors:
            return {"custom_fields": cf_errors}
        save_kwargs["custom_fields"] = cleaned_cf
    account = serializer.save(**save_kwargs)

    if "contacts" in data:
        replace_visible_contacts(account.contacts, contact_ids, request.profile)

    if "tags" in data:
        account.tags.clear()
        if tag_ids:
            account.tags.add(
                *Tags.objects.filter(id__in=tag_ids, org=org, is_active=True)
            )

    if "teams" in data:
        account.teams.clear()
        if team_ids:
            account.teams.add(*Teams.objects.filter(id__in=team_ids, org=org))

    if "assigned_to" in data:
        previous = set(account.assigned_to.values_list("id", flat=True))
        account.assigned_to.clear()
        if assigned_ids:
            account.assigned_to.add(
                *Profile.objects.filter(id__in=assigned_ids, org=org, is_active=True)
            )
        current = account.assigned_to.values_list("id", flat=True)
        recipients = list(set(current) - previous)
        if recipients:
            account_id = account.id
            org_id = str(org.id)
            transaction.on_commit(
                lambda: send_email_to_assigned_user.delay(
                    recipients, account_id, org_id
                ),
                robust=True,
            )
    return None
