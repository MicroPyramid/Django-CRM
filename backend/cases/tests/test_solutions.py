"""
Tests for the Solution (Knowledge Base) API views.

Run with: pytest cases/tests/test_solutions.py -v
"""

import pytest
from django.db import connection
from rest_framework import status

from cases.models import Solution


SOLUTIONS_LIST_URL = "/api/cases/solutions/"


def _detail_url(pk):
    return f"/api/cases/solutions/{pk}/"


def _publish_url(pk):
    return f"/api/cases/solutions/{pk}/publish/"


def _unpublish_url(pk):
    return f"/api/cases/solutions/{pk}/unpublish/"


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
def solution_a(admin_user, org_a):
    """A draft solution belonging to org_a."""
    _set_rls(org_a)
    return Solution.objects.create(
        title="How to reset password",
        description="Step-by-step guide for password reset.",
        status="draft",
        org=org_a,
        created_by=admin_user,
    )


@pytest.fixture
def approved_solution(admin_user, org_a):
    """An approved (but unpublished) solution belonging to org_a."""
    _set_rls(org_a)
    return Solution.objects.create(
        title="Troubleshooting login issues",
        description="Common login issues and resolutions.",
        status="approved",
        is_published=False,
        org=org_a,
        created_by=admin_user,
    )


@pytest.mark.django_db
class TestSolutionListView:
    """Tests for GET /api/cases/solutions/ and POST /api/cases/solutions/"""

    def test_list_solutions(self, admin_client, solution_a):
        response = admin_client.get(SOLUTIONS_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_create_solution(self, admin_client):
        response = admin_client.post(
            SOLUTIONS_LIST_URL,
            {
                "title": "New Knowledge Base Article",
                "description": "Helpful description.",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Knowledge Base Article"
        assert response.data["status"] == "draft"


@pytest.mark.django_db
class TestSolutionDetailView:
    """Tests for GET/PUT/DELETE /api/cases/solutions/<pk>/"""

    def test_get_solution(self, admin_client, solution_a):
        response = admin_client.get(_detail_url(solution_a.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == solution_a.title

    def test_update_solution(self, admin_client, solution_a):
        response = admin_client.put(
            _detail_url(solution_a.pk),
            {
                "title": "Updated title",
                "description": "Updated description.",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        solution_a.refresh_from_db()
        assert solution_a.title == "Updated title"

    def test_publish_solution(self, admin_client, approved_solution):
        """Publishing an approved solution should succeed."""
        response = admin_client.post(_publish_url(approved_solution.pk))
        assert response.status_code == status.HTTP_200_OK
        approved_solution.refresh_from_db()
        assert approved_solution.is_published is True

    def test_unpublish_solution(self, admin_client, approved_solution):
        """Unpublishing a published solution should succeed."""
        # First publish it
        approved_solution.publish()
        assert approved_solution.is_published is True

        response = admin_client.post(_unpublish_url(approved_solution.pk))
        assert response.status_code == status.HTTP_200_OK
        approved_solution.refresh_from_db()
        assert approved_solution.is_published is False
