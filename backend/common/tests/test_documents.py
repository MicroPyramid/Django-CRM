"""
Tests for document management views: list, create, detail, update, delete.

Run with: pytest common/tests/test_documents.py -v
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from common.models import Document, Teams


@pytest.mark.django_db
class TestDocumentListView:
    """Tests for GET/POST /api/documents/"""

    url = "/api/documents/"

    def test_list_documents(self, admin_client):
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "documents_active" in response.data

    def test_create_document(self, admin_client):
        test_file = SimpleUploadedFile(
            "test.txt", b"file content", content_type="text/plain"
        )
        response = admin_client.post(
            self.url,
            {"title": "Test Document", "document_file": test_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["error"] is False

    def test_unauthenticated(self, unauthenticated_client):
        """The request is refused, and refused as a response, not an exception.

        DRF catches ``PermissionDenied`` in ``handle_exception`` and renders it,
        so a test client never sees it raised. Wrapping the call in
        ``pytest.raises`` therefore failed with DID NOT RAISE no matter how the
        endpoint behaved, which meant this test could never have caught the
        access opening up.
        """
        response = unauthenticated_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_documents_context_keys(self, admin_client, org_a):
        """Document list should include all expected context keys."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert "documents_active" in data
        assert "documents_inactive" in data
        assert "users" in data
        assert "status_choices" in data
        assert "search" in data

    def test_create_document_with_shared_to(self, admin_client, org_a, admin_profile):
        """Create document with shared_to profiles via multipart with JSON string."""
        import json

        test_file = SimpleUploadedFile(
            "shared.txt", b"shared content", content_type="text/plain"
        )
        response = admin_client.post(
            self.url,
            {
                "title": "Shared Document",
                "document_file": test_file,
                "shared_to": json.dumps([str(admin_profile.id)]),
            },
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["error"] is False

    def test_create_document_with_teams(self, admin_client, org_a):
        """Create document with teams via multipart with JSON string."""
        import json

        team = Teams.objects.create(name="Doc Team", description="DT", org=org_a)
        test_file = SimpleUploadedFile(
            "team_doc.txt", b"team content", content_type="text/plain"
        )
        response = admin_client.post(
            self.url,
            {
                "title": "Team Document",
                "document_file": test_file,
                "teams": json.dumps([str(team.id)]),
            },
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_document_duplicate_title(self, admin_client, org_a, admin_user):
        """Creating a document with a duplicate title should fail."""
        Document.objects.create(
            title="Duplicate Title",
            document_file="docs/dup.txt",
            org=org_a,
            created_by=admin_user,
        )
        test_file = SimpleUploadedFile(
            "dup.txt", b"dup content", content_type="text/plain"
        )
        response = admin_client.post(
            self.url,
            {"title": "Duplicate Title", "document_file": test_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_documents_filter_by_title(self, admin_client, org_a, admin_user):
        """Filter documents by title query parameter."""
        Document.objects.create(
            title="Alpha Doc",
            document_file="docs/alpha.txt",
            org=org_a,
            created_by=admin_user,
        )
        Document.objects.create(
            title="Beta Doc",
            document_file="docs/beta.txt",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.get(self.url + "?title=Alpha")
        assert response.status_code == status.HTTP_200_OK
        active = response.data["documents_active"]["documents_active"]
        assert len(active) == 1
        assert active[0]["title"] == "Alpha Doc"

    def test_list_documents_filter_by_title_search(
        self, admin_client, org_a, admin_user
    ):
        """Filter documents by title triggers search flag."""
        Document.objects.create(
            title="Searchable Doc",
            document_file="docs/search.txt",
            status="active",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.get(self.url + "?title=Searchable")
        assert response.status_code == status.HTTP_200_OK
        active = response.data["documents_active"]["documents_active"]
        assert len(active) == 1


@pytest.mark.django_db
class TestDocumentDetailView:
    """Tests for GET/PUT/PATCH/DELETE /api/documents/<pk>/"""

    def _url(self, pk):
        return f"/api/documents/{pk}/"

    def _create_doc(self, org, user, title="Sample Doc"):
        """Helper to create a document directly in the database."""
        return Document.objects.create(
            title=title,
            document_file="docs/sample.txt",
            org=org,
            created_by=user,
        )

    def test_get_document(self, admin_client, org_a, admin_user):
        doc = self._create_doc(org_a, admin_user)
        response = admin_client.get(self._url(doc.pk))
        assert response.status_code == status.HTTP_200_OK
        assert "doc_obj" in response.data

    def test_update_document(self, admin_client, org_a, admin_user):
        doc = self._create_doc(org_a, admin_user)
        response = admin_client.put(
            self._url(doc.pk),
            {"title": "Updated Title"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_delete_document(self, admin_client, org_a, admin_user):
        doc = self._create_doc(org_a, admin_user)
        response = admin_client.delete(self._url(doc.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert not Document.objects.filter(pk=doc.pk).exists()

    def test_org_isolation(self, org_b_client, org_a, admin_user, admin_profile):
        """org_b_client cannot access a document belonging to org_a."""
        doc = self._create_doc(org_a, admin_user)
        response = org_b_client.get(self._url(doc.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_document_context(self, admin_client, org_a, admin_user):
        """Document detail should return file type and users."""
        doc = self._create_doc(org_a, admin_user)
        response = admin_client.get(self._url(doc.pk))
        assert response.status_code == status.HTTP_200_OK
        assert "doc_obj" in response.data
        assert "file_type_code" in response.data
        assert "users" in response.data

    def test_get_document_non_admin_not_shared(
        self, user_client, org_a, admin_user, user_profile
    ):
        """Non-admin user not shared to cannot view the document."""
        doc = self._create_doc(org_a, admin_user)
        response = user_client.get(self._url(doc.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_document_non_admin_shared_to(
        self, user_client, org_a, admin_user, user_profile
    ):
        """Non-admin user who is shared_to can view the document."""
        doc = self._create_doc(org_a, admin_user)
        doc.shared_to.add(user_profile)
        response = user_client.get(self._url(doc.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_update_document_with_shared_to(
        self, admin_client, org_a, admin_user, admin_profile
    ):
        """Update document with shared_to."""
        import json

        doc = self._create_doc(org_a, admin_user)
        response = admin_client.put(
            self._url(doc.pk),
            {
                "title": "Updated Sharing",
                "shared_to": json.dumps([str(admin_profile.id)]),
            },
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK
        doc.refresh_from_db()
        assert doc.shared_to.count() == 1

    def test_update_document_with_teams(self, admin_client, org_a, admin_user):
        """Update document with teams."""
        import json

        doc = self._create_doc(org_a, admin_user)
        team = Teams.objects.create(name="Update Team", description="UT", org=org_a)
        response = admin_client.put(
            self._url(doc.pk),
            {
                "title": "Team Update",
                "teams": json.dumps([str(team.id)]),
            },
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK
        doc.refresh_from_db()
        assert doc.teams.count() == 1

    def test_delete_document_non_admin_own(
        self, user_client, org_a, regular_user, user_profile
    ):
        """A non-admin can delete a document they uploaded.

        This previously asserted 403 and said so in its own docstring: the
        view compared `request.profile` (a Profile) with `doc.created_by` (a
        **User** FK), so the branch was always False and nobody could remove
        their own upload. The comparison now uses `created_by_id` against
        `profile.user_id`. See `common/tests/test_documents_access.py` for the
        full matrix, including the cases that must still be refused.
        """
        doc = self._create_doc(org_a, regular_user)
        # Manually set created_by since crum overrides it in tests
        Document.objects.filter(id=doc.id).update(created_by=regular_user)
        response = user_client.delete(self._url(doc.pk))
        assert response.status_code == status.HTTP_200_OK
        assert not Document.objects.filter(id=doc.id).exists()

    def test_delete_document_non_admin_other(
        self, user_client, org_a, admin_user, user_profile
    ):
        """Non-admin cannot delete someone else's document."""
        doc = self._create_doc(org_a, admin_user)
        response = user_client.delete(self._url(doc.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_document_non_admin_not_shared(
        self, user_client, org_a, admin_user, user_profile
    ):
        """Non-admin not shared to cannot update the document."""
        doc = self._create_doc(org_a, admin_user)
        response = user_client.put(
            self._url(doc.pk),
            {"title": "Not Allowed"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_document(self, admin_client, org_a, admin_user):
        """Test partial update via PATCH."""
        doc = self._create_doc(org_a, admin_user)
        response = admin_client.patch(
            self._url(doc.pk),
            {"title": "Patched Title"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_patch_document_non_admin_forbidden(
        self, user_client, org_a, admin_user, user_profile
    ):
        """Non-admin not shared to cannot PATCH the document."""
        doc = self._create_doc(org_a, admin_user)
        response = user_client.patch(
            self._url(doc.pk),
            {"title": "Nope"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
