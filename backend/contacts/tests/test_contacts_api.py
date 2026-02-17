"""
Tests for Contacts API endpoints.

Covers:
- ContactsListView (GET list, POST create)
- ContactDetailView (GET detail, PUT update, DELETE, POST comment)
- Organization isolation between tenants
- Duplicate email validation per org

Run with: pytest contacts/tests/test_contacts_api.py -v
"""

from unittest.mock import patch

import pytest
from django.db import connection
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from contacts.models import Contact


CONTACTS_LIST_URL = "/api/contacts/"


def _detail_url(pk):
    return f"/api/contacts/{pk}/"


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
def contact_a(admin_user, org_a):
    """A contact belonging to org_a, created by admin_user."""
    _set_rls(org_a)
    return Contact.objects.create(
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        org=org_a,
        created_by=admin_user,
    )


@pytest.fixture
def contact_b(user_b, org_b):
    """A contact belonging to org_b, created by user_b."""
    _set_rls(org_b)
    return Contact.objects.create(
        first_name="Bob",
        last_name="Jones",
        email="bob@example.com",
        org=org_b,
        created_by=user_b,
    )


@pytest.mark.django_db
class TestContactListView:
    """Tests for GET /api/contacts/ and POST /api/contacts/"""

    @patch("contacts.views.send_email_to_assigned_user.delay")
    def test_list_contacts(self, mock_email, admin_client, contact_a):
        """Admin can list contacts in their org."""
        response = admin_client.get(CONTACTS_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "contact_obj_list" in response.data
        assert response.data["contacts_count"] >= 1

    @patch("contacts.views.send_email_to_assigned_user.delay")
    def test_create_contact(self, mock_email, admin_client):
        """Admin can create a new contact via POST."""
        payload = {
            "first_name": "Charlie",
            "last_name": "Brown",
            "email": "charlie@example.com",
        }
        response = admin_client.post(CONTACTS_LIST_URL, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_create_contact_unauthenticated(self, unauthenticated_client):
        """Unauthenticated requests are rejected."""
        payload = {
            "first_name": "Nope",
            "last_name": "User",
            "email": "nope@example.com",
        }
        with pytest.raises(PermissionDenied):
            unauthenticated_client.post(
                CONTACTS_LIST_URL, payload, format="json"
            )

    @patch("contacts.views.send_email_to_assigned_user.delay")
    def test_org_isolation(
        self, mock_email, admin_client, org_b_client, contact_a, contact_b
    ):
        """Contacts created in org_a must not appear in org_b's list."""
        # org_b_client should only see org_b contacts
        response = org_b_client.get(CONTACTS_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        emails = [c["email"] for c in response.data["contact_obj_list"]]
        assert "alice@example.com" not in emails
        assert "bob@example.com" in emails


@pytest.mark.django_db
class TestContactDetailView:
    """Tests for GET/PUT/DELETE/POST on /api/contacts/<pk>/"""

    def test_get_contact_detail(self, admin_client, contact_a):
        """Admin can retrieve a single contact's detail."""
        response = admin_client.get(_detail_url(contact_a.pk))
        assert response.status_code == status.HTTP_200_OK
        assert "contact_obj" in response.data
        assert response.data["contact_obj"]["id"] == str(contact_a.pk)

    @patch("contacts.views.send_email_to_assigned_user.delay")
    def test_update_contact(self, mock_email, admin_client, contact_a):
        """Admin can update a contact via PUT."""
        payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "alice@example.com",
        }
        response = admin_client.put(
            _detail_url(contact_a.pk), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        contact_a.refresh_from_db()
        assert contact_a.first_name == "Updated"

    def test_delete_contact(self, admin_client, contact_a):
        """Admin can delete a contact."""
        response = admin_client.delete(_detail_url(contact_a.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert not Contact.objects.filter(pk=contact_a.pk).exists()

    def test_get_contact_cross_org(self, org_b_client, contact_a):
        """Accessing a contact from another org returns 404."""
        response = org_b_client.get(_detail_url(contact_a.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_comment_to_contact(self, admin_client, contact_a):
        """Admin can add a comment to a contact via POST to detail endpoint."""
        payload = {"comment": "This is a test comment"}
        response = admin_client.post(
            _detail_url(contact_a.pk), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "comments" in response.data

    @patch("contacts.views.send_email_to_assigned_user.delay")
    def test_duplicate_email_same_org(self, mock_email, admin_client, contact_a):
        """Creating a contact with a duplicate email in the same org returns 400."""
        payload = {
            "first_name": "Duplicate",
            "last_name": "Email",
            "email": "alice@example.com",
        }
        response = admin_client.post(CONTACTS_LIST_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] is True
