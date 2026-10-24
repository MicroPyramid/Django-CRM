"""``GET /api/leads/response-times/``: per-person first-response numbers.

A lead's response time is ``first_response_at - created_at``. A row counts the
leads its person answered first inside the window (the last ``days`` days of
the org's calendar, today included) that arrived at or after the org's
``lead_response_since``. An admin gets a row for every active member; anyone
else gets only their own. The tests set the response fields directly.
"""

from datetime import datetime, time, timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone

from common.models import Profile, User
from common.org_time import org_timezone
from common.testing import _make_authenticated_client, rls_org
from leads.models import Lead
from leads.response import _median_in_python

URL = "/api/leads/response-times/"

NOW = timezone.now()
STAMP = NOW - timedelta(days=60)
ROW_KEYS = {
    "profile",
    "name",
    "answered",
    "median_seconds",
    "within_5_minutes",
    "within_1_hour",
    "unanswered_now",
}


@pytest.fixture
def org(org_a):
    org_a.lead_response_since = STAMP
    org_a.save(update_fields=["lead_response_since"])
    return org_a


def _member(org, email, name="", role="USER", is_active=True):
    user = User.objects.create_user(email=email, password="x", name=name)
    profile = Profile.objects.create(user=user, org=org, role=role, is_active=is_active)
    return SimpleNamespace(
        profile=profile, client=_make_authenticated_client(user, org, profile)
    )


@pytest.fixture
def colleague(org):
    return _member(org, "colleague@test.com", name="Maria Lopez")


def _lead(org, *, created_at, assigned=(), **fields):
    fields.setdefault("status", "in process")
    with rls_org(org):
        lead = Lead.objects.create(org=org, first_name="Ada", **fields)
        Lead.objects.filter(pk=lead.pk).update(created_at=created_at)
        for profile in assigned:
            lead.assigned_to.add(profile)
    lead.refresh_from_db()
    return lead


def _answered(org, by, seconds, *, at=NOW - timedelta(days=1), **fields):
    """A lead ``by`` first answered at ``at``, ``seconds`` after it arrived."""
    return _lead(
        org,
        created_at=at - timedelta(seconds=seconds),
        first_response_at=at,
        first_response_by=by,
        last_outbound_at=at,
        **fields,
    )


def _rows(response):
    assert response.status_code == 200, response.data
    return response.data["rows"]


def _row_for(response, profile):
    (row,) = [row for row in _rows(response) if row["profile"] == str(profile.id)]
    return row


# --------------------------------------------------------------- who sees what


def test_an_admin_gets_a_row_for_every_active_member(
    org, org_b, admin_client, admin_profile, user_profile, colleague, profile_b
):
    admin_profile.user.name = "Zed Admin"
    admin_profile.user.save(update_fields=["name"])
    _member(org, "gone@test.com", name="Gone", is_active=False)

    rows = _rows(admin_client.get(URL))

    assert [row["name"] for row in rows] == [
        "Maria Lopez",
        "user",
        "Zed Admin",
    ]
    assert {row["profile"] for row in rows} == {
        str(admin_profile.id),
        str(user_profile.id),
        str(colleague.profile.id),
    }
    assert all(set(row) == ROW_KEYS for row in rows)


def test_a_member_gets_only_their_own_row(org, user_client, user_profile, colleague):
    _answered(org, colleague.profile, 30)
    rows = _rows(user_client.get(URL))
    assert [row["profile"] for row in rows] == [str(user_profile.id)]


def test_a_member_who_answers_a_lead_they_do_not_own_is_its_responder(
    org, user_client, user_profile, colleague, admin_profile
):
    """Review Focus 4. The lead is the admin's, assigned to the member, so the
    member can open it without owning it. The member called first: the
    number is theirs, and the colleague's numbers stay out of their view."""
    lead = _answered(org, user_profile, 90, assigned=[user_profile])
    Lead.objects.filter(pk=lead.pk).update(created_by=admin_profile.user)
    _answered(org, colleague.profile, 30)

    (row,) = _rows(user_client.get(URL))

    assert row["profile"] == str(user_profile.id)
    assert row["answered"] == 1
    assert row["median_seconds"] == 90


def test_another_orgs_admin_sees_only_their_own_org(
    org, org_b, org_b_client, profile_b, user_profile
):
    """The org A lead names org B's admin as its responder, and org B's stamp
    is as old as org A's: only the org filter on the leads keeps it out of
    org B's row."""
    org_b.lead_response_since = STAMP
    org_b.save(update_fields=["lead_response_since"])
    _answered(org, user_profile, 30)
    _answered(org, profile_b, 30)
    rows = _rows(org_b_client.get(URL))
    assert [row["profile"] for row in rows] == [str(profile_b.id)]
    assert rows[0]["answered"] == 0


def test_a_lead_answered_by_someone_from_another_org_makes_no_row(
    org, admin_client, profile_b
):
    _answered(org, profile_b, 30)
    profiles = {row["profile"] for row in _rows(admin_client.get(URL))}
    assert str(profile_b.id) not in profiles


def test_anonymous_is_refused(unauthenticated_client):
    assert unauthenticated_client.get(URL).status_code in (401, 403)


# ------------------------------------------------------------------ the numbers


def test_the_numbers_on_a_fixed_set(org, admin_client, user_profile, colleague):
    for seconds in (60, 120, 600, 4000):
        _answered(org, user_profile, seconds)
    # Outside the 30-day window, and from before the stamp: neither counts.
    _answered(org, user_profile, 5, at=NOW - timedelta(days=40))
    _lead(
        org,
        created_at=STAMP - timedelta(days=1),
        first_response_at=NOW - timedelta(days=2),
        first_response_by=user_profile,
    )
    _answered(org, colleague.profile, 30)

    response = admin_client.get(URL)

    assert _row_for(response, user_profile) == {
        "profile": str(user_profile.id),
        "name": "user",
        "answered": 4,
        "median_seconds": 360,
        "within_5_minutes": 50,
        "within_1_hour": 75,
        "unanswered_now": 0,
    }
    colleague_row = _row_for(response, colleague.profile)
    assert colleague_row["answered"] == 1
    assert colleague_row["median_seconds"] == 30
    assert colleague_row["within_5_minutes"] == 100
    assert colleague_row["within_1_hour"] == 100


def test_someone_whose_name_was_cleared_reads_as_their_email(
    org, user_client, user_profile
):
    User.objects.filter(pk=user_profile.user_id).update(name="")
    assert _rows(user_client.get(URL))[0]["name"] == "user@test.com"


def test_an_odd_count_takes_the_middle_value(org, user_client, user_profile):
    for seconds in (10, 500, 9000):
        _answered(org, user_profile, seconds)
    assert _rows(user_client.get(URL))[0]["median_seconds"] == 500


def test_five_minutes_and_one_hour_are_inclusive(org, user_client, user_profile):
    for seconds in (300, 301, 3600, 3601):
        _answered(org, user_profile, seconds)
    (row,) = _rows(user_client.get(URL))
    assert row["within_5_minutes"] == 25
    assert row["within_1_hour"] == 75


def test_percentages_round_down(org, user_client, user_profile):
    for seconds in (10, 20, 9000):
        _answered(org, user_profile, seconds)
    (row,) = _rows(user_client.get(URL))
    assert row["within_5_minutes"] == 66
    assert row["within_1_hour"] == 66


def test_someone_who_answered_nothing_has_zeros_and_no_median(
    org, user_client, user_profile
):
    assert _rows(user_client.get(URL)) == [
        {
            "profile": str(user_profile.id),
            "name": "user",
            "answered": 0,
            "median_seconds": None,
            "within_5_minutes": 0,
            "within_1_hour": 0,
            "unanswered_now": 0,
        }
    ]


def test_a_response_logged_before_the_lead_existed_counts_as_instant(
    org, user_client, user_profile
):
    """Task 2 clamps ``first_response_at`` to ``created_at``, so the earliest
    possible response time is zero."""
    at = NOW - timedelta(days=1)
    _lead(org, created_at=at, first_response_at=at, first_response_by=user_profile)
    (row,) = _rows(user_client.get(URL))
    assert row["median_seconds"] == 0
    assert row["within_5_minutes"] == 100


def test_unanswered_now_counts_waiting_leads_assigned_to_each_person(
    org, admin_client, user_profile, colleague
):
    recent = NOW - timedelta(hours=2)
    _lead(org, created_at=recent, assigned=[user_profile])
    _lead(org, created_at=recent, assigned=[user_profile, colleague.profile])
    _lead(org, created_at=recent, assigned=[user_profile], last_outbound_at=NOW)
    _lead(org, created_at=recent, assigned=[user_profile], status="closed")
    _lead(org, created_at=STAMP - timedelta(days=5), assigned=[colleague.profile])
    _lead(org, created_at=recent)

    response = admin_client.get(URL)

    assert _row_for(response, user_profile)["unanswered_now"] == 2
    assert _row_for(response, colleague.profile)["unanswered_now"] == 1


# ------------------------------------------------------------------ the window


def test_days_defaults_to_30_and_since_is_the_orgs_date(org, user_client):
    org.timezone = "Pacific/Kiritimati"
    org.save(update_fields=["timezone"])
    with org_timezone(org):
        today = timezone.localdate()
    response = user_client.get(URL)
    assert response.status_code == 200
    assert response.data["since"] == (today - timedelta(days=29)).isoformat()


@pytest.mark.parametrize("days", ["7", "30", "90"])
def test_days_from_7_to_90_are_accepted(org, user_client, days):
    response = user_client.get(URL, {"days": days})
    assert response.status_code == 200
    with org_timezone(org):
        expected = timezone.localdate() - timedelta(days=int(days) - 1)
    assert response.data["since"] == expected.isoformat()


@pytest.mark.parametrize("days", ["6", "91", "0", "-30", "abc", "7.5", "1e2"])
def test_days_outside_7_to_90_are_refused(org, user_client, days):
    response = user_client.get(URL, {"days": days})
    assert response.status_code == 400
    assert "days" in response.data


def test_the_window_starts_at_the_orgs_midnight(org, user_client, user_profile):
    org.timezone = "Asia/Kolkata"
    org.save(update_fields=["timezone"])
    with org_timezone(org):
        start = datetime.combine(
            timezone.localdate() - timedelta(days=6),
            time.min,
            tzinfo=timezone.get_current_timezone(),
        )
    _answered(org, user_profile, 60, at=start)
    _answered(org, user_profile, 60, at=start - timedelta(seconds=1))
    (row,) = _rows(user_client.get(URL, {"days": "7"}))
    assert row["answered"] == 1


# ------------------------------------------------------------------ the median


def _fixed_set(org, first, second):
    """Odd and even counts, with microseconds, so interpolation is exercised."""
    for seconds in (12.5, 61, 300.000002, 7200):
        _answered(org, first, seconds)
    for seconds in (3, 45.25, 900):
        _answered(org, second, seconds)
    return Lead.objects.filter(org=org, first_response_by__isnull=False)


def test_the_python_median_on_a_fixed_set(org, user_profile, colleague):
    queryset = _fixed_set(org, user_profile, colleague.profile)
    assert _median_in_python(queryset) == {
        user_profile.id: timedelta(seconds=180, microseconds=500001),
        colleague.profile.id: timedelta(seconds=45, microseconds=250000),
    }
