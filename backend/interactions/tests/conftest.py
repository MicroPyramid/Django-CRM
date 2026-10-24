import pytest

from common.models import Profile, User
from common.testing import _make_authenticated_client
from leads.models import Lead


@pytest.fixture
def colleague(org_a):
    user = User.objects.create_user(email="colleague@test.com", password="x")
    return Profile.objects.create(user=user, org=org_a, role="USER", is_active=True)


@pytest.fixture
def colleague_client(colleague):
    return _make_authenticated_client(colleague.user, colleague.org, colleague)


@pytest.fixture
def lead(org_a, user_profile, colleague):
    """Assigned to the member and their colleague, so both may open it."""
    lead = Lead.objects.create(
        org=org_a,
        first_name="Maria",
        last_name="Lopez",
        email="maria@example.com",
        status="assigned",
    )
    lead.assigned_to.add(user_profile, colleague)
    return lead


@pytest.fixture
def hidden_lead(org_a, admin_profile):
    """A lead only the admin holds."""
    lead = Lead.objects.create(org=org_a, first_name="Hidden", status="assigned")
    lead.assigned_to.add(admin_profile)
    return lead
