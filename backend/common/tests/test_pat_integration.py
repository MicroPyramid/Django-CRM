"""Integration tests driving a PAT through the REAL middleware stack.

These use Django's test ``Client`` (not DRF's APIClient with forced auth) so the
request passes through GetProfileAndOrg → RequireOrgContext → DRF auth exactly
as in production. They run on SQLite (no postgres_only marker) and are the
regression guard for the bug where a valid PAT was rejected with 403 by
RequireOrgContext because org context was never set in middleware.

These probes used to point at ``/api/profile/tokens/``. That endpoint is now on
the credential deny-list in ``common.scopes``: a token may not read or mint
another token. The probes moved to an ordinary endpoint, which is what they were
always really testing, and the deny is asserted here too so the reason this file
changed is recorded next to it rather than only in a commit message.
"""

import pytest
from django.test import Client
from django.utils import timezone

from common.models import PersonalAccessToken


@pytest.mark.django_db
class TestPATThroughMiddlewareStack:
    PROBE_URL = "/api/leads/"
    TOKEN_URL = "/api/profile/tokens/"

    def test_pat_request_reaches_view(self, admin_profile):
        """A valid PAT must reach a protected view (200), NOT be 403'd by
        RequireOrgContext. This is the core regression guard for the fix."""
        raw, _ = PersonalAccessToken.generate(profile=admin_profile, name="cli")
        client = Client()
        resp = client.get(self.PROBE_URL, HTTP_AUTHORIZATION=f"Bearer {raw}")
        assert resp.status_code == 200, resp.content

    def test_pat_can_list_contacts_via_middleware(self, admin_profile):
        """Same PAT reaching a second protected view."""
        raw, _ = PersonalAccessToken.generate(profile=admin_profile, name="cli")
        client = Client()
        resp = client.get("/api/contacts/", HTTP_AUTHORIZATION=f"Bearer {raw}")
        assert resp.status_code == 200, resp.content

    def test_pat_cannot_reach_the_token_endpoint(self, admin_profile):
        """The deny that replaced the old probe. A token cannot manage tokens."""
        raw, _ = PersonalAccessToken.generate(profile=admin_profile, name="cli")
        client = Client()
        resp = client.get(self.TOKEN_URL, HTTP_AUTHORIZATION=f"Bearer {raw}")
        assert resp.status_code == 403, resp.content

    def test_invalid_pat_is_denied(self, admin_profile):
        """A bogus PAT must be denied (not 500, not 200)."""
        client = Client()
        resp = client.get(self.PROBE_URL, HTTP_AUTHORIZATION="Bearer bcrm_pat_bogus")
        assert resp.status_code in (401, 403), resp.content
        assert resp.status_code not in (200, 500)

    def test_revoked_pat_is_denied_through_stack(self, admin_profile):
        """A revoked PAT must be denied through the full stack."""
        raw, pat = PersonalAccessToken.generate(profile=admin_profile, name="cli")
        pat.revoked_at = timezone.now()
        pat.save(update_fields=["revoked_at"])
        client = Client()
        resp = client.get(self.PROBE_URL, HTTP_AUTHORIZATION=f"Bearer {raw}")
        assert resp.status_code in (401, 403), resp.content
        assert resp.status_code not in (200, 500)
