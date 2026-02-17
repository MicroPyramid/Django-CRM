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

    def test_create_team_non_admin_forbidden(self, user_client):
        """Non-admin user cannot create teams."""
        response = user_client.post(
            self.url,
            {"name": "No Permission Team", "description": "Nope"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_team_duplicate_name(self, admin_client, org_a):
        """Creating a team with a duplicate name should fail."""
        Teams.objects.create(name="Duplicate Team", org=org_a)
        response = admin_client.post(
            self.url,
            {"name": "Duplicate Team", "description": "Duplicate"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_team_with_users(self, admin_client, org_a, admin_profile):
        """Create a team and assign users."""
        response = admin_client.post(
            self.url,
            {
                "name": "User Team",
                "description": "Team with users",
                "assign_users": [str(admin_profile.id)],
                "users": [str(admin_profile.id)],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_list_teams_context_keys(self, admin_client, org_a):
        """Team list should include expected context keys."""
        Teams.objects.create(name="Context Team", org=org_a)
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "teams" in response.data
        assert "teams_count" in response.data
        assert "per_page" in response.data

    def test_list_teams_filter_by_name(self, admin_client, org_a):
        """Filter teams by team_name parameter."""
        Teams.objects.create(name="Alpha Team", org=org_a)
        Teams.objects.create(name="Beta Team", org=org_a)
        response = admin_client.get(self.url + "?team_name=Alpha")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["teams_count"] == 1


@pytest.mark.django_db
class TestTeamsDetailView:
    """Tests for GET/PUT/PATCH/DELETE /api/teams/<pk>/"""

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

    def test_get_team_non_admin_forbidden(self, user_client, org_a):
        """Non-admin cannot view team details."""
        team = Teams.objects.create(name="No View", org=org_a)
        response = user_client.get(self._url(team.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_team_non_admin_forbidden(self, user_client, org_a):
        """Non-admin cannot update teams."""
        team = Teams.objects.create(name="No Update", org=org_a)
        response = user_client.put(
            self._url(team.pk),
            {"name": "Not Allowed", "description": "Nope"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_team_non_admin_forbidden(self, user_client, org_a):
        """Non-admin cannot delete teams."""
        team = Teams.objects.create(name="No Delete", org=org_a)
        response = user_client.delete(self._url(team.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_team_with_users(
        self, admin_client, org_a, admin_profile
    ):
        """Update team with assigned users."""
        team = Teams.objects.create(name="Assign Team", org=org_a)
        response = admin_client.put(
            self._url(team.pk),
            {
                "name": "Assign Team",
                "description": "With users",
                "assign_users": [str(admin_profile.id)],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_update_team_duplicate_name(self, admin_client, org_a):
        """Updating to a duplicate name should fail."""
        Teams.objects.create(name="Existing Team", org=org_a)
        team = Teams.objects.create(name="Rename Me", org=org_a)
        response = admin_client.put(
            self._url(team.pk),
            {"name": "Existing Team", "description": "dup"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_team(self, admin_client, org_a):
        """Test partial update via PATCH."""
        team = Teams.objects.create(name="Patch Team", org=org_a)
        response = admin_client.patch(
            self._url(team.pk),
            {"description": "Patched description"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_patch_team_non_admin_forbidden(self, user_client, org_a):
        """Non-admin cannot PATCH teams."""
        team = Teams.objects.create(name="No Patch", org=org_a)
        response = user_client.patch(
            self._url(team.pk),
            {"description": "Nope"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
