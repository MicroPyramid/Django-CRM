from zoneinfo import available_timezones

from django.core.exceptions import ValidationError
from django.db import models

from common.base import BaseModel
from common.models import Org


def _validate_iana_tz(value: str) -> None:
    if value not in available_timezones():
        raise ValidationError(f"{value!r} is not a valid IANA timezone.")


class BusinessCalendar(BaseModel):
    """A working-hours definition that SLA timers honor.

    Per `docs/cases/COORDINATION_DECISIONS.md` D2 we inherit BaseModel and
    declare our own org FK rather than using BaseOrgModel. v1 ships one
    default calendar per org; multi-calendar/per-team is out of scope.
    """

    name = models.CharField(max_length=100, default="Default")
    timezone = models.CharField(
        max_length=64,
        default="UTC",
        validators=[_validate_iana_tz],
        help_text="IANA timezone (e.g. America/New_York).",
    )
    is_default = models.BooleanField(default=True)

    monday_open = models.TimeField(blank=True, null=True)
    monday_close = models.TimeField(blank=True, null=True)
    tuesday_open = models.TimeField(blank=True, null=True)
    tuesday_close = models.TimeField(blank=True, null=True)
    wednesday_open = models.TimeField(blank=True, null=True)
    wednesday_close = models.TimeField(blank=True, null=True)
    thursday_open = models.TimeField(blank=True, null=True)
    thursday_close = models.TimeField(blank=True, null=True)
    friday_open = models.TimeField(blank=True, null=True)
    friday_close = models.TimeField(blank=True, null=True)
    saturday_open = models.TimeField(blank=True, null=True)
    saturday_close = models.TimeField(blank=True, null=True)
    sunday_open = models.TimeField(blank=True, null=True)
    sunday_close = models.TimeField(blank=True, null=True)

    org = models.ForeignKey(
        Org, on_delete=models.CASCADE, related_name="business_calendars"
    )

    class Meta:
        verbose_name = "Business Calendar"
        verbose_name_plural = "Business Calendars"
        db_table = "business_calendar"
        ordering = ("-is_default", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["org"],
                condition=models.Q(is_default=True),
                name="uniq_default_business_calendar_per_org",
            ),
        ]
        indexes = [
            models.Index(fields=["org", "is_default"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.timezone})"

    def windows_by_weekday(self):
        """Return list[(open_time, close_time) | None] indexed 0=Mon..6=Sun."""
        return [
            (self.monday_open, self.monday_close),
            (self.tuesday_open, self.tuesday_close),
            (self.wednesday_open, self.wednesday_close),
            (self.thursday_open, self.thursday_close),
            (self.friday_open, self.friday_close),
            (self.saturday_open, self.saturday_close),
            (self.sunday_open, self.sunday_close),
        ]


class BusinessHoliday(BaseModel):
    """A single full-day off on a calendar (national holiday, company day off).

    Holidays are date-based and apply for the entire day in the calendar's
    timezone — partial-day holidays are out of scope for v1.
    """

    calendar = models.ForeignKey(
        BusinessCalendar, on_delete=models.CASCADE, related_name="holidays"
    )
    date = models.DateField()
    name = models.CharField(max_length=100)
    org = models.ForeignKey(
        Org, on_delete=models.CASCADE, related_name="business_holidays"
    )

    class Meta:
        verbose_name = "Business Holiday"
        verbose_name_plural = "Business Holidays"
        db_table = "business_holiday"
        ordering = ("date",)
        constraints = [
            models.UniqueConstraint(
                fields=["calendar", "date"],
                name="uniq_business_holiday_per_calendar_date",
            ),
        ]
        indexes = [
            models.Index(fields=["calendar", "date"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.date.isoformat()})"
