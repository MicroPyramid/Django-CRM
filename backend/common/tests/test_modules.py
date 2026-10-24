from datetime import UTC, datetime
from types import SimpleNamespace

import crum
import pytest
from django.apps import apps
from django.db.models import Model

from common.audit_log import SecurityAuditLog, audit_log
from common.modules import (
    KEYS,
    MODEL_MODULES,
    available_modules,
    enabled_modules,
    model_module,
    module_label,
    module_off_body,
    module_off_message,
    module_on_since,
    only_available,
    ordered_modules,
    org_of,
)
from common.testing import set_modules_off
from leads.models import Lead

ALL = [
    "deals",
    "leads",
    "goals",
    "tasks",
    "tickets",
    "knowledge_base",
    "documents",
    "invoices",
    "timesheet",
]


def test_a_new_org_has_every_module_on(org_a):
    assert org_a.modules_off == []
    assert org_a.module_order == []
    assert org_a.modules_on_at == {}
    assert available_modules(org_a) == frozenset(KEYS)


def test_default_order_is_todays_sidebar():
    assert KEYS == tuple(ALL)


def test_a_module_needs_its_parent(org_a):
    set_modules_off(org_a, "deals")
    assert "goals" in enabled_modules(org_a)
    assert "goals" not in available_modules(org_a)
    set_modules_off(org_a, "tickets")
    assert "timesheet" in enabled_modules(org_a)
    assert "timesheet" not in available_modules(org_a)
    set_modules_off(org_a, "goals")
    assert "deals" in available_modules(org_a)


def test_unknown_or_malformed_stored_keys_are_ignored(org_a):
    set_modules_off(org_a, "crm", 3, None)
    assert available_modules(org_a) == frozenset(KEYS)


def test_labels_follow_terminology(org_a):
    try:
        org_a.terminology = {"lead.plural": "Enquiries"}
        assert module_label(org_a, "leads") == "Enquiries"
        assert (
            module_off_message(org_a, "leads")
            == "Enquiries is switched off for this organization."
        )
        for bad in ("", 5):
            org_a.terminology = {"lead.plural": bad}
            assert module_label(org_a, "leads") == "Leads"
        assert module_label(org_a, "deals") == "Pipeline"
    finally:
        crum.set_current_request(None)


def test_off_body(org_a):
    assert module_off_body(org_a, "tickets") == {
        "detail": "Tickets is switched off for this organization.",
        "code": "module_off",
        "module": "tickets",
    }


def test_org_order_applies_within_groups(org_a):
    org_a.module_order = ["leads", "timesheet", "invoices"]
    assert [m.key for m in ordered_modules(org_a)] == [
        "leads",
        "deals",
        "goals",
        "tasks",
        "tickets",
        "knowledge_base",
        "documents",
        "timesheet",
        "invoices",
    ]


def test_module_on_since_reads_the_stamp(org_a):
    org_a.modules_on_at = {
        "invoices": "2026-10-01T09:00:00+00:00",
        "leads": "yesterday",
    }
    assert module_on_since(org_a, "invoices") == datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
    assert module_on_since(org_a, "leads") is None
    assert module_on_since(org_a, "tasks") is None


def test_only_available_empties_an_off_module(org_a):
    Lead.objects.create(title="L", org=org_a)
    assert only_available(org_a, "leads", Lead.objects.all()).count() == 1
    set_modules_off(org_a, "leads")
    assert only_available(org_a, "leads", Lead.objects.all()).count() == 0


def test_org_of_prefers_the_request_org(org_a, django_assert_num_queries):
    lead = Lead.objects.create(title="L", org=org_a)
    lead = Lead.objects.get(pk=lead.pk)
    try:
        crum.set_current_request(SimpleNamespace(profile=SimpleNamespace(org=org_a)))
        with django_assert_num_queries(0):
            assert org_of(lead) is org_a
        crum.set_current_request(None)
        assert org_of(lead) == lead.org
    finally:
        crum.set_current_request(None)


def test_every_model_of_a_module_app_is_placed():
    for app in (
        "leads",
        "opportunity",
        "tasks",
        "cases",
        "business_hours",
        "macros",
        "invoices",
    ):
        for model in apps.get_app_config(app).get_models():
            label = model._meta.label
            if label in ("invoices.Product", "leads.LeadSource"):
                assert model_module(label) is None
            else:
                assert label in MODEL_MODULES, label
    assert issubclass(apps.get_model("common.Document"), Model)
    assert model_module("common.Document") == "documents"


def test_modules_changed_is_audited(org_a, admin_user):
    audit_log.modules_changed(admin_user, org_a, ["tickets"], ["invoices"], True)
    row = SecurityAuditLog.objects.get(event_type="MODULES_CHANGED")
    assert (
        row.description
        == "Switched off Tickets; Switched on Invoices; Reordered modules"
    )
    assert row.metadata == {
        "switched_off": ["tickets"],
        "switched_on": ["invoices"],
        "reordered": True,
    }
    assert row.org == org_a


@pytest.mark.parametrize(
    "bad", [[["x"]], [{}], ["nope", 3, None], "leads", {"a": 1}, None]
)
def test_malformed_stored_order_is_ignored(org_a, bad):
    org_a.module_order = bad
    assert [m.key for m in ordered_modules(org_a)] == ALL


def test_deals_stops_copy_reads_with_the_default_label(org_a):
    from common.modules import module

    text = module("deals").stops.format(label=module_label(org_a, "deals"))
    assert text.startswith("Everything in Pipeline leaves every menu")
