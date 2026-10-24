"""Lead webhooks (`LeadIntake`): admins create, edit, re-key and read them.

Every route, reads included, is for admins: an intake's settings say where
the org's leads come from and who gets them. The full key is answered only by
create and by replace; every other answer carries `key_hint`.
"""

import secrets
from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.links import api_url
from common.lookups import get_scoped_or_404
from common.models import Profile, Tags
from common.permissions import HasOrgContext, is_org_admin
from leads.intake_presets import clean_mapping, default_mapping, default_source
from leads.models import LeadIntake, LeadIntakeEvent
from leads.source_rules import check_source

DELIVERIES_SHOWN = 50
# How long a replaced key keeps working, so a sender can be updated in time.
PREVIOUS_KEY_DAYS = 7


def new_key() -> str:
    return secrets.token_urlsafe(32)


def _admin_required():
    return Response(
        {"error": True, "errors": "Admin access required"},
        status=status.HTTP_403_FORBIDDEN,
    )


def _invalid(errors):
    return Response(
        {"error": True, "errors": errors}, status=status.HTTP_400_BAD_REQUEST
    )


def delivery_row(event) -> dict:
    return {
        "id": str(event.id),
        "received_at": event.received_at,
        "result": event.result,
        "lead": str(event.lead_id) if event.lead_id else None,
        "external_id": event.external_id,
        "error": event.error,
    }


class LeadIntakeSerializer(serializers.ModelSerializer):
    """Reads and writes one intake. `key`, `org` and the delivery stamps are
    the server's: absent from `fields` or read-only, so a body naming them is
    ignored."""

    url = serializers.SerializerMethodField()
    key_hint = serializers.SerializerMethodField()
    assignee_details = serializers.SerializerMethodField()
    mapping = serializers.JSONField(required=False)
    default_source = serializers.CharField(
        max_length=64, required=False, allow_blank=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=Tags.objects.none()
    )
    assignee = serializers.PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=Profile.objects.none()
    )

    class Meta:
        model = LeadIntake
        fields = (
            "id",
            "name",
            "preset",
            "url",
            "key_hint",
            "mapping",
            "default_source",
            "source_detail",
            "tags",
            "assignee",
            "assignee_details",
            "is_active",
            "last_received_at",
            "last_error",
            "created_at",
        )
        read_only_fields = ("id", "last_received_at", "last_error", "created_at")

    def __init__(self, *args, **kwargs):
        """Tags and members are looked up in the caller's org only; with no
        org every lookup is empty, so the failure is a refusal."""
        super().__init__(*args, **kwargs)
        self._org = self.context.get("org")
        org = self._org
        self.fields["tags"].child_relation.queryset = (
            Tags.objects.filter(org=org) if org else Tags.objects.none()
        )
        self.fields["assignee"].queryset = (
            Profile.objects.filter(org=org) if org else Profile.objects.none()
        )

    def get_url(self, obj) -> str:
        return api_url(f"/api/public/leads/{obj.id}/")

    def get_key_hint(self, obj) -> str:
        return obj.key[-4:]

    def get_assignee_details(self, obj) -> dict | None:
        profile = obj.assignee
        if profile is None:
            return None
        return {
            "id": str(profile.id),
            "email": profile.user.email,
            "name": profile.user.name,
            "is_active": profile.is_active,
        }

    def validate_name(self, value):
        value = " ".join(value.split())
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_mapping(self, value):
        stored = self.instance.mapping if self.instance is not None else None
        return clean_mapping(value, self._org, stored=stored)

    def validate_default_source(self, value):
        stored = getattr(self.instance, "default_source", None)
        try:
            return check_source(value, self._org, stored)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))

    def validate_assignee(self, value):
        stored = getattr(self.instance, "assignee_id", None)
        if value is not None and not value.is_active and value.id != stored:
            raise serializers.ValidationError(
                "This user is deactivated. Choose an active member."
            )
        return value

    def create(self, validated_data):
        preset = validated_data.get("preset", LeadIntake.PRESET_GENERIC)
        validated_data.setdefault("mapping", default_mapping(preset))
        validated_data.setdefault("default_source", default_source(preset, self._org))
        return super().create(validated_data)


def _row(intake, key=None) -> dict:
    data = LeadIntakeSerializer(intake, context={"org": intake.org}).data
    if key is not None:
        data["key"] = key
    return data


class LeadIntakeListCreateView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Leads"], operation_id="lead_intakes_list")
    def get(self, request):
        if not is_org_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        intakes = (
            LeadIntake.objects.filter(org=org)
            .select_related("assignee__user")
            .prefetch_related("tags")
            .order_by("name", "created_at")
        )
        rows = LeadIntakeSerializer(intakes, many=True, context={"org": org}).data
        return Response({"intakes": rows})

    @extend_schema(
        tags=["Leads"], operation_id="lead_intakes_create", request=LeadIntakeSerializer
    )
    def post(self, request):
        if not is_org_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        serializer = LeadIntakeSerializer(data=request.data, context={"org": org})
        if not serializer.is_valid():
            return _invalid(serializer.errors)
        key = new_key()
        intake = serializer.save(org=org, key=key)
        return Response(_row(intake, key=key), status=status.HTTP_201_CREATED)


class LeadIntakeDetailView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Leads"], operation_id="lead_intakes_read")
    def get(self, request, pk):
        if not is_org_admin(request.profile):
            return _admin_required()
        intake = get_scoped_or_404(LeadIntake, pk, request.profile.org)
        intake.drop_old_events()
        return Response(_row(intake))

    @extend_schema(
        tags=["Leads"], operation_id="lead_intakes_update", request=LeadIntakeSerializer
    )
    def patch(self, request, pk):
        if not is_org_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        intake = get_scoped_or_404(LeadIntake, pk, org)
        serializer = LeadIntakeSerializer(
            intake, data=request.data, partial=True, context={"org": org}
        )
        if not serializer.is_valid():
            return _invalid(serializer.errors)
        serializer.save()
        return Response(_row(intake))

    @extend_schema(tags=["Leads"], operation_id="lead_intakes_delete")
    def delete(self, request, pk):
        if not is_org_admin(request.profile):
            return _admin_required()
        intake = get_scoped_or_404(LeadIntake, pk, request.profile.org)
        intake.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LeadIntakeKeyView(APIView):
    """Replace the key. The new one is answered once; the old one keeps
    working for `PREVIOUS_KEY_DAYS`, and a key older than that is dropped."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Leads"], operation_id="lead_intakes_replace_key")
    def post(self, request, pk):
        if not is_org_admin(request.profile):
            return _admin_required()
        intake = get_scoped_or_404(LeadIntake, pk, request.profile.org)
        key = new_key()
        intake.previous_key = intake.key
        intake.previous_key_expires_at = timezone.now() + timedelta(
            days=PREVIOUS_KEY_DAYS
        )
        intake.key = key
        intake.save(
            update_fields=[
                "key",
                "previous_key",
                "previous_key_expires_at",
                "updated_at",
            ]
        )
        return Response(_row(intake, key=key))


class LeadIntakeDeliveriesView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Leads"], operation_id="lead_intakes_deliveries")
    def get(self, request, pk):
        if not is_org_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        intake = get_scoped_or_404(LeadIntake, pk, org)
        intake.drop_old_events()
        events = LeadIntakeEvent.objects.filter(org=org, intake=intake).order_by(
            "-received_at"
        )[:DELIVERIES_SHOWN]
        return Response({"deliveries": [delivery_row(e) for e in events]})


class LeadIntakeTestView(APIView):
    """Log a `test` delivery, so an admin sees the deliveries list work. It
    makes no lead and touches neither delivery stamp."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Leads"], operation_id="lead_intakes_test")
    def post(self, request, pk):
        if not is_org_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        intake = get_scoped_or_404(LeadIntake, pk, org)
        if not intake.is_active:
            return _invalid({"is_active": ["Switch the webhook on first."]})
        event = LeadIntakeEvent.objects.create(
            org=org, intake=intake, result="test", payload={"test": True}
        )
        return Response(
            {"delivery": delivery_row(event)}, status=status.HTTP_201_CREATED
        )
