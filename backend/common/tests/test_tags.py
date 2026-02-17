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

    def test_create_tag_non_admin_forbidden(self, user_client, org_a):
        """Non-admin user cannot create tags."""
        response = user_client.post(
            self.url,
            {"name": "No Permission"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_tag_empty_name(self, admin_client, org_a):
        """Creating a tag with empty name should fail."""
        response = admin_client.post(
            self.url,
            {"name": ""},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_tag_duplicate_name(self, admin_client, org_a):
        """Creating a tag with duplicate name in same org should fail."""
        Tags.objects.create(name="Duplicate", slug="duplicate", org=org_a)
        response = admin_client.post(
            self.url,
            {"name": "Duplicate"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_tag_reactivate_archived(self, admin_client, org_a):
        """Creating tag with same name as archived tag reactivates it."""
        Tags.objects.create(
            name="Archived Tag", slug="archived-tag", org=org_a, is_active=False
        )
        response = admin_client.post(
            self.url,
            {"name": "Archived Tag"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "reactivated" in response.data["message"].lower()

    def test_create_tag_with_color(self, admin_client, org_a):
        """Create a tag with a specific color."""
        response = admin_client.post(
            self.url,
            {"name": "Red Tag", "color": "red"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["tag"]["color"] == "red"

    def test_create_tag_invalid_color_defaults_to_blue(self, admin_client, org_a):
        """Invalid color should default to blue."""
        response = admin_client.post(
            self.url,
            {"name": "Invalid Color Tag", "color": "neon"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["tag"]["color"] == "blue"

    def test_create_tag_with_description(self, admin_client, org_a):
        """Create a tag with description."""
        response = admin_client.post(
            self.url,
            {"name": "Described Tag", "description": "A tag with description"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["tag"]["description"] == "A tag with description"

    def test_list_tags_excludes_archived(self, admin_client, org_a):
        """Archived tags are not returned by default."""
        Tags.objects.create(name="Active Tag", slug="active-tag", org=org_a)
        Tags.objects.create(
            name="Archived Tag", slug="archived-tag", org=org_a, is_active=False
        )
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["tags_count"] == 1

    def test_list_tags_include_archived(self, admin_client, org_a):
        """Archived tags are included when include_archived=true."""
        Tags.objects.create(name="Active Tag2", slug="active-tag2", org=org_a)
        Tags.objects.create(
            name="Archived Tag2", slug="archived-tag2", org=org_a, is_active=False
        )
        response = admin_client.get(self.url + "?include_archived=true")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["tags_count"] == 2

    def test_list_tags_filter_by_name(self, admin_client, org_a):
        """Filter tags by name."""
        Tags.objects.create(name="Priority", slug="priority", org=org_a)
        Tags.objects.create(name="Urgent", slug="urgent", org=org_a)
        response = admin_client.get(self.url + "?name=Pri")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["tags_count"] == 1


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

    def test_get_tag_not_found(self, admin_client, org_a):
        """Getting a non-existent tag returns 404."""
        import uuid

        fake_id = uuid.uuid4()
        response = admin_client.get(self._url(fake_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_tag_duplicate_name(self, admin_client, org_a):
        """Updating a tag to a name that already exists should fail."""
        Tags.objects.create(name="Existing", slug="existing", org=org_a)
        tag = Tags.objects.create(name="To Update", slug="to-update", org=org_a)
        response = admin_client.put(
            self._url(tag.pk),
            {"name": "Existing"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_tag_empty_name(self, admin_client, org_a):
        """Updating a tag with empty name should fail."""
        tag = Tags.objects.create(name="Empty Update", slug="empty-update", org=org_a)
        response = admin_client.put(
            self._url(tag.pk),
            {"name": ""},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_tag_non_admin_forbidden(self, user_client, org_a):
        """Non-admin user cannot update tags."""
        tag = Tags.objects.create(name="Admin Only", slug="admin-only", org=org_a)
        response = user_client.put(
            self._url(tag.pk),
            {"name": "Not Allowed"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_tag_non_admin_forbidden(self, user_client, org_a):
        """Non-admin user cannot archive tags."""
        tag = Tags.objects.create(name="No Delete", slug="no-delete", org=org_a)
        response = user_client.delete(self._url(tag.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restore_tag_non_admin_forbidden(self, user_client, org_a):
        """Non-admin user cannot restore tags."""
        tag = Tags.objects.create(
            name="No Restore", slug="no-restore", org=org_a, is_active=False
        )
        response = user_client.post(self._restore_url(tag.pk), format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_tag_not_found(self, admin_client, org_a):
        """Updating non-existent tag returns 404."""
        import uuid

        fake_id = uuid.uuid4()
        response = admin_client.put(
            self._url(fake_id),
            {"name": "Ghost Tag"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_tag_not_found(self, admin_client, org_a):
        """Archiving non-existent tag returns 404."""
        import uuid

        fake_id = uuid.uuid4()
        response = admin_client.delete(self._url(fake_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_restore_tag_not_found(self, admin_client, org_a):
        """Restoring non-existent tag returns 404."""
        import uuid

        fake_id = uuid.uuid4()
        response = admin_client.post(self._restore_url(fake_id), format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_tag_with_color(self, admin_client, org_a):
        """Update tag color."""
        tag = Tags.objects.create(name="Color Tag", slug="color-tag", org=org_a)
        response = admin_client.put(
            self._url(tag.pk),
            {"name": "Color Tag", "color": "green"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["tag"]["color"] == "green"

    def test_update_tag_with_description(self, admin_client, org_a):
        """Update tag description."""
        tag = Tags.objects.create(name="Desc Tag", slug="desc-tag", org=org_a)
        response = admin_client.put(
            self._url(tag.pk),
            {"name": "Desc Tag", "description": "Updated description"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
