"""
Tests for organization management views: OrgProfileCreateView, OrgUpdateView,
ProfileView, ProfileDetailView, OrgSettingsView.

Run with: pytest common/tests/test_organizations.py -v
"""

import pytest
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from common.models import Org, Profile


@pytest.mark.django_db
class TestOrgProfileCreateView:
    """Tests for GET/POST /api/org/"""

    url = "/api/org/"

    def test_create_org(self, admin_client, admin_user):
        """Create a new organization."""
        response = admin_client.post(
            self.url,
            {"name": "New Organization"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "org" in response.data
        # User should be an admin of the new org
        assert Profile.objects.filter(
            user=admin_user, org__name="New Organization", role="ADMIN"
        ).exists()

    def test_create_org_special_chars(self, admin_client):
        """Organization name with special characters should fail."""
        response = admin_client.post(
            self.url,
            {"name": "Bad@Name!"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_org_duplicate_name(self, admin_client, org_a):
        """Creating org with duplicate name should fail."""
        response = admin_client.post(
            self.url,
            {"name": org_a.name},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_orgs(self, admin_client, admin_user, admin_profile, org_a):
        """List organizations the user belongs to."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "profile_org_list" in response.data
        org_names = [
            p["org"]["name"] for p in response.data["profile_org_list"]
        ]
        assert org_a.name in org_names

    def test_list_orgs_unauthenticated(self, unauthenticated_client):
        """Unauthenticated user gets 401."""
        response = unauthenticated_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOrgUpdateView:
    """Tests for GET/PUT/PATCH /api/org/<pk>/"""

    def _url(self, pk):
        return f"/api/org/{pk}/"

    def test_get_org(self, admin_client, org_a):
        """Get organization details."""
        response = admin_client.get(self._url(org_a.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "org" in response.data

    def test_update_org(self, admin_client, org_a):
        """Admin can update organization."""
        response = admin_client.put(
            self._url(org_a.id),
            {"name": "Updated Org Name"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        org_a.refresh_from_db()
        assert org_a.name == "Updated Org Name"

    def test_update_org_non_admin_forbidden(
        self, user_client, org_a, user_profile
    ):
        """Non-admin user cannot update organization."""
        response = user_client.put(
            self._url(org_a.id),
            {"name": "Nope"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_different_org_forbidden(
        self, admin_client, org_b
    ):
        """Cannot update a different organization."""
        response = admin_client.put(
            self._url(org_b.id),
            {"name": "Cross Org Update"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_org(self, admin_client, org_a):
        """Partial update of organization via PATCH."""
        response = admin_client.patch(
            self._url(org_a.id),
            {"name": "Patched Org"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_patch_org_non_admin_forbidden(
        self, user_client, org_a, user_profile
    ):
        """Non-admin cannot PATCH organization."""
        response = user_client.patch(
            self._url(org_a.id),
            {"name": "No Patch"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_different_org_forbidden(self, admin_client, org_b):
        """Cannot get a different organization's details."""
        response = admin_client.get(self._url(org_b.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProfileView:
    """Tests for GET/PATCH /api/profile/"""

    url = "/api/profile/"

    def test_get_profile(self, admin_client, admin_profile):
        """Get current user's profile."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "user_obj" in response.data

    def test_patch_profile_phone(self, admin_client, admin_profile):
        """Update phone via PATCH."""
        response = admin_client.patch(
            self.url,
            {"phone": "+9876543210"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "user_obj" in response.data
        admin_profile.refresh_from_db()
        assert admin_profile.phone == "+9876543210"


@pytest.mark.django_db
class TestOrgSettingsView:
    """Tests for GET/PATCH /api/org/settings/"""

    url = "/api/org/settings/"

    def test_get_org_settings(self, admin_client, org_a):
        """Get organization settings."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "default_currency" in response.data
        assert "currency_symbol" in response.data

    def test_patch_org_settings(self, admin_client, org_a):
        """Admin can update organization settings."""
        response = admin_client.patch(
            self.url,
            {"default_currency": "EUR"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        org_a.refresh_from_db()
        assert org_a.default_currency == "EUR"

    def test_patch_org_settings_non_admin_forbidden(
        self, user_client, org_a, user_profile
    ):
        """Non-admin cannot update organization settings."""
        response = user_client.patch(
            self.url,
            {"default_currency": "GBP"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_org_settings_company_name(self, admin_client, org_a):
        """Update company name in org settings."""
        response = admin_client.patch(
            self.url,
            {"company_name": "ACME Corp"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        org_a.refresh_from_db()
        assert org_a.company_name == "ACME Corp"
