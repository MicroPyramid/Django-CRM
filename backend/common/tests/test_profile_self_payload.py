"""What `/api/auth/profile/` tells you about yourself, and about nobody else.

The mobile profile screen reads this endpoint and the web one reads
`/api/profile/`, so the two described the same person differently: teams and
last sign-in were on one and not the other. Both are here now, and both are
only ever the caller's own.
"""

import pytest

from common.models import Teams

URL = "/api/auth/profile/"


@pytest.mark.django_db
class TestSelfProfilePayload:
    def test_lists_the_teams_you_are_on(self, user_client, user_profile, org_a):
        team = Teams.objects.create(name="Support", org=org_a)
        team.users.add(user_profile)
        response = user_client.get(URL)
        assert response.status_code == 200
        assert response.json()["teams"] == ["Support"]

    def test_a_team_you_are_not_on_is_absent(self, user_client, admin_profile, org_a):
        team = Teams.objects.create(name="Finance", org=org_a)
        team.users.add(admin_profile)
        response = user_client.get(URL)
        assert response.json()["teams"] == []

    def test_carries_your_own_last_sign_in(self, user_client, regular_user):
        response = user_client.get(URL)
        assert "last_login" in response.json()

    def test_the_shared_profile_serializer_still_says_nothing_about_sign_ins(
        self, admin_client, user_profile
    ):
        """`ProfileSerializer` is nested into lists of OTHER people.

        Widening it the way this one was widened would publish when every
        colleague last signed in, which is why only the self endpoint carries
        it. `user_details` has always held `last_login`, and that is a
        pre-existing question, not one this change opens; what matters here is
        that the top-level field did not spread.
        """
        response = admin_client.get("/api/users/")
        assert response.status_code == 200
        rows = response.json().get("active_users", {}).get("active_users", [])
        assert all("last_login" not in row for row in rows)

    def test_unauthenticated_is_refused(self, unauthenticated_client):
        # 403 rather than 401: the middleware refuses on the missing org
        # context before DRF gets to say the caller is unauthenticated.
        assert unauthenticated_client.get(URL).status_code == 403
