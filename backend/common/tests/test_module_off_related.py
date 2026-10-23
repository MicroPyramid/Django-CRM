"""An off module's records stay out of other modules' responses.

Every key stays: lists read ``[]``, counts ``0``, single links and summaries
``null``. Nothing stored changes, and a client that sends back what it loaded
never erases a link it was shown as null.
"""

import csv
import datetime
import io
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from accounts.models import Account
from cases.models import Case, Solution, TimeEntry
from common.models import Comment
from common.testing import set_modules_off
from contacts.models import Contact
from invoices.models import (
    Estimate,
    Invoice,
    InvoiceLineItem,
    Product,
    RecurringInvoice,
)
from leads.models import Lead
from opportunity.models import DealPipeline, Opportunity
from tasks.models import Board, BoardColumn, BoardTask, Task
from webforms.models import WebForm, WebFormSubmission

pytestmark = pytest.mark.django_db

WON_ON = datetime.date(2024, 6, 1)
PAST_DUE = datetime.date(2020, 1, 1)
MODELS = (
    Account,
    Contact,
    Lead,
    Opportunity,
    Case,
    Solution,
    TimeEntry,
    Task,
    BoardTask,
    Invoice,
    Estimate,
    RecurringInvoice,
    Product,
    Comment,
    WebFormSubmission,
)


def _rows():
    return {m.__name__: list(m.objects.order_by("pk").values()) for m in MODELS}


@pytest.fixture(params=["admin", "member"])
def viewer(request):
    """The caller and their profile; every record below is assigned to them,
    so a member reads exactly what an admin reads."""
    if request.param == "admin":
        names = ("admin_client", "admin_profile")
    else:
        names = ("user_client", "user_profile")
    return tuple(request.getfixturevalue(n) for n in names)


def _mine(record, profile):
    record.assigned_to.add(profile)
    return record


def _get(client, url, **params):
    response = client.get(url, params)
    assert response.status_code == 200, response.content
    return response.json()


@pytest.fixture
def account(org_a, viewer):
    return _mine(Account.objects.create(name="Acme", org=org_a), viewer[1])


@pytest.fixture
def contact(org_a, viewer, account):
    contact = Contact.objects.create(
        first_name="Ada", last_name="Buyer", email="ada@x.com", org=org_a
    )
    contact.account = account
    contact.save(update_fields=["account"])
    return _mine(contact, viewer[1])


def _deal(org, profile, name, stage, amount, **extra):
    deal = Opportunity.objects.create(
        org=org, name=name, stage=stage, amount=amount, currency="USD", **extra
    )
    return _mine(deal, profile)


def _ticket(org, profile, name="Broken", **extra):
    ticket = Case.objects.create(
        org=org, name=name, status="New", priority="Normal", **extra
    )
    return _mine(ticket, profile)


def _task(org, profile, **extra):
    task = Task.objects.create(
        org=org, title="Call back", status="New", priority="Medium", **extra
    )
    return _mine(task, profile)


def _overdue_invoice(org, profile, account, number="INV-1", due=Decimal("30")):
    invoice = Invoice.objects.create(
        invoice_title=number,
        invoice_number=number,
        org=org,
        account=account,
        status="Sent",
        currency="USD",
        due_date=PAST_DUE,
    )
    Invoice.objects.filter(pk=invoice.pk).update(
        total_amount=due, amount_paid=Decimal("0"), amount_due=due
    )
    return _mine(invoice, profile)


@pytest.fixture
def on_account(org_a, viewer, account):
    """One of each module's records on the account: a won and an open deal, an
    open ticket, a task and an overdue invoice."""
    profile = viewer[1]
    _deal(org_a, profile, "Won", "CLOSED_WON", Decimal("100"), account=account)
    Opportunity.objects.filter(name="Won").update(closed_on=WON_ON)
    _deal(org_a, profile, "Open", "PROPOSAL", Decimal("50"), account=account)
    _ticket(org_a, profile, account=account)
    _task(org_a, profile, account=account)
    _overdue_invoice(org_a, profile, account)


ACCOUNT_LISTS = [
    pytest.param("tickets", ("cases",), ("cases",), id="tickets"),
    pytest.param("deals", ("opportunity_list",), ("opportunities",), id="deals"),
    pytest.param("tasks", ("tasks",), ("tasks",), id="tasks"),
    pytest.param("invoices", ("invoices",), (), id="invoices"),
]
ALL_ACCOUNT_KEYS = {"cases", "opportunity_list", "tasks", "invoices"}


@pytest.mark.parametrize(("module", "keys", "obj_keys"), ACCOUNT_LISTS)
def test_account_detail_hides_off_module_lists(
    viewer, org_a, account, on_account, module, keys, obj_keys
):
    client = viewer[0]
    url = f"/api/accounts/{account.id}/"
    on = _get(client, url)
    for key in ALL_ACCOUNT_KEYS:
        assert on[key], key
    for key in ("cases", "opportunities", "tasks"):
        assert on["account_obj"][key], key
    before = _rows()

    set_modules_off(org_a, module)
    off = _get(client, url)

    for key in keys:
        assert off[key] == []
    for key in ALL_ACCOUNT_KEYS - set(keys):
        assert off[key] == on[key], key
    for key in ("cases", "opportunities", "tasks"):
        expected = [] if key in obj_keys else on["account_obj"][key]
        assert off["account_obj"][key] == expected, key
    assert _rows() == before


def test_account_detail_offers_no_stages_while_pipeline_is_off(viewer, org_a, account):
    client = viewer[0]
    url = f"/api/accounts/{account.id}/"
    set_modules_off(org_a, "deals")
    assert _get(client, url)["stages"] == []
    assert not DealPipeline.objects.filter(org=org_a).exists()

    set_modules_off(org_a)
    assert _get(client, url)["stages"]


FIGURES_ON = {
    "won_count": 1,
    "open_deal_count": 1,
    "open_tickets": 1,
    "first_won_on": WON_ON.isoformat(),
    "won_amount": Decimal("100"),
    "open_pipeline": Decimal("50"),
    "overdue_amount": Decimal("30"),
}
FIGURES_OFF = {
    "deals": {
        "won_count": 0,
        "open_deal_count": 0,
        "first_won_on": None,
        "won_amount": Decimal("0"),
        "open_pipeline": Decimal("0"),
    },
    "tickets": {"open_tickets": 0},
    "invoices": {"overdue_amount": Decimal("0")},
}


def _figures(client, account, where):
    if where == "detail":
        return _get(client, f"/api/accounts/{account.id}/")["account_obj"]["rollups"]
    rows = _get(client, "/api/accounts/")["active_accounts"]["open_accounts"]
    return next(row for row in rows if row["id"] == str(account.id))["rollups"]


def _read_figures(rollups):
    return {
        key: Decimal(rollups[key]) if isinstance(value, Decimal) else rollups[key]
        for key, value in FIGURES_ON.items()
    }


@pytest.mark.parametrize("where", ["list", "detail"])
@pytest.mark.parametrize("module", ["deals", "tickets", "invoices"])
def test_account_figures_count_only_on_modules(
    viewer, org_a, account, on_account, where, module
):
    client = viewer[0]
    assert _read_figures(_figures(client, account, where)) == FIGURES_ON
    before = _rows()

    set_modules_off(org_a, module)

    assert _read_figures(_figures(client, account, where)) == {
        **FIGURES_ON,
        **FIGURES_OFF[module],
    }
    assert _rows() == before


@pytest.mark.parametrize("where", ["list", "detail"])
def test_account_figures_with_every_figure_module_off(
    viewer, org_a, account, on_account, where
):
    set_modules_off(org_a, "deals", "tickets", "invoices")

    rollups = _figures(viewer[0], account, where)

    assert rollups["by_currency"] == []
    assert _read_figures(rollups) == {
        key: value for module in FIGURES_OFF.values() for key, value in module.items()
    }


@pytest.mark.parametrize("leads_on", [True, False])
def test_account_list_offers_leads_only_while_leads_is_on(viewer, org_a, leads_on):
    _mine(Lead.objects.create(org=org_a, title="Lead", first_name="Lee"), viewer[1])
    if not leads_on:
        set_modules_off(org_a, "leads")

    body = _get(viewer[0], "/api/accounts/")

    assert len(body["leads"]) == (1 if leads_on else 0)


CONTACT_LISTS = [
    pytest.param("deals", id="deals"),
    pytest.param("tickets", id="tickets"),
    pytest.param("tasks", id="tasks"),
]
ZERO_DEALS = {"amount": "0", "count": 0, "by_currency": []}


@pytest.mark.parametrize("module", CONTACT_LISTS)
def test_contact_detail_hides_off_module_lists(viewer, org_a, contact, module):
    profile = viewer[1]
    _deal(org_a, profile, "Open", "PROPOSAL", Decimal("50")).contacts.add(contact)
    _ticket(org_a, profile).contacts.add(contact)
    _task(org_a, profile).contacts.add(contact)
    url = f"/api/contacts/{contact.id}/"
    on = _get(viewer[0], url)
    assert len(on["opportunities"]) == 1
    assert on["open_deals"]["count"] == 1
    assert on["opportunity_count"] == 1
    assert len(on["cases"]) == 1
    assert len(on["tasks"]) == 1
    before = _rows()

    set_modules_off(org_a, module)
    off = _get(viewer[0], url)

    hidden = {
        "deals": {
            "opportunities": [],
            "open_deals": ZERO_DEALS,
            "opportunity_count": 0,
        },
        "tickets": {"cases": []},
        "tasks": {"tasks": []},
    }[module]
    for key in ("opportunities", "open_deals", "opportunity_count", "cases", "tasks"):
        assert off[key] == hidden.get(key, on[key]), key
    assert _rows() == before


def test_ticket_detail_hides_articles_while_the_knowledge_base_is_off(viewer, org_a):
    ticket = _ticket(org_a, viewer[1])
    article = Solution.objects.create(
        org=org_a, title="Reset", description="d", status="approved"
    )
    article.cases.add(ticket)
    url = f"/api/cases/{ticket.id}/"
    assert [s["id"] for s in _get(viewer[0], url)["solutions"]] == [str(article.id)]
    before = _rows()

    set_modules_off(org_a, "knowledge_base")

    assert _get(viewer[0], url)["solutions"] == []
    assert _rows() == before


def _logged(org, ticket, profile, invoice=None):
    started = timezone.now() - datetime.timedelta(hours=2)
    return TimeEntry.objects.create(
        org=org,
        case=ticket,
        profile=profile,
        started_at=started,
        ended_at=started + datetime.timedelta(minutes=30),
        billable=True,
        hourly_rate=Decimal("60"),
        currency="USD",
        invoice=invoice,
    )


def test_ticket_rows_hide_time_while_the_timesheet_is_off(viewer, org_a):
    client, profile = viewer
    ticket = _ticket(org_a, profile)
    _logged(org_a, ticket, profile)

    def summaries():
        rows = _get(client, "/api/cases/", slim="true")["cases"]
        detail = _get(client, f"/api/cases/{ticket.id}/")["cases_obj"]
        return [row["time_summary"] for row in rows] + [detail["time_summary"]]

    assert [s["total_minutes"] for s in summaries()] == [30, 30]
    before = _rows()

    set_modules_off(org_a, "timesheet")

    assert summaries() == [None, None]
    assert _rows() == before


TASK_LINKS = [
    pytest.param(
        "opportunity",
        "deals",
        "opportunity",
        lambda org, p: _deal(org, p, "Deal", "PROPOSAL", Decimal("5")),
        id="deal",
    ),
    pytest.param("case", "tickets", "case", _ticket, id="ticket"),
    pytest.param(
        "lead",
        "leads",
        "lead",
        lambda org, p: _mine(
            Lead.objects.create(org=org, title="Lead", first_name="Lee"), p
        ),
        id="lead",
    ),
]


def _task_views(client, task, contact):
    """The task as each response that embeds it shows it."""
    rows = _get(client, "/api/tasks/", slim="true")["tasks"]
    return [
        next(row for row in rows if row["id"] == str(task.id)),
        _get(client, f"/api/tasks/{task.id}/")["task_obj"],
        _get(client, f"/api/contacts/{contact.id}/")["tasks"][0],
    ]


@pytest.mark.parametrize(("field", "module", "kind", "make"), TASK_LINKS)
def test_task_links_hide_off_modules(viewer, org_a, contact, field, module, kind, make):
    client, profile = viewer
    parent = make(org_a, profile)
    task = _task(org_a, profile, **{field: parent})
    task.contacts.add(contact)
    for shown in _task_views(client, task, contact):
        assert shown[field]["id"] == str(parent.id)
    before = _rows()

    set_modules_off(org_a, module)

    for shown in _task_views(client, task, contact):
        assert shown[field] is None
    assert _rows() == before


def test_pin_a_task_on_an_account_keeps_it_while_other_modules_are_off(
    viewer, org_a, account, contact
):
    """A pin: the account link was never hidden, and must not become so."""
    client, profile = viewer
    task = _task(org_a, profile, account=account)
    task.contacts.add(contact)
    set_modules_off(org_a, "deals", "tickets", "leads")

    for shown in _task_views(client, task, contact):
        assert shown["account"]["id"] == str(account.id)
    card = _kanban_card(client, task)
    assert card["related_entity"]["type"] == "account"


def _kanban_card(client, task):
    columns = _get(client, "/api/tasks/kanban/")["columns"]
    cards = [card for column in columns for card in column["tasks"]]
    return next(card for card in cards if card["id"] == str(task.id))


@pytest.mark.parametrize(("field", "module", "kind", "make"), TASK_LINKS)
def test_a_task_card_hides_off_module_names(viewer, org_a, field, module, kind, make):
    client, profile = viewer
    parent = make(org_a, profile)
    task = _task(org_a, profile, **{field: parent})
    assert _kanban_card(client, task)["related_entity"]["type"] == kind

    set_modules_off(org_a, module)

    assert _kanban_card(client, task)["related_entity"] is None


@pytest.fixture
def documents(org_a, viewer, account, contact):
    """An invoice, an estimate and a recurring invoice, each on a deal."""
    profile = viewer[1]
    deal = _deal(org_a, profile, "Deal", "CLOSED_WON", Decimal("10"), account=account)
    today = timezone.localdate()
    common = {"org": org_a, "account": account, "contact": contact, "opportunity": deal}
    invoice = Invoice.objects.create(invoice_title="I", currency="USD", **common)
    estimate = Estimate.objects.create(
        title="E",
        currency="USD",
        issue_date=today,
        expiry_date=today + datetime.timedelta(days=30),
        **common,
    )
    recurring = RecurringInvoice.objects.create(
        title="R",
        frequency="MONTHLY",
        start_date=today,
        next_generation_date=today,
        currency="USD",
        **common,
    )
    return deal, [_mine(r, profile) for r in (invoice, estimate, recurring)]


def _document_deals(client, documents):
    _, (invoice, estimate, recurring) = documents
    estimates = _get(client, "/api/invoices/estimates/")["results"]
    return [
        _get(client, f"/api/invoices/{invoice.id}/")["invoice"]["opportunity"],
        next(e for e in estimates if e["id"] == str(estimate.id))["opportunity"],
        _get(client, f"/api/invoices/estimates/{estimate.id}/")["estimate"][
            "opportunity"
        ],
        _get(client, f"/api/invoices/recurring/{recurring.id}/")["recurring_invoice"][
            "opportunity"
        ],
    ]


def test_an_invoice_hides_its_deal_while_deals_is_off(viewer, org_a, documents):
    deal = documents[0]
    assert [d["id"] for d in _document_deals(viewer[0], documents)] == [
        str(deal.id)
    ] * 4
    before = _rows()

    set_modules_off(org_a, "deals")

    assert _document_deals(viewer[0], documents) == [None] * 4
    assert _rows() == before


@pytest.mark.parametrize(("field", "module", "kind", "make"), TASK_LINKS)
def test_a_task_sent_back_as_loaded_keeps_its_hidden_link(
    viewer, org_a, field, module, kind, make
):
    client, profile = viewer
    parent = make(org_a, profile)
    task = _task(org_a, profile, **{field: parent})
    set_modules_off(org_a, module)
    loaded = _get(client, f"/api/tasks/{task.id}/")["task_obj"]
    assert loaded[field] is None

    body = {key: loaded[key] for key in ("title", "status", "priority", "description")}
    body.update(
        {
            name: (loaded[name] or {}).get("id")
            for name in ("account", "opportunity", "case", "lead")
        }
    )
    response = client.put(f"/api/tasks/{task.id}/", body, format="json")

    assert response.status_code == 200, response.content
    task.refresh_from_db()
    assert getattr(task, f"{field}_id") == parent.id


def test_a_document_sent_back_as_loaded_keeps_its_hidden_deal(viewer, org_a, documents):
    client = viewer[0]
    deal, (invoice, estimate, recurring) = documents
    set_modules_off(org_a, "deals")
    targets = [
        (invoice, f"/api/invoices/{invoice.id}/", "invoice", "invoice_title"),
        (estimate, f"/api/invoices/estimates/{estimate.id}/", "estimate", "title"),
        (
            recurring,
            f"/api/invoices/recurring/{recurring.id}/",
            "recurring_invoice",
            "title",
        ),
    ]
    for record, url, key, title in targets:
        loaded = _get(client, url)[key]
        assert loaded["opportunity"] is None
        body = {
            title: loaded[title],
            "currency": loaded["currency"],
            "account_id": loaded["account"]["id"],
            "contact_id": loaded["contact"]["id"],
            "opportunity_id": None,
        }
        response = client.put(url, body, format="json")
        assert response.status_code == 200, (url, response.content)
        record.refresh_from_db()
        assert record.opportunity_id == deal.id, url


def test_a_time_entry_hides_its_invoice_while_invoices_is_off(viewer, org_a, account):
    """The invoice goes, but ``invoiced`` stays, since an invoiced entry is
    still locked against edits."""
    client, profile = viewer
    ticket = _ticket(org_a, profile, account=account)
    invoice = Invoice.objects.create(
        org=org_a, account=account, invoice_title="Time", invoice_number="INV-7"
    )
    billed = _logged(org_a, ticket, profile, invoice=invoice)
    unbilled = _logged(org_a, ticket, profile)

    def shown():
        """``{entry id: (list, timesheet, CSV)}``, each list and timesheet
        entry as ``(invoice, invoiced)`` and each CSV row as its Invoice cell."""
        listed = _get(client, f"/api/cases/{ticket.id}/time-entries/")
        days = _get(client, "/api/time-entries/timesheet/")["days"]
        week = {e["id"]: e for day in days for e in day["entries"]}
        export = client.get("/api/time-entries/report/export/")
        assert export.status_code == 200, export.content
        rows = list(
            csv.reader(io.StringIO(b"".join(export.streaming_content).decode()))
        )[1:]
        return {
            e["id"]: (
                (e["invoice"], e["invoiced"]),
                (week[e["id"]]["invoice"], week[e["id"]]["invoiced"]),
            )
            for e in listed
        }, sorted(row[-1] for row in rows)

    entries, cells = shown()
    assert entries[str(billed.id)] == (
        (str(invoice.id), True),
        ({"id": str(invoice.id), "invoice_number": "INV-7"}, True),
    )
    assert entries[str(unbilled.id)] == ((None, False), (None, False))
    assert cells == ["", "INV-7"]
    before = _rows()

    set_modules_off(org_a, "invoices")

    entries, cells = shown()
    assert entries[str(billed.id)] == ((None, True), (None, True))
    assert entries[str(unbilled.id)] == ((None, False), (None, False))
    assert cells == ["", ""]
    assert _rows() == before


def test_a_deal_hides_its_next_task_while_tasks_is_off(viewer, org_a):
    client, profile = viewer
    deal = _deal(org_a, profile, "Deal", "PROPOSAL", Decimal("5"))
    task = _task(org_a, profile, opportunity=deal)

    def next_activity():
        rows = _get(client, "/api/opportunities/")["opportunities"]
        return next(row for row in rows if row["id"] == str(deal.id))["next_activity"]

    assert next_activity()["id"] == str(task.id)

    set_modules_off(org_a, "tasks")

    assert next_activity() is None


def test_an_article_hides_its_tickets_while_tickets_is_off(viewer, org_a):
    client, profile = viewer
    article = Solution.objects.create(
        org=org_a, title="Reset", description="d", status="approved"
    )
    article.cases.add(_ticket(org_a, profile))

    def shown():
        rows = _get(client, "/api/cases/solutions/")["results"]
        detail = _get(client, f"/api/cases/solutions/{article.id}/")
        row = next(r for r in rows if r["id"] == str(article.id))
        return row["case_count"], detail["case_count"], len(detail["linked_cases"])

    assert shown() == (1, 1, 1)
    before = _rows()

    set_modules_off(org_a, "tickets")

    assert shown() == (0, 0, 0)
    assert _rows() == before


def test_a_board_card_hides_its_deal_while_deals_is_off(viewer, org_a):
    client, profile = viewer
    board = Board.objects.create(org=org_a, name="Board", owner=profile)
    column = BoardColumn.objects.create(org=org_a, board=board, name="Doing")
    deal = _deal(org_a, profile, "Deal", "PROPOSAL", Decimal("5"))
    BoardTask.objects.create(org=org_a, column=column, title="Card", opportunity=deal)
    url = f"/api/boards/columns/{column.id}/tasks/"
    assert _get(client, url)[0]["opportunity"] == str(deal.id)

    set_modules_off(org_a, "deals")

    assert _get(client, url)[0]["opportunity"] is None


def test_web_form_submissions_hide_off_module_records(viewer, org_a):
    client, profile = viewer
    form = WebForm.objects.create(name="Contact us", org=org_a)
    lead = Lead.objects.create(org=org_a, title="Lead", first_name="Lee")
    ticket = _ticket(org_a, profile, name="Help")
    for link in ({"lead": lead}, {"case": ticket}):
        WebFormSubmission.objects.create(
            org=org_a, form=form, status=WebFormSubmission.ACCEPTED, **link
        )
    url = f"/api/webforms/{form.id}/submissions/"

    def shown():
        rows = _get(client, url)["results"]
        return sorted(
            ((r["lead"], r["lead_name"], r["case"], r["case_name"]) for r in rows),
            key=repr,
        )

    lead_row = (str(lead.id), str(lead), None, None)
    ticket_row = (None, None, str(ticket.id), "Help")
    assert shown() == sorted([lead_row, ticket_row], key=repr)

    set_modules_off(org_a, "leads", "tickets")

    assert shown() == [(None, None, None, None)] * 2


def test_a_person_page_hides_off_module_records(viewer, org_a):
    client, profile = viewer
    deal = _deal(org_a, profile, "Deal", "PROPOSAL", Decimal("5"))
    ticket = _ticket(org_a, profile)
    account = Account.objects.create(name="Kept", org=org_a)
    for target in (deal, ticket, account):
        Comment.objects.create(
            org=org_a, content_object=target, comment="Note", commented_by=profile
        )
    url = f"/api/user/{profile.user_id}/"

    def shown():
        data = _get(client, url)["data"]
        types = sorted(c["content_type"] for c in data["comments"])
        return len(data["opportunity_list"]), len(data["cases"]), types

    assert shown() == (1, 1, ["account", "case", "opportunity"])
    before = _rows()

    set_modules_off(org_a, "deals", "tickets")

    assert shown() == (0, 0, ["account"])
    assert _rows() == before


def test_a_product_counts_no_invoices_while_invoices_is_off(viewer, org_a, account):
    client = viewer[0]
    product = Product.objects.create(org=org_a, name="Seat", price=Decimal("5"))
    invoice = Invoice.objects.create(org=org_a, account=account, invoice_title="I")
    InvoiceLineItem.objects.create(
        org=org_a,
        invoice=invoice,
        product=product,
        name="Seat",
        quantity=Decimal("1"),
        unit_price=Decimal("5"),
    )

    def used_on():
        rows = _get(client, "/api/invoices/products/")["results"]
        detail = _get(client, f"/api/invoices/products/{product.id}/")
        row = next(r for r in rows if r["id"] == str(product.id))
        return row["used_on"], detail["used_on"]

    assert used_on() == (1, 1)

    set_modules_off(org_a, "invoices")

    assert used_on() == (0, 0)


def _three_of_each(org, profile):
    for n in range(3):
        deal = _deal(org, profile, f"Deal {n}", "PROPOSAL", Decimal("5"))
        _task(org, profile, opportunity=deal)
        ticket = _ticket(org, profile, name=f"Ticket {n}")
        _logged(org, ticket, profile)
        Solution.objects.create(
            org=org, title=f"Article {n}", description="d", status="approved"
        ).cases.add(ticket)


ROW_LISTS = [
    pytest.param("/api/tasks/?slim=true", ("deals",), id="tasks"),
    pytest.param("/api/tasks/kanban/", ("deals",), id="task-board"),
    pytest.param("/api/cases/?slim=true", ("timesheet",), id="tickets"),
    pytest.param("/api/opportunities/", ("tasks",), id="deals"),
    pytest.param("/api/cases/solutions/", ("tickets",), id="articles"),
]


@pytest.mark.parametrize(("url", "off"), ROW_LISTS)
def test_hiding_adds_no_queries(admin_client, admin_profile, org_a, url, off):
    _three_of_each(org_a, admin_profile)

    def count():
        with CaptureQueriesContext(connection) as queries:
            _get(admin_client, url)
        return len(queries)

    on = count()
    set_modules_off(org_a, *off)

    assert count() <= on
