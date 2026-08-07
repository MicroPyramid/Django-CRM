"""Uploading a file with an ordinary name used to answer HTTP 500.

``Attachments.file_name`` is 60 characters and ``Attachments.save()`` calls
``full_clean()``, so a longer name raised Django's ``ValidationError``, which is
not DRF's and arrived as a 500. Proven live against the running dev server
before the fix: a 91-character name, which is the default shape of an Android
screenshot, answered 500. Every phone in the world produces names like that,
which is why this had to be closed before the mobile client could upload
anything at all.

Fifteen endpoints each carried their own copy of the six lines that built an
attachment, so this was fifteen defects. They now share ``create_attachment``,
which is also where the size limit lives.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.serializers import ValidationError as DRFValidationError

from common.models import Attachments
from common.utils import (
    ATTACHMENT_MAX_BYTES,
    create_attachment,
    fit_attachment_file_name,
)
from tasks.models import Task

# 91 characters, the name a screenshot arrives with.
LONG_NAME = (
    "IMG_20260807_100432_Screenshot_2026-08-07-10-04-32-123_"
    "com.android.chrome_edited_final.jpg"
)
FIELD_MAX = Attachments._meta.get_field("file_name").max_length


class TestFittingTheName:
    """Pure, so every branch is reachable without a request."""

    def test_a_short_name_is_left_exactly_as_it_is(self):
        assert fit_attachment_file_name("notes.txt", FIELD_MAX) == "notes.txt"

    def test_a_long_name_is_cut_to_the_column(self):
        fitted = fit_attachment_file_name(LONG_NAME, FIELD_MAX)

        assert len(LONG_NAME) > FIELD_MAX
        assert len(fitted) == FIELD_MAX

    def test_the_extension_survives_the_cut(self):
        """What the extension tells you is worth more than the tail of a name.

        Truncating from the right alone would have left `...edited_fin`, and
        every file in the list would look like it had no type.
        """
        assert fit_attachment_file_name(LONG_NAME, FIELD_MAX).endswith(".jpg")

    def test_a_directory_part_is_dropped(self):
        # Django sanitizes the storage path itself. This label is echoed back
        # to clients and rendered, so it has no business carrying a path.
        assert fit_attachment_file_name("../../etc/passwd", FIELD_MAX) == "passwd"

    def test_a_windows_path_is_dropped_too(self):
        fitted = fit_attachment_file_name(r"C:\\Users\\me\\quote.pdf", FIELD_MAX)

        assert fitted == "quote.pdf"

    def test_an_absurd_extension_does_not_eat_the_whole_name(self):
        """A 200-character "extension" is not one, so the stem is what is kept."""
        fitted = fit_attachment_file_name("report." + "x" * 200, FIELD_MAX)

        assert fitted == "report"
        assert len(fitted) <= FIELD_MAX

    def test_an_empty_name_becomes_something_renderable(self):
        assert fit_attachment_file_name("", FIELD_MAX) == "attachment"
        assert fit_attachment_file_name(None, FIELD_MAX) == "attachment"


@pytest.mark.django_db
class TestUploadingThroughAnEndpoint:
    """The defect as a caller met it, on the endpoint mobile uploads to."""

    def _url(self, task):
        return f"/api/tasks/{task.id}/"

    @pytest.fixture
    def task(self, org_a):
        return Task.objects.create(
            title="Send the addendum", org=org_a, status="New", priority="Medium"
        )

    def test_a_long_filename_no_longer_500s(self, admin_client, task):
        response = admin_client.post(
            self._url(task),
            {"task_attachment": SimpleUploadedFile(LONG_NAME, b"bytes")},
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_the_stored_label_is_the_fitted_name(self, admin_client, task, org_a):
        admin_client.post(
            self._url(task),
            {"task_attachment": SimpleUploadedFile(LONG_NAME, b"bytes")},
            format="multipart",
        )

        stored = Attachments.objects.filter(org=org_a).latest("created_at")
        assert len(stored.file_name) <= FIELD_MAX
        assert stored.file_name.endswith(".jpg")

    def test_a_short_filename_still_arrives_intact(self, admin_client, task, org_a):
        """The other direction. The fix must not touch an ordinary upload."""
        admin_client.post(
            self._url(task),
            {"task_attachment": SimpleUploadedFile("notes.txt", b"bytes")},
            format="multipart",
        )

        stored = Attachments.objects.filter(org=org_a).latest("created_at")
        assert stored.file_name == "notes.txt"

    def test_the_attachment_is_scoped_to_the_callers_org(
        self, admin_client, task, org_a
    ):
        admin_client.post(
            self._url(task),
            {"task_attachment": SimpleUploadedFile("notes.txt", b"bytes")},
            format="multipart",
        )

        stored = Attachments.objects.latest("created_at")
        assert stored.org == org_a


@pytest.mark.django_db
class TestTheSizeLimit:
    """An authenticated user could previously store a file of any size.

    Nothing capped it: Django's ``DATA_UPLOAD_MAX_MEMORY_SIZE`` governs
    buffering, not file size, and file uploads are exempt from it. In production
    these go to S3, so the bill and the bucket were both unbounded.

    This is a floor, not a ceiling: the request body still crosses the wire
    before the view sees it. A real limit belongs in the web server too.
    """

    def test_a_file_over_the_limit_is_refused(self, org_a, admin_profile):
        task = Task.objects.create(
            title="Anything", org=org_a, status="New", priority="Medium"
        )
        oversized = SimpleUploadedFile("big.bin", b"x" * (ATTACHMENT_MAX_BYTES + 1))

        with pytest.raises(DRFValidationError):
            create_attachment(oversized, task, admin_profile)

    def test_nothing_is_stored_when_it_is_refused(self, org_a, admin_profile):
        """A rejection that had already written the file would be no limit."""
        task = Task.objects.create(
            title="Anything", org=org_a, status="New", priority="Medium"
        )
        oversized = SimpleUploadedFile("big.bin", b"x" * (ATTACHMENT_MAX_BYTES + 1))
        before = Attachments.objects.count()

        with pytest.raises(DRFValidationError):
            create_attachment(oversized, task, admin_profile)

        assert Attachments.objects.count() == before

    def test_a_file_at_the_limit_is_accepted(self, org_a, admin_profile):
        """The check has to be able to pass, and the boundary is inclusive."""
        task = Task.objects.create(
            title="Anything", org=org_a, status="New", priority="Medium"
        )
        at_limit = SimpleUploadedFile("big.bin", b"x" * ATTACHMENT_MAX_BYTES)

        attachment = create_attachment(at_limit, task, admin_profile)

        assert attachment.pk is not None


@pytest.mark.django_db
class TestAFileSentOnItsOwn:
    """A file with no comment beside it has to be stored.

    On leads it was not. The three lines that create the attachment sat inside
    ``if params.get("comment"):`` on the detail POST, so a file uploaded on its
    own was dropped and the endpoint answered 200 with the unchanged attachment
    list. No error, nothing stored, and the client had every reason to believe
    it had worked. Proven live before the fix, on the running dev server.

    Tasks, cases and opportunities were never nested. All four are pinned here
    because the mobile Attach button sends exactly this: one file, no comment.
    """

    def _upload(self, client, url, field):
        return client.post(
            url,
            {field: SimpleUploadedFile("evidence.pdf", b"bytes")},
            format="multipart",
        )

    def _count(self, org):
        return Attachments.objects.filter(org=org).count()

    def test_a_task_stores_it(self, admin_client, org_a):
        task = Task.objects.create(
            title="T", org=org_a, status="New", priority="Medium"
        )
        before = self._count(org_a)

        response = self._upload(
            admin_client, f"/api/tasks/{task.id}/", "task_attachment"
        )

        assert response.status_code == status.HTTP_200_OK
        assert self._count(org_a) == before + 1

    def test_a_lead_stores_it(self, admin_client, org_a):
        """The defect. This was 200 with nothing stored."""
        from leads.models import Lead

        lead = Lead.objects.create(
            first_name="Jill", last_name="Shaffer", email="j@example.test", org=org_a
        )
        before = self._count(org_a)

        response = self._upload(
            admin_client, f"/api/leads/{lead.id}/", "lead_attachment"
        )

        assert response.status_code == status.HTTP_200_OK
        assert self._count(org_a) == before + 1, "the file was dropped"

    def test_a_deal_stores_it(self, admin_client, org_a):
        from opportunity.models import Opportunity

        deal = Opportunity.objects.create(
            name="Renewal", org=org_a, stage="PROSPECTING"
        )
        before = self._count(org_a)

        response = self._upload(
            admin_client,
            f"/api/opportunities/{deal.id}/",
            "opportunity_attachment",
        )

        assert response.status_code == status.HTTP_200_OK
        assert self._count(org_a) == before + 1

    def test_a_ticket_stores_it(self, admin_client, org_a):
        from cases.models import Case

        case = Case.objects.create(name="Login fails", org=org_a, status="New")
        before = self._count(org_a)

        response = self._upload(
            admin_client, f"/api/cases/{case.id}/", "case_attachment"
        )

        assert response.status_code == status.HTTP_200_OK
        assert self._count(org_a) == before + 1

    def test_the_lead_response_shows_the_new_file(self, admin_client, org_a):
        """The client updates its list from this response rather than refetch.

        A count in the database is not enough: the mobile screen reads the
        `attachments` array the POST answers with, so an upload the response
        omits still looks like it failed.
        """
        from leads.models import Lead

        lead = Lead.objects.create(
            first_name="Jill", last_name="Shaffer", email="j2@example.test", org=org_a
        )

        response = self._upload(
            admin_client, f"/api/leads/{lead.id}/", "lead_attachment"
        )

        assert len(response.data["attachments"]) == 1
        assert response.data["attachments"][0]["file_name"] == "evidence.pdf"
