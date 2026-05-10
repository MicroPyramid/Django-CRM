"""DRF serializers for the business-hours settings API."""

from datetime import time
from zoneinfo import available_timezones

from rest_framework import serializers

from business_hours.models import BusinessCalendar, BusinessHoliday


_WEEKDAY_FIELDS = (
    "monday_open",
    "monday_close",
    "tuesday_open",
    "tuesday_close",
    "wednesday_open",
    "wednesday_close",
    "thursday_open",
    "thursday_close",
    "friday_open",
    "friday_close",
    "saturday_open",
    "saturday_close",
    "sunday_open",
    "sunday_close",
)


class BusinessHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessHoliday
        fields = ("id", "date", "name")
        read_only_fields = ("id",)


class BusinessCalendarSerializer(serializers.ModelSerializer):
    holidays = BusinessHolidaySerializer(many=True, read_only=True)

    class Meta:
        model = BusinessCalendar
        fields = (
            "id",
            "name",
            "timezone",
            "is_default",
            *_WEEKDAY_FIELDS,
            "holidays",
        )
        read_only_fields = ("id", "is_default", "holidays")

    def validate_timezone(self, value):
        if value not in available_timezones():
            raise serializers.ValidationError("Not a valid IANA timezone.")
        return value

    def validate(self, attrs):
        # If a day has open or close it must have both, and close > open.
        for i in range(0, len(_WEEKDAY_FIELDS), 2):
            open_field = _WEEKDAY_FIELDS[i]
            close_field = _WEEKDAY_FIELDS[i + 1]
            open_val = attrs.get(open_field, getattr(self.instance, open_field, None))
            close_val = attrs.get(close_field, getattr(self.instance, close_field, None))
            if (open_val is None) != (close_val is None):
                raise serializers.ValidationError(
                    {open_field: "Open and close must be both set or both null."}
                )
            if open_val is not None and close_val is not None:
                if not isinstance(open_val, time) or not isinstance(close_val, time):
                    continue
                if close_val <= open_val:
                    raise serializers.ValidationError(
                        {close_field: "Close time must be after open time."}
                    )
        return attrs
