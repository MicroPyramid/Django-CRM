"""Tests for Case detail solutions inclusion and link/unlink endpoints."""

import pytest

from cases.models import Solution


@pytest.mark.django_db
class TestCaseDetailSolutions:
    def test_detail_includes_linked_solutions(
        self, admin_client, case_a, org_a, admin_user
    ):
        sol = Solution.objects.create(
            title="Reset password steps",
            description="1. Click forgot password...",
            org=org_a,
            status="approved",
            is_published=True,
            created_by=admin_user,
        )
        sol.cases.add(case_a)

        response = admin_client.get(f"/api/cases/{case_a.pk}/")

        assert response.status_code == 200
        data = response.json()
        assert "solutions" in data
        assert len(data["solutions"]) == 1
        assert data["solutions"][0]["title"] == "Reset password steps"

    def test_detail_solutions_excludes_other_org(
        self, admin_client, case_a, org_b, admin_user
    ):
        Solution.objects.create(
            title="Other org solution",
            description="...",
            org=org_b,
            created_by=admin_user,
        )
        response = admin_client.get(f"/api/cases/{case_a.pk}/")
        assert response.status_code == 200
        assert response.json()["solutions"] == []


@pytest.mark.django_db
class TestCaseSolutionLinking:
    def _solution(self, org, user, **kwargs):
        return Solution.objects.create(
            title=kwargs.get("title", "S"),
            description="x",
            org=org,
            status=kwargs.get("status", "approved"),
            is_published=kwargs.get("is_published", True),
            created_by=user,
        )

    def test_link_solution(self, admin_client, case_a, org_a, admin_user):
        sol = self._solution(org_a, admin_user)
        response = admin_client.post(
            f"/api/cases/{case_a.pk}/solutions/",
            {"solution_id": str(sol.pk)},
            content_type="application/json",
        )
        assert response.status_code == 201
        assert sol in case_a.solutions.all()

    def test_link_idempotent(self, admin_client, case_a, org_a, admin_user):
        sol = self._solution(org_a, admin_user)
        case_a.solutions.add(sol)
        response = admin_client.post(
            f"/api/cases/{case_a.pk}/solutions/",
            {"solution_id": str(sol.pk)},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert case_a.solutions.count() == 1

    def test_link_cross_org_404(self, admin_client, case_a, org_b, admin_user):
        sol = self._solution(org_b, admin_user)
        response = admin_client.post(
            f"/api/cases/{case_a.pk}/solutions/",
            {"solution_id": str(sol.pk)},
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_unlink_solution(self, admin_client, case_a, org_a, admin_user):
        sol = self._solution(org_a, admin_user)
        case_a.solutions.add(sol)
        response = admin_client.delete(
            f"/api/cases/{case_a.pk}/solutions/{sol.pk}/"
        )
        assert response.status_code == 204
        assert sol not in case_a.solutions.all()
