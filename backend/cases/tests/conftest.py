"""Cases-level pytest fixtures shared across test modules."""

import pytest
from django.db import connection

from cases.models import Case


def _set_rls(org):
    """Set PostgreSQL RLS context so direct ORM writes are allowed.

    No-op on SQLite (used in tests).
    """
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


@pytest.fixture
def case_a(admin_user, org_a):
    """A case belonging to org_a, created by admin_user."""
    _set_rls(org_a)
    return Case.objects.create(
        name="Bug in login page",
        status="New",
        priority="High",
        case_type="Bug",
        description="Login page crashes on submit.",
        created_by=admin_user,
        org=org_a,
    )


@pytest.fixture
def case_b(user_b, org_b):
    """A case belonging to org_b, created by user_b. Used for cross-org isolation tests."""
    _set_rls(org_b)
    return Case.objects.create(
        name="Feature request from Org B",
        status="New",
        priority="Low",
        created_by=user_b,
        org=org_b,
    )


@pytest.fixture
def case_b_same_org(admin_user, org_a):
    """A second case in org_a, used for multi-record bulk operations."""
    _set_rls(org_a)
    return Case.objects.create(
        name="Second case",
        status="New",
        priority="Normal",
        case_type="Question",
        description="Second case in org_a.",
        created_by=admin_user,
        org=org_a,
    )
