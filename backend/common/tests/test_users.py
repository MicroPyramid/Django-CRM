"""
Tests for user management views: list users, user detail, update user.

Run with: pytest common/tests/test_users.py -v
"""

import pytest
from rest_framework import status
from rest_framework.exceptions import PermissionDenied


@pytest.mark.django_db
class TestUsersListView:
    """Tests for GET /api/users/"""

    url = "/api/users/"

    def test_list_users_as_admin(self, admin_client):
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "active_users" in response.data

    def test_list_users_unauthenticated(self, unauthenticated_client):
        with pytest.raises(PermissionDenied):
            unauthenticated_client.get(self.url)

    def test_list_users_no_cross_org_leak(
        self, org_b_client, admin_user, admin_profile
    ):
        """org_b_client should not see org_a's users in its listing."""
        response = org_b_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        # Collect all user emails across active and inactive lists
        active = response.data["active_users"]["active_users"]
        inactive = response.data["inactive_users"]["inactive_users"]
        all_emails = [
            p["user_details"]["email"] for p in active
        ] + [
            p["user_details"]["email"] for p in inactive
        ]
        assert admin_user.email not in all_emails


@pytest.mark.django_db
class TestUserDetailView:
    """Tests for GET/PUT /api/user/<pk>/"""

    def _url(self, user_id):
        return f"/api/user/{user_id}/"

    def test_get_user_detail(self, admin_client, admin_user):
        response = admin_client.get(self._url(admin_user.id))
        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data

    def test_update_user(self, admin_client, admin_user):
        response = admin_client.put(
            self._url(admin_user.id),
            {
                "email": admin_user.email,
                "role": "ADMIN",
                "phone": "+1234567890",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_get_user_wrong_org(self, org_b_client, admin_user, admin_profile):
        """org_b_client cannot view a user that belongs to org_a."""
        response = org_b_client.get(self._url(admin_user.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND
