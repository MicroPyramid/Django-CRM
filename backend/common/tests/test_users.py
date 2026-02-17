"""
Tests for user management views: list users, user detail, update user, status.

Run with: pytest common/tests/test_users.py -v
"""

import pytest
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from common.models import Profile


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

    def test_list_users_non_admin_forbidden(self, user_client):
        """Non-admin user should get 403 on user list."""
        response = user_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_context_keys(self, admin_client):
        """User list should include expected context keys."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert "active_users" in data
        assert "inactive_users" in data
        assert "admin_email" in data
        assert "roles" in data
        assert "status" in data

    def test_list_users_with_email_filter(
        self, admin_client, org_a, admin_user, admin_profile
    ):
        """Filter users by email."""
        response = admin_client.get(self.url + "?email=admin")
        assert response.status_code == status.HTTP_200_OK
        active = response.data["active_users"]["active_users"]
        emails = [p["user_details"]["email"] for p in active]
        assert "admin@test.com" in emails

    def test_list_users_with_role_filter(
        self, admin_client, org_a, admin_profile, user_profile
    ):
        """Filter users by role."""
        response = admin_client.get(self.url + "?role=ADMIN")
        assert response.status_code == status.HTTP_200_OK
        active = response.data["active_users"]["active_users"]
        roles = [p["role"] for p in active]
        assert all(r == "ADMIN" for r in roles)

    def test_create_user_validation_error(self, admin_client, org_a):
        """Creating user with duplicate email returns 400."""
        # First create a user that exists
        from common.models import User

        User.objects.create_user(email="existing@test.com", password="pass123")
        from common.models import Profile as ProfileModel

        ProfileModel.objects.create(
            user=User.objects.get(email="existing@test.com"),
            org=org_a,
            role="USER",
            is_active=True,
        )
        response = admin_client.post(
            self.url,
            {
                "email": "existing@test.com",
                "role": "USER",
                "phone": "+1111111111",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_user_non_admin_forbidden(self, user_client):
        """Non-admin user cannot create users."""
        response = user_client.post(
            self.url,
            {
                "email": "nope@test.com",
                "role": "USER",
                "phone": "+1111111112",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_user_empty_body(self, admin_client):
        """Empty POST body returns 400."""
        response = admin_client.post(
            self.url,
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserDetailView:
    """Tests for GET/PUT/PATCH/DELETE /api/user/<pk>/"""

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

    def test_get_user_detail_context(self, admin_client, admin_user):
        """User detail should return full profile data."""
        response = admin_client.get(self._url(admin_user.id))
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert "profile_obj" in data
        assert "opportunity_list" in data
        assert "contacts" in data
        assert "cases" in data
        assert "assigned_data" in data
        assert "comments" in data
        assert "countries" in data

    def test_get_user_detail_non_admin_own_profile(
        self, user_client, regular_user, user_profile
    ):
        """Non-admin can view their own profile."""
        response = user_client.get(self._url(regular_user.id))
        assert response.status_code == status.HTTP_200_OK

    def test_get_user_detail_non_admin_other_profile(
        self, user_client, admin_user, admin_profile, user_profile
    ):
        """Non-admin cannot view someone else's profile."""
        response = user_client.get(self._url(admin_user.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_non_admin_own(
        self, user_client, regular_user, user_profile
    ):
        """Non-admin can update their own profile."""
        response = user_client.put(
            self._url(regular_user.id),
            {
                "email": regular_user.email,
                "role": "USER",
                "phone": "+9876543210",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_user_non_admin_other(
        self, user_client, admin_user, admin_profile, user_profile
    ):
        """Non-admin cannot update someone else's profile."""
        response = user_client.put(
            self._url(admin_user.id),
            {
                "email": admin_user.email,
                "role": "USER",
                "phone": "+1111111111",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_user(self, admin_client, admin_user):
        """Test partial update via PATCH."""
        response = admin_client.patch(
            self._url(admin_user.id),
            {"phone": "+5555555555"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_patch_user_non_admin_other(
        self, user_client, admin_user, admin_profile, user_profile
    ):
        """Non-admin cannot patch someone else's profile."""
        response = user_client.patch(
            self._url(admin_user.id),
            {"phone": "+0000000000"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_as_admin(
        self, admin_client, org_a, regular_user, user_profile
    ):
        """Admin can delete another user."""
        response = admin_client.delete(self._url(regular_user.id))
        assert response.status_code == status.HTTP_200_OK

    def test_delete_user_self_forbidden(self, admin_client, admin_user):
        """Admin cannot delete themselves."""
        response = admin_client.delete(self._url(admin_user.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_non_admin_forbidden(
        self, user_client, admin_user, admin_profile, user_profile
    ):
        """Non-admin cannot delete users."""
        response = user_client.delete(self._url(admin_user.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserStatusView:
    """Tests for POST /api/user/<pk>/status/"""

    def _url(self, user_id):
        return f"/api/user/{user_id}/status/"

    def test_activate_user(
        self, admin_client, org_a, regular_user, user_profile
    ):
        """Admin can activate a user."""
        user_profile.is_active = False
        user_profile.save()
        response = admin_client.post(
            self._url(regular_user.id),
            {"status": "Active"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user_profile.refresh_from_db()
        assert user_profile.is_active is True

    def test_deactivate_user(
        self, admin_client, org_a, regular_user, user_profile
    ):
        """Admin can deactivate a user."""
        response = admin_client.post(
            self._url(regular_user.id),
            {"status": "Inactive"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user_profile.refresh_from_db()
        assert user_profile.is_active is False

    def test_invalid_status(
        self, admin_client, org_a, regular_user, user_profile
    ):
        """Invalid status value returns 400."""
        response = admin_client.post(
            self._url(regular_user.id),
            {"status": "InvalidStatus"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_status_non_admin_forbidden(
        self, user_client, org_a, admin_user, admin_profile, user_profile
    ):
        """Non-admin cannot change user status."""
        response = user_client.post(
            self._url(admin_user.id),
            {"status": "Inactive"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_status_returns_profiles(
        self, admin_client, org_a, regular_user, user_profile
    ):
        """Status endpoint should return active and inactive profiles."""
        response = admin_client.post(
            self._url(regular_user.id),
            {"status": "Active"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "active_profiles" in response.data
        assert "inactive_profiles" in response.data


@pytest.mark.django_db
class TestGetTeamsAndUsersView:
    """Tests for GET /api/users/get-teams-and-users/"""

    url = "/api/users/get-teams-and-users/"

    def test_get_teams_and_users(self, admin_client, org_a):
        """Returns teams and profiles for the org."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "teams" in response.data
        assert "profiles" in response.data
