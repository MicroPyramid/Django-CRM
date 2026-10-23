import uuid
from dataclasses import dataclass

import pytest
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from cases.models import Case, CaseWatcher
from common import object_registry
from common.custom_fields import is_supported_target
from common.models import CustomFieldDefinition, Document, Teams
from common.object_registry import (
    BUILT_IN,
    RegistryConflict,
    all_objects,
    built_in_objects,
    object_for_key,
    object_for_record,
    object_for_target,
    object_module,
    register_hook,
)
from common.serializer import CustomFieldDefinitionSerializer
from common.testing import set_modules_off
from common.tests.object_records import make_record
from conftest import rls_org


def test_the_built_ins_are_the_nine_record_types():
    assert [e.key for e in BUILT_IN] == [
        "lead",
        "contact",
        "account",
        "deal",
        "ticket",
        "task",
        "invoice",
        "estimate",
        "recurring_invoice",
    ]


def test_every_model_with_custom_fields_has_exactly_one_entry():
    with_column = {
        m
        for m in apps.get_models()
        if any(f.name == "custom_fields" for f in m._meta.concrete_fields)
    }
    assert {e.model for e in BUILT_IN} == with_column
    assert len(BUILT_IN) == len(with_column)


def test_keys_and_targets_are_unique():
    keys = [e.key for e in BUILT_IN]
    targets = [e.custom_field_target for e in BUILT_IN]
    assert len(set(keys)) == len(keys)
    assert len(set(targets)) == len(targets)


def test_capability_flags_match_todays_coverage():
    seven = {"lead", "contact", "account", "deal", "ticket", "task", "invoice"}
    assert {e.key for e in BUILT_IN if e.attachments} == seven
    assert {e.key for e in BUILT_IN if e.activity_feed} == seven


@pytest.mark.parametrize("entry", BUILT_IN, ids=lambda e: e.key)
def test_the_read_rule_is_org_limited_and_narrower_for_a_member(
    entry, admin_profile, user_profile, regular_user, admin_user, org_a, org_b
):
    mine = make_record(entry.key, org_a, regular_user)
    theirs = make_record(entry.key, org_a, admin_user)
    with rls_org(org_b):
        foreign = make_record(entry.key, org_b)
    for profile in (admin_profile, user_profile):
        qs = entry.readable(profile)
        assert qs.model is entry.model
        assert qs.filter(pk=mine.pk).exists()
        assert not qs.filter(pk=foreign.pk).exists()
    assert entry.readable(admin_profile).filter(pk=theirs.pk).exists()
    assert not entry.readable(user_profile).filter(pk=theirs.pk).exists()


@pytest.mark.parametrize("entry", BUILT_IN, ids=lambda e: e.key)
def test_records_are_the_orgs_rows(entry, org_a, org_b):
    mine = make_record(entry.key, org_a)
    with rls_org(org_b):
        foreign = make_record(entry.key, org_b)
    with rls_org(org_a):
        pks = set(entry.records(org_a).values_list("pk", flat=True))
    assert mine.pk in pks
    assert foreign.pk not in pks


def test_all_objects_is_the_built_ins(org_a):
    assert all_objects(org_a) == BUILT_IN


def test_lookups_read_the_module_global_at_call_time(org_a, monkeypatch):
    only_lead = BUILT_IN[:1]
    monkeypatch.setattr(object_registry, "BUILT_IN", only_lead)
    assert object_registry.all_objects(org_a) == only_lead
    assert object_registry.object_for_target(org_a, "Case") is None
    case_ct = ContentType.objects.get_for_model(Case)
    assert object_registry.object_for_record(org_a, case_ct, uuid.uuid4()) is None


def test_object_for_target(org_a):
    assert object_for_target(org_a, "Opportunity").key == "deal"
    assert object_for_target(org_a, "deal") is None  # a key is not a target
    assert object_for_target(org_a, "Ghost") is None


def test_object_for_record(org_a):
    case_ct = ContentType.objects.get_for_model(Case)
    assert object_for_record(org_a, case_ct, uuid.uuid4()).key == "ticket"
    assert (
        object_for_record(org_a, ContentType.objects.get_for_model(Teams), uuid.uuid4())
        is None
    )
    ghost = ContentType.objects.create(app_label="gone", model="ghost")
    assert object_for_record(org_a, ghost, uuid.uuid4()) is None


def test_the_endpoint_accepts_exactly_the_registry_targets():
    choices = CustomFieldDefinitionSerializer().fields["target_model"].choices
    assert set(choices) == {e.custom_field_target for e in BUILT_IN}


def test_the_model_carries_no_second_list():
    assert not CustomFieldDefinition._meta.get_field("target_model").choices


def test_is_supported_target_matches_the_registry():
    assert all(is_supported_target(e.custom_field_target) for e in BUILT_IN)
    assert not is_supported_target("Comment") and not is_supported_target("deal")


@dataclass(frozen=True)
class FakeEntry:
    key: str
    prefix: str = ""
    custom_field_target: str = ""
    label: str = "Fake"
    label_plural: str = "Fakes"
    attachments: bool = False
    activity_feed: bool = False
    links: bool = False
    model_label: str = "common.Document"

    @property
    def model(self):
        return apps.get_model(self.model_label)

    def records(self, org):
        return Document.objects.filter(org=org, title__startswith=self.prefix)

    def readable(self, profile):
        return self.records(profile.org)

    def editable(self, profile):
        return self.records(profile.org)


def _hook_for(org, *entries):
    return lambda o: entries if o is not None and o.pk == org.pk else ()


def test_labels_match_the_web_app():
    assert {e.custom_field_target: e.label_plural for e in BUILT_IN} == {
        "Account": "Accounts",
        "Case": "Tickets",
        "Contact": "Contacts",
        "Estimate": "Estimates",
        "Invoice": "Invoices",
        "Lead": "Leads",
        "Opportunity": "Deals",
        "RecurringInvoice": "Recurring invoices",
        "Task": "Tasks",
    }


def test_links_are_the_six_linkable_objects():
    assert [e.key for e in BUILT_IN if e.links] == [
        "lead",
        "contact",
        "account",
        "deal",
        "ticket",
        "task",
    ]


@pytest.mark.parametrize("entry", [e for e in BUILT_IN if e.links], ids=lambda e: e.key)
def test_the_edit_rule_is_org_limited_and_narrower_for_a_member(
    entry, admin_profile, user_profile, regular_user, admin_user, org_a, org_b
):
    mine = make_record(entry.key, org_a, regular_user)
    theirs = make_record(entry.key, org_a, admin_user)
    with rls_org(org_b):
        foreign = make_record(entry.key, org_b)
    admin_qs = entry.editable(admin_profile)
    member_qs = entry.editable(user_profile)
    assert admin_qs.model is entry.model
    assert admin_qs.filter(pk=mine.pk).exists()
    assert admin_qs.filter(pk=theirs.pk).exists()
    assert member_qs.filter(pk=mine.pk).exists()
    assert not member_qs.filter(pk=theirs.pk).exists()
    assert not admin_qs.filter(pk=foreign.pk).exists()
    assert not member_qs.filter(pk=foreign.pk).exists()


def test_a_ticket_watcher_reads_but_cannot_edit(user_profile, admin_user, org_a):
    case = make_record("ticket", org_a, admin_user)
    CaseWatcher.objects.create(case=case, profile=user_profile, org=org_a)
    entry = object_for_key(org_a, "ticket")
    assert entry.readable(user_profile).filter(pk=case.pk).exists()
    assert not entry.editable(user_profile).filter(pk=case.pk).exists()


def test_entries_without_links_edit_nothing(admin_profile, org_a):
    make_record("invoice", org_a)
    entry = object_for_key(org_a, "invoice")
    assert entry.editable(admin_profile).count() == 0


def test_a_hook_adds_entries_for_its_org_only(monkeypatch, org_a, org_b):
    fake = FakeEntry("obj:fake", custom_field_target="obj:fake")
    monkeypatch.setattr(object_registry, "_HOOKS", [_hook_for(org_a, fake)])
    assert all_objects(org_a)[-1].key == "obj:fake"
    assert all_objects(org_a)[: len(BUILT_IN)] == BUILT_IN
    assert all_objects(org_b) == BUILT_IN
    assert all_objects(None) == BUILT_IN


@pytest.mark.parametrize("clash", [{"key": "lead"}, {"custom_field_target": "Lead"}])
def test_a_hook_entry_reusing_a_built_in_raises(clash, monkeypatch, org_a):
    fields = {"key": "obj:fake", "custom_field_target": "obj:fake", **clash}
    monkeypatch.setattr(
        object_registry, "_HOOKS", [_hook_for(org_a, FakeEntry(**fields))]
    )
    with pytest.raises(RegistryConflict, match="Lead|lead"):
        all_objects(org_a)


def test_two_hook_entries_with_one_key_raise(monkeypatch, org_a):
    one = FakeEntry("obj:dup", custom_field_target="obj:one")
    two = FakeEntry("obj:dup", custom_field_target="obj:two")
    monkeypatch.setattr(object_registry, "_HOOKS", [_hook_for(org_a, one, two)])
    with pytest.raises(RegistryConflict, match="obj:dup"):
        all_objects(org_a)


def test_register_hook_keeps_one_copy(monkeypatch):
    monkeypatch.setattr(object_registry, "_HOOKS", [])

    def hook(org):
        return ()

    register_hook(hook)
    register_hook(hook)
    assert object_registry._HOOKS == [hook]


def test_object_for_key(monkeypatch, org_a):
    fake = FakeEntry("obj:fake", custom_field_target="obj:fake")
    assert object_for_key(org_a, "deal").custom_field_target == "Opportunity"
    assert object_for_key(org_a, "obj:fake") is None
    monkeypatch.setattr(object_registry, "_HOOKS", [_hook_for(org_a, fake)])
    assert object_for_key(org_a, "obj:fake") is fake
    assert object_for_key(org_a, "Opportunity") is None
    assert object_for_key(org_a, "ghost") is None


def test_object_for_record_picks_the_entry_holding_the_record(monkeypatch, org_a):
    first = FakeEntry("obj:first", prefix="first-", custom_field_target="obj:first")
    second = FakeEntry("obj:second", prefix="second-", custom_field_target="obj:second")
    monkeypatch.setattr(object_registry, "_HOOKS", [_hook_for(org_a, first, second)])
    ct = ContentType.objects.get_for_model(Document)
    doc_one = Document.objects.create(title="first-a", org=org_a)
    doc_two = Document.objects.create(title="second-a", org=org_a)
    other = Document.objects.create(title="third-a", org=org_a)
    assert object_for_record(org_a, ct, doc_one.pk) is first
    assert object_for_record(org_a, ct, doc_two.pk) is second
    assert object_for_record(org_a, ct, other.pk) is None


def test_the_custom_field_choices_carry_labels():
    assert dict(CustomFieldDefinitionSerializer().fields["target_model"].choices) == {
        e.custom_field_target: e.label_plural for e in BUILT_IN
    }


def _keys(entries):
    return {e.key for e in entries}


def test_entry_module_follows_the_model_map():
    assert {e.key: e.module for e in BUILT_IN} == {
        "lead": "leads",
        "contact": None,
        "account": None,
        "deal": "deals",
        "ticket": "tickets",
        "task": "tasks",
        "invoice": "invoices",
        "estimate": "invoices",
        "recurring_invoice": "invoices",
    }


def test_all_objects_drops_off_module_entries(org_a):
    set_modules_off(org_a, "tickets")
    keys = _keys(all_objects(org_a))
    assert "ticket" not in keys and "lead" in keys
    set_modules_off(org_a, "invoices")
    keys = _keys(all_objects(org_a))
    assert not keys & {"invoice", "estimate", "recurring_invoice"}
    assert {"contact", "account", "ticket"} <= keys
    assert _keys(built_in_objects(org_a)) == keys
    set_modules_off(org_a)
    assert all_objects(org_a) == BUILT_IN == built_in_objects(org_a)


def test_all_objects_without_an_org_is_the_full_list(org_a):
    set_modules_off(org_a, "tickets", "invoices")
    assert all_objects(None) == BUILT_IN


def test_a_hook_entry_without_a_module_stays(monkeypatch, org_a):
    fake = FakeEntry("obj:fake", custom_field_target="obj:fake")
    monkeypatch.setattr(object_registry, "_HOOKS", [_hook_for(org_a, fake)])
    set_modules_off(org_a, "tickets", "invoices", "deals")
    assert all_objects(org_a)[-1] is fake
    assert "obj:fake" not in {e.key for e in built_in_objects(org_a)}


def test_object_module_ignores_the_filter(org_a):
    set_modules_off(org_a, "tickets")
    assert object_module("ticket") == "tickets"
    assert object_module("contact") is None
    assert object_module("ghost") is None
    assert object_module(target="Case") == "tickets"
    assert object_module(target="RecurringInvoice") == "invoices"
    assert object_module(target="Contact") is None
    assert object_module(target="ticket") is None


def test_an_attachment_on_an_off_module_record_is_404(
    admin_client, admin_profile, org_a
):
    from django.core.files.uploadedfile import SimpleUploadedFile

    from accounts.models import Account
    from common.utils import create_attachment

    case = Case.objects.create(name="Watched", org=org_a, status="New")
    account = Account.objects.create(name="Acme", org=org_a)
    on_case = create_attachment(SimpleUploadedFile("a.txt", b"x"), case, admin_profile)
    on_account = create_attachment(
        SimpleUploadedFile("b.txt", b"y"), account, admin_profile
    )
    url = "/api/attachments/{}/download/"
    assert admin_client.get(url.format(on_case.pk)).status_code == 200
    set_modules_off(org_a, "tickets")
    assert admin_client.get(url.format(on_case.pk)).status_code == 404
    assert admin_client.get(url.format(on_account.pk)).status_code == 200
    set_modules_off(org_a)
    assert admin_client.get(url.format(on_case.pk)).status_code == 200
