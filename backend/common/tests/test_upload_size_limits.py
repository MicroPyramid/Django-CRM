"""Uploads outside the attachment endpoints obey the same size limit.

The fifteen ``*_attachment`` endpoints refuse a file over
``ATTACHMENT_MAX_BYTES`` through ``validate_attachment``. Three other uploads
never called it, so any member could store a document of any size, and an org
admin (which anyone who signs up is) a logo of any size, in storage every
tenant shares (issue #827): a document's file on create, ``PUT`` and ``PATCH``,
the org logo, and an invoice template's logo.

The limit is patched down to 2 MB so the files stay cheap to build;
``test_attachment_upload`` pins the real 25 MB boundary.
"""

import io
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from common.models import Document
from invoices.models import InvoiceTemplate

LIMIT = 2 * 1024 * 1024
REFUSAL = "Files must be 2 MB or smaller."


@pytest.fixture(autouse=True)
def small_limit():
    with mock.patch("common.utils.ATTACHMENT_MAX_BYTES", LIMIT):
        yield


def _blob(size):
    return SimpleUploadedFile("big.bin", b"x" * size)


def _image(min_size):
    """A real BMP of at least `min_size` bytes, so only its size can refuse it."""
    side = int((min_size / 3) ** 0.5) + 1
    buf = io.BytesIO()
    Image.new("RGB", (side, side)).save(buf, "BMP")
    return SimpleUploadedFile("logo.bmp", buf.getvalue(), content_type="image/bmp")


@pytest.mark.django_db
class TestDocumentFile:
    url = "/api/documents/"

    @pytest.fixture
    def doc(self, org_a, admin_user):
        return Document.objects.create(
            title="Kept",
            document_file="docs/kept.txt",
            org=org_a,
            created_by=admin_user,
        )

    def test_create_over_the_limit_is_refused(self, admin_client, org_a):
        resp = admin_client.post(
            self.url,
            {"title": "Big", "document_file": _blob(LIMIT + 1)},
            format="multipart",
        )
        assert resp.status_code == 400
        assert resp.json()["errors"]["document_file"] == [REFUSAL]
        assert not Document.objects.filter(org=org_a).exists()

    def test_create_at_the_limit_is_accepted(self, admin_client, org_a):
        resp = admin_client.post(
            self.url,
            {"title": "Fits", "document_file": _blob(LIMIT)},
            format="multipart",
        )
        assert resp.status_code == 201, resp.content
        assert Document.objects.filter(org=org_a, title="Fits").exists()

    @pytest.mark.parametrize("verb", ["put", "patch"])
    def test_replacing_over_the_limit_is_refused(self, admin_client, doc, verb):
        resp = getattr(admin_client, verb)(
            f"{self.url}{doc.id}/",
            {"document_file": _blob(LIMIT + 1)},
            format="multipart",
        )
        assert resp.status_code == 400
        assert resp.json()["errors"]["document_file"] == [REFUSAL]
        doc.refresh_from_db()
        assert doc.document_file.name == "docs/kept.txt"

    @pytest.mark.parametrize("verb", ["put", "patch"])
    def test_replacing_at_the_limit_is_accepted(self, admin_client, doc, verb):
        resp = getattr(admin_client, verb)(
            f"{self.url}{doc.id}/",
            {"document_file": _blob(LIMIT)},
            format="multipart",
        )
        assert resp.status_code == 200, resp.content
        doc.refresh_from_db()
        assert doc.document_file.name != "docs/kept.txt"


@pytest.mark.django_db
class TestOrgLogo:
    url = "/api/org/settings/"

    def test_over_the_limit_is_refused(self, admin_client, org_a):
        resp = admin_client.patch(
            self.url, {"logo": _image(LIMIT + 1)}, format="multipart"
        )
        assert resp.status_code == 400
        assert resp.json()["logo"] == [REFUSAL]
        org_a.refresh_from_db()
        assert not org_a.logo

    def test_under_the_limit_is_accepted(self, admin_client, org_a):
        resp = admin_client.patch(
            self.url, {"logo": _image(10_000)}, format="multipart"
        )
        assert resp.status_code == 200, resp.content
        org_a.refresh_from_db()
        assert org_a.logo


@pytest.mark.django_db
class TestInvoiceTemplateLogo:
    url = "/api/invoices/templates/"

    def test_create_over_the_limit_is_refused(self, admin_client, org_a):
        resp = admin_client.post(
            self.url, {"name": "Big", "logo": _image(LIMIT + 1)}, format="multipart"
        )
        assert resp.status_code == 400
        assert resp.json()["errors"]["logo"] == [REFUSAL]
        assert not InvoiceTemplate.objects.filter(org=org_a).exists()

    def test_update_over_the_limit_is_refused(self, admin_client, org_a):
        template = InvoiceTemplate.objects.create(name="Kept", org=org_a)
        resp = admin_client.put(
            f"{self.url}{template.id}/",
            {"logo": _image(LIMIT + 1)},
            format="multipart",
        )
        assert resp.status_code == 400
        assert resp.json()["errors"]["logo"] == [REFUSAL]
        template.refresh_from_db()
        assert not template.logo

    def test_under_the_limit_is_accepted(self, admin_client, org_a):
        resp = admin_client.post(
            self.url, {"name": "Small", "logo": _image(10_000)}, format="multipart"
        )
        assert resp.status_code == 201, resp.content
        assert InvoiceTemplate.objects.get(org=org_a, name="Small").logo
