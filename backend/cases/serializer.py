from rest_framework import serializers

from accounts.serializer import AccountSerializer
from cases.models import Case, CasePipeline, CaseStage
from common.utils import STATUS_CHOICE
from common.serializer import (
    OrganizationSerializer,
    ProfileSerializer,
    TagsSerializer,
    TeamsSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer


# Note: Removed unused serializer property:
# - created_on_arrow (frontend computes its own humanized timestamps)


class CaseSerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    contacts = ContactSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    created_by = UserSerializer(read_only=True)
    teams = TeamsSerializer(read_only=True, many=True)
    tags = TagsSerializer(read_only=True, many=True)
    org = OrganizationSerializer()

    class Meta:
        model = Case
        fields = (
            "id",
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "description",
            "created_by",
            "created_at",
            "is_active",
            "account",
            "contacts",
            "teams",
            "assigned_to",
            "tags",
            "org",
        )


class CaseCreateSerializer(serializers.ModelSerializer):
    closed_on = serializers.DateField(required=False, allow_null=True)
    org = serializers.PrimaryKeyRelatedField(read_only=True)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org
        # Make account read-only on updates (can only be set on creation)
        if self.instance:
            self.fields["account"].read_only = True

    def validate_name(self, name):
        if self.instance:
            if (
                Case.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Case already exists with this name")

        else:
            if Case.objects.filter(name__iexact=name, org=self.org).exists():
                raise serializers.ValidationError("Case already exists with this name")
        return name

    class Meta:
        model = Case
        fields = (
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "description",
            "is_active",
            "account",
            "org",
        )
        read_only_fields = ("org",)


class CaseCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = (
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "teams",
            "assigned_to",
            "account",
            "contacts",
            "tags",
            "description",
        )


class CaseDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    case_attachment = serializers.FileField()


class CaseCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()


# ============================================
# Kanban Serializers
# ============================================


class CaseStageSerializer(serializers.ModelSerializer):
    """Serializer for case stages."""

    case_count = serializers.SerializerMethodField()

    class Meta:
        model = CaseStage
        fields = [
            "id",
            "name",
            "order",
            "color",
            "stage_type",
            "maps_to_status",
            "wip_limit",
            "case_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "org")

    def get_case_count(self, obj):
        return obj.cases.count()


class CasePipelineSerializer(serializers.ModelSerializer):
    """Serializer for case pipelines with nested stages."""

    stages = CaseStageSerializer(many=True, read_only=True)
    stage_count = serializers.SerializerMethodField()
    case_count = serializers.SerializerMethodField()

    class Meta:
        model = CasePipeline
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "stages",
            "stage_count",
            "case_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "org")

    def get_stage_count(self, obj):
        return obj.stages.count()

    def get_case_count(self, obj):
        return Case.objects.filter(stage__pipeline=obj).count()


class CasePipelineListSerializer(serializers.ModelSerializer):
    """Simplified pipeline serializer for lists."""

    stage_count = serializers.SerializerMethodField()
    case_count = serializers.SerializerMethodField()

    class Meta:
        model = CasePipeline
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "stage_count",
            "case_count",
            "created_at",
        ]

    def get_stage_count(self, obj):
        return obj.stages.count()

    def get_case_count(self, obj):
        return Case.objects.filter(stage__pipeline=obj).count()


class CaseKanbanCardSerializer(serializers.ModelSerializer):
    """Lightweight serializer for kanban cards (minimal fields for performance)."""

    assigned_to = ProfileSerializer(read_only=True, many=True)
    account_name = serializers.SerializerMethodField()
    is_sla_breached = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            "id",
            "name",
            "status",
            "priority",
            "case_type",
            "stage",
            "kanban_order",
            "account_name",
            "assigned_to",
            "is_sla_breached",
            "is_sla_first_response_breached",
            "is_sla_resolution_breached",
            "created_at",
        ]

    def get_account_name(self, obj):
        return obj.account.name if obj.account else None

    def get_is_sla_breached(self, obj):
        """Return True if any SLA is breached."""
        return obj.is_sla_first_response_breached or obj.is_sla_resolution_breached


class CaseMoveSerializer(serializers.Serializer):
    """Serializer for moving cases in kanban."""

    stage_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=STATUS_CHOICE, required=False)
    kanban_order = serializers.DecimalField(
        max_digits=15, decimal_places=6, required=False
    )
    above_case_id = serializers.UUIDField(required=False, allow_null=True)
    below_case_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get("stage_id") and not attrs.get("status"):
            raise serializers.ValidationError(
                "Either stage_id or status must be provided"
            )
        return attrs
