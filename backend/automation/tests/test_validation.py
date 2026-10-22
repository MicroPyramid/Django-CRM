"""Checking a rule's JSON against its org's catalogue, people and endpoints."""

from dataclasses import dataclass

import pytest

from automation import links
from automation.links import LinkSpec, register_link_hook
from automation.models import AutomationRule
from automation.objects import Adapter, FieldSpec
from automation.serializers import RuleSerializer
from automation.validation import validate_rule
from common import object_registry
from common.models import CustomFieldDefinition, Profile, User
from common.object_registry import register_hook
from conftest import rls_org
from opportunity.models import DealPipeline, DealStage
from webhooks.models import WebhookEndpoint

CREATED = {"event": "created", "field": None, "to": None}
UPDATED = {"event": "updated", "field": None, "to": None}


@pytest.fixture(autouse=True)
def restore_link_hooks():
    saved = list(links._HOOKS)
    yield
    links._HOOKS[:] = saved


class FakeLinkHook:
    def __init__(self, object_key, *specs):
        self.object_key, self.specs_offered = object_key, list(specs)

    def specs(self, org, object_key):
        return self.specs_offered if object_key == self.object_key else []

    def records(self, org, object_key, record, spec_id):
        return []


class SiteAdapter(Adapter):
    FIELDS = (
        FieldSpec("name", "Name", "text"),
        FieldSpec("owner_person", "Site owner", "person"),
    )


@dataclass(frozen=True)
class SiteEntry:
    """A hook entry with no assignees and a one-person field."""

    key: str = "obj:site"
    custom_field_target: str = "obj:site"
    label: str = "Site"

    def automation_adapter(self):
        return SiteAdapter(self)


@pytest.fixture
def site():
    saved = list(object_registry._HOOKS)
    register_hook(lambda org: (SiteEntry(),))
    yield
    object_registry._HOOKS[:] = saved


def _profile(org, email, *, active=True, user_active=True):
    user = User.objects.create_user(email=email, password="testpass123")
    if not user_active:
        User.objects.filter(pk=user.pk).update(is_active=False)
    return Profile.objects.create(user=user, org=org, is_active=active)


def _endpoint(org, **extra):
    return WebhookEndpoint.objects.create(
        org=org, url="https://hooks.example.com/in", events=["lead.created"], **extra
    )


@pytest.fixture
def person(org_a):
    return _profile(org_a, "person@test.com")


@pytest.fixture
def endpoint(org_a):
    return _endpoint(org_a)


# Valid on every object, so a test about something else needs no action of its own.
NOTIFY_ADMINS = {"type": "notify", "to": ["admins"], "people": [], "message": "Hi"}


def _rule(
    object_key="lead", trigger=CREATED, conditions=(), actions=(NOTIFY_ADMINS,), **extra
):
    return {
        "object_key": object_key,
        "trigger": trigger,
        "match": "all",
        "conditions": list(conditions) if isinstance(conditions, tuple) else conditions,
        "actions": list(actions) if isinstance(actions, tuple) else actions,
        **extra,
    }


def _cond(field, op, value=None):
    return {"field": field, "op": op, "value": value}


def _set(field, value, target="record"):
    return {"type": "set_field", "target": target, "field": field, "value": value}


def _task(**extra):
    action = {
        "type": "create_task",
        "title": "Call {name}",
        "due_in_days": 2,
        "priority": "High",
        "assign_to": "record",
        "person": None,
    }
    return {**action, **extra}


def _notify(**extra):
    return {
        "type": "notify",
        "to": ["record_assignees"],
        "people": [],
        "message": "New lead: {name}",
        **extra,
    }


def _assign(people, mode="replace"):
    return {"type": "assign", "people": [str(p.id) for p in people], "mode": mode}


def _webhook(endpoint_id):
    return {"type": "webhook", "endpoint": str(endpoint_id)}


def _errors_for(org, **rule):
    return validate_rule(org, _rule(**rule))


def _valid_action(kind, person, admin_profile, endpoint):
    return {
        "set_field": _set("status", "in process"),
        "assign": _assign([person]),
        "create_task": _task(assign_to="person", person=str(person.id)),
        "notify": _notify(people=[str(admin_profile.id)]),
        "webhook": _webhook(endpoint.id),
    }[kind]


@pytest.mark.parametrize(
    "kind", ["set_field", "assign", "create_task", "notify", "webhook"]
)
def test_a_valid_rule_of_each_action_type_passes(
    kind, org_a, person, admin_profile, endpoint
):
    rule = _rule(actions=[_valid_action(kind, person, admin_profile, endpoint)])
    assert validate_rule(org_a, rule) == {}
    serializer = RuleSerializer(data={"name": "Rule", **rule}, context={"org": org_a})
    assert serializer.is_valid(), serializer.errors


def test_a_valid_condition_of_each_type_passes(org_a, person, admin_profile):
    ids = [str(person.id), str(admin_profile.id)]
    conditions = [
        _cond("title", "contains", "renewal"),
        _cond("title", "neq", "Test"),
        _cond("opportunity_amount", "gt", 1000),
        _cond("opportunity_amount", "lt", "2500.50"),
        _cond("close_date", "lt", "2026-12-31"),
        _cond("status", "in", ["assigned", "converted"]),
        _cond("status", "eq", "recycled"),
        _cond("assigned_to", "includes", str(person.id)),
        _cond("assigned_to", "eq", ids),
        _cond("email", "empty"),
        _cond("phone", "not_empty", None),
        _cond("status", "was", "assigned"),
        _cond("status", "was_not", "closed"),
    ]
    assert _errors_for(org_a, trigger=UPDATED, conditions=conditions) == {}
    contact = [_cond("do_not_call", "true"), _cond("do_not_call", "false")]
    assert _errors_for(org_a, object_key="contact", conditions=contact) == {}


def test_the_deal_won_rule_passes(org_a, endpoint):
    register_link_hook(
        FakeLinkHook("deal", LinkSpec("in:property.deals", "Properties", "account"))
    )
    errors = _errors_for(
        org_a,
        object_key="deal",
        trigger={"event": "updated", "field": "stage_kind", "to": "won"},
        actions=[
            _task(title="Kick-off call: {name}", assign_to="record"),
            _notify(to=["parent_assignees", "linked:in:property.deals"]),
            _set("city", "Pune", target="in:property.deals"),
            _set("city", "Pune", target="parent"),
            _webhook(endpoint.id),
        ],
    )
    assert errors == {}


def test_each_limit_is_enforced(org_a):
    twenty = [_cond("title", "contains", "a")] * 20
    ten = [_notify()] * 10
    assert _errors_for(org_a, conditions=twenty, actions=ten) == {}
    assert _errors_for(org_a, actions=[_task(title="x" * 200)]) == {}
    assert _errors_for(org_a, actions=[_notify(message="x" * 500)]) == {}

    errors = _errors_for(org_a, conditions=twenty * 2, actions=ten * 2)
    assert set(errors) == {"conditions", "actions"}
    assert set(_errors_for(org_a, conditions=[*twenty, twenty[0]])) == {"conditions"}
    assert set(_errors_for(org_a, actions=[*ten, ten[0]])) == {"actions"}

    errors = _errors_for(org_a, actions=[_task(title="x" * 201)])
    assert set(errors) == {"actions[0].title"}
    errors = _errors_for(org_a, actions=[_notify(message="x" * 501)])
    assert set(errors) == {"actions[0].message"}
    errors = _errors_for(org_a, actions=[_task(title="   "), _notify(message="")])
    assert set(errors) == {"actions[0].title", "actions[1].message"}


def test_a_rule_needs_an_action(org_a):
    assert _errors_for(org_a) == {}
    assert set(_errors_for(org_a, actions=[])) == {"actions"}
    without = {"object_key": "lead", "trigger": CREATED}
    assert set(validate_rule(org_a, without)) == {"actions"}
    serializer = RuleSerializer(
        data={"name": "Rule", **without}, context={"org": org_a}
    )
    assert not serializer.is_valid()
    assert set(serializer.errors) == {"actions"}


def test_due_in_days_and_rotation_sizes_hold(org_a, person, admin_profile):
    assert _errors_for(org_a, actions=[_task(due_in_days=None)]) == {}
    assert _errors_for(org_a, actions=[_task(due_in_days=365)]) == {}
    for days in (-1, 366, 2.5, True, "2"):
        errors = _errors_for(org_a, actions=[_task(due_in_days=days)])
        assert set(errors) == {"actions[0].due_in_days"}, days

    others = [_profile(org_a, f"p{i}@test.com") for i in range(19)]
    assert _errors_for(org_a, actions=[_assign([person, *others], "rotate")]) == {}
    assert (
        _errors_for(org_a, actions=[_assign([person, admin_profile], "rotate")]) == {}
    )
    for people, mode in (
        ([person], "rotate"),
        ([person, admin_profile, *others], "rotate"),
        ([person, person], "rotate"),
        ([person, admin_profile], "replace"),
        ([], "replace"),
    ):
        errors = _errors_for(org_a, actions=[_assign(people, mode)])
        assert set(errors) == {"actions[0].people"}, (len(people), mode)
    errors = _errors_for(org_a, actions=[_assign([person], "shuffle")])
    assert set(errors) == {"actions[0].mode"}


def test_unknown_fields_operators_and_types_are_refused_with_their_path(org_a):
    errors = _errors_for(
        org_a,
        trigger={"event": "updated", "field": "nickname", "to": None},
        conditions=[
            _cond("nickname", "eq", "x"),
            _cond("status", "gt", "assigned"),
            _cond("opportunity_amount", "eq", "a lot"),
            _cond("close_date", "eq", "2026-02-30"),
            _cond("close_date", "eq", "20261022"),
            _cond("opportunity_amount", "gt", True),
            _cond("opportunity_amount", "gt", "NaN"),
            _cond("title", "contains", 5),
            _cond("title", "regex", ".*"),
        ],
        actions=[
            {"type": "delete_record"},
            _set("nickname", "x"),
            _set("opportunity_amount", "lots"),
            "not an action",
            {**_notify(), "cc": ["someone@example.com"]},
        ],
    )
    assert set(errors) == {
        "trigger.field",
        "conditions[0].field",
        "conditions[1].op",
        "conditions[2].value",
        "conditions[3].value",
        "conditions[4].value",
        "conditions[5].value",
        "conditions[6].value",
        "conditions[7].value",
        "conditions[8].op",
        "actions[0].type",
        "actions[1].field",
        "actions[2].value",
        "actions[3]",
        "actions[4]",
    }
    assert all(
        isinstance(messages, list) and all(isinstance(m, str) and m for m in messages)
        for messages in errors.values()
    )

    assert set(_errors_for(org_a, trigger={"event": "deleted"})) == {"trigger.event"}
    assert set(_errors_for(org_a, trigger="created")) == {"trigger"}
    assert set(_errors_for(org_a, trigger={**CREATED, "when": "now"})) == {"trigger"}
    assert set(_errors_for(org_a, conditions={"field": "title"})) == {"conditions"}
    assert set(_errors_for(org_a, actions="notify")) == {"actions"}
    assert set(_errors_for(org_a, match="most")) == {"match"}


@pytest.mark.parametrize("object_key", ["invoice", "obj:property", "nothing", 5, None])
def test_an_object_rules_cannot_automate_fails_alone(org_a, object_key):
    rule = _rule(
        object_key=object_key,
        trigger={"event": "never"},
        conditions=[_cond("nickname", "eq", 1)],
        actions=[{"type": "delete_record"}],
    )
    errors = validate_rule(org_a, rule)
    assert list(errors) == ["object_key"]
    assert len(errors["object_key"]) == 1


def test_a_choice_value_must_be_an_option(org_a, org_b):
    sales = DealPipeline.default_for(org_a)
    stage = DealStage.objects.filter(pipeline=sales).first()
    with rls_org(org_b):
        theirs = DealPipeline.objects.create(org=org_b, name="Theirs")
        elsewhere = DealStage.objects.create(
            org=org_b, pipeline=theirs, code="ELSEWHERE", label="Elsewhere"
        )
    CustomFieldDefinition.objects.create(
        org=org_a,
        target_model="Lead",
        key="region",
        label="Region",
        field_type="dropdown",
        options=[{"value": "n", "label": "North"}, {"value": "s", "label": "South"}],
    )

    good = _errors_for(
        org_a,
        trigger={"event": "updated", "field": "status", "to": "closed"},
        conditions=[
            _cond("status", "in", ["assigned", "closed"]),
            _cond("custom_fields.region", "eq", "n"),
        ],
        actions=[_set("status", "recycled"), _set("custom_fields.region", "s")],
    )
    assert good == {}
    bad = _errors_for(
        org_a,
        trigger={"event": "updated", "field": "status", "to": "Closed"},
        conditions=[
            _cond("status", "eq", "won"),
            _cond("status", "in", ["assigned", "won"]),
            _cond("status", "in", []),
            _cond("status", "in", "assigned"),
            _cond("custom_fields.region", "eq", "east"),
        ],
        actions=[_set("status", "won"), _set("custom_fields.region", 1)],
    )
    assert set(bad) == {
        "trigger.to",
        "conditions[0].value",
        "conditions[1].value",
        "conditions[2].value",
        "conditions[3].value",
        "conditions[4].value",
        "actions[0].value",
        "actions[1].value",
    }

    deal = {"object_key": "deal", "trigger": UPDATED}
    assert _errors_for(org_a, **deal, actions=[_set("stage", str(stage.pk))]) == {}
    foreign = _errors_for(org_a, **deal, actions=[_set("stage", str(elsewhere.pk))])
    assert set(foreign) == {"actions[0].value"}


def test_another_orgs_person_or_endpoint_is_refused(
    org_a, org_b, person, endpoint, profile_b
):
    with rls_org(org_b):
        their_endpoint = _endpoint(org_b)
    theirs = str(profile_b.id)

    errors = _errors_for(
        org_a,
        trigger={"event": "updated", "field": None, "to": None},
        conditions=[
            _cond("assigned_to", "includes", theirs),
            _cond("assigned_to", "eq", [str(person.id), theirs]),
        ],
        actions=[
            _assign([profile_b]),
            _assign([person, profile_b], "rotate"),
            _task(assign_to="person", person=theirs),
            _notify(people=[theirs]),
            _set("assigned_to", [theirs]),
            _webhook(their_endpoint.id),
        ],
    )
    assert set(errors) == {
        "conditions[0].value",
        "conditions[1].value",
        "actions[0].people",
        "actions[1].people",
        "actions[2].person",
        "actions[3].people",
        "actions[4].value",
        "actions[5].endpoint",
    }
    mine = _errors_for(
        org_a,
        actions=[
            _assign([person]),
            _set("assigned_to", [str(person.id)]),
            _webhook(endpoint.id),
        ],
    )
    assert mine == {}


def test_ids_must_be_canonical(org_a, person, endpoint):
    pk, hook = str(person.id), str(endpoint.id)
    assert (
        _errors_for(
            org_a,
            conditions=[_cond("assigned_to", "includes", pk)],
            actions=[
                {"type": "assign", "people": [pk], "mode": "replace"},
                _task(assign_to="person", person=pk),
                _webhook(hook),
            ],
        )
        == {}
    )
    for form in (str.upper, lambda v: v.replace("-", ""), "{{{}}}".format):
        errors = _errors_for(
            org_a,
            conditions=[_cond("assigned_to", "includes", form(pk))],
            actions=[
                {"type": "assign", "people": [form(pk)], "mode": "replace"},
                _task(assign_to="person", person=form(pk)),
                _webhook(form(hook)),
            ],
        )
        assert set(errors) == {
            "conditions[0].value",
            "actions[0].people",
            "actions[1].person",
            "actions[2].endpoint",
        }, form(pk)


def test_malformed_ids_are_refused_not_raised(org_a):
    errors = _errors_for(
        org_a,
        conditions=[_cond("assigned_to", "includes", "not-an-id")],
        actions=[
            {"type": "assign", "people": ["not-an-id"], "mode": "replace"},
            {"type": "assign", "people": [{"id": "x"}], "mode": "replace"},
            _task(assign_to="person", person=12),
            _webhook("not-an-id"),
            {"type": "webhook", "endpoint": ["x"]},
        ],
    )
    assert set(errors) == {
        "conditions[0].value",
        "actions[0].people",
        "actions[1].people",
        "actions[2].person",
        "actions[3].endpoint",
        "actions[4].endpoint",
    }


def test_an_inactive_person_is_refused(org_a, person):
    gone = _profile(org_a, "gone@test.com", active=False)
    locked = _profile(org_a, "locked@test.com", user_active=False)
    for inactive in (gone, locked):
        pk = str(inactive.id)
        errors = _errors_for(
            org_a,
            conditions=[_cond("assigned_to", "includes", pk)],
            actions=[
                _assign([inactive]),
                _task(assign_to="person", person=pk),
                _notify(people=[str(person.id), pk]),
            ],
        )
        assert set(errors) == {
            "conditions[0].value",
            "actions[0].people",
            "actions[1].person",
            "actions[2].people",
        }
    assert _errors_for(org_a, actions=[_assign([person])]) == {}


def test_a_slack_endpoint_is_refused(org_a, endpoint):
    slack = _endpoint(org_a, format="slack")
    off = _endpoint(org_a, is_active=False)
    assert _errors_for(org_a, actions=[_webhook(endpoint.id)]) == {}
    for refused in (slack, off):
        errors = _errors_for(org_a, actions=[_webhook(refused.id)])
        assert set(errors) == {"actions[0].endpoint"}


def test_a_read_only_field_cannot_be_set(org_a):
    deal = _errors_for(
        org_a, object_key="deal", trigger=UPDATED, actions=[_set("stage_kind", "won")]
    )
    assert set(deal) == {"actions[0].field"}
    lead = _errors_for(
        org_a, actions=[_set("status", "converted"), _set("stage", None)]
    )
    assert set(lead) == {"actions[0].value", "actions[1].field"}
    ticket = _errors_for(
        org_a, object_key="ticket", actions=[_set("status", "Duplicate")]
    )
    assert set(ticket) == {"actions[0].value"}

    readable = _errors_for(
        org_a,
        trigger={"event": "updated", "field": "status", "to": "converted"},
        conditions=[_cond("status", "neq", "converted")],
        actions=[_set("status", "closed"), _set("email", None)],
    )
    assert readable == {}
    assert _errors_for(org_a, actions=[_set("status", None)]) == {}
    errors = _errors_for(
        org_a, actions=[{"type": "set_field", "target": "record", "field": "email"}]
    )
    assert set(errors) == {"actions[0].value"}


def test_people_fields_cannot_be_trigger_fields(org_a, person):
    errors = _errors_for(
        org_a, trigger={"event": "updated", "field": "assigned_to", "to": None}
    )
    assert set(errors) == {"trigger.field"}
    to_person = {"event": "updated", "field": "assigned_to", "to": [str(person.id)]}
    assert set(_errors_for(org_a, trigger=to_person)) == {"trigger.field"}
    on_status = {"event": "updated", "field": "status", "to": None}
    assert _errors_for(org_a, trigger=on_status) == {}
    conditions = [_cond("assigned_to", "not_empty")]
    assert _errors_for(org_a, trigger=on_status, conditions=conditions) == {}


def test_was_needs_an_update_trigger(org_a, person):
    was = [_cond("status", "was", "assigned")]
    assert set(_errors_for(org_a, trigger=CREATED, conditions=was)) == {
        "conditions[0].op"
    }
    assert _errors_for(org_a, trigger=UPDATED, conditions=was) == {}
    people_was = [_cond("assigned_to", "was", [str(person.id)])]
    assert set(_errors_for(org_a, trigger=UPDATED, conditions=people_was)) == {
        "conditions[0].op"
    }


def test_trigger_shapes(org_a):
    on = {"event": "updated", "field": "opportunity_amount", "to": 5000}
    assert _errors_for(org_a, trigger=on) == {}
    for trigger, path in (
        ({"event": "created", "field": "status", "to": None}, "trigger.field"),
        ({"event": "created", "field": None, "to": "closed"}, "trigger.to"),
        ({"event": "updated", "field": None, "to": "closed"}, "trigger.to"),
        ({"event": "updated", "field": "opportunity_amount", "to": "x"}, "trigger.to"),
        ({"event": "updated", "field": "title", "to": ""}, "trigger.to"),
        ({"event": "updated", "field": ["title"], "to": None}, "trigger.field"),
    ):
        assert set(_errors_for(org_a, trigger=trigger)) == {path}, trigger


def test_no_value_operators_take_no_value(org_a):
    conditions = [
        _cond("email", "empty", "x"),
        _cond("email", "eq"),
        _cond("email", "eq", ""),
    ]
    contact = [_cond("do_not_call", "true", True)]
    assert set(_errors_for(org_a, conditions=conditions)) == {
        "conditions[0].value",
        "conditions[1].value",
        "conditions[2].value",
    }
    errors = _errors_for(org_a, object_key="contact", conditions=contact)
    assert set(errors) == {"conditions[0].value"}
    assert set(_errors_for(org_a, conditions=["status"])) == {"conditions[0]"}
    extra = [{**_cond("email", "empty"), "note": "x"}]
    assert set(_errors_for(org_a, conditions=extra)) == {"conditions[0]"}


def test_set_field_targets(org_a):
    spec = LinkSpec("in:property.deals", "Properties", "account")
    unreachable = LinkSpec("in:boat.deals", "Boats", "obj:boat")
    register_link_hook(FakeLinkHook("deal", spec, unreachable))
    deal = {"object_key": "deal", "trigger": UPDATED}

    assert _errors_for(org_a, **deal, actions=[_set("city", "Pune", "parent")]) == {}
    assert _errors_for(org_a, **deal, actions=[_set("city", "Pune", spec.id)]) == {}
    errors = _errors_for(
        org_a,
        **deal,
        actions=[
            _set("amount", 5, "parent"),
            _set("amount", 5, spec.id),
            _set("city", "Pune", unreachable.id),
            _set("city", "Pune", "in:nothing.deals"),
            _set("city", "Pune", None),
        ],
    )
    assert set(errors) == {
        "actions[0].field",
        "actions[1].field",
        "actions[2].target",
        "actions[3].target",
        "actions[4].target",
    }
    for key in ("lead", "contact", "task"):
        errors = _errors_for(
            org_a, object_key=key, actions=[_set("title", "x", "parent")]
        )
        assert set(errors) == {"actions[0].target"}, key
    errors = _errors_for(org_a, actions=[_set("city", "Pune", spec.id)])
    assert set(errors) == {"actions[0].target"}


def test_create_task_assignees(org_a, person):
    for assign_to in ("record", "parent", "owner"):
        assert _errors_for(org_a, actions=[_task(assign_to=assign_to)]) == {}
        assert (
            _errors_for(
                org_a,
                actions=[
                    {
                        k: v
                        for k, v in _task(assign_to=assign_to).items()
                        if k != "person"
                    }
                ],
            )
            == {}
        )
        errors = _errors_for(
            org_a, actions=[_task(assign_to=assign_to, person=str(person.id))]
        )
        assert set(errors) == {"actions[0].person"}, assign_to
    assert set(_errors_for(org_a, actions=[_task(assign_to="person")])) == {
        "actions[0].person"
    }
    errors = _errors_for(org_a, actions=[_task(assign_to="team", priority="Urgent")])
    assert set(errors) == {"actions[0].assign_to", "actions[0].priority"}


def test_notify_recipients(org_a, person):
    register_link_hook(
        FakeLinkHook("lead", LinkSpec("in:property.leads", "Properties", "account"))
    )
    every = ["record_assignees", "record_creator", "parent_assignees", "admins"]
    assert _errors_for(org_a, actions=[_notify(to=every)]) == {}
    assert _errors_for(org_a, actions=[_notify(to=["linked:in:property.leads"])]) == {}
    only_people = _notify(to=[], people=[str(person.id)])
    assert _errors_for(org_a, actions=[only_people]) == {}

    errors = _errors_for(
        org_a,
        actions=[
            _notify(to=[], people=[]),
            _notify(to=["everyone@example.com"]),
            _notify(to=["linked:in:nothing.leads"]),
            _notify(to="admins"),
            _notify(people=str(person.id)),
        ],
    )
    assert set(errors) == {
        "actions[0].to",
        "actions[1].to",
        "actions[2].to",
        "actions[3].to",
        "actions[4].people",
    }


def test_assign_needs_an_assignee_field(org_a, person, site):
    assert _errors_for(org_a, object_key="task", actions=[_assign([person])]) == {}
    errors = _errors_for(org_a, object_key="obj:site", actions=[_assign([person])])
    assert set(errors) == {"actions[0].type"}


def test_a_person_field_takes_one_id(org_a, person, site):
    pk = str(person.id)
    on_owner = {"event": "updated", "field": "owner_person", "to": pk}
    good = _errors_for(
        org_a,
        object_key="obj:site",
        trigger=on_owner,
        conditions=[
            _cond("owner_person", "eq", pk),
            _cond("owner_person", "excludes", pk),
            _cond("owner_person", "was", pk),
        ],
        actions=[_set("owner_person", pk), _set("owner_person", None)],
    )
    assert good == {}
    bad = _errors_for(
        org_a,
        object_key="obj:site",
        trigger={**on_owner, "to": [pk]},
        conditions=[_cond("owner_person", "eq", [pk])],
        actions=[_set("owner_person", [pk])],
    )
    assert set(bad) == {"trigger.to", "conditions[0].value", "actions[0].value"}


def test_an_invalid_rule_raises_its_paths_from_the_serializer(org_a):
    data = {"name": "Rule", **_rule(conditions=[_cond("nickname", "eq", "x")])}
    serializer = RuleSerializer(data=data, context={"org": org_a})
    assert not serializer.is_valid()
    assert set(serializer.errors) == {"conditions[0].field"}
    assert all(isinstance(m, str) for m in serializer.errors["conditions[0].field"])

    for name in ("", "   ", "x" * 121):
        serializer = RuleSerializer(data={**data, "name": name}, context={"org": org_a})
        assert not serializer.is_valid()
        assert "name" in serializer.errors


def test_a_rule_that_broke_can_be_renamed_or_switched_off(org_a, person):
    rule = AutomationRule.objects.create(
        org=org_a,
        name="Assign",
        object_key="lead",
        trigger=CREATED,
        actions=[_assign([person])],
        is_active=True,
    )
    Profile.objects.filter(pk=person.pk).update(is_active=False)

    def patch(data):
        return RuleSerializer(rule, data=data, partial=True, context={"org": org_a})

    off = patch({"is_active": False})
    assert off.is_valid(), off.errors
    off.save()
    rule.refresh_from_db()
    assert rule.is_active is False
    renamed = patch({"name": "Assign (old)"})
    assert renamed.is_valid(), renamed.errors
    on = patch({"is_active": True})
    assert not on.is_valid()
    assert set(on.errors) == {"actions[0].people"}
    edited = patch({"match": "any"})
    assert not edited.is_valid()
    assert set(edited.errors) == {"actions[0].people"}


def test_a_partial_update_validates_the_merged_rule(org_a):
    rule = AutomationRule.objects.create(
        org=org_a,
        name="Deal rule",
        object_key="deal",
        trigger=UPDATED,
        actions=[NOTIFY_ADMINS],
    )
    ok = RuleSerializer(
        rule,
        data={"conditions": [_cond("amount", "gt", 10)]},
        partial=True,
        context={"org": org_a},
    )
    assert ok.is_valid(), ok.errors
    refused = RuleSerializer(
        rule,
        data={"conditions": [_cond("title", "contains", "x")]},
        partial=True,
        context={"org": org_a},
    )
    assert not refused.is_valid()
    assert set(refused.errors) == {"conditions[0].field"}
    renamed = RuleSerializer(
        rule, data={"name": "Renamed"}, partial=True, context={"org": org_a}
    )
    assert renamed.is_valid(), renamed.errors


def test_server_owned_input_is_ignored(org_a, org_b, admin_profile, person):
    forged = {
        "id": "00000000-0000-0000-0000-000000000001",
        "org": str(org_b.id),
        "owner": str(person.id),
        "paused_reason": "forged",
        "switched_on_at": "2020-01-01T00:00:00Z",
        "last_failure_notice_at": "2020-01-01T00:00:00Z",
        "created_at": "2020-01-01T00:00:00Z",
    }
    serializer = RuleSerializer(
        data={"name": "Rule", **_rule(), **forged}, context={"org": org_a}
    )
    assert serializer.is_valid(), serializer.errors
    rule = serializer.save()
    rule.refresh_from_db()
    assert rule.org_id == org_a.id
    assert str(rule.id) != forged["id"]
    assert rule.owner is None
    assert rule.paused_reason == ""
    assert rule.switched_on_at is None
    assert rule.last_failure_notice_at is None

    AutomationRule.objects.filter(pk=rule.pk).update(owner=admin_profile)
    rule.refresh_from_db()
    serializer = RuleSerializer(rule, data=forged, partial=True, context={"org": org_a})
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    rule.refresh_from_db()
    assert rule.org_id == org_a.id
    assert rule.owner_id == admin_profile.id
    assert rule.paused_reason == ""
    assert rule.switched_on_at is None
    assert rule.last_failure_notice_at is None


def test_the_serializer_shows_the_owner_and_read_only_columns(org_a, admin_profile):
    rule = AutomationRule.objects.create(
        org=org_a,
        name="Rule",
        object_key="lead",
        trigger=CREATED,
        owner=admin_profile,
        paused_reason="owner_left",
    )
    data = RuleSerializer(rule, context={"org": org_a}).data
    assert set(data) == {
        "id",
        "name",
        "object_key",
        "trigger",
        "match",
        "conditions",
        "actions",
        "is_active",
        "position",
        "owner",
        "switched_on_at",
        "paused_reason",
        "created_at",
        "updated_at",
    }
    assert data["owner"] == {
        "id": str(admin_profile.id),
        "name": admin_profile.user.name,
    }
    assert data["paused_reason"] == "owner_left"
    rule.owner = None
    assert RuleSerializer(rule, context={"org": org_a}).data["owner"] is None
