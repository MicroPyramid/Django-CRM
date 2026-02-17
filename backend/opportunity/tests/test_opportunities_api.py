"""
Tests for Opportunities API endpoints.

Covers:
- OpportunityListView (GET list, POST create)
- OpportunityDetailView (GET detail, PUT update, DELETE, POST comment)
- OpportunityLineItemListView / DetailView (CRUD for line items)
- Organization isolation between tenants

Run with: pytest opportunity/tests/test_opportunities_api.py -v
"""

from unittest.mock import patch

import pytest
from django.db import connection
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from accounts.models import Account
from opportunity.models import Opportunity, OpportunityLineItem


OPPORTUNITIES_LIST_URL = "/api/opportunities/"


def _detail_url(pk):
    return f"/api/opportunities/{pk}/"


def _line_items_url(opportunity_pk):
    return f"/api/opportunities/{opportunity_pk}/line-items/"


def _line_item_detail_url(opportunity_pk, line_item_pk):
    return f"/api/opportunities/{opportunity_pk}/line-items/{line_item_pk}/"


def _set_rls(org):
    """Set PostgreSQL RLS context so direct ORM writes are allowed.
    No-op on SQLite (used in tests).
    """
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


@pytest.fixture
def opp_a(admin_user, org_a):
    """An opportunity belonging to org_a, created by admin_user."""
    _set_rls(org_a)
    return Opportunity.objects.create(
        name="Org A Deal",
        stage="QUALIFICATION",
        org=org_a,
        created_by=admin_user,
    )


@pytest.fixture
def opp_b(user_b, org_b):
    """An opportunity belonging to org_b, created by user_b."""
    _set_rls(org_b)
    return Opportunity.objects.create(
        name="Org B Deal",
        stage="QUALIFICATION",
        org=org_b,
        created_by=user_b,
    )


@pytest.mark.django_db
class TestOpportunityListView:
    """Tests for GET /api/opportunities/ and POST /api/opportunities/"""

    @patch("opportunity.views.opportunity_views.send_email_to_assigned_user.delay")
    def test_list_opportunities(self, mock_email, admin_client, opp_a):
        """Admin can list opportunities in their org."""
        response = admin_client.get(OPPORTUNITIES_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "opportunities" in response.data
        assert response.data["opportunities_count"] >= 1

    @patch("opportunity.views.opportunity_views.send_email_to_assigned_user.delay")
    def test_create_opportunity(self, mock_email, admin_client):
        """Admin can create an opportunity via POST."""
        payload = {
            "name": "New Deal",
            "stage": "QUALIFICATION",
        }
        response = admin_client.post(
            OPPORTUNITIES_LIST_URL, payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    @patch("opportunity.views.opportunity_views.send_email_to_assigned_user.delay")
    def test_create_opportunity_with_account(
        self, mock_email, admin_client, org_a, admin_user
    ):
        """Admin can create an opportunity linked to an account."""
        _set_rls(org_a)
        account = Account.objects.create(
            name="Acme Corp",
            org=org_a,
            created_by=admin_user,
        )
        payload = {
            "name": "Acme Deal",
            "stage": "QUALIFICATION",
            "account": str(account.pk),
        }
        response = admin_client.post(
            OPPORTUNITIES_LIST_URL, payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_create_opportunity_unauthenticated(self, unauthenticated_client):
        """Unauthenticated requests are rejected."""
        payload = {
            "name": "Unauthorized Deal",
            "stage": "QUALIFICATION",
        }
        with pytest.raises(PermissionDenied):
            unauthenticated_client.post(
                OPPORTUNITIES_LIST_URL, payload, format="json"
            )

    @patch("opportunity.views.opportunity_views.send_email_to_assigned_user.delay")
    def test_org_isolation(
        self, mock_email, admin_client, org_b_client, opp_a, opp_b
    ):
        """Opportunities in org_a must not appear in org_b's list."""
        response = org_b_client.get(OPPORTUNITIES_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        names = [o["name"] for o in response.data["opportunities"]]
        assert "Org A Deal" not in names
        assert "Org B Deal" in names


@pytest.mark.django_db
class TestOpportunityDetailView:
    """Tests for GET/PUT/DELETE/POST on /api/opportunities/<pk>/"""

    @pytest.fixture()
    def opportunity(self, org_a, admin_user):
        _set_rls(org_a)
        return Opportunity.objects.create(
            name="Detail Opp",
            stage="QUALIFICATION",
            org=org_a,
            created_by=admin_user,
        )

    def test_get_detail(self, admin_client, opportunity):
        """Admin can retrieve a single opportunity's detail."""
        response = admin_client.get(_detail_url(opportunity.pk))
        assert response.status_code == status.HTTP_200_OK
        assert "opportunity_obj" in response.data
        assert response.data["opportunity_obj"]["id"] == str(opportunity.pk)

    @patch("opportunity.views.opportunity_views.send_email_to_assigned_user.delay")
    def test_update(self, mock_email, admin_client, opportunity):
        """Admin can update an opportunity via PUT."""
        payload = {
            "name": "Updated Opp",
            "stage": "PROPOSAL",
        }
        response = admin_client.put(
            _detail_url(opportunity.pk), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        opportunity.refresh_from_db()
        assert opportunity.name == "Updated Opp"

    def test_delete(self, admin_client, opportunity):
        """Admin can delete an opportunity."""
        response = admin_client.delete(_detail_url(opportunity.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert not Opportunity.objects.filter(pk=opportunity.pk).exists()

    def test_cross_org(self, org_b_client, opportunity):
        """Accessing an opportunity from another org returns an error."""
        response = org_b_client.get(_detail_url(opportunity.pk))
        # The detail view uses .filter().first() which returns None,
        # then accessing .org on None raises AttributeError -> 500,
        # or RLS hides the row entirely. Either way, data is not returned.
        assert response.status_code != status.HTTP_200_OK or (
            response.data.get("error") is True
        )

    def test_add_comment(self, admin_client, opportunity):
        """Admin can add a comment to an opportunity via POST to detail."""
        payload = {"comment": "Looks like a promising deal"}
        response = admin_client.post(
            _detail_url(opportunity.pk), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "comments" in response.data


@pytest.mark.django_db
class TestOpportunityLineItems:
    """Tests for line item CRUD under /api/opportunities/<pk>/line-items/"""

    @pytest.fixture()
    def opportunity(self, org_a, admin_user):
        _set_rls(org_a)
        return Opportunity.objects.create(
            name="LineItem Opp",
            stage="QUALIFICATION",
            org=org_a,
            created_by=admin_user,
        )

    @pytest.fixture()
    def line_item(self, opportunity, org_a):
        _set_rls(org_a)
        return OpportunityLineItem.objects.create(
            opportunity=opportunity,
            name="Widget A",
            quantity=2,
            unit_price=50,
            org=org_a,
        )

    def test_create_line_item(self, admin_client, opportunity):
        """Admin can create a line item for an opportunity."""
        payload = {
            "name": "Consulting Hours",
            "quantity": 10,
            "unit_price": "150.00",
        }
        response = admin_client.post(
            _line_items_url(opportunity.pk), payload, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["error"] is False
        assert response.data["line_item"]["name"] == "Consulting Hours"

    def test_list_line_items(self, admin_client, opportunity, line_item):
        """Admin can list line items for an opportunity."""
        response = admin_client.get(_line_items_url(opportunity.pk))
        assert response.status_code == status.HTTP_200_OK
        assert "line_items" in response.data
        assert len(response.data["line_items"]) == 1
        assert response.data["line_items"][0]["name"] == "Widget A"

    def test_update_line_item(self, admin_client, opportunity, line_item):
        """Admin can update an existing line item."""
        payload = {
            "name": "Widget A (Revised)",
            "quantity": 5,
            "unit_price": "75.00",
        }
        response = admin_client.put(
            _line_item_detail_url(opportunity.pk, line_item.pk),
            payload,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        line_item.refresh_from_db()
        assert line_item.name == "Widget A (Revised)"
        assert line_item.quantity == 5

    def test_delete_line_item(self, admin_client, opportunity, line_item):
        """Admin can delete a line item."""
        response = admin_client.delete(
            _line_item_detail_url(opportunity.pk, line_item.pk)
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert not OpportunityLineItem.objects.filter(pk=line_item.pk).exists()
