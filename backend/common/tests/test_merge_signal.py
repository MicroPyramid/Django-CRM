"""The ``pre_merge`` signal: sent once by ``merge_records``, before any row moves."""

import uuid

import pytest

from accounts.models import Account
from common.signals import pre_merge
from contacts.models import Contact
from invoices.models import Invoice
from leads.models import Lead
from tasks.models import Task


def _make_lead(org):
    return Lead.objects.create(org=org, first_name="Kay")


def _make_contact(org):
    return Contact.objects.create(org=org, first_name="Ann", last_name="Lee")


def _make_account(org):
    return Account.objects.create(org=org, name=f"Acme {uuid.uuid4().hex[:8]}")


def _task_on_lead(org, loser):
    return Task.objects.create(
        org=org, title="T", status="New", priority="Low", lead=loser
    )


def _invoice_on_contact(org, loser):
    return Invoice.objects.create(
        org=org, invoice_title="I", invoice_number="1", contact=loser
    )


def _task_on_account(org, loser):
    return Task.objects.create(
        org=org, title="T", status="New", priority="Low", account=loser
    )


# module, model, factory, row factory, FK name on the row
CASES = [
    ("leads", Lead, _make_lead, _task_on_lead, "lead_id"),
    ("contacts", Contact, _make_contact, _invoice_on_contact, "contact_id"),
    ("accounts", Account, _make_account, _task_on_account, "account_id"),
]


@pytest.fixture
def receiver():
    connected = []

    def connect(func):
        pre_merge.connect(func, weak=False)
        connected.append(func)

    yield connect
    for func in connected:
        pre_merge.disconnect(func)


@pytest.mark.parametrize("module,model,make,make_row,fk", CASES)
def test_pre_merge_is_sent_once_before_any_row_moves(
    admin_client, org_a, receiver, module, model, make, make_row, fk
):
    keeper, loser = make(org_a), make(org_a)
    row = make_row(org_a, loser)
    calls = []

    def listen(sender, keeper, loser, **kwargs):
        calls.append(
            (sender, keeper.pk, loser.pk, type(row).objects.get(pk=row.pk).__dict__[fk])
        )

    receiver(listen)
    response = admin_client.post(
        f"/api/{module}/{keeper.pk}/merge/", {"merge_id": str(loser.pk)}, format="json"
    )
    assert response.status_code == 200, response.content
    assert calls == [(model, keeper.pk, loser.pk, loser.pk)]
    row.refresh_from_db()
    assert getattr(row, fk) == keeper.pk


@pytest.mark.parametrize("module,model,make,make_row,fk", CASES)
def test_a_receiver_error_aborts_the_whole_merge(
    admin_client, org_a, receiver, module, model, make, make_row, fk
):
    keeper, loser = make(org_a), make(org_a)
    row = make_row(org_a, loser)

    def explode(sender, **kwargs):
        raise RuntimeError("receiver failed")

    receiver(explode)
    admin_client.raise_request_exception = False
    response = admin_client.post(
        f"/api/{module}/{keeper.pk}/merge/", {"merge_id": str(loser.pk)}, format="json"
    )
    assert response.status_code >= 400
    assert model.objects.filter(pk__in=[keeper.pk, loser.pk]).count() == 2
    row.refresh_from_db()
    assert getattr(row, fk) == loser.pk
