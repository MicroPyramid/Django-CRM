"""Web forms follow the module they write into.

While a form's target module is off, its public endpoints answer the
not-found an unknown form gets, CORS headers included, publishing it is
refused, and choosing that target is refused. Forms for a module that is on
keep working.
"""

import uuid

import pytest
from django.core.cache import cache
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from cases.models import Case
from common.modules import module_off_message
from common.testing import set_modules_off
from leads.models import Lead
from webforms.cors import allow_webform_origin
from webforms.models import WebForm, WebFormDailyStat, WebFormField, WebFormSubmission

LIST_URL = "/api/webforms/"
TICKETS_OFF = "Tickets is switched off for this organization."
ORIGIN = "https://customer.example"


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


def _form(org, target, *, published=True):
    form = WebForm.objects.create(
        name=f"{target} form", org=org, target=target, is_published=published
    )
    source = (
        WebFormField.SOURCE_LEAD if target == "lead" else WebFormField.SOURCE_TICKET
    )
    WebFormField.objects.create(
        form=form,
        org=org,
        order=0,
        source=source,
        label="Email",
        is_required=True,
        **{f"{target}_field": "email"},
    )
    return form


def _public(org_id, form_id):
    return f"/api/public/forms/{org_id}/{form_id}/"


def _answers(org_id, form_id):
    """What the three public endpoints say for this form, as (status, body)."""
    client = APIClient()
    base = _public(org_id, form_id)
    responses = (
        client.post(f"{base}submit/", {"email": "pat@example.com"}, format="json"),
        client.get(f"{base}embed/"),
        client.get(f"{base}embed.js"),
    )
    return [(r.status_code, r.content) for r in responses]


@pytest.mark.parametrize(
    "closed, still_open, module",
    [("ticket", "lead", "tickets"), ("lead", "ticket", "leads")],
)
def test_a_form_closes_with_its_target_module(org_a, closed, still_open, module):
    off_form = _form(org_a, closed)
    on_form = _form(org_a, still_open)
    unknown = _answers(org_a.id, uuid.uuid4())
    assert unknown[0] == (404, b'{"detail":"Form not found."}')
    assert [status for status, _ in unknown] == [404, 404, 404]

    set_modules_off(org_a, module)
    assert _answers(org_a.id, off_form.id) == unknown
    assert not WebFormSubmission.objects.filter(form=off_form).exists()
    assert not WebFormDailyStat.objects.filter(form=off_form).exists()
    created = Case if closed == "ticket" else Lead
    assert not created.objects.filter(org=org_a).exists()

    assert [status for status, _ in _answers(org_a.id, on_form.id)] == [200, 200, 200]
    kept = Lead if still_open == "lead" else Case
    assert kept.objects.filter(org=org_a).count() == 1

    set_modules_off(org_a)
    assert [status for status, _ in _answers(org_a.id, off_form.id)] == [200, 200, 200]
    assert created.objects.filter(org=org_a).count() == 1


def _cors(org_id, form_id):
    """(status, CORS headers) for a preflight and a POST from a listed origin."""
    client = APIClient()
    url = f"{_public(org_id, form_id)}submit/"
    responses = (
        client.options(
            url, HTTP_ORIGIN=ORIGIN, HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST"
        ),
        client.post(
            url, {"email": "pat@example.com"}, format="json", HTTP_ORIGIN=ORIGIN
        ),
    )
    return [
        (
            r.status_code,
            {
                name.lower(): value
                for name, value in r.headers.items()
                if name.lower().startswith("access-control-") or name.lower() == "vary"
            },
        )
        for r in responses
    ]


def test_cors_closes_with_the_target_module(org_a):
    form = _form(org_a, "ticket")
    form.allowed_origins = [ORIGIN]
    form.save(update_fields=["allowed_origins"])
    unknown = _cors(org_a.id, uuid.uuid4())
    assert [s for s, _ in unknown] == [200, 404]
    assert not any("access-control-allow-origin" in h for _, h in unknown)

    set_modules_off(org_a, "tickets")
    assert _cors(org_a.id, form.id) == unknown
    assert not Case.objects.filter(org=org_a).exists()

    set_modules_off(org_a)
    opened = _cors(org_a.id, form.id)
    assert [s for s, _ in opened] == [200, 200]
    assert [h.get("access-control-allow-origin") for _, h in opened] == [ORIGIN] * 2


def test_the_cors_check_reads_the_form_in_one_query(org_a):
    """Pin: it runs on every submit request, and read one row before too."""
    form = _form(org_a, "ticket")
    form.allowed_origins = [ORIGIN]
    form.save(update_fields=["allowed_origins"])
    request = RequestFactory().post(
        f"{_public(org_a.id, form.id)}submit/", HTTP_ORIGIN=ORIGIN
    )
    with CaptureQueriesContext(connection) as captured:
        assert allow_webform_origin(None, request) is True
    reads = [q for q in captured.captured_queries if "set_config" not in q["sql"]]
    assert len(reads) == 1


def test_publishing_a_form_for_an_off_module_is_refused(
    admin_client, user_client, org_a
):
    form = _form(org_a, "ticket", published=False)
    url = f"{LIST_URL}{form.id}/publish/"
    set_modules_off(org_a, "tickets")
    assert user_client.post(url).status_code == 403

    response = admin_client.post(url)
    assert (response.status_code, response.json()) == (
        400,
        {
            "error": True,
            "errors": f"{TICKETS_OFF} Switch it on before publishing this form.",
        },
    )
    form.refresh_from_db()
    assert form.is_published is False
    published = _form(org_a, "ticket")
    response = admin_client.post(f"{LIST_URL}{published.id}/publish/")
    assert response.json()["errors"] == "This form is already published."

    set_modules_off(org_a)
    assert admin_client.post(url).status_code == 200
    form.refresh_from_db()
    assert form.is_published is True


def test_choosing_an_off_target_is_refused(admin_client, user_client, org_a):
    ticket_rows = [{"source": "ticket", "ticket_field": "email", "label": "Email"}]
    new_ticket_form = {"name": "Support", "target": "ticket", "fields": ticket_rows}
    lead_form = _form(org_a, "lead", published=False)
    change = {"target": "ticket", "fields": ticket_rows}
    set_modules_off(org_a, "tickets")

    refused = user_client.post(LIST_URL, new_ticket_form, format="json")
    assert refused.status_code == 403
    response = admin_client.post(LIST_URL, new_ticket_form, format="json")
    assert (response.status_code, response.json()) == (400, {"target": [TICKETS_OFF]})
    response = admin_client.put(f"{LIST_URL}{lead_form.id}/", change, format="json")
    assert (response.status_code, response.json()) == (400, {"target": [TICKETS_OFF]})
    assert list(WebForm.objects.filter(org=org_a)) == [lead_form]
    lead_form.refresh_from_db()
    assert lead_form.target == "lead"

    set_modules_off(org_a, "leads")
    response = admin_client.post(LIST_URL, {"name": "Contact us"}, format="json")
    assert response.status_code == 400
    assert response.json() == {"target": [module_off_message(org_a, "leads")]}

    set_modules_off(org_a)
    created = admin_client.post(LIST_URL, new_ticket_form, format="json")
    assert created.status_code == 201
    response = admin_client.put(f"{LIST_URL}{lead_form.id}/", change, format="json")
    assert response.status_code == 200, response.content
    lead_form.refresh_from_db()
    assert lead_form.target == "ticket"


def test_editing_an_existing_forms_name_still_works_while_off(admin_client, org_a):
    """Pin: a write that keeps the target was never refused."""
    form = _form(org_a, "ticket")
    set_modules_off(org_a, "tickets")
    url = f"{LIST_URL}{form.id}/"
    assert admin_client.put(url, {"name": "Renamed"}, format="json").status_code == 200
    resent = {"name": "Renamed again", "target": "ticket"}
    assert admin_client.put(url, resent, format="json").status_code == 200
    form.refresh_from_db()
    assert (form.name, form.target) == ("Renamed again", "ticket")
