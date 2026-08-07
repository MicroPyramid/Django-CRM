"""
Tests for the v2 "Today" action queue: GET /api/dashboard/today/ (ApiTodayView).

Two things are under test: that each of the four sources (unanswered cases,
overdue invoices, quiet deals, due tasks) lands in the right bucket, and. The
part that matters for a multi-tenant app. That a member sees only their own
rows and no request ever crosses an org boundary.

Run with: pytest common/tests/test_today.py -v
"""

import datetime

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework import status

from cases.models import Case
from common.views.dashboard_views import TODAY_QUEUE_LIMIT, TODAY_SOURCE_LIMIT
from invoices.models import Invoice
from opportunity.models import Opportunity
from tasks.models import Task


def _set_rls(org):
    """Set the RLS session var so a direct ORM insert satisfies the org policy.

    No-op on SQLite (the default test DB has no RLS / set_config); required when
    the suite runs against PostgreSQL.
    """
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as c:
        c.execute("SELECT set_config('app.current_org', %s, false)", [str(org.id)])


def _ids(rows):
    return {row["id"] for row in rows}


def _today():
    return timezone.localdate()


def _days(n):
    return datetime.timedelta(days=n)


@pytest.mark.django_db
class TestTodayView:
    url = "/api/dashboard/today/"

    # ── shape / auth ────────────────────────────────────────────────────
    def test_today_shape(self, admin_client, org_a):
        resp = admin_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert set(resp.data.keys()) == {"queue", "summary", "later"}
        assert set(resp.data["summary"].keys()) == {
            "count",
            "shown",
            "sources",
            "quiet_deals",
            "quiet_value",
            "cleared_yesterday",
        }
        assert isinstance(resp.data["queue"], list)
        assert isinstance(resp.data["later"], list)

    def test_today_requires_auth(self, unauthenticated_client):
        resp = unauthenticated_client.get(self.url)
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    # ── invoices ────────────────────────────────────────────────────────
    def test_overdue_invoice_in_queue(self, admin_client, org_a):
        _set_rls(org_a)
        inv = Invoice.objects.create(
            invoice_title="Past due invoice",
            org=org_a,
            currency="USD",
            total_amount=1200,
            status="Sent",
            due_date=_today() - _days(9),
        )
        resp = admin_client.get(self.url)
        item = next(
            (i for i in resp.data["queue"] if i["id"] == f"invoice-{inv.id}"), None
        )
        assert item is not None
        assert item["due"] == "Overdue"
        assert item["action"] == "Send a reminder"
        assert item["href"] == f"/invoices/{inv.id}"

    def test_future_invoice_is_later_not_queue(self, admin_client, org_a):
        _set_rls(org_a)
        inv = Invoice.objects.create(
            invoice_title="Due Friday",
            org=org_a,
            currency="USD",
            total_amount=1000,
            status="Sent",
            due_date=_today() + _days(5),
        )
        resp = admin_client.get(self.url)
        assert f"invoice-{inv.id}" not in _ids(resp.data["queue"])
        assert f"invoice-{inv.id}" in _ids(resp.data["later"])

    def test_paid_invoice_absent(self, admin_client, org_a):
        _set_rls(org_a)
        inv = Invoice.objects.create(
            invoice_title="Settled",
            org=org_a,
            currency="USD",
            total_amount=1000,
            status="Paid",
            due_date=_today() - _days(9),
        )
        resp = admin_client.get(self.url)
        assert f"invoice-{inv.id}" not in _ids(resp.data["queue"])

    # ── cases ───────────────────────────────────────────────────────────
    def test_unanswered_case_in_queue(self, admin_client, org_a, admin_user):
        _set_rls(org_a)
        case = Case.objects.create(
            name="SSO login loop",
            status="New",
            priority="Urgent",
            case_type="Question",
            org=org_a,
            created_by=admin_user,
            first_response_at=None,
        )
        resp = admin_client.get(self.url)
        item = next(
            (i for i in resp.data["queue"] if i["id"] == f"case-{case.id}"), None
        )
        assert item is not None
        assert item["action"] == "Reply"
        assert item["href"] == f"/tickets/{case.id}"

    def test_answered_case_absent(self, admin_client, org_a, admin_user):
        _set_rls(org_a)
        case = Case.objects.create(
            name="Already replied",
            status="New",
            priority="Low",
            case_type="Question",
            org=org_a,
            created_by=admin_user,
            first_response_at=timezone.now(),
        )
        resp = admin_client.get(self.url)
        assert f"case-{case.id}" not in _ids(resp.data["queue"])

    # ── deals (aging) ───────────────────────────────────────────────────
    def test_quiet_deal_in_queue_and_summary(self, admin_client, org_a):
        _set_rls(org_a)
        opp = Opportunity.objects.create(
            name="Northwind renewal",
            org=org_a,
            stage="PROSPECTING",
            amount=42000,
            currency="USD",
            stage_changed_at=timezone.now() - _days(40),
        )
        resp = admin_client.get(self.url)
        assert resp.data["summary"]["quiet_deals"] >= 1
        assert resp.data["summary"]["quiet_value"] >= 42000
        item = next(
            (i for i in resp.data["queue"] if i["id"] == f"deal-{opp.id}"), None
        )
        assert item is not None
        # 40 days in a 14-day stage is past 1.5x expected → rotten (red/rust).
        assert item["tone"] == "rust"
        assert item["href"] == f"/pipeline/{opp.id}"

    def test_fresh_deal_not_quiet(self, admin_client, org_a):
        _set_rls(org_a)
        opp = Opportunity.objects.create(
            name="Fresh deal",
            org=org_a,
            stage="PROSPECTING",
            amount=5000,
            currency="USD",
            stage_changed_at=timezone.now() - _days(2),
        )
        resp = admin_client.get(self.url)
        assert f"deal-{opp.id}" not in _ids(resp.data["queue"])
        assert resp.data["summary"]["quiet_deals"] == 0

    # ── tasks ───────────────────────────────────────────────────────────
    def test_task_due_today_in_queue(self, admin_client, org_a, admin_user):
        _set_rls(org_a)
        task = Task.objects.create(
            title="Call Corner Bakery",
            status="New",
            priority="Medium",
            org=org_a,
            created_by=admin_user,
            due_date=_today(),
        )
        resp = admin_client.get(self.url)
        assert f"task-{task.id}" in _ids(resp.data["queue"])

    def test_task_next_week_is_later_not_queue(self, admin_client, org_a, admin_user):
        _set_rls(org_a)
        task = Task.objects.create(
            title="Rollout call",
            status="New",
            priority="Low",
            org=org_a,
            created_by=admin_user,
            due_date=_today() + _days(3),
        )
        resp = admin_client.get(self.url)
        assert f"task-{task.id}" not in _ids(resp.data["queue"])
        assert f"task-{task.id}" in _ids(resp.data["later"])

    def test_cleared_yesterday_counts_completed_task(
        self, admin_client, org_a, admin_user
    ):
        _set_rls(org_a)
        task = Task.objects.create(
            title="Done thing",
            status="Completed",
            priority="Low",
            org=org_a,
            created_by=admin_user,
            due_date=_today(),
        )
        # updated_at is auto_now; .update() bypasses it, backdating the touch.
        Task.objects.filter(id=task.id).update(updated_at=timezone.now() - _days(1))
        resp = admin_client.get(self.url)
        assert resp.data["summary"]["cleared_yesterday"] >= 1

    # ── the security-critical pair ──────────────────────────────────────
    def test_member_sees_only_own_items(
        self, user_client, org_a, regular_user, admin_user
    ):
        """A USER's queue includes rows they created and excludes a colleague's."""
        _set_rls(org_a)
        others = Invoice.objects.create(
            invoice_title="Admin's overdue invoice",
            org=org_a,
            currency="USD",
            total_amount=500,
            status="Sent",
            due_date=_today() - _days(3),
        )
        Invoice.objects.filter(id=others.id).update(created_by=admin_user)
        mine = Invoice.objects.create(
            invoice_title="My overdue invoice",
            org=org_a,
            currency="USD",
            total_amount=700,
            status="Sent",
            due_date=_today() - _days(3),
        )
        Invoice.objects.filter(id=mine.id).update(created_by=regular_user)

        resp = user_client.get(self.url)
        ids = _ids(resp.data["queue"])
        assert f"invoice-{mine.id}" in ids
        assert f"invoice-{others.id}" not in ids

    def test_admin_sees_colleague_items(self, admin_client, org_a, regular_user):
        """The same colleague-owned row the member is scoped to IS visible to an
        admin. Proving the member exclusion above is scoping, not a dropped row."""
        _set_rls(org_a)
        inv = Invoice.objects.create(
            invoice_title="Someone else's overdue invoice",
            org=org_a,
            currency="USD",
            total_amount=500,
            status="Sent",
            due_date=_today() - _days(3),
        )
        Invoice.objects.filter(id=inv.id).update(created_by=regular_user)
        resp = admin_client.get(self.url)
        assert f"invoice-{inv.id}" in _ids(resp.data["queue"])

    def test_cross_tenant_isolation(self, admin_client, org_a, org_b):
        """org_a's Today never includes an org_b row."""
        _set_rls(org_b)
        foreign = Invoice.objects.create(
            invoice_title="Org B invoice",
            org=org_b,
            currency="USD",
            total_amount=999,
            status="Sent",
            due_date=_today() - _days(4),
        )
        _set_rls(org_a)
        resp = admin_client.get(self.url)
        assert f"invoice-{foreign.id}" not in _ids(resp.data["queue"])


@pytest.mark.django_db
class TestTheHeaderCountMatchesThePage:
    """The header used to read "42 things want you today" over 8 rows, and then
    close with "That's everything due today."

    `summary.count` was `len(queue)`, taken after a per-source cap of 25 and
    before the queue cap of 8, so it was a third number that matched neither the
    rows on screen nor the org's real total. These tests pin both ends of it: the
    count is the true total, and the page is told how many it is showing and
    where the rest live.
    """

    url = "/api/dashboard/today/"

    def _overdue_invoices(self, org, n, created_by=None):
        for i in range(n):
            inv = Invoice.objects.create(
                invoice_title=f"Overdue {i}",
                org=org,
                currency="USD",
                total_amount=100 + i,
                status="Sent",
                due_date=_today() - _days(i + 1),
            )
            if created_by is not None:
                Invoice.objects.filter(id=inv.id).update(created_by=created_by)

    def test_the_count_is_the_total_and_shown_is_the_rows(self, admin_client, org_a):
        _set_rls(org_a)
        self._overdue_invoices(org_a, 12)

        summary = admin_client.get(self.url).data["summary"]

        assert summary["count"] == 12
        assert summary["shown"] == TODAY_QUEUE_LIMIT

    def test_the_page_can_tell_it_is_not_showing_everything(self, admin_client, org_a):
        """The closing line is the page's to draw, and this pair is what it
        draws from. With more than fits, shown < count; with fewer, they agree
        and the page may say "that's everything" truthfully."""
        _set_rls(org_a)
        self._overdue_invoices(org_a, 12)
        assert admin_client.get(self.url).data["summary"]["shown"] < 12

        Invoice.objects.filter(org=org_a).delete()
        self._overdue_invoices(org_a, 3)
        summary = admin_client.get(self.url).data["summary"]
        assert summary["shown"] == summary["count"] == 3

    def test_the_count_survives_the_per_source_cap(self, admin_client, org_a):
        """The old count read the queue list, so an org past the 25-per-source
        cap got 25: not its total, and not what it could see either."""
        _set_rls(org_a)
        self._overdue_invoices(org_a, TODAY_SOURCE_LIMIT + 5)

        summary = admin_client.get(self.url).data["summary"]

        assert summary["count"] == TODAY_SOURCE_LIMIT + 5

    def test_the_sources_say_where_the_overflow_went(
        self, admin_client, org_a, admin_user
    ):
        _set_rls(org_a)
        self._overdue_invoices(org_a, 10)
        for i in range(4):
            Task.objects.create(
                title=f"Due today {i}",
                org=org_a,
                status="New",
                priority="Medium",
                due_date=_today(),
                created_by=admin_user,
            )

        summary = admin_client.get(self.url).data["summary"]
        by_label = {s["label"]: s for s in summary["sources"]}

        assert by_label["overdue invoices"]["count"] == 10
        assert by_label["overdue invoices"]["href"] == "/invoices"
        assert by_label["tasks due"]["count"] == 4
        assert by_label["tasks due"]["href"] == "/tasks"
        assert sum(s["count"] for s in summary["sources"]) == summary["count"] == 14

    def test_a_source_with_nothing_in_it_is_not_listed(self, admin_client, org_a):
        """An empty source would render as a link to a page with nothing on it."""
        _set_rls(org_a)
        self._overdue_invoices(org_a, 2)

        summary = admin_client.get(self.url).data["summary"]

        assert [s["label"] for s in summary["sources"]] == ["overdue invoices"]

    def test_the_count_is_scoped_to_the_member(
        self, user_client, org_a, regular_user, admin_user
    ):
        """The count is derived from the same querysets the queue is, so a
        member's header cannot leak the size of a colleague's workload."""
        _set_rls(org_a)
        self._overdue_invoices(org_a, 9, created_by=admin_user)
        self._overdue_invoices(org_a, 2, created_by=regular_user)

        summary = user_client.get(self.url).data["summary"]

        assert summary["count"] == 2
        assert summary["shown"] == 2

    def test_the_count_stops_at_the_org_boundary(self, admin_client, org_a, org_b):
        _set_rls(org_b)
        self._overdue_invoices(org_b, 6)
        _set_rls(org_a)
        self._overdue_invoices(org_a, 1)

        summary = admin_client.get(self.url).data["summary"]

        assert summary["count"] == 1
