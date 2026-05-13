"""Macros app fixtures."""

import pytest

from cases.models import Case
from contacts.models import Contact
from macros.models import Macro


@pytest.fixture
def org_macro(org_a):
    return Macro.objects.create(
        org=org_a,
        title="Greeting",
        body="Hi %customer_name%, this is %agent_name% from %org_name%.",
        scope=Macro.SCOPE_ORG,
        is_active=True,
    )


@pytest.fixture
def personal_macro(org_a, user_profile):
    return Macro.objects.create(
        org=org_a,
        title="My closer",
        body="Thanks, %customer_name% — case #%case_id% is closed.",
        scope=Macro.SCOPE_PERSONAL,
        owner=user_profile,
        is_active=True,
    )


@pytest.fixture
def case_factory(org_a):
    """Construct a case with optional contact attached."""

    def _make(*, name="Case", contact=None, status="New", priority="Normal"):
        case = Case.objects.create(
            org=org_a,
            name=name,
            status=status,
            priority=priority,
        )
        if contact is not None:
            case.contacts.add(contact)
        return case

    return _make


@pytest.fixture
def contact_factory(org_a):
    def _make(*, first_name="Alex", last_name="Doe", email="alex@example.com"):
        return Contact.objects.create(
            org=org_a,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

    return _make
