"""
Tests for magic link authentication: request, verify, rate limiting, token expiry.

Run with: pytest common/tests/test_magic_link.py -v
"""

import secrets
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework import status

from common.models import MagicLinkToken, Profile, User


@pytest.mark.django_db
class TestMagicLinkRequest:
    """Tests for POST /api/auth/magic-link/request/"""

    url = "/api/auth/magic-link/request/"

    def test_request_returns_200_for_valid_email(self, unauthenticated_client):
        """Should always return 200 regardless of whether email exists."""
        with patch("common.tasks.send_magic_link_email") as mock_task:
            mock_task.delay = lambda *a: None
            response = unauthenticated_client.post(
                self.url, {"email": "anyone@example.com"}, format="json"
            )
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data

    def test_request_creates_token(self, unauthenticated_client):
        """Should create a MagicLinkToken record."""
        with patch("common.tasks.send_magic_link_email") as mock_task:
            mock_task.delay = lambda *a: None
            unauthenticated_client.post(
                self.url, {"email": "test@example.com"}, format="json"
            )
        assert MagicLinkToken.objects.filter(email="test@example.com").exists()

    def test_request_invalidates_previous_tokens(self, unauthenticated_client):
        """New request should invalidate existing unused tokens."""
        old_token = MagicLinkToken.objects.create(
            email="test@example.com",
            token=secrets.token_hex(32),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        with patch("common.tasks.send_magic_link_email") as mock_task:
            mock_task.delay = lambda *a: None
            unauthenticated_client.post(
                self.url, {"email": "test@example.com"}, format="json"
            )
        old_token.refresh_from_db()
        assert old_token.is_used is True

    def test_request_rate_limit(self, unauthenticated_client):
        """Should silently reject after 5 requests per hour."""
        email = "ratelimit@example.com"
        for _ in range(5):
            MagicLinkToken.objects.create(
                email=email,
                token=secrets.token_hex(32),
                expires_at=timezone.now() + timedelta(minutes=10),
            )
        with patch("common.tasks.send_magic_link_email") as mock_task:
            mock_task.delay = lambda *a: None
            unauthenticated_client.post(
                self.url, {"email": email}, format="json"
            )
        # Should still be exactly 5 tokens (no new one created due to rate limit)
        assert MagicLinkToken.objects.filter(email=email).count() == 5

    def test_request_invalid_email_format(self, unauthenticated_client):
        """Invalid email should still return 200 (no enumeration)."""
        response = unauthenticated_client.post(
            self.url, {"email": "not-an-email"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_request_missing_email(self, unauthenticated_client):
        """Missing email should still return 200 (no enumeration)."""
        response = unauthenticated_client.post(
            self.url, {}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestMagicLinkVerify:
    """Tests for POST /api/auth/magic-link/verify/"""

    url = "/api/auth/magic-link/verify/"

    def _create_valid_token(self, email="test@example.com"):
        return MagicLinkToken.objects.create(
            email=email,
            token=secrets.token_hex(32),
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def test_verify_valid_token_existing_user(self, unauthenticated_client, admin_user, admin_profile):
        """Valid token for existing user should return JWT tokens."""
        token_obj = self._create_valid_token(email=admin_user.email)
        response = unauthenticated_client.post(
            self.url, {"token": token_obj.token}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data
        assert "user" in response.data

    def test_verify_valid_token_new_user(self, unauthenticated_client):
        """Valid token for new email should create user and return tokens."""
        token_obj = self._create_valid_token(email="newuser@example.com")
        response = unauthenticated_client.post(
            self.url, {"token": token_obj.token}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert User.objects.filter(email="newuser@example.com").exists()
        user = User.objects.get(email="newuser@example.com")
        assert user.is_active is True

    def test_verify_marks_token_used(self, unauthenticated_client):
        """Token should be marked as used after verification."""
        token_obj = self._create_valid_token()
        unauthenticated_client.post(
            self.url, {"token": token_obj.token}, format="json"
        )
        token_obj.refresh_from_db()
        assert token_obj.is_used is True
        assert token_obj.used_at is not None

    def test_verify_used_token_rejected(self, unauthenticated_client):
        """Already used token should be rejected."""
        token_obj = self._create_valid_token()
        token_obj.is_used = True
        token_obj.save()
        response = unauthenticated_client.post(
            self.url, {"token": token_obj.token}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_expired_token_rejected(self, unauthenticated_client):
        """Expired token should be rejected."""
        token_obj = MagicLinkToken.objects.create(
            email="expired@example.com",
            token=secrets.token_hex(32),
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        response = unauthenticated_client.post(
            self.url, {"token": token_obj.token}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_invalid_token(self, unauthenticated_client):
        """Non-existent token should be rejected."""
        response = unauthenticated_client.post(
            self.url, {"token": "nonexistent-token-value"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_missing_token(self, unauthenticated_client):
        """Missing token field should be rejected."""
        response = unauthenticated_client.post(
            self.url, {}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_returns_org_for_existing_user(
        self, unauthenticated_client, admin_user, admin_profile, org_a
    ):
        """Existing user with org should get current_org in response."""
        token_obj = self._create_valid_token(email=admin_user.email)
        response = unauthenticated_client.post(
            self.url, {"token": token_obj.token}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "current_org" in response.data
        assert response.data["current_org"]["id"] == str(org_a.id)

    def test_verify_new_user_no_org(self, unauthenticated_client):
        """New user should not have current_org."""
        token_obj = self._create_valid_token(email="brand-new@example.com")
        response = unauthenticated_client.post(
            self.url, {"token": token_obj.token}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "current_org" not in response.data

    def test_verify_replay_attack_prevented(self, unauthenticated_client):
        """Same token should not work twice."""
        token_obj = self._create_valid_token()
        # First use
        response1 = unauthenticated_client.post(
            self.url, {"token": token_obj.token}, format="json"
        )
        assert response1.status_code == status.HTTP_200_OK
        # Second use (replay)
        response2 = unauthenticated_client.post(
            self.url, {"token": token_obj.token}, format="json"
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
