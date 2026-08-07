"""Whose day a ticket lands on, when UTC and the org's timezone disagree.

Every chart on the service dashboard is a list of buckets labelled with a
calendar date. This module used to cut those buckets at UTC midnight, and did
it consistently, which is what made it hard to see: a Kolkata org's tickets
opened between midnight and 05:30 were all filed under the day before, so the
chart showed a quiet morning and then a spike that never happened, and the
backlog line dropped a day early.

The rest of the app moved to per-org days when ``Org.timezone`` shipped (see
``common/tests/test_timezone_dates.py``); the analytics buckets were the last
thing still cutting on UTC.

Every test here is paired with its mirror, one org east of UTC and one west, at
the same instant. A boundary computed globally rather than per org fails at
least one of each pair, whichever direction it is wrong in.
"""

from __future__ import annotations

import datetime
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.utils import timezone

from cases import analytics
from cases.models import Case
from common.org_time import activate_org_timezone

# 20:00 UTC on 6 August is 01:30 on the 7th in Kolkata and 16:00 on the 6th in
# New York. Every assertion below turns on those being different days.
AFTER_LOCAL_MIDNIGHT = datetime.datetime(
    2026, 8, 6, 20, 0, tzinfo=datetime.timezone.utc
)
# Midnight on 7 August in Kolkata, so a window anchored here covers exactly one
# of that org's days.
KOLKATA_MIDNIGHT = datetime.datetime(2026, 8, 6, 18, 30, tzinfo=datetime.timezone.utc)
_DAY = datetime.timedelta(days=1)


def _utc(year, month, day, hour=0, minute=0):
    return datetime.datetime(
        year, month, day, hour, minute, tzinfo=datetime.timezone.utc
    )


@contextmanager
def _as_org(tz_name):
    """Run a block with an org's timezone active, the way the middleware does."""
    activate_org_timezone(SimpleNamespace(timezone=tz_name))
    try:
        yield
    finally:
        timezone.deactivate()


@pytest.fixture
def cases_qs(org_a):
    return Case.objects.filter(org=org_a)


def _case(org, name="Printer down", **fields):
    """A case with its server-set timestamps forced to the instants we want."""
    case = Case.objects.create(org=org, name=name, status="New", priority="Normal")
    if fields:
        Case.objects.filter(pk=case.pk).update(**fields)
    return case


class TestBucketEdges:
    """The window is the same instant either way; the days inside it are not."""

    def test_east_of_utc_one_local_day_is_one_bucket(self):
        with _as_org("Asia/Kolkata"):
            out = analytics._bucket_dates(KOLKATA_MIDNIGHT, KOLKATA_MIDNIGHT + _DAY)

        assert [d.isoformat() for d in out] == ["2026-08-07"]

    def test_west_of_utc_the_same_window_straddles_two(self):
        # 18:30 UTC is 14:30 in New York, so this window runs from one
        # afternoon to the next and genuinely touches two of that org's days.
        with _as_org("America/New_York"):
            out = analytics._bucket_dates(KOLKATA_MIDNIGHT, KOLKATA_MIDNIGHT + _DAY)

        assert [d.isoformat() for d in out] == ["2026-08-06", "2026-08-07"]


@pytest.mark.django_db
class TestFirstResponseSeries:
    """`compute_frt` buckets by when the ticket was opened."""

    def _one_ticket(self, org):
        return _case(
            org,
            created_at=AFTER_LOCAL_MIDNIGHT,
            first_response_at=AFTER_LOCAL_MIDNIGHT + datetime.timedelta(hours=2),
            sla_first_response_hours=4,
        )

    def _series(self, cases_qs):
        out = analytics.compute_frt(cases_qs, _utc(2026, 8, 5), _utc(2026, 8, 9))
        return {row["bucket"]: row for row in out["series"]}

    def test_east_of_utc_an_after_midnight_ticket_counts_on_the_new_day(
        self, org_a, cases_qs
    ):
        self._one_ticket(org_a)

        with _as_org("Asia/Kolkata"):
            series = self._series(cases_qs)

        assert series["2026-08-07"]["count"] == 1
        assert series["2026-08-07"]["median"] == pytest.approx(2.0)
        assert series["2026-08-06"]["count"] == 0

    def test_west_of_utc_the_same_ticket_is_still_the_day_befores(
        self, org_a, cases_qs
    ):
        self._one_ticket(org_a)

        with _as_org("America/New_York"):
            series = self._series(cases_qs)

        assert series["2026-08-06"]["count"] == 1
        assert series["2026-08-07"]["count"] == 0


@pytest.mark.django_db
class TestBacklog:
    """Backlog asks "was this open at the end of day D", so the end of the day
    is the whole answer."""

    def _resolved_after_midnight(self, org):
        return _case(
            org,
            created_at=_utc(2026, 8, 1),
            resolved_at=AFTER_LOCAL_MIDNIGHT,
            status="Closed",
        )

    def _by_day(self, cases_qs):
        out = analytics.compute_backlog(cases_qs, _utc(2026, 8, 5), _utc(2026, 8, 9))
        return {row["date"]: row for row in out["series"]}

    def test_east_of_utc_it_is_still_open_at_the_end_of_the_day_before(
        self, org_a, cases_qs
    ):
        # Resolved at 01:30 on the 7th in Kolkata, so at the end of the 6th
        # this ticket was still in the queue.
        self._resolved_after_midnight(org_a)

        with _as_org("Asia/Kolkata"):
            days = self._by_day(cases_qs)

        assert days["2026-08-06"]["open_count"] == 1
        assert days["2026-08-07"]["open_count"] == 0

    def test_west_of_utc_the_same_ticket_had_already_closed(self, org_a, cases_qs):
        # 16:00 on the 6th in New York: closed well before that day ended.
        self._resolved_after_midnight(org_a)

        with _as_org("America/New_York"):
            days = self._by_day(cases_qs)

        assert days["2026-08-06"]["open_count"] == 0

    def test_the_drilldown_returns_what_the_chart_counted(self, org_a, cases_qs):
        """A bar that opens a list of a different length is worse than no bar.

        The series and the drilldown compute the end of the day separately, so
        this is the one assertion that catches them drifting apart.
        """
        case = self._resolved_after_midnight(org_a)

        with _as_org("Asia/Kolkata"):
            days = self._by_day(cases_qs)
            ids = list(
                analytics.case_ids_for_metric(
                    "backlog",
                    cases_qs,
                    _utc(2026, 8, 5),
                    _utc(2026, 8, 9),
                    bucket="2026-08-06",
                )
            )

        assert days["2026-08-06"]["open_count"] == len(ids) == 1
        assert ids == [case.id]

    def test_the_drilldown_is_empty_where_the_chart_counted_nothing(
        self, org_a, cases_qs
    ):
        self._resolved_after_midnight(org_a)

        with _as_org("America/New_York"):
            ids = list(
                analytics.case_ids_for_metric(
                    "backlog",
                    cases_qs,
                    _utc(2026, 8, 5),
                    _utc(2026, 8, 9),
                    bucket="2026-08-06",
                )
            )

        assert ids == []


@pytest.mark.django_db
class TestServiceOverviewWindow:
    """The dashboard's window is "the last N days", which is only a fixed
    number of buckets if the days are cut where the org cuts them."""

    def _volume(self, org_a, cases_qs, tz_name):
        with patch("django.utils.timezone.now", return_value=AFTER_LOCAL_MIDNIGHT):
            with _as_org(tz_name):
                return analytics.compute_service_overview(cases_qs, org_a.id, days=2)[
                    "volume"
                ]

    def test_east_of_utc_the_last_bucket_is_the_orgs_today(self, org_a, cases_qs):
        volume = self._volume(org_a, cases_qs, "Asia/Kolkata")

        assert [row["date"] for row in volume] == ["2026-08-06", "2026-08-07"]

    def test_west_of_utc_today_has_not_arrived_yet(self, org_a, cases_qs):
        volume = self._volume(org_a, cases_qs, "America/New_York")

        assert [row["date"] for row in volume] == ["2026-08-05", "2026-08-06"]

    def test_an_after_midnight_ticket_counts_on_the_orgs_today(self, org_a, cases_qs):
        _case(org_a, created_at=AFTER_LOCAL_MIDNIGHT)

        volume = self._volume(org_a, cases_qs, "Asia/Kolkata")

        assert {row["date"]: row["opened"] for row in volume} == {
            "2026-08-06": 0,
            "2026-08-07": 1,
        }


@pytest.mark.django_db
class TestDateOnlyWindowIsTheOrgsDay:
    """`?from=2026-08-06&to=2026-08-06` names a day, not an instant.

    Anchoring it to UTC midnight asked a Kolkata org about the 24 hours running
    from 05:30 on the 6th to 05:30 on the 7th: a window that is neither the day
    the user picked nor any whole day at all.
    """

    url = "/api/cases/analytics/frt/?from=2026-08-06&to=2026-08-06"

    @pytest.fixture
    def two_tickets(self, org_a):
        """One in each org's 6 August, and neither in both.

        19:00 UTC on the 5th is 00:30 on the 6th in Kolkata and 15:00 on the
        5th in New York; 19:00 UTC on the 6th is 00:30 on the 7th in Kolkata
        and 15:00 on the 6th in New York.
        """
        return (
            _case(org_a, name="Kolkata's sixth", created_at=_utc(2026, 8, 5, 19)),
            _case(org_a, name="New York's sixth", created_at=_utc(2026, 8, 6, 19)),
        )

    def _ids_in_window(self, admin_client, org_a, tz_name):
        org_a.timezone = tz_name
        org_a.save(update_fields=["timezone"])
        response = admin_client.get(self.url)
        assert response.status_code == 200
        return set(response.data["case_ids"])

    def test_east_of_utc(self, admin_client, org_a, two_tickets):
        kolkatas, new_yorks = two_tickets

        ids = self._ids_in_window(admin_client, org_a, "Asia/Kolkata")

        assert str(kolkatas.id) in ids
        assert str(new_yorks.id) not in ids

    def test_west_of_utc(self, admin_client, org_a, two_tickets):
        kolkatas, new_yorks = two_tickets

        ids = self._ids_in_window(admin_client, org_a, "America/New_York")

        assert str(new_yorks.id) in ids
        assert str(kolkatas.id) not in ids
