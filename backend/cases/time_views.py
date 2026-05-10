"""
Time-tracking endpoints (Tier 3 time-tracking).

Case-scoped:

* ``GET  /api/cases/<pk>/time-entries/``        — list (visible to actor)
* ``POST /api/cases/<pk>/time-entries/``        — manual entry
* ``POST /api/cases/<pk>/time-entries/start/``  — start a running timer (409 if one active)
* ``GET  /api/cases/<pk>/time-summary/``        — totals + by-profile breakdown

Entry-scoped (registered at the project root under ``/api/time-entries/``):

* ``POST   /api/time-entries/<pk>/stop/``       — stop a running timer
* ``PUT    /api/time-entries/<pk>/``            — owner or admin
* ``DELETE /api/time-entries/<pk>/``            — owner or admin
* ``GET    /api/time-entries/timesheet/``       — week view, grouped by day
"""

from collections import OrderedDict
from datetime import date, datetime, timedelta

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import Case, TimeEntry
from cases.serializer import (
    TimeEntryCreateSerializer,
    TimeEntrySerializer,
    TimeEntryUpdateSerializer,
)
from common.permissions import HasOrgContext


def _is_admin(profile):
    return profile.role == "ADMIN" or getattr(profile, "is_organization_admin", False)


def _visible_entry_qs(profile):
    """Org-scoped queryset honouring agent-vs-admin visibility."""
    qs = TimeEntry.objects.filter(org=profile.org)
    if not _is_admin(profile):
        qs = qs.filter(profile=profile)
    return qs.select_related("profile", "profile__user", "case")


class TimeEntryListCreateView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request, pk):
        case = get_object_or_404(Case, id=pk, org=request.profile.org)
        entries = _visible_entry_qs(request.profile).filter(case=case).order_by(
            "-started_at"
        )
        return Response(TimeEntrySerializer(entries, many=True).data)

    def post(self, request, pk):
        case = get_object_or_404(Case, id=pk, org=request.profile.org)
        serializer = TimeEntryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            entry = TimeEntry.objects.create(
                org=request.profile.org,
                case=case,
                profile=request.profile,
                **serializer.validated_data,
            )
        except IntegrityError as exc:
            # Most likely the partial unique on (profile) for active timers,
            # or the end-after-start CheckConstraint as a defense-in-depth.
            return Response(
                {"detail": str(exc).splitlines()[0][:200]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            TimeEntrySerializer(entry).data, status=status.HTTP_201_CREATED
        )


class TimeEntryStartView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @transaction.atomic
    def post(self, request, pk):
        case = get_object_or_404(Case, id=pk, org=request.profile.org)

        # Reject if this profile already has a running timer (anywhere). The
        # one_active_timer_per_profile partial unique would also catch this
        # at INSERT time, but a 409 with the offending case id is friendlier
        # than a 400 from IntegrityError.
        running = (
            TimeEntry.objects.select_for_update()
            .filter(profile=request.profile, ended_at__isnull=True)
            .first()
        )
        if running is not None:
            return Response(
                {
                    "detail": "You already have a running timer.",
                    "running_entry_id": str(running.id),
                    "running_case_id": str(running.case_id),
                },
                status=status.HTTP_409_CONFLICT,
            )

        entry = TimeEntry.objects.create(
            org=request.profile.org,
            case=case,
            profile=request.profile,
            started_at=timezone.now(),
            description=(request.data.get("description") or "").strip(),
            billable=bool(request.data.get("billable", False)),
        )
        return Response(
            TimeEntrySerializer(entry).data, status=status.HTTP_201_CREATED
        )


class TimeSummaryView(APIView):
    """``GET /api/cases/<pk>/time-summary/`` — totals + per-profile breakdown.

    Same shape as ``CaseSerializer.time_summary`` for clients that don't
    want to refetch the full case envelope.
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request, pk):
        case = get_object_or_404(Case, id=pk, org=request.profile.org)
        qs = case.time_entries.filter(ended_at__isnull=False)
        total = qs.aggregate(total=Sum("duration_minutes"))["total"] or 0
        billable = (
            qs.filter(billable=True).aggregate(s=Sum("duration_minutes"))["s"] or 0
        )
        last_entry_at = (
            qs.order_by("-started_at").values_list("started_at", flat=True).first()
        )
        by_profile = []
        for row in (
            qs.values("profile_id", "profile__user__email")
            .annotate(minutes=Sum("duration_minutes"))
            .order_by("-minutes")
        ):
            by_profile.append(
                {
                    "profile_id": str(row["profile_id"]),
                    "name": row.get("profile__user__email") or "",
                    "minutes": row["minutes"] or 0,
                }
            )
        return Response(
            {
                "total_minutes": total,
                "billable_minutes": billable,
                "last_entry_at": last_entry_at,
                "by_profile": by_profile,
            }
        )


class TimeEntryDetailView(APIView):
    """PUT/DELETE for a specific time entry. Owner or admin only."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def _get_entry(self, request, pk):
        try:
            entry = TimeEntry.objects.get(id=pk, org=request.profile.org)
        except TimeEntry.DoesNotExist:
            return None
        if entry.profile_id != request.profile.id and not _is_admin(request.profile):
            return False  # Sentinel: row exists but caller is not authorized.
        return entry

    def put(self, request, pk):
        entry = self._get_entry(request, pk)
        if entry is None:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        if entry is False:
            return Response(
                {"detail": "Not authorized to edit this entry."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = TimeEntryUpdateSerializer(entry, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        # Apply allowed fields explicitly so we never overwrite invoice/profile/case.
        for field, value in serializer.validated_data.items():
            setattr(entry, field, value)
        entry.save()
        return Response(TimeEntrySerializer(entry).data)

    def delete(self, request, pk):
        entry = self._get_entry(request, pk)
        if entry is None:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        if entry is False:
            return Response(
                {"detail": "Not authorized to delete this entry."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if entry.invoice_id is not None:
            return Response(
                {"detail": "Cannot delete an entry that has been invoiced."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TimeEntryStopView(APIView):
    """``POST /api/time-entries/<pk>/stop/`` — stop a running timer."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @transaction.atomic
    def post(self, request, pk):
        entry = (
            TimeEntry.objects.select_for_update()
            .filter(id=pk, org=request.profile.org)
            .first()
        )
        if entry is None:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        if entry.profile_id != request.profile.id and not _is_admin(request.profile):
            return Response(
                {"detail": "Not authorized to stop this entry."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if entry.ended_at is not None:
            return Response(
                {"detail": "Timer is already stopped."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        entry.ended_at = timezone.now()
        entry.save()
        return Response(TimeEntrySerializer(entry).data)


class UnbilledEntriesView(APIView):
    """``GET /api/time-entries/unbilled/?account=<uuid>`` — list billable,
    stopped, not-yet-invoiced entries for an account so the invoice picker
    can show them. Org-scoped; admins see all entries, agents only their own.
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request):
        account_id = request.query_params.get("account")
        qs = (
            _visible_entry_qs(request.profile)
            .filter(billable=True, invoice__isnull=True, ended_at__isnull=False)
            .order_by("-started_at")
        )
        if account_id:
            qs = qs.filter(case__account_id=account_id)
        return Response(TimeEntrySerializer(qs, many=True).data)


class TimesheetView(APIView):
    """``GET /api/time-entries/timesheet/?profile=<id>&start=<date>&end=<date>``.

    Returns entries for ``profile`` (defaults to caller) between ``start`` and
    ``end`` inclusive, grouped into a list of day buckets with totals. Only
    admins may pass a ``profile`` other than their own.
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request):
        profile_param = request.query_params.get("profile")
        target_profile_id = request.profile.id
        if profile_param and profile_param != str(request.profile.id):
            if not _is_admin(request.profile):
                return Response(
                    {"detail": "Only admins can view another profile's timesheet."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            target_profile_id = profile_param

        try:
            start = self._parse_date(request.query_params.get("start"))
            end = self._parse_date(request.query_params.get("end"))
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        if start is None or end is None:
            today = date.today()
            # Default to this Mon..Sun (ISO week).
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
        if end < start:
            return Response(
                {"detail": "end must be on or after start."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = (
            TimeEntry.objects.filter(
                org=request.profile.org,
                profile_id=target_profile_id,
                ended_at__isnull=False,
                started_at__date__gte=start,
                started_at__date__lte=end,
            )
            .select_related("case", "profile", "profile__user")
            .order_by("started_at")
        )
        days = OrderedDict()
        cursor = start
        while cursor <= end:
            days[cursor.isoformat()] = {
                "date": cursor.isoformat(),
                "entries": [],
                "total_minutes": 0,
                "billable_minutes": 0,
            }
            cursor += timedelta(days=1)
        for entry in qs:
            day_key = entry.started_at.date().isoformat()
            bucket = days.get(day_key)
            if bucket is None:
                # Entry's local date may fall outside the window when timezone
                # math straddles midnight; skip silently.
                continue
            bucket["entries"].append(TimeEntrySerializer(entry).data)
            bucket["total_minutes"] += entry.duration_minutes or 0
            if entry.billable:
                bucket["billable_minutes"] += entry.duration_minutes or 0

        week_total = sum(d["total_minutes"] for d in days.values())
        billable_total = sum(d["billable_minutes"] for d in days.values())
        return Response(
            {
                "profile_id": str(target_profile_id),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "days": list(days.values()),
                "total_minutes": week_total,
                "billable_minutes": billable_total,
            }
        )

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid date {value!r}; expected YYYY-MM-DD.") from exc
