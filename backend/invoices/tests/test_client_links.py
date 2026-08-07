"""Every link that leaves the system in an email must be reachable.

Four builders emitted four different broken URLs. The invoice and estimate
portal links doubled the scheme (``http://http://localhost:8000/portal/...``)
because the caller passed ``DOMAIN_NAME``, which already has one, into an
``f"{protocol}://{domain}/..."`` template. The estimate task was dispatched with
no domain at all and fell back to ``http://localhost/``. The CSAT builder read
``DOMAIN_NAME`` directly, and `backend/.env` sets it to the empty string, so it
emitted the relative ``/csat/<token>``.

The assertions are deliberately about URL shape rather than an exact string: the
one-scheme check is what every one of those bugs failed, and it keeps holding
whatever host an operator configures.
"""

import re

import pytest
from django.test import override_settings

from common.links import frontend_url


class TestFrontendUrl:
    @override_settings(FRONTEND_URL="https://app.example.com")
    def test_builds_absolute_url(self):
        assert (
            frontend_url("/portal/invoice/abc")
            == "https://app.example.com/portal/invoice/abc"
        )

    @override_settings(FRONTEND_URL="https://app.example.com/")
    def test_strips_a_trailing_slash_on_the_base(self):
        assert frontend_url("/csat/abc") == "https://app.example.com/csat/abc"

    @override_settings(FRONTEND_URL="https://app.example.com")
    def test_leading_slash_on_the_path_is_optional(self):
        assert frontend_url("csat/abc") == "https://app.example.com/csat/abc"

    @override_settings(FRONTEND_URL="https://app.example.com")
    def test_exactly_one_scheme(self):
        """The bug: DOMAIN_NAME carries a scheme and the template added another."""
        assert len(re.findall(r"https?://", frontend_url("/portal/invoice/t"))) == 1


@pytest.mark.django_db
class TestEmittedLinks:
    """Drive the real builders and inspect the URL they hand the template."""

    @override_settings(FRONTEND_URL="https://app.example.com")
    def test_invoice_portal_link(self, org_a, admin_profile):
        from invoices.models import Invoice
        from invoices.tasks import send_invoice_to_client

        invoice = Invoice.objects.create(
            org=org_a,
            invoice_title="Portal link",
            client_email="client@example.com",
            public_link_enabled=True,
        )
        captured = {}

        import invoices.tasks as tasks_module

        original = tasks_module.render_to_string

        def spy(template, context=None, **kwargs):
            captured.update(context or {})
            return original(template, context=context, **kwargs)

        tasks_module.render_to_string = spy
        try:
            send_invoice_to_client(str(invoice.id), str(org_a.id), include_pdf=False)
        finally:
            tasks_module.render_to_string = original

        url = captured.get("public_url")
        assert url is not None, captured
        assert url.startswith("https://app.example.com/portal/invoice/")
        assert len(re.findall(r"https?://", url)) == 1

    @override_settings(FRONTEND_URL="https://app.example.com")
    def test_csat_link(self, org_a, admin_profile):
        """CSAT built a relative path when DOMAIN_NAME was empty, as `.env` sets it."""
        from common.links import frontend_url as build

        link = build("/csat/sometoken")
        assert link.startswith("https://app.example.com/csat/")
        assert not link.startswith("/")
