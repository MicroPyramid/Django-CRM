"""
Tests for authentication views: login, register, me, token refresh, org switch,
Google OAuth callback, Google ID token, and token refresh edge cases.

Run with: pytest common/tests/test_auth.py -v
"""

import base64
import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

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
        Profile.objects.create(
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

    def test_login_missing_email(self, unauthenticated_client):
        """Login without email should fail."""
        response = unauthenticated_client.post(
            self.url,
            {"password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_password(self, unauthenticated_client, admin_user):
        """Login without password should fail."""
        response = unauthenticated_client.post(
            self.url,
            {"email": "admin@test.com"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_empty_body(self, unauthenticated_client):
        """Login with empty body should fail."""
        response = unauthenticated_client.post(
            self.url,
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_user_data_returned(
        self, unauthenticated_client, admin_user, admin_profile
    ):
        """Login should return user details."""
        response = unauthenticated_client.post(
            self.url,
            {"email": "admin@test.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user_data = response.data["user"]
        assert "email" in user_data
        assert user_data["email"] == "admin@test.com"

    def test_login_user_no_org(self, unauthenticated_client):
        """Login for user without any org should return tokens without current_org."""
        User.objects.create_user(email="orphan@test.com", password="testpass123")
        response = unauthenticated_client.post(
            self.url,
            {"email": "orphan@test.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "current_org" not in response.data


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

    def test_register_password_mismatch(self, unauthenticated_client):
        """Mismatched passwords should fail."""
        response = unauthenticated_client.post(
            self.url,
            {
                "email": "mismatch@test.com",
                "password": "securepass123",
                "confirm_password": "differentpass",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password(self, unauthenticated_client):
        """Too short a password should fail validation."""
        response = unauthenticated_client.post(
            self.url,
            {
                "email": "short@test.com",
                "password": "short",
                "confirm_password": "short",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_email(self, unauthenticated_client):
        """Invalid email format should fail."""
        response = unauthenticated_client.post(
            self.url,
            {
                "email": "not-an-email",
                "password": "securepass123",
                "confirm_password": "securepass123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_created_user_is_inactive(self, unauthenticated_client):
        """Registered user should be inactive by default."""
        response = unauthenticated_client.post(
            self.url,
            {
                "email": "inactive@test.com",
                "password": "securepass123",
                "confirm_password": "securepass123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="inactive@test.com")
        assert user.is_active is False


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

    def test_me_returns_organizations(self, admin_client, admin_user, admin_profile, org_a):
        """Me endpoint should include user's organizations."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "organizations" in response.data
        org_ids = [o["id"] for o in response.data["organizations"]]
        assert str(org_a.id) in org_ids


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

    def test_refresh_missing_token(self, unauthenticated_client):
        """Missing refresh token should fail."""
        response = unauthenticated_client.post(
            self.url,
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_refresh_token_without_org(self, unauthenticated_client, admin_user):
        """Refresh token without org context should still work."""
        token = OrgAwareRefreshToken.for_user_and_org(admin_user, None)
        response = unauthenticated_client.post(
            self.url,
            {"refresh": str(token)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_revoked_membership(
        self, unauthenticated_client, admin_user, org_a, admin_profile
    ):
        """Refreshing token after org membership is revoked should fail."""
        token = OrgAwareRefreshToken.for_user_and_org(admin_user, org_a, admin_profile)
        # Deactivate the profile (revoke membership)
        admin_profile.is_active = False
        admin_profile.save()
        response = unauthenticated_client.post(
            self.url,
            {"refresh": str(token)},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_refresh_inactive_user(
        self, unauthenticated_client, admin_user, org_a, admin_profile
    ):
        """Refreshing token for an inactive user should fail."""
        token = OrgAwareRefreshToken.for_user_and_org(admin_user, org_a, admin_profile)
        admin_user.is_active = False
        admin_user.save()
        response = unauthenticated_client.post(
            self.url,
            {"refresh": str(token)},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


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

    def test_switch_org_returns_profile(self, admin_client, admin_user, org_b):
        """Switch org should return profile details."""
        Profile.objects.create(
            user=admin_user, org=org_b, role="USER", is_active=True
        )
        response = admin_client.post(
            self.url,
            {"org_id": str(org_b.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "profile" in response.data
        assert response.data["profile"]["role"] == "USER"

    def test_switch_org_returns_tokens(self, admin_client, admin_user, org_b):
        """Switch org should return new access and refresh tokens."""
        Profile.objects.create(
            user=admin_user, org=org_b, role="ADMIN", is_active=True
        )
        response = admin_client.post(
            self.url,
            {"org_id": str(org_b.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data

    def test_switch_org_unauthenticated(self, unauthenticated_client, org_a):
        """Unauthenticated user cannot switch org."""
        response = unauthenticated_client.post(
            self.url,
            {"org_id": str(org_a.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfileDetailView:
    """Tests for GET /api/auth/profile/"""

    url = "/api/auth/profile/"

    def test_profile_detail_authenticated(self, admin_client, admin_profile, org_a):
        """Authenticated user with org context gets profile details."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "ADMIN"
        assert str(response.data["org"]["id"]) == str(org_a.id)

    def test_profile_detail_unauthenticated(self, unauthenticated_client):
        """Unauthenticated user gets error (401 or PermissionDenied from middleware)."""
        with pytest.raises((PermissionDenied, Exception)):
            unauthenticated_client.get(self.url)


# ---------------------------------------------------------------------------
# Google OAuth Callback View tests (lines 52-137)
# ---------------------------------------------------------------------------


def _make_fake_id_token(email, picture="https://photo.example.com/pic.jpg"):
    """Create a fake JWT-like ID token with the given email in the payload."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(
        json.dumps({"email": email, "picture": picture}).encode()
    ).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"fakesig").decode().rstrip("=")
    return f"{header}.{payload}.{signature}"


@pytest.mark.django_db
class TestGoogleOAuthCallbackView:
    """Tests for POST /api/auth/google/callback/"""

    url = "/api/auth/google/callback/"

    def test_missing_parameters(self, unauthenticated_client):
        """Missing code/code_verifier/redirect_uri should return 400."""
        response = unauthenticated_client.post(
            self.url, {"code": "test"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing required parameters" in response.data["error"]

    @patch("common.views.auth_views.requests.post")
    def test_google_request_exception(self, mock_post, unauthenticated_client):
        """Network error communicating with Google should return 502."""
        import requests as req_lib

        mock_post.side_effect = req_lib.RequestException("Connection error")
        response = unauthenticated_client.post(
            self.url,
            {
                "code": "authcode",
                "code_verifier": "verifier",
                "redirect_uri": "http://localhost:3000/callback",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    @patch("common.views.auth_views.requests.post")
    def test_google_token_exchange_failure(self, mock_post, unauthenticated_client):
        """Non-200 from Google token endpoint should return 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.content = b'{"error_description": "invalid_grant"}'
        mock_response.json.return_value = {"error_description": "invalid_grant"}
        mock_post.return_value = mock_response

        response = unauthenticated_client.post(
            self.url,
            {
                "code": "badcode",
                "code_verifier": "verifier",
                "redirect_uri": "http://localhost:3000/callback",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid_grant" in response.data["error"]

    @patch("common.views.auth_views.requests.post")
    def test_missing_id_token(self, mock_post, unauthenticated_client):
        """Response without id_token should return 400."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "at"}
        mock_post.return_value = mock_response

        response = unauthenticated_client.post(
            self.url,
            {
                "code": "authcode",
                "code_verifier": "verifier",
                "redirect_uri": "http://localhost:3000/callback",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No ID token" in response.data["error"]

    @patch("common.views.auth_views.requests.post")
    def test_invalid_id_token_format(self, mock_post, unauthenticated_client):
        """Malformed id_token should return 400."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id_token": "not-a-jwt"}
        mock_post.return_value = mock_response

        response = unauthenticated_client.post(
            self.url,
            {
                "code": "authcode",
                "code_verifier": "verifier",
                "redirect_uri": "http://localhost:3000/callback",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid ID token" in response.data["error"]

    @patch("common.views.auth_views.requests.post")
    def test_no_email_in_token(self, mock_post, unauthenticated_client):
        """ID token without email should return 400."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Build a token without email
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "123"}).encode()).decode().rstrip("=")
        header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode()).decode().rstrip("=")
        sig = base64.urlsafe_b64encode(b"sig").decode().rstrip("=")
        mock_response.json.return_value = {"id_token": f"{header}.{payload}.{sig}"}
        mock_post.return_value = mock_response

        response = unauthenticated_client.post(
            self.url,
            {
                "code": "authcode",
                "code_verifier": "verifier",
                "redirect_uri": "http://localhost:3000/callback",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No email" in response.data["error"]

    @patch("common.views.auth_views.requests.post")
    def test_successful_oauth_new_user(self, mock_post, unauthenticated_client):
        """Successful OAuth should create user and return tokens."""
        fake_token = _make_fake_id_token("newgoogle@example.com")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id_token": fake_token, "access_token": "at"}
        mock_post.return_value = mock_response

        response = unauthenticated_client.post(
            self.url,
            {
                "code": "authcode",
                "code_verifier": "verifier",
                "redirect_uri": "http://localhost:3000/callback",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data
        assert response.data["user"]["email"] == "newgoogle@example.com"
        # Verify user was created
        assert User.objects.filter(email="newgoogle@example.com").exists()

    @patch("common.views.auth_views.requests.post")
    def test_successful_oauth_existing_user(self, mock_post, unauthenticated_client, admin_user):
        """Successful OAuth with existing user should return tokens without creating new user."""
        fake_token = _make_fake_id_token(admin_user.email)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id_token": fake_token, "access_token": "at"}
        mock_post.return_value = mock_response

        user_count_before = User.objects.count()
        response = unauthenticated_client.post(
            self.url,
            {
                "code": "authcode",
                "code_verifier": "verifier",
                "redirect_uri": "http://localhost:3000/callback",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert User.objects.count() == user_count_before

    @patch("common.views.auth_views.requests.post")
    def test_token_exchange_failure_empty_content(self, mock_post, unauthenticated_client):
        """Non-200 with empty content body should return generic error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b""
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        response = unauthenticated_client.post(
            self.url,
            {
                "code": "badcode",
                "code_verifier": "verifier",
                "redirect_uri": "http://localhost:3000/callback",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Google ID Token View tests (lines 173-232)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGoogleIdTokenView:
    """Tests for POST /api/auth/google/"""

    url = "/api/auth/google/"

    def test_missing_id_token(self, unauthenticated_client):
        """Missing idToken should return 400."""
        response = unauthenticated_client.post(
            self.url, {}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing idToken" in response.data["error"]

    @patch("google.oauth2.id_token.verify_oauth2_token")
    @patch("google.auth.transport.requests.Request")
    def test_invalid_token(self, mock_request_cls, mock_verify, unauthenticated_client):
        """Invalid Google token should return 400."""
        mock_verify.side_effect = ValueError("Invalid token")
        response = unauthenticated_client.post(
            self.url, {"idToken": "bad-token"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid token" in response.data["error"]

    @patch("google.oauth2.id_token.verify_oauth2_token")
    @patch("google.auth.transport.requests.Request")
    def test_no_email_in_verified_token(self, mock_request_cls, mock_verify, unauthenticated_client):
        """Token without email claim should return 400."""
        mock_verify.return_value = {"sub": "12345"}
        response = unauthenticated_client.post(
            self.url, {"idToken": "valid-but-no-email"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No email" in response.data["error"]

    @patch("google.oauth2.id_token.verify_oauth2_token")
    @patch("google.auth.transport.requests.Request")
    def test_successful_new_user(self, mock_request_cls, mock_verify, unauthenticated_client):
        """Valid token with new email should create user and return JWT."""
        mock_verify.return_value = {
            "email": "mobileuser@example.com",
            "picture": "https://photo.example.com/pic.jpg",
        }
        response = unauthenticated_client.post(
            self.url, {"idToken": "valid-token"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "JWTtoken" in response.data
        assert response.data["user"]["email"] == "mobileuser@example.com"
        assert User.objects.filter(email="mobileuser@example.com").exists()

    @patch("google.oauth2.id_token.verify_oauth2_token")
    @patch("google.auth.transport.requests.Request")
    def test_successful_existing_user_with_orgs(
        self, mock_request_cls, mock_verify, unauthenticated_client, admin_user, admin_profile, org_a
    ):
        """Existing user should get their organizations in response."""
        mock_verify.return_value = {
            "email": admin_user.email,
            "picture": "https://photo.example.com/pic.jpg",
        }
        response = unauthenticated_client.post(
            self.url, {"idToken": "valid-token"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["organizations"]) == 1
        assert response.data["organizations"][0]["id"] == str(org_a.id)


# ---------------------------------------------------------------------------
# Token refresh - User.DoesNotExist edge case (lines 503-504)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTokenRefreshUserNotFound:
    """Test token refresh when user has been deleted."""

    url = "/api/auth/refresh-token/"

    def test_refresh_deleted_user(self, unauthenticated_client, admin_user, org_a, admin_profile):
        """Refreshing token for a deleted user should return 401."""
        token = OrgAwareRefreshToken.for_user_and_org(admin_user, org_a, admin_profile)
        token_str = str(token)
        # Delete the user
        admin_user.delete()
        response = unauthenticated_client.post(
            self.url,
            {"refresh": token_str},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found" in response.data["error"]
