"""REST API tests for /api/business-hours/."""

from datetime import date, time

import pytest

from business_hours.models import BusinessCalendar, BusinessHoliday


CALENDAR_URL = "/api/business-hours/calendar/"


def _detail_url(cal_id):
    return f"/api/business-hours/calendar/{cal_id}/"


def _holiday_list_url(cal_id):
    return f"/api/business-hours/calendar/{cal_id}/holidays/"


def _holiday_detail_url(cal_id, hid):
    return f"/api/business-hours/calendar/{cal_id}/holidays/{hid}/"


@pytest.mark.django_db
class TestGetCalendar:
    def test_unauthenticated(self, client):
        r = client.get(CALENDAR_URL)
        assert r.status_code in (401, 403)

    def test_creates_default_on_first_load(self, admin_client, org_a):
        assert not BusinessCalendar.objects.filter(org=org_a).exists()
        r = admin_client.get(CALENDAR_URL)
        assert r.status_code == 200
        body = r.json()
        assert body["is_default"] is True
        assert body["timezone"] == "UTC"
        assert body["holidays"] == []
        assert BusinessCalendar.objects.filter(org=org_a).count() == 1

    def test_returns_existing_with_holidays(
        self, admin_client, calendar_a, holiday_factory
    ):
        holiday_factory(calendar_a, date=date(2026, 7, 4), name="Independence Day")
        r = admin_client.get(CALENDAR_URL)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == str(calendar_a.id)
        assert len(body["holidays"]) == 1
        assert body["holidays"][0]["name"] == "Independence Day"

    def test_user_can_read_calendar(self, user_client, calendar_a):
        r = user_client.get(CALENDAR_URL)
        assert r.status_code == 200


@pytest.mark.django_db
class TestUpdateCalendar:
    def test_admin_can_update_hours(self, admin_client, calendar_a):
        r = admin_client.put(
            _detail_url(calendar_a.id),
            data={"monday_open": "08:00:00", "monday_close": "18:00:00"},
            format="json",
        )
        assert r.status_code == 200
        calendar_a.refresh_from_db()
        assert calendar_a.monday_open == time(8, 0)
        assert calendar_a.monday_close == time(18, 0)

    def test_admin_can_change_timezone(self, admin_client, calendar_a):
        r = admin_client.put(
            _detail_url(calendar_a.id),
            data={"timezone": "America/New_York"},
            format="json",
        )
        assert r.status_code == 200
        calendar_a.refresh_from_db()
        assert calendar_a.timezone == "America/New_York"

    def test_invalid_timezone_rejected(self, admin_client, calendar_a):
        r = admin_client.put(
            _detail_url(calendar_a.id),
            data={"timezone": "Mars/Phobos"},
            format="json",
        )
        assert r.status_code == 400

    def test_close_before_open_rejected(self, admin_client, calendar_a):
        r = admin_client.put(
            _detail_url(calendar_a.id),
            data={"monday_open": "17:00:00", "monday_close": "09:00:00"},
            format="json",
        )
        assert r.status_code == 400

    def test_close_without_open_rejected(self, admin_client, calendar_a):
        r = admin_client.put(
            _detail_url(calendar_a.id),
            data={"saturday_close": "12:00:00"},
            format="json",
        )
        assert r.status_code == 400

    def test_non_admin_cannot_update(self, user_client, calendar_a):
        r = user_client.put(
            _detail_url(calendar_a.id),
            data={"monday_open": "08:00:00", "monday_close": "18:00:00"},
            format="json",
        )
        assert r.status_code == 403

    def test_cross_org_update_404s(self, admin_client, org_b):
        other = BusinessCalendar.objects.create(org=org_b, name="OrgB", is_default=True)
        r = admin_client.put(
            _detail_url(other.id),
            data={"monday_open": "08:00:00", "monday_close": "18:00:00"},
            format="json",
        )
        assert r.status_code == 404


@pytest.mark.django_db
class TestHolidayEndpoints:
    def test_admin_can_add_holiday(self, admin_client, calendar_a):
        r = admin_client.post(
            _holiday_list_url(calendar_a.id),
            data={"date": "2026-12-25", "name": "Christmas"},
            format="json",
        )
        assert r.status_code == 201
        assert BusinessHoliday.objects.filter(
            calendar=calendar_a, date=date(2026, 12, 25)
        ).exists()

    def test_add_holiday_idempotent(self, admin_client, calendar_a, holiday_factory):
        holiday_factory(calendar_a, date=date(2026, 12, 25), name="Christmas")
        r = admin_client.post(
            _holiday_list_url(calendar_a.id),
            data={"date": "2026-12-25", "name": "Christmas Day"},
            format="json",
        )
        assert r.status_code == 200
        assert BusinessHoliday.objects.filter(
            calendar=calendar_a, date=date(2026, 12, 25)
        ).count() == 1

    def test_user_cannot_add(self, user_client, calendar_a):
        r = user_client.post(
            _holiday_list_url(calendar_a.id),
            data={"date": "2026-12-25", "name": "Christmas"},
            format="json",
        )
        assert r.status_code == 403

    def test_admin_can_delete_holiday(
        self, admin_client, calendar_a, holiday_factory
    ):
        h = holiday_factory(calendar_a, date=date(2026, 7, 4), name="Independence Day")
        r = admin_client.delete(_holiday_detail_url(calendar_a.id, h.id))
        assert r.status_code == 204
        assert not BusinessHoliday.objects.filter(pk=h.pk).exists()

    def test_user_cannot_delete(self, user_client, calendar_a, holiday_factory):
        h = holiday_factory(calendar_a, date=date(2026, 7, 4), name="Independence Day")
        r = user_client.delete(_holiday_detail_url(calendar_a.id, h.id))
        assert r.status_code == 403

    def test_cross_org_delete_404s(self, admin_client, org_b):
        other_cal = BusinessCalendar.objects.create(
            org=org_b, name="OrgB", is_default=True
        )
        h = BusinessHoliday.objects.create(
            calendar=other_cal,
            org=org_b,
            date=date(2026, 7, 4),
            name="OrgB holiday",
        )
        r = admin_client.delete(_holiday_detail_url(other_cal.id, h.id))
        assert r.status_code == 404
