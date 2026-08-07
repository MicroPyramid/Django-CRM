import hashlib
from datetime import timedelta

import pytest
from django.utils import timezone

from common.models import PersonalAccessToken


@pytest.mark.django_db
class TestPersonalAccessToken:
    def test_generate_returns_raw_token_and_persists_hash(self, org_a, admin_profile):
        raw, pat = PersonalAccessToken.generate(
            profile=admin_profile, name="Claude Desktop"
        )
        assert raw.startswith("bcrm_pat_")
        assert pat.token_hash == hashlib.sha256(raw.encode()).hexdigest()
        assert pat.token_hash != raw
        assert pat.token_prefix and raw.startswith(pat.token_prefix)
        assert pat.org == org_a
        assert pat.profile == admin_profile

    def test_is_valid_true_when_active(self, admin_profile):
        _, pat = PersonalAccessToken.generate(profile=admin_profile, name="x")
        assert pat.is_valid() is True

    def test_is_valid_false_when_revoked(self, admin_profile):
        _, pat = PersonalAccessToken.generate(profile=admin_profile, name="x")
        pat.revoked_at = timezone.now()
        pat.save()
        assert pat.is_valid() is False

    def test_is_valid_false_when_expired(self, admin_profile):
        _, pat = PersonalAccessToken.generate(
            profile=admin_profile,
            name="x",
            expires_at=timezone.now() - timedelta(days=1),
        )
        assert pat.is_valid() is False


@pytest.mark.postgres_only
@pytest.mark.django_db
def test_pat_table_has_no_rls_policy():
    """personal_access_token is intentionally exempt from RLS.

    It is an auth-bootstrap table looked up by token_hash before any tenant
    context exists (mirroring the Org table). Isolation for token management
    is enforced by explicit org+profile filters in common/views/pat_views.py,
    not by a row-level security policy. Assert no policy exists on the table.
    """
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    with connection.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM pg_policies WHERE tablename = %s",
            ["personal_access_token"],
        )
        assert cur.fetchone()[0] == 0
