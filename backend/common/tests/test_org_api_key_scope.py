"""What the organization API key is allowed to do.

The key is one per tenant, never expires, and resolves to an arbitrary active
ADMIN profile. That made it a permanent unrevokable admin session for the org,
which is what these tests now pin shut: it reads, it does not write, and it
cannot reach another credential.

Both the middleware and `common.external_auth.APIKeyAuthentication` resolve this
key independently, so the deny cases are asserted through a real request (which
exercises the middleware) and the auth class is exercised directly, because a
guard on one copy and not the other is no guard.
"""

import pytest
from django.test import override_settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient, APIRequestFactory

from common.external_auth import APIKeyAuthentication
from common.models import PersonalAccessToken


def _key_client(org):
    client = APIClient()
    client.credentials(HTTP_TOKEN=org.api_key)
    return client


@pytest.mark.django_db
class TestOrgApiKeyIsReadOnly:
    def test_key_can_read(self, org_a, admin_profile):
        assert _key_client(org_a).get("/api/leads/").status_code == 200

    def test_key_cannot_create(self, org_a, admin_profile):
        from leads.models import Lead

        before = Lead.objects.count()
        resp = _key_client(org_a).post(
            "/api/leads/", {"title": "Via key", "first_name": "A", "last_name": "B"}
        )
        assert resp.status_code == 403
        assert Lead.objects.count() == before

    def test_key_cannot_delete(self, org_a, admin_profile):
        from leads.models import Lead

        lead = Lead.objects.create(
            title="Survivor", first_name="Sur", last_name="Vivor", org=org_a
        )
        assert _key_client(org_a).delete(f"/api/leads/{lead.id}/").status_code == 403
        assert Lead.objects.filter(id=lead.id).exists()

    def test_key_cannot_patch(self, org_a, admin_profile):
        from leads.models import Lead

        lead = Lead.objects.create(
            title="Unchanged", first_name="Un", last_name="Changed", org=org_a
        )
        resp = _key_client(org_a).patch(f"/api/leads/{lead.id}/", {"title": "Changed"})
        assert resp.status_code == 403
        lead.refresh_from_db()
        assert lead.title == "Unchanged"


@pytest.mark.django_db
class TestOrgApiKeyCannotReachCredentials:
    def test_key_cannot_read_itself(self, org_a, admin_profile):
        """Reading itself is harmless; rotating itself is a denial of service.

        Both go through one path, and there is no case for a key that manages
        keys, so both are refused.
        """
        assert _key_client(org_a).get("/api/org/api-key/").status_code == 403

    def test_key_cannot_rotate_itself(self, org_a, admin_profile):
        before = org_a.api_key
        assert _key_client(org_a).post("/api/org/api-key/").status_code == 403
        org_a.refresh_from_db()
        assert org_a.api_key == before

    def test_key_cannot_mint_a_personal_token(self, org_a, admin_profile):
        """The escalation: a leaked org key mints a PAT owned by a real admin.

        The key is read-only, so this is already refused as a write. It is
        asserted separately because the deny-list must hold even if the
        read-only limit is ever relaxed for some endpoint.
        """
        before = PersonalAccessToken.objects.count()
        resp = _key_client(org_a).post("/api/profile/tokens/", {"name": "from-key"})
        assert resp.status_code == 403
        assert PersonalAccessToken.objects.count() == before

    def test_key_cannot_list_tokens(self, org_a, admin_profile):
        assert _key_client(org_a).get("/api/profile/tokens/").status_code == 403

    def test_key_cannot_read_org_token_oversight(self, org_a, admin_profile):
        assert _key_client(org_a).get("/api/org/tokens/").status_code == 403


@pytest.mark.django_db
class TestOrgApiKeyKillSwitch:
    @override_settings(ORG_API_KEY_AUTH_ENABLED=False)
    def test_disabled_refuses_even_reads(self, org_a, admin_profile):
        assert _key_client(org_a).get("/api/leads/").status_code == 403

    @override_settings(ORG_API_KEY_AUTH_ENABLED=True)
    def test_enabled_is_the_default_behaviour(self, org_a, admin_profile):
        assert _key_client(org_a).get("/api/leads/").status_code == 200

    def test_a_jwt_session_is_unaffected_by_the_switch(self, admin_client):
        """The switch keys on the credential, not on the endpoint or the person."""
        with override_settings(ORG_API_KEY_AUTH_ENABLED=False):
            assert admin_client.get("/api/leads/").status_code == 200


@pytest.mark.django_db
class TestAuthClassCarriesTheSameLimits:
    """The DRF auth class is a second, independent copy of the key resolution."""

    def setup_method(self):
        self.factory = APIRequestFactory()
        self.auth = APIKeyAuthentication()

    def test_read_authenticates(self, org_a, admin_profile, admin_user):
        request = self.factory.get("/api/leads/", HTTP_TOKEN=org_a.api_key)
        user, _ = self.auth.authenticate(request)
        assert user == admin_user

    def test_write_is_refused(self, org_a, admin_profile):
        request = self.factory.post("/api/leads/", HTTP_TOKEN=org_a.api_key)
        with pytest.raises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_credential_path_is_refused(self, org_a, admin_profile):
        request = self.factory.get("/api/org/api-key/", HTTP_TOKEN=org_a.api_key)
        with pytest.raises(AuthenticationFailed):
            self.auth.authenticate(request)

    @override_settings(ORG_API_KEY_AUTH_ENABLED=False)
    def test_kill_switch_is_refused(self, org_a, admin_profile):
        request = self.factory.get("/api/leads/", HTTP_TOKEN=org_a.api_key)
        with pytest.raises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_no_token_header_defers(self):
        assert self.auth.authenticate(self.factory.get("/api/leads/")) is None
