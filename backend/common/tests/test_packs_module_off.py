"""Applying and clearing a starter pack while modules are off: off parts are
reported as skipped with the module message, and no off module's sample rows
are ever deleted."""

import copy

import pytest

from accounts.models import Account
from cases.models import Case, CasePipeline
from common.models import CustomFieldDefinition
from common.modules import module_off_message
from common.packs.applier import apply_pack, clear_sample_data
from common.packs.loader import get_pack
from common.testing import set_modules_off
from contacts.models import Contact
from invoices.models import Product
from leads.models import Lead, LeadPipeline
from opportunity.models import Opportunity
from tasks.models import Task, TaskPipeline


@pytest.fixture
def pack():
    """Real estate plus a ticket custom field, trimmed to two sample tickets."""
    pack = copy.deepcopy(get_pack("real-estate"))
    pack["custom_fields"] = [
        *pack["custom_fields"],
        {
            "target": "Case",
            "key": "severity",
            "label": "Severity",
            "field_type": "text",
        },
    ]
    sample = pack["sample_data"]
    sample["tickets"] = sample["tickets"][:2]
    kept = {t["name"] for t in sample["tickets"]}
    sample["tasks"] = [
        t for t in sample["tasks"] if not t.get("ticket") or t["ticket"] in kept
    ]
    return pack


def _skipped(report, org, key):
    message = module_off_message(org, key)
    return [(s["type"], s["name"]) for s in report["skipped"] if s["reason"] == message]


def test_a_pack_skips_off_modules_and_says_why(org_a, admin_profile, pack):
    set_modules_off(org_a, "tickets", "deals")
    sample = pack["sample_data"]
    ticket_tasks = [t["title"] for t in sample["tasks"] if t.get("ticket")]
    deal_tasks = [t["title"] for t in sample["tasks"] if t.get("deal")]
    assert ticket_tasks and deal_tasks

    report = apply_pack(org_a, pack, admin_profile)

    assert not CasePipeline.objects.filter(org=org_a).exists()
    assert not CustomFieldDefinition.objects.filter(
        org=org_a, target_model="Case"
    ).exists()
    assert not Case.objects.filter(org=org_a).exists()
    assert not Opportunity.objects.filter(org=org_a).exists()
    skipped_tickets = _skipped(report, org_a, "tickets")
    assert ("case_pipeline", pack["case_pipeline"]["name"]) in skipped_tickets
    assert ("custom_field", "severity") in skipped_tickets
    assert {("sample_ticket", t["name"]) for t in sample["tickets"]} <= set(
        skipped_tickets
    )
    assert {("sample_task", title) for title in ticket_tasks} <= set(skipped_tickets)
    skipped_deals = _skipped(report, org_a, "deals")
    assert {("sample_deal", d["name"]) for d in sample["deals"]} <= set(skipped_deals)
    assert {("sample_task", title) for title in deal_tasks} <= set(skipped_deals)
    # The parts of modules that are on are built as before.
    assert LeadPipeline.objects.filter(org=org_a).exists()
    assert Lead.objects.filter(org=org_a, is_sample=True).exists()
    assert Account.objects.filter(org=org_a, is_sample=True).exists()
    assert Contact.objects.filter(org=org_a, is_sample=True).exists()
    assert Task.objects.filter(org=org_a, is_sample=True).exists()
    assert report["failed"] == []


@pytest.mark.parametrize(
    ("module", "key", "pipeline"),
    [
        ("leads", "lead_pipeline", LeadPipeline),
        ("tickets", "case_pipeline", CasePipeline),
        ("tasks", "task_pipeline", TaskPipeline),
    ],
)
def test_each_pipeline_follows_its_module(
    org_a, admin_profile, pack, module, key, pipeline
):
    set_modules_off(org_a, module)
    # Read before the pack applies its terminology.
    reason = module_off_message(org_a, module)

    report = apply_pack(org_a, pack, admin_profile)

    name = pack[key]["name"]
    assert not pipeline.objects.filter(org=org_a, name=name).exists()
    assert {"type": key, "name": name, "reason": reason} in report["skipped"]
    others = {"lead_pipeline", "case_pipeline", "task_pipeline"} - {key}
    assert {c["type"] for c in report["created"]} >= others


@pytest.mark.parametrize(
    ("off", "built"),
    [
        (("deals",), True),
        (("invoices",), True),
        (("deals", "invoices"), False),
    ],
)
def test_products_skip_only_when_deals_and_invoices_are_both_off(
    org_a, admin_profile, pack, off, built
):
    set_modules_off(org_a, *off)

    report = apply_pack(org_a, pack, admin_profile)

    assert Product.objects.filter(org=org_a).exists() is built
    skipped = _skipped(report, org_a, "invoices")
    assert (("product", pack["products"][0]["name"]) in skipped) is not built


def test_clearing_sample_data_keeps_off_module_rows(org_a, admin_profile, pack):
    apply_pack(org_a, pack, admin_profile)
    tickets = Case.objects.filter(org=org_a, is_sample=True)
    assert tickets.count() == 2
    ticket_accounts = set(tickets.values_list("account_id", flat=True)) - {None}
    set_modules_off(org_a, "tickets")

    result = clear_sample_data(org_a)

    assert result["switched_off"] == {"sample_ticket": 2}
    assert tickets.count() == 2
    assert ticket_accounts
    assert ticket_accounts <= set(
        Account.objects.filter(org=org_a, is_sample=True).values_list("id", flat=True)
    )
    for model in (Lead, Opportunity, Task, Contact):
        assert not model.objects.filter(org=org_a, is_sample=True).exists()
    assert "sample_ticket" not in result["deleted"]


def test_clearing_with_every_module_on_reports_nothing_switched_off(
    org_a, admin_profile, pack
):
    apply_pack(org_a, pack, admin_profile)

    assert clear_sample_data(org_a)["switched_off"] == {}
