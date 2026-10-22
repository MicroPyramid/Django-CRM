"""The two neutral hooks another edition fills: linked records and the plan."""

import pytest

from automation import links, plan
from automation.links import LinkSpec, link_specs, linked_records, register_link_hook
from automation.models import AutomationRule
from automation.plan import Runnable, may_switch_on, register_plan_hook, runnable
from common.tests.object_records import make_record


@pytest.fixture(autouse=True)
def restore_hooks():
    saved_links, saved_plan = list(links._HOOKS), list(plan._HOOKS)
    yield
    links._HOOKS[:] = saved_links
    plan._HOOKS[:] = saved_plan


class FakeLinkHook:
    def __init__(self, object_key, spec, records):
        self.object_key, self.spec, self._records = object_key, spec, records
        self.asked = []

    def specs(self, org, object_key):
        return [self.spec] if object_key == self.object_key else []

    def records(self, org, object_key, record, spec_id):
        self.asked.append(spec_id)
        return self._records


class FakePlanHook:
    def __init__(self, refusal, rule_ids=frozenset()):
        self.refusal, self.rule_ids = refusal, rule_ids

    def may_switch_on(self, org, rule):
        return self.refusal

    def runnable(self, org, rules):
        return Runnable(self.rule_ids, {"x": "Over"}, "summary")


def _rule(org, name):
    return AutomationRule.objects.create(org=org, name=name, object_key="lead")


def test_no_link_hook_means_no_links(org_a):
    deal = make_record("deal", org_a)
    assert link_specs(org_a, "deal") == []
    assert linked_records(org_a, "deal", deal, "in:property.deals") == []


def test_a_link_hook_answers_for_its_specs_only(org_a):
    deal = make_record("deal", org_a)
    one, two = make_record("lead", org_a), make_record("lead", org_a)
    first_spec = LinkSpec("in:a.deals", "As", "obj:a")
    second_spec = LinkSpec("in:b.deals", "Bs", "obj:b")
    first = FakeLinkHook("deal", first_spec, [one])
    second = FakeLinkHook("deal", second_spec, [two])
    register_link_hook(first)
    register_link_hook(second)
    register_link_hook(first)

    assert link_specs(org_a, "deal") == [first_spec, second_spec]
    assert link_specs(org_a, "ticket") == []
    assert linked_records(org_a, "deal", deal, "in:b.deals") == [two]
    assert first.asked == [] and second.asked == ["in:b.deals"]
    assert linked_records(org_a, "deal", deal, "in:a.deals") == [one]
    assert linked_records(org_a, "deal", deal, "in:nobody.deals") == []
    assert linked_records(org_a, "ticket", deal, "in:a.deals") == []


def test_plan_defaults_allow_everything(org_a):
    rules = [_rule(org_a, "One"), _rule(org_a, "Two")]
    assert may_switch_on(org_a, rules[0]) is None
    assert runnable(org_a, rules) == Runnable(frozenset(r.id for r in rules), {}, None)
    assert runnable(org_a, []) == Runnable(frozenset(), {}, None)


def test_a_second_plan_hook_is_refused(org_a):
    rule = _rule(org_a, "One")
    first = FakePlanHook("No more rules")
    register_plan_hook(first)
    with pytest.raises(RuntimeError):
        register_plan_hook(FakePlanHook(None))
    assert may_switch_on(org_a, rule) == "No more rules"
    assert runnable(org_a, [rule]) == Runnable(frozenset(), {"x": "Over"}, "summary")


def test_registering_the_same_plan_hook_twice_is_fine(org_a):
    rule = _rule(org_a, "One")
    hook = FakePlanHook(None, frozenset({rule.id}))
    register_plan_hook(hook)
    register_plan_hook(hook)
    assert plan._HOOKS == [hook]
    assert may_switch_on(org_a, rule) is None
    assert runnable(org_a, [rule]).rule_ids == frozenset({rule.id})
