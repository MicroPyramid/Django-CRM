"""Who may open a contact.

Extracted from ``ContactDetailView.assert_contact_access`` so the attachment
download view asks the same question rather than carrying a second copy of the
answer. The detail view still calls it.
"""

from rest_framework.exceptions import PermissionDenied

from common.permissions import is_org_admin

_DENIED = "You do not have Permission to perform this action"


def contact_account_ids(contact):
    """Every account this contact is joined to, by either route."""
    accounts = set(contact.account_contacts.values_list("id", flat=True))
    if contact.account_id:
        accounts.add(contact.account_id)
    return accounts


def has_contact_access(profile, contact):
    """Who may work on this person's record.

    One predicate for every verb, because the divergence was the bug. The list
    filter and ``delete`` compared ``created_by`` (a User) against
    ``request.profile.user``, correctly. ``get``, ``put``, ``patch`` and the
    comment endpoint compared it against ``request.profile`` -- a Profile is
    never equal to a User, so those four branches could only ever be False.
    The result a non-admin actually saw: their own contacts listed on the
    index, 403 on opening any of them, and a successful delete on the same
    record they had just been refused a look at.

    Assignment to the account the person belongs to counts as access. Whoever
    owns the company owns the conversation with the people at it, and there is
    no reading under which that is true for viewing but false for editing.
    """
    if is_org_admin(profile):
        return True
    if profile.user_id == contact.created_by_id:
        return True
    if profile.id in {assignee.id for assignee in contact.assigned_to.all()}:
        return True
    my_accounts = set(profile.account_assigned_users.values_list("id", flat=True))
    return bool(my_accounts & contact_account_ids(contact))


def assert_contact_access(profile, contact):
    """Raise 403 unless ``profile`` may open ``contact``."""
    if not has_contact_access(profile, contact):
        raise PermissionDenied(_DENIED)
