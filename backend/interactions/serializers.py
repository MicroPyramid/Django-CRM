from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from interactions.access import PERSON_ORIGINS, may_change_interaction
from interactions.models import (
    CALL_OUTCOMES,
    DIRECTION_CHOICES,
    KIND_CHOICES,
    Interaction,
)
from interactions.service import HOME_KEYS

FUTURE_SLACK = timedelta(minutes=5)
# The largest value the integer column holds on PostgreSQL.
MAX_DURATION = 2_147_483_647

ENQUIRY_REFUSED = "Enquiries are recorded when a lead arrives; they cannot be logged."
KIND_FIXED = "The kind of an interaction cannot be changed."
RECORD_FIXED = "The record an interaction is on cannot be changed."
ONE_RECORD = "Name exactly one record: lead, contact, account, opportunity or case."
TOO_LATE = "This is more than five minutes in the future."
CALLS_ONLY = "Only a call has an outcome."


class InteractionSerializer(serializers.ModelSerializer):
    logged_by_details = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Interaction
        fields = (
            "id",
            "kind",
            "direction",
            "occurred_at",
            "duration_seconds",
            "duration_estimated",
            "outcome",
            "subject",
            "body",
            "logged_by",
            "logged_by_details",
            "participants",
            "lead",
            "contact",
            "account",
            "opportunity",
            "case",
            "home",
            "origin",
            "external_id",
            "created_at",
            "can_edit",
        )
        read_only_fields = fields

    def get_logged_by_details(self, obj) -> dict | None:
        profile = obj.logged_by
        if profile is None:
            return None
        return {
            "id": str(profile.id),
            "name": profile.user.name,
            "email": profile.user.email,
        }

    def get_can_edit(self, obj) -> bool:
        profile = self.context.get("profile")
        return profile is not None and may_change_interaction(profile, obj)


class InteractionWriteSerializer(serializers.Serializer):
    """What a person may send. `logged_by`, `org`, `participants` and
    `external_id` are the server's and are not read from the body.

    On an edit, `kind`, `home` and the record links may be sent back as they
    are, and are refused if they differ.
    """

    kind = serializers.ChoiceField(choices=KIND_CHOICES)
    direction = serializers.ChoiceField(choices=DIRECTION_CHOICES, required=False)
    occurred_at = serializers.DateTimeField(required=False)
    duration_seconds = serializers.IntegerField(
        min_value=0, max_value=MAX_DURATION, allow_null=True, required=False
    )
    duration_estimated = serializers.BooleanField(required=False)
    outcome = serializers.ChoiceField(
        choices=CALL_OUTCOMES, allow_blank=True, required=False
    )
    subject = serializers.CharField(max_length=200, allow_blank=True, required=False)
    body = serializers.CharField(max_length=10_000, allow_blank=True, required=False)
    origin = serializers.ChoiceField(choices=PERSON_ORIGINS, required=False)
    home = serializers.ChoiceField(choices=HOME_KEYS, required=False)
    lead = serializers.UUIDField(allow_null=True, required=False)
    contact = serializers.UUIDField(allow_null=True, required=False)
    account = serializers.UUIDField(allow_null=True, required=False)
    opportunity = serializers.UUIDField(allow_null=True, required=False)
    case = serializers.UUIDField(allow_null=True, required=False)

    def validate_kind(self, value):
        if self.instance is not None:
            if value != self.instance.kind:
                raise serializers.ValidationError(KIND_FIXED)
        elif value == "enquiry":
            raise serializers.ValidationError(ENQUIRY_REFUSED)
        return value

    def validate_occurred_at(self, value):
        if value > timezone.now() + FUTURE_SLACK:
            raise serializers.ValidationError(TOO_LATE)
        return value

    def validate(self, attrs):
        current = self.instance
        kind = attrs.get("kind", getattr(current, "kind", None))
        outcome = attrs.get("outcome", getattr(current, "outcome", ""))
        if outcome and kind != "call":
            raise serializers.ValidationError({"outcome": [CALLS_ONLY]})

        if current is None:
            # The one record named is the home; `home` itself is derived.
            attrs.pop("home", None)
            named = [name for name in HOME_KEYS if attrs.get(name)]
            if len(named) != 1:
                raise serializers.ValidationError(ONE_RECORD)
            home = named[0]
            for name in HOME_KEYS:
                if name != home:
                    attrs.pop(name, None)
            attrs["home"] = home
            return attrs

        if attrs.pop("home", current.home) != current.home:
            raise serializers.ValidationError({"home": [RECORD_FIXED]})
        for name in HOME_KEYS:
            if name in attrs and attrs.pop(name) != getattr(current, f"{name}_id"):
                raise serializers.ValidationError({name: [RECORD_FIXED]})
        attrs.pop("kind", None)
        return attrs
