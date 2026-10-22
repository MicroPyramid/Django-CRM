"""The automation tables: their indexes, uniqueness rules and row-level security."""

import uuid

import pytest
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from automation.models import AutomationRotation, AutomationRule, AutomationRun
from common.testing import org_tables_not_covered, rls_policy_gaps

MODELS = (AutomationRule, AutomationRun, AutomationRotation)


@pytest.fixture
def rule(org_a):
    return AutomationRule.objects.create(org=org_a, name="Rule", object_key="lead")


def _run(rule, status, window_start=None):
    return AutomationRun.objects.create(
        org=rule.org,
        rule=rule,
        object_key="lead",
        record_id=uuid.uuid4(),
        record_name="Record",
        status=status,
        chain_id=uuid.uuid4(),
        window_start=window_start,
    )


def test_every_model_restates_the_org_index():
    for model in MODELS:
        assert any(
            list(index.fields) == ["org", "-created_at"]
            for index in model._meta.indexes
        ), model.__name__


@pytest.mark.django_db
def test_one_skipped_row_per_rule_and_window(rule):
    window = timezone.now().replace(minute=0, second=0, microsecond=0)
    _run(rule, "skipped", window)
    with pytest.raises(IntegrityError), transaction.atomic():
        _run(rule, "skipped", window)
    _run(rule, "done", window)
    _run(rule, "done", window)
    assert AutomationRun.objects.filter(rule=rule).count() == 3


@pytest.mark.django_db
def test_one_rotation_row_per_action(rule):
    AutomationRotation.objects.create(org=rule.org, rule=rule, action_index=0)
    with pytest.raises(IntegrityError), transaction.atomic():
        AutomationRotation.objects.create(org=rule.org, rule=rule, action_index=0)
    AutomationRotation.objects.create(org=rule.org, rule=rule, action_index=1)


def test_every_org_table_is_listed_or_excluded():
    assert org_tables_not_covered() == []


@pytest.mark.postgres_only
def test_every_listed_table_has_its_policies():
    if connection.vendor != "postgresql":
        pytest.skip("RLS policies exist only on PostgreSQL")
    assert rls_policy_gaps() == []
