"""Tests for the add_business_hours walker."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from business_hours.calendar import add_business_hours


_UTC = ZoneInfo("UTC")
_NY = ZoneInfo("America/New_York")


@pytest.mark.django_db
class TestAddBusinessHours:
    def test_none_calendar_falls_back_to_walltime(self):
        start = datetime(2026, 5, 9, 17, 0, tzinfo=_UTC)  # Sat 5pm
        result = add_business_hours(start, 4, None)
        assert result == start + timedelta(hours=4)

    def test_zero_hours_returns_start(self, calendar_a):
        start = datetime(2026, 5, 11, 10, 0, tzinfo=_UTC)
        assert add_business_hours(start, 0, calendar_a) == start

    def test_within_open_window(self, calendar_a):
        start = datetime(2026, 5, 11, 10, 0, tzinfo=_UTC)  # Mon 10am UTC
        result = add_business_hours(start, 4, calendar_a)
        assert result == datetime(2026, 5, 11, 14, 0, tzinfo=_UTC)

    def test_spans_lunch_in_single_window_unchanged(self, calendar_a):
        start = datetime(2026, 5, 11, 12, 0, tzinfo=_UTC)
        # Single open window means 12pm + 3 = 3pm same day
        result = add_business_hours(start, 3, calendar_a)
        assert result == datetime(2026, 5, 11, 15, 0, tzinfo=_UTC)

    def test_skip_weekend(self, calendar_a):
        # Friday 5/8/2026 4pm + 4 hours of business = Mon 5/11 noon
        start = datetime(2026, 5, 8, 16, 0, tzinfo=_UTC)
        result = add_business_hours(start, 4, calendar_a)
        # 1h on Friday (4pm-5pm), then Sat/Sun skipped, 3h on Mon (9am-12pm)
        assert result == datetime(2026, 5, 11, 12, 0, tzinfo=_UTC)

    def test_start_before_open(self, calendar_a):
        # Mon 5am + 2 hours = Mon 11am (clock starts at 9am open)
        start = datetime(2026, 5, 11, 5, 0, tzinfo=_UTC)
        result = add_business_hours(start, 2, calendar_a)
        assert result == datetime(2026, 5, 11, 11, 0, tzinfo=_UTC)

    def test_start_after_close(self, calendar_a):
        # Mon 7pm + 1 hour = Tue 10am
        start = datetime(2026, 5, 11, 19, 0, tzinfo=_UTC)
        result = add_business_hours(start, 1, calendar_a)
        assert result == datetime(2026, 5, 12, 10, 0, tzinfo=_UTC)

    def test_start_on_weekend(self, calendar_a):
        # Sat 10am + 2 hours = Mon 11am
        start = datetime(2026, 5, 9, 10, 0, tzinfo=_UTC)
        result = add_business_hours(start, 2, calendar_a)
        assert result == datetime(2026, 5, 11, 11, 0, tzinfo=_UTC)

    def test_skip_holiday(self, calendar_a, holiday_factory):
        # Make Mon 5/11 a holiday — Mon's 8 hours move to Tue
        holiday_factory(calendar_a, date=date(2026, 5, 11), name="Founders Day")
        start = datetime(2026, 5, 11, 10, 0, tzinfo=_UTC)
        result = add_business_hours(start, 4, calendar_a)
        assert result == datetime(2026, 5, 12, 13, 0, tzinfo=_UTC)

    def test_multi_day_spill(self, calendar_a):
        # Mon 9am + 24 working hours = Wed 5pm (3 full 8-hour days).
        start = datetime(2026, 5, 11, 9, 0, tzinfo=_UTC)
        result = add_business_hours(start, 24, calendar_a)
        assert result == datetime(2026, 5, 13, 17, 0, tzinfo=_UTC)

    def test_dst_spring_forward(self, ny_calendar):
        # 2026-03-08 is the spring-forward date in NY (2am → 3am).
        # A 9-5 NY workday loses no business hours, so a Mon 3/9 case at
        # 9am NY + 8h = Mon 3/9 5pm NY, which is 21:00 UTC (NY is EDT).
        # Pick a friday 3/6 4pm NY start + 1h business + Mon 3/9 0..7 = 4pm Mon
        start = datetime(2026, 3, 6, 16, 0, tzinfo=_NY)  # Fri 4pm NY (pre-DST EST)
        result = add_business_hours(start, 9, ny_calendar)
        # 1h Fri 4-5pm + 8h Monday 9-5 = Mon 3/9 5pm NY (post-DST EDT).
        assert result.astimezone(_NY) == datetime(2026, 3, 9, 17, 0, tzinfo=_NY)

    def test_naive_input_treated_as_utc(self, calendar_a):
        start_naive = datetime(2026, 5, 11, 10, 0)
        result = add_business_hours(start_naive, 2, calendar_a)
        # Result is aware; converting back to UTC matches.
        assert result.astimezone(_UTC) == datetime(2026, 5, 11, 12, 0, tzinfo=_UTC)

    def test_calendar_with_no_open_windows_falls_back(self, org_a):
        from business_hours.models import BusinessCalendar

        cal = BusinessCalendar.objects.create(
            org=org_a, name="Closed", is_default=False
        )
        start = datetime(2026, 5, 11, 9, 0, tzinfo=_UTC)
        result = add_business_hours(start, 5, cal)
        assert result == start + timedelta(hours=5)

    def test_preserves_input_timezone(self, calendar_a):
        start_ny = datetime(2026, 5, 11, 10, 0, tzinfo=_NY)
        result = add_business_hours(start_ny, 2, calendar_a)
        assert result.tzinfo == _NY
