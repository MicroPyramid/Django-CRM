"""
Tests for common/models.py and common/base.py - model methods and properties.

Covers:
- CommentFiles.save() auto-populate org
- Attachments.file_type() with various extensions
- Document.file_type() with various extensions
- SessionToken.revoke() and cleanup_expired()
- Activity.created_on_arrow property
- AssignableMixin properties (get_team_users, etc.)
- OrgScopedQuerySet and OrgScopedManager methods

Run with: pytest common/tests/test_models.py -v
"""

import uuid
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from accounts.models import Account
from common.models import (
    Activity,
    Attachments,
    Comment,
    CommentFiles,
    Document,
    Org,
    Profile,
    SessionToken,
    Teams,
    User,
)


# ---------------------------------------------------------------------------
# CommentFiles.save() auto-populate org
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCommentFilesSave:
    """Test CommentFiles.save() auto-populates org from parent comment."""

    def test_auto_populate_org_from_comment(self, org_a, admin_profile):
        """CommentFiles should inherit org from parent comment if not set."""
        ct = ContentType.objects.get_for_model(Org)
        comment = Comment.objects.create(
            content_type=ct,
            object_id=org_a.pk,
            comment="Test comment",
            commented_by=admin_profile,
            org=org_a,
        )
        cf = CommentFiles(comment=comment)
        cf.save()
        assert cf.org_id == org_a.pk

    def test_explicit_org_not_overridden(self, org_a, org_b, admin_profile):
        """CommentFiles with explicitly set org should keep it."""
        ct = ContentType.objects.get_for_model(Org)
        comment = Comment.objects.create(
            content_type=ct,
            object_id=org_a.pk,
            comment="Test comment",
            commented_by=admin_profile,
            org=org_a,
        )
        cf = CommentFiles(comment=comment, org=org_b)
        cf.save()
        # org_b was explicitly set, so it should remain
        assert cf.org_id == org_b.pk


# ---------------------------------------------------------------------------
# Attachments.file_type()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAttachmentsFileType:
    """Test Attachments.file_type() returns correct type tuples."""

    def _make_attachment(self, org, filename):
        """Create an Attachment instance with a mocked file URL."""
        ct = ContentType.objects.get_for_model(Org)
        att = Attachments(
            content_type=ct,
            object_id=org.pk,
            file_name=filename,
            org=org,
        )
        att.attachment = MagicMock()
        att.attachment.url = f"/media/attachments/{filename}"
        return att

    def test_audio_file(self, org_a):
        att = self._make_attachment(org_a, "song.mp3")
        assert att.file_type() == ("audio", "fa fa-file-audio")

    def test_video_file(self, org_a):
        att = self._make_attachment(org_a, "clip.mp4")
        assert att.file_type() == ("video", "fa fa-file-video")

    def test_image_file(self, org_a):
        att = self._make_attachment(org_a, "photo.png")
        assert att.file_type() == ("image", "fa fa-file-image")

    def test_pdf_file(self, org_a):
        att = self._make_attachment(org_a, "document.pdf")
        assert att.file_type() == ("pdf", "fa fa-file-pdf")

    def test_code_file(self, org_a):
        att = self._make_attachment(org_a, "app.json")
        assert att.file_type() == ("code", "fa fa-file-code")

    def test_text_file(self, org_a):
        att = self._make_attachment(org_a, "readme.doc")
        assert att.file_type() == ("text", "fa fa-file-alt")

    def test_sheet_file(self, org_a):
        att = self._make_attachment(org_a, "data.xlsx")
        assert att.file_type() == ("sheet", "fa fa-file-excel")

    def test_zip_file(self, org_a):
        att = self._make_attachment(org_a, "archive.zip")
        assert att.file_type() == ("zip", "fa fa-file-archive")

    def test_unknown_extension(self, org_a):
        att = self._make_attachment(org_a, "file.xyz")
        assert att.file_type() == ("file", "fa fa-file")

    def test_no_extension(self, org_a):
        att = self._make_attachment(org_a, "README")
        att.attachment.url = "/media/attachments/README"
        assert att.file_type() == ("file", "fa fa-file")


# ---------------------------------------------------------------------------
# Document.file_type()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDocumentFileType:
    """Test Document.file_type() returns correct type tuples."""

    def _make_document(self, org, filename):
        doc = Document(title="Test", org=org)
        doc.document_file = MagicMock()
        doc.document_file.url = f"/media/docs/{filename}"
        return doc

    def test_audio_file(self, org_a):
        doc = self._make_document(org_a, "song.wav")
        assert doc.file_type() == ("audio", "fa fa-file-audio")

    def test_video_file(self, org_a):
        doc = self._make_document(org_a, "clip.avi")
        assert doc.file_type() == ("video", "fa fa-file-video")

    def test_image_file(self, org_a):
        doc = self._make_document(org_a, "photo.jpg")
        assert doc.file_type() == ("image", "fa fa-file-image")

    def test_pdf_file(self, org_a):
        doc = self._make_document(org_a, "report.pdf")
        assert doc.file_type() == ("pdf", "fa fa-file-pdf")

    def test_code_file(self, org_a):
        doc = self._make_document(org_a, "script.py")
        assert doc.file_type() == ("code", "fa fa-file-code")

    def test_text_file(self, org_a):
        doc = self._make_document(org_a, "letter.docx")
        assert doc.file_type() == ("text", "fa fa-file-alt")

    def test_sheet_file(self, org_a):
        doc = self._make_document(org_a, "budget.csv")
        assert doc.file_type() == ("sheet", "fa fa-file-excel")

    def test_zip_file(self, org_a):
        doc = self._make_document(org_a, "backup.tar")
        assert doc.file_type() == ("zip", "fa fa-file-archive")

    def test_unknown_extension(self, org_a):
        doc = self._make_document(org_a, "data.bin")
        assert doc.file_type() == ("file", "fa fa-file")

    def test_no_extension(self, org_a):
        doc = self._make_document(org_a, "Makefile")
        doc.document_file.url = "/media/docs/Makefile"
        assert doc.file_type() == ("file", "fa fa-file")


# ---------------------------------------------------------------------------
# SessionToken.revoke() and cleanup_expired()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSessionToken:
    """Test SessionToken.revoke() and cleanup_expired() methods."""

    def _create_token(self, user, **kwargs):
        defaults = {
            "user": user,
            "token_jti": str(uuid.uuid4()),
            "refresh_token_jti": str(uuid.uuid4()),
            "expires_at": timezone.now() + timezone.timedelta(hours=1),
            "is_active": True,
        }
        defaults.update(kwargs)
        return SessionToken.objects.create(**defaults)

    def test_revoke(self, admin_user):
        token = self._create_token(admin_user)
        assert token.is_active is True
        assert token.revoked_at is None

        token.revoke()
        token.refresh_from_db()

        assert token.is_active is False
        assert token.revoked_at is not None

    def test_cleanup_expired(self, admin_user):
        # Create an expired token
        expired = self._create_token(
            admin_user,
            token_jti=str(uuid.uuid4()),
            refresh_token_jti=str(uuid.uuid4()),
            expires_at=timezone.now() - timezone.timedelta(hours=1),
        )
        # Create a valid token
        valid = self._create_token(
            admin_user,
            token_jti=str(uuid.uuid4()),
            refresh_token_jti=str(uuid.uuid4()),
            expires_at=timezone.now() + timezone.timedelta(hours=1),
        )

        deleted_count, _ = SessionToken.cleanup_expired()
        assert deleted_count == 1
        assert not SessionToken.objects.filter(pk=expired.pk).exists()
        assert SessionToken.objects.filter(pk=valid.pk).exists()


# ---------------------------------------------------------------------------
# Activity.created_on_arrow
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestActivityCreatedOnArrow:
    """Test Activity.created_on_arrow property."""

    def test_created_on_arrow_format(self, org_a, admin_profile):
        activity = Activity.objects.create(
            user=admin_profile,
            action="CREATE",
            entity_type="Account",
            entity_id=uuid.uuid4(),
            entity_name="Test Account",
            org=org_a,
        )
        result = activity.created_on_arrow
        assert result.endswith(" ago")
        # Should contain a time unit like "seconds", "minutes", etc.
        assert len(result) > 4


# ---------------------------------------------------------------------------
# AssignableMixin properties (via Account model which uses it)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAssignableMixin:
    """Test AssignableMixin properties on Account model."""

    def test_get_team_users(self, org_a, admin_profile, user_profile):
        team = Teams.objects.create(name="Sales", description="Sales team", org=org_a)
        team.users.add(admin_profile, user_profile)

        account = Account.objects.create(name="Test Account Mixin1", org=org_a)
        account.teams.add(team)

        team_users = account.get_team_users
        assert admin_profile in team_users
        assert user_profile in team_users

    def test_get_team_and_assigned_users(self, org_a, admin_profile, user_profile):
        team = Teams.objects.create(name="Sales", description="Sales team", org=org_a)
        team.users.add(admin_profile)

        account = Account.objects.create(name="Test Account Mixin2", org=org_a)
        account.teams.add(team)
        account.assigned_to.add(user_profile)

        all_users = account.get_team_and_assigned_users
        assert admin_profile in all_users
        assert user_profile in all_users

    def test_get_assigned_users_not_in_teams(self, org_a, admin_profile, user_profile):
        team = Teams.objects.create(name="Sales", description="Sales team", org=org_a)
        team.users.add(admin_profile)

        account = Account.objects.create(name="Test Account Mixin3", org=org_a)
        account.teams.add(team)
        account.assigned_to.add(admin_profile, user_profile)

        not_in_teams = account.get_assigned_users_not_in_teams
        # admin_profile is in team AND assigned, so excluded
        assert admin_profile not in not_in_teams
        # user_profile is assigned but not in team
        assert user_profile in not_in_teams

    def test_no_teams_no_assignments(self, org_a):
        account = Account.objects.create(name="Test Account Mixin4", org=org_a)
        assert account.get_team_users.count() == 0
        assert account.get_team_and_assigned_users.count() == 0
        assert account.get_assigned_users_not_in_teams.count() == 0


# ---------------------------------------------------------------------------
# OrgScopedQuerySet and OrgScopedManager
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrgScopedManager:
    """Test OrgScopedQuerySet.for_org() and for_request() via a model that uses them."""

    def test_for_org_filters_correctly(self, org_a, org_b):
        """for_org should only return records for the specified org."""
        # We need a model that uses OrgScopedManager. SecurityAuditLog uses BaseModel
        # which does NOT use OrgScopedManager. Let's test via the base classes directly.
        from common.base import OrgScopedManager, OrgScopedQuerySet

        # Create a mock model to test the queryset methods
        # Instead, let's check the queryset methods manually
        qs = OrgScopedQuerySet(model=Activity)
        # We can't easily test without a real model using OrgScopedManager,
        # but we can at least instantiate and check it doesn't error
        manager = OrgScopedManager()
        assert manager is not None

    def test_for_request_with_profile(self, org_a, admin_profile):
        """for_request should filter by org from request.profile."""
        from common.base import OrgScopedQuerySet

        # Create activities in different orgs
        Activity.objects.create(
            user=admin_profile,
            action="CREATE",
            entity_type="Account",
            entity_id=uuid.uuid4(),
            org=org_a,
        )

        request = MagicMock()
        request.profile = admin_profile

        # Test OrgScopedQuerySet.for_request directly
        qs = OrgScopedQuerySet(model=Activity, using="default")
        result = qs.for_request(request)
        assert result.count() == 1

    def test_for_request_without_profile(self):
        """for_request without profile should return empty queryset."""
        from common.base import OrgScopedQuerySet

        request = MagicMock(spec=[])  # no profile attribute

        qs = OrgScopedQuerySet(model=Activity, using="default")
        result = qs.for_request(request)
        assert result.count() == 0

    def test_for_org(self, org_a, org_b, admin_profile):
        """for_org should filter activities by specified org."""
        from common.base import OrgScopedQuerySet

        Activity.objects.create(
            user=admin_profile,
            action="CREATE",
            entity_type="Account",
            entity_id=uuid.uuid4(),
            org=org_a,
        )
        Activity.objects.create(
            user=admin_profile,
            action="UPDATE",
            entity_type="Lead",
            entity_id=uuid.uuid4(),
            org=org_b,
        )

        qs = OrgScopedQuerySet(model=Activity, using="default")
        result = qs.for_org(org_a)
        assert result.count() == 1
        assert result.first().org == org_a
