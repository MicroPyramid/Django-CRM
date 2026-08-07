"""Org-wide token oversight, the admin's cross-user view and revoke.

Distinct from test_pat_api.py, which covers the SELF-scoped /profile/tokens/
endpoints. These endpoints (/org/tokens/) are the admin oversight half added
for the /v2/settings/api-tokens page: read every token in the org, revoke any
of them. Every rule is asserted both ways, the allowed path AND the forbidden
one, because personal_access_token has no RLS, so the explicit org filter and
the IsOrgAdmin gate are the only barriers and a silent regression in either
would leak or let through cross-tenant/cross-role access.
"""

import uuid
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from common.models import PersonalAccessToken

LIST_URL = "/api/org/tokens/"


def _detail_url(pk):
    return f"/api/org/tokens/{pk}/"


@pytest.mark.django_db
class TestOrgTokenList:
    def test_admin_sees_every_owner_in_org(
        self, admin_client, admin_profile, user_profile
    ):
        # Two owners, one org. The self-scoped list would show only the admin's;
        # this oversight list must show both.
        _, mine = PersonalAccessToken.generate(profile=admin_profile, name="mine")
        _, theirs = PersonalAccessToken.generate(profile=user_profile, name="theirs")

        body = admin_client.get(LIST_URL).json()
        assert body["error"] is False
        ids = {t["id"] for t in body["tokens"]}
        assert str(mine.id) in ids
        assert str(theirs.id) in ids
        assert body["totals"]["count"] == 2

        # Owner block is present and names the person + role; is_active carried.
        by_id = {t["id"]: t for t in body["tokens"]}
        assert by_id[str(theirs.id)]["owner"]["role"] == "USER"
        assert by_id[str(theirs.id)]["owner"]["is_active"] is True

    def test_non_admin_is_forbidden(self, user_client, user_profile):
        # A member must not see the whole org's tokens, not even their own via
        # this endpoint; self-service lives on /profile/tokens/.
        PersonalAccessToken.generate(profile=user_profile, name="mine")
        resp = user_client.get(LIST_URL)
        assert resp.status_code == 403, resp.content

    def test_cross_org_isolation(self, org_b_client, admin_profile, profile_b):
        # No RLS on this table: the org filter is the ONLY barrier. Org B's admin
        # must never see org A's token.
        _, a_token = PersonalAccessToken.generate(
            profile=admin_profile, name="org-a-secret"
        )
        _, b_token = PersonalAccessToken.generate(profile=profile_b, name="org-b-own")

        body = org_b_client.get(LIST_URL).json()
        ids = {t["id"] for t in body["tokens"]}
        assert str(a_token.id) not in ids
        assert str(b_token.id) in ids
        assert body["totals"]["count"] == 1

    def test_orphaned_counts_live_token_on_deactivated_owner(
        self, admin_client, admin_profile, user_profile
    ):
        user_profile.is_active = False
        user_profile.save()
        PersonalAccessToken.generate(profile=user_profile, name="left-behind")

        body = admin_client.get(LIST_URL).json()
        assert body["totals"]["orphaned"] == 1
        assert body["totals"]["live"] == 1
        row = body["tokens"][0]
        assert row["owner"]["is_active"] is False
        assert row["is_live"] is True  # token-valid, even though auth would reject it

    def test_revoked_and_expired_are_not_orphaned_or_live(
        self, admin_client, admin_profile, user_profile
    ):
        user_profile.is_active = False
        user_profile.save()
        _, revoked = PersonalAccessToken.generate(profile=user_profile, name="revoked")
        revoked.revoked_at = timezone.now()
        revoked.save()
        PersonalAccessToken.generate(
            profile=user_profile,
            name="expired",
            expires_at=timezone.now() - timedelta(days=1),
        )

        body = admin_client.get(LIST_URL).json()
        assert body["totals"]["count"] == 2
        assert body["totals"]["live"] == 0
        assert body["totals"]["orphaned"] == 0

    def test_unused_90d_counted(self, admin_client, admin_profile):
        _, stale = PersonalAccessToken.generate(profile=admin_profile, name="stale")
        PersonalAccessToken.objects.filter(pk=stale.pk).update(
            last_used_at=timezone.now() - timedelta(days=120)
        )
        _, fresh = PersonalAccessToken.generate(profile=admin_profile, name="fresh")
        PersonalAccessToken.objects.filter(pk=fresh.pk).update(
            last_used_at=timezone.now()
        )

        body = admin_client.get(LIST_URL).json()
        assert body["totals"]["unused_90d"] == 1

    def test_a_token_just_issued_is_not_unused_for_90_days(
        self, admin_client, admin_profile
    ):
        # last_used_at is null for a token issued three years ago AND for one
        # issued a minute ago. Counting on null alone put the token you had just
        # created into "unused for 90+ days" on the very next reload.
        PersonalAccessToken.generate(profile=admin_profile, name="brand new")

        body = admin_client.get(LIST_URL).json()
        assert body["totals"]["unused_90d"] == 0

    def test_a_never_used_token_counts_once_it_is_old_enough(
        self, admin_client, admin_profile
    ):
        # The other half: never used is still the strongest signal there is, so
        # an old one has to count. created_at is what dates it.
        _, forgotten = PersonalAccessToken.generate(
            profile=admin_profile, name="forgotten"
        )
        PersonalAccessToken.objects.filter(pk=forgotten.pk).update(
            created_at=timezone.now() - timedelta(days=120)
        )

        body = admin_client.get(LIST_URL).json()
        assert body["totals"]["unused_90d"] == 1

    def test_no_secret_ever_serialized(self, admin_client, admin_profile):
        raw, _ = PersonalAccessToken.generate(profile=admin_profile, name="cli")
        body = admin_client.get(LIST_URL).json()
        assert raw not in str(body)
        assert all("token_hash" not in t for t in body["tokens"])
        assert all("token" not in t for t in body["tokens"])

    def test_unauthenticated_is_403(self, unauthenticated_client):
        # Same shape as the self endpoint: the org-context middleware denies a
        # credential-less request before DRF's auth layer would emit a 401.
        resp = unauthenticated_client.get(LIST_URL)
        assert resp.status_code == 403, resp.content


@pytest.mark.django_db
class TestOrgTokenRevoke:
    def test_admin_revokes_another_members_token(
        self, admin_client, admin_profile, user_profile
    ):
        # The whole reason this endpoint exists: the self-scoped revoke 404s on
        # someone else's token; the admin one retires it.
        _, theirs = PersonalAccessToken.generate(profile=user_profile, name="theirs")
        resp = admin_client.delete(_detail_url(theirs.id))
        assert resp.status_code == 200, resp.content
        theirs.refresh_from_db()
        assert theirs.revoked_at is not None

    def test_non_admin_cannot_revoke(self, user_client, admin_profile):
        _, target = PersonalAccessToken.generate(profile=admin_profile, name="admins")
        resp = user_client.delete(_detail_url(target.id))
        assert resp.status_code == 403, resp.content
        target.refresh_from_db()
        assert target.revoked_at is None

    def test_cross_org_revoke_is_404(self, org_b_client, admin_profile):
        _, a_token = PersonalAccessToken.generate(profile=admin_profile, name="org-a")
        resp = org_b_client.delete(_detail_url(a_token.id))
        assert resp.status_code == 404, resp.content
        a_token.refresh_from_db()
        assert a_token.revoked_at is None

    def test_revoke_is_idempotent(self, admin_client, admin_profile, user_profile):
        _, t = PersonalAccessToken.generate(profile=user_profile, name="theirs")
        first = admin_client.delete(_detail_url(t.id))
        assert first.status_code == 200, first.content
        t.refresh_from_db()
        stamp = t.revoked_at
        assert stamp is not None
        second = admin_client.delete(_detail_url(t.id))
        assert second.status_code == 200, second.content
        t.refresh_from_db()
        assert t.revoked_at == stamp  # not re-stamped

    def test_revoke_unknown_uuid_is_404(self, admin_client, admin_profile):
        resp = admin_client.delete(_detail_url(uuid.uuid4()))
        assert resp.status_code == 404, resp.content


@pytest.mark.django_db
def test_deactivated_owner_token_is_rejected_at_the_api(admin_client, user_profile):
    """End-to-end proof of the page's reframed claim.

    The mock said a deactivated owner's token "keeps working with their old
    role." It does not: with the owner's profile.is_active false, the token is
    refused at the door. This guards the copy on /v2/settings/api-tokens and
    /v2/team, and complements the unit test test_pat_auth.py::
    test_inactive_profile_raises with a real request through the middleware.
    """
    raw, _ = PersonalAccessToken.generate(profile=user_profile, name="pre-deactivation")
    user_profile.is_active = False
    user_profile.save()

    resp = Client().get("/api/leads/", HTTP_AUTHORIZATION=f"Bearer {raw}")
    assert resp.status_code in (401, 403), resp.content
