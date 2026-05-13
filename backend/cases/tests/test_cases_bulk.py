"""Tests for the bulk update / bulk delete Case endpoints."""

import pytest


@pytest.mark.django_db
class TestBulkUpdateCases:
    def test_bulk_update_status(self, admin_client, case_a, case_b_same_org):
        response = admin_client.post(
            "/api/cases/bulk/update/",
            {
                "ids": [str(case_a.pk), str(case_b_same_org.pk)],
                "fields": {"status": "Pending"},
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        case_a.refresh_from_db()
        case_b_same_org.refresh_from_db()
        assert case_a.status == "Pending"
        assert case_b_same_org.status == "Pending"

    def test_bulk_update_priority(self, admin_client, case_a):
        response = admin_client.post(
            "/api/cases/bulk/update/",
            {"ids": [str(case_a.pk)], "fields": {"priority": "Urgent"}},
            content_type="application/json",
        )
        assert response.status_code == 200
        case_a.refresh_from_db()
        assert case_a.priority == "Urgent"

    def test_bulk_update_rejects_unknown_field(self, admin_client, case_a):
        response = admin_client.post(
            "/api/cases/bulk/update/",
            {"ids": [str(case_a.pk)], "fields": {"name": "hacker"}},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_bulk_update_skips_other_org(self, admin_client, case_a, case_b):
        response = admin_client.post(
            "/api/cases/bulk/update/",
            {
                "ids": [str(case_a.pk), str(case_b.pk)],
                "fields": {"status": "Closed", "closed_on": "2026-05-09"},
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["updated"] == 1
        case_b.refresh_from_db()
        assert case_b.status != "Closed"

    def test_bulk_update_empty_ids(self, admin_client):
        response = admin_client.post(
            "/api/cases/bulk/update/",
            {"ids": [], "fields": {"status": "Pending"}},
            content_type="application/json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestBulkDeleteCases:
    def test_bulk_delete_soft(self, admin_client, case_a, case_b_same_org):
        response = admin_client.post(
            "/api/cases/bulk/delete/",
            {"ids": [str(case_a.pk), str(case_b_same_org.pk)]},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["deleted"] == 2
        case_a.refresh_from_db()
        case_b_same_org.refresh_from_db()
        assert case_a.is_active is False
        assert case_b_same_org.is_active is False

    def test_bulk_delete_skips_other_org(self, admin_client, case_a, case_b):
        response = admin_client.post(
            "/api/cases/bulk/delete/",
            {"ids": [str(case_a.pk), str(case_b.pk)]},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["deleted"] == 1
        case_b.refresh_from_db()
        assert case_b.is_active is True

    def test_bulk_delete_empty(self, admin_client):
        response = admin_client.post(
            "/api/cases/bulk/delete/",
            {"ids": []},
            content_type="application/json",
        )
        assert response.status_code == 400
