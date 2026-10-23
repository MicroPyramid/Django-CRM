"""GET and PUT /api/org/modules/: who may read and change an org's modules,
the 400 envelope, the refusals, and what a change leaves alone."""

import pytest

from accounts.models import Account
from cases.models import Case, InboundMailbox
from common.audit_log import SecurityAuditLog
from common.models import User
from common.modules import KEYS
from common.testing import (
    _make_authenticated_client,
    clear_rls_context,
    set_modules_off,
)
from invoices.models import Invoice
from leads.models import Lead
from tasks.models import Task
from webforms.models import WebForm

URL = "/api/org/modules/"
ROW_KEYS = {"key", "label", "group", "covers", "stops", "enabled", "available", "needs"}
DEFAULT_ORDER = [
    "deals", "leads", "goals", "tasks", "tickets", "knowledge_base", "documents",
    "invoices", "timesheet",
]  # fmt: skip


def put(client, off, order=()):
    return client.put(URL, {"off": list(off), "order": list(order)}, format="json")


def rows(response):
    return {r["key"]: r for r in response.json()["modules"]}


def form(org, name, target="lead", published=True):
    return WebForm.objects.create(
        org=org, name=name, target=target, is_published=published
    )


class TestRead:
    def test_any_member_reads_the_modules(self, user_client, admin_client):
        response = user_client.get(URL)
        assert response.status_code == 200
        body = response.json()
        assert [r["key"] for r in body["modules"]] == DEFAULT_ORDER
        assert all(set(r) == ROW_KEYS for r in body["modules"])
        assert [r["group"] for r in body["modules"]] == (
            ["sell"] * 3 + ["serve"] * 4 + ["bill"] * 2
        )
        assert body["can_edit"] is False
        assert admin_client.get(URL).json()["can_edit"] is True

    def test_the_rows_carry_the_contract_values(self, user_client):
        goals = rows(user_client.get(URL))["goals"]
        assert goals == {
            "key": "goals",
            "label": "Goals",
            "group": "sell",
            "covers": "Sales goals, the leaderboard and goal history.",
            "stops": "Goals leave every menu, and goal milestone emails stop.",
            "enabled": True,
            "available": True,
            "needs": "deals",
        }

    def test_no_session_is_403(self, unauthenticated_client):
        for response in (
            unauthenticated_client.get(URL),
            put(unauthenticated_client, []),
        ):
            assert response.status_code == 403
            assert response.json() == {
                "detail": "Authentication credentials were not provided."
            }

    def test_a_session_with_no_org_is_403(self, db):
        user = User.objects.create_user(email="lone@test.com", password="x")
        client = _make_authenticated_client(user, None, None)
        assert client.get(URL).status_code == 403

    def test_patch_is_405(self, admin_client):
        assert admin_client.patch(URL, {"off": []}, format="json").status_code == 405

    def test_labels_and_stops_follow_terminology_and_never_leak_the_template(
        self, admin_client, org_a
    ):
        for terminology in (
            {},
            {"lead.plural": "Enquiries", "opportunity.plural": "Jobs"},
        ):
            org_a.terminology = terminology
            org_a.save(update_fields=["terminology"])
            for response in (admin_client.get(URL), put(admin_client, [], KEYS)):
                body = response.json()
                assert all("{" not in r["stops"] for r in body["modules"])
                assert all("{label}" not in r["stops"] for r in body["modules"])
        by_key = rows(admin_client.get(URL))
        assert by_key["leads"]["label"] == "Enquiries"
        assert (
            by_key["leads"]["stops"] == "Enquiries leave every menu, search and Today."
        )
        assert by_key["deals"]["label"] == "Jobs"
        assert by_key["deals"]["stops"].startswith("Everything in Jobs leaves")
        assert by_key["invoices"]["stops"].endswith(
            "Payment reminders that fall due while Invoices is off are not sent later."
        )
        assert by_key["invoices"]["stops"].count("Invoices") == 2


class TestWho:
    def test_a_member_cannot_switch_modules(self, user_client, org_a):
        response = put(user_client, ["tickets"])
        assert response.status_code == 403
        assert response.json() == {
            "error": True,
            "errors": "Only admins can switch modules on or off.",
        }
        org_a.refresh_from_db()
        assert org_a.modules_off == []
        assert not SecurityAuditLog.objects.filter(event_type="MODULES_CHANGED")

    def test_a_member_is_refused_before_the_body_is_read(self, user_client):
        response = user_client.put(URL, {"off": "nonsense"}, format="json")
        assert response.status_code == 403


class TestSwitching:
    def test_an_admin_switches_tickets_off_and_on(self, admin_client, org_a):
        response = put(admin_client, ["tickets"])
        assert response.status_code == 200
        assert response.json() == admin_client.get(URL).json()
        by_key = rows(response)
        assert by_key["tickets"]["enabled"] is False
        assert by_key["timesheet"]["enabled"] is True
        assert by_key["timesheet"]["available"] is False
        org_a.refresh_from_db()
        assert org_a.modules_off == ["tickets"]
        assert org_a.modules_on_at == {}

        by_key = rows(put(admin_client, []))
        assert by_key["tickets"]["available"] and by_key["timesheet"]["available"]
        org_a.refresh_from_db()
        assert set(org_a.modules_on_at) == {"tickets", "timesheet"}
        stamps = dict(org_a.modules_on_at)

        assert put(admin_client, []).status_code == 200
        org_a.refresh_from_db()
        assert org_a.modules_on_at == stamps

    def test_switching_deals_off_keeps_the_goals_setting(self, admin_client):
        response = put(admin_client, ["deals"])
        assert response.status_code == 200
        goals = rows(response)["goals"]
        assert goals["enabled"] is True
        assert goals["available"] is False

    def test_goals_cannot_switch_on_while_deals_is_off(self, admin_client, org_a):
        set_modules_off(org_a, "deals", "goals")
        response = put(admin_client, ["deals"])
        assert response.status_code == 400
        assert response.json() == {
            "off": ["Goals needs Pipeline. Switch Pipeline on first."]
        }
        org_a.refresh_from_db()
        assert org_a.modules_off == ["deals", "goals"]
        response = put(admin_client, [])
        assert response.status_code == 200
        assert rows(response)["goals"]["available"] is True

    NEEDS = {"off": ["Goals needs Pipeline. Switch Pipeline on first."]}

    def test_goals_cannot_switch_on_as_pipeline_switches_off(self, admin_client, org_a):
        set_modules_off(org_a, "goals")
        response = put(admin_client, ["deals"])
        assert response.status_code == 400
        assert response.json() == self.NEEDS
        org_a.refresh_from_db()
        assert org_a.modules_off == ["goals"]

    @pytest.mark.parametrize(
        "stored, sent, status",
        [
            ([], ["deals"], 200),
            (["goals", "deals"], ["goals"], 200),
            (["goals", "deals"], [], 200),
            (["goals", "deals"], ["deals"], 400),
        ],
    )
    def test_goals_needs_pipeline_on_the_new_off_list(
        self, admin_client, org_a, stored, sent, status
    ):
        set_modules_off(org_a, *stored)
        response = put(admin_client, sent)
        assert response.status_code == status
        if status == 400:
            assert response.json() == self.NEEDS
        else:
            goals = rows(response)["goals"]
            assert (goals["enabled"], goals["available"]) == (
                "goals" not in sent,
                not sent,
            )

    def test_timesheet_needs_tickets_the_same_way(self, admin_client, org_a):
        needs = {"off": ["Timesheet needs Tickets. Switch Tickets on first."]}
        set_modules_off(org_a, "timesheet")
        response = put(admin_client, ["tickets"])
        assert response.status_code == 400 and response.json() == needs
        set_modules_off(org_a, "timesheet", "tickets")
        assert put(admin_client, ["tickets"]).json() == needs
        assert put(admin_client, ["timesheet"]).status_code == 200
        assert put(admin_client, []).status_code == 200
        assert put(admin_client, ["tickets"]).status_code == 200
        assert rows(admin_client.get(URL))["timesheet"]["available"] is False

    def test_the_order_is_saved_and_returned_within_groups(self, admin_client, org_a):
        order = [
            "goals",
            "leads",
            "deals",
            "documents",
            "tasks",
            "timesheet",
            "invoices",
        ]
        response = put(admin_client, [], order)
        assert response.status_code == 200
        assert [r["key"] for r in response.json()["modules"]] == [
            "goals", "leads", "deals",
            "documents", "tasks", "tickets", "knowledge_base",
            "timesheet", "invoices",
        ]  # fmt: skip
        org_a.refresh_from_db()
        assert org_a.module_order == order
        assert [r["key"] for r in admin_client.get(URL).json()["modules"]][:3] == [
            "goals", "leads", "deals",
        ]  # fmt: skip

    def test_a_module_already_off_does_not_block_a_reorder(self, admin_client, org_a):
        set_modules_off(org_a, "tickets")
        form(org_a, "Support", target="ticket")
        response = put(admin_client, ["tickets"], ["leads", "deals"])
        assert response.status_code == 200
        assert [r["key"] for r in response.json()["modules"]][:2] == ["leads", "deals"]


class TestMalformed:
    @pytest.mark.parametrize(
        "body, errors",
        [
            ({"order": []}, {"off": ["This field is required."]}),
            ({"off": []}, {"order": ["This field is required."]}),
            ({"off": "tickets", "order": []}, {"off": ["Send a list of module keys."]}),
            ({"off": [3], "order": []}, {"off": ["Send a list of module keys."]}),
            ({"off": [], "order": "leads"}, {"order": ["Send a list of module keys."]}),
            ({"off": ["crm"], "order": []}, {"off": ['Unknown module: "crm".']}),
            (
                {"off": [], "order": ["leads", "leads"]},
                {"order": ["Name each module once."]},
            ),
            (
                {"off": ["x", "tickets"], "order": ["leads", "leads", "y"]},
                {"off": ['Unknown module: "x".'], "order": ['Unknown module: "y".']},
            ),
            (
                [],
                {
                    "off": ["This field is required."],
                    "order": ["This field is required."],
                },
            ),
        ],
    )
    def test_malformed_bodies_are_400(self, admin_client, org_a, body, errors):
        response = admin_client.put(URL, body, format="json")
        assert response.status_code == 400
        assert response.json() == errors
        org_a.refresh_from_db()
        assert org_a.modules_off == [] and org_a.module_order == []
        assert org_a.modules_on_at == {}
        assert not SecurityAuditLog.objects.filter(event_type="MODULES_CHANGED")


class TestRefusals:
    def test_published_forms_refuse_switching_their_module_off(
        self, admin_client, org_a
    ):
        contact = form(org_a, "Contact us")
        form(org_a, "Draft", published=False)
        response = put(admin_client, ["leads"])
        assert response.status_code == 400
        assert response.json() == {
            "off": [
                "Leads still receives submissions from the published web form "
                '"Contact us". Unpublish it first, so no submission is lost.'
            ]
        }
        form(org_a, "Zed help", target="ticket")
        form(org_a, "Billing help", target="ticket")
        response = put(admin_client, ["tickets"])
        assert response.json() == {
            "off": [
                "Tickets still receives submissions from 2 published web forms: "
                '"Billing help", "Zed help". Unpublish them first, so no '
                "submission is lost."
            ]
        }
        WebForm.objects.filter(org=org_a).update(is_published=False)
        assert put(admin_client, ["leads", "tickets"]).status_code == 200
        assert contact.target_module == "leads"

    def test_many_forms_are_capped_at_five_names(self, admin_client, org_a):
        for n in range(7):
            form(org_a, f"Form {n}")
        message = put(admin_client, ["leads"]).json()["off"][0]
        assert '"Form 4" and 2 more.' in message
        assert "7 published web forms" in message

    def test_an_active_mailbox_refuses_switching_tickets_off(self, admin_client, org_a):
        InboundMailbox.objects.create(
            org=org_a, address="off@acme.test", is_active=False
        )
        assert put(admin_client, ["tickets"]).status_code == 200
        put(admin_client, [])
        InboundMailbox.objects.create(org=org_a, address="help@acme.test")
        response = put(admin_client, ["tickets"])
        assert response.status_code == 400
        assert response.json() == {
            "off": [
                "Tickets still receives email at help@acme.test. Switch that "
                "mailbox off first, so no email is lost."
            ]
        }
        InboundMailbox.objects.create(org=org_a, address="billing@acme.test")
        assert put(admin_client, ["tickets"]).json() == {
            "off": [
                "Tickets still receives email at 2 mailboxes: billing@acme.test, "
                "help@acme.test. Switch them off first, so no email is lost."
            ]
        }
        org_a.refresh_from_db()
        assert org_a.modules_off == []

    def test_a_dependent_module_is_refused_too(self, admin_client, org_a):
        form(org_a, "Support", target="ticket")
        assert put(admin_client, ["tickets", "timesheet"]).status_code == 400


class TestAudit:
    def test_a_change_is_audited_with_who_and_what(
        self, admin_client, admin_user, org_a
    ):
        put(admin_client, ["tickets"])
        entries = SecurityAuditLog.objects.filter(event_type="MODULES_CHANGED")
        assert entries.count() == 1
        entry = entries.get()
        assert entry.user == admin_user and entry.org == org_a
        assert entry.metadata == {
            "switched_off": ["tickets"],
            "switched_on": [],
            "reordered": False,
        }
        put(admin_client, ["tickets"])
        put(admin_client, ["tickets"], DEFAULT_ORDER)
        assert entries.count() == 1
        put(admin_client, [], ["leads", "deals"])
        assert entries.count() == 2
        assert entries.order_by("-created_at").first().metadata == {
            "switched_off": [],
            "switched_on": ["tickets"],
            "reordered": True,
        }

    def test_the_entry_carries_the_request_and_the_audit_api_returns_it(
        self, admin_client, org_a
    ):
        admin_client.put(
            URL,
            {"off": ["tickets"], "order": []},
            format="json",
            HTTP_USER_AGENT="ModulesTest/1.0",
            REMOTE_ADDR="203.0.113.9",
        )
        entry = SecurityAuditLog.objects.get(event_type="MODULES_CHANGED")
        assert entry.ip_address == "203.0.113.9"
        assert entry.user_agent == "ModulesTest/1.0"
        assert entry.request_path == URL
        listed = admin_client.get(
            "/api/org/audit-log/", {"event_type": "MODULES_CHANGED"}
        ).json()["results"]
        assert len(listed) == 1
        assert listed[0]["details"] == {
            "switched_off": ["tickets"],
            "switched_on": [],
            "reordered": False,
        }
        assert listed[0]["ip_address"] == "203.0.113.9"
        assert listed[0]["request_path"] == URL


class TestLeavesAlone:
    def test_switching_off_changes_no_record(self, admin_client, org_a, admin_profile):
        account = Account.objects.create(name="Acme", org=org_a)
        lead = Lead.objects.create(
            title="Lead", first_name="A", last_name="B", org=org_a
        )
        case = Case.objects.create(
            name="Ticket", status="New", priority="Normal", org=org_a, account=account
        )
        invoice = Invoice.objects.create(
            org=org_a, account=account, invoice_title="Work"
        )
        task = Task.objects.create(
            title="Task", status="New", priority="High", org=org_a
        )
        records = [lead, case, invoice, task]
        before = {r.pk: r.updated_at for r in records}
        off = ["leads", "tickets", "invoices", "tasks"]
        assert put(admin_client, off).status_code == 200
        org_a.refresh_from_db()
        assert set(org_a.modules_off) == set(off)
        assert put(admin_client, []).status_code == 200
        for r in records:
            r.refresh_from_db()
            assert r.updated_at == before[r.pk]
        assert Lead.objects.count() == Case.objects.count() == 1
        assert Invoice.objects.count() == Task.objects.count() == 1

    def test_org_settings_cannot_write_module_fields(self, admin_client, org_a):
        response = admin_client.patch(
            "/api/org/settings/",
            {"modules_off": ["leads"], "module_order": ["leads"]},
            format="json",
        )
        assert response.status_code == 200
        org_a.refresh_from_db()
        assert org_a.modules_off == [] and org_a.module_order == []

    def test_another_org_is_untouched(self, admin_client, org_a, org_b):
        set_modules_off(org_b, "goals")
        assert put(admin_client, ["tickets"], ["leads", "deals"]).status_code == 200
        org_a.refresh_from_db()
        assert org_a.modules_off == ["tickets"]
        assert org_a.module_order == ["leads", "deals"]
        org_b.refresh_from_db()
        assert org_b.modules_off == ["goals"]
        assert org_b.module_order == [] and org_b.modules_on_at == {}
        assert not SecurityAuditLog.objects.filter(org=org_b)


@pytest.mark.postgres_only
def test_refusals_see_rows_under_rls(admin_client, org_a):
    """Skipped on SQLite. Under a non-superuser role an empty context matches no
    rows, so a refusal proves the request set the org context itself."""
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    form(org_a, "Contact us")
    InboundMailbox.objects.create(org=org_a, address="help@acme.test")
    clear_rls_context()
    response = put(admin_client, ["leads"])
    assert response.status_code == 400
    assert "Contact us" in response.json()["off"][0]
    response = put(admin_client, ["tickets"])
    assert response.status_code == 400
    assert "help@acme.test" in response.json()["off"][0]
