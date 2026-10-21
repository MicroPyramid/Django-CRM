import uuid

import pytest
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from cases.models import Case
from common import object_registry
from common.custom_fields import is_supported_target
from common.models import CustomFieldDefinition, Teams
from common.object_registry import (
    BUILT_IN,
    all_objects,
    object_for_record,
    object_for_target,
)
from common.serializer import CustomFieldDefinitionSerializer
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
