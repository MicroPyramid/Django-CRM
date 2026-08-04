"""``HasOrgContext`` on the three user-management views.

``UsersListView``, ``UserDetailView`` and ``UserStatusView`` each read
``request.profile`` unconditionally: ``request.profile.role`` for the admin
check, ``request.profile.org`` for the object lookup. ``GetProfileAndOrg``
leaves ``request.profile`` as ``None`` whenever the JWT carries no ``org_id``
claim, or carries one the caller is no longer a member of, so every one of
those reads was an ``AttributeError`` on a stale token: a 500 where the answer
should have been a 403.

This is not a tenant leak. The middleware already requires ``is_active=True``
before it sets ``request.profile`` (``common/middleware/get_company.py``), so a
deactivated profile never reached these views to begin with. What was missing
was the clean refusal.

Both directions are asserted, since a permission class that cannot return
``False`` is decoration and one that cannot return ``True`` is an outage.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from common.models import Profile


def _client_without_org_claim(user):
    """A client whose JWT authenticates but names no org.

    This is the shape a token has between login and picking an org, and the
    shape a stale token keeps after its membership is revoked.
    """
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.mark.django_db
class TestUsersListViewOrgContext:
    url = "/api/users/"

    def test_without_org_context_it_is_refused_not_crashed(self, admin_user):
        response = _client_without_org_claim(admin_user).get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_with_org_context_an_admin_still_gets_through(self, admin_client):
        """The False direction is worthless without this one beside it."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_post_without_org_context_is_refused(self, admin_user):
        response = _client_without_org_claim(admin_user).post(
            self.url, {"email": "x@test.com", "role": "USER"}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserDetailViewOrgContext:
    def test_without_org_context_it_is_refused_not_crashed(
        self, admin_user, admin_profile
    ):
        client = _client_without_org_claim(admin_user)
        response = client.get(f"/api/user/{admin_user.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_with_org_context_an_admin_still_gets_through(
        self, admin_client, admin_user, admin_profile
    ):
        response = admin_client.get(f"/api/user/{admin_user.id}/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserStatusViewOrgContext:
    def test_without_org_context_it_is_refused_not_crashed(
        self, admin_user, user_profile
    ):
        client = _client_without_org_claim(admin_user)
        response = client.post(
            f"/api/user/{user_profile.user.id}/status/",
            {"status": "Inactive"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_with_org_context_an_admin_still_gets_through(
        self, admin_client, user_profile
    ):
        response = admin_client.post(
            f"/api/user/{user_profile.user.id}/status/",
            {"status": "Inactive"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user_profile.refresh_from_db()
        assert Profile.objects.get(pk=user_profile.pk).is_active is False
