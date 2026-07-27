"""
Tests for user management views: list users, user detail, update user, status.

Run with: pytest common/tests/test_users.py -v
"""

import pytest
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from common.models import Address, Profile


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

    def test_create_user_minimal_payload(self, admin_client, org_a):
        """Admin can create a user with just email and role."""
        response = admin_client.post(
            self.url,
            {
                "email": "new-member@test.com",
                "role": "USER",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Profile.objects.filter(
            user__email="new-member@test.com", org=org_a
        ).exists()

    def test_create_user_minimal_payload_creates_no_address(self, admin_client, org_a):
        """No address fields sent -> no empty Address row is created."""
        response = admin_client.post(
            self.url,
            {"email": "no-address@test.com", "role": "USER"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        profile = Profile.objects.get(user__email="no-address@test.com", org=org_a)
        assert profile.address is None

    def test_create_user_with_address_scopes_address_to_org(self, admin_client, org_a):
        """Address fields sent -> Address is created and scoped to the admin's org."""
        response = admin_client.post(
            self.url,
            {
                "email": "with-address@test.com",
                "role": "USER",
                "city": "Hyderabad",
                "country": "IN",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        profile = Profile.objects.get(user__email="with-address@test.com", org=org_a)
        assert profile.address is not None
        assert profile.address.city == "Hyderabad"
        assert profile.address.org == org_a

    def test_create_user_reuses_existing_account_from_another_org(
        self, admin_client, org_a, org_b
    ):
        """Inviting an email that already has an account adds a Profile, not a 400."""
        from common.models import User

        existing = User.objects.create_user(
            email="veteran@test.com", password="pass123"
        )
        Profile.objects.create(user=existing, org=org_b, role="USER", is_active=True)

        response = admin_client.post(
            self.url,
            {"email": "veteran@test.com", "role": "USER"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        # Same underlying account, now a member of both orgs.
        assert User.objects.filter(email="veteran@test.com").count() == 1
        new_profile = Profile.objects.get(user=existing, org=org_a)
        assert new_profile.role == "USER"
        assert Profile.objects.filter(user=existing, org=org_b).exists()

    def test_create_user_reuse_does_not_mutate_existing_account(
        self, admin_client, org_a, org_b
    ):
        """Inviting an existing account must not touch that account's own fields."""
        from common.models import User

        existing = User.objects.create_user(
            email="dormant@test.com", password="pass123"
        )
        existing.name = "Original Name"
        existing.profile_pic = "original.png"
        existing.is_active = False
        existing.save()
        Profile.objects.create(user=existing, org=org_b, role="ADMIN", is_active=True)

        response = admin_client.post(
            self.url,
            {
                "email": "dormant@test.com",
                "role": "USER",
                "profile_pic": "attacker.png",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        existing.refresh_from_db()
        assert existing.name == "Original Name"
        assert existing.profile_pic == "original.png"
        # A deactivated account must not be silently re-enabled by an invite.
        assert existing.is_active is False

    def test_create_user_losing_race_returns_400_not_500(self, admin_client, org_a):
        """A concurrent invite that wins the DB race yields 400, never a 500."""
        from unittest.mock import patch

        from django.db import IntegrityError

        # Stands in for a second request that committed the same membership
        # between this request's validation and its INSERT.
        with patch.object(
            Profile.objects, "create", side_effect=IntegrityError("duplicate key")
        ):
            response = admin_client.post(
                self.url,
                {"email": "raced@test.com", "role": "USER"},
                format="json",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_user_rolls_back_account_when_membership_fails(
        self, admin_client, org_a
    ):
        """A failed invite must not strand a half-built account behind it."""
        from unittest.mock import patch

        from django.db import IntegrityError

        from common.models import User

        with patch.object(
            Profile.objects, "create", side_effect=IntegrityError("duplicate key")
        ):
            admin_client.post(
                self.url,
                {"email": "orphan@test.com", "role": "USER", "city": "Hyderabad"},
                format="json",
            )

        assert not User.objects.filter(email="orphan@test.com").exists()
        assert not Address.objects.filter(city="Hyderabad").exists()

    def test_create_user_duplicate_within_same_org_rejected(self, admin_client, org_a):
        """Re-inviting someone who is already a member of this org still 400s."""
        from common.models import User

        member = User.objects.create_user(email="member@test.com", password="pass123")
        Profile.objects.create(user=member, org=org_a, role="USER", is_active=True)

        response = admin_client.post(
            self.url,
            {"email": "member@test.com", "role": "USER"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Profile.objects.filter(user=member, org=org_a).count() == 1


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

    def test_patch_user_email_taken_by_another_account(
        self, admin_client, org_a, org_b, regular_user, user_profile
    ):
        """Renaming a user onto an email another account owns is a clean 400."""
        from common.models import User

        other = User.objects.create_user(email="taken@test.com", password="pass123")
        Profile.objects.create(user=other, org=org_b, role="USER", is_active=True)

        response = admin_client.patch(
            self._url(regular_user.id),
            {"email": "taken@test.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        regular_user.refresh_from_db()
        assert regular_user.email != "taken@test.com"

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
