"""The adapters: what each built-in object offers rules, and how a rule reads,
snapshots and writes a record through its module's own update service."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.db import connection
from django.db.models import QuerySet

from accounts.models import Account
from accounts.serializer import AccountCreateSerializer
from automation.adapters.deals import NOT_A_STAGE
from automation.objects import (
    FIELD_TYPES,
    Adapter,
    Choice,
    FieldSpec,
    adapter_for,
    automatable,
)
from cases.serializer import CaseCreateSerializer
from cases.workflow import DUPLICATE_BY_MERGE_ONLY
from common import object_registry
from common.models import CustomFieldDefinition, Profile, User
from common.object_registry import ObjectEntry, object_for_key, register_hook
from common.tests.object_records import make_record
from conftest import rls_org
from contacts.serializer import CreateContactSerializer
from leads.models import Lead, LeadPipeline, LeadStage
from leads.serializer import LeadCreateSerializer
from leads.updates import CONVERSION_REFUSED
from opportunity.models import DealPipeline, DealStage, Opportunity
from opportunity.serializer import OpportunityCreateSerializer
from tasks.serializer import TaskCreateSerializer
from webhooks import events

TABLE = {
    "lead": {
        "title": "text",
        "first_name": "text",
        "last_name": "text",
        "email": "text",
        "phone": "text",
        "company_name": "text",
        "job_title": "text",
        "website": "text",
        "city": "text",
        "country": "choice",
        "status": "choice",
        "source": "choice",
        "industry": "choice",
        "rating": "choice",
        "stage": "choice",
        "opportunity_amount": "number",
        "probability": "number",
        "close_date": "date",
        "next_follow_up": "date",
        "assigned_to": "people",
    },
    "contact": {
        "first_name": "text",
        "last_name": "text",
        "email": "text",
        "phone": "text",
        "organization": "text",
        "title": "text",
        "department": "text",
        "city": "text",
        "country": "choice",
        "do_not_call": "boolean",
        "assigned_to": "people",
    },
    "account": {
        "name": "text",
        "email": "text",
        "phone": "text",
        "website": "text",
        "city": "text",
        "country": "choice",
        "industry": "choice",
        "number_of_employees": "number",
        "annual_revenue": "number",
        "assigned_to": "people",
    },
    "deal": {
        "name": "text",
        "stage": "choice",
        "stage_kind": "choice",
        "opportunity_type": "choice",
        "lead_source": "choice",
        "amount": "number",
        "probability": "number",
        "closed_on": "date",
        "assigned_to": "people",
    },
    "ticket": {
        "name": "text",
        "status": "choice",
        "priority": "choice",
        "case_type": "choice",
        "closed_on": "date",
        "assigned_to": "people",
    },
    "task": {
        "title": "text",
        "status": "choice",
        "priority": "choice",
        "due_date": "date",
        "assigned_to": "people",
    },
}
KEYS = list(TABLE)
READ_ONLY = {"lead": {"stage"}, "deal": {"stage_kind"}}

SERVICES = {
    "lead": "automation.adapters.leads.update_lead",
    "contact": "automation.adapters.contacts.update_contact",
    "account": "automation.adapters.accounts.update_account",
    "deal": "automation.adapters.deals.update_deal",
    "ticket": "automation.adapters.tickets.update_case",
    "task": "automation.adapters.tasks.update_task",
}
# The first text field of each object, which every test write changes.
TEXT_FIELD = {
    key: next(k for k, t in TABLE[key].items() if t == "text") for key in KEYS
}

SERVER_OWNED = {
    "org",
    "id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "is_active",
    "is_sample",
}

ROUTES = {
    "lead": "/leads/{}",
    "contact": "/contacts/{}",
    "account": "/accounts/{}",
    "deal": "/pipeline/{}",
    "ticket": "/tickets/{}",
    "task": "/tasks/{}",
}

WEBHOOK_DATA = {
    "lead": events.lead_data,
    "contact": events.contact_data,
    "account": events.account_data,
    "deal": events.deal_data,
    "ticket": events.ticket_data,
    "task": events.task_data,
}

# One value of each type the object has, so the shape checks are not vacuous.
POPULATE = {
    "lead": {
        "status": "assigned",
        "country": "IN",
        "opportunity_amount": Decimal("10.50"),
        "probability": 30,
        "close_date": date(2026, 1, 2),
    },
    "contact": {"country": "IN", "do_not_call": True},
    "account": {
        "industry": "FINANCE",
        "number_of_employees": 12,
        "annual_revenue": Decimal("5000.00"),
    },
    "deal": {
        "lead_source": "CALL",
        "amount": Decimal("100.00"),
        "probability": 40,
        "closed_on": date(2026, 3, 4),
    },
    "ticket": {"priority": "High", "closed_on": date(2026, 5, 6)},
    "task": {"priority": "High", "due_date": date(2026, 7, 8)},
}

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _adapter(org, key):
    adapter = adapter_for(org, key)
    assert adapter is not None
    return adapter


def _profile(org, email, *, active=True, role="USER"):
    user = User.objects.create_user(email=email, password="testpass123")
    return Profile.objects.create(user=user, org=org, role=role, is_active=active)


def _set(record, **values):
    """Write columns without `save()`, which some models use to settle state."""
    type(record).objects.filter(pk=record.pk).update(**values)
    record.refresh_from_db()
    return record


def _custom(org, target, key, field_type, **extra):
    return CustomFieldDefinition.objects.create(
        org=org,
        target_model=target,
        key=key,
        label=key.replace("_", " ").title(),
        field_type=field_type,
        **extra,
    )


@pytest.fixture
def restore_registry_hooks():
    saved = list(object_registry._HOOKS)
    yield
    object_registry._HOOKS[:] = saved


# The catalogue


@pytest.mark.parametrize("key", KEYS)
def test_fields_match_the_table(key, org_a):
    fields = _adapter(org_a, key).fields(org_a)
    assert [f.key for f in fields] == list(TABLE[key])
    assert {f.key: f.type for f in fields} == TABLE[key]
    assert {f.key for f in fields if not f.settable} == READ_ONLY.get(key, set())
    assert all(f.type in FIELD_TYPES for f in fields)
    assert all(f.label for f in fields)
    assert all(f.choices for f in fields if f.type == "choice" and f.key != "stage")


@pytest.mark.parametrize("key", KEYS)
def test_no_server_owned_field_is_offered(key, org_a):
    keys = {f.key for f in _adapter(org_a, key).fields(org_a)}
    assert not keys & SERVER_OWNED
    assert not [k for k in keys if "token" in k]


def _edit_serializer(key, record, profile):
    request = SimpleNamespace(profile=profile)
    serializer_class = {
        "lead": LeadCreateSerializer,
        "contact": CreateContactSerializer,
        "account": AccountCreateSerializer,
        "deal": OpportunityCreateSerializer,
        "ticket": CaseCreateSerializer,
        "task": TaskCreateSerializer,
    }[key]
    return serializer_class(instance=record, data={}, request_obj=request, partial=True)


@pytest.mark.parametrize("key", KEYS)
def test_every_settable_field_is_one_the_edit_form_writes(key, org_a, admin_profile):
    record = make_record(key, org_a)
    writable = {
        name
        for name, field in _edit_serializer(key, record, admin_profile).fields.items()
        if not field.read_only
    }
    for spec in _adapter(org_a, key).fields(org_a):
        if spec.type == "people":
            continue
        assert (spec.key in writable) == spec.settable, spec.key


@pytest.mark.parametrize("key", ["lead", "contact", "account"])
def test_country_is_a_choice_of_the_stored_codes(key, org_a):
    country = next(f for f in _adapter(org_a, key).fields(org_a) if f.key == "country")
    assert country.settable
    assert Choice("IN", "India") in country.choices
    assert Choice("GB", "United Kingdom") in country.choices
    assert all(len(c.value) <= 3 for c in country.choices)


@pytest.mark.parametrize("key", KEYS)
def test_custom_fields_are_appended(key, org_a, org_b):
    target = object_for_key(org_a, key).custom_field_target
    _custom(org_a, target, "note", "text", display_order=1)
    _custom(org_a, target, "long_note", "textarea", display_order=2)
    _custom(org_a, target, "score", "number", display_order=3)
    _custom(org_a, target, "seen_on", "date", display_order=4)
    _custom(
        org_a,
        target,
        "region",
        "dropdown",
        display_order=5,
        options=[{"value": "n", "label": "North"}, {"value": "s", "label": "South"}],
    )
    _custom(org_a, target, "vip", "checkbox", display_order=6)
    _custom(org_a, target, "retired", "text", is_active=False)
    other_target = "Task" if target != "Task" else "Lead"
    _custom(org_a, other_target, "elsewhere", "text")
    with rls_org(org_b):
        _custom(org_b, target, "theirs", "text")

    fields = _adapter(org_a, key).fields(org_a)
    assert [f.key for f in fields[: len(TABLE[key])]] == list(TABLE[key])
    custom = fields[len(TABLE[key]) :]
    assert [(f.key, f.type, f.settable) for f in custom] == [
        ("custom_fields.note", "text", True),
        ("custom_fields.long_note", "text", True),
        ("custom_fields.score", "number", True),
        ("custom_fields.seen_on", "date", True),
        ("custom_fields.region", "choice", True),
        ("custom_fields.vip", "boolean", True),
    ]
    assert custom[0].label == "Note"
    assert custom[4].choices == (Choice("n", "North"), Choice("s", "South"))


# Reading


@pytest.mark.parametrize("key", KEYS)
def test_read_and_snapshot_shapes(key, org_a, admin_profile):
    target = object_for_key(org_a, key).custom_field_target
    _custom(org_a, target, "score", "number")
    _custom(org_a, target, "seen_on", "date")
    _custom(org_a, target, "vip", "checkbox")
    _custom(org_a, target, "note", "text")
    record = _set(
        make_record(key, org_a),
        custom_fields={"score": 5.0, "seen_on": "2026-09-10", "vip": True, "note": ""},
        **POPULATE[key],
    )
    active = admin_profile
    inactive = _profile(org_a, "gone@test.com", active=False)
    record.assigned_to.add(active, inactive)
    adapter = _adapter(org_a, key)
    fields = adapter.fields(org_a)

    for spec in fields:
        value = adapter.read(record, spec.key)
        if spec.type == "people":
            assert value == [str(active.pk)]
        elif value is None:
            continue
        elif spec.type in ("text", "choice"):
            assert isinstance(value, str), spec.key
        elif spec.type == "number":
            assert isinstance(value, (Decimal, int)), spec.key
            assert not isinstance(value, bool), spec.key
        elif spec.type == "date":
            assert ISO_DATE.match(value), spec.key
        elif spec.type == "boolean":
            assert isinstance(value, bool), spec.key

    for field, stored in POPULATE[key].items():
        expected = stored.isoformat() if isinstance(stored, date) else stored
        assert adapter.read(record, field) == expected, field
    assert adapter.read(record, "custom_fields.score") == Decimal("5")
    assert adapter.read(record, "custom_fields.seen_on") == "2026-09-10"
    assert adapter.read(record, "custom_fields.vip") is True
    assert adapter.read(record, "custom_fields.note") is None
    assert adapter.read(record, "custom_fields.never_set") is None

    snapshot = adapter.snapshot(record)
    assert set(snapshot) == {f.key for f in fields if f.type != "people"}
    assert snapshot == {k: adapter.read(record, k) for k in snapshot}


def test_read_resolves_through_the_catalogue(org_a):
    class Dynamic(Adapter):
        def own_fields(self, org):
            return [
                FieldSpec("title", "Title", "text"),
                FieldSpec("assigned_to", "Assigned to", "people"),
            ]

    adapter = Dynamic(object_for_key(org_a, "lead"))
    lead = make_record("lead", org_a)
    assert adapter.read(lead, "title") == "Rec"
    assert adapter.read(lead, "assigned_to") == []
    assert set(adapter.snapshot(lead)) == {"title"}
    with pytest.raises(KeyError):
        adapter.read(lead, "email")


@pytest.mark.parametrize("key", KEYS)
def test_reads_after_the_first_cost_no_query(key, org_a, django_assert_num_queries):
    record = make_record(key, org_a)
    adapter = _adapter(org_a, key)
    adapter.read(record, TEXT_FIELD[key])
    with django_assert_num_queries(0):
        adapter.read(record, TEXT_FIELD[key])
        adapter.read(record, "custom_fields.anything")


@pytest.mark.parametrize("key", KEYS)
def test_people_reads_active_members_of_the_records_org(key, org_a, org_b):
    record = make_record(key, org_a)
    ids = sorted(str(_profile(org_a, f"p{n}@test.com").pk) for n in range(3))
    record.assigned_to.add(*Profile.objects.filter(pk__in=ids))
    with rls_org(org_b):
        stranger = _profile(org_b, "stranger@test.com")
    record.assigned_to.add(stranger)
    assert _adapter(org_a, key).read(record, "assigned_to") == ids


@pytest.mark.parametrize("key", KEYS)
def test_load_finds_only_the_orgs_record(key, org_a, org_b):
    mine = make_record(key, org_a)
    with rls_org(org_b):
        theirs = make_record(key, org_b)
    adapter = _adapter(org_a, key)
    assert adapter.load(org_a, mine.pk) == mine
    assert adapter.load(org_a, str(mine.pk)) == mine
    assert adapter.load(org_a, theirs.pk) is None
    assert adapter.load(org_a, "not-an-id") is None


@pytest.mark.parametrize("key", KEYS)
def test_path_is_the_web_detail_route(key, org_a):
    record = make_record(key, org_a)
    assert _adapter(org_a, key).path(record) == ROUTES[key].format(record.pk)


@pytest.mark.parametrize("key", KEYS)
def test_webhook_data_is_the_modules_payload(key, org_a):
    record = make_record(key, org_a)
    assert _adapter(org_a, key).webhook_data(record) == WEBHOOK_DATA[key](record)


def test_names(org_a):
    names = {key: _adapter(org_a, key).name(make_record(key, org_a)) for key in KEYS}
    assert names["contact"] == "Rec Person"
    assert names["account"].startswith("Rec ")
    assert {names[k] for k in ("lead", "deal", "ticket", "task")} == {"Rec"}
    lead = _adapter(org_a, "lead")
    assert lead.name(Lead(first_name="Ada", last_name="Lovelace", org=org_a)) == (
        "Ada Lovelace"
    )
    assert lead.name(Lead(email="ada@example.com", org=org_a)) == "ada@example.com"
    assert lead.name(Lead(org=org_a)) == "Untitled lead"


@pytest.mark.parametrize("key", KEYS)
def test_people_are_the_active_assignees_or_the_creator(
    key, org_a, regular_user, user_profile, admin_profile
):
    record = make_record(key, org_a, regular_user)
    gone = _profile(org_a, "gone@test.com", active=False)
    record.assigned_to.add(admin_profile, gone)
    adapter = _adapter(org_a, key)
    assert adapter.people(record, "assignees") == [admin_profile]
    assert adapter.people(record, "creator") == [user_profile]
    Profile.objects.filter(pk=user_profile.pk).update(is_active=False)
    assert adapter.people(record, "creator") == []
    assert adapter.people(make_record(key, org_a), "creator") == []
    with pytest.raises(ValueError):
        adapter.people(record, "watchers")


# Parents and the tasks a rule creates


def test_a_deal_and_a_ticket_have_their_account_as_parent(org_a, org_b):
    account = Account.objects.create(name="Parent", org=org_a)
    with rls_org(org_b):
        foreign = Account.objects.create(name="Foreign", org=org_b)
    for key in ("deal", "ticket"):
        adapter = _adapter(org_a, key)
        assert type(adapter).parent_key == "account"
        record = make_record(key, org_a)
        assert adapter.parent(record) is None
        assert adapter.parent_label(record) == "account"
        _set(record, account=account)
        assert adapter.parent(record) == ("account", account)
        assert adapter.parent_label(record) == "account"
        # An account outside the record's org is never its parent.
        _set(record, account=foreign)
        assert adapter.parent(record) is None


@pytest.mark.parametrize(
    ("key", "column", "parent_key", "label"),
    [
        ("deal", "account", "account", "account"),
        ("ticket", "account", "account", "account"),
        ("task", "lead", "lead", "parent"),
    ],
)
def test_a_parent_is_found_without_following_the_relation(
    key, column, parent_key, label, org_a, org_b
):
    """Under RLS another org's row is invisible, so following the relation
    raises. Here the relation raises outright and the lookup must not care."""
    record = make_record(key, org_a)
    mine = make_record(parent_key, org_a)
    with rls_org(org_b):
        foreign = make_record(parent_key, org_b)
    model = type(record)
    related = model._meta.get_field(column).related_model
    adapter = _adapter(org_a, key)

    def hidden(instance):
        raise related.DoesNotExist

    _set(record, **{column: foreign})
    with patch.object(model, column, property(hidden)):
        assert adapter.parent(record) is None
        assert adapter.parent_label(record) == label
    _set(record, **{column: mine})
    with patch.object(model, column, property(hidden)):
        assert adapter.parent(record) == (parent_key, mine)


def _rls_binds_this_role():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )
        return not cursor.fetchone()[0]


@pytest.mark.postgres_only
def test_a_parent_in_another_org_is_none_under_row_level_security(org_a, org_b):
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    if not _rls_binds_this_role():
        pytest.skip("Needs a role row-level security binds, as in CI")
    with rls_org(org_b):
        foreign = Account.objects.create(name="Foreign", org=org_b)
    with rls_org(org_a):
        mine = Account.objects.create(name="Mine", org=org_a)
        assert not Account.objects.filter(pk=foreign.pk).exists()
        for key in ("deal", "ticket"):
            adapter = _adapter(org_a, key)
            # An account in another org is never the parent.
            record = _set(make_record(key, org_a), account=foreign)
            assert adapter.parent(record) is None
            assert adapter.parent_label(record) == "account"
            _set(record, account=mine)
            assert adapter.parent(record) == ("account", mine)


def test_parent_label_reads_the_orgs_registry(org_a, restore_registry_hooks):
    register_hook(lambda org: (DuckEntry("obj:site", "obj:site", label="Site"),))

    class SiteChild(Adapter):
        parent_key = "obj:site"

    adapter = SiteChild(object_for_key(org_a, "lead"))
    assert adapter.parent_label(make_record("lead", org_a)) == "site"


def test_a_tasks_parent_is_whichever_record_it_links(org_a):
    adapter = _adapter(org_a, "task")
    assert type(adapter).parent_key is None
    task = make_record("task", org_a)
    assert adapter.parent(task) is None
    assert adapter.parent_label(task) == "parent"
    for column, key in (
        ("lead", "lead"),
        ("account", "account"),
        ("opportunity", "deal"),
        ("case", "ticket"),
    ):
        parent = make_record(key, org_a)
        columns = dict.fromkeys(("lead", "account", "opportunity", "case"))
        _set(task, **{**columns, column: parent})
        assert adapter.parent(task) == (key, parent)
        assert adapter.parent_label(task) == key


@pytest.mark.parametrize("key", ["lead", "contact", "account"])
def test_leads_contacts_and_accounts_have_no_parent(key, org_a):
    adapter = _adapter(org_a, key)
    assert type(adapter).parent_key is None
    assert adapter.parent(make_record(key, org_a)) is None


@pytest.mark.parametrize("key", KEYS)
def test_task_parent_links_a_new_task_to_the_record(key, org_a):
    record = make_record(key, org_a)
    expected = {
        "lead": {"lead": str(record.pk)},
        "contact": {"contacts": [str(record.pk)]},
        "account": {"account": str(record.pk)},
        "deal": {"opportunity": str(record.pk)},
        "ticket": {"case": str(record.pk)},
        "task": {},
    }[key]
    assert _adapter(org_a, key).task_parent(record) == expected


# Writing


@pytest.mark.parametrize("key", KEYS)
def test_write_goes_through_the_update_service(key, org_a, admin_profile, user_profile):
    target = object_for_key(org_a, key).custom_field_target
    _custom(org_a, target, "kept", "text")
    _custom(org_a, target, "score", "number")
    record = _set(make_record(key, org_a), custom_fields={"kept": "yes", "score": 1})
    changes = {
        TEXT_FIELD[key]: "New value",
        "assigned_to": [str(user_profile.pk)],
        "custom_fields.score": 7,
    }
    with patch(SERVICES[key], return_value=None) as service:
        assert _adapter(org_a, key).write(record, changes, admin_profile) is None
    service.assert_called_once()
    (request, got, data), kwargs = service.call_args
    assert got == record
    assert request.profile == admin_profile
    # Only the custom keys asked for: the service keeps the rest from the row.
    assert data == {
        TEXT_FIELD[key]: "New value",
        "assigned_to": [str(user_profile.pk)],
        "custom_fields": {"score": 7},
    }
    assert kwargs == {}


@pytest.mark.parametrize("key", KEYS)
def test_write_saves_through_the_real_service(key, org_a, admin_profile, user_profile):
    record = make_record(key, org_a)
    errors = _adapter(org_a, key).write(
        record,
        {TEXT_FIELD[key]: "Written by a rule", "assigned_to": [str(user_profile.pk)]},
        admin_profile,
    )
    assert errors is None
    record.refresh_from_db()
    assert getattr(record, TEXT_FIELD[key]) == "Written by a rule"
    assert list(record.assigned_to.all()) == [user_profile]


@pytest.mark.parametrize("key", KEYS)
def test_a_custom_value_changed_since_the_load_stands(key, org_a, admin_profile):
    target = object_for_key(org_a, key).custom_field_target
    _custom(org_a, target, "first", "text")
    _custom(org_a, target, "second", "text")
    loaded = _set(make_record(key, org_a), custom_fields={"first": "a", "second": "a"})
    type(loaded).objects.filter(pk=loaded.pk).update(
        custom_fields={"first": "a", "second": "theirs"}
    )

    errors = _adapter(org_a, key).write(
        loaded, {"custom_fields.first": "mine"}, admin_profile
    )

    assert errors is None
    stored = type(loaded).objects.get(pk=loaded.pk)
    assert stored.custom_fields == {"first": "mine", "second": "theirs"}


@pytest.mark.parametrize("key", KEYS)
def test_write_locks_the_record_it_updates(key, org_a, admin_profile):
    """SQLite drops FOR UPDATE, so this asks which querysets were locked."""
    record = make_record(key, org_a)
    original = QuerySet.select_for_update
    with patch.object(
        QuerySet, "select_for_update", autospec=True, side_effect=original
    ) as spy:
        errors = _adapter(org_a, key).write(
            record, {TEXT_FIELD[key]: "x"}, admin_profile
        )
    assert errors is None
    assert any(
        call.args[0].model is type(record) and call.kwargs == {"no_key": True}
        for call in spy.call_args_list
    )


def test_a_record_gone_before_the_lock_is_refused(org_a, admin_profile):
    deal = make_record("deal", org_a)
    with (
        patch.object(
            ObjectEntry, "records", lambda self, org: self.model.objects.none()
        ),
        patch(SERVICES["deal"], return_value=None) as service,
    ):
        errors = _adapter(org_a, "deal").write(deal, {"name": "x"}, admin_profile)
    assert errors == {"detail": ["Cannot edit this deal."]}
    service.assert_not_called()


@pytest.mark.parametrize("key", KEYS)
def test_write_refuses_an_actor_who_cannot_edit(
    key, org_a, admin_user, regular_user, user_profile
):
    hidden = make_record(key, org_a, admin_user)
    own = make_record(key, org_a, regular_user)
    adapter = _adapter(org_a, key)
    with patch(SERVICES[key], return_value=None) as service:
        errors = adapter.write(hidden, {TEXT_FIELD[key]: "x"}, user_profile)
        assert errors and isinstance(errors, dict)
        service.assert_not_called()
        assert adapter.write(own, {TEXT_FIELD[key]: "x"}, user_profile) is None
        service.assert_called_once()


@pytest.mark.parametrize("key", KEYS)
def test_write_refuses_an_actor_from_another_org(key, org_a, org_b, profile_b):
    record = make_record(key, org_a)
    adapter = _adapter(org_a, key)
    # Even with an edit rule that would let them, the org check holds.
    model = object_for_key(org_a, key).model
    with (
        patch.object(ObjectEntry, "editable", lambda self, p: model.objects.all()),
        patch(SERVICES[key], return_value=None) as service,
    ):
        errors = adapter.write(record, {TEXT_FIELD[key]: "x"}, profile_b)
    assert errors and isinstance(errors, dict)
    service.assert_not_called()


@pytest.mark.parametrize("key", KEYS)
def test_write_refuses_an_inactive_actor(key, org_a, admin_profile):
    record = make_record(key, org_a)
    adapter = _adapter(org_a, key)
    with patch(SERVICES[key], return_value=None) as service:
        assert adapter.write(record, {TEXT_FIELD[key]: "x"}, admin_profile) is None
        Profile.objects.filter(pk=admin_profile.pk).update(is_active=False)
        admin_profile.refresh_from_db()
        errors = adapter.write(record, {TEXT_FIELD[key]: "x"}, admin_profile)
    assert errors and isinstance(errors, dict)
    service.assert_called_once()


@pytest.mark.parametrize("key", KEYS)
def test_write_refuses_a_key_a_rule_may_not_set(key, org_a, admin_profile):
    record = make_record(key, org_a)
    adapter = _adapter(org_a, key)
    refused = [*SERVER_OWNED, "description", *READ_ONLY.get(key, ())]
    with patch(SERVICES[key], return_value=None) as service:
        for field in refused:
            errors = adapter.write(record, {field: "x"}, admin_profile)
            assert set(errors) == {field}, field
        service.assert_not_called()


@pytest.mark.parametrize("key", KEYS)
def test_a_malformed_id_comes_back_as_an_error_dict(key, org_a, admin_profile):
    record = make_record(key, org_a)
    errors = _adapter(org_a, key).write(
        record, {"assigned_to": ["not-an-id"]}, admin_profile
    )
    assert isinstance(errors, dict) and "assigned_to" in errors


def test_a_service_refusal_comes_back_with_its_message(org_a, admin_profile):
    lead = make_record("lead", org_a)
    errors = _adapter(org_a, "lead").write(lead, {"status": "converted"}, admin_profile)
    assert errors == {"status": [CONVERSION_REFUSED]}


# Per-object choices


def test_converted_is_not_settable(org_a):
    status = next(f for f in _adapter(org_a, "lead").fields(org_a) if f.key == "status")
    assert status.settable
    by_value = {c.value: c for c in status.choices}
    assert not by_value["converted"].settable
    assert all(c.settable for v, c in by_value.items() if v != "converted")
    assert set(by_value) == {v for v, _ in Lead._meta.get_field("status").choices}


def test_duplicate_is_not_settable(org_a, admin_profile):
    adapter = _adapter(org_a, "ticket")
    status = next(f for f in adapter.fields(org_a) if f.key == "status")
    by_value = {c.value: c for c in status.choices}
    assert not by_value["Duplicate"].settable
    assert all(c.settable for v, c in by_value.items() if v != "Duplicate")
    ticket = make_record("ticket", org_a)
    errors = adapter.write(ticket, {"status": "Duplicate"}, admin_profile)
    assert errors == {"status": [DUPLICATE_BY_MERGE_ONLY]}


def _stage(pipeline, code):
    return DealStage.objects.get(pipeline=pipeline, code=code)


@pytest.fixture
def two_pipelines(org_a):
    """Two pipelines seeded the way the pipeline view seeds one, so codes repeat."""
    sales = DealPipeline.default_for(org_a)
    renewals = DealPipeline.objects.create(org=org_a, name="Renewals")
    renewals.seed_stages()
    DealStage.objects.create(
        org=org_a, pipeline=renewals, code="SIGNED", label="Signed", kind="won"
    )
    return sales, renewals


def test_stage_kind_reads_won_for_any_won_stage(org_a, two_pipelines):
    sales, renewals = two_pipelines
    adapter = _adapter(org_a, "deal")
    won_in_sales = Opportunity.objects.create(
        name="A", org=org_a, pipeline=sales, stage="CLOSED_WON"
    )
    won_in_renewals = Opportunity.objects.create(
        name="B", org=org_a, pipeline=renewals, stage="SIGNED"
    )
    open_deal = Opportunity.objects.create(
        name="C", org=org_a, pipeline=renewals, stage="PROPOSAL"
    )
    lost = Opportunity.objects.create(
        name="D", org=org_a, pipeline=sales, stage="CLOSED_LOST"
    )
    assert adapter.read(won_in_sales, "stage_kind") == "won"
    assert adapter.read(won_in_renewals, "stage_kind") == "won"
    assert adapter.read(open_deal, "stage_kind") == "open"
    assert adapter.read(lost, "stage_kind") == "lost"
    assert adapter.snapshot(won_in_renewals)["stage_kind"] == "won"


def test_stage_choices_are_grouped_by_pipeline(org_a, org_b, two_pipelines):
    sales, renewals = two_pipelines
    with rls_org(org_b):
        theirs = DealPipeline.objects.create(org=org_b, name="Theirs")
        elsewhere = DealStage.objects.create(
            org=org_b, pipeline=theirs, code="ELSEWHERE", label="Elsewhere"
        )
    fields = {f.key: f for f in _adapter(org_a, "deal").fields(org_a)}
    stages = fields["stage"].choices
    won_sales = _stage(sales, "CLOSED_WON")
    won_renewals = _stage(renewals, "CLOSED_WON")
    assert Choice(str(won_sales.pk), "Closed Won", "Sales") in stages
    assert Choice(str(won_renewals.pk), "Closed Won", "Renewals") in stages
    assert won_sales.pk != won_renewals.pk
    assert len({c.value for c in stages}) == len(stages)
    assert {c.group for c in stages} == {"Sales", "Renewals"}
    assert str(elsewhere.pk) not in {c.value for c in stages}
    assert [c.value for c in fields["stage_kind"].choices] == ["open", "won", "lost"]
    assert not fields["stage_kind"].settable


def test_a_deals_stage_reads_as_its_stage_id(org_a, two_pipelines):
    sales, renewals = two_pipelines
    adapter = _adapter(org_a, "deal")
    in_sales = Opportunity.objects.create(
        name="A", org=org_a, pipeline=sales, stage="CLOSED_WON"
    )
    in_renewals = Opportunity.objects.create(
        name="B", org=org_a, pipeline=renewals, stage="CLOSED_WON"
    )
    assert adapter.read(in_sales, "stage") == str(_stage(sales, "CLOSED_WON").pk)
    assert adapter.read(in_renewals, "stage") == str(_stage(renewals, "CLOSED_WON").pk)
    assert adapter.snapshot(in_renewals)["stage"] == adapter.read(in_renewals, "stage")


def test_a_stage_of_the_deals_pipeline_moves_it(org_a, admin_profile, two_pipelines):
    sales, _ = two_pipelines
    deal = Opportunity.objects.create(
        name="A", org=org_a, pipeline=sales, stage="QUALIFICATION"
    )
    proposal = _stage(sales, "PROPOSAL")
    adapter = _adapter(org_a, "deal")
    assert adapter.write(deal, {"stage": str(proposal.pk)}, admin_profile) is None
    deal.refresh_from_db()
    assert (deal.stage, deal.pipeline_id) == ("PROPOSAL", sales.pk)
    assert adapter.read(deal, "stage") == str(proposal.pk)


def test_a_stage_from_elsewhere_is_refused(org_a, org_b, admin_profile, two_pipelines):
    sales, renewals = two_pipelines
    with rls_org(org_b):
        theirs = DealPipeline.default_for(org_b)
    deal = Opportunity.objects.create(
        name="A", org=org_a, pipeline=sales, stage="QUALIFICATION"
    )
    adapter = _adapter(org_a, "deal")
    refused = (
        str(_stage(renewals, "PROPOSAL").pk),
        str(_stage(theirs, "PROPOSAL").pk),
        "PROPOSAL",
        "not-an-id",
        None,
    )
    with patch(SERVICES["deal"], return_value=None) as service:
        for value in refused:
            errors = adapter.write(deal, {"stage": value}, admin_profile)
            assert errors == {"stage": [NOT_A_STAGE]}, value
    service.assert_not_called()
    deal.refresh_from_db()
    assert (deal.stage, deal.pipeline_id) == ("QUALIFICATION", sales.pk)


def test_lead_stage_choices_are_grouped_by_lead_pipeline(org_a, org_b):
    inbound = LeadPipeline.objects.create(name="Inbound", org=org_a)
    new = LeadStage.objects.create(pipeline=inbound, name="New", order=1, org=org_a)
    retired = LeadPipeline.objects.create(name="Old", org=org_a, is_active=False)
    LeadStage.objects.create(pipeline=retired, name="Gone", org=org_a)
    with rls_org(org_b):
        theirs = LeadPipeline.objects.create(name="Theirs", org=org_b)
        LeadStage.objects.create(pipeline=theirs, name="Elsewhere", org=org_b)
    adapter = _adapter(org_a, "lead")
    stage = next(f for f in adapter.fields(org_a) if f.key == "stage")
    assert stage.choices == (Choice(str(new.pk), "New", "Inbound"),)
    assert not stage.settable
    lead = _set(make_record("lead", org_a), stage=new)
    assert adapter.read(lead, "stage") == str(new.pk)


# Which objects can be automated


def test_invoices_have_no_adapter(org_a):
    assert adapter_for(org_a, "invoice") is None
    assert adapter_for(org_a, "estimate") is None
    assert adapter_for(org_a, "recurring_invoice") is None
    assert adapter_for(org_a, "nothing") is None
    assert [entry.key for entry, _ in automatable(org_a)] == KEYS
    assert all(adapter.entry is entry for entry, adapter in automatable(org_a))


@dataclass(frozen=True)
class DuckEntry:
    """An entry from a registry hook that is not an `ObjectEntry`."""

    key: str
    custom_field_target: str
    adapter: object = None
    label: str = "Duck"

    def automation_adapter(self):
        return self.adapter


@dataclass(frozen=True)
class PlainEntry:
    key: str
    custom_field_target: str


def test_a_hook_entry_offers_an_adapter_through_its_method(
    org_a, restore_registry_hooks
):
    sentinel = object()
    register_hook(
        lambda org: (
            DuckEntry("obj:with", "obj:with", sentinel),
            DuckEntry("obj:none", "obj:none"),
            PlainEntry("obj:plain", "obj:plain"),
        )
    )
    assert adapter_for(org_a, "obj:with") is sentinel
    assert adapter_for(org_a, "obj:none") is None
    assert adapter_for(org_a, "obj:plain") is None
    assert [entry.key for entry, _ in automatable(org_a)] == [*KEYS, "obj:with"]
