"""Capturing changes: what a save hands the rule engine, and when.

The engine is patched throughout to record what it receives.
"""

import csv
import io
import logging
import uuid
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from crum import set_current_request
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, transaction
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from accounts.models import Account
from automation import capture
from automation.capture import Change
from automation.models import AutomationRule
from automation.objects import Adapter
from cases.models import Case
from common.packs import applier
from common.packs.applier import apply_pack
from common.packs.loader import get_pack
from conftest import rls_org
from leads.models import Lead
from opportunity.models import DealPipeline, DealStage, Opportunity
from webforms.models import WebForm, WebFormField

OBJECTS = ("lead", "contact", "account", "deal", "ticket", "task")


@pytest.fixture
def processed():
    """Every change handed to the engine, in order."""
    received = []
    with patch("automation.engine.process", side_effect=received.extend):
        yield received


def _rule(org, object_key, **extra):
    fields = {"is_active": True, **extra}
    return AutomationRule.objects.create(
        org=org, name=f"On {object_key}", object_key=object_key, **fields
    )


@contextmanager
def _request():
    """A request as crum sees it, without a view: capture buffers, nothing flushes."""
    request = RequestFactory().get("/")
    set_current_request(request)
    try:
        yield request
    finally:
        set_current_request(None)


def _csv(name, headers, rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return SimpleUploadedFile(name, buf.getvalue().encode("utf-8"), "text/csv")


def _reads_old_row(query, table):
    sql = query["sql"]
    return sql.startswith("SELECT") and f'FROM "{table}"' in sql


def test_a_patch_produces_one_change_with_old_and_new_values(
    admin_client, org_a, processed
):
    lead = Lead.objects.create(org=org_a, title="Old title")
    _rule(org_a, "lead")

    response = admin_client.patch(
        f"/api/leads/{lead.pk}/", {"title": "New title"}, format="json"
    )

    assert response.status_code == 200, response.content
    assert processed == [
        Change(
            org_a.id, "lead", lead.pk, "updated", {"title": ("Old title", "New title")}
        )
    ]


def test_a_record_saved_twice_in_one_request_is_one_change(
    admin_client, org_a, processed
):
    sales = DealPipeline.default_for(org_a)
    open_stage = DealStage.objects.get(pipeline=sales, code="QUALIFICATION")
    won = DealStage.objects.get(pipeline=sales, code="CLOSED_WON")
    deal = Opportunity.objects.create(
        name="Big deal", org=org_a, pipeline=sales, stage="QUALIFICATION", amount=900
    )
    _rule(org_a, "deal")

    with patch.object(
        Opportunity, "save", autospec=True, side_effect=Opportunity.save
    ) as save:
        response = admin_client.patch(
            f"/api/opportunities/{deal.pk}/",
            {"stage": "CLOSED_WON", "closed_on": "2026-10-01"},
            format="json",
        )

    assert response.status_code == 200, response.content
    assert save.call_count == 2
    [change] = processed
    assert (change.object_key, change.record_id, change.event) == (
        "deal",
        deal.pk,
        "updated",
    )
    assert change.changes["stage"] == (str(open_stage.pk), str(won.pk))
    assert change.changes["stage_kind"] == ("open", "won")
    assert change.changes["closed_on"] == (None, "2026-10-01")


def test_create_then_update_in_one_request_is_one_created(org_a, processed):
    _rule(org_a, "lead")
    with _request() as request:
        lead = Lead.objects.create(org=org_a, title="First")
        lead.title = "Second"
        lead.save()
        lead.city = "Pune"
        lead.save()
        assert capture.flush(request) == [
            Change(org_a.id, "lead", lead.pk, "created", {})
        ]
        assert capture.flush(request) == []
    assert processed == []


def test_two_updates_keep_the_first_old_value_and_the_last_new_one(org_a):
    lead = Lead.objects.create(org=org_a, title="Start")
    _rule(org_a, "lead")
    with _request() as request:
        lead.title = "Middle"
        lead.save()
        lead.title = "End"
        lead.city = "Pune"
        lead.save()
        changes = capture.flush(request)
    assert changes == [
        Change(
            org_a.id,
            "lead",
            lead.pk,
            "updated",
            {"title": ("Start", "End"), "city": (None, "Pune")},
        )
    ]


def test_a_field_that_ends_where_it_started_is_not_a_change(org_a):
    lead = Lead.objects.create(org=org_a, title="Start")
    _rule(org_a, "lead")
    with _request() as request:
        lead.title = "Moved"
        lead.city = "Pune"
        lead.save()
        lead.title = "Start"
        lead.save()
        assert capture.flush(request) == [
            Change(org_a.id, "lead", lead.pk, "updated", {"city": (None, "Pune")})
        ]

        lead.title = "Moved"
        lead.save()
        lead.title = "Start"
        lead.save()
        assert capture.flush(request) == []

        lead.save()
        assert capture.flush(request) == []


def test_no_active_rule_means_no_old_row_query(org_a, django_assert_num_queries):
    lead = Lead.objects.create(org=org_a, title="Quiet")

    with django_assert_num_queries(2) as quiet:
        lead.title = "Still quiet"
        lead.save()
    assert not any(_reads_old_row(q, "lead") for q in quiet.captured_queries)
    assert not any(q["sql"].startswith("SAVEPOINT") for q in quiet.captured_queries)

    _rule(org_a, "lead")
    # Four of the eleven are the savepoints around capture's reads, and one
    # reads the org's lead sources for the field catalogue.
    with django_assert_num_queries(11) as watched:
        lead.title = "Watched"
        lead.save()
    assert sum(_reads_old_row(q, "lead") for q in watched.captured_queries) == 1


@pytest.mark.parametrize(
    "rule",
    [
        {"is_active": False},
        {"paused_reason": "owner_not_admin"},
        {"object_key": "contact"},
        {"other_org": True},
    ],
    ids=["switched_off", "paused", "other_object", "other_org"],
)
def test_only_a_switched_on_unpaused_rule_on_the_object_counts(
    rule, org_a, org_b, django_capture_on_commit_callbacks, processed
):
    rule = dict(rule)
    owner = org_b if rule.pop("other_org", False) else org_a
    with rls_org(owner):
        AutomationRule.objects.create(
            org=owner, name="Rule", **{"object_key": "lead", "is_active": True, **rule}
        )
    lead = Lead.objects.create(org=org_a, title="Before")
    assert not capture.has_active_rules(org_a.id, "lead")

    with django_capture_on_commit_callbacks(execute=True):
        lead.title = "After"
        lead.save()
    assert processed == []

    _rule(org_a, "lead")
    assert capture.has_active_rules(org_a.id, "lead")
    with django_capture_on_commit_callbacks(execute=True):
        lead.title = "Again"
        lead.save()
    assert processed == [
        Change(org_a.id, "lead", lead.pk, "updated", {"title": ("After", "Again")})
    ]


def test_the_rule_check_runs_once_per_request(org_a):
    lead = Lead.objects.create(org=org_a, title="One")
    with _request(), CaptureQueriesContext(connection) as queries:
        for title in ("Two", "Three", "Four"):
            lead.title = title
            lead.save()
    rule_reads = [q for q in queries.captured_queries if "automation_rule" in q["sql"]]
    assert len(rule_reads) == 1


def test_outside_a_request_the_change_waits_for_commit(
    org_a, django_capture_on_commit_callbacks, processed
):
    _rule(org_a, "lead")
    lead = Lead.objects.create(org=org_a, title="Before")

    with django_capture_on_commit_callbacks() as callbacks:
        lead.title = "After"
        lead.save()
    assert processed == []

    for callback in callbacks:
        callback()
    assert processed == [
        Change(org_a.id, "lead", lead.pk, "updated", {"title": ("Before", "After")})
    ]


def test_imports_packs_and_bulk_edits_capture_nothing(
    admin_client,
    org_a,
    admin_profile,
    django_capture_on_commit_callbacks,
    monkeypatch,
    processed,
):
    for key in OBJECTS:
        _rule(org_a, key)

    lead_file = _csv(
        "leads.csv", ["first_name", "last_name", "email"], [["Ada", "Byte", "ada@x.io"]]
    )
    response = admin_client.post(
        "/api/leads/import/commit/", {"file": lead_file}, format="multipart"
    )
    assert response.status_code == 200, response.content
    assert response.json()["created"] == 1

    contact_file = _csv(
        "contacts.csv",
        ["first_name", "last_name", "email"],
        [["Pat", "Lee", "pat@x.io"]],
    )
    response = admin_client.post(
        "/api/contacts/import/commit/", {"file": contact_file}, format="multipart"
    )
    assert response.status_code == 200, response.content
    assert response.json()["created"] == 1

    ticket_file = _csv(
        "tickets.csv", ["name", "status", "priority"], [["Login bug", "New", "High"]]
    )
    response = admin_client.post(
        "/api/cases/import/commit/", {"file": ticket_file}, format="multipart"
    )
    assert response.status_code == 200, response.content
    assert response.json()["created"] == 1

    # A regular write made while the sample data goes in shows the marker
    # covers the whole step, not only the sample rows.
    create_sample = applier._create_sample

    def create_sample_and_a_real_account(*args, **kwargs):
        Account.objects.create(org=org_a, name=f"Real {uuid.uuid4().hex[:8]}")
        return create_sample(*args, **kwargs)

    monkeypatch.setattr(applier, "_create_sample", create_sample_and_a_real_account)
    with django_capture_on_commit_callbacks(execute=True):
        report = apply_pack(org_a, get_pack("real-estate"), admin_profile)
    assert report["created"]
    assert Lead.objects.filter(org=org_a, is_sample=True).exists()

    tickets = [
        Case.objects.create(org=org_a, name=f"Ticket {n}", status="New")
        for n in range(2)
    ]
    response = admin_client.post(
        "/api/cases/bulk/update/",
        {"ids": [str(t.pk) for t in tickets], "fields": {"status": "Pending"}},
        format="json",
    )
    assert response.status_code == 200, response.content
    assert response.json()["updated"] == 2

    assert processed == []


def test_a_persons_edit_of_a_pack_sample_record_is_captured(
    admin_client, org_a, admin_profile, django_capture_on_commit_callbacks, processed
):
    _rule(org_a, "lead")
    with django_capture_on_commit_callbacks(execute=True):
        apply_pack(org_a, get_pack("real-estate"), admin_profile)
    assert processed == []
    sample = Lead.objects.filter(org=org_a, is_sample=True).first()
    old = sample.title

    response = admin_client.patch(
        f"/api/leads/{sample.pk}/", {"title": "Demo, edited"}, format="json"
    )

    assert response.status_code == 200, response.content
    assert processed == [
        Change(org_a.id, "lead", sample.pk, "updated", {"title": (old, "Demo, edited")})
    ]


def test_suppressed_writes_are_not_captured_and_the_marker_lifts(org_a):
    _rule(org_a, "lead")
    with _request() as request:
        with capture.suppress_rules():
            quiet = Lead.objects.create(org=org_a, title="Imported")
            quiet.title = "Imported, edited"
            quiet.save()
        loud = Lead.objects.create(org=org_a, title="Typed in")
        changes = capture.flush(request)
    assert changes == [Change(org_a.id, "lead", loud.pk, "created", {})]


def test_inside_a_running_rule_the_change_goes_to_the_chain(org_a, processed):
    lead = Lead.objects.create(org=org_a, title="A")
    _rule(org_a, "lead")
    chain = SimpleNamespace(changes={})
    with patch("automation.engine.current_chain", return_value=chain):
        with _request() as request:
            lead.title = "B"
            lead.save()
            lead.title = "C"
            lead.save()
            assert capture.flush(request) == []
    assert list(chain.changes.values()) == [
        Change(org_a.id, "lead", lead.pk, "updated", {"title": ("A", "C")})
    ]
    assert processed == []


def test_raw_saves_are_not_captured(org_a):
    _rule(org_a, "lead")
    now = timezone.now()
    lead = Lead(org=org_a, title="Fixture", created_at=now, updated_at=now)
    with _request() as request:
        lead.save_base(raw=True)
        assert capture.flush(request) == []
        lead.title = "Edited"
        lead.save()
        assert capture.flush(request) == [
            Change(
                org_a.id, "lead", lead.pk, "updated", {"title": ("Fixture", "Edited")}
            )
        ]


@pytest.mark.parametrize("failing_call", [1, 2], ids=["before", "after"])
def test_a_capture_failure_does_not_fail_the_save(org_a, caplog, failing_call):
    lead = Lead.objects.create(org=org_a, title="Old title")
    _rule(org_a, "lead")
    real_snapshot = Adapter.snapshot
    calls = []

    def snapshot(adapter, record):
        calls.append(record)
        if len(calls) == failing_call:
            raise RuntimeError("boom")
        return real_snapshot(adapter, record)

    with (
        patch.object(Adapter, "snapshot", snapshot),
        caplog.at_level(logging.ERROR, logger="automation.capture"),
        _request() as request,
    ):
        lead.title = "Private title"
        lead.save()
        assert capture.flush(request) == []

    assert len(calls) == failing_call
    lead.refresh_from_db()
    assert lead.title == "Private title"
    assert len([r for r in caplog.records if r.name == "automation.capture"]) == 1
    assert "Private title" not in caplog.text
    assert "Old title" not in caplog.text


@pytest.mark.postgres_only
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("failing_call", [1, 2], ids=["before", "after"])
def test_a_database_error_in_capture_leaves_the_save_committed(
    org_a, caplog, failing_call
):
    """PostgreSQL refuses every statement after an error until a rollback, so
    capture's reads must fail inside their own savepoint, not the caller's."""
    if connection.vendor != "postgresql":
        pytest.skip("Only PostgreSQL aborts a transaction on an error")
    lead = Lead.objects.create(org=org_a, title="Old title")
    _rule(org_a, "lead")
    real_snapshot = Adapter.snapshot
    calls = []

    def snapshot(adapter, record):
        calls.append(record)
        if len(calls) == failing_call:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM automation_no_such_table")
        return real_snapshot(adapter, record)

    with (
        patch.object(Adapter, "snapshot", snapshot),
        caplog.at_level(logging.ERROR, logger="automation.capture"),
        _request() as request,
    ):
        with transaction.atomic():
            lead.title = "Saved title"
            lead.save()
            Lead.objects.filter(pk=lead.pk).update(city="Pune")
        assert capture.flush(request) == []

    assert len(calls) == failing_call
    lead.refresh_from_db()
    assert (lead.title, lead.city) == ("Saved title", "Pune")
    assert len([r for r in caplog.records if r.name == "automation.capture"]) == 1


def test_an_anonymous_web_form_submission_is_captured(
    unauthenticated_client, org_a, admin_profile, processed
):
    cache.clear()
    form = WebForm.objects.create(
        name="Contact us", org=org_a, is_published=True, lead_source="other"
    )
    WebFormField.objects.create(
        form=form,
        org=org_a,
        order=0,
        source=WebFormField.SOURCE_LEAD,
        lead_field="email",
        label="Email",
        is_required=True,
    )
    _rule(org_a, "lead")

    response = unauthenticated_client.post(
        f"/api/public/forms/{org_a.id}/{form.id}/submit/",
        {"email": "pat@example.com"},
        format="json",
    )

    assert response.status_code == 200, response.content
    lead = Lead.objects.get(org=org_a, email="pat@example.com")
    assert processed == [Change(org_a.id, "lead", lead.pk, "created", {})]


def test_the_middleware_never_raises(admin_client, org_a, caplog):
    lead = Lead.objects.create(org=org_a, title="Old title")
    _rule(org_a, "lead")

    with (
        patch("automation.engine.process", side_effect=RuntimeError("boom")),
        caplog.at_level(logging.ERROR, logger="automation.middleware"),
    ):
        response = admin_client.patch(
            f"/api/leads/{lead.pk}/", {"title": "Private title"}, format="json"
        )

    assert response.status_code == 200, response.content
    logged = [r for r in caplog.records if r.name == "automation.middleware"]
    assert len(logged) == 1
    assert "Private title" not in caplog.text
    assert "Old title" not in caplog.text


def test_the_middleware_runs_before_the_webhook_flush():
    assert settings.MIDDLEWARE[-1] == "automation.middleware.AutomationMiddleware"
    assert settings.MIDDLEWARE[-2] == "webhooks.middleware.WebhookEventsMiddleware"
