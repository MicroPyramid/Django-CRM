"""
Tests for the Case list and detail API views.

Run with: pytest cases/tests/test_cases_api.py -v
"""

from unittest.mock import patch

import pytest
from django.db import connection
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from cases.models import Case


CASES_LIST_URL = "/api/cases/"


def _detail_url(pk):
    return f"/api/cases/{pk}/"


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
    """A case belonging to org_b, created by user_b."""
    _set_rls(org_b)
    return Case.objects.create(
        name="Feature request from Org B",
        status="New",
        priority="Low",
        created_by=user_b,
        org=org_b,
    )


@pytest.mark.django_db
class TestCaseListView:
    """Tests for GET /api/cases/ and POST /api/cases/"""

    def test_list_cases(self, admin_client, case_a):
        response = admin_client.get(CASES_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "cases" in response.data
        assert response.data["cases_count"] >= 1

    @patch("cases.views.send_email_to_assigned_user")
    def test_create_case(self, mock_email, admin_client):
        response = admin_client.post(
            CASES_LIST_URL,
            {
                "name": "New support ticket",
                "status": "New",
                "priority": "Normal",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "id" in response.data

    def test_create_case_unauthenticated(self, unauthenticated_client):
        with pytest.raises(PermissionDenied):
            unauthenticated_client.post(
                CASES_LIST_URL,
                {
                    "name": "Should fail",
                    "status": "New",
                    "priority": "Normal",
                },
                format="json",
            )

    def test_org_isolation(self, org_b_client, case_a):
        """org_b_client must not see cases belonging to org_a."""
        response = org_b_client.get(CASES_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        case_ids = [c["id"] for c in response.data["cases"]]
        assert str(case_a.id) not in case_ids

    @patch("cases.views.send_email_to_assigned_user")
    def test_create_case_invalid(self, mock_email, admin_client):
        """POST without the required 'name' field should return 400."""
        response = admin_client.post(
            CASES_LIST_URL,
            {
                "status": "New",
                "priority": "Normal",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] is True


@pytest.mark.django_db
class TestCaseDetailView:
    """Tests for GET/PUT/DELETE/POST /api/cases/<pk>/"""

    def test_get_detail(self, admin_client, case_a):
        response = admin_client.get(_detail_url(case_a.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["cases_obj"]["id"] == str(case_a.id)

    @patch("cases.views.send_email_to_assigned_user")
    def test_update_case(self, mock_email, admin_client, case_a):
        response = admin_client.put(
            _detail_url(case_a.pk),
            {
                "name": "Updated case name",
                "status": "Assigned",
                "priority": "Urgent",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        case_a.refresh_from_db()
        assert case_a.name == "Updated case name"

    def test_delete_case(self, admin_client, case_a):
        response = admin_client.delete(_detail_url(case_a.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert not Case.objects.filter(pk=case_a.pk).exists()

    def test_cross_org_detail_returns_404(self, org_b_client, case_a):
        """A client from org_b cannot retrieve a case from org_a."""
        response = org_b_client.get(_detail_url(case_a.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_comment(self, admin_client, case_a):
        response = admin_client.post(
            _detail_url(case_a.pk),
            {"comment": "This is a test comment."},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "comments" in response.data
