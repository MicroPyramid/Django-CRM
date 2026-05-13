"""Business-hours app fixtures."""

from datetime import time

import pytest

from business_hours.models import BusinessCalendar, BusinessHoliday


@pytest.fixture
def calendar_a(org_a):
    """Mon-Fri 9-5 UTC default calendar for org_a."""
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


@pytest.fixture
def ny_calendar(org_a):
    """Mon-Fri 9-5 America/New_York calendar (DST testing)."""
    return BusinessCalendar.objects.create(
        org=org_a,
        name="NY",
        timezone="America/New_York",
        is_default=False,
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


@pytest.fixture
def holiday_factory():
    def _make(calendar, *, date, name="Holiday"):
        return BusinessHoliday.objects.create(
            calendar=calendar, org=calendar.org, date=date, name=name
        )

    return _make
