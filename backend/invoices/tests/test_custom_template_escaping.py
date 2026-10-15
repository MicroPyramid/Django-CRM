"""Field values are escaped when they fill a custom invoice template.

Only admins may write `template_html`, but any member who may create an invoice
writes the values that fill it. `render_invoice_template` pasted those values
in raw, so a member could put markup in `notes` that restyled or covered the
admin's layout in the PDF a client receives, such as the bank details or the
totals (issue #825). The default template already escaped the same fields
through Django's autoescape; custom templates now match it.
"""

from datetime import date
from unittest.mock import patch

import pytest

from accounts.models import Account
from invoices.models import Invoice, InvoiceTemplate
from invoices.pdf import generate_invoice_pdf, render_invoice_template

MARKUP = '<b class="x">A&B</b>'
ESCAPED = "&lt;b class=&quot;x&quot;&gt;A&amp;B&lt;/b&gt;"

MEMBER_FIELDS = [
    "invoice_number",
    "invoice_title",
    "client_name",
    "client_email",
    "client_phone",
    "notes",
    "terms",
    "billing_address_line",
    "billing_city",
    "billing_state",
    "billing_postcode",
    "billing_country",
    "client_address_line",
    "client_city",
    "client_state",
    "client_postcode",
    "client_country",
]


@pytest.fixture
def invoice(org_a):
    account = Account.objects.create(name="Acme", org=org_a)
    return Invoice.objects.create(
        invoice_title="March work",
        client_name="Acme Ltd",
        due_date=date(2026, 11, 14),
        account=account,
        currency="USD",
        org=org_a,
    )


def _render(template_html, invoice):
    return render_invoice_template(
        template_html, {"invoice": invoice, "org": invoice.org}
    )


@pytest.mark.django_db
class TestCustomTemplateEscaping:
    @pytest.mark.parametrize("field", MEMBER_FIELDS)
    def test_member_written_field_is_escaped(self, invoice, field):
        setattr(invoice, field, MARKUP)
        assert _render(f"[{{{{invoice.{field}}}}}]", invoice) == f"[{ESCAPED}]"

    def test_org_name_is_escaped(self, invoice, org_a):
        org_a.name = MARKUP
        assert _render("[{{org.name}}]", invoice) == f"[{ESCAPED}]"

    def test_the_templates_own_markup_and_plain_values_are_unchanged(self, invoice):
        html = '<h1 style="color:red">{{invoice.client_name}}</h1>{{invoice.due_date}}'
        assert _render(html, invoice) == '<h1 style="color:red">Acme Ltd</h1>2026-11-14'

    def test_the_pdf_renderer_receives_the_escaped_value(self, invoice, org_a):
        """The report's payload, end to end through `generate_invoice_pdf`."""
        invoice.template = InvoiceTemplate.objects.create(
            name="Custom",
            template_html="<p>{{invoice.notes}}</p>",
            org=org_a,
        )
        invoice.notes = '<div style="position:absolute;top:0">PAY TO 9999</div>'
        with patch("invoices.pdf.HTML") as html:
            generate_invoice_pdf(invoice)
        rendered = html.call_args.kwargs["string"]
        assert "<div" not in rendered
        assert "&lt;div style=&quot;position:absolute;top:0&quot;&gt;" in rendered
