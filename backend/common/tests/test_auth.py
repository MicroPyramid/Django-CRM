"""
Tests for authentication views: login, register, me, token refresh, org switch.

Run with: pytest common/tests/test_auth.py -v
"""

import pytest
from rest_framework import status

from common.models import Org, Profile, User
from common.serializer import OrgAwareRefreshToken


@pytest.mark.django_db
class TestLoginView:
    """Tests for POST /api/auth/login/"""

    url = "/api/auth/login/"

    def test_login_success(self, unauthenticated_client, admin_user, admin_profile):
        response = unauthenticated_client.post(
            self.url,
            {"email": "admin@test.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data
        assert "current_org" in response.data

    def test_login_wrong_password(self, unauthenticated_client, admin_user, admin_profile):
        response = unauthenticated_client.post(
            self.url,
            {"email": "admin@test.com", "password": "wrongpassword"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, unauthenticated_client):
        response = unauthenticated_client.post(
            self.url,
            {"email": "nobody@test.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_returns_tokens_and_org(
        self, unauthenticated_client, admin_user, admin_profile, org_a
    ):
        response = unauthenticated_client.post(
            self.url,
            {"email": "admin@test.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert "current_org" in data
        assert data["current_org"]["id"] == str(org_a.id)

    def test_login_with_specific_org(self, unauthenticated_client, admin_user, org_b):
        # Give admin_user access to org_b
        profile_b = Profile.objects.create(
            user=admin_user, org=org_b, role="USER", is_active=True
        )
        response = unauthenticated_client.post(
            self.url,
            {
                "email": "admin@test.com",
                "password": "testpass123",
                "org_id": str(org_b.id),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["current_org"]["id"] == str(org_b.id)

    def test_login_unauthorized_org(
        self, unauthenticated_client, admin_user, admin_profile, org_b
    ):
        # admin_user does NOT have a profile in org_b
        response = unauthenticated_client.post(
            self.url,
            {
                "email": "admin@test.com",
                "password": "testpass123",
                "org_id": str(org_b.id),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestRegisterView:
    """Tests for POST /api/auth/register/"""

    url = "/api/auth/register/"

    def test_register_success(self, unauthenticated_client):
        response = unauthenticated_client.post(
            self.url,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "confirm_password": "securepass123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "user_id" in response.data
        assert response.data["email"] == "newuser@test.com"

    def test_register_duplicate_email(self, unauthenticated_client, admin_user):
        response = unauthenticated_client.post(
            self.url,
            {
                "email": "admin@test.com",
                "password": "securepass123",
                "confirm_password": "securepass123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_fields(self, unauthenticated_client):
        response = unauthenticated_client.post(
            self.url,
            {"email": "newuser@test.com"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMeView:
    """Tests for GET /api/auth/me/"""

    url = "/api/auth/me/"

    def test_me_authenticated(self, admin_client, admin_user):
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == admin_user.email

    def test_me_unauthenticated(self, unauthenticated_client):
        response = unauthenticated_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefreshView:
    """Tests for POST /api/auth/refresh-token/"""

    url = "/api/auth/refresh-token/"

    def test_refresh_valid_token(
        self, unauthenticated_client, admin_user, org_a, admin_profile
    ):
        token = OrgAwareRefreshToken.for_user_and_org(admin_user, org_a, admin_profile)
        response = unauthenticated_client.post(
            self.url,
            {"refresh": str(token)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_refresh_invalid_token(self, unauthenticated_client):
        response = unauthenticated_client.post(
            self.url,
            {"refresh": "invalid-token-string"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOrgSwitchView:
    """Tests for POST /api/auth/switch-org/"""

    url = "/api/auth/switch-org/"

    def test_switch_org_success(self, admin_client, admin_user, org_b):
        # Give admin_user access to org_b
        Profile.objects.create(
            user=admin_user, org=org_b, role="USER", is_active=True
        )
        response = admin_client.post(
            self.url,
            {"org_id": str(org_b.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["current_org"]["id"] == str(org_b.id)

    def test_switch_to_unauthorized_org(self, admin_client, org_b):
        # admin_user does NOT have a profile in org_b
        response = admin_client.post(
            self.url,
            {"org_id": str(org_b.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_switch_org_missing_org_id(self, admin_client):
        response = admin_client.post(
            self.url,
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
