import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import PermissionDenied

from accounts.models import Account
from common.models import Attachments, Comment, Tags


@pytest.mark.django_db
class TestAccountListView:
    """Tests for GET /api/accounts/ and POST /api/accounts/."""

    def test_list_accounts(self, admin_client, org_a):
        Account.objects.create(name="Test Account", org=org_a)
        response = admin_client.get("/api/accounts/")
        assert response.status_code == 200
        data = response.json()
        assert "active_accounts" in data

    def test_create_account(self, admin_client, org_a):
        response = admin_client.post("/api/accounts/", {"name": "New Account"})
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert Account.objects.filter(name="New Account", org=org_a).exists()

    def test_create_account_with_tags(self, admin_client, org_a):
        tag = Tags.objects.create(name="VIP", org=org_a)
        response = admin_client.post(
            "/api/accounts/",
            {"name": "Tagged Account", "tags": [str(tag.id)]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False

    def test_create_account_invalid_data(self, admin_client):
        response = admin_client.post("/api/accounts/", {})
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    def test_create_account_unauthenticated(self, unauthenticated_client):
        with pytest.raises(PermissionDenied):
            unauthenticated_client.post(
                "/api/accounts/", {"name": "Test"}
            )


@pytest.mark.django_db
class TestAccountDetailView:
    """Tests for GET/PUT/DELETE /api/accounts/<pk>/."""

    def test_get_account_detail(self, admin_client, org_a):
        account = Account.objects.create(name="Detail Account", org=org_a)
        response = admin_client.get(f"/api/accounts/{account.id}/")
        assert response.status_code == 200
        data = response.json()
        assert "account_obj" in data

    def test_update_account(self, admin_client, org_a):
        account = Account.objects.create(name="Old Name", org=org_a)
        response = admin_client.put(
            f"/api/accounts/{account.id}/",
            {"name": "New Name"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False

    def test_delete_account(self, admin_client, org_a):
        account = Account.objects.create(name="Delete Me", org=org_a)
        response = admin_client.delete(f"/api/accounts/{account.id}/")
        assert response.status_code == 200
        assert not Account.objects.filter(id=account.id).exists()

    def test_get_account_cross_org(self, org_b_client, org_a):
        account = Account.objects.create(name="Org A Account", org=org_a)
        response = org_b_client.get(f"/api/accounts/{account.id}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestAccountCommentView:
    """Tests for PUT/DELETE /api/accounts/comment/<pk>/."""

    def test_edit_comment(self, admin_client, admin_profile, org_a):
        account = Account.objects.create(name="Comment Account", org=org_a)
        ct = ContentType.objects.get_for_model(Account)
        comment = Comment.objects.create(
            content_type=ct,
            object_id=account.id,
            comment="Test comment",
            commented_by=admin_profile,
            org=org_a,
            created_by=admin_profile.user,
            updated_by=admin_profile.user,
        )
        response = admin_client.put(
            f"/api/accounts/comment/{comment.id}/",
            {"comment": "Updated"},
            format="json",
        )
        assert response.status_code == 200

    def test_delete_comment(self, admin_client, admin_profile, org_a):
        account = Account.objects.create(name="Comment Account", org=org_a)
        ct = ContentType.objects.get_for_model(Account)
        comment = Comment.objects.create(
            content_type=ct,
            object_id=account.id,
            comment="Delete me",
            commented_by=admin_profile,
            org=org_a,
            created_by=admin_profile.user,
            updated_by=admin_profile.user,
        )
        response = admin_client.delete(
            f"/api/accounts/comment/{comment.id}/"
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestAccountAttachmentView:
    """Tests for DELETE /api/accounts/attachment/<pk>/."""

    def test_delete_attachment(self, admin_client, admin_profile, org_a):
        account = Account.objects.create(name="Attachment Account", org=org_a)
        ct = ContentType.objects.get_for_model(Account)
        attachment = Attachments.objects.create(
            content_type=ct,
            object_id=account.id,
            file_name="test.txt",
            attachment=SimpleUploadedFile("test.txt", b"content"),
            org=org_a,
            created_by=admin_profile.user,
        )
        response = admin_client.delete(
            f"/api/accounts/attachment/{attachment.id}/"
        )
        assert response.status_code == 200
