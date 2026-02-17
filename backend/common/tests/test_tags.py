"""
Tests for tag management views: list, create, detail, update, soft-delete, restore.

Run with: pytest common/tests/test_tags.py -v
"""

import pytest
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from common.models import Tags


@pytest.mark.django_db
class TestTagsListView:
    """Tests for GET/POST /api/tags/"""

    url = "/api/tags/"

    def test_create_tag(self, admin_client, org_a):
        response = admin_client.post(
            self.url,
            {"name": "Important"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["error"] is False
        assert response.data["tag"]["name"] == "Important"

    def test_list_tags(self, admin_client, org_a):
        Tags.objects.create(name="Urgent", slug="urgent", org=org_a)
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "tags" in response.data
        assert response.data["tags_count"] >= 1

    def test_unauthenticated(self, unauthenticated_client):
        with pytest.raises(PermissionDenied):
            unauthenticated_client.get(self.url)


@pytest.mark.django_db
class TestTagsDetailView:
    """Tests for GET/PUT/DELETE /api/tags/<pk>/ and POST /api/tags/<pk>/restore/"""

    def _url(self, pk):
        return f"/api/tags/{pk}/"

    def _restore_url(self, pk):
        return f"/api/tags/{pk}/restore/"

    def test_get_tag(self, admin_client, org_a):
        tag = Tags.objects.create(name="Feature", slug="feature", org=org_a)
        response = admin_client.get(self._url(tag.pk))
        assert response.status_code == status.HTTP_200_OK
        assert "tag" in response.data

    def test_update_tag(self, admin_client, org_a):
        tag = Tags.objects.create(name="Old Tag", slug="old-tag", org=org_a)
        response = admin_client.put(
            self._url(tag.pk),
            {"name": "New Tag"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert response.data["tag"]["name"] == "New Tag"

    def test_soft_delete_tag(self, admin_client, org_a):
        tag = Tags.objects.create(name="Deletable", slug="deletable", org=org_a)
        response = admin_client.delete(self._url(tag.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        # Tag still exists in the database but is inactive
        tag.refresh_from_db()
        assert tag.is_active is False

    def test_restore_tag(self, admin_client, org_a):
        tag = Tags.objects.create(
            name="Archived", slug="archived", org=org_a, is_active=False
        )
        response = admin_client.post(self._restore_url(tag.pk), format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        tag.refresh_from_db()
        assert tag.is_active is True
