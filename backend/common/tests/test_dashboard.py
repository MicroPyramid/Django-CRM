"""
Tests for dashboard views: ApiHomeView, ActivityListView.

Run with: pytest common/tests/test_dashboard.py -v
"""

import uuid

import pytest
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

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
        """Unauthenticated user gets PermissionDenied."""
        with pytest.raises(PermissionDenied):
            unauthenticated_client.get(self.url)

    def test_dashboard_counts(self, admin_client, org_a, admin_user):
        """Dashboard should return accurate counts."""
        Account.objects.create(name="Acc1", org=org_a)
        Account.objects.create(name="Acc2", org=org_a)
        Contact.objects.create(first_name="Con", last_name="Tact", org=org_a)
        Lead.objects.create(
            first_name="Lead", last_name="One",
            email="lead1@test.com", org=org_a
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
