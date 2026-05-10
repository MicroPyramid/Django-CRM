"""Unit tests for the analytics aggregation module.

These hit the pure functions in `cases.analytics` directly so they don't
depend on the request layer. Window math, percentiles, and breach counting
are the things that historically slip; everything else is a thin DB query.
"""

from datetime import datetime, timedelta, timezone as dt_timezone

import pytest
from django.utils import timezone

from cases import analytics
from cases.models import Case
from common.models import Profile, User


def _utc(year, month, day, hour=0):
    return datetime(year, month, day, hour, tzinfo=dt_timezone.utc)


@pytest.fixture
def cases_qs(org_a):
    return Case.objects.filter(org=org_a)


# --------------------------------------------------------------------------
# Helpers


class TestPercentile:
    def test_empty_returns_none(self):
        assert analytics._percentile([], 50) is None

    def test_single_value(self):
        assert analytics._percentile([7.0], 50) == 7.0
        assert analytics._percentile([7.0], 90) == 7.0

    def test_median_even_length(self):
        # Linear interpolation: 50th of [1,2,3,4] = 2.5.
        assert analytics._percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.5

    def test_p90(self):
        # 10 values, p90 = index 8.1 → between values[8] and values[9].
        v = [float(i) for i in range(1, 11)]
        assert analytics._percentile(v, 90) == pytest.approx(9.1)


class TestBucketDates:
    def test_three_day_inclusive(self):
        from_dt = _utc(2026, 5, 1, 0)
        to_dt = _utc(2026, 5, 4, 0)
        out = analytics._bucket_dates(from_dt, to_dt)
        assert [d.isoformat() for d in out] == [
            "2026-05-01",
            "2026-05-02",
            "2026-05-03",
        ]

    def test_zero_window(self):
        from_dt = to_dt = _utc(2026, 5, 1, 0)
        assert analytics._bucket_dates(from_dt, to_dt) == []


# --------------------------------------------------------------------------
# FRT


class TestComputeFrt:
    def test_empty_window(self, cases_qs):
        out = analytics.compute_frt(cases_qs, _utc(2026, 1, 1), _utc(2026, 1, 2))
        assert out["count"] == 0
        assert out["median_hours"] is None
        assert out["p90_hours"] is None
        assert out["breach_count"] == 0

    def test_single_response(self, org_a, cases_qs):
        c = Case.objects.create(
            org=org_a,
            name="One",
            status="New",
            priority="Normal",
            sla_first_response_hours=4,
        )
        # Backdate created_at, set first_response 2h later.
        Case.objects.filter(pk=c.pk).update(
            created_at=_utc(2026, 5, 1, 10),
            first_response_at=_utc(2026, 5, 1, 12),
        )
        out = analytics.compute_frt(cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 2))
        assert out["count"] == 1
        assert out["median_hours"] == pytest.approx(2.0)
        assert out["p90_hours"] == pytest.approx(2.0)
        assert out["breach_count"] == 0

    def test_breach_when_response_exceeds_sla(self, org_a, cases_qs):
        c = Case.objects.create(
            org=org_a,
            name="Slow",
            status="New",
            priority="Normal",
            sla_first_response_hours=1,
        )
        Case.objects.filter(pk=c.pk).update(
            created_at=_utc(2026, 5, 1, 8),
            first_response_at=_utc(2026, 5, 1, 14),
        )
        out = analytics.compute_frt(cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 2))
        assert out["count"] == 1
        assert out["breach_count"] == 1

    def test_open_case_breach_counted_when_overdue(self, org_a, cases_qs):
        c = Case.objects.create(
            org=org_a,
            name="Open",
            status="New",
            priority="Normal",
            sla_first_response_hours=1,
        )
        Case.objects.filter(pk=c.pk).update(
            created_at=timezone.now() - timedelta(hours=5),
        )
        out = analytics.compute_frt(
            cases_qs, timezone.now() - timedelta(days=1), timezone.now()
        )
        assert out["count"] == 0  # No first_response_at → no median bucket.
        assert out["breach_count"] == 1

    def test_series_buckets_by_creation_day(self, org_a, cases_qs):
        c1 = Case.objects.create(
            org=org_a,
            name="A",
            status="New",
            priority="Normal",
            sla_first_response_hours=4,
        )
        c2 = Case.objects.create(
            org=org_a,
            name="B",
            status="New",
            priority="Normal",
            sla_first_response_hours=4,
        )
        Case.objects.filter(pk=c1.pk).update(
            created_at=_utc(2026, 5, 1, 8),
            first_response_at=_utc(2026, 5, 1, 11),
        )
        Case.objects.filter(pk=c2.pk).update(
            created_at=_utc(2026, 5, 2, 8),
            first_response_at=_utc(2026, 5, 2, 14),
        )
        out = analytics.compute_frt(cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 3))
        days = {row["bucket"]: row for row in out["series"]}
        assert days["2026-05-01"]["median"] == pytest.approx(3.0)
        assert days["2026-05-02"]["median"] == pytest.approx(6.0)
        assert days["2026-05-01"]["count"] == 1


# --------------------------------------------------------------------------
# MTTR


class TestComputeMttr:
    def test_empty_window(self, cases_qs):
        out = analytics.compute_mttr(cases_qs, _utc(2026, 1, 1), _utc(2026, 1, 2))
        assert out["count"] == 0
        assert out["mean_hours"] is None
        assert out["by_priority"] == {}

    def test_by_priority_split(self, org_a, cases_qs):
        c1 = Case.objects.create(
            org=org_a, name="U1", status="Closed", priority="Urgent", closed_on="2026-05-01"
        )
        c2 = Case.objects.create(
            org=org_a, name="L1", status="Closed", priority="Low", closed_on="2026-05-02"
        )
        Case.objects.filter(pk=c1.pk).update(
            created_at=_utc(2026, 5, 1, 0), resolved_at=_utc(2026, 5, 1, 4)
        )
        Case.objects.filter(pk=c2.pk).update(
            created_at=_utc(2026, 5, 1, 0), resolved_at=_utc(2026, 5, 2, 0)
        )
        out = analytics.compute_mttr(cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 3))
        assert out["count"] == 2
        assert out["by_priority"]["Urgent"]["mean_hours"] == pytest.approx(4.0)
        assert out["by_priority"]["Low"]["mean_hours"] == pytest.approx(24.0)
        assert out["mean_hours"] == pytest.approx(14.0)

    def test_only_resolved_in_window_counted(self, org_a, cases_qs):
        # Closed before window: ignored.
        c = Case.objects.create(
            org=org_a, name="Old", status="Closed", priority="Low", closed_on="2026-04-01"
        )
        Case.objects.filter(pk=c.pk).update(
            created_at=_utc(2026, 4, 1, 0), resolved_at=_utc(2026, 4, 1, 4)
        )
        out = analytics.compute_mttr(cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 3))
        assert out["count"] == 0


# --------------------------------------------------------------------------
# Backlog


class TestComputeBacklog:
    def test_open_count_steps_with_resolution(self, org_a, cases_qs):
        c1 = Case.objects.create(org=org_a, name="A", status="New", priority="Normal")
        c2 = Case.objects.create(org=org_a, name="B", status="New", priority="Urgent")
        Case.objects.filter(pk=c1.pk).update(created_at=_utc(2026, 5, 1, 0))
        Case.objects.filter(pk=c2.pk).update(created_at=_utc(2026, 5, 1, 0))
        # Resolve c1 on day 2.
        Case.objects.filter(pk=c1.pk).update(resolved_at=_utc(2026, 5, 2, 12))

        out = analytics.compute_backlog(cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 4))
        days = {row["date"]: row for row in out["series"]}
        assert days["2026-05-01"]["open_count"] == 2
        assert days["2026-05-01"]["urgent_count"] == 1
        # End of day 2: c1 resolved, c2 still open.
        assert days["2026-05-02"]["open_count"] == 1
        assert days["2026-05-03"]["open_count"] == 1

    def test_empty(self, cases_qs):
        out = analytics.compute_backlog(cases_qs, _utc(2026, 1, 1), _utc(2026, 1, 3))
        assert all(row["open_count"] == 0 for row in out["series"])


# --------------------------------------------------------------------------
# Agents


class TestComputeAgents:
    def test_groups_per_assignee(self, org_a, cases_qs, user_profile, admin_profile):
        c1 = Case.objects.create(
            org=org_a, name="A", status="New", priority="Normal",
            sla_first_response_hours=4,
        )
        c2 = Case.objects.create(
            org=org_a, name="B", status="New", priority="Normal",
            sla_first_response_hours=4,
        )
        c1.assigned_to.add(user_profile)
        c2.assigned_to.add(admin_profile)
        Case.objects.filter(pk=c1.pk).update(
            created_at=_utc(2026, 5, 1, 8),
            first_response_at=_utc(2026, 5, 1, 11),
        )
        Case.objects.filter(pk=c2.pk).update(
            created_at=_utc(2026, 5, 1, 8),
            first_response_at=_utc(2026, 5, 1, 14),
        )
        out = analytics.compute_agents(cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 2))
        by_email = {row["email"]: row for row in out}
        assert by_email["user@test.com"]["handled"] == 1
        assert by_email["user@test.com"]["avg_frt_hours"] == pytest.approx(3.0)
        assert by_email["admin@test.com"]["handled"] == 1
        assert by_email["admin@test.com"]["avg_frt_hours"] == pytest.approx(6.0)
        # csat_avg always None until CsatSurvey ships.
        assert all(row["csat_avg"] is None for row in out)

    def test_multi_assignee_counts_each(self, org_a, cases_qs, user_profile, admin_profile):
        c = Case.objects.create(
            org=org_a, name="Shared", status="New", priority="Normal",
        )
        c.assigned_to.add(user_profile, admin_profile)
        Case.objects.filter(pk=c.pk).update(created_at=_utc(2026, 5, 1, 8))
        out = analytics.compute_agents(cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 2))
        assert sum(row["handled"] for row in out) == 2


# --------------------------------------------------------------------------
# SLA


class TestComputeSla:
    def test_empty(self, cases_qs):
        out = analytics.compute_sla(cases_qs, _utc(2026, 1, 1), _utc(2026, 1, 2))
        assert out["total"] == 0
        assert out["frt_breach_rate"] is None
        assert out["resolution_breach_rate"] is None

    def test_breach_rates_split_by_priority(self, org_a, cases_qs):
        # One Urgent that breached FRT, one Normal that responded fine.
        c1 = Case.objects.create(
            org=org_a, name="U", status="New", priority="Urgent",
            sla_first_response_hours=1, sla_resolution_hours=4,
        )
        c2 = Case.objects.create(
            org=org_a, name="N", status="New", priority="Normal",
            sla_first_response_hours=4, sla_resolution_hours=24,
        )
        Case.objects.filter(pk=c1.pk).update(
            created_at=_utc(2026, 5, 1, 0),
            first_response_at=_utc(2026, 5, 1, 3),
            resolved_at=_utc(2026, 5, 1, 6),  # 6h > 4h → resolution breach too.
        )
        Case.objects.filter(pk=c2.pk).update(
            created_at=_utc(2026, 5, 1, 0),
            first_response_at=_utc(2026, 5, 1, 1),
            resolved_at=_utc(2026, 5, 1, 8),
        )
        out = analytics.compute_sla(cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 2))
        assert out["total"] == 2
        assert out["frt_breach_count"] == 1
        assert out["resolution_breach_count"] == 1
        assert out["by_priority"]["Urgent"]["frt_breach_rate"] == 1.0
        assert out["by_priority"]["Normal"]["frt_breach_rate"] == 0.0


# --------------------------------------------------------------------------
# Drilldown helper


class TestCaseIdsForMetric:
    def test_frt_returns_window_ids(self, org_a, cases_qs):
        c = Case.objects.create(org=org_a, name="X", status="New", priority="Normal")
        Case.objects.filter(pk=c.pk).update(created_at=_utc(2026, 5, 1, 12))
        ids = list(
            analytics.case_ids_for_metric(
                "frt", cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 2)
            )
        )
        assert c.id in ids

    def test_backlog_requires_bucket(self, cases_qs):
        with pytest.raises(ValueError):
            list(
                analytics.case_ids_for_metric(
                    "backlog", cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 2)
                )
            )

    def test_unknown_metric_raises(self, cases_qs):
        with pytest.raises(ValueError):
            list(
                analytics.case_ids_for_metric(
                    "garbage", cases_qs, _utc(2026, 5, 1), _utc(2026, 5, 2)
                )
            )
