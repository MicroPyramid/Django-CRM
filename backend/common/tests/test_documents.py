"""
Tests for document management views: list, create, detail, update, delete.

Run with: pytest common/tests/test_documents.py -v
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from common.models import Document


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
        with pytest.raises(PermissionDenied):
            unauthenticated_client.get(self.url)


@pytest.mark.django_db
class TestDocumentDetailView:
    """Tests for GET/PUT/DELETE /api/documents/<pk>/"""

    def _url(self, pk):
        return f"/api/documents/{pk}/"

    def _create_doc(self, org, user):
        """Helper to create a document directly in the database."""
        return Document.objects.create(
            title="Sample Doc",
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
