"""
Tests for common/external_auth.py - APIKeyAuthentication.

Covers the authenticate() method: valid key, missing key, invalid key,
and missing admin profile scenarios.

Run with: pytest common/tests/test_external_auth.py -v
"""

import pytest
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed

from common.external_auth import APIKeyAuthentication
from common.models import Org, Profile, User


@pytest.mark.django_db
class TestAPIKeyAuthentication:
    """Tests for APIKeyAuthentication.authenticate()."""

    def setup_method(self):
        self.factory = RequestFactory()
        self.auth = APIKeyAuthentication()

    def test_no_token_header_returns_none(self):
        """Request without Token header should return None (pass to next auth)."""
        request = self.factory.get("/api/some-endpoint/")
        result = self.auth.authenticate(request)
        assert result is None

    def test_valid_api_key_returns_user(self, org_a, admin_user, admin_profile):
        """Valid API key should return (user, None) for an active admin profile."""
        request = self.factory.get(
            "/api/some-endpoint/", HTTP_TOKEN=org_a.api_key
        )
        user, auth = self.auth.authenticate(request)
        assert user == admin_user
        assert auth is None
        assert request.profile == admin_profile
        assert request.org == org_a
        assert request.META["org"] == str(org_a.id)

    def test_invalid_api_key_raises(self):
        """Invalid API key should raise AuthenticationFailed."""
        request = self.factory.get(
            "/api/some-endpoint/", HTTP_TOKEN="invalid-key-12345"
        )
        with pytest.raises(AuthenticationFailed, match="Invalid API Key"):
            self.auth.authenticate(request)

    def test_inactive_org_raises(self, org_a):
        """API key for inactive org should raise AuthenticationFailed."""
        org_a.is_active = False
        org_a.save()
        request = self.factory.get(
            "/api/some-endpoint/", HTTP_TOKEN=org_a.api_key
        )
        with pytest.raises(AuthenticationFailed, match="Invalid API Key"):
            self.auth.authenticate(request)

    def test_no_admin_profile_raises(self, org_a):
        """Org with no active admin profile should raise AuthenticationFailed."""
        # org_a exists but has no profiles at all
        request = self.factory.get(
            "/api/some-endpoint/", HTTP_TOKEN=org_a.api_key
        )
        with pytest.raises(AuthenticationFailed, match="Invalid API Key configuration"):
            self.auth.authenticate(request)

    def test_non_admin_profile_not_used(self, org_a, regular_user):
        """Org with only USER-role profiles should raise (no ADMIN profile)."""
        Profile.objects.create(
            user=regular_user, org=org_a, role="USER", is_active=True
        )
        request = self.factory.get(
            "/api/some-endpoint/", HTTP_TOKEN=org_a.api_key
        )
        with pytest.raises(AuthenticationFailed, match="Invalid API Key configuration"):
            self.auth.authenticate(request)

    def test_inactive_admin_profile_not_used(self, org_a, admin_user):
        """Inactive admin profile should not be returned."""
        Profile.objects.create(
            user=admin_user, org=org_a, role="ADMIN", is_active=False
        )
        request = self.factory.get(
            "/api/some-endpoint/", HTTP_TOKEN=org_a.api_key
        )
        with pytest.raises(AuthenticationFailed, match="Invalid API Key configuration"):
            self.auth.authenticate(request)
