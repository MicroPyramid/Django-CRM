"""Transaction-local RLS context tests.

`RequireOrgContext` sets ``app.current_org`` *transaction-locally*
(``set_config(..., is_local=True)``) inside a request-wrapping transaction, so
the value is bound to that transaction and reverts on COMMIT/ROLLBACK. That is
what makes the app safe behind a connection pooler in transaction-pooling mode
(e.g. PgBouncer): a server backend handed to the next client can never carry a
stale tenant's context.

PostgreSQL-only — SQLite has no ``set_config()``/RLS, so these skip there
(which is the default test backend; run against Postgres to exercise them).
"""

import pytest
from django.db import connection, transaction
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, TransactionTestCase

from common.middleware.rls_context import RequireOrgContext
from common.models import Org

pytestmark = pytest.mark.postgres_only


def _is_postgres():
    return connection.vendor == "postgresql"


def _current_org(cursor):
    cursor.execute("SELECT current_setting('app.current_org', true)")
    return cursor.fetchone()[0]


class TestTransactionLocalMechanics(TransactionTestCase):
    """The GUC is scoped to its transaction and gone afterwards.

    Uses TransactionTestCase so the ``atomic()`` block below is a real
    transaction that actually COMMITs (not a savepoint inside a test wrapper) —
    that is what exercises the transaction-local revert. Works even when the DB
    user is a superuser, since it only checks GUC scope, not RLS filtering.
    """

    def test_guc_reverts_after_its_transaction(self):
        if not _is_postgres():
            self.skipTest("set_config()/RLS requires PostgreSQL")

        org_id = "11111111-1111-1111-1111-111111111111"
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute("SELECT set_config('app.current_org', %s, true)", [org_id])
                assert _current_org(cur) == org_id  # visible inside the txn

        # A fresh transaction must NOT see the previous transaction's value.
        with connection.cursor() as cur:
            leaked = _current_org(cur)
        assert leaked in ("", None), f"transaction-local GUC leaked: {leaked!r}"


class TestMiddlewareWrapsRequest(TestCase):
    """RequireOrgContext sets the GUC, inside a transaction, for normal paths
    and skips both for streaming (NON_ATOMIC) paths."""

    def _run(self, path):
        captured = {}

        def get_response(request):
            captured["in_atomic"] = connection.in_atomic_block
            with connection.cursor() as cur:
                captured["guc"] = _current_org(cur)
            return HttpResponse("ok")

        request = RequestFactory().get(path)
        request.org = Org.objects.create(name="MW Org")
        response = RequireOrgContext(get_response)(request)
        return response, request, captured

    def test_normal_path_sets_txn_local_context(self):
        if not _is_postgres():
            self.skipTest("set_config()/RLS requires PostgreSQL")
        response, request, captured = self._run("/api/leads/")
        assert response.status_code == 200
        assert captured["in_atomic"] is True
        assert captured["guc"] == str(request.org.id)

    def test_streaming_path_is_not_wrapped_and_unset(self):
        if not _is_postgres():
            self.skipTest("set_config()/RLS requires PostgreSQL")
        # The SSE stream does no ORM and must not be wrapped in a request-wide
        # transaction; the middleware leaves the context unset for it.
        _response, _request, captured = self._run("/api/notifications/stream/")
        assert captured["guc"] in ("", None)


def _set_context(value):
    """Set app.current_org at SESSION scope (survives autocommit statements)."""
    with connection.cursor() as cur:
        cur.execute("SELECT set_config('app.current_org', %s, false)", [str(value)])


def _bypasses_rls():
    """True when the current DB role is exempt from row-level security.

    BOTH ``rolsuper`` and ``rolbypassrls`` defeat RLS. Checking ``usesuper``
    alone would miss a role like ``crm_superadmin``, which is not a superuser
    but carries BYPASSRLS — so RLS would be silently inert while the check
    reported everything was fine.
    """
    with connection.cursor() as cur:
        cur.execute(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )
        row = cur.fetchone()
    return bool(row[0]) if row else True


class TestNoCrossTenantLeak(TransactionTestCase):
    """End-to-end leak guard: a request scoped to org A must not leave A's
    context readable to a later, unscoped query on the same connection.

    The GUC-scope half is asserted unconditionally. The half that proves the
    database actually *enforces* isolation needs a role without superuser or
    BYPASSRLS, and skips loudly otherwise — see the skip message.
    """

    def test_context_does_not_persist_after_request(self):
        if not _is_postgres():
            self.skipTest("set_config()/RLS requires PostgreSQL")

        org = Org.objects.create(name="Leak Org A")

        def get_response(request):
            return HttpResponse("ok")

        request = RequestFactory().get("/api/leads/")
        request.org = org
        RequireOrgContext(get_response)(request)  # request commits here

        # After the request's transaction committed, a new transaction sees no
        # leftover context — the property PgBouncer transaction pooling needs.
        with connection.cursor() as cur:
            assert _current_org(cur) in ("", None)

    def test_rls_actually_filters_rows_by_context(self):
        """The GUC is not merely *set* — the database enforces it.

        Everything else in this file checks that `app.current_org` has the right
        value and the right lifetime. None of it proves the policies do anything:
        under a superuser (or BYPASSRLS) role every assertion here still passes
        while RLS is completely inert. This test closes that gap by querying
        WITHOUT any `org=` filter, so only the database can be hiding the rows.
        """
        if not _is_postgres():
            self.skipTest("set_config()/RLS requires PostgreSQL")
        if _bypasses_rls():
            self.skipTest(
                "TENANT ISOLATION NOT VERIFIED: this DB role is a superuser or has "
                "BYPASSRLS, so RLS is inert and the assertions below would pass "
                "even with every policy dropped. Point the tests at a non-superuser "
                "role (see RLS_SETUP.md, 'crm_user') to actually exercise them."
            )

        from leads.models import Lead

        self.addCleanup(_set_context, "")

        org_a = Org.objects.create(name="RLS Org A")
        org_b = Org.objects.create(name="RLS Org B")

        # Rows must be inserted under their own org's context — the INSERT
        # policy's WITH CHECK rejects writing a row for another tenant.
        _set_context(org_a.id)
        lead_a = Lead.objects.create(first_name="Visible", last_name="OrgA", org=org_a)
        _set_context(org_b.id)
        lead_b = Lead.objects.create(first_name="Hidden", last_name="OrgB", org=org_b)

        # Scoped to A, with NO org filter in the query: B's row must be absent.
        _set_context(org_a.id)
        visible = set(Lead.objects.values_list("id", flat=True))
        assert lead_a.id in visible, "org A's own lead was hidden from org A"
        assert lead_b.id not in visible, (
            "org B's lead is visible under org A's context — RLS is not isolating tenants"
        )

        # No context at all: policies fail closed rather than opening up.
        _set_context("")
        assert Lead.objects.count() == 0, "unset context returned rows — RLS fails OPEN"
