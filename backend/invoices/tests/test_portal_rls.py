"""RLS-enforced proof for the portal token → org resolution (Option 1).

These run only under a non-superuser Postgres role (``RLS_ENFORCE=1
--ds=crm.test_settings_postgres``), because the whole point is the behaviour
that a superuser dev DB hides: with an empty ``app.current_org`` the isolation
policy makes the estimate row invisible, so the anonymous portal view can only
work if it resolves the org from the unscoped lookup first.

See docs/PORTAL_RLS.md and [[client-portal-403]].
"""

import pytest
from django.db import connection
from django.utils import timezone

from common.models import Org
from common.portal_tokens import resolve_portal_org
from common.tasks import set_rls_context
from invoices.models import Estimate

pytestmark = [pytest.mark.postgres_only, pytest.mark.django_db]


def _set_ctx(value):
    with connection.cursor() as cur:
        cur.execute("SELECT set_config('app.current_org', %s, false)", [value])


def test_portal_access_token_table_has_no_rls_policy():
    """The lookup must be readable with an empty context, so it carries no policy."""
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    with connection.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM pg_policies WHERE tablename = %s",
            ["portal_access_token"],
        )
        assert cur.fetchone()[0] == 0


def test_resolution_reads_estimate_that_empty_context_hides():
    """The full Option-1 chain under a role that actually enforces RLS."""
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")

    # Org is not org-scoped, so it inserts without a context.
    org = Org.objects.create(name="RLS Portal Org")

    # Scoped inserts need the context set. This mimics an authenticated write.
    _set_ctx(str(org.id))
    try:
        estimate = Estimate.objects.create(
            org=org,
            title="RLS estimate",
            currency="USD",
            issue_date=timezone.localdate(),
        )
        token = estimate.public_token
    finally:
        _set_ctx("")

    # The anonymous portal request arrives with an empty context.
    # 1. The bug this fixes: the scoped query cannot see the row.
    assert Estimate.objects.filter(public_token=token).first() is None

    # 2. The unscoped lookup resolves the org anyway.
    resolved = resolve_portal_org(token, "estimate")
    assert resolved == str(org.id)

    # 3. With the resolved context set, the row is readable under full RLS.
    try:
        set_rls_context(resolved)
        assert Estimate.objects.filter(public_token=token).first() is not None
    finally:
        _set_ctx("")

    # 4. A wrong resource type must not resolve (an estimate token is not an
    #    invoice token), so it cannot be redirected onto another endpoint.
    assert resolve_portal_org(token, "invoice") is None
