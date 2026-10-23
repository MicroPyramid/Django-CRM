"""Invoicing across modules while one is off: the routes that need two modules,
a deal named on a document, and a stored deal that an edit must not erase."""

import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from accounts.models import Account
from cases.models import Case, TimeEntry
from common.testing import set_modules_off
from contacts.models import Contact
from invoices.models import Estimate, Invoice, RecurringInvoice
from opportunity.models import DealPipeline, DealStage, Opportunity, OpportunityLineItem

DEALS_OFF = "Pipeline is switched off for this organization."


@pytest.fixture
def account(org_a):
    return Account.objects.create(name="Billed Co", org=org_a)


@pytest.fixture
def contact(org_a, account):
    contact = Contact.objects.create(first_name="Ada", last_name="Buyer", org=org_a)
    contact.account = account
    contact.save(update_fields=["account"])
    return contact


@pytest.fixture
def won_deal(org_a, account, contact):
    pipeline = DealPipeline.objects.create(org=org_a, name="Renewals")
    for order, (code, kind) in enumerate([("TALKING", "open"), ("SIGNED", "won")], 1):
        DealStage.objects.create(
            org=org_a, pipeline=pipeline, code=code, label=code, kind=kind, order=order
        )
    deal = Opportunity.objects.create(
        org=org_a,
        name="Renewal",
        stage="SIGNED",
        pipeline=pipeline,
        account=account,
        closed_on=timezone.localdate(),
        currency="USD",
    )
    deal.contacts.add(contact)
    OpportunityLineItem.objects.create(
        opportunity=deal,
        org=org_a,
        name="Seat",
        quantity=Decimal("2"),
        unit_price=Decimal("50"),
    )
    return deal


def _is_off(response, key):
    assert response.status_code == 404, response.content
    body = response.json()
    assert (body["code"], body["module"]) == ("module_off", key)


def test_invoicing_a_deal_needs_invoices_and_deals(admin_client, org_a, won_deal):
    url = f"/api/invoices/from-opportunity/{won_deal.id}/"

    set_modules_off(org_a, "invoices")
    _is_off(admin_client.post(url), "invoices")

    set_modules_off(org_a, "deals")
    _is_off(admin_client.post(url), "deals")

    set_modules_off(org_a)
    assert admin_client.post(url).status_code == 201
    assert Invoice.objects.filter(opportunity=won_deal).count() == 1


def test_invoicing_time_needs_the_timesheet(
    admin_client, org_a, account, admin_profile
):
    case = Case.objects.create(
        name="Work", status="New", priority="Normal", org=org_a, account=account
    )
    entry = TimeEntry.objects.create(
        org=org_a,
        case=case,
        profile=admin_profile,
        started_at=timezone.now() - datetime.timedelta(hours=2),
        ended_at=timezone.now() - datetime.timedelta(hours=1),
        billable=True,
        hourly_rate=Decimal("100.00"),
        currency="USD",
    )
    set_modules_off(org_a, "timesheet")

    response = admin_client.post(
        "/api/invoices/from-time-entries/",
        {"account_id": str(account.id), "entry_ids": [str(entry.id)]},
        format="json",
    )

    _is_off(response, "timesheet")
    assert not Invoice.objects.exists()


def _body(kind, account, contact, **extra):
    today = timezone.localdate()
    if kind == "estimate":
        return {
            "title": "Estimate",
            "account_id": str(account.id),
            "contact_id": str(contact.id),
            "currency": "USD",
            "issue_date": str(today),
            "expiry_date": str(today + datetime.timedelta(days=30)),
            "line_items": [{"name": "Design", "quantity": "1", "unit_price": "10.00"}],
            **extra,
        }
    if kind == "recurring":
        return {
            "title": "Retainer",
            "account_id": str(account.id),
            "contact_id": str(contact.id),
            "frequency": "MONTHLY",
            "start_date": str(today),
            "next_generation_date": str(today),
            "payment_terms": "NET_30",
            "currency": "USD",
            "is_active": True,
            **extra,
        }
    return {
        "invoice_title": "Invoice",
        "account_id": str(account.id),
        "contact_id": str(contact.id),
        "currency": "USD",
        **extra,
    }


KINDS = [
    pytest.param(Invoice, "invoice", "/api/invoices/", id="invoice"),
    pytest.param(Estimate, "estimate", "/api/invoices/estimates/", id="estimate"),
    pytest.param(
        RecurringInvoice, "recurring", "/api/invoices/recurring/", id="recurring"
    ),
]


@pytest.mark.parametrize(("model", "kind", "url"), KINDS)
def test_naming_a_deal_on_a_document_is_refused_while_deals_is_off(
    admin_client, org_a, account, contact, won_deal, model, kind, url
):
    set_modules_off(org_a, "deals")

    response = admin_client.post(
        url,
        _body(kind, account, contact, opportunity_id=str(won_deal.id)),
        format="json",
    )

    assert response.status_code == 400, response.content
    assert response.json()["errors"]["opportunity_id"] == [DEALS_OFF]
    assert not model.objects.exists()


def test_naming_a_deal_on_an_estimate_is_refused_while_deals_is_off(
    admin_client, org_a, account, contact, won_deal
):
    set_modules_off(org_a, "deals")

    response = admin_client.post(
        "/api/invoices/estimates/",
        _body("estimate", account, contact, opportunity_id=str(won_deal.id)),
        format="json",
    )

    assert response.status_code == 400, response.content
    assert response.json()["errors"]["opportunity_id"] == [DEALS_OFF]


@pytest.mark.parametrize(("model", "kind", "url"), KINDS)
def test_a_document_keeps_its_stored_deal_on_edit(
    admin_client, org_a, account, contact, won_deal, model, kind, url
):
    created = admin_client.post(
        url,
        _body(kind, account, contact, opportunity_id=str(won_deal.id)),
        format="json",
    )
    assert created.status_code == 201, created.content
    record = model.objects.get()
    assert record.opportunity_id == won_deal.id
    set_modules_off(org_a, "deals")

    # What a client that loaded the record sends back: the link resent, omitted,
    # or null (the shape it saw), and none may move or clear the stored deal.
    for extra in ({"opportunity_id": str(won_deal.id)}, {}, {"opportunity_id": None}):
        response = admin_client.put(
            f"{url}{record.id}/", _body(kind, account, contact, **extra), format="json"
        )
        assert response.status_code == 200, response.content
        record.refresh_from_db()
        assert record.opportunity_id == won_deal.id


def test_naming_a_different_deal_while_deals_is_off_leaves_the_stored_one(
    admin_client, org_a, account, contact, won_deal
):
    created = admin_client.post(
        "/api/invoices/",
        _body("invoice", account, contact, opportunity_id=str(won_deal.id)),
        format="json",
    )
    assert created.status_code == 201, created.content
    invoice = Invoice.objects.get()
    other = Opportunity.objects.create(
        org=org_a, name="Other", stage="", account=account
    )
    set_modules_off(org_a, "deals")

    response = admin_client.put(
        f"/api/invoices/{invoice.id}/",
        _body("invoice", account, contact, opportunity_id=str(other.id)),
        format="json",
    )

    assert response.status_code == 400, response.content
    invoice.refresh_from_db()
    assert invoice.opportunity_id == won_deal.id
