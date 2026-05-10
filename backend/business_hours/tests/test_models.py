"""BusinessCalendar / BusinessHoliday model tests."""

from datetime import date, time

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from business_hours.models import BusinessCalendar, BusinessHoliday


@pytest.mark.django_db
class TestBusinessCalendarModel:
    def test_create_with_defaults(self, org_a):
        cal = BusinessCalendar.objects.create(org=org_a)
        assert cal.is_default is True
        assert cal.timezone == "UTC"
        assert cal.name == "Default"

    def test_only_one_default_per_org(self, org_a, calendar_a):
        with pytest.raises(IntegrityError):
            BusinessCalendar.objects.create(
                org=org_a, name="Second default", is_default=True
            )

    def test_second_non_default_allowed(self, org_a, calendar_a):
        cal = BusinessCalendar.objects.create(
            org=org_a, name="Eu hours", is_default=False
        )
        assert cal.id is not None

    def test_invalid_timezone_rejected(self, org_a):
        cal = BusinessCalendar(org=org_a, timezone="Mars/Phobos")
        with pytest.raises(ValidationError):
            cal.full_clean()

    def test_str(self, calendar_a):
        assert str(calendar_a) == "Default (UTC)"

    def test_windows_by_weekday_indices(self, calendar_a):
        win = calendar_a.windows_by_weekday()
        assert len(win) == 7
        assert win[0] == (time(9, 0), time(17, 0))  # Monday
        assert win[5] == (None, None)  # Saturday closed
        assert win[6] == (None, None)  # Sunday closed


@pytest.mark.django_db
class TestBusinessHolidayModel:
    def test_create(self, calendar_a):
        h = BusinessHoliday.objects.create(
            calendar=calendar_a,
            org=calendar_a.org,
            date=date(2026, 12, 25),
            name="Christmas",
        )
        assert h.id is not None
        assert h.calendar == calendar_a

    def test_unique_per_calendar_date(self, calendar_a):
        BusinessHoliday.objects.create(
            calendar=calendar_a,
            org=calendar_a.org,
            date=date(2026, 12, 25),
            name="Christmas",
        )
        with pytest.raises(IntegrityError):
            BusinessHoliday.objects.create(
                calendar=calendar_a,
                org=calendar_a.org,
                date=date(2026, 12, 25),
                name="Christmas Day",
            )

    def test_calendar_cascade_deletes_holidays(self, calendar_a):
        BusinessHoliday.objects.create(
            calendar=calendar_a,
            org=calendar_a.org,
            date=date(2026, 12, 25),
            name="Christmas",
        )
        cal_pk = calendar_a.pk
        calendar_a.delete()
        assert not BusinessHoliday.objects.filter(calendar_id=cal_pk).exists()

    def test_str_includes_date(self, calendar_a, holiday_factory):
        h = holiday_factory(calendar_a, date=date(2026, 7, 4), name="Independence Day")
        assert "2026-07-04" in str(h)
