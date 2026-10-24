"""Unanswered leads: the rule, the list filter, the lead payload, the export,
saved views and the two dashboard counts.

The rule, with ``arrival_at = coalesce(last_enquiry_at, created_at)``: a lead
is unanswered when its status is assigned, in process or recycled, it has no
outbound since it arrived, and it arrived at or after the org's
``lead_response_since``. ``waiting_since`` is ``created_at`` when nothing
outbound was ever logged and the lead itself is newer than the stamp, else
``arrival_at``. The tests set the response fields directly.
"""

import csv
import io
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from common.models import Profile, User
from common.saved_views import LISTS
from common.testing import _make_authenticated_client, rls_org, set_modules_off
from leads.models import Lead
from leads.response import unanswered, unanswered_summary, with_response_state

LIST_URL = "/api/leads/"
EXPORT_URL = "/api/leads/export/"

NOW = timezone.now()
STAMP = NOW - timedelta(days=10)


@pytest.fixture
def org(org_a):
    org_a.lead_response_since = STAMP
    org_a.save(update_fields=["lead_response_since"])
    return org_a


@pytest.fixture
def colleague(org):
    user = User.objects.create_user(email="colleague@test.com", password="x")
    profile = Profile.objects.create(user=user, org=org, role="USER", is_active=True)
    return SimpleNamespace(
        profile=profile, client=_make_authenticated_client(user, org, profile)
    )


def _lead(org, *, created_at=NOW - timedelta(days=1), assigned=(), **fields):
    fields.setdefault("status", "assigned")
    fields.setdefault("first_name", "Ada")
    with rls_org(org):
        lead = Lead.objects.create(org=org, **fields)
        # `created_at` is auto_now_add, so only an update can backdate it.
        Lead.objects.filter(pk=lead.pk).update(created_at=created_at)
        for profile in assigned:
            lead.assigned_to.add(profile)
    lead.refresh_from_db()
    return lead


def _state(lead, org):
    row = with_response_state(Lead.objects.filter(pk=lead.pk), org).get()
    return row.is_unanswered, row.waiting_since


def _open_rows(response):
    assert response.status_code == 200, response.data
    return response.data["open_leads"]["open_leads"]


def _when(value):
    return datetime.fromisoformat(value) if value else None


# ------------------------------------------------------------------ the rule


class TestTheRule:
    def test_a_new_lead_nobody_answered_waits_since_it_arrived(self, org):
        lead = _lead(org)
        assert _state(lead, org) == (True, lead.created_at)

    def test_an_answered_lead_is_not_waiting(self, org):
        lead = _lead(org, last_outbound_at=NOW - timedelta(hours=20))
        assert _state(lead, org) == (False, None)

    def test_answered_then_enquired_again_waits_since_the_enquiry(self, org):
        enquiry = NOW - timedelta(hours=2)
        lead = _lead(
            org,
            last_outbound_at=NOW - timedelta(hours=20),
            last_enquiry_at=enquiry,
        )
        assert _state(lead, org) == (True, enquiry)

    def test_a_new_lead_that_asks_twice_still_waits_since_it_arrived(self, org):
        lead = _lead(org, last_enquiry_at=NOW - timedelta(hours=2))
        assert _state(lead, org) == (True, lead.created_at)

    def test_an_outbound_at_the_moment_of_arrival_answers_it(self, org):
        arrived = NOW - timedelta(hours=3)
        lead = _lead(org, created_at=arrived, last_outbound_at=arrived)
        assert _state(lead, org) == (False, None)

    @pytest.mark.parametrize("status", ["assigned", "in process", "recycled"])
    def test_open_statuses_can_wait(self, org, status):
        assert _state(_lead(org, status=status), org)[0] is True

    @pytest.mark.parametrize("status", ["converted", "closed"])
    def test_converted_and_closed_leads_never_wait(self, org, status):
        assert _state(_lead(org, status=status), org) == (False, None)

    def test_a_lead_from_before_the_stamp_is_left_out(self, org):
        lead = _lead(org, created_at=STAMP - timedelta(days=400))
        assert _state(lead, org) == (False, None)

    def test_a_lead_arriving_exactly_at_the_stamp_counts(self, org):
        lead = _lead(org, created_at=STAMP)
        assert _state(lead, org) == (True, STAMP)

    def test_an_old_lead_that_enquired_before_the_stamp_is_left_out(self, org):
        lead = _lead(
            org,
            created_at=STAMP - timedelta(days=400),
            last_enquiry_at=STAMP - timedelta(days=1),
        )
        assert _state(lead, org) == (False, None)

    def test_an_old_lead_enquiring_after_the_stamp_waits_since_that_enquiry(self, org):
        """Review Focus 3: years-old and never answered, then asks again after
        the release. It is unanswered, waiting since the new enquiry, not since
        it was created."""
        enquiry = NOW - timedelta(hours=5)
        lead = _lead(
            org, created_at=STAMP - timedelta(days=700), last_enquiry_at=enquiry
        )
        assert _state(lead, org) == (True, enquiry)

    def test_an_old_lead_answered_long_ago_waits_since_its_new_enquiry(self, org):
        enquiry = NOW - timedelta(hours=5)
        lead = _lead(
            org,
            created_at=STAMP - timedelta(days=700),
            last_outbound_at=STAMP - timedelta(days=600),
            last_enquiry_at=enquiry,
        )
        assert _state(lead, org) == (True, enquiry)

    def test_the_stamp_is_the_orgs_own(self, org, org_b):
        """Org B's stamp is in the future, so the same kind of lead does not
        count there while it does in org A."""
        org_b.lead_response_since = NOW + timedelta(days=1)
        org_b.save(update_fields=["lead_response_since"])
        mine, theirs = _lead(org), _lead(org_b)
        assert _state(mine, org)[0] is True
        assert _state(theirs, org_b)[0] is False

    def test_the_annotation_never_reaches_another_org(self, org, org_b):
        _lead(org_b)
        assert (
            not with_response_state(Lead.objects.all(), org).filter(org=org_b).exists()
        )
        assert list(unanswered(Lead.objects.all(), org)) == []

    def test_unanswered_returns_exactly_the_waiting_leads(self, org):
        waiting = _lead(org, first_name="Waiting")
        _lead(org, first_name="Answered", last_outbound_at=NOW)
        _lead(org, first_name="Closed", status="closed")
        assert [lead.pk for lead in unanswered(Lead.objects.all(), org)] == [waiting.pk]

    def test_the_summary_counts_and_finds_the_oldest(self, org):
        _lead(org, created_at=NOW - timedelta(hours=1))
        oldest = _lead(org, created_at=NOW - timedelta(hours=9))
        _lead(org, last_outbound_at=NOW)
        assert unanswered_summary(Lead.objects.all(), org) == {
            "count": 2,
            "oldest_since": oldest.created_at,
        }

    def test_the_summary_of_nothing(self, org):
        assert unanswered_summary(Lead.objects.none(), org) == {
            "count": 0,
            "oldest_since": None,
        }


# ------------------------------------------------------------ the lead list


class TestTheList:
    def test_unanswered_true_lists_only_waiting_leads_oldest_first(
        self, org, admin_client
    ):
        middle = _lead(org, first_name="Middle", created_at=NOW - timedelta(hours=5))
        newest = _lead(org, first_name="Newest", created_at=NOW - timedelta(hours=1))
        oldest = _lead(org, first_name="Oldest", created_at=NOW - timedelta(hours=9))
        _lead(org, first_name="Answered", last_outbound_at=NOW)
        _lead(org, first_name="Old", created_at=STAMP - timedelta(days=30))

        rows = _open_rows(admin_client.get(LIST_URL, {"unanswered": "true"}))

        assert [row["id"] for row in rows] == [
            str(oldest.id),
            str(middle.id),
            str(newest.id),
        ]
        assert all(row["is_unanswered"] for row in rows)
        assert [_when(row["waiting_since"]) for row in rows] == [
            oldest.created_at,
            middle.created_at,
            newest.created_at,
        ]

    def test_the_wait_orders_by_waiting_since_not_by_creation(self, org, admin_client):
        """Created first but answered, then enquired an hour ago: it has waited
        less than a lead created three hours ago."""
        requeued = _lead(
            org,
            first_name="Requeued",
            created_at=NOW - timedelta(days=3),
            last_outbound_at=NOW - timedelta(days=2),
            last_enquiry_at=NOW - timedelta(hours=1),
        )
        fresh = _lead(org, first_name="Fresh", created_at=NOW - timedelta(hours=3))
        rows = _open_rows(admin_client.get(LIST_URL, {"unanswered": "true"}))
        assert [row["id"] for row in rows] == [str(fresh.id), str(requeued.id)]

    def test_without_the_filter_both_kinds_come_back_with_their_state(
        self, org, admin_client
    ):
        waiting = _lead(org, first_name="Waiting")
        answered = _lead(org, first_name="Answered", last_outbound_at=NOW)
        rows = {row["id"]: row for row in _open_rows(admin_client.get(LIST_URL))}
        assert rows[str(waiting.id)]["is_unanswered"] is True
        assert _when(rows[str(waiting.id)]["waiting_since"]) == waiting.created_at
        assert rows[str(answered.id)]["is_unanswered"] is False
        assert rows[str(answered.id)]["waiting_since"] is None

    def test_anything_but_true_leaves_the_list_unfiltered(self, org, admin_client):
        _lead(org, first_name="Waiting")
        _lead(org, first_name="Answered", last_outbound_at=NOW)
        rows = _open_rows(admin_client.get(LIST_URL, {"unanswered": "false"}))
        assert len(rows) == 2

    def test_combines_with_assigned_to(self, org, admin_client, user_profile):
        mine = _lead(org, first_name="Mine", assigned=[user_profile])
        _lead(org, first_name="Unassigned")
        _lead(
            org,
            first_name="Mine but answered",
            assigned=[user_profile],
            last_outbound_at=NOW,
        )
        rows = _open_rows(
            admin_client.get(
                LIST_URL,
                {"unanswered": "true", "assigned_to": str(user_profile.id)},
            )
        )
        assert [row["id"] for row in rows] == [str(mine.id)]

    def test_a_lead_with_two_assignees_is_listed_once(
        self, org, admin_client, user_profile, colleague
    ):
        both = _lead(org, assigned=[user_profile, colleague.profile])
        rows = _open_rows(
            admin_client.get(
                LIST_URL,
                {
                    "unanswered": "true",
                    "assigned_to": [str(user_profile.id), str(colleague.profile.id)],
                },
            )
        )
        assert [row["id"] for row in rows] == [str(both.id)]

    def test_a_member_sees_only_the_waiting_leads_they_can_open(
        self, org, user_client, user_profile, admin_client
    ):
        mine = _lead(org, first_name="Mine", assigned=[user_profile])
        _lead(org, first_name="Someone else's")

        member_rows = _open_rows(user_client.get(LIST_URL, {"unanswered": "true"}))
        admin_rows = _open_rows(admin_client.get(LIST_URL, {"unanswered": "true"}))

        assert [row["id"] for row in member_rows] == [str(mine.id)]
        assert len(admin_rows) == 2

    def test_another_orgs_waiting_leads_never_appear(self, org, org_b, admin_client):
        _lead(org_b)
        assert _open_rows(admin_client.get(LIST_URL, {"unanswered": "true"})) == []

    def test_the_next_offset_follows_the_waiting_order(self, org, admin_client):
        for hours in range(1, 13):
            _lead(org, first_name=f"L{hours}", created_at=NOW - timedelta(hours=hours))
        first = admin_client.get(LIST_URL, {"unanswered": "true", "limit": 5})
        page = first.data["open_leads"]
        assert page["leads_count"] == 12
        assert page["offset"] == 5
        assert [row["first_name"] for row in page["open_leads"]] == [
            "L12",
            "L11",
            "L10",
            "L9",
            "L8",
        ]
        last = admin_client.get(
            LIST_URL, {"unanswered": "true", "limit": 5, "offset": 10}
        ).data["open_leads"]
        assert [row["first_name"] for row in last["open_leads"]] == ["L2", "L1"]
        assert last["offset"] is None


# ---------------------------------------------------------- the lead payload


RESPONSE_FIELDS = {
    "first_response_at",
    "first_response_by",
    "first_response_by_details",
    "last_outbound_at",
    "waiting_since",
    "is_unanswered",
}


class TestThePayload:
    def test_list_rows_carry_the_response_fields(self, org, admin_client, colleague):
        colleague.profile.user.name = "Maria Lopez"
        colleague.profile.user.save(update_fields=["name"])
        answered_at = NOW - timedelta(hours=20)
        lead = _lead(
            org,
            first_response_at=answered_at,
            first_response_by=colleague.profile,
            last_outbound_at=answered_at,
        )
        (row,) = _open_rows(admin_client.get(LIST_URL))
        assert RESPONSE_FIELDS <= set(row)
        assert row["id"] == str(lead.id)
        assert _when(row["first_response_at"]) == answered_at
        assert str(row["first_response_by"]) == str(colleague.profile.id)
        assert row["first_response_by_details"] == {
            "id": str(colleague.profile.id),
            "name": "Maria Lopez",
        }
        assert _when(row["last_outbound_at"]) == answered_at
        assert row["is_unanswered"] is False
        assert row["waiting_since"] is None

    def test_a_responder_whose_name_was_cleared_reads_as_their_email(
        self, org, admin_client, colleague
    ):
        User.objects.filter(pk=colleague.profile.user_id).update(name="")
        _lead(org, first_response_at=NOW, first_response_by=colleague.profile)
        (row,) = _open_rows(admin_client.get(LIST_URL))
        assert row["first_response_by_details"]["name"] == "colleague@test.com"

    def test_an_unanswered_lead_has_no_responder(self, org, admin_client):
        _lead(org)
        (row,) = _open_rows(admin_client.get(LIST_URL))
        assert row["first_response_at"] is None
        assert row["first_response_by"] is None
        assert row["first_response_by_details"] is None
        assert row["last_outbound_at"] is None
        assert row["is_unanswered"] is True

    def test_detail_carries_the_response_fields(self, org, admin_client):
        enquiry = NOW - timedelta(hours=2)
        lead = _lead(
            org, last_outbound_at=NOW - timedelta(hours=9), last_enquiry_at=enquiry
        )
        body = admin_client.get(f"{LIST_URL}{lead.id}/").data["lead_obj"]
        assert RESPONSE_FIELDS <= set(body)
        assert body["is_unanswered"] is True
        assert _when(body["waiting_since"]) == enquiry

    def test_the_comment_post_answers_with_the_fields_too(self, org, admin_client):
        lead = _lead(org)
        body = admin_client.post(
            f"{LIST_URL}{lead.id}/", {"comment": "Rang, no answer"}, format="json"
        ).data["lead_obj"]
        assert body["is_unanswered"] is True

    def test_the_response_fields_cannot_be_written(self, org, admin_client, colleague):
        lead = _lead(org)
        response = admin_client.patch(
            f"{LIST_URL}{lead.id}/",
            {
                "first_response_at": NOW.isoformat(),
                "first_response_by": str(colleague.profile.id),
                "last_outbound_at": NOW.isoformat(),
                "waiting_since": NOW.isoformat(),
                "is_unanswered": False,
            },
            format="json",
        )
        assert response.status_code == 200, response.data
        lead.refresh_from_db()
        assert lead.first_response_at is None
        assert lead.first_response_by_id is None
        assert lead.last_outbound_at is None
        assert _state(lead, org) == (True, lead.created_at)

    def test_the_responder_costs_no_query_per_row(
        self, org, admin_client, admin_profile, user_profile, colleague
    ):
        """Compared on the same three rows, with and without a first responder,
        so only what this field adds is measured."""

        def queries_for_list():
            with CaptureQueriesContext(connection) as captured:
                assert admin_client.get(LIST_URL).status_code == 200
            return len(captured)

        leads = [_lead(org, first_name=f"L{i}") for i in range(3)]
        without = queries_for_list()
        for lead, profile in zip(
            leads, [admin_profile, user_profile, colleague.profile]
        ):
            Lead.objects.filter(pk=lead.pk).update(
                first_response_at=NOW, first_response_by=profile
            )
        assert queries_for_list() == without


# -------------------------------------------------- export and saved views


def _csv_first_names(response):
    assert response.status_code == 200, response.content
    body = b"".join(response.streaming_content).decode("utf-8")
    rows = list(csv.reader(io.StringIO(body[1:])))
    column = rows[0].index("First name")
    return [row[column] for row in rows[1:]]


class TestExportAndSavedViews:
    def test_the_export_holds_the_unanswered_list_in_its_order(self, org, admin_client):
        _lead(org, first_name="Newer", created_at=NOW - timedelta(hours=1))
        _lead(org, first_name="Older", created_at=NOW - timedelta(hours=8))
        _lead(org, first_name="Answered", last_outbound_at=NOW)
        listed = [
            row["first_name"]
            for row in _open_rows(admin_client.get(LIST_URL, {"unanswered": "true"}))
        ]
        exported = _csv_first_names(
            admin_client.get(EXPORT_URL, {"unanswered": "true"})
        )
        assert listed == exported == ["Older", "Newer"]

    def test_a_members_export_holds_only_their_waiting_leads(
        self, org, user_client, user_profile
    ):
        _lead(org, first_name="Mine", assigned=[user_profile])
        _lead(org, first_name="Not mine")
        assert _csv_first_names(
            user_client.get(EXPORT_URL, {"unanswered": "true"})
        ) == ["Mine"]

    def test_the_unanswered_preset_can_be_saved(self, org, user_client):
        assert "unanswered" in LISTS["leads"][1]
        response = user_client.post(
            "/api/saved-views/",
            {
                "module": "leads",
                "name": "Unanswered",
                "filters": {"unanswered": "true", "open": "true"},
            },
            format="json",
        )
        assert response.status_code == 201, response.data
        assert response.data["filters"] == {
            "unanswered": ["true"],
            "open": ["true"],
        }


# ------------------------------------------------------------ the dashboards


DASHBOARDS = ["/api/dashboard/", "/api/dashboard/today/"]


@pytest.mark.parametrize("url", DASHBOARDS)
class TestDashboardCount:
    def test_an_admin_counts_every_waiting_lead(self, url, org, admin_client):
        _lead(org, created_at=NOW - timedelta(hours=1))
        oldest = _lead(org, created_at=NOW - timedelta(hours=7))
        _lead(org, last_outbound_at=NOW)
        _lead(org, status="closed")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data["unanswered_leads"] == {
            "count": 2,
            "oldest_since": oldest.created_at,
        }

    def test_a_member_counts_only_the_leads_they_can_see(
        self, url, org, user_client, user_profile
    ):
        mine = _lead(org, created_at=NOW - timedelta(hours=1), assigned=[user_profile])
        _lead(org, created_at=NOW - timedelta(hours=7))
        response = user_client.get(url)
        assert response.data["unanswered_leads"] == {
            "count": 1,
            "oldest_since": mine.created_at,
        }

    def test_a_member_with_nothing_visible_counts_nothing(self, url, org, user_client):
        _lead(org)
        assert user_client.get(url).data["unanswered_leads"] == {
            "count": 0,
            "oldest_since": None,
        }

    def test_another_orgs_leads_are_never_counted(self, url, org, org_b, admin_client):
        _lead(org_b)
        assert admin_client.get(url).data["unanswered_leads"]["count"] == 0

    def test_the_old_lead_that_asked_again_counts_from_its_enquiry(
        self, url, org, admin_client
    ):
        enquiry = NOW - timedelta(hours=3)
        _lead(org, created_at=STAMP - timedelta(days=500), last_enquiry_at=enquiry)
        _lead(org, created_at=STAMP - timedelta(days=500))
        assert admin_client.get(url).data["unanswered_leads"] == {
            "count": 1,
            "oldest_since": enquiry,
        }

    def test_with_leads_switched_off_nothing_is_counted(self, url, org, admin_client):
        _lead(org)
        set_modules_off(org, "leads")
        assert admin_client.get(url).data["unanswered_leads"] == {
            "count": 0,
            "oldest_since": None,
        }
