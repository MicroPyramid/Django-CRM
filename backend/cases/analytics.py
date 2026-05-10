"""Pure analytics aggregation for the cases reporting endpoints.

The functions here take a base `Case` queryset (already filtered by org +
visibility + any caller-supplied filters) plus a [from_dt, to_dt) window
and return JSON-friendly dicts that the views serialize directly.

Why pull values into Python rather than use DB percentiles? SQLite (used in
the test suite) has no `percentile_cont`. The volumes here (cases per org per
window) sit well within the millions-of-rows-into-Python range; if a deployment
ever pushes past that, switch to a Postgres-only path or the optional
`CaseMetricsDaily` cache table called out in the spec.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone as dt_timezone
from typing import Iterable, Optional
from uuid import UUID

from django.db.models import Count, Q, QuerySet
from django.utils import timezone


# ---------------------------------------------------------------------------
# Helpers


def _percentile(sorted_values: list[float], pct: float) -> Optional[float]:
    """Linear-interpolation percentile (matches numpy.percentile default).

    Returns None for empty input. ``pct`` is in [0, 100]. ``sorted_values``
    must already be sorted ascending.
    """
    if not sorted_values:
        return None
    if pct <= 0:
        return sorted_values[0]
    if pct >= 100:
        return sorted_values[-1]
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return sorted_values[lo]
    frac = rank - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


def _hours_between(later: datetime, earlier: datetime) -> float:
    return (later - earlier).total_seconds() / 3600.0


def _bucket_dates(from_dt: datetime, to_dt: datetime) -> list[date]:
    """Inclusive list of UTC dates from from_dt to to_dt-1 day."""
    if to_dt <= from_dt:
        return []
    start = from_dt.date()
    end = (to_dt - timedelta(seconds=1)).date()
    out: list[date] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=1)
    return out


def _coerce_window(
    from_dt: Optional[datetime], to_dt: Optional[datetime]
) -> tuple[datetime, datetime]:
    """Defaults to last 30 days; ensures both ends are tz-aware UTC."""
    now = timezone.now()
    if to_dt is None:
        to_dt = now
    if from_dt is None:
        from_dt = to_dt - timedelta(days=30)
    if timezone.is_naive(from_dt):
        from_dt = from_dt.replace(tzinfo=dt_timezone.utc)
    if timezone.is_naive(to_dt):
        to_dt = to_dt.replace(tzinfo=dt_timezone.utc)
    return from_dt, to_dt


# ---------------------------------------------------------------------------
# Metric computations


def compute_frt(
    qs: QuerySet,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> dict:
    """First Response Time aggregation.

    Window scopes by `Case.created_at`. For each case with `first_response_at`
    set, FRT = first_response_at - created_at. Breach counts cases where
    FRT > sla_first_response_hours, OR where first_response_at is null and
    `now - created_at > sla` (an in-flight breach).
    """
    from_dt, to_dt = _coerce_window(from_dt, to_dt)
    in_window = qs.filter(created_at__gte=from_dt, created_at__lt=to_dt)

    rows = list(
        in_window.values_list(
            "id",
            "created_at",
            "first_response_at",
            "sla_first_response_hours",
        )
    )
    now = timezone.now()
    deltas: list[float] = []
    breach_count = 0
    case_ids: list[UUID] = []
    breach_ids: list[UUID] = []
    for case_id, created_at, first_response_at, sla_hours in rows:
        case_ids.append(case_id)
        if first_response_at is not None:
            hours = _hours_between(first_response_at, created_at)
            deltas.append(hours)
            if hours > (sla_hours or 0):
                breach_count += 1
                breach_ids.append(case_id)
        else:
            # Open-but-unresponded: count as breach if SLA already exceeded.
            if _hours_between(now, created_at) > (sla_hours or 0):
                breach_count += 1
                breach_ids.append(case_id)

    deltas.sort()
    median_h = _percentile(deltas, 50)
    p90_h = _percentile(deltas, 90)

    # Daily series of medians (created_at bucket).
    series: list[dict] = []
    by_day: dict[date, list[float]] = {}
    for _id, created_at, first_response_at, _sla in rows:
        if first_response_at is None:
            continue
        bucket = created_at.date()
        by_day.setdefault(bucket, []).append(
            _hours_between(first_response_at, created_at)
        )
    for d in _bucket_dates(from_dt, to_dt):
        values = sorted(by_day.get(d, []))
        series.append(
            {
                "bucket": d.isoformat(),
                "median": _percentile(values, 50) if values else None,
                "count": len(values),
            }
        )

    return {
        "median_hours": median_h,
        "p90_hours": p90_h,
        "count": len(deltas),
        "breach_count": breach_count,
        "series": series,
        "case_ids": [str(cid) for cid in case_ids],
        "breach_case_ids": [str(cid) for cid in breach_ids],
    }


def compute_mttr(
    qs: QuerySet,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> dict:
    """Mean Time To Resolution. Window scopes by `Case.resolved_at`."""
    from_dt, to_dt = _coerce_window(from_dt, to_dt)
    rows = list(
        qs.filter(
            resolved_at__isnull=False,
            resolved_at__gte=from_dt,
            resolved_at__lt=to_dt,
        ).values_list("id", "created_at", "resolved_at", "priority")
    )
    deltas: list[float] = []
    by_priority_lists: dict[str, list[float]] = {}
    case_ids: list[UUID] = []
    for case_id, created_at, resolved_at, priority in rows:
        h = _hours_between(resolved_at, created_at)
        deltas.append(h)
        case_ids.append(case_id)
        by_priority_lists.setdefault(priority, []).append(h)

    deltas_sorted = sorted(deltas)
    by_priority: dict[str, dict] = {}
    for prio, values in by_priority_lists.items():
        values.sort()
        by_priority[prio] = {
            "mean_hours": (sum(values) / len(values)) if values else None,
            "median_hours": _percentile(values, 50),
            "p90_hours": _percentile(values, 90),
            "count": len(values),
        }

    return {
        "mean_hours": (sum(deltas) / len(deltas)) if deltas else None,
        "median_hours": _percentile(deltas_sorted, 50),
        "p90_hours": _percentile(deltas_sorted, 90),
        "count": len(deltas),
        "by_priority": by_priority,
        "case_ids": [str(cid) for cid in case_ids],
    }


def compute_backlog(
    qs: QuerySet,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> dict:
    """Open + urgent counts at end of each day in window.

    Open at day D = created_at <= end_of_D AND (resolved_at IS NULL OR resolved_at > end_of_D).
    Cheap with the new (org, resolved_at) index since we never scan more than
    once per case row to materialize the window.
    """
    from_dt, to_dt = _coerce_window(from_dt, to_dt)
    rows = list(
        qs.filter(
            Q(created_at__lt=to_dt)
            & (Q(resolved_at__isnull=True) | Q(resolved_at__gte=from_dt))
        ).values_list("created_at", "resolved_at", "priority")
    )

    series: list[dict] = []
    for d in _bucket_dates(from_dt, to_dt):
        # End-of-day in UTC. Spec note: timezone story is documented at the
        # response level; switch to org-local end-of-day once business-hours
        # supplies the tz consistently.
        end_of_day = datetime.combine(
            d + timedelta(days=1), datetime.min.time(), tzinfo=dt_timezone.utc
        )
        open_count = 0
        urgent_count = 0
        for created_at, resolved_at, priority in rows:
            if created_at >= end_of_day:
                continue
            if resolved_at is not None and resolved_at <= end_of_day:
                continue
            open_count += 1
            if priority == "Urgent":
                urgent_count += 1
        series.append(
            {
                "date": d.isoformat(),
                "open_count": open_count,
                "urgent_count": urgent_count,
            }
        )

    return {"series": series}


def compute_agents(
    qs: QuerySet,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> list[dict]:
    """Per-agent rollup. A case with N assignees counts once per agent.

    Returns list of `{profile_id, name, email, handled, avg_frt_hours, csat_avg, breach_rate}`.
    `csat_avg` is computed from `CsatSurvey` rows (responded, in-window) tied
    to cases this agent was assigned to.
    """
    from_dt, to_dt = _coerce_window(from_dt, to_dt)
    in_window = qs.filter(created_at__gte=from_dt, created_at__lt=to_dt)

    rows = list(
        in_window.values_list(
            "id",
            "created_at",
            "first_response_at",
            "resolved_at",
            "sla_first_response_hours",
            "sla_resolution_hours",
            "assigned_to",
            "assigned_to__user__email",
        )
    )
    now = timezone.now()

    # Per-agent CSAT averages, scoped to the same case set + window. Pulled
    # in one query keyed by profile_id so we don't N+1 inside the loop.
    from cases.models import CsatSurvey

    case_ids = {row[0] for row in rows}
    csat_pairs = list(
        CsatSurvey.objects.filter(
            case_id__in=case_ids, rating__isnull=False
        ).values_list("case_id", "rating")
    )
    rating_by_case = {cid: rating for cid, rating in csat_pairs}

    agg: dict[UUID, dict] = {}
    for (
        case_id,
        created_at,
        first_response_at,
        resolved_at,
        sla_frt,
        sla_res,
        profile_id,
        email,
    ) in rows:
        if profile_id is None:
            continue
        bucket = agg.setdefault(
            profile_id,
            {
                "profile_id": str(profile_id),
                "name": email or "",
                "email": email or "",
                "handled": 0,
                "frt_values": [],
                "csat_values": [],
                "breach_count": 0,
            },
        )
        bucket["handled"] += 1
        if case_id in rating_by_case:
            bucket["csat_values"].append(rating_by_case[case_id])
        if first_response_at is not None:
            h = _hours_between(first_response_at, created_at)
            bucket["frt_values"].append(h)
            if h > (sla_frt or 0):
                bucket["breach_count"] += 1
        elif _hours_between(now, created_at) > (sla_frt or 0):
            bucket["breach_count"] += 1
        # Resolution breach: closed past SLA, OR open past SLA.
        if resolved_at is not None:
            if _hours_between(resolved_at, created_at) > (sla_res or 0):
                bucket["breach_count"] += 1
        elif _hours_between(now, created_at) > (sla_res or 0):
            bucket["breach_count"] += 1

    out: list[dict] = []
    for bucket in agg.values():
        frt_values = bucket.pop("frt_values")
        avg_frt = (sum(frt_values) / len(frt_values)) if frt_values else None
        csat_values = bucket.pop("csat_values")
        avg_csat = (sum(csat_values) / len(csat_values)) if csat_values else None
        breach_count = bucket.pop("breach_count")
        # breach_rate denominator is "events that could breach": one FRT-check
        # plus one resolution-check per case, so 2 * handled.
        denom = max(1, 2 * bucket["handled"])
        bucket["avg_frt_hours"] = avg_frt
        bucket["csat_avg"] = avg_csat
        bucket["breach_rate"] = breach_count / denom
        out.append(bucket)

    out.sort(key=lambda r: (-r["handled"], r["email"]))
    return out


def compute_sla(
    qs: QuerySet,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> dict:
    """Org-wide SLA breach rates. Window scopes by `Case.created_at`."""
    from_dt, to_dt = _coerce_window(from_dt, to_dt)
    rows = list(
        qs.filter(created_at__gte=from_dt, created_at__lt=to_dt).values_list(
            "id",
            "created_at",
            "first_response_at",
            "resolved_at",
            "sla_first_response_hours",
            "sla_resolution_hours",
            "priority",
        )
    )
    now = timezone.now()

    total = len(rows)
    frt_breach = 0
    res_breach = 0
    breach_ids_frt: list[UUID] = []
    breach_ids_res: list[UUID] = []
    by_priority: dict[str, dict] = {}

    for (
        case_id,
        created_at,
        first_response_at,
        resolved_at,
        sla_frt,
        sla_res,
        priority,
    ) in rows:
        prio_bucket = by_priority.setdefault(
            priority,
            {"total": 0, "frt_breach": 0, "resolution_breach": 0},
        )
        prio_bucket["total"] += 1

        is_frt_breach = False
        if first_response_at is not None:
            if _hours_between(first_response_at, created_at) > (sla_frt or 0):
                is_frt_breach = True
        elif _hours_between(now, created_at) > (sla_frt or 0):
            is_frt_breach = True
        if is_frt_breach:
            frt_breach += 1
            breach_ids_frt.append(case_id)
            prio_bucket["frt_breach"] += 1

        is_res_breach = False
        if resolved_at is not None:
            if _hours_between(resolved_at, created_at) > (sla_res or 0):
                is_res_breach = True
        elif _hours_between(now, created_at) > (sla_res or 0):
            is_res_breach = True
        if is_res_breach:
            res_breach += 1
            breach_ids_res.append(case_id)
            prio_bucket["resolution_breach"] += 1

    def _rate(num: int, denom: int) -> Optional[float]:
        return (num / denom) if denom else None

    by_priority_out: dict[str, dict] = {}
    for prio, b in by_priority.items():
        by_priority_out[prio] = {
            "total": b["total"],
            "frt_breach_rate": _rate(b["frt_breach"], b["total"]),
            "resolution_breach_rate": _rate(b["resolution_breach"], b["total"]),
        }

    return {
        "total": total,
        "frt_breach_count": frt_breach,
        "resolution_breach_count": res_breach,
        "frt_breach_rate": _rate(frt_breach, total),
        "resolution_breach_rate": _rate(res_breach, total),
        "by_priority": by_priority_out,
        "frt_breach_case_ids": [str(cid) for cid in breach_ids_frt],
        "resolution_breach_case_ids": [str(cid) for cid in breach_ids_res],
    }


# ---------------------------------------------------------------------------
# Drilldown helper


def case_ids_for_metric(
    metric: str,
    qs: QuerySet,
    from_dt: Optional[datetime],
    to_dt: Optional[datetime],
    bucket: Optional[str] = None,
) -> Iterable[UUID]:
    """Return the set of case ids that the named metric/bucket pulls in.

    Used by both the drilldown JSON endpoint and the CSV export. Bucket is
    metric-specific: e.g. "breach" for frt/sla, a date string for backlog.
    """
    from_dt, to_dt = _coerce_window(from_dt, to_dt)

    if metric == "frt":
        in_window = qs.filter(created_at__gte=from_dt, created_at__lt=to_dt)
        if bucket == "breach":
            data = compute_frt(qs, from_dt, to_dt)
            return [UUID(s) for s in data["breach_case_ids"]]
        return in_window.values_list("id", flat=True)

    if metric == "mttr":
        return qs.filter(
            resolved_at__isnull=False,
            resolved_at__gte=from_dt,
            resolved_at__lt=to_dt,
        ).values_list("id", flat=True)

    if metric == "sla":
        if bucket == "frt_breach":
            return [UUID(s) for s in compute_sla(qs, from_dt, to_dt)["frt_breach_case_ids"]]
        if bucket == "resolution_breach":
            return [
                UUID(s)
                for s in compute_sla(qs, from_dt, to_dt)["resolution_breach_case_ids"]
            ]
        return qs.filter(
            created_at__gte=from_dt, created_at__lt=to_dt
        ).values_list("id", flat=True)

    if metric == "backlog":
        # Bucket is a YYYY-MM-DD date — return cases open at end of that day.
        if not bucket:
            raise ValueError("backlog drilldown requires a bucket=YYYY-MM-DD")
        target = date.fromisoformat(bucket)
        end_of_day = datetime.combine(
            target + timedelta(days=1),
            datetime.min.time(),
            tzinfo=dt_timezone.utc,
        )
        return qs.filter(
            Q(created_at__lt=end_of_day)
            & (Q(resolved_at__isnull=True) | Q(resolved_at__gt=end_of_day))
        ).values_list("id", flat=True)

    if metric == "agents":
        # Bucket = profile_id (uuid string).
        if not bucket:
            raise ValueError("agents drilldown requires a bucket=<profile_id>")
        return qs.filter(
            created_at__gte=from_dt,
            created_at__lt=to_dt,
            assigned_to=bucket,
        ).values_list("id", flat=True).distinct()

    raise ValueError(f"unknown metric: {metric}")
