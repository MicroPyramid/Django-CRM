"""
Tests for team management views: list, create, detail, update, delete teams.

Run with: pytest common/tests/test_teams.py -v
"""

import pytest
from rest_framework import status

from common.models import Teams


@pytest.mark.django_db
class TestTeamsListView:
    """Tests for GET/POST /api/teams/"""

    url = "/api/teams/"

    def test_create_team(self, admin_client, org_a):
        response = admin_client.post(
            self.url,
            {"name": "Engineering", "description": "Engineering team"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_list_teams(self, admin_client, org_a):
        Teams.objects.create(name="Sales", org=org_a)
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "teams" in response.data

    def test_list_teams_non_admin(self, user_client):
        response = user_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTeamsDetailView:
    """Tests for GET/PUT/DELETE /api/teams/<pk>/"""

    def _url(self, pk):
        return f"/api/teams/{pk}/"

    def test_get_team_detail(self, admin_client, org_a):
        team = Teams.objects.create(name="Support", org=org_a)
        response = admin_client.get(self._url(team.pk))
        assert response.status_code == status.HTTP_200_OK
        assert "team" in response.data

    def test_update_team(self, admin_client, org_a):
        team = Teams.objects.create(name="Old Name", org=org_a)
        response = admin_client.put(
            self._url(team.pk),
            {"name": "New Name", "description": "Updated"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_delete_team(self, admin_client, org_a):
        team = Teams.objects.create(name="To Delete", org=org_a)
        response = admin_client.delete(self._url(team.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert not Teams.objects.filter(pk=team.pk).exists()
