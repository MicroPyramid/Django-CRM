"""Shared surfaces leave off modules out: search, the home figures, Today, the
activity feed, saved views and tag usage."""

from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.http import QueryDict
from django.utils import timezone

from accounts.models import Account
from cases.models import Case, Solution
from common.models import Activity, Document, SavedView, Tags
from common.modules import model_module
from common.saved_views import LISTS, SAVED_VIEW_MODULES
from common.testing import set_modules_off
from contacts.models import Contact
from invoices.models import Invoice
from leads.models import Lead
from opportunity.models import DealPipeline, Opportunity, SalesGoal

pytestmark = pytest.mark.django_db

TICKETS_OFF = "Tickets is switched off for this organization."


def _stamp(obj, user):
    type(obj).objects.filter(pk=obj.pk).update(created_by=user)
    obj.refresh_from_db()
    return obj


def test_search_leaves_out_off_modules(admin_client, org_a):
    token = "Zephyr"
    Lead.objects.create(
        first_name=token,
        last_name="L",
        status="in process",
        company_name="X",
        org=org_a,
    )
    Case.objects.create(
        name=f"{token} ticket", status="New", priority="Normal", org=org_a
    )
    account = Account.objects.create(name=f"{token} Corp", org=org_a)
    Contact.objects.create(first_name=token, last_name="P", email="c@x.com", org=org_a)
    Invoice.objects.create(
        invoice_title=f"{token} invoice",
        account=account,
        currency="USD",
        status="Draft",
        org=org_a,
    )
    Solution.objects.create(
        org=org_a, title=f"{token} guide", description="d", status="approved"
    )

    def types():
        body = admin_client.get("/api/search/", {"q": token}).json()
        return {r["type"] for r in body["results"]}

    assert types() == {"lead", "ticket", "account", "contact", "invoice", "solution"}
    set_modules_off(org_a, "leads", "tickets", "invoices", "knowledge_base")
    assert types() == {"account", "contact"}


def test_home_figures_leave_out_off_modules(admin_client, org_a, admin_profile):
    today = timezone.localdate()
    Lead.objects.create(first_name="A", last_name="B", status="assigned", org=org_a)
    Opportunity.objects.create(name="Deal", stage="PROSPECTING", org=org_a)
    from tasks.models import Task

    Task.objects.create(
        title="T",
        status="New",
        priority="Low",
        due_date=today + timedelta(days=1),
        org=org_a,
    )
    SalesGoal.objects.create(
        name="G",
        goal_type="REVENUE",
        target_value=Decimal("100"),
        period_type="MONTHLY",
        period_start=today - timedelta(days=1),
        period_end=today + timedelta(days=5),
        assigned_to=admin_profile,
        currency="USD",
        org=org_a,
    )
    body = admin_client.get("/api/dashboard/").json()
    assert body["leads_count"] == 1
    assert body["opportunities_count"] == 1
    assert len(body["goal_summary"]) == 1
    assert len(body["tasks"]) == 1

    set_modules_off(org_a, "leads", "deals", "tasks")
    body = admin_client.get("/api/dashboard/").json()
    assert body["leads_count"] == 0
    assert body["opportunities_count"] == 0
    assert body["goal_summary"] == []
    assert body["tasks"] == []
    assert body["hot_leads"] == []


@pytest.mark.parametrize("client_name", ["admin_client", "user_client"])
def test_home_pipeline_is_empty_and_not_created_while_pipeline_is_off(
    request, org_a, client_name
):
    client = request.getfixturevalue(client_name)

    def pipeline():
        response = client.get("/api/dashboard/")
        assert response.status_code == 200
        return response.json()["pipeline_by_stage"]

    set_modules_off(org_a, "deals")
    assert pipeline() == {}
    assert not DealPipeline.objects.filter(org=org_a).exists()

    set_modules_off(org_a)
    stages = pipeline()
    assert stages
    assert all(row["label"] and row["kind"] for row in stages.values())


def test_today_leaves_out_off_modules(admin_client, org_a):
    yesterday = timezone.localdate() - timedelta(days=1)
    account = Account.objects.create(name="Co", org=org_a)
    Invoice.objects.create(
        invoice_title="Late",
        account=account,
        currency="USD",
        status="Sent",
        due_date=yesterday,
        total_amount=Decimal("10"),
        org=org_a,
    )
    Case.objects.create(name="Help", status="New", priority="Normal", org=org_a)
    url = "/api/dashboard/today/"
    body = admin_client.get(url).json()
    assert {i["id"].split("-")[0] for i in body["queue"]} == {"invoice", "case"}

    set_modules_off(org_a, "tickets", "invoices")
    body = admin_client.get(url).json()
    assert body["queue"] == []
    assert body["summary"]["sources"] == []
    assert body["summary"]["count"] == 0


def test_the_import_prompt_ignores_leads_while_off(admin_client, org_a):
    Lead.objects.create(first_name="A", last_name="B", status="assigned", org=org_a)
    url = "/api/dashboard/"
    assert admin_client.get(url).json()["empty_workspace"] is False
    set_modules_off(org_a, "leads")
    assert admin_client.get(url).json()["empty_workspace"] is True


def test_the_activity_feed_leaves_out_off_modules(
    admin_client, user_client, org_a, admin_profile, regular_user
):
    case = _stamp(
        Case.objects.create(name="Mine", status="New", priority="Normal", org=org_a),
        regular_user,
    )
    document = Document.objects.create(title="Doc", document_file="d/x.pdf", org=org_a)
    account = _stamp(Account.objects.create(name="Acme", org=org_a), regular_user)
    for entity_type, record, name in (
        ("Case", case, "Mine"),
        ("Document", document, "Doc"),
        ("Account", account, "Acme"),
    ):
        Activity.objects.create(
            user=admin_profile,
            action="UPDATE",
            entity_type=entity_type,
            entity_id=record.id,
            entity_name=name,
            org=org_a,
        )

    def names(client):
        rows = client.get("/api/activities/").json()["activities"]
        return {r["entity_name"] for r in rows}

    assert names(admin_client) == {"Mine", "Doc", "Acme"}
    assert "Mine" in names(user_client)

    set_modules_off(org_a, "tickets")
    assert names(admin_client) == {"Doc", "Acme"}
    assert names(user_client) == {"Acme"}

    set_modules_off(org_a, "tickets", "documents")
    assert names(admin_client) == {"Acme"}


@pytest.fixture
def views(org_a, user_profile):
    return {
        module: SavedView.objects.create(
            org=org_a, profile=user_profile, module=module, name=module, filters={}
        )
        for module in ("leads", "cases", "contacts")
    }


def test_saved_views_of_an_off_module_are_hidden(user_client, org_a, views):
    url = "/api/saved-views/"
    set_modules_off(org_a, "tickets")
    listed = user_client.get(url).json()["saved_views"]
    assert {v["module"] for v in listed} == {"leads", "contacts"}
    assert user_client.get(url, {"module": "cases"}).json()["saved_views"] == []
    detail = f"{url}{views['cases'].id}/"
    assert user_client.get(detail).status_code == 404
    assert user_client.patch(detail, {"name": "new"}, format="json").status_code == 404
    assert user_client.delete(detail).status_code == 404
    assert SavedView.objects.filter(pk=views["cases"].pk, name="cases").exists()
    assert user_client.get(f"{url}{views['leads'].id}/").status_code == 200

    org_a.modules_off = []
    org_a.save(update_fields=["modules_off"])
    assert user_client.get(detail).status_code == 200


def test_saving_a_view_for_an_off_module_is_refused(user_client, org_a):
    set_modules_off(org_a, "tickets")
    response = user_client.post(
        "/api/saved-views/",
        {"module": "cases", "name": "Open", "filters": {}},
        format="json",
    )
    assert response.status_code == 400
    assert response.json() == {"module": [TICKETS_OFF]}
    ok = user_client.post(
        "/api/saved-views/",
        {"module": "contacts", "name": "Open", "filters": {}},
        format="json",
    )
    assert ok.status_code == 201


@pytest.mark.parametrize("module", sorted(LISTS))
def test_each_saved_view_list_follows_its_models_module(
    module, admin_user, admin_profile
):
    """A list missing from SAVED_VIEW_MODULES would stay on with its module off."""
    build, _ = LISTS[module]
    queryset = build(
        SimpleNamespace(profile=admin_profile, user=admin_user), QueryDict()
    )
    assert SAVED_VIEW_MODULES.get(module) == model_module(queryset.model._meta.label)


def test_tag_usage_leaves_out_off_modules(admin_client, org_a):
    tag = Tags.objects.create(name="Vip", slug="vip", org=org_a)
    case = Case.objects.create(name="C", status="New", priority="Normal", org=org_a)
    case.tags.add(tag)

    def body():
        return admin_client.get("/api/tags/").json()

    row = body()["tags"][0]
    assert row["usage"]["cases"] == 1
    assert {"macros", "solutions"} <= set(row["usage"])
    assert body()["totals"]["unused"] == 0

    set_modules_off(org_a, "tickets", "knowledge_base")
    data = body()
    usage = data["tags"][0]["usage"]
    assert not {"cases", "macros", "solutions"} & set(usage)
    assert "accounts" in usage
    assert data["totals"]["unused"] == 0
