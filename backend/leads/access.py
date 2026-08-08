"""Who may open a lead.

Extracted from ``LeadDetailView.assert_lead_access`` so that the attachment
download view can ask the same question without owning a second copy of the
answer. The detail view still calls it; there is one definition, and the
docstring explaining why lives on it.
"""

from rest_framework.exceptions import PermissionDenied

from common.permissions import is_org_admin

_DENIED = "You do not have Permission to perform this action"


def has_lead_access(profile, user, lead):
    """Admins and superusers see every lead in the org; everyone else sees
    their own.

    The same rule ``LeadListView`` applies when it narrows the queryset to
    ``Q(assigned_to__in=[profile]) | Q(created_by=profile.user)``. Without it,
    a lead the list deliberately withholds is still readable by id.

    ``Lead.created_by`` is a **User** FK, so the creator half compares
    ``profile.user_id``. Two hand-rolled copies of this check once built a set
    of Profile ids and appended a User id to it, which meant the creator's own
    id was never in the set and the check denied the person it existed to
    admit.
    """
    if is_org_admin(profile) or user.is_superuser:
        return True
    if profile.user_id == lead.created_by_id:
        return True
    return profile.id in {assignee.id for assignee in lead.assigned_to.all()}


def assert_lead_access(profile, user, lead):
    """Raise 403 unless ``profile`` may open ``lead``.

    It raises rather than returning a Response: ``get_context_data`` returns
    the dict that ``get()`` passes to ``Response(...)``, so a Response returned
    from in there was wrapped in a second one and rendered as a 500 instead of
    the intended 403.
    """
    if not has_lead_access(profile, user, lead):
        raise PermissionDenied(_DENIED)
