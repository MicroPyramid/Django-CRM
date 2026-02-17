import pytest
from rest_framework.exceptions import PermissionDenied

from leads.models import Lead


@pytest.mark.django_db
class TestLeadListView:
    """Tests for GET /api/leads/ and POST /api/leads/."""

    def test_list_leads(self, admin_client, admin_user, org_a):
        Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            created_by=admin_user,
            org=org_a,
        )
        response = admin_client.get("/api/leads/")
        assert response.status_code == 200
        data = response.json()
        assert "open_leads" in data

    def test_create_lead(self, admin_client, org_a):
        response = admin_client.post(
            "/api/leads/",
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert Lead.objects.filter(email="jane@example.com", org=org_a).exists()

    def test_create_lead_invalid_data(self, admin_client):
        response = admin_client.post(
            "/api/leads/",
            {"email": "not-a-valid-email"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    def test_create_lead_unauthenticated(self, unauthenticated_client):
        with pytest.raises(PermissionDenied):
            unauthenticated_client.post(
                "/api/leads/",
                {"first_name": "Test", "last_name": "Lead", "email": "t@t.com"},
            )

    def test_org_isolation(self, org_b_client, admin_user, org_a):
        Lead.objects.create(
            first_name="Private",
            last_name="Lead",
            email="private@org-a.com",
            created_by=admin_user,
            org=org_a,
        )
        response = org_b_client.get("/api/leads/")
        assert response.status_code == 200
        data = response.json()
        open_leads_list = data["open_leads"]["open_leads"]
        emails = [lead["email"] for lead in open_leads_list]
        assert "private@org-a.com" not in emails


@pytest.mark.django_db
class TestLeadDetailView:
    """Tests for GET/PUT/DELETE /api/leads/<pk>/."""

    def test_get_lead_detail(self, admin_client, admin_user, org_a):
        lead = Lead.objects.create(
            first_name="Detail",
            last_name="Lead",
            email="detail@example.com",
            created_by=admin_user,
            org=org_a,
        )
        response = admin_client.get(f"/api/leads/{lead.id}/")
        assert response.status_code == 200
        data = response.json()
        assert "lead_obj" in data

    def test_update_lead(self, admin_client, admin_user, org_a):
        lead = Lead.objects.create(
            first_name="Old",
            last_name="Name",
            email="update@example.com",
            created_by=admin_user,
            org=org_a,
        )
        response = admin_client.put(
            f"/api/leads/{lead.id}/",
            {
                "first_name": "New",
                "last_name": "Name",
                "email": "update@example.com",
            },
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False

    def test_delete_lead(self, admin_client, admin_user, org_a):
        lead = Lead.objects.create(
            first_name="Delete",
            last_name="Me",
            email="delete@example.com",
            created_by=admin_user,
            org=org_a,
        )
        response = admin_client.delete(f"/api/leads/{lead.id}/")
        assert response.status_code == 200
        assert not Lead.objects.filter(id=lead.id).exists()

    def test_get_lead_cross_org(self, org_b_client, admin_user, org_a):
        lead = Lead.objects.create(
            first_name="Cross",
            last_name="Org",
            email="cross@org-a.com",
            created_by=admin_user,
            org=org_a,
        )
        response = org_b_client.get(f"/api/leads/{lead.id}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestLeadCommentView:
    """Tests for POST /api/leads/<pk>/ (adding comments)."""

    def test_add_comment_to_lead(self, admin_client, admin_user, org_a):
        lead = Lead.objects.create(
            first_name="Comment",
            last_name="Lead",
            email="comment@example.com",
            created_by=admin_user,
            org=org_a,
        )
        response = admin_client.post(
            f"/api/leads/{lead.id}/",
            {"comment": "This is a test comment"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "lead_obj" in data
        assert "comments" in data


@pytest.mark.django_db
class TestLeadUniqueEmail:
    """Tests for unique email constraint per organization."""

    def test_duplicate_email_same_org(self, admin_client, org_a):
        admin_client.post(
            "/api/leads/",
            {
                "first_name": "First",
                "last_name": "Lead",
                "email": "dupe@example.com",
            },
        )
        response = admin_client.post(
            "/api/leads/",
            {
                "first_name": "Second",
                "last_name": "Lead",
                "email": "dupe@example.com",
            },
        )
        assert response.status_code == 400

    def test_same_email_different_org(
        self, admin_client, org_b_client, admin_user, user_b, org_a, org_b
    ):
        resp1 = admin_client.post(
            "/api/leads/",
            {
                "first_name": "Org A",
                "last_name": "Lead",
                "email": "shared@example.com",
            },
        )
        assert resp1.status_code == 200

        resp2 = org_b_client.post(
            "/api/leads/",
            {
                "first_name": "Org B",
                "last_name": "Lead",
                "email": "shared@example.com",
            },
        )
        assert resp2.status_code == 200
