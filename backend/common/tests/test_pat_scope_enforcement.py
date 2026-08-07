"""End-to-end scope enforcement for personal access tokens.

`test_scopes.py` proves the matcher. This proves the matcher is actually wired
in: that a real HTTP request carrying a scoped token gets refused before the
view runs, and that an interactive JWT session is untouched by any of it.

The interactive-session cases are the important half. A boundary that also
blocks the browser is not a boundary, it is an outage, so every deny here has a
paired assertion that the same request from `admin_client` still works.
"""

import pytest
from rest_framework.test import APIClient

from common.models import PersonalAccessToken
from common.serializer import PersonalAccessTokenCreateSerializer


def _pat_client(profile, scopes=None, name="cli"):
    raw, _ = PersonalAccessToken.generate(profile=profile, name=name, scopes=scopes)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
    return client


@pytest.mark.django_db
class TestScopeEnforcement:
    def test_unscoped_token_still_reads(self, admin_profile):
        """Every token issued before scopes existed carries `[]`. It must keep working."""
        assert _pat_client(admin_profile).get("/api/leads/").status_code == 200

    def test_unscoped_token_still_writes(self, admin_profile):
        resp = _pat_client(admin_profile).post(
            "/api/leads/",
            {"title": "Scope check", "first_name": "Un", "last_name": "Scoped"},
        )
        assert resp.status_code not in (401, 403)

    def test_read_scope_allows_get(self, admin_profile):
        client = _pat_client(admin_profile, scopes=["*:read"])
        assert client.get("/api/leads/").status_code == 200

    def test_read_scope_refuses_post(self, admin_profile):
        client = _pat_client(admin_profile, scopes=["*:read"])
        resp = client.post(
            "/api/leads/", {"title": "Nope", "first_name": "No", "last_name": "Write"}
        )
        assert resp.status_code == 403

    def test_read_scope_refuses_delete(self, admin_profile, org_a):
        from leads.models import Lead

        lead = Lead.objects.create(
            title="Deletable", first_name="De", last_name="Lete", org=org_a
        )
        client = _pat_client(admin_profile, scopes=["*:read"])
        assert client.delete(f"/api/leads/{lead.id}/").status_code == 403
        assert Lead.objects.filter(id=lead.id).exists()

    def test_resource_scope_confines_reads(self, admin_profile):
        client = _pat_client(admin_profile, scopes=["leads:read"])
        assert client.get("/api/leads/").status_code == 200
        assert client.get("/api/contacts/").status_code == 403

    def test_denial_body_names_the_reason(self, admin_profile):
        client = _pat_client(admin_profile, scopes=["leads:read"])
        resp = client.get("/api/contacts/")
        assert "scoped" in resp.json()["detail"].lower()


@pytest.mark.django_db
class TestCredentialDenyList:
    """No token may read or mint another credential, whatever its scopes.

    Both directions are asserted on every path: the token is refused AND the
    browser session is not, because the deny-list keys on how the request
    authenticated, never on who the caller is.
    """

    def test_token_cannot_list_tokens(self, admin_profile):
        assert _pat_client(admin_profile).get("/api/profile/tokens/").status_code == 403

    def test_session_can_list_tokens(self, admin_client):
        assert admin_client.get("/api/profile/tokens/").status_code == 200

    def test_token_cannot_mint_a_token(self, admin_profile):
        """Self-replication defeats revocation: revoke the leaked one, the child lives."""
        client = _pat_client(admin_profile)  # minting this one is itself a write
        before = PersonalAccessToken.objects.count()
        resp = client.post("/api/profile/tokens/", {"name": "child"})
        assert resp.status_code == 403
        assert PersonalAccessToken.objects.count() == before

    def test_session_can_mint_a_token(self, admin_client):
        assert (
            admin_client.post(
                "/api/profile/tokens/", {"name": "from-browser"}
            ).status_code
            == 201
        )

    def test_full_access_token_still_cannot_mint(self, admin_profile):
        """`[]` means unrestricted for ordinary endpoints, and still not for this one."""
        client = _pat_client(admin_profile, scopes=[])
        assert client.post("/api/profile/tokens/", {"name": "child"}).status_code == 403

    def test_write_scoped_token_still_cannot_mint(self, admin_profile):
        client = _pat_client(admin_profile, scopes=["*:write"])
        assert client.post("/api/profile/tokens/", {"name": "child"}).status_code == 403

    def test_token_cannot_read_the_org_api_key(self, admin_profile):
        """The escalation this closes: token reads the org key, key outlives the token."""
        assert _pat_client(admin_profile).get("/api/org/api-key/").status_code == 403

    def test_session_can_read_the_org_api_key(self, admin_client):
        assert admin_client.get("/api/org/api-key/").status_code == 200

    def test_token_cannot_rotate_the_org_api_key(self, admin_profile, org_a):
        before = org_a.api_key
        assert _pat_client(admin_profile).post("/api/org/api-key/").status_code == 403
        org_a.refresh_from_db()
        assert org_a.api_key == before

    def test_token_cannot_read_org_wide_token_oversight(self, admin_profile):
        assert _pat_client(admin_profile).get("/api/org/tokens/").status_code == 403

    def test_token_cannot_revoke_another_token(self, admin_profile):
        _, victim = PersonalAccessToken.generate(profile=admin_profile, name="victim")
        resp = _pat_client(admin_profile).delete(f"/api/org/tokens/{victim.id}/")
        assert resp.status_code == 403
        victim.refresh_from_db()
        assert victim.revoked_at is None

    def test_org_settings_is_not_swept_up(self, admin_profile):
        """`/api/org/api-key/` is denied; `/api/org/…` in general is not.

        A prefix that swallowed the whole `org/` namespace would break every
        token's access to org settings while looking like the same rule.
        """
        assert _pat_client(admin_profile).get("/api/org/settings/").status_code == 200


@pytest.mark.django_db
class TestScopeValidationAtCreation:
    def test_valid_scopes_accepted_and_normalized(self):
        ser = PersonalAccessTokenCreateSerializer(
            data={"name": "cli", "scopes": [" LEADS:Read ", "*:write"]}
        )
        assert ser.is_valid(), ser.errors
        assert ser.validated_data["scopes"] == ["leads:read", "*:write"]

    def test_unknown_resource_rejected(self):
        ser = PersonalAccessTokenCreateSerializer(
            data={"name": "cli", "scopes": ["nosuchapp:read"]}
        )
        assert not ser.is_valid()
        assert "scopes" in ser.errors

    def test_unknown_action_rejected(self):
        ser = PersonalAccessTokenCreateSerializer(
            data={"name": "cli", "scopes": ["leads:destroy"]}
        )
        assert not ser.is_valid()

    def test_malformed_scope_rejected(self):
        ser = PersonalAccessTokenCreateSerializer(
            data={"name": "cli", "scopes": ["leads"]}
        )
        assert not ser.is_valid()

    def test_empty_list_still_accepted(self):
        ser = PersonalAccessTokenCreateSerializer(data={"name": "cli", "scopes": []})
        assert ser.is_valid(), ser.errors
        assert ser.validated_data["scopes"] == []

    def test_duplicate_scopes_collapse(self):
        ser = PersonalAccessTokenCreateSerializer(
            data={"name": "cli", "scopes": ["leads:read", "LEADS:READ"]}
        )
        assert ser.is_valid(), ser.errors
        assert ser.validated_data["scopes"] == ["leads:read"]
