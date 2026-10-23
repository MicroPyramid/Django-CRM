"""The emailed invoice and estimate links while Invoices is off.

A customer holding a link gets exactly the answer an unknown token gets, and
the same link opens again once the module is back on.
"""

import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from common.testing import set_modules_off
from invoices.models import Estimate, Invoice

INVOICE_GONE = {"error": True, "message": "Invoice not found or link expired"}
ESTIMATE_GONE = {"error": True, "message": "Estimate not found or link expired"}
ACCEPT = {"name": "Dana Buyer", "email": "dana@buyer.example"}

# (record, method, path after the token, the not-found body)
ROUTES = [
    ("invoice", "get", "", INVOICE_GONE),
    ("invoice", "get", "pdf/", INVOICE_GONE),
    ("estimate", "get", "", ESTIMATE_GONE),
    ("estimate", "get", "pdf/", ESTIMATE_GONE),
    ("estimate", "post", "accept/", ESTIMATE_GONE),
    ("estimate", "post", "decline/", ESTIMATE_GONE),
]


@pytest.fixture
def invoice(org_a):
    return Invoice.objects.create(
        org=org_a,
        invoice_title="Fit-out",
        client_email="dana@buyer.example",
        currency="USD",
        status="Sent",
    )


@pytest.fixture
def estimate(org_a):
    return Estimate.objects.create(
        org=org_a,
        title="Fit-out",
        client_name="Dana Buyer",
        client_email="dana@buyer.example",
        currency="USD",
        status="Sent",
        issue_date=timezone.localdate(),
        expiry_date=timezone.localdate() + datetime.timedelta(days=30),
    )


def _send(record, method, tail, token):
    url = f"/api/public/{record}/{token}/{tail}"
    with (
        patch("invoices.public_views.generate_invoice_pdf", return_value=b"%PDF-"),
        patch("invoices.public_views.generate_estimate_pdf", return_value=b"%PDF-"),
    ):
        if method == "post":
            return APIClient().post(url, ACCEPT, format="json")
        return APIClient().get(url)


def _state(row):
    row.refresh_from_db()
    return row.status, row.viewed_at


@pytest.mark.parametrize("record, method, tail, gone", ROUTES)
def test_public_links_close_with_invoices(
    org_a, invoice, estimate, record, method, tail, gone
):
    row = invoice if record == "invoice" else estimate
    unknown = _send(record, method, tail, "not-a-real-token")
    assert (unknown.status_code, unknown.json()) == (404, gone)
    before = _state(row)

    set_modules_off(org_a, "invoices")
    response = _send(record, method, tail, row.public_token)
    assert (response.status_code, response.json()) == (404, gone)
    assert _state(row) == before

    set_modules_off(org_a)
    assert _send(record, method, tail, row.public_token).status_code == 200


def test_accepting_an_estimate_changes_nothing_while_off(org_a, estimate):
    set_modules_off(org_a, "invoices")
    for action in ("accept/", "decline/"):
        response = _send("estimate", "post", action, estimate.public_token)
        assert response.status_code == 404
    estimate.refresh_from_db()
    assert estimate.status == "Sent"
    assert (estimate.accepted_at, estimate.accepted_by_name) == (None, "")
    assert estimate.declined_at is None


@pytest.mark.parametrize("record, method, tail, gone", ROUTES)
def test_an_unknown_token_answers_as_before(org_a, record, method, tail, gone):
    """Pin: an unknown token has no org to check, on or off."""
    for off in ((), ("invoices",)):
        set_modules_off(org_a, *off)
        response = _send(record, method, tail, "not-a-real-token")
        assert (response.status_code, response.json()) == (404, gone)
