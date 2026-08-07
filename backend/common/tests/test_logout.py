"""
Signing out used to be a client-side gesture on both the web app and the phone.
Each cleared its own storage and told the user they were signed out, while the
refresh token stayed valid for its full fourteen days. A copy taken from a
shared machine, a device backup, or a proxy log kept minting access tokens for
a fortnight after the session was, as far as the user knew, over.

Rotation and blacklisting were already switched on. The endpoint to use them
was what was missing.

Run with: pytest common/tests/test_logout.py -v
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from common.serializer import OrgAwareRefreshToken

URL = "/api/auth/logout/"
REFRESH_URL = "/api/auth/refresh-token/"


def _tokens(user, org, profile):
    return OrgAwareRefreshToken.for_user_and_org(user, org, profile)


@pytest.mark.django_db
class TestSigningOutRevokes:
    """The whole point: after logout, the refresh token is dead."""

    def test_the_refresh_token_stops_working(self, admin_user, org_a, admin_profile):
        client = APIClient()
        token = _tokens(admin_user, org_a, admin_profile)

        # It works before, which is what makes the assertion after it mean
        # something. Without this line the test would pass against a broken
        # token factory.
        before = client.post(REFRESH_URL, {"refresh": str(token)}, format="json")
        assert before.status_code == status.HTTP_200_OK

        # The refreshed pair is the one a real client would now hold.
        live_refresh = before.data["refresh"]

        out = client.post(URL, {"refresh": live_refresh}, format="json")
        assert out.status_code == status.HTTP_200_OK

        after = client.post(REFRESH_URL, {"refresh": live_refresh}, format="json")
        assert after.status_code == status.HTTP_401_UNAUTHORIZED

    def test_it_works_without_an_access_token(self, admin_user, org_a, admin_profile):
        # The case the endpoint exists for. A phone that sat in a pocket
        # presses Sign Out with an access token that expired hours ago. If
        # logout demanded authentication it would fail here, leaving the
        # refresh token alive for the rest of its fourteen days.
        client = APIClient()  # no credentials set at all
        token = _tokens(admin_user, org_a, admin_profile)

        response = client.post(URL, {"refresh": str(token)}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert (
            client.post(REFRESH_URL, {"refresh": str(token)}, format="json").status_code
            == status.HTTP_401_UNAUTHORIZED
        )

    def test_signing_out_one_session_leaves_the_other_alone(
        self, admin_user, org_a, admin_profile
    ):
        # Signing out on the phone must not sign the user out of their desktop.
        # "Sign out everywhere" is a different feature, and building it by
        # accident here would be a surprise nobody asked for.
        client = APIClient()
        phone = _tokens(admin_user, org_a, admin_profile)
        desktop = _tokens(admin_user, org_a, admin_profile)

        client.post(URL, {"refresh": str(phone)}, format="json")

        still_good = client.post(REFRESH_URL, {"refresh": str(desktop)}, format="json")
        assert still_good.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestSigningOutIsSafeToRepeat:
    """A sign-out that errors is a sign-out the user retries or abandons."""

    def test_a_second_logout_still_reports_success(
        self, admin_user, org_a, admin_profile
    ):
        client = APIClient()
        token = str(_tokens(admin_user, org_a, admin_profile))
        client.post(URL, {"refresh": token}, format="json")

        # The state the caller asked for is already true. Answering 401 here
        # would make a client show a failure for a sign-out that succeeded.
        again = client.post(URL, {"refresh": token}, format="json")
        assert again.status_code == status.HTTP_200_OK

    def test_a_garbage_token_is_not_a_server_error(self):
        response = APIClient().post(URL, {"refresh": "not-a-jwt"}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_a_missing_token_is_a_bad_request(self):
        # Distinct from the above on purpose: no token at all is a client bug
        # worth surfacing, where an unusable token is the desired end state.
        response = APIClient().post(URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestSigningOutCannotReachAnotherSession:
    """Possession of the token is the authorization, so it must be checked."""

    def test_holding_one_users_token_does_not_revoke_anothers(
        self, admin_user, org_a, admin_profile, regular_user, user_profile
    ):
        client = APIClient()
        victim = _tokens(regular_user, org_a, user_profile)
        attacker = _tokens(admin_user, org_a, admin_profile)

        client.post(URL, {"refresh": str(attacker)}, format="json")

        # Revoking is scoped to the token presented, not to the user, the org,
        # or anything the caller could name in the body.
        survived = client.post(REFRESH_URL, {"refresh": str(victim)}, format="json")
        assert survived.status_code == status.HTTP_200_OK

    def test_a_body_naming_someone_else_changes_nothing(
        self, admin_user, org_a, admin_profile, regular_user, user_profile
    ):
        client = APIClient()
        victim = _tokens(regular_user, org_a, user_profile)

        # Server-derived identity: the view reads the token, never the body.
        response = client.post(
            URL,
            {
                "refresh": str(_tokens(admin_user, org_a, admin_profile)),
                "user_id": str(regular_user.id),
                "user": str(regular_user.id),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        survived = client.post(REFRESH_URL, {"refresh": str(victim)}, format="json")
        assert survived.status_code == status.HTTP_200_OK
