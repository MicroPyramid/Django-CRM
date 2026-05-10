"""Tests for the SLA pause/resume signal and deadline math on Case."""

from datetime import datetime, time, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from business_hours.models import BusinessCalendar
from cases.models import Case


_UTC = ZoneInfo("UTC")


@pytest.fixture
def calendar_a(org_a):
    return BusinessCalendar.objects.create(
        org=org_a,
        name="Default",
        timezone="UTC",
        is_default=True,
        monday_open=time(9, 0),
        monday_close=time(17, 0),
        tuesday_open=time(9, 0),
        tuesday_close=time(17, 0),
        wednesday_open=time(9, 0),
        wednesday_close=time(17, 0),
        thursday_open=time(9, 0),
        thursday_close=time(17, 0),
        friday_open=time(9, 0),
        friday_close=time(17, 0),
    )


@pytest.mark.django_db
class TestSLAPauseSignal:
    def test_status_to_pending_stamps_paused_at(self, case_a):
        assert case_a.sla_paused_at is None
        case_a.status = "Pending"
        case_a.save()
        case_a.refresh_from_db()
        assert case_a.sla_paused_at is not None
        assert case_a.sla_paused_seconds == 0

    def test_pending_to_other_accumulates_seconds(self, case_a):
        # First, simulate going Pending an hour ago.
        one_hour_ago = timezone.now() - timedelta(hours=1)
        case_a.status = "Pending"
        case_a.sla_paused_at = one_hour_ago
        case_a.save(update_fields=["status", "sla_paused_at", "updated_at"])

        case_a.status = "New"
        case_a.save()
        case_a.refresh_from_db()

        assert case_a.sla_paused_at is None
        assert case_a.sla_paused_seconds >= 3590  # ~1 hour, allow signal jitter

    def test_repeated_pause_resume_accumulates(self, case_a):
        # First cycle.
        case_a.status = "Pending"
        case_a.sla_paused_at = timezone.now() - timedelta(minutes=30)
        case_a.save(update_fields=["status", "sla_paused_at", "updated_at"])
        case_a.status = "New"
        case_a.save()
        case_a.refresh_from_db()
        first_total = case_a.sla_paused_seconds
        assert first_total >= 1790

        # Second cycle.
        case_a.status = "Pending"
        case_a.sla_paused_at = timezone.now() - timedelta(minutes=15)
        case_a.save(update_fields=["status", "sla_paused_at", "updated_at"])
        case_a.status = "New"
        case_a.save()
        case_a.refresh_from_db()

        assert case_a.sla_paused_seconds >= first_total + 890

    def test_no_change_no_op(self, case_a):
        case_a.name = "Renamed"
        case_a.save()
        case_a.refresh_from_db()
        assert case_a.sla_paused_at is None
        assert case_a.sla_paused_seconds == 0

    def test_other_to_other_transition_no_op(self, case_a):
        case_a.status = "In Progress"
        case_a.save()
        case_a.refresh_from_db()
        assert case_a.sla_paused_at is None
        assert case_a.sla_paused_seconds == 0


@pytest.mark.django_db
class TestSLADeadlineWithCalendar:
    def test_uses_business_hours_when_calendar_present(self, case_a, calendar_a):
        # Pin created_at to a known point so the math is deterministic.
        # 2026-05-08 is Friday; 4-hour SLA started Fri 4pm = Mon noon.
        case_a.created_at = datetime(2026, 5, 8, 16, 0, tzinfo=_UTC)
        case_a.sla_first_response_hours = 4
        case_a.save(
            update_fields=[
                "created_at",
                "sla_first_response_hours",
                "updated_at",
            ]
        )
        deadline = case_a.first_response_sla_deadline
        assert deadline == datetime(2026, 5, 11, 12, 0, tzinfo=_UTC)

    def test_falls_back_to_walltime_without_calendar(self, case_a):
        # No calendar in this test → wall-clock arithmetic.
        case_a.created_at = datetime(2026, 5, 8, 16, 0, tzinfo=_UTC)
        case_a.sla_first_response_hours = 4
        case_a.save(
            update_fields=[
                "created_at",
                "sla_first_response_hours",
                "updated_at",
            ]
        )
        deadline = case_a.first_response_sla_deadline
        assert deadline == datetime(2026, 5, 8, 20, 0, tzinfo=_UTC)

    def test_paused_seconds_push_deadline_forward(self, case_a, calendar_a):
        case_a.created_at = datetime(2026, 5, 11, 9, 0, tzinfo=_UTC)
        case_a.sla_first_response_hours = 4
        case_a.sla_paused_seconds = 3600  # 1h customer wait already accumulated
        case_a.save(
            update_fields=[
                "created_at",
                "sla_first_response_hours",
                "sla_paused_seconds",
                "updated_at",
            ]
        )
        deadline = case_a.first_response_sla_deadline
        # Mon 9am + 4h business = 1pm; +1h pause = 2pm.
        assert deadline == datetime(2026, 5, 11, 14, 0, tzinfo=_UTC)

    def test_currently_pending_extends_deadline(self, case_a, calendar_a):
        # Case is currently pending — paused_at set 30 minutes ago.
        case_a.created_at = datetime(2026, 5, 11, 9, 0, tzinfo=_UTC)
        case_a.sla_first_response_hours = 4
        case_a.status = "Pending"
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        case_a.sla_paused_at = thirty_min_ago
        case_a.save(
            update_fields=[
                "created_at",
                "sla_first_response_hours",
                "status",
                "sla_paused_at",
                "updated_at",
            ]
        )
        deadline = case_a.first_response_sla_deadline
        # Base deadline = Mon 1pm UTC; plus ~30min from currently-pending state.
        base = datetime(2026, 5, 11, 13, 0, tzinfo=_UTC)
        assert deadline >= base + timedelta(minutes=29)
        assert deadline <= base + timedelta(minutes=31)

    def test_breach_check_uses_business_hours(self, case_a, calendar_a):
        # Friday 4pm + 4 hours business = Monday noon. Test "now" = Saturday
        # 6pm (which is past the wall-clock deadline of Fri 8pm but BEFORE
        # the business-hours deadline of Mon noon) should NOT breach.
        case_a.created_at = datetime(2026, 5, 8, 16, 0, tzinfo=_UTC)
        case_a.sla_first_response_hours = 4
        case_a.first_response_at = None
        case_a.save(
            update_fields=[
                "created_at",
                "sla_first_response_hours",
                "first_response_at",
                "updated_at",
            ]
        )
        with patch(
            "django.utils.timezone.now",
            return_value=datetime(2026, 5, 9, 18, 0, tzinfo=_UTC),
        ):
            assert case_a.is_sla_first_response_breached is False

    def test_first_response_at_clears_breach(self, case_a, calendar_a):
        case_a.created_at = datetime(2026, 5, 1, 9, 0, tzinfo=_UTC)
        case_a.sla_first_response_hours = 1
        case_a.first_response_at = datetime(2026, 5, 1, 9, 30, tzinfo=_UTC)
        case_a.save(
            update_fields=[
                "created_at",
                "sla_first_response_hours",
                "first_response_at",
                "updated_at",
            ]
        )
        assert case_a.is_sla_first_response_breached is False
