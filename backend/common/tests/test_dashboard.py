"""
Tests for dashboard views: ApiHomeView, ActivityListView.

Run with: pytest common/tests/test_dashboard.py -v
"""

import uuid

import pytest
from rest_framework import status

from accounts.models import Account
from common.models import Activity
from contacts.models import Contact
from leads.models import Lead
from opportunity.models import Opportunity


@pytest.mark.django_db
class TestDashboardView:
    """Tests for GET /api/dashboard/"""

    url = "/api/dashboard/"

    def test_dashboard_authenticated(self, admin_client, org_a):
        """Authenticated admin gets dashboard data."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert "accounts_count" in data
        assert "contacts_count" in data
        assert "leads_count" in data
        assert "opportunities_count" in data

    def test_dashboard_unauthenticated(self, unauthenticated_client):
        """The request is refused, and refused as a response, not an exception.

        DRF catches ``PermissionDenied`` in ``handle_exception`` and renders it,
        so a test client never sees it raised. Wrapping the call in
        ``pytest.raises`` therefore failed with DID NOT RAISE no matter how the
        endpoint behaved, which meant this test could never have caught the
        access opening up.
        """
        response = unauthenticated_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dashboard_counts(self, admin_client, org_a, admin_user):
        """Dashboard should return accurate counts."""
        Account.objects.create(name="Acc1", org=org_a)
        Account.objects.create(name="Acc2", org=org_a)
        Contact.objects.create(first_name="Con", last_name="Tact", org=org_a)
        Lead.objects.create(
            first_name="Lead", last_name="One", email="lead1@test.com", org=org_a
        )
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["accounts_count"] == 2
        assert response.data["contacts_count"] == 1
        assert response.data["leads_count"] == 1

    def test_dashboard_urgent_counts(self, admin_client, org_a):
        """Dashboard should return urgent_counts section."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "urgent_counts" in response.data
        urgent = response.data["urgent_counts"]
        assert "overdue_tasks" in urgent
        assert "tasks_due_today" in urgent
        assert "followups_today" in urgent
        assert "hot_leads" in urgent

    def test_dashboard_pipeline_by_stage(self, admin_client, org_a):
        """Dashboard should return pipeline_by_stage section."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "pipeline_by_stage" in response.data

    def test_dashboard_revenue_metrics(self, admin_client, org_a):
        """Dashboard should return revenue_metrics section."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "revenue_metrics" in response.data
        metrics = response.data["revenue_metrics"]
        assert "pipeline_value" in metrics
        assert "weighted_pipeline" in metrics
        assert "won_this_month" in metrics
        assert "conversion_rate" in metrics
        assert "currency" in metrics

    def test_dashboard_hot_leads(self, admin_client, org_a):
        """Dashboard should return hot_leads list."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "hot_leads" in response.data

    def test_dashboard_tasks(self, admin_client, org_a):
        """Dashboard should return tasks."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "tasks" in response.data

    def test_dashboard_activities(self, admin_client, org_a):
        """Dashboard should return recent activities."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "activities" in response.data

    def test_dashboard_non_admin(self, user_client, org_a, regular_user, user_profile):
        """Non-admin user should see only their own data."""
        # Create an account owned by a different user - non-admin shouldn't see it
        Account.objects.create(name="Admin Account", org=org_a)
        user_account = Account.objects.create(name="User Account", org=org_a)
        # Manually set created_by since crum overrides it in tests
        Account.objects.filter(id=user_account.id).update(created_by=regular_user)
        response = user_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        # Non-admin should only see accounts they created or are assigned to
        assert response.data["accounts_count"] == 1


@pytest.mark.django_db
class TestActivityListView:
    """Tests for GET /api/activities/"""

    url = "/api/activities/"

    def test_list_activities(self, admin_client, org_a, admin_profile):
        """Get recent activities."""
        Activity.objects.create(
            user=admin_profile,
            action="CREATE",
            entity_type="Account",
            entity_id=uuid.uuid4(),
            entity_name="Test Account",
            org=org_a,
        )
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "activities" in response.data
        assert response.data["count"] >= 1

    def test_list_activities_with_limit(self, admin_client, org_a, admin_profile):
        """Test limit parameter."""
        for i in range(5):
            Activity.objects.create(
                user=admin_profile,
                action="CREATE",
                entity_type="Account",
                entity_id=uuid.uuid4(),
                entity_name=f"Account {i}",
                org=org_a,
            )
        response = admin_client.get(self.url + "?limit=2")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_activities_filter_by_entity_type(
        self, admin_client, org_a, admin_profile
    ):
        """Filter activities by entity_type."""
        Activity.objects.create(
            user=admin_profile,
            action="CREATE",
            entity_type="Account",
            entity_id=uuid.uuid4(),
            entity_name="Account Activity",
            org=org_a,
        )
        Activity.objects.create(
            user=admin_profile,
            action="CREATE",
            entity_type="Lead",
            entity_id=uuid.uuid4(),
            entity_name="Lead Activity",
            org=org_a,
        )
        response = admin_client.get(self.url + "?entity_type=Account")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestDashboardScopedMetrics:
    """The KPI row has to agree with itself, and with the caller's role.

    Every case here was reproduced on a real member session before it was
    written: the dashboard read "4 Open Deals" beside a pipeline holding two,
    and a 5% conversion rate that belonged to the whole org.
    """

    url = "/api/dashboard/"

    def _deal(self, org, name, stage, amount, creator, assignees=()):
        deal = Opportunity.objects.create(
            name=name, org=org, stage=stage, amount=amount, probability=50
        )
        # `BaseModel.save()` sets created_by from the thread-local current
        # user and ignores the kwarg, so authorship has to be written with an
        # UPDATE that skips save() entirely.
        Opportunity.objects.filter(pk=deal.pk).update(created_by=creator)
        if assignees:
            deal.assigned_to.set(assignees)
        return deal

    def _lead(self, org, last_name, email, status_value, creator, assignees=()):
        lead = Lead.objects.create(
            first_name="L",
            last_name=last_name,
            email=email,
            org=org,
            status=status_value,
        )
        Lead.objects.filter(pk=lead.pk).update(created_by=creator)
        if assignees:
            lead.assigned_to.set(assignees)
        return lead

    def test_open_deals_count_excludes_closed_stages(
        self, admin_client, org_a, admin_user
    ):
        self._deal(org_a, "Open one", "PROPOSAL", 100, admin_user)
        self._deal(org_a, "Open two", "NEGOTIATION", 200, admin_user)
        self._deal(org_a, "Banked", "CLOSED_WON", 900, admin_user)
        self._deal(org_a, "Lost", "CLOSED_LOST", 400, admin_user)

        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        metrics = response.data["revenue_metrics"]

        assert metrics["open_opportunities_count"] == 2
        # The card beside it sums the same two deals, so the pair must agree.
        assert metrics["pipeline_value"] == 300.0
        # The all-stage count is still published, and still counts all stages.
        assert response.data["opportunities_count"] == 4

    def test_conversion_rate_is_scoped_to_the_caller(
        self, user_client, org_a, admin_user, regular_user, user_profile
    ):
        # The member owns two leads, one of them converted: 50%.
        self._lead(org_a, "Converted", "m1@test.com", "converted", regular_user)
        self._lead(org_a, "Open", "m2@test.com", "assigned", regular_user)
        # The org holds eight more that are none of the member's business.
        for i in range(8):
            self._lead(org_a, str(i), f"t{i}@test.com", "assigned", admin_user)

        response = user_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["revenue_metrics"]["conversion_rate"] == 50.0

    def test_admin_conversion_rate_still_covers_the_org(
        self, admin_client, org_a, admin_user, regular_user
    ):
        self._lead(org_a, "Converted", "a1@test.com", "converted", admin_user)
        for i in range(3):
            self._lead(org_a, str(i), f"b{i}@test.com", "assigned", regular_user)

        response = admin_client.get(self.url)
        assert response.data["revenue_metrics"]["conversion_rate"] == 25.0

    def test_member_totals_are_not_multiplied_by_assignees(
        self, user_client, org_a, regular_user, user_profile, admin_profile
    ):
        """One deal, created by the member and assigned to two people, is one.

        Narrowing straight onto the assigned_to M2M turns this into two joined
        rows, both matching on created_by, which doubles the count and doubles
        the pipeline sum.
        """
        self._deal(
            org_a,
            "Shared",
            "PROPOSAL",
            1000,
            regular_user,
            assignees=[user_profile, admin_profile],
        )

        response = user_client.get(self.url)
        metrics = response.data["revenue_metrics"]

        assert metrics["open_opportunities_count"] == 1
        assert metrics["pipeline_value"] == 1000.0
        assert response.data["opportunities_count"] == 1

    def test_member_lead_count_is_not_multiplied_by_assignees(
        self, user_client, org_a, regular_user, user_profile, admin_profile
    ):
        self._lead(
            org_a,
            "Lead",
            "shared@test.com",
            "assigned",
            regular_user,
            assignees=[user_profile, admin_profile],
        )

        response = user_client.get(self.url)
        assert response.data["leads_count"] == 1

    def test_member_sees_only_their_own_deals(
        self, user_client, org_a, admin_user, regular_user, user_profile
    ):
        self._deal(org_a, "Mine", "PROPOSAL", 100, regular_user)
        self._deal(org_a, "Theirs", "PROPOSAL", 5000, admin_user)

        response = user_client.get(self.url)
        metrics = response.data["revenue_metrics"]

        assert metrics["open_opportunities_count"] == 1
        assert metrics["pipeline_value"] == 100.0

    def test_dashboard_declares_org_context(self):
        """The permission class is the contract; middleware is the safety net."""
        from common.permissions import HasOrgContext
        from common.views.dashboard_views import ApiHomeView

        assert HasOrgContext in ApiHomeView.permission_classes


@pytest.mark.django_db
class TestDashboardSendsOnlyWhatItRenders:
    """The dashboard used to serialize four whole tables nobody read.

    Measured against the seeded org: 384 KB of response, of which
    ``opportunities`` (162 KB), ``accounts`` (86 KB), ``leads`` (84 KB) and
    ``contacts`` (41 KB) were 97%. The only caller is the mobile dashboard, and
    its model reads counts, ``urgent_counts``, ``pipeline_by_stage``,
    ``revenue_metrics``, ``hot_leads``, ``tasks``, ``activities`` and
    ``goal_summary``. It never touched the four lists.

    They were also unpaged, so the payload grew with the org forever.
    """

    url = "/api/dashboard/"

    # Note the trap here: ``hot_leads`` is a list on the response AND a count
    # inside ``urgent_counts``. Only the top-level list survives.
    DROPPED = ("accounts", "contacts", "leads", "opportunities")

    KEPT = (
        "accounts_count",
        "contacts_count",
        "leads_count",
        "opportunities_count",
        "urgent_counts",
        "pipeline_by_stage",
        "revenue_metrics",
        "hot_leads",
        "tasks",
        "activities",
        "goal_summary",
    )

    def test_the_four_unread_lists_are_gone(self, admin_client, org_a):
        Account.objects.create(name="Acc1", org=org_a)
        Contact.objects.create(first_name="Con", last_name="Tact", org=org_a)
        Lead.objects.create(
            first_name="Lead", last_name="One", email="lead1@test.com", org=org_a
        )
        Opportunity.objects.create(name="Deal", org=org_a, stage="PROSPECTING")

        response = admin_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        for key in self.DROPPED:
            assert key not in response.data, f"{key} is back in the response"

    def test_everything_a_client_reads_is_still_there(self, admin_client, org_a):
        """The other direction. Trimming is only safe while this passes."""
        response = admin_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        for key in self.KEPT:
            assert key in response.data, f"{key} disappeared"

    def test_the_counts_still_count_the_rows_that_were_dropped(
        self, admin_client, org_a
    ):
        """The querysets stayed; only the serialization went."""
        Account.objects.create(name="Acc1", org=org_a)
        Account.objects.create(name="Acc2", org=org_a)

        response = admin_client.get(self.url)

        assert response.data["accounts_count"] == 2
