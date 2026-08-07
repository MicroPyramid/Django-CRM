"""The template editor fetch: the one read that returns the raw markup.

``template_html`` and ``template_css`` are org-authored HTML/CSS rendered into
a PDF server-side, so every list and detail response replaces them with
booleans and a byte count. That is right, and it left the edit form unable to
pre-fill the two fields it exists to change.

This route serves them, admin-only, on its own path so the detail response that
every member reads stays narrow. The tests pin both halves: the markup comes
back here for an admin, and it still does not come back anywhere else.
"""

import pytest
from rest_framework import status

from accounts.models import Account
from invoices.models import InvoiceTemplate

MARKUP = "<h1>{{ invoice.number }}</h1><script>alert(1)</script>"
CSS = "h1 { color: red; }"


@pytest.fixture
def template(org_a):
    return InvoiceTemplate.objects.create(
        name="House style",
        template_html=MARKUP,
        template_css=CSS,
        org=org_a,
    )


@pytest.fixture
def template_org_b(org_b):
    return InvoiceTemplate.objects.create(
        name="Other tenant style",
        template_html="<h1>not yours</h1>",
        org=org_b,
    )


def _editor_url(template):
    return f"/api/invoices/templates/{template.id}/editor/"


@pytest.mark.django_db
class TestAdminCanLoadTheMarkup:
    def test_returns_html_and_css(self, admin_client, template):
        response = admin_client.get(_editor_url(template))
        assert response.status_code == status.HTTP_200_OK, response.content
        body = response.json()
        assert body["template_html"] == MARKUP
        assert body["template_css"] == CSS

    def test_returns_the_rest_of_the_editable_fields(self, admin_client, template):
        """A prefill that omits a field makes the next save blank it."""
        body = admin_client.get(_editor_url(template)).json()
        for field in (
            "name",
            "primary_color",
            "secondary_color",
            "default_notes",
            "default_terms",
            "footer_text",
            "is_default",
        ):
            assert field in body, f"the editor cannot pre-fill {field}"


@pytest.mark.django_db
class TestTheMarkupStaysOffEveryOtherRead:
    """The False direction for the widening: nothing else grew the fields."""

    def test_detail_still_hides_it(self, admin_client, template):
        body = admin_client.get(f"/api/invoices/templates/{template.id}/").json()
        assert "template_html" not in body
        assert "template_css" not in body
        assert body["has_custom_html"] is True

    def test_list_still_hides_it(self, admin_client, template):
        body = admin_client.get("/api/invoices/templates/").json()
        rows = body["results"] if isinstance(body, dict) else body
        assert rows, "no templates came back, so this proves nothing"
        for row in rows:
            assert "template_html" not in row
            assert "template_css" not in row


@pytest.mark.django_db
class TestOnlyAdminsAndOnlyThisOrg:
    def test_a_member_is_refused(self, user_client, template):
        response = user_client.get(_editor_url(template))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "template_html" not in response.content.decode()

    def test_a_member_is_refused_before_the_id_is_looked_up(self, user_client, org_a):
        """A 404 here would tell a member which template ids exist."""
        missing = InvoiceTemplate(id="00000000-0000-0000-0000-000000000000")
        response = user_client.get(_editor_url(missing))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_another_org_is_a_404(self, admin_client, template_org_b):
        response = admin_client.get(_editor_url(template_org_b))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not yours" not in response.content.decode()

    def test_unauthenticated_is_refused(self, unauthenticated_client, template):
        response = unauthenticated_client.get(_editor_url(template))
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


@pytest.mark.django_db
class TestTheEditRoundTrip:
    """What the endpoint exists for: load, change one field, save the rest."""

    def test_prefill_then_save_keeps_the_markup(self, admin_client, template):
        loaded = admin_client.get(_editor_url(template)).json()
        loaded["name"] = "House style v2"

        response = admin_client.put(
            f"/api/invoices/templates/{template.id}/",
            {
                k: v
                for k, v in loaded.items()
                if k not in ("id", "created_at", "updated_at")
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.content

        template.refresh_from_db()
        assert template.name == "House style v2"
        assert template.template_html == MARKUP, (
            "the round trip blanked the markup, which is the bug this endpoint "
            "exists to prevent"
        )
        assert template.template_css == CSS


@pytest.mark.django_db
def test_the_pdf_still_renders_from_the_stored_markup(admin_client, org_a, template):
    """The markup is only meaningful because the server renders it.

    Asserting the field survives a round trip is not enough on its own if the
    render path stops reading it, so this pins that they are the same field.
    """
    account = Account.objects.create(name="Template Account", org=org_a)
    from invoices.models import Invoice

    invoice = Invoice.objects.create(
        invoice_title="Rendered",
        account=account,
        currency="USD",
        org=org_a,
        template=template,
    )
    assert invoice.template.template_html == MARKUP
