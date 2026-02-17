"""
Tests for API settings (domain) views: DomainList, DomainDetailView.

Run with: pytest common/tests/test_settings.py -v
"""

import pytest
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from common.models import APISettings


@pytest.mark.django_db
class TestDomainListView:
    """Tests for GET/POST /api/api-settings/"""

    url = "/api/api-settings/"

    def test_list_api_settings(self, admin_client, org_a):
        """Get list of API settings."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "api_settings" in response.data
        assert "users" in response.data

    def test_create_api_setting(self, admin_client, org_a):
        """Create a new API setting."""
        response = admin_client.post(
            self.url,
            {"title": "Test API", "website": "https://example.com"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["error"] is False

    def test_create_api_setting_invalid_website(self, admin_client, org_a):
        """Creating API setting with invalid website should fail."""
        response = admin_client.post(
            self.url,
            {"title": "Bad API", "website": "not-a-url"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated(self, unauthenticated_client):
        """Unauthenticated user gets PermissionDenied."""
        with pytest.raises(PermissionDenied):
            unauthenticated_client.get(self.url)


@pytest.mark.django_db
class TestDomainDetailView:
    """Tests for GET/PUT/PATCH/DELETE /api/api-settings/<pk>/"""

    def _url(self, pk):
        return f"/api/api-settings/{pk}/"

    def _create_setting(self, org, user):
        return APISettings.objects.create(
            title="Test Setting",
            website="https://test.com",
            org=org,
            created_by=user,
        )

    def test_get_api_setting(self, admin_client, org_a, admin_user):
        """Get a single API setting."""
        setting = self._create_setting(org_a, admin_user)
        response = admin_client.get(self._url(setting.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "domain" in response.data

    def test_update_api_setting(self, admin_client, org_a, admin_user):
        """Update an API setting."""
        setting = self._create_setting(org_a, admin_user)
        response = admin_client.put(
            self._url(setting.pk),
            {"title": "Updated Setting", "website": "https://updated.com"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_delete_api_setting(self, admin_client, org_a, admin_user):
        """Delete an API setting."""
        setting = self._create_setting(org_a, admin_user)
        response = admin_client.delete(self._url(setting.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert not APISettings.objects.filter(pk=setting.pk).exists()

    def test_patch_api_setting(self, admin_client, org_a, admin_user):
        """Partial update via PATCH."""
        setting = self._create_setting(org_a, admin_user)
        response = admin_client.patch(
            self._url(setting.pk),
            {"title": "Patched Title"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_get_api_setting_cross_org(
        self, org_b_client, org_a, admin_user, admin_profile
    ):
        """Cross-org access should return 404."""
        setting = self._create_setting(org_a, admin_user)
        response = org_b_client.get(self._url(setting.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND
